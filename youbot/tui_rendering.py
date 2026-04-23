from __future__ import annotations

from rich.panel import Panel
from textual.widgets import ListItem, Static


class RepoListItem(ListItem):
    def __init__(self, repo_id: str, label: str) -> None:
        self.repo_id = repo_id
        super().__init__(Static(label))


def build_activity_panel(snapshot) -> Panel:
    if snapshot is None:
        return Panel(
            "No coding-agent activity yet.\n\n"
            "Code and adapter changes will stream progress here while they run.",
            title="Activity",
            border_style="magenta",
        )

    lines = [
        f"Status: {snapshot.status}",
        f"Target repo: {snapshot.repo_id}",
        f"Target kind: {snapshot.target_kind}",
        f"Backend: {snapshot.backend_name}",
        f"Session id: {snapshot.session_id or 'pending'}",
        f"Started: {snapshot.started_at}",
    ]
    if snapshot.finished_at is not None:
        lines.append(f"Finished: {snapshot.finished_at}")
    if snapshot.exit_code is not None:
        lines.append(f"Exit code: {snapshot.exit_code}")
    lines.extend(["", "Recent output:"])
    recent_entries = snapshot.entries[-14:]
    if not recent_entries:
        lines.append("(waiting for agent output)")
    else:
        for entry in recent_entries:
            prefix = {"status": "[status]", "stdout": "[out]", "stderr": "[err]"}[entry.stream]
            lines.append(f"{prefix} {entry.content}")

    return Panel(
        "\n".join(lines),
        title=f"Coding Activity: {snapshot.request_summary[:48]}",
        border_style="magenta",
    )


def build_repo_panel(active_repo_id: str | None, repo, cache: dict[str, object]):
    if active_repo_id is None:
        return Panel(
            "No repo selected.\n\n"
            "Select a repo in the sidebar to open its workspace.\n"
            "You can still chat globally and let routing choose a repo.",
            title="Global Workspace",
            border_style="green",
        )
    if repo is None:
        return Panel(f"Focused repo {active_repo_id!r} is not available.", title="Repo Workspace")
    return cache.get(
        repo.repo_id,
        Panel(f"Loading overview for {repo.repo_id}...", title="Repo Workspace"),
    )


def repo_header(active_repo_id: str | None, repo) -> tuple[str, str]:
    if active_repo_id is None:
        return "Workspace", "Select a repo to open a focused workspace."
    if repo is None:
        return "Workspace", "Focused repo is unavailable."
    return repo.repo_id, repo.purpose_summary or default_repo_subtitle(repo.repo_id)


def scope_heights(active_repo_id: str | None) -> tuple[str | int, str | int]:
    if active_repo_id is None:
        return 8, "1fr"
    return "1fr", 10


def default_repo_subtitle(repo_id: str) -> str:
    fallback = {
        "job_search": "Applications, follow-ups, and top openings.",
        "life_admin": "Priority tasks, admin work, and personal operations.",
        "trader-bot": "Research directions, findings, and trading workflows.",
    }
    return fallback.get(repo_id, "Repo-specific workspace and common actions.")
