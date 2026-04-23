from __future__ import annotations

import json
from dataclasses import asdict

from youbot.config import state_root
from youbot.models import ConversationMessage, ConversationRecord
from youbot.utils import atomic_write, ensure_dir, make_id, now_iso


class ConversationStore:
    def __init__(self) -> None:
        self._path = state_root() / "conversation" / "history.json"

    def _ensure_parent(self) -> None:
        ensure_dir(self._path.parent)

    def get_conversation(self) -> ConversationRecord:
        self._ensure_parent()
        if not self._path.exists():
            record = ConversationRecord(
                conversation_id=make_id(),
                messages=[],
                updated_at=now_iso(),
                last_response_id=None,
            )
            self._write(record)
            return record
        payload = json.loads(self._path.read_text())
        return ConversationRecord(
            conversation_id=payload["conversation_id"],
            messages=[ConversationMessage(**item) for item in payload["messages"]],
            updated_at=payload["updated_at"],
            last_response_id=payload.get("last_response_id"),
        )

    def append_message(self, message: ConversationMessage) -> None:
        record = self.get_conversation()
        record.messages.append(message)
        record.updated_at = now_iso()
        self._write(record)

    def clear_conversation(self) -> None:
        record = ConversationRecord(
            conversation_id=make_id(),
            messages=[],
            updated_at=now_iso(),
            last_response_id=None,
        )
        self._write(record)

    def set_last_response_id(self, response_id: str | None) -> None:
        record = self.get_conversation()
        record.last_response_id = response_id
        record.updated_at = now_iso()
        self._write(record)

    def _write(self, record: ConversationRecord) -> None:
        self._ensure_parent()
        atomic_write(
            self._path,
            json.dumps(
                {
                    "conversation_id": record.conversation_id,
                    "messages": [asdict(message) for message in record.messages],
                    "updated_at": record.updated_at,
                    "last_response_id": record.last_response_id,
                },
                indent=2,
            )
            + "\n",
        )
