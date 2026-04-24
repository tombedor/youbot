from __future__ import annotations

from pathlib import Path

import git
import yaml
from pydantic import BaseModel

from youbot.config.app_config import YOUBOT_STATE_DIR
from youbot.state.models import Project

PROJECTS_DIR = YOUBOT_STATE_DIR / "projects"
REGISTRY_FILE = YOUBOT_STATE_DIR / "registry.yaml"


class _Registry(BaseModel):
    projects: list[Project] = []


class ProjectRegistry:
    def __init__(self) -> None:
        self._ensure_state_repo()

    def _ensure_state_repo(self) -> None:
        YOUBOT_STATE_DIR.mkdir(parents=True, exist_ok=True)
        if not (YOUBOT_STATE_DIR / ".git").exists():
            git.Repo.init(YOUBOT_STATE_DIR)

    def _load(self) -> _Registry:
        if not REGISTRY_FILE.exists():
            return _Registry()
        with REGISTRY_FILE.open() as f:
            data = yaml.safe_load(f) or {}
        return _Registry(**data)

    def _save(self, registry: _Registry, message: str) -> None:
        YOUBOT_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with REGISTRY_FILE.open("w") as f:
            yaml.dump(registry.model_dump(mode="json"), f, default_flow_style=False)
        self._commit(message)

    def _commit(self, message: str) -> None:
        repo = git.Repo(YOUBOT_STATE_DIR)
        repo.git.add(A=True)
        if repo.is_dirty(index=True):
            repo.index.commit(message)

    def all(self) -> list[Project]:
        return self._load().projects

    def get(self, name: str) -> Project | None:
        return next((p for p in self.all() if p.name == name), None)

    def add(self, project: Project) -> None:
        registry = self._load()
        if any(p.name == project.name for p in registry.projects):
            raise ValueError(f"Project '{project.name}' already registered")
        registry.projects.append(project)
        project_dir(project.name).mkdir(parents=True, exist_ok=True)
        self._save(registry, f"add project {project.name}")

    def update(self, project: Project) -> None:
        registry = self._load()
        registry.projects = [p if p.name != project.name else project for p in registry.projects]
        self._save(registry, f"update project {project.name}")

    def remove(self, name: str) -> None:
        registry = self._load()
        registry.projects = [p for p in registry.projects if p.name != name]
        self._save(registry, f"remove project {name}")


def project_dir(name: str) -> Path:
    return PROJECTS_DIR / name
