from __future__ import annotations

import json
from dataclasses import asdict

from youbot.config import AppConfig, state_root
from youbot.executor import Executor
from youbot.models import CommandRecord, ExecutionResult, RepoRecord
from youbot.utils import ensure_dir


class Scheduler:
    def __init__(self, config: AppConfig, executor: Executor) -> None:
        self._config = config
        self._executor = executor

    def run_all(self, repos: list[RepoRecord], commands: dict[str, list[CommandRecord]]) -> list[ExecutionResult]:
        results: list[ExecutionResult] = []
        for job in self._config.scheduler_jobs:
            repo = next((repo for repo in repos if repo.repo_id == job.repo_id), None)
            if repo is None:
                continue
            command = next(
                (command for command in commands.get(job.repo_id, []) if command.command_name == job.command_name),
                None,
            )
            if command is None:
                continue
            result = self._executor.run(repo, command, [])
            results.append(result)
        self._write_history(results)
        return results

    def _write_history(self, results: list[ExecutionResult]) -> None:
        path = state_root() / "scheduler" / "run_history.json"
        ensure_dir(path.parent)
        payload = [
            {
                "repo_id": result.repo_id,
                "command_name": result.command_name,
                "exit_code": result.exit_code,
                "started_at": result.started_at,
                "finished_at": result.finished_at,
            }
            for result in results
        ]
        path.write_text(json.dumps(payload, indent=2) + "\n")

