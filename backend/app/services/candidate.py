"""候选池服务：被匹配者列表（已有 profile，按性别过滤，排除拉黑者）。"""
from __future__ import annotations

from typing import Any

from app.storage import blacklist, profiles, users


def list_candidates(viewer: dict[str, str], gender: str | None = None) -> dict[str, Any]:
    """对 viewer 来说可见的候选池。gender 可选值：M/F/None(不限)。"""
    blacklist.ensure()
    items: list[dict[str, Any]] = []
    for u in users.list_by_role("matchee"):
        if blacklist.is_blocked(blocker_id=u["id"], blocked_id=viewer["id"]):
            continue
        prof = profiles.find_by_user(u["id"])
        if not prof:
            continue
        if gender and u.get("gender") and u["gender"] != gender:
            continue
        structured = profiles.parse_structured(prof)
        items.append(
            {
                "user_id": u["id"],
                "name": u.get("name", ""),
                "gender": u.get("gender", ""),
                "avatar_url": _avatar_url(u.get("avatar_path", "")),
                "self_intro": structured.get("self_intro", ""),
            }
        )
    return {"viewer_user_id": viewer["id"], "items": items}


def get_detail(user_id: str) -> dict[str, Any] | None:
    u = users.find_by_id(user_id)
    if not u or "matchee" not in (u.get("roles") or ""):
        return None
    prof = profiles.find_by_user(user_id)
    if not prof:
        return None
    structured = profiles.parse_structured(prof)
    return {
        "user_id": u["id"],
        "name": u.get("name", ""),
        "gender": u.get("gender", ""),
        "avatar_url": _avatar_url(u.get("avatar_path", "")),
        "self_intro": structured.get("self_intro", ""),
        "personality": structured.get("personality", []),
        "hobbies": structured.get("hobbies", []),
    }


def _avatar_url(path: str) -> str:
    if not path:
        return ""
    return f"/uploads/{path.rsplit('/', 1)[-1]}"
