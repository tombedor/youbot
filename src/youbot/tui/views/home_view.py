from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from youbot.state.models import Project
from youbot.tui.controllers.home_controller import HomeController


class HomeView(Screen[None]):
    BINDINGS = [
        ("a", "add_repo", "Add Repo"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._controller = HomeController(self)
        self._project_list: list[Project] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="project-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self._controller.refresh()

    async def on_screen_resume(self) -> None:
        await self._controller.refresh()

    async def set_projects(self, projects: list[Project]) -> None:
        self._project_list = projects
        lv = self.query_one("#project-list", ListView)
        await lv.clear()
        if not projects:
            await lv.append(ListItem(Label("No projects yet. Press 'a' to add one.")))
            return
        for project in projects:
            await lv.append(ListItem(Label(project.name)))
        lv.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        lv = self.query_one("#project-list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self._project_list):
            self._controller.open_project(self._project_list[lv.index])

    def action_add_repo(self) -> None:
        self._controller.add_repo()

    def action_quit(self) -> None:
        self.app.exit()
