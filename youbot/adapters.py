from __future__ import annotations

import json
from dataclasses import asdict

from youbot.config import state_root
from youbot.models import (
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
        overview_sections = self._select_overview_sections(repo, commands)
        quick_actions = self._select_quick_actions(repo, commands)
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
        self._write_generated_notes(repo, adapter)
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

    def _select_overview_sections(
        self,
        repo: RepoRecord,
        commands: list[CommandRecord],
    ) -> list[OverviewSectionSpec]:
        preferred_specs: dict[str, list[OverviewSectionSpec]] = {
            "job_search": [
                OverviewSectionSpec(
                    command_name="pipeline-status",
                    arguments=["json"],
                    title="Active Pipeline",
                    render_mode="json",
                    max_lines=12,
                    fallback_command_names=["active-openings"],
                ),
                OverviewSectionSpec(
                    command_name="next-actions",
                    arguments=["json"],
                    title="Next Actions",
                    render_mode="json",
                    max_lines=8,
                ),
                OverviewSectionSpec(
                    command_name="active-openings",
                    arguments=["json"],
                    title="Top Openings",
                    render_mode="json",
                    max_lines=6,
                ),
            ],
            "life_admin": [
                OverviewSectionSpec(
                    command_name="task-digest",
                    arguments=["json"],
                    title="Priority Digest",
                    render_mode="json",
                    max_lines=10,
                    fallback_command_names=["task-list"],
                ),
                OverviewSectionSpec(
                    command_name="task-list",
                    arguments=["5", "json"],
                    title="Top Tasks",
                    render_mode="json",
                    max_lines=8,
                ),
            ],
            "trader-bot": [
                OverviewSectionSpec(
                    command_name="research-program",
                    title="Research Program",
                    render_mode="text",
                    max_lines=14,
                    fallback_command_names=["research-findings"],
                ),
                OverviewSectionSpec(
                    command_name="research-findings",
                    title="Recent Findings",
                    render_mode="text",
                    max_lines=14,
                ),
            ],
        }
        preferred = preferred_specs.get(repo.repo_id)
        if preferred is not None:
            available = {command.command_name for command in commands}
            return [
                spec
                for spec in preferred
                if spec.command_name in available
                or any(name in available for name in spec.fallback_command_names)
            ]

        fallback_candidates = ("status", "list", "overview", "summary")
        for command in commands:
            if any(token in command.command_name for token in fallback_candidates):
                return [
                    OverviewSectionSpec(
                        command_name=command.command_name,
                        title=f"{repo.repo_id} Overview",
                        max_lines=12,
                    )
                ]
        return []

    def _write_generated_notes(self, repo: RepoRecord, adapter: AdapterRecord) -> None:
        lines = [
            f"# Generated adapter notes for {repo.repo_id}",
            "",
            f"Generated at: {adapter.updated_at}",
            f"Repo path: {repo.path}",
            "",
            "This file is generated by youbot during repo onboarding / refresh.",
            (
                "It captures the current adapter decision so it can later be refined "
                "manually or regenerated."
            ),
            "",
            "## Overview sections",
        ]
        if not adapter.overview_sections:
            lines.append("No overview sections were inferred.")
        else:
            for section in adapter.overview_sections:
                lines.extend(
                    [
                        f"- command: {section.command_name}",
                        f"  arguments: {section.arguments}",
                        f"  title: {section.title}",
                        f"  render_mode: {section.render_mode}",
                        f"  max_lines: {section.max_lines}",
                        f"  fallbacks: {section.fallback_command_names}",
                    ]
                )
        lines.extend(["", "## Quick actions"])
        if not adapter.quick_actions:
            lines.append("No quick actions were inferred.")
        else:
            for action in adapter.quick_actions:
                lines.extend(
                    [
                        f"- command: {action.command_name}",
                        f"  title: {action.title}",
                        f"  arguments: {action.arguments}",
                    ]
                )
        atomic_write(self._generated_root / f"{repo.repo_id}.md", "\n".join(lines) + "\n")

    def _select_quick_actions(
        self, repo: RepoRecord, commands: list[CommandRecord]
    ) -> list[QuickActionSpec]:
        preferred_specs: dict[str, list[QuickActionSpec]] = {
            "job_search": [
                QuickActionSpec(command_name="pipeline-status", title="Pipeline"),
                QuickActionSpec(command_name="next-actions", title="Next actions"),
                QuickActionSpec(command_name="active-openings", title="Openings"),
                QuickActionSpec(command_name="action-items", title="Action items"),
            ],
            "life_admin": [
                QuickActionSpec(command_name="task-digest", title="Priority digest"),
                QuickActionSpec(command_name="task-list", title="Top tasks", arguments=["5"]),
                QuickActionSpec(command_name="task-create", title="Add task"),
                QuickActionSpec(command_name="task-search", title="Search tasks"),
            ],
            "trader-bot": [
                QuickActionSpec(command_name="research-program", title="Research program"),
                QuickActionSpec(command_name="research-findings", title="Recent findings"),
                QuickActionSpec(command_name="research-cycle", title="Run research"),
                QuickActionSpec(command_name="list-markets", title="List markets"),
            ],
        }
        preferred = preferred_specs.get(repo.repo_id)
        available = {command.command_name for command in commands}
        if preferred is not None:
            return [spec for spec in preferred if spec.command_name in available]

        boilerplate = {
            "default",
            "venv",
            "install",
            "sync",
            "format",
            "lint",
            "typecheck",
            "pyright",
            "test",
        }
        inferred: list[QuickActionSpec] = []
        for command in commands:
            if command.command_name in boilerplate:
                continue
            inferred.append(QuickActionSpec(command_name=command.command_name))
            if len(inferred) >= 4:
                break
        return inferred

    def metadata_path(self, repo_id: str):
        return self._root / f"{repo_id}.json"
