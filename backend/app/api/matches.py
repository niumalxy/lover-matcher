"""/api/v1/matches —— 匹配记录与决策。"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.models.common import ok
from app.models.match import MatchDecisionRequest
from app.services import match as match_service
from app.services.auth import current_user

router = APIRouter(prefix="/api/v1/matches", tags=["matches"])


@router.get("/pending")
def pending(user: dict = Depends(current_user)) -> dict:
    return ok(match_service.list_pending_for_matchee(user["id"]))


@router.get("/mine")
def mine(user: dict = Depends(current_user)) -> dict:
    return ok(match_service.list_for_user(user["id"]))


@router.post("/{match_id}/decision")
def decide(
    match_id: str, req: MatchDecisionRequest, user: dict = Depends(current_user)
) -> dict:
    return ok(match_service.decide(match_id, user["id"], req.decision))


@router.get("/{match_id}")
def detail(match_id: str, user: dict = Depends(current_user)) -> dict:
    return ok(match_service.get_detail(match_id, user["id"]))
