from __future__ import annotations

import json
from dataclasses import asdict

from youbot.config import state_root
from youbot.models import AdapterRecord, CommandRecord, RepoRecord
from youbot.utils import atomic_write, ensure_dir, now_iso


class AdapterLoader:
    def __init__(self) -> None:
        self._root = state_root() / "adapters" / "metadata"

    def refresh(self, repo: RepoRecord, commands: list[CommandRecord]) -> AdapterRecord:
        ensure_dir(self._root)
        adapter = AdapterRecord(
            adapter_id=f"{repo.repo_id}-adapter",
            repo_id=repo.repo_id,
            version="0.1.0",
            view_names=["overview", "conversation"],
            command_palette_entries=[command.command_name for command in commands],
            output_rules=["repo_overview_preview"],
            updated_at=now_iso(),
        )
        atomic_write(self._root / f"{repo.repo_id}.json", json.dumps(asdict(adapter), indent=2) + "\n")
        return adapter
