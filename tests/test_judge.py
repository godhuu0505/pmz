"""条件付き自律ルール版判定の単体テスト（要件 §3.4 / §7 #5）。"""

from gatekeeper.core.decision import AutonomyLevel
from gatekeeper.core.judge import judge
from gatekeeper.models import CISignal, CodeSignal, RiskFlag, Verdict
from gatekeeper.signals import (
    CriterionResult,
    CriterionStatus,
    GateSignals,
    RequirementAssessment,
)


def _code(*flags: RiskFlag) -> CodeSignal:
    return CodeSignal(diff_summary="x", risk_flags=list(flags), lines_changed=10)


def _green_ci() -> CISignal:
    return CISignal(tests_pass=True, coverage=0.9)


def _met(confidence: float) -> RequirementAssessment:
    return RequirementAssessment(
        results=[CriterionResult(criterion="c", status=CriterionStatus.MET, confidence=confidence)]
    )


def test_auto_approve_when_all_green_high_confidence_no_risk() -> None:
    # §7 #5: 確信度≥T・全緑・高リスクなし・受け入れ基準充足 → 自律承認。
    sig = GateSignals(code=_code(), ci=_green_ci(), requirement=_met(0.95))
    d = judge(sig)
    assert d.verdict is Verdict.GO
    assert d.autonomy is AutonomyLevel.AUTO_APPROVE
    assert d.is_autonomous is True
    assert "auto_approve" in d.fired_rules


def test_hard_guard_blocks_auto_approve_even_when_green() -> None:
    # §7 #5 / インバリアント #3: 高リスク領域は確信度に関係なく自律承認禁止。
    sig = GateSignals(code=_code(RiskFlag.DB_MIGRATION), ci=_green_ci(), requirement=_met(0.99))
    d = judge(sig)
    assert d.verdict is Verdict.GO
    assert d.autonomy is AutonomyLevel.HUMAN_REVIEW
    assert d.hard_guarded is True
    assert "hard_guard" in d.fired_rules


def test_ci_red_is_autonomous_block() -> None:
    sig = GateSignals(
        code=_code(),
        ci=CISignal(tests_pass=False),
        requirement=_met(0.99),
    )
    d = judge(sig)
    assert d.verdict is Verdict.NO_GO
    assert d.autonomy is AutonomyLevel.AUTO_BLOCK
    assert "ci_not_green" in d.fired_rules


def test_unmet_criterion_is_autonomous_block() -> None:
    sig = GateSignals(
        code=_code(),
        ci=_green_ci(),
        requirement=RequirementAssessment(
            results=[CriterionResult(criterion="c", status=CriterionStatus.UNMET, confidence=0.9)]
        ),
    )
    d = judge(sig)
    assert d.verdict is Verdict.NO_GO
    assert d.autonomy is AutonomyLevel.AUTO_BLOCK
    assert "requirement_unmet" in d.fired_rules


def test_unverifiable_escalates_to_human() -> None:
    # §3.2.1: 「検証不能」は断定せず人間にエスカレーション（棄権）。
    sig = GateSignals(
        code=_code(),
        ci=_green_ci(),
        requirement=RequirementAssessment(
            results=[CriterionResult(criterion="c", status=CriterionStatus.UNVERIFIABLE)]
        ),
    )
    d = judge(sig)
    assert d.autonomy is AutonomyLevel.HUMAN_REVIEW
    assert d.needs_human is True
    assert "requirement_unverifiable" in d.fired_rules


def test_low_confidence_escalates_to_human() -> None:
    sig = GateSignals(code=_code(), ci=_green_ci(), requirement=_met(0.5))
    d = judge(sig)
    assert d.autonomy is AutonomyLevel.HUMAN_REVIEW
    assert "low_confidence" in d.fired_rules


def test_empty_assessment_does_not_auto_approve() -> None:
    # 申告基準なし＝充足を確認できていない → 自律承認しない（保守的デフォルト・§3.4）。
    sig = GateSignals(code=_code(), ci=_green_ci(), requirement=RequirementAssessment())
    d = judge(sig)
    assert d.autonomy is AutonomyLevel.HUMAN_REVIEW
