from __future__ import annotations

from collections.abc import Callable

from youbot.adapter_change import build_adapter_change_request, build_self_repo_record
from youbot.adapters import AdapterLoader
from youbot.coding_agent_runner import CodingAgentRunner
from youbot.coding_agent_sessions import CodingAgentSessionRegistry
from youbot.executor import Executor
from youbot.models import CommandRecord, RepoRecord


class ToolCallHandler:
    def __init__(
        self,
        *,
        repos_provider: Callable[[], list[RepoRecord]],
        get_repo: Callable[[str], RepoRecord | None],
        get_commands: Callable[[str], list[CommandRecord]],
        session_registry: CodingAgentSessionRegistry,
        executor: Executor,
        coding_agent_runner: CodingAgentRunner,
        adapter_loader: AdapterLoader,
    ) -> None:
        self._repos_provider = repos_provider
        self._get_repo = get_repo
        self._get_commands = get_commands
        self._session_registry = session_registry
        self._executor = executor
        self._coding_agent_runner = coding_agent_runner
        self._adapter_loader = adapter_loader

    def handle(self, name: str, arguments: dict) -> dict:
        handlers = {
            "list_repos": lambda: self._list_repos(),
            "get_repo_overview": lambda: self._get_repo_overview(arguments["repo_id"]),
            "list_repo_commands": lambda: self._list_repo_commands(arguments["repo_id"]),
            "run_repo_command": lambda: self._run_repo_command(
                arguments["repo_id"],
                arguments["command_name"],
                arguments.get("arguments", []),
            ),
            "run_code_change": lambda: self._run_code_change(
                arguments["repo_id"], arguments["request"]
            ),
            "run_adapter_change": lambda: self._run_adapter_change(
                arguments["repo_id"], arguments["request"]
            ),
        }
        handler = handlers.get(name)
        return {"error": f"Unknown tool {name}"} if handler is None else handler()

    def _list_repos(self) -> dict:
        return {
            "repos": [
                {
                    "repo_id": repo.repo_id,
                    "name": repo.name,
                    "path": repo.path,
                    "status": repo.status,
                }
                for repo in self._repos_provider()
            ]
        }

    def _get_repo_overview(self, repo_id: str) -> dict:
        repo = self._get_repo(repo_id)
        if repo is None:
            return {"error": f"Unknown repo {repo_id}"}
        session_ref = self._session_registry.get_session(repo.repo_id)
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

    def _list_repo_commands(self, repo_id: str) -> dict:
        return {
            "repo_id": repo_id,
            "commands": [
                {
                    "command_name": command.command_name,
                    "description": command.description,
                }
                for command in self._get_commands(repo_id)
            ],
        }

    def _run_repo_command(
        self,
        repo_id: str,
        command_name: str,
        arguments: list[str],
    ) -> dict:
        repo = self._get_repo(repo_id)
        if repo is None:
            return {"error": f"Unknown repo {repo_id}"}
        command = next(
            (
                item
                for item in self._get_commands(repo.repo_id)
                if item.command_name == command_name
            ),
            None,
        )
        if command is None:
            return {"error": f"Unknown command {command_name} for repo {repo.repo_id}"}
        result = self._executor.run(repo, command, arguments)
        return {
            "repo_id": repo.repo_id,
            "command_name": command.command_name,
            "exit_code": result.exit_code,
            "stdout_preview": result.stdout[:2000],
            "stderr_preview": result.stderr[:2000],
        }

    def _run_code_change(self, repo_id: str, request: str) -> dict:
        repo = self._get_repo(repo_id)
        if repo is None:
            return {"error": f"Unknown repo {repo_id}"}
        result = self._coding_agent_runner.run_code_change(repo, request)
        return {
            "repo_id": repo.repo_id,
            "target_kind": result.target_kind,
            "backend": result.backend_name,
            "session_id": result.session_id,
            "exit_code": result.exit_code,
            "stdout_preview": result.stdout[:2000],
            "stderr_preview": result.stderr[:2000],
        }

    def _run_adapter_change(self, repo_id: str, request: str) -> dict:
        repo = self._get_repo(repo_id)
        if repo is None:
            return {"error": f"Unknown repo {repo_id}"}
        result = self._coding_agent_runner.run_code_change(
            build_self_repo_record(),
            build_adapter_change_request(
                repo,
                self._adapter_loader.metadata_path(repo.repo_id),
                request,
            ),
            target_kind="adapter",
        )
        return {
            "repo_id": repo.repo_id,
            "target_kind": result.target_kind,
            "backend": result.backend_name,
            "session_id": result.session_id,
            "exit_code": result.exit_code,
            "stdout_preview": result.stdout[:2000],
            "stderr_preview": result.stderr[:2000],
        }
