from __future__ import annotations

from pathlib import Path

import libtmux


class TmuxClient:
    def __init__(self) -> None:
        self._server = libtmux.Server()

    def create_session(self, name: str, working_dir: Path) -> libtmux.Session:
        return self._server.new_session(
            session_name=name,
            start_directory=str(working_dir),
            detach=True,
        )

    def get_session(self, name: str) -> libtmux.Session | None:
        try:
            return self._server.sessions.get(session_name=name)
        except Exception:
            return None

    def session_exists(self, name: str) -> bool:
        return self.get_session(name) is not None

    def list_sessions(self) -> list[libtmux.Session]:
        try:
            return list(self._server.sessions)
        except Exception:
            return []

    def attach_session(self, name: str) -> None:
        session = self.get_session(name)
        if session is None:
            raise ValueError(f"No tmux session named '{name}'")
        session.attach()

    def send_keys(self, name: str, keys: str) -> None:
        session = self.get_session(name)
        if session is None:
            raise ValueError(f"No tmux session named '{name}'")
        pane = session.active_window.active_pane
        pane.send_keys(keys)

    def capture_pane(self, name: str) -> str:
        session = self.get_session(name)
        if session is None:
            return ""
        pane = session.active_window.active_pane
        return "\n".join(pane.capture_pane())

    def kill_session(self, name: str) -> None:
        session = self.get_session(name)
        if session:
            session.kill()

    @staticmethod
    def session_name(project_name: str, task_id: str, agent: str) -> str:
        return f"youbot-{project_name}-{task_id}-{agent}"
