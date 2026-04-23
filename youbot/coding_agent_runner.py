from __future__ import annotations

import json
import re
import subprocess
import time
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
        run_id = make_id()
        started_at = now_iso()
        self._activity_store.start(
            run_id=run_id,
            repo_id=repo.repo_id,
            backend_name=backend.backend_name,
            target_kind=target_kind,
            request_summary=request[:160],
        )
        self._activity_store.append(
            run_id, stream="status", content=f"Starting {backend.backend_name} session."
        )
        self._activity_store.append(
            run_id, stream="status", content=f"Invocation: {' '.join(invocation[:-1])} <prompt>"
        )
        started = time.perf_counter()
        try:
            process = subprocess.Popen(
                invocation,
                cwd=repo.path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            finished_at = now_iso()
            duration_ms = int((time.perf_counter() - started) * 1000)
            self._activity_store.append(run_id, stream="stderr", content=str(exc))
            self._activity_store.finish(run_id, exit_code=1, session_id=seeded_session_id)
            result = CodingAgentResult(
                repo_id=repo.repo_id,
                backend_name=backend.backend_name,
                target_kind=target_kind,  # type: ignore[arg-type]
                exit_code=1,
                stdout="",
                stderr=str(exc),
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                session_id=seeded_session_id,
            )
            self._append_run_log(result)
            return result
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
        finished_at = now_iso()
        duration_ms = int((time.perf_counter() - started) * 1000)
        stdout_text = "".join(stdout_lines)
        stderr_text = "".join(stderr_lines)
        combined = "\n".join(part for part in (stdout_text, stderr_text) if part)
        session_id = self._extract_session_id(
            backend.backend_name, combined, session_ref, seeded_session_id
        )
        self._activity_store.set_session_id(run_id, session_id)
        result = CodingAgentResult(
            repo_id=repo.repo_id,
            backend_name=backend.backend_name,
            target_kind=target_kind,  # type: ignore[arg-type]
            exit_code=return_code,
            stdout=stdout_text,
            stderr=stderr_text,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            session_id=session_id,
        )
        if session_id is not None:
            self._sessions.set_session(
                CodingAgentSessionRef(
                    repo_id=repo.repo_id,
                    backend_name=backend.backend_name,
                    session_kind="noninteractive",
                    session_id=session_id,
                    purpose_summary=request[:120],
                    status="active",
                    last_used_at=finished_at,
                )
            )
        self._activity_store.finish(run_id, exit_code=result.exit_code, session_id=session_id)
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
