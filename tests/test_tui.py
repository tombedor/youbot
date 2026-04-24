from __future__ import annotations

from pathlib import Path

import pytest

from youbot.state.models import MergeBehavior, Project, Task
from youbot.state.project_registry import ProjectRegistry
from youbot.state.task_repository import TaskRepository
from youbot.tui.app import YoubotApp


@pytest.fixture()
def app(registry: ProjectRegistry) -> YoubotApp:
    instance = YoubotApp()
    instance.registry = registry
    return instance


@pytest.fixture()
def app_with_projects(
    app: YoubotApp,
    registry: ProjectRegistry,
    tmp_path: Path,
) -> YoubotApp:
    for name in ("alpha", "beta"):
        path = tmp_path / name
        path.mkdir()
        registry.add(Project(name=name, path=path))
    return app


@pytest.fixture()
def app_with_tasks(
    app_with_projects: YoubotApp,
    registry: ProjectRegistry,
    tmp_path: Path,
) -> YoubotApp:
    task_repo = TaskRepository("alpha", registry)
    task_repo.add(Task(title="First task"))
    task_repo.add(Task(title="Second task"))
    return app_with_projects


async def _labels(pilot: object, app: YoubotApp) -> list[str]:
    from textual.widgets import Label
    return [str(w.content) for w in app.screen.query(Label)]


async def test_home_shows_no_projects(app: YoubotApp) -> None:
    async with app.run_test() as pilot:
        await pilot.pause(0.1)
        assert any("No projects" in label for label in await _labels(pilot, app))


async def test_home_shows_projects(app_with_projects: YoubotApp) -> None:
    async with app_with_projects.run_test() as pilot:
        await pilot.pause(0.1)
        labels = await _labels(pilot, app_with_projects)
        assert any("alpha" in label for label in labels)
        assert any("beta" in label for label in labels)


async def test_navigate_to_project_detail(app_with_projects: YoubotApp) -> None:
    from youbot.tui.views.project_detail_view import ProjectDetailView

    async with app_with_projects.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert isinstance(app_with_projects.screen, ProjectDetailView)


async def test_project_detail_shows_tasks(app_with_tasks: YoubotApp) -> None:
    from youbot.tui.views.project_detail_view import ProjectDetailView

    async with app_with_tasks.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert isinstance(app_with_tasks.screen, ProjectDetailView)
        labels = await _labels(pilot, app_with_tasks)
        assert any("First task" in label for label in labels)
        assert any("Second task" in label for label in labels)


async def test_create_task(app_with_projects: YoubotApp) -> None:
    from youbot.tui.views.new_task_view import NewTaskView
    from youbot.tui.views.project_detail_view import ProjectDetailView

    async with app_with_projects.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        await pilot.press("n")
        await pilot.pause(0.1)
        assert isinstance(app_with_projects.screen, NewTaskView)
        await pilot.press(*"Fix the bug")
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert isinstance(app_with_projects.screen, ProjectDetailView)
        labels = await _labels(pilot, app_with_projects)
        assert any("Fix the bug" in label for label in labels)


async def test_back_navigation(app_with_projects: YoubotApp) -> None:
    from youbot.tui.views.home_view import HomeView
    from youbot.tui.views.project_detail_view import ProjectDetailView

    async with app_with_projects.run_test() as pilot:
        await pilot.pause(0.1)
        await pilot.press("enter")
        await pilot.pause(0.1)
        assert isinstance(app_with_projects.screen, ProjectDetailView)
        await pilot.press("escape")
        await pilot.pause(0.1)
        assert isinstance(app_with_projects.screen, HomeView)
