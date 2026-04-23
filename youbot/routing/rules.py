from __future__ import annotations

import re

from youbot.core.models import CommandRecord, RepoRecord

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
REPO_FALLBACK_COMMANDS: dict[str, tuple[tuple[str, str], ...]] = {
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


def select_repo(lowered: str, repos: list[RepoRecord]) -> str | None:
    for repo in repos:
        if repo.repo_id.replace("_", "-") in lowered or repo.name.replace("_", "-") in lowered:
            return repo.repo_id
    for repo_id, keywords in REPO_KEYWORDS.items():
        if any(word in lowered for word in keywords):
            return repo_id
    return None


def select_command(lowered: str, commands: list[CommandRecord]) -> CommandRecord | None:
    normalized_words = set(TOKEN_RE.findall(lowered))
    for command in commands:
        command_tokens = set(command.command_name.replace("-", "_").split("_"))
        if command.command_name in lowered or command_tokens <= normalized_words:
            return command
    return None


def desired_fallback_command(repo_id: str, lowered: str) -> str | None:
    for token, command_name in REPO_FALLBACK_COMMANDS.get(repo_id, ()):
        if token in lowered:
            return command_name
    return None


def infer_arguments(command_name: str, lowered: str) -> list[str]:
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


def looks_like_adapter_change(lowered: str) -> bool:
    return any(token in lowered for token in ADAPTER_UI_TOKENS) and any(
        token in lowered for token in ADAPTER_CHANGE_TOKENS
    )
