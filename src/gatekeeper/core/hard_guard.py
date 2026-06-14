"""決定論的ハードガード（要件 §7 #5 / 設計インバリアント #3）.

決済・認証・DBマイグレーション等の高リスク領域は、**LLMの確信度に関係なく
自律承認を禁止**する。確信度はLLMの自己申告であり、ハルシネーション時には確信度も
嘘になり得るため、LLMが覆せない決定論的な壁を別に持つことが肝（§7 #5 補足）。

このモジュールはルール（どのフラグがハードガード対象か）の単一の出どころ。
``models.RiskFlag`` を再利用し、ロジックは純粋関数として単体テスト可能にしている。
"""

from __future__ import annotations

from collections.abc import Iterable

from gatekeeper.models import RiskFlag

# 現状すべての RiskFlag がハードガード対象（db_migration / auth / payment・§7 #5）。
# 将来リスク領域を細分化しても、ここだけ変えれば自律承認禁止の範囲が決まる。
HARD_GUARDED_FLAGS: frozenset[RiskFlag] = frozenset(RiskFlag)


def hard_guarded_flags(flags: Iterable[RiskFlag]) -> list[RiskFlag]:
    """与えられたフラグのうちハードガード対象のものを返す（監査証跡の根拠用）。"""
    return [f for f in flags if f in HARD_GUARDED_FLAGS]


def is_hard_guarded(flags: Iterable[RiskFlag]) -> bool:
    """ハードガードが作動するか（＝自律承認を禁止すべきか・§7 #5）。

    ``ReleaseRecord.has_hard_guard_risk()`` と同じ判定をフラグ列に対して行う純粋関数。
    """
    return bool(hard_guarded_flags(flags))
