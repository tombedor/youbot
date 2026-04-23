from __future__ import annotations

import time
from dataclasses import dataclass

from youbot.coding_agent_activity import CodingAgentActivityStore
from youbot.coding_agent_backend import build_invocation, extract_session_id
from youbot.coding_agent_logs import append_run_log
from youbot.coding_agent_process import launch_process, wait_for_process
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.config import AppConfig
from youbot.models import CodingAgentBackend, CodingAgentResult, CodingAgentSessionRef, RepoRecord
from youbot.utils import make_id, now_iso


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
        invocation, seeded_session_id = build_invocation(backend, session_ref, request, context)
        run = self._start_run(
            repo=repo,
            request=request,
            backend_name=backend.backend_name,
            invocation=invocation,
            target_kind=target_kind,
            session_ref=session_ref,
            seeded_session_id=seeded_session_id,
        )
        process = launch_process(invocation, repo.path)
        if isinstance(process, OSError):
            return self._handle_launch_error(run, process)
        stdout_text, stderr_text, return_code = wait_for_process(
            process,
            run.run_id,
            self._activity_store.append,
        )
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
        append_run_log(result)
        return result

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
        session_id = extract_session_id(
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
        append_run_log(result)
        return result
