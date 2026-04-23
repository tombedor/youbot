from __future__ import annotations

from youbot.models import CommandRecord, ConversationRecord, RepoRecord, RouteDecision
from youbot.routing_rules import (
    CODE_CHANGE_WORDS,
    desired_fallback_command,
    infer_arguments,
    looks_like_adapter_change,
    select_command,
    select_repo,
)


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
        repo_id = active_repo_id or select_repo(lowered, repos)
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
        if not looks_like_adapter_change(lowered):
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
            command = select_command(lowered, commands)
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
            arguments=infer_arguments(command.command_name, lowered),
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

    def _fallback_command(
        self, repo_id: str, lowered: str, commands: list[CommandRecord]
    ) -> CommandRecord | None:
        desired = desired_fallback_command(repo_id, lowered)
        if desired is None:
            return None
        for command in commands:
            if command.command_name == desired:
                return command
        return None
