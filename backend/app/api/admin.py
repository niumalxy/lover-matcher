"""/admin —— 后台管理（浏览器访问 + JSON API）。

鉴权：所有 /admin/api/* 接口要求请求头 `X-Admin-Token`，与环境变量 `ADMIN_TOKEN` 比对。
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.errors import AuthError, BusinessError
from app.llm import registry as llm_registry
from app.models.common import ok
from app.storage import base
from app.storage import users as users_storage
from app.storage.matches import MATCHES_CSV

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_TOKEN = "1024213619"

ADMIN_HTML = Path(__file__).resolve().parent.parent / "admin_web" / "index.html"


def _expected_token() -> str:
    return os.getenv("ADMIN_TOKEN", DEFAULT_ADMIN_TOKEN)


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    if x_admin_token != _expected_token():
        raise AuthError("admin token 错误")


page_router = APIRouter(tags=["admin"])
api_router = APIRouter(prefix="/admin/api", tags=["admin"], dependencies=[Depends(require_admin)])


@page_router.get("/admin", response_class=HTMLResponse)
def admin_page() -> HTMLResponse:
    return HTMLResponse(ADMIN_HTML.read_text(encoding="utf-8"))


class SetProviderRequest(BaseModel):
    name: str


@api_router.get("/providers")
def list_providers() -> dict:
    """列 provider 名 + 模型，**不返回 key**。"""
    out = []
    for name, cfg in llm_registry.list_providers().items():
        out.append({"name": name, "model": cfg.get("model", ""), "api_base": cfg.get("api_base", "")})
    return ok(out)


@api_router.get("/providers/current")
def current_provider() -> dict:
    return ok({"name": llm_registry.get_current_provider_name()})


@api_router.put("/providers/current")
def set_current(req: SetProviderRequest) -> dict:
    try:
        llm_registry.set_current_provider(req.name)
    except ValueError as e:
        raise BusinessError(code=4007, msg=str(e))
    return ok({"name": req.name})


@api_router.get("/candidates")
def all_candidates() -> dict:
    """列出所有 matchee 用户（含画像状态）。"""
    out = []
    for u in users_storage.list_by_role("matchee"):
        out.append(
            {
                "user_id": u["id"],
                "name": u.get("name", ""),
                "gender": u.get("gender", ""),
                "openid": u.get("openid", ""),
            }
        )
    return ok(out)


@api_router.get("/matches")
def all_matches() -> dict:
    """列出所有 match 记录。admin 视角；contact 不暴露。"""
    all_rows = base.read_all(MATCHES_CSV)
    out = []
    for r in all_rows:
        matchee = users_storage.find_by_id(r["matchee_user_id"]) or {}
        matcher = users_storage.find_by_id(r["matcher_user_id"]) or {}
        out.append(
            {
                "id": r["id"],
                "conversation_id": r["conversation_id"],
                "matchee_name": matchee.get("name", ""),
                "matcher_name": matcher.get("name", ""),
                "decision": r["matchee_decision"],
                "created_at": r["created_at"],
                "decided_at": r.get("decided_at", ""),
            }
        )
    return ok(out)
