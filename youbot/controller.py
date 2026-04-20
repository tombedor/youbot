from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from youbot.coding_agent_runner import CodingAgentRunner
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.config import AppConfig, load_config, update_last_active_repo
from youbot.conversation_store import ConversationStore
from youbot.executor import Executor
from youbot.justfile_parser import JustfileParser
from youbot.models import CommandRecord, ConversationMessage, RepoRecord
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
        self.registry = Registry(self.config, JustfileParser())
        self.executor = Executor()
        self.router = Router()
        self.coding_agent_runner = CodingAgentRunner(self.config, self.session_registry)
        self.scheduler = Scheduler(self.config, self.executor)
        self.repos, self.commands = self.registry.load()

    def set_active_repo(self, repo_id: str | None) -> None:
        update_last_active_repo(repo_id)

    def get_repo(self, repo_id: str) -> RepoRecord | None:
        for repo in self.repos:
            if repo.repo_id == repo_id:
                return repo
        return None

    def get_commands(self, repo_id: str) -> list[CommandRecord]:
        return self.commands.get(repo_id, [])

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
