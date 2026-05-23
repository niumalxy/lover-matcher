"""conversations.csv 领域操作。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.config import DATA_DIR
from app.storage import base

CONVERSATIONS_CSV = DATA_DIR / "conversations.csv"
HEADERS = [
    "id",
    "matchee_user_id",
    "matcher_user_id",
    "status",
    "created_at",
    "updated_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_by_id(conv_id: str) -> dict[str, str] | None:
    return base.find_one(CONVERSATIONS_CSV, id=conv_id)


def find_active_between(matchee_id: str, matcher_id: str) -> dict[str, str] | None:
    rows = base.find_all(CONVERSATIONS_CSV, matchee_user_id=matchee_id, matcher_user_id=matcher_id)
    for r in rows:
        if r.get("status") in ("active", "matched"):
            return r
    return None


def list_for_matcher(matcher_id: str) -> list[dict[str, str]]:
    return base.find_all(CONVERSATIONS_CSV, matcher_user_id=matcher_id)


def list_for_matchee(matchee_id: str) -> list[dict[str, str]]:
    return base.find_all(CONVERSATIONS_CSV, matchee_user_id=matchee_id)


def create(matchee_id: str, matcher_id: str) -> dict[str, str]:
    now = _now()
    row = {
        "id": str(uuid.uuid4()),
        "matchee_user_id": matchee_id,
        "matcher_user_id": matcher_id,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    base.append_row(CONVERSATIONS_CSV, HEADERS, row)
    return row


def set_status(conv_id: str, status: str) -> int:
    return base.update_rows(
        CONVERSATIONS_CSV,
        HEADERS,
        match={"id": conv_id},
        update={"status": status, "updated_at": _now()},
    )
