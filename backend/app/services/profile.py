"""画像服务：用 LLM 把自由文本转结构化择偶画像。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.llm import client
from app.models.profile import StructuredProfile

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "profile_extract.txt"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_structured(raw_input: str) -> dict[str, Any]:
    """调用 LLM 把 raw_input 转为 StructuredProfile 形状的 dict。失败时返回空骨架。"""
    prompt = _load_prompt().replace("{{RAW_INPUT}}", raw_input)
    reply = client.chat(
        messages=[
            {"role": "system", "content": "你是一个画像分析助手，严格按要求返回 JSON。"},
            {"role": "user", "content": prompt},
        ],
        json_mode=True,
        max_tokens=2000,
        temperature=0.3,
    )
    try:
        data = json.loads(reply)
    except json.JSONDecodeError:
        logger.warning("画像提取 LLM 返回非 JSON: %s", reply[:200])
        data = {}
    # 用 Pydantic 校验+补齐默认字段，结果回到 dict 返回
    return StructuredProfile.model_validate(data).model_dump()
