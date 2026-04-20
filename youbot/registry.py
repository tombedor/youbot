from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from youbot.adapters import AdapterLoader
from youbot.config import AppConfig, state_root
from youbot.justfile_parser import JustfileParser
from youbot.models import CommandRecord, RepoRecord
from youbot.utils import atomic_write, ensure_dir, now_iso


class Registry:
    def __init__(self, config: AppConfig, parser: JustfileParser) -> None:
        self._config = config
        self._parser = parser
        self._adapters = AdapterLoader()
        self._root = state_root() / "registry"
        self._repos_path = self._root / "repos.json"
        self._commands_path = self._root / "commands.json"

    def load(self) -> tuple[list[RepoRecord], dict[str, list[CommandRecord]]]:
        ensure_dir(self._root)
        repos = [self._build_repo_record(repo) for repo in self._config.repos]
        commands = {repo.repo_id: self._parser.parse_repo(repo) for repo in repos if repo.status == "ready"}
        for repo in repos:
            if repo.status == "ready":
                adapter = self._adapters.refresh(repo, commands.get(repo.repo_id, []))
                repo.adapter_id = adapter.adapter_id
        self._write_repos(repos)
        self._write_commands(commands)
        return repos, commands

    def _build_repo_record(self, repo_config) -> RepoRecord:
        path = Path(repo_config.path)
        if not path.exists():
            status = "missing"
        elif not (path / "justfile").exists():
            status = "invalid"
        else:
            status = "ready"
        return RepoRecord(
            repo_id=repo_config.repo_id,
            name=repo_config.name,
            path=repo_config.path,
            classification=repo_config.classification,
            status=status,
            last_scanned_at=now_iso(),
        )

    def _write_repos(self, repos: list[RepoRecord]) -> None:
        atomic_write(self._repos_path, json.dumps([asdict(repo) for repo in repos], indent=2) + "\n")

    def _write_commands(self, commands: dict[str, list[CommandRecord]]) -> None:
        payload = {repo_id: [asdict(command) for command in items] for repo_id, items in commands.items()}
        atomic_write(self._commands_path, json.dumps(payload, indent=2) + "\n")
