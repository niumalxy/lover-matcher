"""/api/v1/auth/* —— 登录与 openid 换取。"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.models.common import ok
from app.models.user import LoginRequest
from app.storage import users

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# MVP: dev_mode 直接把 code 当作 openid。生产再接微信 jscode2session。
DEV_MODE = True


@router.post("/login")
def login(req: LoginRequest) -> dict:
    if DEV_MODE:
        openid = req.code
    else:
        raise NotImplementedError("生产模式微信换码尚未实现")
    user = users.find_by_openid(openid)
    if not user:
        user = users.create_minimal(openid)
        logger.info("自动创建新用户 openid=%s id=%s", openid, user["id"])
    return ok({"openid": openid, "user_id": user["id"]})
