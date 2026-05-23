"""智能恋爱助手：模拟被匹配者画像，与匹配者对话并评估匹配。

核心：单次 LLM 调用同时产出 reply 和 evaluation（JSON mode）。
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.errors import BusinessError, NotFoundError
from app.llm import client
from app.storage import conversations, matches, messages, profiles, users

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "matcher_agent.txt"


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items) if items else "(无)"


def _build_system_prompt(matchee_user: dict[str, str], structured: dict[str, Any]) -> str:
    tmpl = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        tmpl.replace("{{NAME}}", matchee_user.get("name", "") or "(未填)")
        .replace("{{GENDER}}", matchee_user.get("gender", "") or "(未填)")
        .replace("{{SELF_INTRO}}", structured.get("self_intro", "") or "(无)")
        .replace("{{PERSONALITY}}", ", ".join(structured.get("personality", [])) or "(无)")
        .replace("{{HOBBIES}}", ", ".join(structured.get("hobbies", [])) or "(无)")
        .replace("{{SPEAKING_STYLE}}", structured.get("speaking_style", "") or "(无)")
        .replace("{{HARD_REQUIREMENTS}}", _format_list(structured.get("hard_requirements", [])))
        .replace("{{SOFT_REQUIREMENTS}}", _format_list(structured.get("soft_requirements", [])))
    )


def _history_to_messages(history: list[dict[str, str]]) -> list[dict[str, str]]:
    """messages.csv 中 sender=matcher 是 user，sender=agent 是 assistant。"""
    out = []
    for m in history:
        role = "user" if m["sender"] == "matcher" else "assistant"
        out.append({"role": role, "content": m["content"]})
    return out


def handle_matcher_message(conversation_id: str, matcher_input: str) -> dict[str, Any]:
    """处理匹配者的一条消息：

    1. 落库 matcher 消息
    2. 拉历史 + 画像，组 prompt 调 LLM（JSON mode）
    3. 解析 reply + evaluation
    4. 落库 agent 回复，按 evaluation 更新 conversation 状态、必要时创建 match
    5. 返回 {reply, status, match_id?}
    """
    conv = conversations.find_by_id(conversation_id)
    if not conv:
        raise NotFoundError("会话不存在")
    if conv["status"] != "active":
        raise BusinessError(code=4003, msg=f"会话已 {conv['status']}，不能再发消息")

    matchee = users.find_by_id(conv["matchee_user_id"])
    if not matchee:
        raise NotFoundError("被匹配者不存在")
    prof = profiles.find_by_user(matchee["id"])
    if not prof:
        raise BusinessError(code=4004, msg="被匹配者尚未填画像")
    structured = profiles.parse_structured(prof)

    # 1. 先落库 matcher 消息（用户先说话才能让 agent 看到）
    messages.append(conversation_id, "matcher", matcher_input)

    # 2. 组 prompt
    system_prompt = _build_system_prompt(matchee, structured)
    history = messages.list_by_conversation(conversation_id)
    llm_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    llm_messages.extend(_history_to_messages(history))

    raw = client.chat(llm_messages, json_mode=True, max_tokens=1500, temperature=0.7)
    reply, evaluation = _parse_llm_json(raw)

    # 3. 落库 agent 回复
    messages.append(conversation_id, "agent", reply)

    # 4. 按 evaluation 流转状态
    decision = evaluation.get("decision", "continue")
    match_id: str | None = None
    new_status = "active"
    if decision == "sufficient":
        new_status = "matched"
        conversations.set_status(conversation_id, "matched")
        match_row = matches.create(
            conversation_id=conversation_id,
            matchee_id=conv["matchee_user_id"],
            matcher_id=conv["matcher_user_id"],
        )
        match_id = match_row["id"]
        logger.info("会话 %s 判定匹配，match=%s 理由=%s", conversation_id, match_id, evaluation.get("reason"))
    elif decision == "insufficient":
        new_status = "ended"
        conversations.set_status(conversation_id, "ended")
        logger.info("会话 %s 判定不合适，结束。理由=%s", conversation_id, evaluation.get("reason"))

    return {
        "reply": reply,
        "status": new_status,
        "match_id": match_id,
        "evaluation_reason": evaluation.get("reason", ""),  # 调试用，可考虑前端不展示
    }


def _parse_llm_json(raw: str) -> tuple[str, dict[str, Any]]:
    try:
        data = json.loads(raw)
        reply = str(data.get("reply", "")).strip()
        evaluation = data.get("evaluation") or {}
        if not isinstance(evaluation, dict):
            evaluation = {}
        if not reply:
            raise ValueError("reply 为空")
        return reply, evaluation
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("LLM JSON 解析失败: %s | raw=%s", e, raw[:300])
        # 兜底：把整段当 reply，evaluation 默认 continue
        return raw or "（系统暂时没听清，能再说一遍吗？）", {"decision": "continue", "reason": "fallback"}
