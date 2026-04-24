from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from youbot.state.models import Project, Task
from youbot.tui.controllers.project_detail_controller import ProjectDetailController


class ProjectDetailView(Screen[None]):
    BINDINGS = [
        ("n", "new_task", "New Task"),
        ("l", "live_session", "Live Session"),
        ("b", "background_session", "Background Session"),
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, project: Project) -> None:
        super().__init__()
        self.project = project
        self._controller = ProjectDetailController(self)
        self._task_list: list[Task] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Project: {self.project.name}", id="project-title")
        yield ListView(id="task-list")
        yield Footer()

    async def on_mount(self) -> None:
        await self._controller.refresh()

    async def on_screen_resume(self) -> None:
        await self._controller.refresh()

    async def set_tasks(self, tasks: list[Task]) -> None:
        self._task_list = tasks
        lv = self.query_one("#task-list", ListView)
        await lv.clear()
        if not tasks:
            await lv.append(ListItem(Label("No tasks yet. Press 'n' to create one.")))
            return
        for task in tasks:
            active = any(s.active for s in task.sessions)
            indicator = " [bg]" if active else ""
            await lv.append(ListItem(Label(f"[{task.status.value}] {task.title}{indicator}")))
        lv.index = 0

    def _highlighted_task(self) -> Task | None:
        lv = self.query_one("#task-list", ListView)
        if lv.index is not None and 0 <= lv.index < len(self._task_list):
            return self._task_list[lv.index]
        return None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        task = self._highlighted_task()
        if task:
            self._controller.open_task(task)

    def action_new_task(self) -> None:
        self._controller.new_task()

    def action_live_session(self) -> None:
        task = self._highlighted_task()
        if task:
            self._controller.enter_live_session(task)

    def action_background_session(self) -> None:
        task = self._highlighted_task()
        if task:
            self._controller.start_background_session(task)

    def action_go_back(self) -> None:
        self.app.pop_screen()
