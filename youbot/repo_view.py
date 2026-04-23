from __future__ import annotations

from typing import Any

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from youbot.adapters import AdapterLoader
from youbot.executor import Executor
from youbot.models import AdapterRecord, CommandRecord, OverviewSectionSpec, RepoRecord


class RepoViewBuilder:
    def __init__(self, adapter_loader: AdapterLoader, executor: Executor) -> None:
        self._adapter_loader = adapter_loader
        self._executor = executor

    def build(self, repo: RepoRecord, commands: list[CommandRecord]) -> RenderableType:
        adapter = self._adapter_loader.load(repo.repo_id)
        sections = self._build_preview_sections(repo, commands, adapter)
        quick_actions = self._build_quick_actions_panel(commands, adapter)
        if not sections:
            return quick_actions
        if len(sections) == 1:
            return Group(sections[0], quick_actions)

        primary = sections[0]
        secondary = Group(*sections[1:], quick_actions)
        grid = Table.grid(expand=True)
        grid.add_column(ratio=3)
        grid.add_column(ratio=2)
        grid.add_row(primary, secondary)
        return grid

    def _build_quick_actions_panel(
        self, commands: list[CommandRecord], adapter: AdapterRecord | None
    ) -> Panel:
        available = {command.command_name: command for command in commands}
        quick_actions = (
            []
            if adapter is None
            else [item for item in adapter.quick_actions if item.command_name in available]
        )
        table = Table(expand=True, box=None, show_header=False)
        table.add_column("Action", style="bold cyan", no_wrap=True)
        table.add_column("Command")
        table.add_column("Description")
        for action in quick_actions[:4]:
            command = available[action.command_name]
            invocation = " ".join([command.command_name, *action.arguments]).strip()
            table.add_row(
                action.title or command.command_name.replace("-", " "),
                invocation,
                command.description or "Common action",
            )
        if not quick_actions:
            table.add_row(
                "No quick actions", "", "Adapter metadata has not defined recommended commands yet."
            )
        elif len(commands) > len(quick_actions):
            table.add_row(
                "More", "", f"{len(commands) - len(quick_actions)} additional commands available."
            )
        return Panel(table, title="Quick Actions", border_style="blue")

    def _build_preview_sections(
        self,
        repo: RepoRecord,
        commands: list[CommandRecord],
        adapter: AdapterRecord | None,
    ) -> list[Panel]:
        if adapter is None or not adapter.overview_sections:
            return [
                Panel(
                    "No repo overview preview configured.",
                    title="Overview",
                    border_style="yellow",
                )
            ]

        panels: list[Panel] = []
        for spec in adapter.overview_sections:
            resolved = self._resolve_overview_section(commands, spec)
            if resolved is None:
                panels.append(self._missing_section_panel(spec))
                continue

            command, arguments, label = resolved
            result = self._executor.run(repo, command, arguments)
            panels.append(self._render_overview_result(repo.repo_id, result, spec, label))
        return panels

    def _resolve_overview_section(
        self,
        commands: list[CommandRecord],
        section: OverviewSectionSpec,
    ) -> tuple[CommandRecord, list[str], str] | None:
        candidate_names = [section.command_name, *section.fallback_command_names]
        for index, command_name in enumerate(candidate_names):
            command = next((item for item in commands if item.command_name == command_name), None)
            if command is None:
                continue
            arguments = section.arguments if index == 0 else []
            label = " ".join([*command.invocation, *arguments])
            return command, arguments, label
        return None

    def _missing_section_panel(self, spec: OverviewSectionSpec) -> Panel:
        return Panel(
            "Configured overview command is not available in the current command inventory.",
            title=spec.title or "Overview",
            border_style="yellow",
        )

    def _render_overview_result(
        self,
        repo_id: str,
        result,
        spec: OverviewSectionSpec,
        label: str,
    ) -> Panel:
        title = spec.title or "Overview"
        if result.exit_code != 0:
            preview_error = (
                result.stderr.strip() or result.stdout.strip() or "Preview command failed."
            )
            return Panel(
                Text(f"Preview unavailable.\n{self._limit_lines(preview_error, max_lines=8)}"),
                title=title,
                border_style="red",
            )

        renderable = self._render_successful_overview(repo_id, result, spec, label)
        return Panel(renderable, title=title, border_style="green")

    def _render_successful_overview(self, repo_id: str, result, spec, label: str):
        if spec.render_mode == "json" and result.parsed_payload is not None:
            return self._render_json_overview(repo_id, result.parsed_payload, spec, label)

        preview_text = result.stdout.strip() or "(no stdout)"
        if repo_id == "trader-bot" and spec.command_name == "research-findings":
            return self._render_trader_findings(preview_text)
        if repo_id == "trader-bot" and spec.command_name == "research-program":
            return self._render_trader_program(preview_text, spec.max_lines)
        return Text(self._limit_lines(preview_text, max_lines=spec.max_lines))

    def _render_json_overview(
        self,
        repo_id: str,
        payload: dict | list,
        spec: OverviewSectionSpec,
        label: str,
    ):
        handlers = {
            ("job_search", "pipeline-status"): lambda: self._render_job_search_pipeline(payload),
            ("job_search", "next-actions"): lambda: self._render_checklist(
                payload.get("items", []), max_items=6
            ),
            ("job_search", "active-openings"): lambda: self._render_job_search_openings(payload),
            ("life_admin", "task-digest"): lambda: self._render_life_admin_digest(payload),
            ("life_admin", "task-list"): lambda: self._render_task_list(
                payload.get("tasks", []), max_items=5
            ),
            ("trader-bot", "research-findings"): lambda: Text(str(payload)),
        }
        handler = handlers.get((repo_id, spec.command_name))
        if isinstance(payload, dict) and handler is not None:
            return handler()
        return Text(self._limit_lines(str(payload), max_lines=spec.max_lines))

    def _render_job_search_pipeline(self, payload: dict[str, Any]):
        active_rows = []
        closed_rows = 0
        for row in payload.get("table", []):
            status = row.get("Status", "")
            if any(token in status.lower() for token in ("rejected", "soft no", "closed")):
                closed_rows += 1
                continue
            active_rows.append(row)

        summary = Text()
        summary.append(f"Active opportunities: {len(active_rows)}", style="bold green")
        if closed_rows:
            summary.append(f"  Hidden closed outcomes: {closed_rows}", style="yellow")

        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Company", style="bold")
        table.add_column("Status", style="green")
        table.add_column("Notes")
        for row in active_rows[:7]:
            table.add_row(row.get("Company", ""), row.get("Status", ""), row.get("Notes", ""))
        if len(active_rows) > 7:
            table.add_row("...", "", f"{len(active_rows) - 7} more active opportunities")
        return Group(summary, table)

    def _render_job_search_openings(self, payload: dict[str, Any]):
        summary = Text()
        summary.append(f"Tracked openings: {len(payload.get('items', []))}", style="bold green")

        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Company", style="bold")
        table.add_column("Opening")
        highlights = 0
        for item in payload.get("items", []):
            details = str(item.get("details", ""))
            if "TOP PRIORITY" not in details:
                continue
            title = details.split(" — ")[0] if " — " in details else details
            table.add_row(str(item.get("name", "")), title)
            highlights += 1
            if highlights >= 5:
                break
        if highlights == 0:
            for item in payload.get("items", [])[:5]:
                details = str(item.get("details", ""))
                title = details.split(" — ")[0] if " — " in details else details
                table.add_row(str(item.get("name", "")), title)
        return Group(summary, table)

    def _render_checklist(self, items: list[dict[str, Any]], *, max_items: int):
        lines = [f"- {item.get('text', '')}" for item in items[:max_items]]
        if len(items) > max_items:
            lines.append(f"... {len(items) - max_items} more")
        return Text("\n".join(lines))

    def _render_life_admin_digest(self, payload: dict[str, Any]):
        counts = payload.get("counts", {})
        summary = Text("", style="")
        summary.append(f"{counts.get('urgent', 0)} urgent", style="bold red")
        summary.append("  |  ", style="dim")
        summary.append(f"{counts.get('high', 0)} high", style="bold yellow")
        summary.append("  |  ", style="dim")
        summary.append(f"{counts.get('medium', 0)} medium", style="bold")
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Priority", style="bold")
        table.add_column("Task")
        for task in payload.get("urgent", [])[:3]:
            table.add_row("Urgent", task.get("title", ""))
        for task in payload.get("high", [])[:3]:
            table.add_row("High", task.get("title", ""))
        return Group(summary, table)

    def _render_task_list(self, tasks: list[dict[str, Any]], *, max_items: int):
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Task", style="bold")
        table.add_column("Priority")
        table.add_column("Status")
        for task in tasks[:max_items]:
            table.add_row(
                task.get("title", ""), str(task.get("priority", "")), str(task.get("status", ""))
            )
        return table

    def _render_trader_findings(self, text: str):
        strategies: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("### "):
                strategies.append(stripped.removeprefix("### ").strip())
            if len(strategies) >= 6:
                break
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("#", style="bold cyan", width=3)
        table.add_column("Strategy", style="bold")
        for index, item in enumerate(strategies, start=1):
            table.add_row(str(index), item.replace("_", " "))
        return table

    def _render_trader_program(self, text: str, max_lines: int):
        goal = ""
        directions: list[tuple[str, str]] = []
        current_title = ""
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("Goal:"):
                goal = stripped.removeprefix("Goal:").strip()
            elif stripped.startswith("### "):
                current_title = stripped.removeprefix("### ").strip()
            elif stripped.startswith("Markets:") and current_title:
                directions.append((current_title, stripped.removeprefix("Markets:").strip()))
                current_title = ""
            if len(directions) >= max_lines:
                break

        summary = Text(
            goal or "Active market research directions extracted from the current program.",
            style="italic",
        )
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Direction", style="bold")
        table.add_column("Markets")
        for title, markets in directions[:4]:
            table.add_row(title, markets)
        return Group(summary, table)

    def _limit_lines(self, text: str, *, max_lines: int) -> str:
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return "\n".join([*lines[:max_lines], f"... ({len(lines) - max_lines} more lines)"])
