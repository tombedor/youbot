from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from youbot.state.models import Project, Task
from youbot.tui.controllers.task_controller import TaskController


class TaskView(Screen[None]):
    BINDINGS = [
        ("l", "live_session", "Live Session"),
        ("b", "background_session", "Background Session"),
        ("escape", "go_back", "Back"),
    ]

    def __init__(self, project: Project, task: Task) -> None:
        super().__init__()
        self.project = project
        self.task = task
        self._controller = TaskController(self)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(f"Task: {self.task.title}", id="task-title")
        yield Label(f"Status: {self.task.status.value}", id="task-status")
        yield Label("Past Sessions:", id="sessions-label")
        yield ListView(id="session-list")
        yield Footer()

    def on_mount(self) -> None:
        self._controller.refresh()

    def set_sessions(self, task: Task) -> None:
        lv = self.query_one("#session-list", ListView)
        lv.clear()
        if not task.sessions:
            lv.append(ListItem(Label("No sessions yet.")))
            return
        for s in task.sessions:
            status = "ACTIVE" if s.active else "inactive"
            summary = f" — {s.summary}" if s.summary else ""
            lv.append(ListItem(Label(f"{s.agent.value} [{status}]{summary}")))

    def action_live_session(self) -> None:
        self._controller.enter_live_session()

    def action_background_session(self) -> None:
        self._controller.start_background_session()

    def action_go_back(self) -> None:
        self.app.pop_screen()
