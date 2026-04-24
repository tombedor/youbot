from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from youbot.state.models import Project

if TYPE_CHECKING:
    from youbot.tui.views.add_repo_view import AddRepoView


class AddRepoController:
    def __init__(self, view: "AddRepoView") -> None:
        self._view = view

    def submit(self) -> None:
        from textual.widgets import Input, Select

        name = self._view.query_one("#name-input", Input).value.strip()
        path_str = self._view.query_one("#path-input", Input).value.strip()
        merge = self._view.query_one("#merge-select", Select).value

        if not name or not path_str:
            return

        path = Path(path_str).expanduser().resolve()
        project = Project(name=name, path=path, merge_behavior=merge)  # type: ignore[arg-type]

        app = self._view.app  # type: ignore[attr-defined]
        app.registry.add(project)
        self._view.app.pop_screen()
