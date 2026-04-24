from __future__ import annotations

import yaml
from pydantic import BaseModel

from youbot.state.models import Task, TaskStatus
from youbot.state.project_registry import ProjectRegistry, project_dir


class _TaskStore(BaseModel):
    tasks: list[Task] = []


class TaskRepository:
    def __init__(self, project_name: str, registry: ProjectRegistry) -> None:
        self._project_name = project_name
        self._registry = registry
        self._tasks_file = project_dir(project_name) / "tasks.yaml"
        self._todo_md = project_dir(project_name) / "TODO.md"

    def _load(self) -> _TaskStore:
        if not self._tasks_file.exists():
            return _TaskStore()
        with self._tasks_file.open() as f:
            data = yaml.safe_load(f) or {}
        return _TaskStore(**data)

    def _save(self, store: _TaskStore) -> None:
        self._tasks_file.parent.mkdir(parents=True, exist_ok=True)
        with self._tasks_file.open("w") as f:
            yaml.dump(store.model_dump(mode="json"), f, default_flow_style=False)
        self._write_todo_md(store.tasks)
        self._registry._commit(f"update tasks for {self._project_name}")

    def _write_todo_md(self, tasks: list[Task]) -> None:
        lines = [f"# {self._project_name} — Tasks\n"]
        for status in TaskStatus:
            group = [t for t in tasks if t.status == status]
            if not group:
                continue
            lines.append(f"\n## {status.value}\n")
            for task in group:
                lines.append(f"- [{task.id}] {task.title}")
                if task.description:
                    lines.append(f"  {task.description}")
                for s in task.sessions:
                    active = "ACTIVE" if s.active else "inactive"
                    lines.append(f"  - {s.agent.value}: branch={s.branch or 'none'} [{active}]")
                    if s.summary:
                        lines.append(f"    {s.summary}")
        with self._todo_md.open("w") as f:
            f.write("\n".join(lines) + "\n")

    def all(self) -> list[Task]:
        return self._load().tasks

    def get(self, task_id: str) -> Task | None:
        return next((t for t in self.all() if t.id == task_id), None)

    def add(self, task: Task) -> Task:
        store = self._load()
        store.tasks.append(task)
        self._save(store)
        return task

    def update(self, task: Task) -> None:
        store = self._load()
        store.tasks = [t if t.id != task.id else task for t in store.tasks]
        self._save(store)

    def delete(self, task_id: str) -> None:
        store = self._load()
        store.tasks = [t for t in store.tasks if t.id != task_id]
        self._save(store)
