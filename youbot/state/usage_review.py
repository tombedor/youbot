from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from youbot.config import state_root
from youbot.core.models import ConversationMessage, UsageReviewBundle
from youbot.utils import atomic_write, ensure_dir, make_id, now_iso


class UsageReviewService:
    def __init__(self) -> None:
        self._state_root = state_root()
        self._reviews_root = self._state_root / "reviews"
        self._bundles_root = self._reviews_root / "bundles"

    def build_bundle(
        self,
        *,
        max_messages: int = 200,
        max_command_runs: int = 100,
        max_coding_agent_runs: int = 100,
        max_activity_entries: int = 200,
    ) -> UsageReviewBundle:
        notes: list[str] = []
        conversation_payload = self._read_json(
            self._state_root / "conversation" / "history.json", notes=notes
        )
        messages = [
            ConversationMessage(**item)
            for item in conversation_payload.get("messages", [])[-max_messages:]
        ]
        command_runs = self._read_jsonl(
            self._state_root / "runs" / "commands.jsonl",
            limit=max_command_runs,
            notes=notes,
        )
        coding_agent_runs = self._read_jsonl(
            self._state_root / "runs" / "coding_agents.jsonl",
            limit=max_coding_agent_runs,
            notes=notes,
        )
        activity_entries = self._read_jsonl(
            self._state_root / "activity" / "coding_agent_events.jsonl",
            limit=max_activity_entries,
            notes=notes,
        )
        activity_log_refs = [
            str(path)
            for path in [
                self._state_root / "activity" / "coding_agent_current.json",
                self._state_root / "activity" / "coding_agent_events.jsonl",
            ]
            if path.exists()
        ]
        bundle = UsageReviewBundle(
            bundle_id=make_id(),
            created_at=now_iso(),
            source_state_root=str(self._state_root),
            window_summary=(
                f"{len(messages)} messages, {len(command_runs)} command runs, "
                f"{len(coding_agent_runs)} coding-agent runs"
            ),
            conversation_id=conversation_payload.get("conversation_id"),
            messages=messages,
            command_runs=command_runs,
            coding_agent_runs=coding_agent_runs,
            activity_entries=activity_entries,
            activity_log_refs=activity_log_refs,
            notes=notes,
        )
        return bundle

    def write_bundle(self, bundle: UsageReviewBundle) -> Path:
        ensure_dir(self._bundles_root)
        path = self._bundles_root / f"{bundle.bundle_id}.json"
        atomic_write(path, json.dumps(asdict(bundle), indent=2) + "\n")
        latest_path = self._reviews_root / "latest.json"
        latest_payload = {
            "bundle_id": bundle.bundle_id,
            "created_at": bundle.created_at,
            "bundle_path": str(path),
            "window_summary": bundle.window_summary,
        }
        atomic_write(latest_path, json.dumps(latest_payload, indent=2) + "\n")
        return path

    def build_and_write_bundle(
        self,
        *,
        max_messages: int = 200,
        max_command_runs: int = 100,
        max_coding_agent_runs: int = 100,
        max_activity_entries: int = 200,
    ) -> tuple[UsageReviewBundle, Path]:
        bundle = self.build_bundle(
            max_messages=max_messages,
            max_command_runs=max_command_runs,
            max_coding_agent_runs=max_coding_agent_runs,
            max_activity_entries=max_activity_entries,
        )
        return bundle, self.write_bundle(bundle)

    def _read_json(self, path: Path, *, notes: list[str]) -> dict[str, Any]:
        if not path.exists():
            notes.append(f"Missing JSON source: {path}")
            return {}
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            notes.append(f"Corrupt JSON source skipped: {path}")
            return {}
        if not isinstance(payload, dict):
            notes.append(f"Unexpected JSON shape skipped: {path}")
            return {}
        return payload

    def _read_jsonl(self, path: Path, *, limit: int, notes: list[str]) -> list[dict[str, Any]]:
        if not path.exists():
            notes.append(f"Missing JSONL source: {path}")
            return []
        items: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                notes.append(f"Skipped corrupt JSONL line {line_number} from {path}")
                continue
            if isinstance(payload, dict):
                items.append(payload)
        return items[-limit:]
