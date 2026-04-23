from __future__ import annotations

import json

from youbot.config import state_root
from youbot.models import CodingAgentResult
from youbot.utils import ensure_dir


def append_run_log(result: CodingAgentResult) -> None:
    log_path = state_root() / "runs" / "coding_agents.jsonl"
    ensure_dir(log_path.parent)
    payload = {
        "repo_id": result.repo_id,
        "backend_name": result.backend_name,
        "target_kind": result.target_kind,
        "session_id": result.session_id,
        "exit_code": result.exit_code,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
    }
    with log_path.open("a") as handle:
        handle.write(json.dumps(payload) + "\n")
