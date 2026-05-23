"""/api/v1/conversations —— 对话生命周期。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.errors import ForbiddenError, NotFoundError
from app.models.common import ok
from app.models.conversation import (
    ConversationOut,
    MessageOut,
    SendMessageRequest,
    StartConversationRequest,
)
from app.services import matcher_agent
from app.services.auth import current_user
from app.storage import blacklist, conversations, messages, users

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


def _conv_to_out(conv: dict[str, str], viewer_id: str) -> dict:
    peer_id = (
        conv["matchee_user_id"] if viewer_id == conv["matcher_user_id"] else conv["matcher_user_id"]
    )
    peer = users.find_by_id(peer_id)
    peer_name = peer.get("name", "") if peer else ""
    avatar_path = (peer.get("avatar_path", "") if peer else "") or ""
    peer_avatar = f"/uploads/{avatar_path.rsplit('/', 1)[-1]}" if avatar_path else ""
    return ConversationOut(
        id=conv["id"],
        matchee_user_id=conv["matchee_user_id"],
        matcher_user_id=conv["matcher_user_id"],
        status=conv["status"],  # type: ignore[arg-type]
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        peer_name=peer_name,
        peer_avatar_url=peer_avatar,
    ).model_dump()


def _msg_to_out(m: dict[str, str]) -> dict:
    return MessageOut(
        id=m["id"],
        conversation_id=m["conversation_id"],
        sender=m["sender"],  # type: ignore[arg-type]
        content=m["content"],
        created_at=m["created_at"],
    ).model_dump()


@router.post("")
def start(req: StartConversationRequest, user: dict = Depends(current_user)) -> dict:
    matchee = users.find_by_id(req.matchee_user_id)
    if not matchee or "matchee" not in (matchee.get("roles") or ""):
        raise NotFoundError("被匹配者不存在")
    if blacklist.is_blocked(blocker_id=matchee["id"], blocked_id=user["id"]):
        raise ForbiddenError("你已被对方拉黑，无法发起会话")
    existing = conversations.find_active_between(matchee["id"], user["id"])
    if existing:
        existing_msgs = messages.list_by_conversation(existing["id"])
        if not existing_msgs:
            try:
                matcher_agent.generate_opening(existing["id"])
            except Exception:
                logger.warning("已有会话 %s 开场白补发失败", existing["id"])
        return ok(_conv_to_out(existing, user["id"]))
    conv = conversations.create(matchee_id=matchee["id"], matcher_id=user["id"])
    try:
        matcher_agent.generate_opening(conv["id"])
    except Exception:
        logger.warning("会话 %s 开场白生成失败，跳过", conv["id"])
    return ok(_conv_to_out(conv, user["id"]))


@router.get("/mine")
def list_mine(user: dict = Depends(current_user)) -> dict:
    seen: dict[str, dict[str, str]] = {}
    for c in conversations.list_for_matcher(user["id"]):
        seen[c["id"]] = c
    for c in conversations.list_for_matchee(user["id"]):
        seen[c["id"]] = c
    items = sorted(seen.values(), key=lambda r: r.get("updated_at", ""), reverse=True)
    return ok([_conv_to_out(c, user["id"]) for c in items])


@router.get("/{conv_id}/messages")
def list_messages(conv_id: str, user: dict = Depends(current_user)) -> dict:
    conv = conversations.find_by_id(conv_id)
    if not conv:
        raise NotFoundError("会话不存在")
    if user["id"] not in (conv["matcher_user_id"], conv["matchee_user_id"]):
        raise ForbiddenError("无权查看")
    return ok([_msg_to_out(m) for m in messages.list_by_conversation(conv_id)])


@router.post("/{conv_id}/messages")
def send_message(
    conv_id: str,
    req: SendMessageRequest,
    user: dict = Depends(current_user),
) -> dict:
    conv = conversations.find_by_id(conv_id)
    if not conv:
        raise NotFoundError("会话不存在")
    if conv["matcher_user_id"] != user["id"]:
        raise ForbiddenError("只有匹配者本人能在此会话发消息")
    result = matcher_agent.handle_matcher_message(conv_id, req.content)
    return ok(result)


@router.post("/{conv_id}/end")
def end_conversation(conv_id: str, user: dict = Depends(current_user)) -> dict:
    conv = conversations.find_by_id(conv_id)
    if not conv:
        raise NotFoundError("会话不存在")
    if conv["matcher_user_id"] != user["id"]:
        raise ForbiddenError("只有匹配者能主动结束")
    if conv["status"] == "active":
        conversations.set_status(conv_id, "ended")
    return ok({"status": "ended"})
