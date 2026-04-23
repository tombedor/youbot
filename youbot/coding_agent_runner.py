from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from threading import Thread

from youbot.coding_agent_activity import CodingAgentActivityStore
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.config import AppConfig
from youbot.models import (
    CodingAgentBackend,
    CodingAgentResult,
    CodingAgentSessionRef,
    RepoRecord,
)
from youbot.utils import make_id, now_iso

CODEX_SESSION_RE = re.compile(r"session id:\s*([0-9a-fA-F-]{36})")


@dataclass(slots=True)
class CodeChangeRun:
    repo: RepoRecord
    request: str
    backend_name: str
    target_kind: str
    session_ref: CodingAgentSessionRef | None
    seeded_session_id: str | None
    run_id: str
    started_at: str
    started: float


class CodingAgentRunner:
    def __init__(
        self,
        config: AppConfig,
        sessions: CodingAgentSessionRegistry,
        activity_store: CodingAgentActivityStore | None = None,
    ) -> None:
        self._config = config
        self._sessions = sessions
        self._activity_store = activity_store or CodingAgentActivityStore()

    def get_backend(self, repo_id: str | None = None) -> CodingAgentBackend:
        if repo_id is not None:
            # Repo overrides can be added later when registry metadata exists.
            _ = repo_id
        return self._config.backends[self._config.default_backend]

    def run_code_change(
        self,
        repo: RepoRecord,
        request: str,
        context: str | None = None,
        *,
        target_kind: str = "repo",
    ) -> CodingAgentResult:
        backend = self.get_backend(repo.repo_id)
        session_ref = self._sessions.get_session(repo.repo_id)
        invocation, seeded_session_id = self._build_invocation(
            backend, session_ref, request, context
        )
        run = self._start_run(
            repo=repo,
            request=request,
            backend_name=backend.backend_name,
            invocation=invocation,
            target_kind=target_kind,
            session_ref=session_ref,
            seeded_session_id=seeded_session_id,
        )
        process = self._launch_process(invocation, repo.path)
        if isinstance(process, OSError):
            return self._handle_launch_error(run, process)
        stdout_text, stderr_text, return_code = self._wait_for_process(process, run.run_id)
        return self._finalize_success(
            run,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            return_code=return_code,
        )

    def _start_run(
        self,
        *,
        repo: RepoRecord,
        request: str,
        backend_name: str,
        invocation: list[str],
        target_kind: str,
        session_ref: CodingAgentSessionRef | None,
        seeded_session_id: str | None,
    ) -> CodeChangeRun:
        run_id = make_id()
        started_at = now_iso()
        self._activity_store.start(
            run_id=run_id,
            repo_id=repo.repo_id,
            backend_name=backend_name,
            target_kind=target_kind,
            request_summary=request[:160],
        )
        self._activity_store.append(
            run_id, stream="status", content=f"Starting {backend_name} session."
        )
        self._activity_store.append(
            run_id, stream="status", content=f"Invocation: {' '.join(invocation[:-1])} <prompt>"
        )
        return CodeChangeRun(
            repo=repo,
            request=request,
            backend_name=backend_name,
            target_kind=target_kind,
            session_ref=session_ref,
            seeded_session_id=seeded_session_id,
            run_id=run_id,
            started_at=started_at,
            started=time.perf_counter(),
        )

    def _launch_process(self, invocation: list[str], repo_path: str):
        try:
            return subprocess.Popen(
                invocation,
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            return exc

    def _handle_launch_error(self, run: CodeChangeRun, error: OSError) -> CodingAgentResult:
        finished_at = now_iso()
        duration_ms = int((time.perf_counter() - run.started) * 1000)
        self._activity_store.append(run.run_id, stream="stderr", content=str(error))
        self._activity_store.finish(run.run_id, exit_code=1, session_id=run.seeded_session_id)
        result = CodingAgentResult(
            repo_id=run.repo.repo_id,
            backend_name=run.backend_name,  # type: ignore[arg-type]
            target_kind=run.target_kind,  # type: ignore[arg-type]
            exit_code=1,
            stdout="",
            stderr=str(error),
            started_at=run.started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            session_id=run.seeded_session_id,
        )
        self._append_run_log(result)
        return result

    def _wait_for_process(
        self, process: subprocess.Popen[str], run_id: str
    ) -> tuple[str, str, int]:
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []
        stdout_thread = Thread(
            target=self._consume_stream,
            args=(process.stdout, stdout_lines, run_id, "stdout"),
            daemon=True,
        )
        stderr_thread = Thread(
            target=self._consume_stream,
            args=(process.stderr, stderr_lines, run_id, "stderr"),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        return_code = process.wait()
        stdout_thread.join()
        stderr_thread.join()
        return "".join(stdout_lines), "".join(stderr_lines), return_code

    def _finalize_success(
        self,
        run: CodeChangeRun,
        stdout_text: str,
        stderr_text: str,
        return_code: int,
    ) -> CodingAgentResult:
        finished_at = now_iso()
        duration_ms = int((time.perf_counter() - run.started) * 1000)
        combined = "\n".join(part for part in (stdout_text, stderr_text) if part)
        session_id = self._extract_session_id(
            run.backend_name,
            combined,
            run.session_ref,
            run.seeded_session_id,
        )
        self._activity_store.set_session_id(run.run_id, session_id)
        result = CodingAgentResult(
            repo_id=run.repo.repo_id,
            backend_name=run.backend_name,  # type: ignore[arg-type]
            target_kind=run.target_kind,  # type: ignore[arg-type]
            exit_code=return_code,
            stdout=stdout_text,
            stderr=stderr_text,
            started_at=run.started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            session_id=session_id,
        )
        if session_id is not None:
            self._sessions.set_session(
                CodingAgentSessionRef(
                    repo_id=run.repo.repo_id,
                    backend_name=run.backend_name,  # type: ignore[arg-type]
                    session_kind="noninteractive",
                    session_id=session_id,
                    purpose_summary=run.request[:120],
                    status="active",
                    last_used_at=finished_at,
                )
            )
        self._activity_store.finish(run.run_id, exit_code=result.exit_code, session_id=session_id)
        self._append_run_log(result)
        return result

    def _build_invocation(
        self,
        backend: CodingAgentBackend,
        session_ref: CodingAgentSessionRef | None,
        request: str,
        context: str | None,
    ) -> tuple[list[str], str | None]:
        prompt = request if context is None else f"{context}\n\n{request}"
        if backend.backend_name == "codex":
            if session_ref is not None and session_ref.backend_name == "codex":
                return [
                    *backend.command_prefix,
                    *backend.default_args,
                    "exec",
                    "resume",
                    session_ref.session_id,
                    prompt,
                ], session_ref.session_id
            return [*backend.command_prefix, *backend.default_args, "exec", prompt], None
        if session_ref is not None and session_ref.backend_name == "claude_code":
            return [
                *backend.command_prefix,
                *backend.default_args,
                "-p",
                "--resume",
                session_ref.session_id,
                prompt,
            ], session_ref.session_id
        session_id = make_id()
        return [
            *backend.command_prefix,
            *backend.default_args,
            "-p",
            "--session-id",
            session_id,
            prompt,
        ], session_id

    def _consume_stream(
        self,
        handle,
        target: list[str],
        run_id: str,
        stream: str,
    ) -> None:
        if handle is None:
            return
        try:
            for line in handle:
                target.append(line)
                stripped = line.rstrip()
                if stripped:
                    self._activity_store.append(run_id, stream=stream, content=stripped)
        finally:
            handle.close()

    def _extract_session_id(
        self,
        backend_name: str,
        output: str,
        session_ref: CodingAgentSessionRef | None,
        seeded_session_id: str | None,
    ) -> str | None:
        if backend_name == "codex":
            match = CODEX_SESSION_RE.search(output)
            if match is not None:
                return match.group(1)
            if session_ref is not None:
                return session_ref.session_id
        if backend_name == "claude_code":
            return seeded_session_id or (
                session_ref.session_id if session_ref is not None else None
            )
        return session_ref.session_id if session_ref is not None else None

    def _append_run_log(self, result: CodingAgentResult) -> None:
        from youbot.config import state_root
        from youbot.utils import ensure_dir

        log_path = state_root() / "runs" / "coding_agents.jsonl"
        ensure_dir(log_path.parent)
        payload = {
            "repo_id": result.repo_id,
            "backend_name": result.backend_name,
            "target_kind": result.target_kind,
            "session_id": result.session_id,
            "exit_code": result.exit_code,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        }
        with log_path.open("a") as handle:
            handle.write(json.dumps(payload) + "\n")
