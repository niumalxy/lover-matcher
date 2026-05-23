"""profiles.csv 的领域操作。structured 字段存 JSON 字符串。"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import DATA_DIR
from app.storage import base

PROFILES_CSV = DATA_DIR / "profiles.csv"
HEADERS = [
    "id",
    "user_id",
    "raw_input",
    "structured",
    "created_at",
    "updated_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_by_user(user_id: str) -> dict[str, str] | None:
    return base.find_one(PROFILES_CSV, user_id=user_id)


def list_all() -> list[dict[str, str]]:
    return base.read_all(PROFILES_CSV)


def upsert(user_id: str, raw_input: str, structured: dict[str, Any]) -> dict[str, str]:
    existing = find_by_user(user_id)
    structured_json = json.dumps(structured, ensure_ascii=False)
    if existing:
        base.update_rows(
            PROFILES_CSV,
            HEADERS,
            match={"id": existing["id"]},
            update={
                "raw_input": raw_input,
                "structured": structured_json,
                "updated_at": _now(),
            },
        )
        return find_by_user(user_id) or existing
    now = _now()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "raw_input": raw_input,
        "structured": structured_json,
        "created_at": now,
        "updated_at": now,
    }
    base.append_row(PROFILES_CSV, HEADERS, row)
    return row


def parse_structured(row: dict[str, str]) -> dict[str, Any]:
    raw = row.get("structured") or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}
