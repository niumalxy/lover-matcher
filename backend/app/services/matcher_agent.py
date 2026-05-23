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
from app.storage import blacklist, conversations, matches, messages, profiles, users

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "matcher_agent.txt"
OPENING_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "matcher_agent_opening.txt"


def _format_list(items: list[str]) -> str:
    return "\n".join(f"- {x}" for x in items) if items else "(无)"


PRIORITY_LABEL = {"low": "低", "medium": "中", "high": "高"}


def _format_custom_questions(questions: list[dict]) -> str:
    if not questions:
        return "（无）"
    lines = []
    for q in questions:
        priority = PRIORITY_LABEL.get(q.get("priority", "medium"), "中")
        lines.append(f"- [{priority}] {q.get('question', '')}")
        if q.get("ideal_answer"):
            lines.append(f"  理想回答：{q.get('ideal_answer')}")
    return "\n".join(lines)


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
        .replace("{{CUSTOM_QUESTIONS}}", _format_custom_questions(structured.get("custom_questions", [])))
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
    elif decision == "blacklist":
        new_status = "blacklisted"
        conversations.set_status(conversation_id, "blacklisted")
        blacklist.ensure()
        blacklist.add_block(
            blocker_id=conv["matchee_user_id"],
            blocked_id=conv["matcher_user_id"],
            reason=evaluation.get("reason", ""),
        )
        logger.info("会话 %s 被匹配者拉黑匹配者，理由=%s", conversation_id, evaluation.get("reason"))
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


def generate_opening(conversation_id: str) -> str:
    """创建会话后，由 agent 发出第一句问候。"""
    conv = conversations.find_by_id(conversation_id)
    if not conv:
        raise NotFoundError("会话不存在")
    matchee = users.find_by_id(conv["matchee_user_id"])
    matcher_user = users.find_by_id(conv["matcher_user_id"])
    if not matchee or not matcher_user:
        raise NotFoundError("用户不存在")
    prof = profiles.find_by_user(matchee["id"])
    if not prof:
        raise BusinessError(code=4004, msg="被匹配者尚未填画像")
    structured = profiles.parse_structured(prof)

    matcher_prof = profiles.find_by_user(matcher_user["id"])
    matcher_structured = profiles.parse_structured(matcher_prof) if matcher_prof else {}

    tmpl = OPENING_PROMPT_PATH.read_text(encoding="utf-8")
    system_prompt = (
        tmpl.replace("{{NAME}}", matchee.get("name", "") or "(未填)")
        .replace("{{GENDER}}", matchee.get("gender", "") or "(未填)")
        .replace("{{SELF_INTRO}}", structured.get("self_intro", "") or "(无)")
        .replace("{{PERSONALITY}}", ", ".join(structured.get("personality", [])) or "(无)")
        .replace("{{HOBBIES}}", ", ".join(structured.get("hobbies", [])) or "(无)")
        .replace("{{SPEAKING_STYLE}}", structured.get("speaking_style", "") or "(无)")
        .replace("{{MATCHER_NAME}}", matcher_user.get("name", "") or "(未填)")
        .replace("{{MATCHER_GENDER}}", matcher_user.get("gender", "") or "(未填)")
        .replace("{{MATCHER_SELF_INTRO}}", matcher_structured.get("self_intro", "") or "(未填)")
        .replace("{{MATCHER_PERSONALITY}}", ", ".join(matcher_structured.get("personality", [])) or "(无)")
        .replace("{{MATCHER_HOBBIES}}", ", ".join(matcher_structured.get("hobbies", [])) or "(无)")
    )

    llm_messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "请以被匹配者的身份发起开场白，说第一句话。"},
    ]

    raw = client.chat(llm_messages, json_mode=True, max_tokens=300, temperature=0.8)
    reply, _ = _parse_llm_json(raw)

    messages.append(conversation_id, "agent", reply)
    logger.info("会话 %s agent 开场白已发送", conversation_id)
    return reply
