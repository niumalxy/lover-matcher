"""blacklist.csv 的领域操作。被匹配者可以拉黑匹配者，阻止其再看到自己。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import DATA_DIR
from app.storage import base

BLACKLIST_CSV = DATA_DIR / "blacklist.csv"
HEADERS = [
    "id",
    "blocker_user_id",
    "blocked_user_id",
    "reason",
    "created_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure() -> None:
    base.ensure_csv(BLACKLIST_CSV, HEADERS)


def is_blocked(blocker_id: str, blocked_id: str) -> bool:
    row = base.find_one(BLACKLIST_CSV, blocker_user_id=blocker_id, blocked_user_id=blocked_id)
    return row is not None


def add_block(blocker_id: str, blocked_id: str, reason: str = "") -> dict[str, Any]:
    now = _now()
    row: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "blocker_user_id": blocker_id,
        "blocked_user_id": blocked_id,
        "reason": reason,
        "created_at": now,
    }
    base.append_row(BLACKLIST_CSV, HEADERS, row)
    return row
