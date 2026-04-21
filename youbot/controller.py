from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from youbot.coding_agent_runner import CodingAgentRunner
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.adapters import AdapterLoader
from youbot.config import AppConfig, add_repo_config, load_config
from youbot.conversation_store import ConversationStore
from youbot.executor import Executor
from youbot.justfile_parser import JustfileParser
from youbot.models import AdapterRecord, CommandRecord, ConversationMessage, RepoRecord
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

    def build_repo_view(self, repo_id: str) -> str:
        repo = self.get_repo(repo_id)
        if repo is None:
            return f"Focused repo {repo_id!r} is not available."

        commands = self.get_commands(repo.repo_id)
        session_ref = self.session_registry.get_session(repo.repo_id)
        command_lines = [
            f"- {command.command_name}: {command.description or 'No description'}"
            for command in commands[:12]
        ]
        if len(commands) > 12:
            command_lines.append(f"... and {len(commands) - 12} more")

        session_text = (
            "No coding-agent session tracked yet."
            if session_ref is None
            else (
                f"Backend: {session_ref.backend_name}\n"
                f"Kind: {session_ref.session_kind}\n"
                f"Session: {session_ref.session_id}\n"
                f"Status: {session_ref.status}"
            )
        )

        adapter = self.adapter_loader.load(repo.repo_id)
        preview_text = self._build_repo_preview(repo, commands, adapter)
        return (
            f"Repo: {repo.repo_id}\n"
            f"Path: {repo.path}\n"
            f"Status: {repo.status}\n"
            f"Adapter: {repo.adapter_id or 'none'}\n\n"
            "Coding Agent\n"
            f"{session_text}\n\n"
            "Overview\n"
            f"{preview_text}\n\n"
            "Commands\n"
            + ("\n".join(command_lines) if command_lines else "(no commands discovered)")
        )

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

    def _build_repo_preview(
        self,
        repo: RepoRecord,
        commands: list[CommandRecord],
        adapter: AdapterRecord | None,
    ) -> str:
        if adapter is None or adapter.overview_command is None:
            return "No repo overview preview configured."

        selected = self._resolve_overview_command(commands, adapter)
        if selected is None:
            return "Configured overview command is not available in the current command inventory."

        command, arguments, label, max_lines, title = selected
        result = self.executor.run(repo, command, arguments)
        if result.exit_code != 0:
            preview_error = result.stderr.strip() or result.stdout.strip() or "Preview command failed."
            return (
                f"{title or 'Overview'}\n"
                f"Source: {label}\n"
                f"Preview unavailable.\n"
                f"{self._limit_lines(preview_error, max_lines=8)}"
            )

        preview_text = result.stdout.strip() or "(no stdout)"
        return (
            f"{title or 'Overview'}\n"
            f"Source: {label}\n"
            f"{self._limit_lines(preview_text, max_lines=max_lines)}"
        )

    def _resolve_overview_command(
        self,
        commands: list[CommandRecord],
        adapter: AdapterRecord,
    ) -> tuple[CommandRecord, list[str], str, int, str | None] | None:
        overview = adapter.overview_command
        if overview is None:
            return None

        candidate_names = [overview.command_name, *overview.fallback_command_names]
        for index, command_name in enumerate(candidate_names):
            command = next((item for item in commands if item.command_name == command_name), None)
            if command is None:
                continue
            arguments = overview.arguments if index == 0 else []
            label = " ".join([*command.invocation, *arguments])
            return command, arguments, label, overview.max_lines, overview.title
        return None

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
