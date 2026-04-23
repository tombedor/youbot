from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from youbot.models import CommandRecord, RepoRecord
from youbot.openai_tools import build_tool_specs

INSTRUCTIONS = """
You are the primary orchestrator for Youbot.

Use tool calls to inspect repos and execute actions.
Prefer tool calls over guessing.
Keep user-facing answers concise and practical.
When a repo is selected in the UI, treat it as the default focus but do not ignore
the user's explicit repo mentions.
Do not expose raw backend transcript details unless the user asks for them.
For command execution, summarize the result rather than repeating entire logs verbatim.
For code changes, use the coding-agent tool and summarize what was attempted, the
session id, and whether it succeeded.
When a request is about how a repo appears inside youbot's UI, use the adapter-change
tool instead of editing the child repo.
"""


class OpenAIChatOrchestrator:
    def __init__(self) -> None:
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._model = os.getenv("OPENAI_MODEL", "gpt-5.2")
        self._client = OpenAI(api_key=self._api_key) if self._api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def respond(
        self,
        *,
        user_message: str,
        active_repo_id: str | None,
        repos: list[RepoRecord],
        commands: dict[str, list[CommandRecord]],
        last_response_id: str | None,
        tool_handler,
    ) -> tuple[str, str | None]:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        tools = self._build_tools(repos, commands)
        response = self._client.responses.create(
            model=self._model,
            instructions=self._build_instructions(active_repo_id, repos),
            input=user_message,
            previous_response_id=last_response_id,
            tools=tools,
            parallel_tool_calls=False,
        )

        while True:
            function_calls = [
                item for item in response.output if getattr(item, "type", None) == "function_call"
            ]
            if not function_calls:
                return response.output_text or "No response generated.", response.id

            tool_outputs: list[dict[str, Any]] = []
            for call in function_calls:
                arguments = json.loads(call.arguments or "{}")
                output_payload = tool_handler(call.name, arguments)
                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(output_payload),
                    }
                )

            response = self._client.responses.create(
                model=self._model,
                instructions=self._build_instructions(active_repo_id, repos),
                previous_response_id=response.id,
                input=tool_outputs,
                tools=tools,
                parallel_tool_calls=False,
            )

    def _build_instructions(self, active_repo_id: str | None, repos: list[RepoRecord]) -> str:
        repo_lines = "\n".join(f"- {repo.repo_id}: {repo.path} [{repo.status}]" for repo in repos)
        active = active_repo_id or "none"
        return f"{INSTRUCTIONS}\n\nActive repo focus: {active}\n\nKnown repos:\n{repo_lines}"

    def _build_tools(
        self,
        repos: list[RepoRecord],
        commands: dict[str, list[CommandRecord]],
    ) -> list[dict[str, Any]]:
        return build_tool_specs(repos, commands)
