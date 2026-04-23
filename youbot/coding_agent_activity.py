from __future__ import annotations

import json
from dataclasses import asdict

from youbot.config import state_root
from youbot.models import CodingAgentActivityEntry, CodingAgentActivitySnapshot
from youbot.utils import atomic_write, ensure_dir, now_iso


class CodingAgentActivityStore:
    def __init__(self) -> None:
        self._root = state_root() / "activity"
        self._current_path = self._root / "coding_agent_current.json"
        self._history_path = self._root / "coding_agent_events.jsonl"

    def start(
        self,
        *,
        run_id: str,
        repo_id: str,
        backend_name: str,
        target_kind: str,
        request_summary: str,
    ) -> CodingAgentActivitySnapshot:
        snapshot = CodingAgentActivitySnapshot(
            run_id=run_id,
            status="running",
            repo_id=repo_id,
            backend_name=backend_name,  # type: ignore[arg-type]
            target_kind=target_kind,  # type: ignore[arg-type]
            request_summary=request_summary,
            session_id=None,
            started_at=now_iso(),
            updated_at=now_iso(),
        )
        self._write_snapshot(snapshot)
        self._append_event(
            {
                "run_id": run_id,
                "event": "started",
                "repo_id": repo_id,
                "backend_name": backend_name,
                "target_kind": target_kind,
                "request_summary": request_summary,
                "created_at": snapshot.started_at,
            }
        )
        return snapshot

    def append(
        self, run_id: str, *, stream: str, content: str
    ) -> CodingAgentActivitySnapshot | None:
        snapshot = self.get_current()
        if snapshot is None or snapshot.run_id != run_id:
            return None
        entry = CodingAgentActivityEntry(
            stream=stream,  # type: ignore[arg-type]
            content=content.rstrip("\n"),
            created_at=now_iso(),
        )
        snapshot.entries.append(entry)
        snapshot.updated_at = entry.created_at
        self._write_snapshot(snapshot)
        self._append_event(
            {
                "run_id": run_id,
                "event": "output",
                "stream": stream,
                "content": entry.content,
                "created_at": entry.created_at,
            }
        )
        return snapshot

    def set_session_id(
        self, run_id: str, session_id: str | None
    ) -> CodingAgentActivitySnapshot | None:
        snapshot = self.get_current()
        if snapshot is None or snapshot.run_id != run_id:
            return None
        snapshot.session_id = session_id
        snapshot.updated_at = now_iso()
        self._write_snapshot(snapshot)
        if session_id is not None:
            self._append_event(
                {
                    "run_id": run_id,
                    "event": "session_id",
                    "session_id": session_id,
                    "created_at": snapshot.updated_at,
                }
            )
        return snapshot

    def finish(
        self, run_id: str, *, exit_code: int, session_id: str | None
    ) -> CodingAgentActivitySnapshot | None:
        snapshot = self.get_current()
        if snapshot is None or snapshot.run_id != run_id:
            return None
        snapshot.status = "finished"
        snapshot.exit_code = exit_code
        snapshot.session_id = session_id
        snapshot.finished_at = now_iso()
        snapshot.updated_at = snapshot.finished_at
        self._write_snapshot(snapshot)
        self._append_event(
            {
                "run_id": run_id,
                "event": "finished",
                "exit_code": exit_code,
                "session_id": session_id,
                "created_at": snapshot.finished_at,
            }
        )
        return snapshot

    def clear(self) -> None:
        ensure_dir(self._root)
        atomic_write(self._current_path, "")

    def get_current(self) -> CodingAgentActivitySnapshot | None:
        if not self._current_path.exists():
            return None
        text = self._current_path.read_text().strip()
        if not text:
            return None
        payload = json.loads(text)
        return CodingAgentActivitySnapshot(
            run_id=payload["run_id"],
            status=payload["status"],
            repo_id=payload["repo_id"],
            backend_name=payload["backend_name"],
            target_kind=payload["target_kind"],
            request_summary=payload["request_summary"],
            session_id=payload.get("session_id"),
            started_at=payload["started_at"],
            updated_at=payload["updated_at"],
            finished_at=payload.get("finished_at"),
            exit_code=payload.get("exit_code"),
            entries=[CodingAgentActivityEntry(**item) for item in payload.get("entries", [])],
        )

    def _append_event(self, payload: dict) -> None:
        ensure_dir(self._root)
        with self._history_path.open("a") as handle:
            handle.write(json.dumps(payload) + "\n")

    def _write_snapshot(self, snapshot: CodingAgentActivitySnapshot) -> None:
        ensure_dir(self._root)
        atomic_write(self._current_path, json.dumps(asdict(snapshot), indent=2) + "\n")
