from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import RenderableType
from rich.text import Text

from youbot.adapters.change import build_adapter_change_request, build_self_repo_record
from youbot.adapters.loader import AdapterLoader
from youbot.agents.activity import CodingAgentActivityStore
from youbot.agents.runner import CodingAgentRunner
from youbot.agents.sessions import CodingAgentSessionRegistry
from youbot.chat.openai_chat import OpenAIChatOrchestrator
from youbot.chat.tool_handler import ToolCallHandler
from youbot.config import AppConfig, add_repo_config, load_config
from youbot.core.executor import Executor
from youbot.core.models import (
    CodingAgentActivitySnapshot,
    CodingAgentResult,
    CommandRecord,
    ConversationMessage,
    ExecutionResult,
    RepoClassification,
    RepoRecord,
)
from youbot.core.scaffold import scaffold_managed_repo
from youbot.core.scheduler import Scheduler
from youbot.routing.router import Router
from youbot.state.conversation_store import ConversationStore
from youbot.state.justfile_parser import JustfileParser
from youbot.state.registry import Registry
from youbot.state.usage_review import UsageReviewService
from youbot.tui.repo_view import RepoViewBuilder
from youbot.utils import make_id, now_iso


@dataclass(slots=True)
class ProcessedMessage:
    summary: str
    body: str
    repo_id: str | None


class AppController:
    def __init__(self) -> None:
        self.config: AppConfig = load_config()
        self.active_repo_id: str | None = None
        self.conversation_store = ConversationStore()
        self.session_registry = CodingAgentSessionRegistry()
        self.activity_store = CodingAgentActivityStore()
        self.usage_review_service = UsageReviewService()
        self.adapter_loader = AdapterLoader()
        self.registry = Registry(self.config, JustfileParser())
        self.executor = Executor()
        self.repo_view_builder = RepoViewBuilder(self.adapter_loader, self.executor)
        self.router = Router()
        self.openai_chat = OpenAIChatOrchestrator()
        self.coding_agent_runner = CodingAgentRunner(
            self.config, self.session_registry, self.activity_store
        )
        self.scheduler = Scheduler(self.config, self.executor)
        self.repos, self.commands = self.registry.load()
        self.tool_handler = ToolCallHandler(
            repos_provider=lambda: self.repos,
            get_repo=self.get_repo,
            get_commands=self.get_commands,
            session_registry=self.session_registry,
            executor=self.executor,
            coding_agent_runner=self.coding_agent_runner,
            adapter_loader=self.adapter_loader,
        )

    def set_active_repo(self, repo_id: str | None) -> None:
        if repo_id != self.active_repo_id:
            self.conversation_store.set_last_response_id(None)
        self.active_repo_id = repo_id

    def get_repo(self, repo_id: str) -> RepoRecord | None:
        for repo in self.repos:
            if repo.repo_id == repo_id:
                return repo
        return None

    def get_commands(self, repo_id: str) -> list[CommandRecord]:
        return self.commands.get(repo_id, [])

    def build_repo_view(self, repo_id: str) -> RenderableType:
        repo = self.get_repo(repo_id)
        if repo is None:
            return Text(f"Focused repo {repo_id!r} is not available.")
        return self.repo_view_builder.build(repo, self.get_commands(repo.repo_id))

    def process_message(self, user_message: str, active_repo_id: str | None) -> ProcessedMessage:
        self.active_repo_id = active_repo_id
        self.conversation_store.append_message(
            ConversationMessage(
                message_id=make_id(),
                role="user",
                content=user_message,
                created_at=now_iso(),
            )
        )
        builtin = self._maybe_handle_builtin_command(user_message)
        if builtin is not None:
            self._record_assistant(builtin.body)
            return builtin

        conversation = self.conversation_store.get_conversation()
        if self.openai_chat.enabled:
            body, response_id = self.openai_chat.respond(
                user_message=user_message,
                active_repo_id=active_repo_id,
                repos=self.repos,
                commands=self.commands,
                last_response_id=conversation.last_response_id,
                tool_handler=self.tool_handler.handle,
            )
            self.conversation_store.set_last_response_id(response_id)
            self._record_assistant(body)
            return ProcessedMessage("Assistant", body, active_repo_id)

        decision = self.router.route(
            user_message, active_repo_id, conversation, self.repos, self.commands
        )

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
            agent_result = self.coding_agent_runner.run_code_change(repo, request)
            body = self._format_coding_agent_result(agent_result)
            self._record_assistant(body)
            return ProcessedMessage("Code change", body, repo.repo_id)

        if decision.action_type == "adapter_change":
            request = decision.arguments[0] if decision.arguments else user_message
            body = self.run_adapter_change(repo, request)
            self._record_assistant(body)
            return ProcessedMessage("Adapter change", body, repo.repo_id)

        command = next(
            (
                command
                for command in self.commands.get(repo.repo_id, [])
                if command.command_name == decision.command_name
            ),
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

    def _format_execution_result(self, result: ExecutionResult) -> str:
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

    def _format_coding_agent_result(self, result: CodingAgentResult) -> str:
        header = (
            f"Repo: {result.repo_id}\n"
            f"Target: {result.target_kind}\n"
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

    def run_scheduled_jobs(self) -> list[ExecutionResult]:
        return self.scheduler.run_all(self.repos, self.commands)

    def init_managed_repo(self, path: str, name: str) -> str:
        scaffold_managed_repo(Path(path), name, now_iso().split("T")[0])
        return f"Initialized managed repo at {path}"

    def register_repo(
        self,
        path: str,
        *,
        name: str | None = None,
        classification: RepoClassification = "integrated",
    ) -> RepoRecord:
        repo_path = Path(path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repo path does not exist: {repo_path}")
        if not (repo_path / "justfile").exists():
            raise ValueError(f"Repo path does not contain a justfile: {repo_path}")

        add_repo_config(path=str(repo_path), name=name, classification=classification)
        self.config = load_config()
        self.registry = Registry(self.config, JustfileParser())
        self.coding_agent_runner = CodingAgentRunner(
            self.config, self.session_registry, self.activity_store
        )
        self.repos, self.commands = self.registry.load()

        registered = next(
            (repo for repo in self.repos if Path(repo.path).resolve() == repo_path), None
        )
        if registered is None:
            raise RuntimeError(f"Repo registration completed but repo was not loaded: {repo_path}")
        return registered

    def get_coding_agent_activity(self) -> CodingAgentActivitySnapshot | None:
        return self.activity_store.get_current()

    def review_usage(self) -> tuple[str, str]:
        bundle, path = self.usage_review_service.build_and_write_bundle()
        lines = [
            f"Bundle: {path}",
            f"Window: {bundle.window_summary}",
            f"Conversation id: {bundle.conversation_id or 'unknown'}",
            f"Activity entries: {len(bundle.activity_entries)}",
        ]
        if bundle.activity_log_refs:
            lines.append("Activity logs:")
            lines.extend(f"- {item}" for item in bundle.activity_log_refs)
        if bundle.notes:
            lines.append("Notes:")
            lines.extend(f"- {item}" for item in bundle.notes)
        return "\n".join(lines), str(path)

    def run_adapter_change(self, repo: RepoRecord, request: str) -> str:
        prompt = build_adapter_change_request(
            repo,
            self.adapter_loader.metadata_path(repo.repo_id),
            request,
        )
        result = self.coding_agent_runner.run_code_change(
            build_self_repo_record(),
            prompt,
            target_kind="adapter",
        )
        return self._format_coding_agent_result(result)

    def _maybe_handle_builtin_command(self, user_message: str) -> ProcessedMessage | None:
        lowered = user_message.strip().lower()
        if lowered != "/review-usage":
            return None
        summary, _bundle_path = self.review_usage()
        body = (
            f"Generated a usage review bundle for this installation.\n\n{summary}\n\n"
            "Use this bundle when working on the youbot repo so coding changes can "
            "be informed by real usage."
        )
        return ProcessedMessage("Usage review", body, self.active_repo_id)
