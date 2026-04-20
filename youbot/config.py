from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from youbot.models import CodingAgentBackend, CodingBackendName, RepoClassification
from youbot.utils import atomic_write, ensure_dir


DEFAULT_STATE_ROOT = Path.home() / ".youbot"
REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(slots=True)
class RepoConfig:
    repo_id: str
    name: str
    path: str
    classification: RepoClassification


@dataclass(slots=True)
class SchedulerJob:
    job_id: str
    repo_id: str
    command_name: str
    schedule_type: str
    cron: str | None = None


@dataclass(slots=True)
class AppConfig:
    repos: list[RepoConfig]
    scheduler_enabled: bool
    scheduler_jobs: list[SchedulerJob]
    default_backend: CodingBackendName
    backends: dict[CodingBackendName, CodingAgentBackend]


def state_root() -> Path:
    return DEFAULT_STATE_ROOT


def config_path() -> Path:
    return state_root() / "config.json"


def default_config_payload() -> dict[str, Any]:
    return {
        "repos": [
            {
                "repo_id": "job_search",
                "name": "job_search",
                "path": str((REPO_ROOT.parent / "job_search").resolve()),
                "classification": "integrated",
            },
            {
                "repo_id": "life_admin",
                "name": "life_admin",
                "path": str((REPO_ROOT.parent / "life_admin").resolve()),
                "classification": "integrated",
            },
            {
                "repo_id": "trader-bot",
                "name": "trader-bot",
                "path": str((REPO_ROOT.parent / "trader-bot").resolve()),
                "classification": "integrated",
            },
        ],
        "scheduler": {"enabled": False, "jobs": []},
        "coding_agent": {
            "default_backend": "codex",
            "backends": {
                "codex": {"command_prefix": ["codex"], "default_args": []},
                "claude_code": {"command_prefix": ["claude"], "default_args": []},
            },
        },
    }


def ensure_default_config() -> Path:
    root = state_root()
    ensure_dir(root)
    path = config_path()
    if not path.exists():
        atomic_write(path, json.dumps(default_config_payload(), indent=2) + "\n")
    return path


def load_config() -> AppConfig:
    path = ensure_default_config()
    payload = json.loads(path.read_text())

    repos = [
        RepoConfig(
            repo_id=item["repo_id"],
            name=item["name"],
            path=item["path"],
            classification=item["classification"],
        )
        for item in payload["repos"]
    ]
    scheduler_jobs = [
        SchedulerJob(
            job_id=item["job_id"],
            repo_id=item["repo_id"],
            command_name=item["command_name"],
            schedule_type=item["schedule_type"],
            cron=item.get("cron"),
        )
        for item in payload["scheduler"]["jobs"]
    ]
    backends = {
        name: CodingAgentBackend(
            backend_name=name,  # type: ignore[arg-type]
            command_prefix=backend_payload["command_prefix"],
            default_args=backend_payload.get("default_args", []),
        )
        for name, backend_payload in payload["coding_agent"]["backends"].items()
    }
    return AppConfig(
        repos=repos,
        scheduler_enabled=payload["scheduler"]["enabled"],
        scheduler_jobs=scheduler_jobs,
        default_backend=payload["coding_agent"]["default_backend"],
        backends=backends,
    )


def as_payload(config: AppConfig) -> dict[str, Any]:
    return {
        "repos": [asdict(repo) for repo in config.repos],
        "scheduler": {
            "enabled": config.scheduler_enabled,
            "jobs": [asdict(job) for job in config.scheduler_jobs],
        },
        "coding_agent": {
            "default_backend": config.default_backend,
            "backends": {name: asdict(backend) for name, backend in config.backends.items()},
        },
    }
