from __future__ import annotations

from textual.app import App

from youbot.config.app_config import AppConfig
from youbot.notifications.notifier import Notifier
from youbot.session.session_manager import SessionManager
from youbot.session.tmux_client import TmuxClient
from youbot.state.project_registry import ProjectRegistry
from youbot.tui.views.home_view import HomeView


class YoubotApp(App[None]):
    TITLE = "youbot"
    CSS_PATH = None

    def __init__(self) -> None:
        super().__init__()
        self.config = AppConfig.load()
        self.registry = ProjectRegistry()
        self.tmux = TmuxClient()
        self.notifier = Notifier()
        self.session_manager = SessionManager(self.tmux, self.notifier)

    async def on_mount(self) -> None:
        await self.push_screen(HomeView())


def main() -> None:
    YoubotApp().run()
