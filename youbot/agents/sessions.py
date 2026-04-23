from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from youbot.config import state_root
from youbot.core.models import CodingAgentSessionRef
from youbot.utils import atomic_write, ensure_dir


class CodingAgentSessionRegistry:
    def __init__(self) -> None:
        self._path = state_root() / "coding_agent_sessions" / "sessions.json"

    def _load(self) -> dict[str, Any]:
        ensure_dir(self._path.parent)
        if not self._path.exists():
            self._path.write_text("{}\n")
        return json.loads(self._path.read_text())  # type: ignore[no-any-return]

    def get_session(self, repo_id: str) -> CodingAgentSessionRef | None:
        payload = self._load()
        item = payload.get(repo_id)
        if item is None:
            return None
        return CodingAgentSessionRef(**item)

    def set_session(self, session: CodingAgentSessionRef) -> None:
        payload = self._load()
        payload[session.repo_id] = asdict(session)
        atomic_write(self._path, json.dumps(payload, indent=2) + "\n")

    def clear_session(self, repo_id: str) -> None:
        payload = self._load()
        payload.pop(repo_id, None)
        atomic_write(self._path, json.dumps(payload, indent=2) + "\n")
