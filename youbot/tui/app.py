from __future__ import annotations

from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, ListView, RichLog, Static

from youbot.core.controller import AppController
from youbot.core.models import CodingAgentActivitySnapshot
from youbot.tui.layout import APP_CSS
from youbot.tui.rendering import (
    RepoListItem,
    build_activity_panel,
    build_repo_panel,
    repo_header,
    scope_heights,
)


class YoubotApp(App[None]):
    CSS = APP_CSS

    BINDINGS = [
        ("ctrl+r", "reload_repos", "Reload repos"),
        ("ctrl+l", "clear_conversation", "Clear conversation"),
    ]

    active_repo_id: reactive[str | None] = reactive(None)
    is_processing: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.controller = AppController()
        self.active_repo_id = None
        self.is_processing = False
        self._processing_frame = 0
        self._repo_view_cache: dict[str, object] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Repos", classes="section-title")
                yield ListView(id="repo-list")
            with Vertical(id="main"):
                with Vertical(id="repo-shell"):
                    yield Static("Workspace", id="repo-title", classes="section-title")
                    yield Static("Select a repo to open a focused workspace.", id="repo-subtitle")
                    yield Static("", id="repo-view")
                with Vertical(id="chat-shell"):
                    with Horizontal(id="chat-header"):
                        yield Static("Assistant", id="conversation-title", classes="section-title")
                        yield Static("", id="processing-indicator")
                    yield RichLog(id="conversation", wrap=True, markup=False)
                with Vertical(id="activity-shell"):
                    yield Static("Coding Activity", id="activity-title", classes="section-title")
                    yield Static("", id="activity-view")
                with Vertical(id="composer-shell"):
                    yield Input(
                        placeholder="Ask youbot to run a command or use /code ...", id="input"
                    )
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.12, self._advance_processing_indicator)
        self.set_interval(0.35, self._refresh_activity_view)
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._refresh_activity_view()
        self._update_repo_header()
        self._update_scope_layout()
        self._sync_processing_ui()

    def action_reload_repos(self) -> None:
        self.controller = AppController()
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._refresh_activity_view()
        self._update_repo_header()
        self._update_scope_layout()
        self._sync_processing_ui()

    def action_clear_conversation(self) -> None:
        self.controller.conversation_store.clear_conversation()
        self._render_conversation()
        self._render_repo_view()
        self._refresh_activity_view()
        self._update_repo_header()
        self._update_scope_layout()
        self._sync_processing_ui()

    @on(ListView.Selected, "#repo-list")
    def on_repo_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, RepoListItem):
            self.active_repo_id = event.item.repo_id
            self.controller.set_active_repo(self.active_repo_id)
            self._render_repo_view()
            self._update_repo_header()
            self._update_scope_layout()
            self.load_repo_view(self.active_repo_id)

    @on(Input.Submitted, "#input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message or self.is_processing:
            return
        input_widget = self.query_one("#input", Input)
        input_widget.value = ""
        self.query_one("#conversation", RichLog).write(f"> {message}")
        self._set_processing(True)
        self.process_user_message(message)

    @work(thread=True)
    def process_user_message(self, message: str) -> None:
        try:
            processed = self.controller.process_message(message, self.active_repo_id)
        except Exception as exc:
            self.call_from_thread(
                self._append_result, "Error", f"Processing failed.\n\n```\n{exc}\n```"
            )
        else:
            self.call_from_thread(self._append_result, processed.summary, processed.body)
        finally:
            self.call_from_thread(self._set_processing, False)

    def _append_result(self, summary: str, body: str) -> None:
        log = self.query_one("#conversation", RichLog)
        log.write(Rule(summary, style="blue"))
        log.write(Markdown(body))
        if self.active_repo_id is not None:
            self.load_repo_view(self.active_repo_id)
        self._render_repo_view()
        self._refresh_activity_view()
        self._update_scope_layout()

    @work(thread=True)
    def load_repo_view(self, repo_id: str) -> None:
        content = self.controller.build_repo_view(repo_id)
        self.call_from_thread(self._store_repo_view, repo_id, content)

    def _store_repo_view(self, repo_id: str, content: object) -> None:
        self._repo_view_cache[repo_id] = content
        if self.active_repo_id == repo_id:
            self._render_repo_view()

    def _set_processing(self, processing: bool) -> None:
        self.is_processing = processing
        if processing:
            self._processing_frame = 0
        self._sync_processing_ui()

    def _advance_processing_indicator(self) -> None:
        if not self.is_processing:
            return
        self._processing_frame = (self._processing_frame + 1) % 4
        self._sync_processing_ui()

    def _sync_processing_ui(self) -> None:
        indicator = self.query_one("#processing-indicator", Static)
        input_widget = self.query_one("#input", Input)
        if self.is_processing:
            frames = ["|", "/", "-", "\\"]
            indicator.update(f"{frames[self._processing_frame]} Processing message...")
            input_widget.disabled = True
            input_widget.placeholder = "Youbot is working..."
        else:
            indicator.update("")
            input_widget.disabled = False
            input_widget.placeholder = "Ask youbot to run a command or use /code ..."

    def _refresh_activity_view(self) -> None:
        panel = self.query_one("#activity-view", Static)
        snapshot = self.controller.get_coding_agent_activity()
        panel.update(self._build_activity_panel(snapshot))

    def _build_activity_panel(self, snapshot: CodingAgentActivitySnapshot | None) -> Panel:
        return build_activity_panel(snapshot)

    def _refresh_repo_list(self) -> None:
        repo_list = self.query_one("#repo-list", ListView)
        repo_list.clear()
        for repo in self.controller.repos:
            label = repo.repo_id if repo.status == "ready" else f"{repo.repo_id} [{repo.status}]"
            item = RepoListItem(repo.repo_id, label)
            repo_list.append(item)
        if self.active_repo_id is not None:
            items = list(repo_list.children)
            for index, child in enumerate(items):
                if isinstance(child, RepoListItem) and child.repo_id == self.active_repo_id:
                    repo_list.index = index
                    break
        else:
            repo_list.index = None

    def _render_conversation(self) -> None:
        log = self.query_one("#conversation", RichLog)
        log.clear()
        for message in self.controller.conversation_store.get_conversation().messages:
            if message.role == "user":
                log.write(Text(f"You: {message.content}", style="bold"))
            else:
                log.write(Rule(message.role.title(), style="blue"))
                log.write(Markdown(message.content))

    def _render_repo_view(self) -> None:
        panel = self.query_one("#repo-view", Static)
        repo = (
            None if self.active_repo_id is None else self.controller.get_repo(self.active_repo_id)
        )
        panel.update(build_repo_panel(self.active_repo_id, repo, self._repo_view_cache))

    def _update_repo_header(self) -> None:
        title = self.query_one("#repo-title", Static)
        subtitle = self.query_one("#repo-subtitle", Static)
        repo = (
            None if self.active_repo_id is None else self.controller.get_repo(self.active_repo_id)
        )
        title_text, subtitle_text = repo_header(self.active_repo_id, repo)
        title.update(title_text)
        subtitle.update(subtitle_text)

    def _update_scope_layout(self) -> None:
        repo_shell = self.query_one("#repo-shell", Vertical)
        chat_shell = self.query_one("#chat-shell", Vertical)
        repo_height, chat_height = scope_heights(self.active_repo_id)
        repo_shell.styles.height = repo_height
        chat_shell.styles.height = chat_height
