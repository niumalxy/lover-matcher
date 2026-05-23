"""匹配服务：决策处理 + 详情视图（contact 暴露在 approved 后）。"""
from __future__ import annotations

from typing import Any

from app.errors import BusinessError, ForbiddenError, NotFoundError
from app.storage import matches, users


def list_pending_for_matchee(matchee_id: str) -> list[dict[str, Any]]:
    rows = matches.list_pending_for_matchee(matchee_id)
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return [_render(r, viewer_id=matchee_id) for r in rows]


def list_for_user(user_id: str) -> list[dict[str, Any]]:
    """matcher 和 matchee 都能查到自己参与的所有 match。"""
    seen: dict[str, dict[str, str]] = {}
    for r in matches.list_for_matcher(user_id):
        seen[r["id"]] = r
    for r in matches.list_for_matchee(user_id):
        seen[r["id"]] = r
    rows = sorted(seen.values(), key=lambda r: r.get("created_at", ""), reverse=True)
    return [_render(r, viewer_id=user_id) for r in rows]


def decide(match_id: str, matchee_id: str, decision: str) -> dict[str, Any]:
    row = matches.find_by_id(match_id)
    if not row:
        raise NotFoundError("匹配记录不存在")
    if row["matchee_user_id"] != matchee_id:
        raise ForbiddenError("只有被匹配者本人能决定")
    if row["matchee_decision"] != "pending":
        raise BusinessError(code=4006, msg="已经决定过了")
    matches.set_decision(match_id, decision)
    updated = matches.find_by_id(match_id) or row
    return _render(updated, viewer_id=matchee_id)


def get_detail(match_id: str, viewer_id: str) -> dict[str, Any]:
    row = matches.find_by_id(match_id)
    if not row:
        raise NotFoundError("匹配记录不存在")
    if viewer_id not in (row["matchee_user_id"], row["matcher_user_id"]):
        raise ForbiddenError("无权查看")
    return _render(row, viewer_id=viewer_id)


def _render(row: dict[str, str], viewer_id: str) -> dict[str, Any]:
    peer_id = (
        row["matcher_user_id"] if viewer_id == row["matchee_user_id"] else row["matchee_user_id"]
    )
    peer = users.find_by_id(peer_id) or {}
    avatar_path = peer.get("avatar_path", "") or ""
    peer_avatar = f"/uploads/{avatar_path.rsplit('/', 1)[-1]}" if avatar_path else ""
    # contact 仅在 approved 后才暴露
    peer_contact = peer.get("contact", "") if row["matchee_decision"] == "approved" else ""
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "matchee_user_id": row["matchee_user_id"],
        "matcher_user_id": row["matcher_user_id"],
        "matchee_decision": row["matchee_decision"],
        "created_at": row["created_at"],
        "decided_at": row.get("decided_at", ""),
        "peer_name": peer.get("name", ""),
        "peer_avatar_url": peer_avatar,
        "peer_contact": peer_contact,
    }
