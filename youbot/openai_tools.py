from __future__ import annotations

from typing import Any

from youbot.models import CommandRecord, RepoRecord


def build_tool_specs(
    repos: list[RepoRecord],
    commands: dict[str, list[CommandRecord]],
) -> list[dict[str, Any]]:
    repo_ids = [repo.repo_id for repo in repos]
    all_commands = sorted(
        {command.command_name for items in commands.values() for command in items}
    )
    return [
        _function_tool("list_repos", "List the repos currently registered in youbot."),
        _repo_tool(
            "get_repo_overview",
            "Get metadata, adapter state, and coding-agent session info for a repo.",
            repo_ids,
        ),
        _repo_tool(
            "list_repo_commands",
            "List the discovered just commands for a repo.",
            repo_ids,
        ),
        _command_tool(repo_ids, all_commands),
        _request_tool(
            "run_code_change",
            (
                "Run a code-change request in a repo through the configured "
                "non-interactive coding-agent backend."
            ),
            repo_ids,
        ),
        _request_tool(
            "run_adapter_change",
            (
                "Update the youbot-owned adapter/view for how a repo is presented "
                "in the selected-repo workspace."
            ),
            repo_ids,
        ),
    ]


def _function_tool(
    name: str,
    description: str,
    properties: dict[str, Any] | None = None,
    required: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties or {},
            "required": required or [],
            "additionalProperties": False,
        },
    }


def _repo_tool(name: str, description: str, repo_ids: list[str]) -> dict[str, Any]:
    return _function_tool(
        name,
        description,
        properties={"repo_id": {"type": "string", "enum": repo_ids}},
        required=["repo_id"],
    )


def _command_tool(repo_ids: list[str], all_commands: list[str]) -> dict[str, Any]:
    return _function_tool(
        "run_repo_command",
        "Run a discovered just command in a repo.",
        properties={
            "repo_id": {"type": "string", "enum": repo_ids},
            "command_name": {"type": "string", "enum": all_commands},
            "arguments": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
        },
        required=["repo_id", "command_name"],
    )


def _request_tool(name: str, description: str, repo_ids: list[str]) -> dict[str, Any]:
    return _function_tool(
        name,
        description,
        properties={
            "repo_id": {"type": "string", "enum": repo_ids},
            "request": {"type": "string"},
        },
        required=["repo_id", "request"],
    )
