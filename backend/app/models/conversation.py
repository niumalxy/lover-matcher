"""对话/消息模型。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ConversationStatus = Literal["active", "matched", "ended", "blacklisted"]
MessageSender = Literal["matcher", "agent"]


class StartConversationRequest(BaseModel):
    matchee_user_id: str


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender: MessageSender
    content: str
    created_at: str


class ConversationOut(BaseModel):
    id: str
    matchee_user_id: str
    matcher_user_id: str
    status: ConversationStatus
    created_at: str
    updated_at: str
    peer_name: str = ""
    peer_avatar_url: str = ""
