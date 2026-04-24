from __future__ import annotations

from pathlib import Path

import pytest

import youbot.config.app_config as app_config_module
import youbot.state.project_registry as registry_module


@pytest.fixture()
def youbot_state_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    state_dir = tmp_path / ".youbot"
    state_dir.mkdir()
    monkeypatch.setattr(app_config_module, "YOUBOT_STATE_DIR", state_dir)
    monkeypatch.setattr(app_config_module, "CONFIG_FILE", state_dir / "config.yaml")
    monkeypatch.setattr(registry_module, "YOUBOT_STATE_DIR", state_dir)
    monkeypatch.setattr(registry_module, "PROJECTS_DIR", state_dir / "projects")
    monkeypatch.setattr(registry_module, "REGISTRY_FILE", state_dir / "registry.yaml")
    return state_dir


@pytest.fixture()
def registry(youbot_state_dir: Path) -> registry_module.ProjectRegistry:
    return registry_module.ProjectRegistry()


@pytest.fixture()
def sample_projects(tmp_path: Path) -> list[tuple[str, Path]]:
    projects = [
        ("alpha", tmp_path / "alpha"),
        ("beta", tmp_path / "beta"),
    ]
    for name, path in projects:
        path.mkdir()
    return projects
