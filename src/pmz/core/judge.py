"""条件付き自律のルール版判定（要件 §3.4 / §7 #5 — LLMなしの骨格）.

W1 死守ラインの土台。**まず LLM なしの決定論ルールでグリーンにする**ための判定コア。
要件充足の 3値判定（``RequirementAssessment``）は外から渡す（将来 LLM / `/trace` が生成）。
このモジュール自身は決定論で、単体テストから書ける。

判定方針（§3.4 条件付き自律 ＋ §7 #5 自律承認条件）:

- **客観的 No-Go → 自律ブロック**: CIが緑でない、または受け入れ基準に「満たさない」がある。
  良くないリリースを自律で止めるのは安全側（選択バイアスは許容・§3.3.1）。
- **自律承認（AUTO_APPROVE）は全条件を満たす時だけ**（§7 #5）:
  確信度 ≥ T かつ 客観ゲート全緑 かつ 高リスクフラグなし（ハードガード非作動）かつ
  受け入れ基準が「検証不能」を含まず充足。
- **それ以外は人間承認（HUMAN_REVIEW）**: ハードガード作動 / 「検証不能」あり /
  確信度不足。迷えば人間が保守的デフォルト（§3.4）。
"""

from __future__ import annotations

from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.core.hard_guard import hard_guarded_flags
from pmz.models import ReleaseRecord, Verdict
from pmz.signals import GateSignals, RequirementAssessment, build_signals

# 自律承認に要する確信度の下限 T（§7 #5）。自己改善ループ(C)の評価で継続調整する対象（§3.4）。
CONFIDENCE_THRESHOLD = 0.8

MODEL_VERSION = "rule-based-v0"


def judge(signals: GateSignals, *, threshold: float = CONFIDENCE_THRESHOLD) -> GateDecision:
    """客観シグナルから条件付き自律の判定を下す（決定論・§3.4 / §7 #5）。"""
    fired: list[str] = []
    rationale: list[str] = []

    guarded = hard_guarded_flags(signals.risk_flags())
    is_guarded = bool(guarded)

    ci_green = signals.ci_all_green()
    req = signals.requirement

    # 1) 客観的 No-Go → 自律ブロック（CI赤 / 受け入れ基準が「満たさない」）。
    if not ci_green:
        fired.append("ci_not_green")
        rationale.append("CIが全緑ではない（test/lint/build/security_scan のいずれか不合格）。")
    if req.has_unmet():
        fired.append("requirement_unmet")
        rationale.append("受け入れ基準に「満たさない」項目がある（要件未達・§3.2.1）。")

    if not ci_green or req.has_unmet():
        return GateDecision(
            verdict=Verdict.NO_GO,
            autonomy=AutonomyLevel.AUTO_BLOCK,
            confidence=1.0,  # 客観イベントに基づく決定論的 No-Go
            rationale=rationale,
            fired_rules=fired,
            hard_guarded=is_guarded,
            model_version=MODEL_VERSION,
        )

    # ここから CI 全緑 かつ 「満たさない」なし。自律承認の可否を順に削る（§7 #5）。
    confidence = req.min_confidence()

    # 2) ハードガード作動 → 確信度に関係なく自律承認禁止（§7 #5 / インバリアント #3）。
    if is_guarded:
        fired.append("hard_guard")
        rationale.append(
            "高リスク領域（" + ", ".join(f.value for f in guarded) + "）のため自律承認を禁止。"
        )
        return GateDecision(
            verdict=Verdict.GO,
            autonomy=AutonomyLevel.HUMAN_REVIEW,
            confidence=confidence,
            rationale=rationale,
            fired_rules=fired,
            hard_guarded=True,
            model_version=MODEL_VERSION,
        )

    # 3) 「検証不能」を含む → 断定せず人間にエスカレーション（§3.2.1 棄権）。
    if req.has_unverifiable() or not req.all_met():
        fired.append("requirement_unverifiable")
        rationale.append(
            "受け入れ基準に「検証不能」または未確認があり断定できない（人間にエスカレーション・§3.2.1）。"
        )
        return GateDecision(
            verdict=Verdict.GO,
            autonomy=AutonomyLevel.HUMAN_REVIEW,
            confidence=confidence,
            rationale=rationale,
            fired_rules=fired,
            hard_guarded=False,
            model_version=MODEL_VERSION,
        )

    # 4) 確信度不足 → 人間承認（§3.4 中リスク）。
    if confidence < threshold:
        fired.append("low_confidence")
        rationale.append(f"確信度 {confidence:.2f} が閾値 {threshold:.2f} 未満。")
        return GateDecision(
            verdict=Verdict.GO,
            autonomy=AutonomyLevel.HUMAN_REVIEW,
            confidence=confidence,
            rationale=rationale,
            fired_rules=fired,
            hard_guarded=False,
            model_version=MODEL_VERSION,
        )

    # 5) 全条件クリア → 自律実行（§7 #5）。
    fired.append("auto_approve")
    rationale.append(
        "客観ゲート全緑・高リスクなし・受け入れ基準すべて充足・確信度十分のため自律承認。"
    )
    return GateDecision(
        verdict=Verdict.GO,
        autonomy=AutonomyLevel.AUTO_APPROVE,
        confidence=confidence,
        rationale=rationale,
        fired_rules=fired,
        hard_guarded=False,
        model_version=MODEL_VERSION,
    )


def judge_record(
    record: ReleaseRecord,
    assessment: RequirementAssessment | None = None,
    *,
    threshold: float = CONFIDENCE_THRESHOLD,
) -> GateDecision:
    """``ReleaseRecord`` を判定する薄いラッパ（合成データのバックテスト用）。

    ``assessment`` を省略すると要件充足は全件「検証不能」となり、CIが緑でも
    人間承認に落ちる（LLMなしの保守的既定・§3.2.1）。
    """
    return judge(build_signals(record, assessment), threshold=threshold)
