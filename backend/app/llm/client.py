"""LLM 调用统一入口。所有业务层必须经此调用，不要直接 import openai。"""
from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI

from app.llm.registry import get_current_provider_name, get_provider_config

logger = logging.getLogger(__name__)

_clients: dict[str, OpenAI] = {}


def _get_client(provider: str) -> tuple[OpenAI, dict[str, Any]]:
    cfg = get_provider_config(provider)
    if provider not in _clients:
        _clients[provider] = OpenAI(api_key=cfg["api_key"], base_url=cfg["api_base"])
    return _clients[provider], cfg


def chat(
    messages: list[dict[str, str]],
    provider: str | None = None,
    json_mode: bool = False,
    max_tokens: int | None = None,
    temperature: float = 0.7,
) -> str:
    """同步调用 LLM 聊天接口，返回 assistant 消息内容。

    provider=None 时使用 admin 设定的当前默认 provider。
    json_mode=True 时要求模型返回 JSON（兼容 OpenAI response_format）。
    """
    name = provider or get_current_provider_name()
    client, cfg = _get_client(name)
    kwargs: dict[str, Any] = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    logger.info("LLM call provider=%s model=%s json_mode=%s", name, cfg["model"], json_mode)
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""
