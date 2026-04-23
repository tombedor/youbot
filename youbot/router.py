from __future__ import annotations

import re

from youbot.models import CommandRecord, ConversationRecord, RepoRecord, RouteDecision

TOKEN_RE = re.compile(r"[a-z0-9_-]+")


class Router:
    def route(
        self,
        user_message: str,
        active_repo_id: str | None,
        conversation: ConversationRecord,
        repos: list[RepoRecord],
        commands: dict[str, list[CommandRecord]],
    ) -> RouteDecision:
        _ = conversation
        lowered = user_message.lower()
        if lowered.startswith("/code "):
            repo_id = active_repo_id or self._select_repo(lowered, repos)
            return RouteDecision(
                repo_id=repo_id,
                action_type="code_change",
                command_name=None,
                arguments=[user_message[len("/code ") :].strip()],
                reasoning_summary="Explicit code-change request.",
                confidence=0.95,
            )

        if self._looks_like_adapter_change(lowered):
            repo_id = active_repo_id or self._select_repo(lowered, repos)
            return RouteDecision(
                repo_id=repo_id,
                action_type="adapter_change",
                command_name=None,
                arguments=[user_message],
                reasoning_summary=(
                    "Request appears to target the youbot-owned repo view or adapter."
                ),
                confidence=0.8,
            )

        repo_id = active_repo_id or self._select_repo(lowered, repos)
        if repo_id is None:
            return RouteDecision(
                repo_id=None,
                action_type="clarify",
                command_name=None,
                arguments=[],
                reasoning_summary="Could not determine a target repo.",
                confidence=0.2,
            )

        fallback = self._fallback_command(repo_id, lowered, commands.get(repo_id, []))
        if fallback is not None:
            return RouteDecision(
                repo_id=repo_id,
                action_type="command",
                command_name=fallback.command_name,
                arguments=self._infer_arguments(fallback.command_name, lowered),
                reasoning_summary=f"Applied repo fallback to {fallback.command_name}.",
                confidence=0.8,
            )

        command_match = self._select_command(lowered, commands.get(repo_id, []))
        if command_match is not None:
            return RouteDecision(
                repo_id=repo_id,
                action_type="command",
                command_name=command_match.command_name,
                arguments=self._infer_arguments(command_match.command_name, lowered),
                reasoning_summary=f"Matched command {command_match.command_name}.",
                confidence=0.9,
            )

        if any(
            word in lowered
            for word in ("add ", "update ", "create ", "change ", "implement ", "edit ")
        ):
            return RouteDecision(
                repo_id=repo_id,
                action_type="code_change",
                command_name=None,
                arguments=[],
                reasoning_summary="Language suggests a code change instead of an existing command.",
                confidence=0.7,
            )

        return RouteDecision(
            repo_id=repo_id,
            action_type="clarify",
            command_name=None,
            arguments=[],
            reasoning_summary="Repo selected but no clear command matched.",
            confidence=0.4,
        )

    def _select_repo(self, lowered: str, repos: list[RepoRecord]) -> str | None:
        for repo in repos:
            if repo.repo_id.replace("_", "-") in lowered or repo.name.replace("_", "-") in lowered:
                return repo.repo_id
        if any(word in lowered for word in ("task", "calendar", "linear")):
            return "life_admin"
        if any(
            word in lowered
            for word in ("job", "pipeline", "resume", "opening", "apply", "netflix", "cursor")
        ):
            return "job_search"
        if any(
            word in lowered
            for word in ("trade", "market", "spotify", "nfl", "research", "position")
        ):
            return "trader-bot"
        return None

    def _select_command(self, lowered: str, commands: list[CommandRecord]) -> CommandRecord | None:
        normalized_words = set(TOKEN_RE.findall(lowered))
        for command in commands:
            command_tokens = set(command.command_name.replace("-", "_").split("_"))
            if command.command_name in lowered or command_tokens <= normalized_words:
                return command
        return None

    def _fallback_command(
        self, repo_id: str, lowered: str, commands: list[CommandRecord]
    ) -> CommandRecord | None:
        desired = None
        if repo_id == "life_admin":
            if "task" in lowered:
                desired = "task-list"
            elif "calendar" in lowered or "agenda" in lowered or "today" in lowered:
                desired = "cal-today"
        elif repo_id == "job_search":
            if "pipeline" in lowered or "status" in lowered:
                desired = "pipeline-status"
            elif "next" in lowered or "action" in lowered:
                desired = "next-actions"
            elif "openings" in lowered or "jobs" in lowered or "roles" in lowered:
                desired = "active-openings"
        elif repo_id == "trader-bot":
            if "program" in lowered:
                desired = "research-program"
            elif "findings" in lowered or "strategies" in lowered:
                desired = "research-findings"
            elif "datasets" in lowered:
                desired = "list-datasets"
        if desired is None:
            return None
        for command in commands:
            if command.command_name == desired:
                return command
        return None

    def _infer_arguments(self, command_name: str, lowered: str) -> list[str]:
        if command_name == "task-list":
            match = re.search(r"\b(\d+)\b", lowered)
            return [match.group(1)] if match is not None else ["20"]
        if command_name == "search-action-items":
            tokens = [
                token
                for token in TOKEN_RE.findall(lowered)
                if token not in {"search", "action", "items"}
            ]
            return [" ".join(tokens)] if tokens else [lowered]
        return []

    def _looks_like_adapter_change(self, lowered: str) -> bool:
        ui_tokens = (
            "view",
            "workspace",
            "panel",
            "layout",
            "render",
            "rendering",
            "adapter",
            "quick action",
            "header",
            "display",
            "sort visible",
            "filter visible",
            "inside youbot",
            "in youbot",
        )
        change_tokens = ("change", "update", "edit", "make", "show", "reorder", "move", "hide")
        return any(token in lowered for token in ui_tokens) and any(
            token in lowered for token in change_tokens
        )
