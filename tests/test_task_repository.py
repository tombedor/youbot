from __future__ import annotations

from pathlib import Path

from youbot.state.models import Project, Task, TaskStatus
from youbot.state.project_registry import ProjectRegistry
from youbot.state.task_repository import TaskRepository


def _repo(registry: ProjectRegistry, name: str, tmp_path: Path) -> TaskRepository:
    project = Project(name=name, path=tmp_path / name)
    (tmp_path / name).mkdir(exist_ok=True)
    registry.add(project)
    return TaskRepository(name, registry)


def test_empty(registry: ProjectRegistry, tmp_path: Path) -> None:
    repo = _repo(registry, "proj", tmp_path)
    assert repo.all() == []


def test_add_and_get(registry: ProjectRegistry, tmp_path: Path) -> None:
    repo = _repo(registry, "proj", tmp_path)
    task = Task(title="Fix the thing")
    repo.add(task)
    assert repo.get(task.id) is not None
    assert repo.get(task.id).title == "Fix the thing"  # type: ignore[union-attr]


def test_status_defaults_to_todo(registry: ProjectRegistry, tmp_path: Path) -> None:
    repo = _repo(registry, "proj", tmp_path)
    task = Task(title="Some work")
    repo.add(task)
    assert repo.get(task.id).status == TaskStatus.TODO  # type: ignore[union-attr]


def test_update_status(registry: ProjectRegistry, tmp_path: Path) -> None:
    repo = _repo(registry, "proj", tmp_path)
    task = Task(title="Do a thing")
    repo.add(task)
    task.status = TaskStatus.COMPLETE
    repo.update(task)
    assert repo.get(task.id).status == TaskStatus.COMPLETE  # type: ignore[union-attr]


def test_delete(registry: ProjectRegistry, tmp_path: Path) -> None:
    repo = _repo(registry, "proj", tmp_path)
    task = Task(title="Temporary")
    repo.add(task)
    repo.delete(task.id)
    assert repo.get(task.id) is None


def test_todo_md_generated(registry: ProjectRegistry, tmp_path: Path) -> None:
    import youbot.state.project_registry as reg_module
    repo = _repo(registry, "proj", tmp_path)
    task = Task(title="Write tests")
    repo.add(task)
    todo_md = reg_module.project_dir("proj") / "TODO.md"
    assert todo_md.exists()
    content = todo_md.read_text()
    assert "Write tests" in content
