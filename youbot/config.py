from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
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
            "backends": {
                name: {
                    "command_prefix": backend.command_prefix,
                    "default_args": backend.default_args,
                }
                for name, backend in config.backends.items()
            },
        },
    }


def save_config(config: AppConfig) -> None:
    path = ensure_default_config()
    atomic_write(path, json.dumps(as_payload(config), indent=2) + "\n")


def make_repo_id(name: str) -> str:
    repo_id = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return repo_id or "repo"


def add_repo_config(
    *,
    path: str,
    name: str | None = None,
    classification: RepoClassification = "integrated",
) -> RepoConfig:
    config = load_config()
    resolved_path = str(Path(path).resolve())
    existing_by_path = next(
        (repo for repo in config.repos if Path(repo.path).resolve() == Path(resolved_path)),
        None,
    )
    repo_name = name or Path(resolved_path).name
    if existing_by_path is not None:
        existing_by_path.name = repo_name
        existing_by_path.classification = classification
        save_config(config)
        return existing_by_path

    base_repo_id = make_repo_id(repo_name)
    repo_id = base_repo_id
    existing_ids = {repo.repo_id for repo in config.repos}
    suffix = 2
    while repo_id in existing_ids:
        repo_id = f"{base_repo_id}-{suffix}"
        suffix += 1

    repo = RepoConfig(
        repo_id=repo_id,
        name=repo_name,
        path=resolved_path,
        classification=classification,
    )
    config.repos.append(repo)
    save_config(config)
    return repo
