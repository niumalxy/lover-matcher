"""/api/v1/users/* —— 当前用户信息与头像上传。"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import UPLOADS_DIR
from app.errors import BusinessError
from app.models.common import ok
from app.models.user import UserOut, UserUpdateRequest
from app.services.auth import current_user
from app.storage import users

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/users", tags=["users"])

ALLOWED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5MB


def _user_to_out(row: dict[str, str]) -> dict:
    avatar_path = row.get("avatar_path") or ""
    avatar_url = f"/uploads/{Path(avatar_path).name}" if avatar_path else ""
    return UserOut(
        id=row["id"],
        openid=row["openid"],
        name=row.get("name", ""),
        gender=row.get("gender", "") or "",
        expected_gender=row.get("expected_gender", "") or "",
        contact=row.get("contact", ""),
        avatar_url=avatar_url,
        roles=row.get("roles", ""),
    ).model_dump()


@router.get("/me")
def get_me(user: dict = Depends(current_user)) -> dict:
    return ok(_user_to_out(user))


@router.put("/me")
def update_me(req: UserUpdateRequest, user: dict = Depends(current_user)) -> dict:
    users.update(user["id"], req.model_dump(exclude_none=True))
    updated = users.find_by_id(user["id"]) or user
    return ok(_user_to_out(updated))


@router.post("/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict = Depends(current_user),
) -> dict:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise BusinessError(code=4001, msg=f"不支持的图片类型：{ext}")
    data = await file.read()
    if len(data) > MAX_AVATAR_BYTES:
        raise BusinessError(code=4002, msg="图片超过 5MB 限制")
    filename = f"{user['id']}_{uuid.uuid4().hex[:8]}{ext}"
    target = UPLOADS_DIR / filename
    target.write_bytes(data)
    rel = f"uploads/{filename}"
    users.update(user["id"], {"avatar_path": rel})
    logger.info("用户 %s 上传头像 -> %s", user["id"], rel)
    return ok({"avatar_url": f"/uploads/{filename}"})
