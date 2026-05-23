"""用户/画像/对话/匹配的 Pydantic 模型（请求体 + 出参 DTO）。"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Gender = Literal["M", "F"]
ExpectedGender = Literal["M", "F", "ANY"]


class LoginRequest(BaseModel):
    code: str = Field(..., description="微信 wx.login 拿到的 code；dev_mode 下作为 openid 直传")


class UserOut(BaseModel):
    id: str
    openid: str
    name: str = ""
    gender: Gender | Literal[""] = ""
    expected_gender: ExpectedGender | Literal[""] = ""
    contact: str = ""
    avatar_url: str = ""
    roles: str = ""


class UserUpdateRequest(BaseModel):
    name: str | None = None
    gender: Gender | None = None
    expected_gender: ExpectedGender | None = None
    contact: str | None = None
