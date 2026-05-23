"""业务异常 + 统一 JSON 异常响应。"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class BusinessError(Exception):
    def __init__(self, code: int, msg: str, data: Any = None, http_status: int = 400) -> None:
        self.code = code
        self.msg = msg
        self.data = data
        self.http_status = http_status
        super().__init__(msg)


class AuthError(BusinessError):
    def __init__(self, msg: str = "未认证") -> None:
        super().__init__(code=401, msg=msg, http_status=401)


class NotFoundError(BusinessError):
    def __init__(self, msg: str = "资源不存在") -> None:
        super().__init__(code=404, msg=msg, http_status=404)


class ForbiddenError(BusinessError):
    def __init__(self, msg: str = "无权限") -> None:
        super().__init__(code=403, msg=msg, http_status=403)


async def business_error_handler(request: Request, exc: BusinessError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "msg": exc.msg, "data": exc.data},
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": 422, "msg": "参数错误", "data": exc.errors()},
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("未处理异常: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "服务器内部错误", "data": None},
    )
