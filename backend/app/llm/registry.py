"""Provider 注册表：读 conf.yml 列出可用 provider，读写 runtime.json 中的默认 provider。"""
from __future__ import annotations

import logging
from typing import Any

from app.config import get_runtime, load_providers, set_runtime

logger = logging.getLogger(__name__)

# 兜底默认 provider；优先读 runtime.json
FALLBACK_PROVIDER = "mimo"


def list_providers() -> dict[str, dict[str, Any]]:
    return load_providers()


def list_provider_names() -> list[str]:
    return list(load_providers().keys())


def get_provider_config(name: str) -> dict[str, Any]:
    providers = load_providers()
    if name not in providers:
        raise ValueError(f"未知 provider: {name}")
    return providers[name]


def get_current_provider_name() -> str:
    name = get_runtime().get("current_provider")
    providers = load_providers()
    if not name or name not in providers:
        if name and name not in providers:
            logger.warning(
                "runtime.current_provider=%s 不在 conf.yml 中，回退到 %s",
                name,
                FALLBACK_PROVIDER,
            )
        return FALLBACK_PROVIDER if FALLBACK_PROVIDER in providers else next(iter(providers))
    return name


def set_current_provider(name: str) -> None:
    if name not in load_providers():
        raise ValueError(f"未知 provider: {name}")
    set_runtime("current_provider", name)
    logger.info("默认 provider 切换为 %s", name)
