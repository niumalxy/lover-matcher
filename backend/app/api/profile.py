"""/api/v1/profile —— 被匹配者画像 + 择偶标准。"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from app.models.common import ok
from app.models.profile import ProfileExtractRequest, ProfileOut, ProfilePutRequest
from app.services import profile as profile_service
from app.services.auth import current_user
from app.storage import profiles

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.post("/extract")
def extract(req: ProfileExtractRequest, _user: dict = Depends(current_user)) -> dict:
    structured = profile_service.extract_structured(req.raw_input)
    return ok({"structured": structured})


@router.put("")
def upsert_profile(req: ProfilePutRequest, user: dict = Depends(current_user)) -> dict:
    row = profiles.upsert(user["id"], req.raw_input, req.structured.model_dump())
    return ok(_profile_to_out(row))


@router.get("")
def get_profile(user: dict = Depends(current_user)) -> dict:
    row = profiles.find_by_user(user["id"])
    if not row:
        return ok(None)
    return ok(_profile_to_out(row))


def _profile_to_out(row: dict[str, str]) -> dict:
    return ProfileOut(
        user_id=row["user_id"],
        raw_input=row.get("raw_input", ""),
        structured=profiles.parse_structured(row),  # type: ignore[arg-type]
        updated_at=row.get("updated_at", ""),
    ).model_dump()
