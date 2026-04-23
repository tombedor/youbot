from __future__ import annotations

from collections.abc import Callable

from youbot.adapters.change import build_adapter_change_request, build_self_repo_record
from youbot.adapters.loader import AdapterLoader
from youbot.agents.runner import CodingAgentRunner
from youbot.agents.sessions import CodingAgentSessionRegistry
from youbot.core.executor import Executor
from youbot.core.models import CommandRecord, RepoRecord

ToolResult = dict[str, object]


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

    def handle(self, name: str, arguments: dict[str, object]) -> ToolResult:
        if name == "list_repos":
            return self._list_repos()
        if name == "get_repo_overview":
            return self._get_repo_overview(str(arguments["repo_id"]))
        if name == "list_repo_commands":
            return self._list_repo_commands(str(arguments["repo_id"]))
        if name == "run_repo_command":
            raw = arguments.get("arguments")
            extra = [str(a) for a in raw] if isinstance(raw, list) else []
            return self._run_repo_command(
                str(arguments["repo_id"]), str(arguments["command_name"]), extra
            )
        if name == "run_code_change":
            return self._run_code_change(str(arguments["repo_id"]), str(arguments["request"]))
        if name == "run_adapter_change":
            return self._run_adapter_change(str(arguments["repo_id"]), str(arguments["request"]))
        return {"error": f"Unknown tool {name}"}

    def _list_repos(self) -> ToolResult:
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

    def _get_repo_overview(self, repo_id: str) -> ToolResult:
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

    def _list_repo_commands(self, repo_id: str) -> ToolResult:
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
    ) -> ToolResult:
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

    def _run_code_change(self, repo_id: str, request: str) -> ToolResult:
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

    def _run_adapter_change(self, repo_id: str, request: str) -> ToolResult:
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
