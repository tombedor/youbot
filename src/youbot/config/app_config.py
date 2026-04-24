from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from youbot.state.models import CodingAgent

YOUBOT_STATE_DIR = Path.home() / ".youbot"
CONFIG_FILE = YOUBOT_STATE_DIR / "config.yaml"


class AppConfig(BaseModel):
    default_repo_location: Path = Path.home() / "development"
    default_coding_agent: CodingAgent = CodingAgent.CLAUDE_CODE

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_FILE.exists():
            return cls()
        with CONFIG_FILE.open() as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def save(self) -> None:
        YOUBOT_STATE_DIR.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)
