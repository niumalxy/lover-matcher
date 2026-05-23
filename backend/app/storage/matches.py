"""matches.csv 领域操作。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.config import DATA_DIR
from app.storage import base

MATCHES_CSV = DATA_DIR / "matches.csv"
HEADERS = [
    "id",
    "conversation_id",
    "matchee_user_id",
    "matcher_user_id",
    "matchee_decision",
    "created_at",
    "decided_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_by_id(match_id: str) -> dict[str, str] | None:
    return base.find_one(MATCHES_CSV, id=match_id)


def find_by_conversation(conv_id: str) -> dict[str, str] | None:
    return base.find_one(MATCHES_CSV, conversation_id=conv_id)


def list_pending_for_matchee(matchee_id: str) -> list[dict[str, str]]:
    return [
        r
        for r in base.find_all(MATCHES_CSV, matchee_user_id=matchee_id)
        if r.get("matchee_decision") == "pending"
    ]


def list_for_matcher(matcher_id: str) -> list[dict[str, str]]:
    return base.find_all(MATCHES_CSV, matcher_user_id=matcher_id)


def list_for_matchee(matchee_id: str) -> list[dict[str, str]]:
    return base.find_all(MATCHES_CSV, matchee_user_id=matchee_id)


def create(conversation_id: str, matchee_id: str, matcher_id: str) -> dict[str, str]:
    row = {
        "id": str(uuid.uuid4()),
        "conversation_id": conversation_id,
        "matchee_user_id": matchee_id,
        "matcher_user_id": matcher_id,
        "matchee_decision": "pending",
        "created_at": _now(),
        "decided_at": "",
    }
    base.append_row(MATCHES_CSV, HEADERS, row)
    return row


def set_decision(match_id: str, decision: str) -> int:
    return base.update_rows(
        MATCHES_CSV,
        HEADERS,
        match={"id": match_id},
        update={"matchee_decision": decision, "decided_at": _now()},
    )
