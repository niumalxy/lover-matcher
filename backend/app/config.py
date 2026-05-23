"""配置加载：conf.yml（不可变 provider 池）+ runtime.json（运行时可变状态）。"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Any

import yaml

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
CONF_DIR = BASE_DIR / "conf"
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
LOCKS_DIR = DATA_DIR / "locks"

CONF_FILE = CONF_DIR / "conf.yml"
RUNTIME_FILE = CONF_DIR / "runtime.json"

_runtime_lock = Lock()


def ensure_dirs() -> None:
    for d in (DATA_DIR, UPLOADS_DIR, LOCKS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def load_providers() -> dict[str, dict[str, Any]]:
    """返回 conf.yml 中所有 provider 配置；每次读取，不缓存（便于热改）。"""
    if not CONF_FILE.exists():
        raise FileNotFoundError(f"conf.yml 不存在：{CONF_FILE}")
    with open(CONF_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("conf.yml 顶层必须是字典")
    return data


def get_runtime() -> dict[str, Any]:
    if not RUNTIME_FILE.exists():
        return {}
    with open(RUNTIME_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def set_runtime(key: str, value: Any) -> None:
    with _runtime_lock:
        data = get_runtime()
        data[key] = value
        RUNTIME_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RUNTIME_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
