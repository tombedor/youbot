from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from youbot.adapters.generation import (
    select_overview_sections,
    select_quick_actions,
    write_generated_notes,
)
from youbot.config import state_root
from youbot.core.models import (
    AdapterRecord,
    CommandRecord,
    OverviewSectionSpec,
    QuickActionSpec,
    RepoRecord,
)
from youbot.utils import atomic_write, ensure_dir, now_iso


class AdapterLoader:
    def __init__(self) -> None:
        self._root = state_root() / "adapters" / "metadata"
        self._generated_root = state_root() / "adapters" / "generated"

    def refresh(self, repo: RepoRecord, commands: list[CommandRecord]) -> AdapterRecord:
        ensure_dir(self._root)
        ensure_dir(self._generated_root)
        overview_sections = select_overview_sections(repo, commands)
        quick_actions = select_quick_actions(repo, commands)
        adapter = AdapterRecord(
            adapter_id=f"{repo.repo_id}-adapter",
            repo_id=repo.repo_id,
            version="0.1.0",
            view_names=["overview", "conversation"],
            command_palette_entries=[command.command_name for command in commands],
            output_rules=["repo_overview_preview"],
            updated_at=now_iso(),
            overview_sections=overview_sections,
            quick_actions=quick_actions,
        )
        atomic_write(self.metadata_path(repo.repo_id), json.dumps(asdict(adapter), indent=2) + "\n")
        write_generated_notes(self._generated_root / f"{repo.repo_id}.md", repo, adapter)
        return adapter

    def load(self, repo_id: str) -> AdapterRecord | None:
        path = self.metadata_path(repo_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text())
        overview_sections = [
            OverviewSectionSpec(**item) for item in payload.get("overview_sections", [])
        ]
        quick_actions = [QuickActionSpec(**item) for item in payload.get("quick_actions", [])]
        return AdapterRecord(
            adapter_id=payload["adapter_id"],
            repo_id=payload["repo_id"],
            version=payload["version"],
            view_names=payload["view_names"],
            command_palette_entries=payload["command_palette_entries"],
            output_rules=payload["output_rules"],
            updated_at=payload["updated_at"],
            overview_sections=overview_sections,
            quick_actions=quick_actions,
        )

    def metadata_path(self, repo_id: str) -> Path:
        return self._root / f"{repo_id}.json"
