"""LLM 冒烟测试。

用法（在 backend/ 目录下）：
    uv run python -m scripts.test_llm
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows 终端默认 cp936，强制 stdout 走 UTF-8 防止中文乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 让 scripts 能 import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm import client  # noqa: E402
from app.llm.registry import get_current_provider_name, list_provider_names  # noqa: E402
from app.logging_setup import setup_logging  # noqa: E402


def main() -> None:
    setup_logging()
    print(f"可用 provider: {list_provider_names()}")
    provider = get_current_provider_name()
    print(f"当前默认 provider: {provider}")
    reply = client.chat(
        messages=[
            {"role": "system", "content": "你是一个简短回答的测试助手。"},
            {"role": "user", "content": "请用一句话证明你在工作，包含当前年份。"},
        ],
        max_tokens=200,
    )
    print(f"LLM 回复:\n{reply}")


if __name__ == "__main__":
    main()
