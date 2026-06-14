"""合成リリース履歴（要件 §9.1）のロード。

``synthetic_releases.json`` は手作りのデモ用データセット（~24件・trap→learn→catch）。
``correct_verdict`` は **合成データだから正解を仕込める** 前提であり、実運用では成立しない
（§9.1 / インバリアント #7）。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pmz.models import ReleaseRecord

_DATA_FILE = Path(__file__).with_name("synthetic_releases.json")


@lru_cache(maxsize=1)
def load_synthetic_releases() -> list[ReleaseRecord]:
    """合成リリース履歴を読み込み、timestamp 昇順で返す（バックテストの時系列順）。"""
    raw = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    records = [ReleaseRecord.model_validate(r) for r in raw]
    records.sort(key=lambda r: r.timestamp)
    return records
