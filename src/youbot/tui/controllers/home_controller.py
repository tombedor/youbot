from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from youbot.tui.views.home_view import HomeView


class HomeController:
    def __init__(self, view: "HomeView") -> None:
        self._view = view

    async def refresh(self) -> None:
        registry = self._view.app.registry  # type: ignore[attr-defined]
        await self._view.set_projects(registry.all())

    def open_project(self, project: object) -> None:
        from youbot.tui.views.project_detail_view import ProjectDetailView

        self._view.app.push_screen(ProjectDetailView(project))  # type: ignore[arg-type]

    def add_repo(self) -> None:
        from youbot.tui.views.add_repo_view import AddRepoView

        self._view.app.push_screen(AddRepoView())
