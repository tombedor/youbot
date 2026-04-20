from __future__ import annotations

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, ListItem, ListView, RichLog, Static

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
      padding: 1;
    }

    #main {
      border: round $accent;
    }

    #repo-view {
      height: 8;
      border: solid $surface;
      padding: 0 1;
      overflow: auto;
    }

    #conversation {
      height: 1fr;
      border: solid $surface;
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

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("Repos")
                yield ListView(id="repo-list")
            with Vertical(id="main"):
                yield Static("", id="repo-view")
                yield RichLog(id="conversation", wrap=True, markup=False)
                yield Static("", id="status")
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
        log.write(f"[{summary}]\n{body}")
        self._render_repo_view()
        self._update_scope_layout()
        self._update_status(summary)

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
            prefix = ">" if message.role == "user" else f"[{message.role}]"
            log.write(f"{prefix} {message.content}")

    def _render_repo_view(self) -> None:
        panel = self.query_one("#repo-view", Static)
        if self.active_repo_id is None:
            panel.update(
                "Global Chat\n\n"
                "No repo selected.\n"
                "Select a repo in the sidebar to open its overview.\n"
                "You can still chat globally and let routing choose a repo."
            )
            return

        repo = self.controller.get_repo(self.active_repo_id)
        if repo is None:
            panel.update(f"Focused repo {self.active_repo_id!r} is not available.")
            return

        commands = self.controller.get_commands(repo.repo_id)
        session_ref = self.controller.session_registry.get_session(repo.repo_id)
        command_lines = [
            f"- {command.command_name}: {command.description or 'No description'}"
            for command in commands[:12]
        ]
        if len(commands) > 12:
            command_lines.append(f"... and {len(commands) - 12} more")

        session_text = (
            "No coding-agent session tracked yet."
            if session_ref is None
            else (
                f"Backend: {session_ref.backend_name}\n"
                f"Kind: {session_ref.session_kind}\n"
                f"Session: {session_ref.session_id}\n"
                f"Status: {session_ref.status}"
            )
        )
        body = (
            f"Repo: {repo.repo_id}\n"
            f"Path: {repo.path}\n"
            f"Status: {repo.status}\n"
            f"Adapter: {repo.adapter_id or 'none'}\n\n"
            "Coding Agent\n"
            f"{session_text}\n\n"
            "Commands\n"
            + ("\n".join(command_lines) if command_lines else "(no commands discovered)")
        )
        panel.update(body)

    def _update_scope_layout(self) -> None:
        repo_view = self.query_one("#repo-view", Static)
        conversation = self.query_one("#conversation", RichLog)
        if self.active_repo_id is None:
            repo_view.styles.height = 8
            conversation.styles.height = "1fr"
        else:
            repo_view.styles.height = "1fr"
            conversation.styles.height = 10

    def _update_status(self, text: str) -> None:
        self.query_one("#status", Static).update(text)
