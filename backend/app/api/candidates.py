"""/api/v1/candidates —— 候选池查询。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.errors import NotFoundError
from app.models.common import ok
from app.services import candidate as candidate_service
from app.services.auth import current_user

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


@router.get("")
def list_candidates(
    user: dict = Depends(current_user),
    gender: str | None = Query(default=None, description="M/F，不传则不限"),
) -> dict:
    return ok(candidate_service.list_candidates(user, gender=gender))


@router.get("/{user_id}")
def get_candidate(user_id: str, _user: dict = Depends(current_user)) -> dict:
    detail = candidate_service.get_detail(user_id)
    if not detail:
        raise NotFoundError("候选者不存在或未填画像")
    return ok(detail)
