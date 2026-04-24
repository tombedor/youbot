from __future__ import annotations

from typing import Callable

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label


class NewTaskView(Screen[None]):
    BINDINGS = [("escape", "go_back", "Cancel")]

    def __init__(self, on_create: Callable[[str], None]) -> None:
        super().__init__()
        self._on_create = on_create

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Task title:")
        yield Input(placeholder="Describe the task...", id="task-title-input")
        yield Button("Create", id="create-btn", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        title = self.query_one("#task-title-input", Input).value.strip()
        if title:
            self._on_create(title)
            self.app.pop_screen()

    def action_go_back(self) -> None:
        self.app.pop_screen()
