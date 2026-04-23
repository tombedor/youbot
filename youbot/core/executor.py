from __future__ import annotations

import json
import subprocess
import time

from youbot.core.models import CommandRecord, ExecutionResult, RepoRecord
from youbot.utils import now_iso


class Executor:
    def run(
        self, repo: RepoRecord, command: CommandRecord, arguments: list[str]
    ) -> ExecutionResult:
        invocation = [*command.invocation, *arguments]
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
        parsed_payload = self._parse_payload(completed.stdout)
        self._append_run_log(
            {
                "repo_id": repo.repo_id,
                "command_name": command.command_name,
                "invocation": invocation,
                "exit_code": completed.returncode,
                "started_at": started_at,
                "finished_at": finished_at,
            }
        )
        return ExecutionResult(
            repo_id=repo.repo_id,
            command_name=command.command_name,
            invocation=invocation,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            parsed_payload=parsed_payload,
        )

    def _parse_payload(self, stdout: str) -> dict[str, object] | list[object] | None:
        text = stdout.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return parsed
        return None

    def _append_run_log(self, payload: dict[str, object]) -> None:

        from youbot.config import state_root
        from youbot.utils import ensure_dir

        log_path = state_root() / "runs" / "commands.jsonl"
        ensure_dir(log_path.parent)
        with log_path.open("a") as handle:
            handle.write(json.dumps(payload) + "\n")
