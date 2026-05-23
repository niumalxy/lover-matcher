"""匹配记录模型。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MatchDecision = Literal["pending", "approved", "rejected"]


class MatchDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]


class MatchOut(BaseModel):
    id: str
    conversation_id: str
    matchee_user_id: str
    matcher_user_id: str
    matchee_decision: MatchDecision
    created_at: str
    decided_at: str = ""
    peer_name: str = ""
    peer_avatar_url: str = ""
    peer_contact: str = ""  # 仅在 approved 时返回非空
