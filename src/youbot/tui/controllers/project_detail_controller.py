from __future__ import annotations

from typing import TYPE_CHECKING

from youbot.state.models import Task
from youbot.state.task_repository import TaskRepository

if TYPE_CHECKING:
    from youbot.tui.views.project_detail_view import ProjectDetailView


class ProjectDetailController:
    def __init__(self, view: "ProjectDetailView") -> None:
        self._view = view

    def _task_repo(self) -> TaskRepository:
        app = self._view.app  # type: ignore[attr-defined]
        return TaskRepository(self._view.project.name, app.registry)

    async def refresh(self) -> None:
        await self._view.set_tasks(self._task_repo().all())

    def new_task(self) -> None:
        from youbot.tui.views.new_task_view import NewTaskView

        def on_create(title: str) -> None:
            task = Task(title=title)
            self._task_repo().add(task)
            self._view.app.call_later(self.refresh)  # type: ignore[attr-defined]

        self._view.app.push_screen(NewTaskView(on_create))

    def open_task(self, task: Task) -> None:
        from youbot.tui.views.task_view import TaskView

        self._view.app.push_screen(TaskView(self._view.project, task))

    def enter_live_session(self, task: Task) -> None:
        app = self._view.app  # type: ignore[attr-defined]
        agent = app.config.default_coding_agent
        agent_session = app.session_manager.start_session(
            self._view.project.name,
            self._view.project.path,
            task,
            agent,
            background=False,
        )
        existing = task.session_for(agent)
        if existing is None:
            task.sessions.append(agent_session)
            self._task_repo().update(task)
        app.session_manager.attach_session(agent_session)

    def start_background_session(self, task: Task) -> None:
        app = self._view.app  # type: ignore[attr-defined]
        agent = app.config.default_coding_agent
        agent_session = app.session_manager.start_session(
            self._view.project.name,
            self._view.project.path,
            task,
            agent,
            background=True,
        )
        existing = task.session_for(agent)
        if existing is None:
            task.sessions.append(agent_session)
            self._task_repo().update(task)
        self.refresh()
