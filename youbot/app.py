from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, ListItem, ListView, RichLog, Static
from rich.markdown import Markdown
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
      padding: 0 1;
      text-style: bold;
      color: $text;
    }

    #repo-shell {
      border: round green;
      background: $boost;
      padding: 0 1 1 1;
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
      padding: 0 1 1 1;
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

    #composer-shell {
      border: round yellow;
      background: $panel;
      padding: 0 1 1 1;
    }

    #status {
      height: auto;
      padding: 0 1;
      color: $text-muted;
    }
    """

    BINDINGS = [
        ("ctrl+r", "reload_repos", "Reload repos"),
        ("ctrl+l", "clear_conversation", "Clear conversation"),
    ]

    active_repo_id: reactive[str | None] = reactive(None)

    def __init__(self) -> None:
        super().__init__()
        self.controller = AppController()
        self.active_repo_id = None
        self._repo_view_cache: dict[str, object] = {}

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Repos", classes="section-title")
                yield ListView(id="repo-list")
            with Vertical(id="main"):
                with Vertical(id="repo-shell"):
                    yield Static("Repo Workspace", id="repo-title", classes="section-title")
                    yield Static("", id="repo-view")
                with Vertical(id="chat-shell"):
                    yield Static("Conversation", id="conversation-title", classes="section-title")
                    yield RichLog(id="conversation", wrap=True, markup=False)
                yield Static("", id="status")
                with Vertical(id="composer-shell"):
                    yield Static("Composer", id="composer-title", classes="section-title")
                    yield Input(placeholder="Ask youbot to run a command or use /code ...", id="input")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        if self.active_repo_id is not None:
            self._update_status(f"Focused repo: {self.active_repo_id}")
        else:
            self._update_status("No repo focused.")

    def action_reload_repos(self) -> None:
        self.controller = AppController()
        self._refresh_repo_list()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        self._update_status("Reloaded repo registry.")

    def action_clear_conversation(self) -> None:
        self.controller.conversation_store.clear_conversation()
        self._render_conversation()
        self._render_repo_view()
        self._update_scope_layout()
        self._update_status("Cleared conversation history.")

    @on(ListView.Selected, "#repo-list")
    def on_repo_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, RepoListItem):
            self.active_repo_id = event.item.repo_id
            self.controller.set_active_repo(self.active_repo_id)
            self._render_repo_view()
            self._update_scope_layout()
            self._update_status(f"Focused repo: {self.active_repo_id}")
            self.load_repo_view(self.active_repo_id)

    @on(Input.Submitted, "#input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        message = event.value.strip()
        if not message:
            return
        input_widget = self.query_one("#input", Input)
        input_widget.value = ""
        self.query_one("#conversation", RichLog).write(f"> {message}")
        self.process_user_message(message)

    @work(thread=True)
    def process_user_message(self, message: str) -> None:
        processed = self.controller.process_message(message, self.active_repo_id)
        self.call_from_thread(self._append_result, processed.summary, processed.body)

    def _append_result(self, summary: str, body: str) -> None:
        log = self.query_one("#conversation", RichLog)
        log.write(Panel(Markdown(body), title=summary, border_style="blue"))
        if self.active_repo_id is not None:
            self.load_repo_view(self.active_repo_id)
        self._render_repo_view()
        self._update_scope_layout()
        self._update_status(summary)

    @work(thread=True)
    def load_repo_view(self, repo_id: str) -> None:
        content = self.controller.build_repo_view(repo_id)
        self.call_from_thread(self._store_repo_view, repo_id, content)

    def _store_repo_view(self, repo_id: str, content: object) -> None:
        self._repo_view_cache[repo_id] = content
        if self.active_repo_id == repo_id:
            self._render_repo_view()

    def _refresh_repo_list(self) -> None:
        repo_list = self.query_one("#repo-list", ListView)
        repo_list.clear()
        for repo in self.controller.repos:
            label = f"{repo.repo_id} [{repo.status}]"
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
                log.write(Text(f"> {message.content}"))
            else:
                log.write(Panel(Markdown(message.content), title=message.role.title(), border_style="blue"))

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

    def _update_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)
