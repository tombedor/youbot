from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select

from youbot.state.models import MergeBehavior
from youbot.tui.controllers.add_repo_controller import AddRepoController


class AddRepoView(Screen[None]):
    BINDINGS = [("escape", "go_back", "Cancel")]

    def __init__(self) -> None:
        super().__init__()
        self._controller = AddRepoController(self)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Add a project")
        yield Label("Project name:")
        yield Input(placeholder="my-project", id="name-input")
        yield Label("Path to repo:")
        yield Input(placeholder="~/development/my-project", id="path-input")
        yield Label("Merge behavior:")
        yield Select(
            [("Open PR", MergeBehavior.OPEN_PR), ("Auto-merge", MergeBehavior.AUTO_MERGE)],
            id="merge-select",
            value=MergeBehavior.OPEN_PR,
        )
        yield Button("Add Project", id="add-btn", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self._controller.submit()

    def action_go_back(self) -> None:
        self.app.pop_screen()
