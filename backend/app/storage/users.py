"""users.csv 的领域操作。"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.config import DATA_DIR
from app.storage import base

USERS_CSV = DATA_DIR / "users.csv"
HEADERS = [
    "id",
    "openid",
    "name",
    "gender",
    "expected_gender",
    "contact",
    "avatar_path",
    "roles",
    "created_at",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def find_by_openid(openid: str) -> dict[str, str] | None:
    return base.find_one(USERS_CSV, openid=openid)


def find_by_id(user_id: str) -> dict[str, str] | None:
    return base.find_one(USERS_CSV, id=user_id)


def list_all() -> list[dict[str, str]]:
    return base.read_all(USERS_CSV)


def list_by_role(role: str) -> list[dict[str, str]]:
    return [u for u in list_all() if role in (u.get("roles") or "")]


def create_minimal(openid: str) -> dict[str, str]:
    """注册时只填 openid，其余字段留待 PUT /users/me 补齐。默认拥有 matchee+matcher 两个角色。"""
    row = {
        "id": str(uuid.uuid4()),
        "openid": openid,
        "name": "",
        "gender": "",
        "expected_gender": "",
        "contact": "",
        "avatar_path": "",
        "roles": "matchee,matcher",
        "created_at": _now(),
    }
    base.append_row(USERS_CSV, HEADERS, row)
    return row


def update(user_id: str, fields: dict[str, Any]) -> int:
    """仅更新非 None 字段，键限定在 HEADERS 内（排除 id/openid/created_at/roles 不让客户端改）。"""
    allowed = {"name", "gender", "expected_gender", "contact", "avatar_path"}
    payload = {k: str(v) for k, v in fields.items() if v is not None and k in allowed}
    if not payload:
        return 0
    return base.update_rows(USERS_CSV, HEADERS, match={"id": user_id}, update=payload)
