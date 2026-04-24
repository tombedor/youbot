from __future__ import annotations

from pathlib import Path

import pytest

from youbot.state.models import MergeBehavior, Project
from youbot.state.project_registry import ProjectRegistry


def test_empty_registry(registry: ProjectRegistry) -> None:
    assert registry.all() == []


def test_add_and_retrieve(registry: ProjectRegistry, tmp_path: Path) -> None:
    project = Project(name="myrepo", path=tmp_path / "myrepo", merge_behavior=MergeBehavior.OPEN_PR)
    registry.add(project)
    assert len(registry.all()) == 1
    assert registry.get("myrepo") == project


def test_duplicate_add_raises(registry: ProjectRegistry, tmp_path: Path) -> None:
    project = Project(name="myrepo", path=tmp_path / "myrepo")
    registry.add(project)
    with pytest.raises(ValueError, match="already registered"):
        registry.add(project)


def test_update(registry: ProjectRegistry, tmp_path: Path) -> None:
    project = Project(name="myrepo", path=tmp_path / "myrepo", merge_behavior=MergeBehavior.OPEN_PR)
    registry.add(project)
    updated = project.model_copy(update={"merge_behavior": MergeBehavior.AUTO_MERGE})
    registry.update(updated)
    assert registry.get("myrepo").merge_behavior == MergeBehavior.AUTO_MERGE  # type: ignore[union-attr]


def test_remove(registry: ProjectRegistry, tmp_path: Path) -> None:
    project = Project(name="myrepo", path=tmp_path / "myrepo")
    registry.add(project)
    registry.remove("myrepo")
    assert registry.get("myrepo") is None


def test_persists_across_instances(registry: ProjectRegistry, tmp_path: Path, youbot_state_dir: Path) -> None:
    project = Project(name="myrepo", path=tmp_path / "myrepo")
    registry.add(project)
    registry2 = ProjectRegistry()
    assert registry2.get("myrepo") == project
