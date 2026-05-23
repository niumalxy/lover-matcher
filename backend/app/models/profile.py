"""画像（被匹配者）相关模型。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class StructuredProfile(BaseModel):
    """LLM 提取的结构化画像。保留用户语言风格。"""

    self_intro: str = Field(default="", description="第一人称自我介绍，保留用户措辞风格")
    personality: list[str] = Field(default_factory=list)
    hobbies: list[str] = Field(default_factory=list)
    hard_requirements: list[str] = Field(default_factory=list)
    soft_requirements: list[str] = Field(default_factory=list)
    speaking_style: str = Field(default="", description="供 agent 模仿的说话风格简描")


class ProfileExtractRequest(BaseModel):
    raw_input: str = Field(..., min_length=1)


class ProfilePutRequest(BaseModel):
    raw_input: str
    structured: StructuredProfile


class ProfileOut(BaseModel):
    user_id: str
    raw_input: str
    structured: StructuredProfile
    updated_at: str = ""
