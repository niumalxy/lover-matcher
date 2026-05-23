"""CSV 通用读写：文件级锁（filelock）+ 原子重写。

约定：所有写操作必须经此模块，不允许 service/api 层直接 open() 写 CSV。
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable

from filelock import FileLock

from app.config import LOCKS_DIR

logger = logging.getLogger(__name__)


def _lock_for(csv_path: Path, timeout: int = 10) -> FileLock:
    LOCKS_DIR.mkdir(parents=True, exist_ok=True)
    return FileLock(str(LOCKS_DIR / f"{csv_path.name}.lock"), timeout=timeout)


def ensure_csv(path: Path, headers: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(headers)


def read_all(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def find_one(path: Path, **filters: str) -> dict[str, str] | None:
    for row in read_all(path):
        if all(row.get(k) == v for k, v in filters.items()):
            return row
    return None


def find_all(path: Path, **filters: str) -> list[dict[str, str]]:
    return [
        row
        for row in read_all(path)
        if all(row.get(k) == v for k, v in filters.items())
    ]


def append_row(path: Path, headers: list[str], row: dict[str, str]) -> None:
    ensure_csv(path, headers)
    with _lock_for(path):
        with open(path, "a", encoding="utf-8", newline="") as f:
            csv.DictWriter(f, fieldnames=headers).writerow(row)


def update_rows(
    path: Path,
    headers: list[str],
    match: dict[str, str],
    update: dict[str, str],
) -> int:
    """更新匹配 match 的行，返回更新条数。整文件原子重写。"""
    with _lock_for(path):
        rows = read_all(path)
        n = 0
        for row in rows:
            if all(row.get(k) == v for k, v in match.items()):
                row.update(update)
                n += 1
        if n:
            _rewrite(path, headers, rows)
    return n


def _rewrite(path: Path, headers: list[str], rows: Iterable[dict[str, str]]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(path)
