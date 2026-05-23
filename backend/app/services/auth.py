"""鉴权：从 X-OpenId 头注入当前用户。MVP 简化方案。"""
from __future__ import annotations

from fastapi import Header

from app.errors import AuthError
from app.storage import users


def current_user(x_openid: str | None = Header(default=None, alias="X-OpenId")) -> dict[str, str]:
    if not x_openid:
        raise AuthError("缺少 X-OpenId 请求头")
    user = users.find_by_openid(x_openid)
    if not user:
        raise AuthError("用户未注册，请先调用 /api/v1/auth/login")
    return user


def current_user_optional(
    x_openid: str | None = Header(default=None, alias="X-OpenId"),
) -> dict[str, str] | None:
    if not x_openid:
        return None
    return users.find_by_openid(x_openid)
