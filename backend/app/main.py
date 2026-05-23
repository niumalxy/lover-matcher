"""FastAPI 应用入口。

启动：
    cd backend && uv run uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.api import admin as admin_api
from app.api import auth as auth_api
from app.api import candidates as candidates_api
from app.api import conversations as conversations_api
from app.api import matches as matches_api
from app.api import profile as profile_api
from app.api import users as users_api
from app.config import UPLOADS_DIR, ensure_dirs
from app.errors import (
    BusinessError,
    business_error_handler,
    generic_error_handler,
    validation_error_handler,
)
from app.logging_setup import setup_logging

setup_logging()
ensure_dirs()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Lover-Matcher Backend",
    version="0.1.0",
    description="恋爱匹配平台 MVP 后端",
)

app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

app.include_router(auth_api.router)
app.include_router(users_api.router)
app.include_router(profile_api.router)
app.include_router(candidates_api.router)
app.include_router(conversations_api.router)
app.include_router(matches_api.router)
app.include_router(admin_api.page_router)
app.include_router(admin_api.api_router)


@app.get("/healthz", tags=["meta"])
def healthz() -> dict:
    return {"code": 0, "msg": "ok", "data": {"status": "alive"}}


logger.info("Lover-Matcher backend initialized")
