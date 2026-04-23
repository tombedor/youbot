from __future__ import annotations

from pathlib import Path

from youbot.config import REPO_ROOT
from youbot.models import RepoRecord


def build_self_repo_record() -> RepoRecord:
    return RepoRecord(
        repo_id="youbot",
        name="youbot",
        path=str(REPO_ROOT),
        classification="managed",
        status="ready",
        purpose_summary="Repo-first conversational TUI orchestrator.",
    )


def build_adapter_change_request(
    repo: RepoRecord,
    adapter_metadata_path: Path,
    request: str,
) -> str:
    return (
        "You are editing the youbot-owned adapter/view layer.\n\n"
        f"Target integrated repo: {repo.repo_id}\n"
        f"Child repo path: {repo.path}\n"
        f"Adapter metadata path: {adapter_metadata_path}\n"
        f"Youbot repo path: {REPO_ROOT}\n\n"
        "Default behavior:\n"
        "- Edit the youbot adapter/view behavior for this repo.\n"
        "- Do not edit the child repo unless the request explicitly requires child-repo changes.\n"
        "- Prefer adapter metadata or youbot UI/rendering code changes when possible.\n"
        "- Keep the selected-repo workspace reloadable after the change.\n\n"
        f"Requested change:\n{request}"
    )
