from __future__ import annotations

from typing import TYPE_CHECKING

from youbot.state.task_repository import TaskRepository

if TYPE_CHECKING:
    from youbot.tui.views.task_view import TaskView


class TaskController:
    def __init__(self, view: "TaskView") -> None:
        self._view = view

    def _task_repo(self) -> TaskRepository:
        app = self._view.app  # type: ignore[attr-defined]
        return TaskRepository(self._view.project.name, app.registry)

    def refresh(self) -> None:
        task = self._task_repo().get(self._view.task.id) or self._view.task
        self._view.task = task
        self._view.set_sessions(task)

    def enter_live_session(self) -> None:
        app = self._view.app  # type: ignore[attr-defined]
        agent = app.config.default_coding_agent
        task = self._view.task
        agent_session = app.session_manager.start_session(
            self._view.project.name,
            self._view.project.path,
            task,
            agent,
            background=False,
        )
        if task.session_for(agent) is None:
            task.sessions.append(agent_session)
            self._task_repo().update(task)
        app.session_manager.attach_session(agent_session)

    def start_background_session(self) -> None:
        app = self._view.app  # type: ignore[attr-defined]
        agent = app.config.default_coding_agent
        task = self._view.task
        agent_session = app.session_manager.start_session(
            self._view.project.name,
            self._view.project.path,
            task,
            agent,
            background=True,
        )
        if task.session_for(agent) is None:
            task.sessions.append(agent_session)
            self._task_repo().update(task)
        self.refresh()
