from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from youbot.coding_agent_runner import CodingAgentRunner
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.adapters import AdapterLoader
from youbot.config import AppConfig, add_repo_config, load_config
from youbot.conversation_store import ConversationStore
from youbot.executor import Executor
from youbot.justfile_parser import JustfileParser
from youbot.models import AdapterRecord, CommandRecord, ConversationMessage, OverviewSectionSpec, RepoRecord
from youbot.openai_chat import OpenAIChatOrchestrator
from youbot.registry import Registry
from youbot.router import Router
from youbot.scheduler import Scheduler
from youbot.scaffold import scaffold_managed_repo
from youbot.utils import make_id, now_iso


@dataclass(slots=True)
class ProcessedMessage:
    summary: str
    body: str
    repo_id: str | None


class AppController:
    def __init__(self) -> None:
        self.config: AppConfig = load_config()
        self.conversation_store = ConversationStore()
        self.session_registry = CodingAgentSessionRegistry()
        self.adapter_loader = AdapterLoader()
        self.registry = Registry(self.config, JustfileParser())
        self.executor = Executor()
        self.router = Router()
        self.openai_chat = OpenAIChatOrchestrator()
        self.coding_agent_runner = CodingAgentRunner(self.config, self.session_registry)
        self.scheduler = Scheduler(self.config, self.executor)
        self.repos, self.commands = self.registry.load()

    def set_active_repo(self, repo_id: str | None) -> None:
        _ = repo_id

    def get_repo(self, repo_id: str) -> RepoRecord | None:
        for repo in self.repos:
            if repo.repo_id == repo_id:
                return repo
        return None

    def get_commands(self, repo_id: str) -> list[CommandRecord]:
        return self.commands.get(repo_id, [])

    def build_repo_view(self, repo_id: str) -> Panel:
        repo = self.get_repo(repo_id)
        if repo is None:
            return Panel(f"Focused repo {repo_id!r} is not available.", title="Repo Workspace")

        commands = self.get_commands(repo.repo_id)
        session_ref = self.session_registry.get_session(repo.repo_id)
        adapter = self.adapter_loader.load(repo.repo_id)
        header = Text.assemble(
            ("Repo: ", "bold"),
            repo.repo_id,
            "\n",
            ("Status: ", "bold"),
            repo.status,
            "\n",
            ("Adapter: ", "bold"),
            repo.adapter_id or "none",
        )
        session_text = Text(
            "No coding-agent session tracked yet."
            if session_ref is None
            else (
                f"Backend: {session_ref.backend_name}\n"
                f"Kind: {session_ref.session_kind}\n"
                f"Session: {session_ref.session_id}\n"
                f"Status: {session_ref.status}"
            )
        )
        sections = [
            Columns(
                [
                    Panel(header, title="Repo", border_style="cyan"),
                    Panel(session_text, title="Coding Agent", border_style="magenta"),
                ],
                expand=True,
                equal=True,
            ),
            *self._build_repo_preview_sections(repo, commands, adapter),
            self._build_commands_panel(commands),
        ]
        return Panel(Group(*sections), title="Repo Workspace", border_style="green")

    def _build_commands_panel(self, commands: list[CommandRecord]) -> Panel:
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Command", style="bold")
        table.add_column("Description")
        for command in commands[:8]:
            table.add_row(command.command_name, command.description or "No description")
        if len(commands) > 8:
            table.add_row("...", f"{len(commands) - 8} more commands")
        return Panel(table, title="Commands", border_style="blue")

    def _build_repo_preview_sections(
        self,
        repo: RepoRecord,
        commands: list[CommandRecord],
        adapter: AdapterRecord | None,
    ) -> list[Panel]:
        if adapter is None or not adapter.overview_sections:
            return [Panel("No repo overview preview configured.", title="Overview", border_style="yellow")]

        panels: list[Panel] = []
        for spec in adapter.overview_sections:
            selected = self._resolve_overview_section(commands, spec)
            if selected is None:
                panels.append(
                    Panel(
                        "Configured overview command is not available in the current command inventory.",
                        title=spec.title or "Overview",
                        border_style="yellow",
                    )
                )
                continue

            command, arguments, label = selected
            result = self.executor.run(repo, command, arguments)
            panels.append(self._render_overview_result(repo.repo_id, result, spec, label))
        return panels

    def process_message(self, user_message: str, active_repo_id: str | None) -> ProcessedMessage:
        self.conversation_store.append_message(
            ConversationMessage(
                message_id=make_id(),
                role="user",
                content=user_message,
                created_at=now_iso(),
            )
        )
        conversation = self.conversation_store.get_conversation()
        if self.openai_chat.enabled:
            body, response_id = self.openai_chat.respond(
                user_message=user_message,
                active_repo_id=active_repo_id,
                repos=self.repos,
                commands=self.commands,
                last_response_id=conversation.last_response_id,
                tool_handler=self._handle_tool_call,
            )
            self.conversation_store.set_last_response_id(response_id)
            self._record_assistant(body)
            return ProcessedMessage("Assistant", body, active_repo_id)

        decision = self.router.route(user_message, active_repo_id, conversation, self.repos, self.commands)

        if decision.action_type == "clarify":
            body = f"I couldn't determine a command confidently.\n\n{decision.reasoning_summary}"
            self._record_assistant(body)
            return ProcessedMessage("Clarification needed", body, decision.repo_id)

        repo = self.get_repo(decision.repo_id) if decision.repo_id is not None else None
        if repo is None:
            body = "No repo selected."
            self._record_assistant(body)
            return ProcessedMessage("Missing repo", body, None)

        if decision.action_type == "code_change":
            request = decision.arguments[0] if decision.arguments else user_message
            result = self.coding_agent_runner.run_code_change(repo, request)
            body = self._format_coding_agent_result(result)
            self._record_assistant(body)
            return ProcessedMessage("Code change", body, repo.repo_id)

        command = next(
            (command for command in self.commands.get(repo.repo_id, []) if command.command_name == decision.command_name),
            None,
        )
        if command is None:
            body = f"Command {decision.command_name!r} was not found in {repo.repo_id}."
            self._record_assistant(body)
            return ProcessedMessage("Command missing", body, repo.repo_id)

        result = self.executor.run(repo, command, decision.arguments)
        body = self._format_execution_result(result)
        self._record_assistant(body)
        return ProcessedMessage(command.command_name, body, repo.repo_id)

    def _record_assistant(self, content: str) -> None:
        self.conversation_store.append_message(
            ConversationMessage(
                message_id=make_id(),
                role="assistant",
                content=content,
                created_at=now_iso(),
            )
        )

    def _format_execution_result(self, result) -> str:
        header = (
            f"Repo: {result.repo_id}\n"
            f"Command: {' '.join(result.invocation)}\n"
            f"Exit code: {result.exit_code}\n"
            f"Duration: {result.duration_ms}ms"
        )
        stdout = result.stdout.strip() or "(no stdout)"
        stderr = result.stderr.strip()
        if stderr:
            return f"{header}\n\nSTDOUT\n{stdout}\n\nSTDERR\n{stderr}"
        return f"{header}\n\nSTDOUT\n{stdout}"

    def _format_coding_agent_result(self, result) -> str:
        header = (
            f"Repo: {result.repo_id}\n"
            f"Backend: {result.backend_name}\n"
            f"Exit code: {result.exit_code}\n"
            f"Session id: {result.session_id or 'unknown'}\n"
            f"Duration: {result.duration_ms}ms"
        )
        stdout = result.stdout.strip() or "(no stdout)"
        stderr = result.stderr.strip()
        if stderr:
            return f"{header}\n\nSTDOUT\n{stdout}\n\nSTDERR\n{stderr}"
        return f"{header}\n\nSTDOUT\n{stdout}"

    def run_scheduled_jobs(self) -> list:
        return self.scheduler.run_all(self.repos, self.commands)

    def init_managed_repo(self, path: str, name: str) -> str:
        scaffold_managed_repo(Path(path), name, now_iso().split("T")[0])
        return f"Initialized managed repo at {path}"

    def register_repo(
        self,
        path: str,
        *,
        name: str | None = None,
        classification: str = "integrated",
    ) -> RepoRecord:
        repo_path = Path(path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repo path does not exist: {repo_path}")
        if not (repo_path / "justfile").exists():
            raise ValueError(f"Repo path does not contain a justfile: {repo_path}")

        add_repo_config(path=str(repo_path), name=name, classification=classification)  # type: ignore[arg-type]
        self.config = load_config()
        self.registry = Registry(self.config, JustfileParser())
        self.coding_agent_runner = CodingAgentRunner(self.config, self.session_registry)
        self.repos, self.commands = self.registry.load()

        registered = next((repo for repo in self.repos if Path(repo.path).resolve() == repo_path), None)
        if registered is None:
            raise RuntimeError(f"Repo registration completed but repo was not loaded: {repo_path}")
        return registered

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

    def _render_json_overview(
        self,
        repo_id: str,
        payload: dict | list,
        spec: OverviewSectionSpec,
        label: str,
    ):
        if repo_id == "job_search" and spec.command_name == "pipeline-status" and isinstance(payload, dict):
            return self._render_job_search_pipeline(payload, label)
        if repo_id == "job_search" and spec.command_name == "next-actions" and isinstance(payload, dict):
            return self._render_checklist(payload.get("items", []), label, max_items=6)
        if repo_id == "job_search" and spec.command_name == "active-openings" and isinstance(payload, dict):
            return self._render_job_search_openings(payload, label)
        if repo_id == "life_admin" and spec.command_name == "task-digest" and isinstance(payload, dict):
            return self._render_life_admin_digest(payload, label)
        if repo_id == "life_admin" and spec.command_name == "task-list" and isinstance(payload, dict):
            return self._render_task_list(payload.get("tasks", []), label, max_items=5)
        if repo_id == "trader-bot" and spec.command_name == "research-findings" and isinstance(payload, str):
            return Text(payload)
        return Text(f"Source: {label}\n{self._limit_lines(str(payload), max_lines=spec.max_lines)}")

    def _render_job_search_pipeline(self, payload: dict[str, Any], label: str):
        active_rows = []
        closed_rows = 0
        for row in payload.get("table", []):
            status = row.get("Status", "")
            if any(token in status.lower() for token in ("rejected", "soft no", "closed")):
                closed_rows += 1
                continue
            active_rows.append(row)

        summary = Text(f"Source: {label}\n")
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

    def _render_job_search_openings(self, payload: dict[str, Any], label: str):
        summary = Text(f"Source: {label}\n")
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

    def _render_checklist(self, items: list[dict[str, Any]], label: str, *, max_items: int):
        lines = [f"Source: {label}"]
        for item in items[:max_items]:
            lines.append(f"- {item.get('text', '')}")
        if len(items) > max_items:
            lines.append(f"... {len(items) - max_items} more")
        return Text("\n".join(lines))

    def _render_life_admin_digest(self, payload: dict[str, Any], label: str):
        counts = payload.get("counts", {})
        summary = Text(f"Source: {label}\n", style="")
        summary.append(
            f"Urgent: {counts.get('urgent', 0)}  High: {counts.get('high', 0)}  Medium: {counts.get('medium', 0)}",
            style="bold",
        )
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Priority", style="bold")
        table.add_column("Task")
        for task in payload.get("urgent", [])[:3]:
            table.add_row("Urgent", task.get("title", ""))
        for task in payload.get("high", [])[:3]:
            table.add_row("High", task.get("title", ""))
        return Group(summary, table)

    def _render_task_list(self, tasks: list[dict[str, Any]], label: str, *, max_items: int):
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("Task", style="bold")
        table.add_column("Priority")
        table.add_column("Status")
        for task in tasks[:max_items]:
            table.add_row(task.get("title", ""), str(task.get("priority", "")), str(task.get("status", "")))
        return Group(Text(f"Source: {label}"), table)

    def _render_overview_result(
        self,
        repo_id: str,
        result,
        spec: OverviewSectionSpec,
        label: str,
    ) -> Panel:
        title = spec.title or "Overview"
        if result.exit_code != 0:
            preview_error = result.stderr.strip() or result.stdout.strip() or "Preview command failed."
            return Panel(
                Text(f"Source: {label}\nPreview unavailable.\n{self._limit_lines(preview_error, max_lines=8)}"),
                title=title,
                border_style="red",
            )

        if spec.render_mode == "json" and result.parsed_payload is not None:
            renderable = self._render_json_overview(repo_id, result.parsed_payload, spec, label)
            return Panel(renderable, title=title, border_style="green")

        preview_text = result.stdout.strip() or "(no stdout)"
        if repo_id == "trader-bot" and spec.command_name == "research-findings":
            renderable = self._render_trader_findings(preview_text, label)
        elif repo_id == "trader-bot" and spec.command_name == "research-program":
            renderable = self._render_trader_program(preview_text, label, spec.max_lines)
        else:
            renderable = Text(f"Source: {label}\n{self._limit_lines(preview_text, max_lines=spec.max_lines)}")
        return Panel(renderable, title=title, border_style="green")

    def _render_trader_findings(self, text: str, label: str):
        strategies: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("### "):
                strategies.append(stripped.removeprefix("### ").strip())
            if len(strategies) >= 6:
                break
        lines = [f"Source: {label}", "Latest validated strategies:"]
        for item in strategies:
            lines.append(f"- {item}")
        return Text("\n".join(lines))

    def _render_trader_program(self, text: str, label: str, max_lines: int):
        important_lines: list[str] = [f"Source: {label}"]
        capture_prefixes = ("# Auto Research Program", "## Research Goal", "## Active Research Directions", "### ")
        for line in text.splitlines():
            stripped = line.strip()
            if any(stripped.startswith(prefix) for prefix in capture_prefixes):
                important_lines.append(stripped)
            if stripped.startswith("Markets:"):
                important_lines.append(stripped)
            if len(important_lines) >= max_lines:
                break
        return Text("\n".join(important_lines))

    def _limit_lines(self, text: str, *, max_lines: int) -> str:
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if len(lines) <= max_lines:
            return "\n".join(lines)
        return "\n".join([*lines[:max_lines], f"... ({len(lines) - max_lines} more lines)"])

    def _handle_tool_call(self, name: str, arguments: dict) -> dict:
        if name == "list_repos":
            return {
                "repos": [
                    {
                        "repo_id": repo.repo_id,
                        "name": repo.name,
                        "path": repo.path,
                        "status": repo.status,
                    }
                    for repo in self.repos
                ]
            }

        if name == "get_repo_overview":
            repo = self.get_repo(arguments["repo_id"])
            if repo is None:
                return {"error": f"Unknown repo {arguments['repo_id']}"}
            session_ref = self.session_registry.get_session(repo.repo_id)
            return {
                "repo_id": repo.repo_id,
                "path": repo.path,
                "status": repo.status,
                "adapter_id": repo.adapter_id,
                "coding_agent_session": None
                if session_ref is None
                else {
                    "backend": session_ref.backend_name,
                    "session_kind": session_ref.session_kind,
                    "session_id": session_ref.session_id,
                    "status": session_ref.status,
                    "last_used_at": session_ref.last_used_at,
                },
            }

        if name == "list_repo_commands":
            repo_id = arguments["repo_id"]
            return {
                "repo_id": repo_id,
                "commands": [
                    {
                        "command_name": command.command_name,
                        "description": command.description,
                    }
                    for command in self.get_commands(repo_id)
                ],
            }

        if name == "run_repo_command":
            repo = self.get_repo(arguments["repo_id"])
            if repo is None:
                return {"error": f"Unknown repo {arguments['repo_id']}"}
            command = next(
                (
                    command
                    for command in self.get_commands(repo.repo_id)
                    if command.command_name == arguments["command_name"]
                ),
                None,
            )
            if command is None:
                return {"error": f"Unknown command {arguments['command_name']} for repo {repo.repo_id}"}
            result = self.executor.run(repo, command, arguments.get("arguments", []))
            return {
                "repo_id": repo.repo_id,
                "command_name": command.command_name,
                "exit_code": result.exit_code,
                "stdout_preview": result.stdout[:2000],
                "stderr_preview": result.stderr[:2000],
            }

        if name == "run_code_change":
            repo = self.get_repo(arguments["repo_id"])
            if repo is None:
                return {"error": f"Unknown repo {arguments['repo_id']}"}
            result = self.coding_agent_runner.run_code_change(repo, arguments["request"])
            return {
                "repo_id": repo.repo_id,
                "backend": result.backend_name,
                "session_id": result.session_id,
                "exit_code": result.exit_code,
                "stdout_preview": result.stdout[:2000],
                "stderr_preview": result.stderr[:2000],
            }

        return {"error": f"Unknown tool {name}"}
