from __future__ import annotations

import re

from youbot.models import CommandRecord, ConversationRecord, RepoRecord, RouteDecision

TOKEN_RE = re.compile(r"[a-z0-9_-]+")
CODE_CHANGE_WORDS = ("add ", "update ", "create ", "change ", "implement ", "edit ")
ADAPTER_UI_TOKENS = (
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
ADAPTER_CHANGE_TOKENS = ("change", "update", "edit", "make", "show", "reorder", "move", "hide")
REPO_KEYWORDS: dict[str, tuple[str, ...]] = {
    "life_admin": ("task", "calendar", "linear"),
    "job_search": ("job", "pipeline", "resume", "opening", "apply", "netflix", "cursor"),
    "trader-bot": ("trade", "market", "spotify", "nfl", "research", "position"),
}
REPO_FALLBACK_COMMANDS: dict[str, tuple[tuple[str, ...], str]] = {
    "life_admin": (
        ("task", "task-list"),
        ("calendar", "cal-today"),
        ("agenda", "cal-today"),
        ("today", "cal-today"),
    ),
    "job_search": (
        ("pipeline", "pipeline-status"),
        ("status", "pipeline-status"),
        ("next", "next-actions"),
        ("action", "next-actions"),
        ("openings", "active-openings"),
        ("jobs", "active-openings"),
        ("roles", "active-openings"),
    ),
    "trader-bot": (
        ("program", "research-program"),
        ("findings", "research-findings"),
        ("strategies", "research-findings"),
        ("datasets", "list-datasets"),
    ),
}


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
        repo_id = active_repo_id or self._select_repo(lowered, repos)
        explicit_code = self._explicit_code_change(user_message, lowered, repo_id)
        if explicit_code is not None:
            return explicit_code
        adapter_change = self._adapter_change(user_message, lowered, repo_id)
        if adapter_change is not None:
            return adapter_change
        if repo_id is None:
            return RouteDecision(
                repo_id=None,
                action_type="clarify",
                command_name=None,
                arguments=[],
                reasoning_summary="Could not determine a target repo.",
                confidence=0.2,
            )

        command_decision = self._route_command(repo_id, lowered, commands.get(repo_id, []))
        if command_decision is not None:
            return command_decision
        if any(word in lowered for word in CODE_CHANGE_WORDS):
            return self._decision(
                repo_id,
                "code_change",
                reasoning_summary="Language suggests a code change instead of an existing command.",
                confidence=0.7,
            )
        return self._decision(
            repo_id,
            "clarify",
            reasoning_summary="Repo selected but no clear command matched.",
            confidence=0.4,
        )

    def _explicit_code_change(
        self,
        user_message: str,
        lowered: str,
        repo_id: str | None,
    ) -> RouteDecision | None:
        if not lowered.startswith("/code "):
            return None
        return self._decision(
            repo_id,
            "code_change",
            arguments=[user_message[len("/code ") :].strip()],
            reasoning_summary="Explicit code-change request.",
            confidence=0.95,
        )

    def _adapter_change(
        self,
        user_message: str,
        lowered: str,
        repo_id: str | None,
    ) -> RouteDecision | None:
        if not self._looks_like_adapter_change(lowered):
            return None
        return self._decision(
            repo_id,
            "adapter_change",
            arguments=[user_message],
            reasoning_summary="Request appears to target the youbot-owned repo view or adapter.",
            confidence=0.8,
        )

    def _route_command(
        self,
        repo_id: str,
        lowered: str,
        commands: list[CommandRecord],
    ) -> RouteDecision | None:
        command = self._fallback_command(repo_id, lowered, commands)
        reasoning = None
        confidence = 0.8
        if command is None:
            command = self._select_command(lowered, commands)
            reasoning = None if command is None else f"Matched command {command.command_name}."
            confidence = 0.9
        else:
            reasoning = f"Applied repo fallback to {command.command_name}."
        if command is None:
            return None
        return self._decision(
            repo_id,
            "command",
            command_name=command.command_name,
            arguments=self._infer_arguments(command.command_name, lowered),
            reasoning_summary=reasoning,
            confidence=confidence,
        )

    def _decision(
        self,
        repo_id: str | None,
        action_type: str,
        *,
        command_name: str | None = None,
        arguments: list[str] | None = None,
        reasoning_summary: str,
        confidence: float,
    ) -> RouteDecision:
        return RouteDecision(
            repo_id=repo_id,
            action_type=action_type,  # type: ignore[arg-type]
            command_name=command_name,
            arguments=[] if arguments is None else arguments,
            reasoning_summary=reasoning_summary,
            confidence=confidence,
        )

    def _select_repo(self, lowered: str, repos: list[RepoRecord]) -> str | None:
        for repo in repos:
            if repo.repo_id.replace("_", "-") in lowered or repo.name.replace("_", "-") in lowered:
                return repo.repo_id
        for repo_id, keywords in REPO_KEYWORDS.items():
            if any(word in lowered for word in keywords):
                return repo_id
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
        desired = self._desired_fallback_command(repo_id, lowered)
        if desired is None:
            return None
        for command in commands:
            if command.command_name == desired:
                return command
        return None

    def _desired_fallback_command(self, repo_id: str, lowered: str) -> str | None:
        for token, command_name in REPO_FALLBACK_COMMANDS.get(repo_id, ()):
            if token in lowered:
                return command_name
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
        return any(token in lowered for token in ADAPTER_UI_TOKENS) and any(
            token in lowered for token in ADAPTER_CHANGE_TOKENS
        )
