from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, ListItem, ListView, RichLog, Static
from rich.markdown import Markdown
from rich.rule import Rule
from rich.panel import Panel
from rich.text import Text

from youbot.controller import AppController


class RepoListItem(ListItem):
    def __init__(self, repo_id: str, label: str) -> None:
        self.repo_id = repo_id
        super().__init__(Static(label))


class YoubotApp(App[None]):
    CSS = """
    Screen {
      layout: vertical;
    }

    #body {
      height: 1fr;
    }

    #sidebar {
      width: 30;
      border: round $accent;
      background: $panel-darken-1;
      padding: 1;
      margin-right: 1;
    }

    #main {
      padding: 0;
    }

    .section-title {
      height: auto;
      padding: 0 0 1 0;
      text-style: bold;
      color: $text-muted;
    }

    #repo-shell {
      border: round green;
      background: $boost;
      padding: 1;
      margin-bottom: 1;
    }

    #repo-view {
      height: 8;
      border: none;
      background: transparent;
      overflow: auto;
    }

    #chat-shell {
      height: 1fr;
      border: round blue;
      background: $surface-darken-1;
      padding: 1;
      margin-bottom: 1;
    }

    #conversation-title {
      color: $text;
    }

    #conversation {
      height: 1fr;
      border: none;
      background: transparent;
    }

    #processing-indicator {
      height: auto;
      padding: 0 0 1 0;
      color: $text-muted;
    }

    #composer-shell {
      border: round yellow;
      background: $panel;
      padding: 1;
    }
    """

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
                    yield Static("", id="repo-view")
                with Vertical(id="chat-shell"):
                    yield Static("Assistant", id="conversation-title", classes="section-title")
                    yield Static("", id="processing-indicator")
                    yield RichLog(id="conversation", wrap=True, markup=False)
                with Vertical(id="composer-shell"):
                    yield Static("Ask", id="composer-title", classes="section-title")
                    yield Input(placeholder="Ask youbot to run a command or use /code ...", id="input")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(0.12, self._advance_processing_indicator)
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        self._sync_processing_ui()

    def action_reload_repos(self) -> None:
        self.controller = AppController()
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        self._sync_processing_ui()

    def action_clear_conversation(self) -> None:
        self.controller.conversation_store.clear_conversation()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        self._sync_processing_ui()

    @on(ListView.Selected, "#repo-list")
    def on_repo_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, RepoListItem):
            self.active_repo_id = event.item.repo_id
            self.controller.set_active_repo(self.active_repo_id)
            self._render_repo_view()
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
            self.call_from_thread(self._append_result, "Error", f"Processing failed.\n\n```\n{exc}\n```")
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

    def _refresh_repo_list(self) -> None:
        repo_list = self.query_one("#repo-list", ListView)
        repo_list.clear()
        for repo in self.controller.repos:
            label = repo.repo_id if repo.status == "ready" else f"{repo.repo_id} [{repo.status}]"
            item = RepoListItem(repo.repo_id, label)
            repo_list.append(item)
        if self.active_repo_id is not None:
            items = list(repo_list.children)
            for index, item in enumerate(items):
                if isinstance(item, RepoListItem) and item.repo_id == self.active_repo_id:
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
        if self.active_repo_id is None:
            panel.update(
                Panel(
                    "No repo selected.\n\n"
                    "Select a repo in the sidebar to open its workspace.\n"
                    "You can still chat globally and let routing choose a repo.",
                    title="Global Workspace",
                    border_style="green",
                )
            )
            return

        repo = self.controller.get_repo(self.active_repo_id)
        if repo is None:
            panel.update(Panel(f"Focused repo {self.active_repo_id!r} is not available.", title="Repo Workspace"))
            return
        panel.update(self._repo_view_cache.get(repo.repo_id, Panel(f"Loading overview for {repo.repo_id}...", title="Repo Workspace")))

    def _update_scope_layout(self) -> None:
        repo_shell = self.query_one("#repo-shell", Vertical)
        chat_shell = self.query_one("#chat-shell", Vertical)
        if self.active_repo_id is None:
            repo_shell.styles.height = 8
            chat_shell.styles.height = "1fr"
        else:
            repo_shell.styles.height = "1fr"
            chat_shell.styles.height = 12
