"""自己改善バックテストの統合テスト（要件 §6.1 / §9.1 — デモの心臓）.

「見逃す → 学習 → 検知」が合成データで成立し、KPI（§6.1）を満たすことを保証する。
"""

from __future__ import annotations

from pmz.data import load_synthetic_releases
from pmz.eval.backtest import run_self_improvement
from pmz.models import Act, Verdict


def test_synthetic_dataset_has_24_records() -> None:
    records = load_synthetic_releases()
    assert len(records) == 24
    # タイムスタンプ昇順（バックテストの時系列順）。
    assert records == sorted(records, key=lambda r: r.timestamp)


def test_self_improvement_reduces_false_approve_to_zero() -> None:
    result = run_self_improvement()
    # KPI #1: 誤承認率を大幅削減（学習前は見逃しありで >0、学習後は 0）。
    assert result.before.false_approve_rate > 0
    assert result.after.false_approve_rate == 0.0


def test_recurrence_detection_rate_is_100_percent() -> None:
    # KPI #2: 再発アーキタイプ検知率 = 100%（唯一100%と言える強KPI・デモの山場）。
    result = run_self_improvement()
    assert result.recurrence_detection_rate == 1.0


def test_false_block_rate_not_worsened() -> None:
    # KPI #3: 誤ブロック率を悪化させない（健全性の担保）。
    result = run_self_improvement()
    assert result.after.false_block_rate <= result.before.false_block_rate
    assert result.after.f_beta() >= result.before.f_beta()


def test_traps_missed_then_catches_blocked() -> None:
    # 物語の核: trap は学習前に見逃され、catch は学習後に検知ブロックされる。
    result = run_self_improvement()
    for rec, before, after in result.timeline:
        if rec.arc.act is Act.TRAP:
            assert before.verdict is Verdict.GO  # 学習前は見逃し（誤承認）
            assert after.verdict is Verdict.NO_GO  # 学習後は検知
        if rec.arc.act is Act.CATCH:
            assert after.verdict is Verdict.NO_GO  # 再来は必ず検知


def test_two_rules_learned() -> None:
    result = run_self_improvement()
    assert result.rulebook.version == 2
    archetypes = {r.archetype for r in result.rulebook.rules}
    assert len(archetypes) == 2  # db_migration と requirement_miss の両型を学習
