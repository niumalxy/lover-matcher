"""messages.csv 领域操作。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.config import DATA_DIR
from app.storage import base

MESSAGES_CSV = DATA_DIR / "messages.csv"
HEADERS = ["id", "conversation_id", "sender", "content", "created_at"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_by_conversation(conv_id: str) -> list[dict[str, str]]:
    rows = base.find_all(MESSAGES_CSV, conversation_id=conv_id)
    rows.sort(key=lambda r: r.get("created_at", ""))
    return rows


def append(conv_id: str, sender: str, content: str) -> dict[str, str]:
    row = {
        "id": str(uuid.uuid4()),
        "conversation_id": conv_id,
        "sender": sender,
        "content": content,
        "created_at": _now(),
    }
    base.append_row(MESSAGES_CSV, HEADERS, row)
    return row
