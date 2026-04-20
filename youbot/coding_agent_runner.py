from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from youbot.config import AppConfig
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.models import (
    CodingAgentBackend,
    CodingAgentResult,
    CodingAgentSessionRef,
    RepoRecord,
)
from youbot.utils import make_id, now_iso


CODEX_SESSION_RE = re.compile(r"session id:\s*([0-9a-fA-F-]{36})")


class CodingAgentRunner:
    def __init__(self, config: AppConfig, sessions: CodingAgentSessionRegistry) -> None:
        self._config = config
        self._sessions = sessions

    def get_backend(self, repo_id: str | None = None) -> CodingAgentBackend:
        if repo_id is not None:
            # Repo overrides can be added later when registry metadata exists.
            _ = repo_id
        return self._config.backends[self._config.default_backend]

    def run_code_change(self, repo: RepoRecord, request: str, context: str | None = None) -> CodingAgentResult:
        backend = self.get_backend(repo.repo_id)
        session_ref = self._sessions.get_session(repo.repo_id)
        invocation, seeded_session_id = self._build_invocation(backend, session_ref, request, context)
        started_at = now_iso()
        started = time.perf_counter()
        completed = subprocess.run(
            invocation,
            cwd=repo.path,
            capture_output=True,
            text=True,
            check=False,
        )
        finished_at = now_iso()
        duration_ms = int((time.perf_counter() - started) * 1000)
        combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        session_id = self._extract_session_id(backend.backend_name, combined, session_ref, seeded_session_id)
        result = CodingAgentResult(
            repo_id=repo.repo_id,
            backend_name=backend.backend_name,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
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
                return [*backend.command_prefix, "exec", "resume", session_ref.session_id, prompt], session_ref.session_id
            return [*backend.command_prefix, "exec", prompt], None
        if session_ref is not None and session_ref.backend_name == "claude_code":
            return [*backend.command_prefix, "-p", "--resume", session_ref.session_id, prompt], session_ref.session_id
        session_id = make_id()
        return [*backend.command_prefix, "-p", "--session-id", session_id, prompt], session_id

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
            return seeded_session_id or (session_ref.session_id if session_ref is not None else None)
        return session_ref.session_id if session_ref is not None else None

    def _append_run_log(self, result: CodingAgentResult) -> None:
        from youbot.config import state_root
        from youbot.utils import ensure_dir

        log_path = state_root() / "runs" / "coding_agents.jsonl"
        ensure_dir(log_path.parent)
        payload = {
            "repo_id": result.repo_id,
            "backend_name": result.backend_name,
            "session_id": result.session_id,
            "exit_code": result.exit_code,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
        }
        with log_path.open("a") as handle:
            handle.write(json.dumps(payload) + "\n")
