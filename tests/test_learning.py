"""自己改善コアの単体テスト（要件 §3.3.1）。"""

from __future__ import annotations

from datetime import datetime

from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.core.judge import judge
from pmz.eval.metrics import confusion_matrix
from pmz.learning.memory import CaseMemory, MisjudgedCase
from pmz.learning.retrospective import is_confirmed_bad, learn_rule_from
from pmz.learning.rulebook import LearnedRule, RuleAction, Rulebook
from pmz.models import (
    Arc,
    Archetype,
    CISignal,
    CodeSignal,
    IncidentAxis,
    IncidentValue,
    Labels,
    LabelStatus,
    ReleaseRecord,
    RequirementAxis,
    RequirementSignal,
    RequirementValue,
    RiskFlag,
    Verdict,
)
from pmz.signals import (
    CriterionResult,
    CriterionStatus,
    GateSignals,
    RequirementAssessment,
)


def _record(
    *,
    rid: str = "rel-x",
    changed_files: list[str],
    archetype: Archetype | None,
    incident: IncidentValue = IncidentValue.OK,
    requirement: RequirementValue = RequirementValue.MET,
    req_status: LabelStatus = LabelStatus.FINAL,
) -> ReleaseRecord:
    return ReleaseRecord(
        id=rid,
        pr_number=1,
        commit_sha="0" * 40,
        timestamp=datetime(2026, 5, 1),
        author="dev",
        code=CodeSignal(diff_summary="x", changed_files=changed_files),
        ci=CISignal(tests_pass=True),
        requirement=RequirementSignal(),
        labels=Labels(
            incident_axis=IncidentAxis(value=incident),
            requirement_axis=RequirementAxis(value=requirement, status=req_status),
            correct_verdict=Verdict.NO_GO,
        ),
        arc=Arc(archetype=archetype),
    )


def _signals(changed_files: list[str]) -> GateSignals:
    return GateSignals(
        code=CodeSignal(diff_summary="x", changed_files=changed_files),
        ci=CISignal(tests_pass=True),
    )


def test_learned_rule_matches_by_dir_glob() -> None:
    rule = LearnedRule(
        id="r1",
        version=1,
        archetype=Archetype.DB_MIGRATION,
        file_globs=["db/migrations/*"],
        description="x",
        created_from="rel-07",
    )
    assert rule.matches(_signals(["db/migrations/0051_alter.sql"]))
    assert not rule.matches(_signals(["src/api/handler.py"]))


def test_rulebook_versions_and_dedup() -> None:
    book = Rulebook()
    assert book.version == 0
    rule = LearnedRule(
        id="r1",
        version=1,
        archetype=Archetype.DB_MIGRATION,
        file_globs=["db/migrations/*"],
        description="x",
        created_from="rel-07",
    )
    book.add(rule)
    assert book.version == 1
    assert book.has(Archetype.DB_MIGRATION, ["db/migrations/*"])
    assert not book.has(Archetype.REQUIREMENT_MISS, ["db/migrations/*"])


def test_is_confirmed_bad_uses_objective_labels() -> None:
    # 障害確定 → bad。
    assert is_confirmed_bad(
        _record(
            changed_files=["db/migrations/x.sql"],
            archetype=Archetype.DB_MIGRATION,
            incident=IncidentValue.FAIL,
        )
    )
    # 要件未達が final → bad。
    assert is_confirmed_bad(
        _record(
            changed_files=["src/billing/x.py"],
            archetype=Archetype.REQUIREMENT_MISS,
            requirement=RequirementValue.UNMET,
            req_status=LabelStatus.FINAL,
        )
    )
    # 暫定（provisional）の未達はまだ確定でない → not bad。
    assert not is_confirmed_bad(
        _record(
            changed_files=["src/billing/x.py"],
            archetype=Archetype.REQUIREMENT_MISS,
            requirement=RequirementValue.UNMET,
            req_status=LabelStatus.PROVISIONAL,
        )
    )


def test_learn_rule_generalizes_db_migration_dir() -> None:
    rec = _record(
        changed_files=["db/migrations/0042_add_index.sql", "src/orders/repo.py"],
        archetype=Archetype.DB_MIGRATION,
        incident=IncidentValue.FAIL,
    )
    rule = learn_rule_from(rec, version=1)
    assert rule is not None
    # db_migration は migration 標識のファイルだけを一般化する（src/orders は巻き込まない）。
    assert rule.file_globs == ["db/migrations/*"]
    assert rule.action is RuleAction.BLOCK


def test_learn_rule_requirement_miss_uses_all_changed_dirs() -> None:
    rec = _record(
        changed_files=["src/billing/invoice.py"],
        archetype=Archetype.REQUIREMENT_MISS,
        requirement=RequirementValue.UNMET,
    )
    rule = learn_rule_from(rec, version=2)
    assert rule is not None
    assert rule.file_globs == ["src/billing/*"]


def test_learn_rule_returns_none_without_archetype() -> None:
    rec = _record(changed_files=["src/api/x.py"], archetype=None)
    assert learn_rule_from(rec, version=1) is None


def test_memory_does_not_match_root_level_files() -> None:
    # ルート直下ファイル同士（親ディレクトリなし）は「類似」と判定しない。
    mem = CaseMemory()
    mem.add(
        MisjudgedCase(
            release_id="r1",
            archetype=None,
            predicted_verdict=Verdict.GO,
            correct_verdict=Verdict.NO_GO,
            changed_files=["CHANGELOG.md"],
        )
    )
    assert mem.similar(_signals(["README.md"])) == []
    # 同一ディレクトリ配下なら類似ヒットする。
    mem.add(
        MisjudgedCase(
            release_id="r2",
            archetype=None,
            predicted_verdict=Verdict.GO,
            correct_verdict=Verdict.NO_GO,
            changed_files=["src/billing/a.py"],
        )
    )
    assert [c.release_id for c in mem.similar(_signals(["src/billing/b.py"]))] == ["r2"]


def test_effective_verdict_treats_human_review_as_not_approved() -> None:
    # HUMAN_REVIEW（棄権）は自律承認ではないので実効判定は No-Go。
    human = GateDecision(verdict=Verdict.GO, autonomy=AutonomyLevel.HUMAN_REVIEW, confidence=0.9)
    assert human.effective_verdict is Verdict.NO_GO
    auto = GateDecision(verdict=Verdict.GO, autonomy=AutonomyLevel.AUTO_APPROVE, confidence=0.9)
    assert auto.effective_verdict is Verdict.GO


def test_hard_guarded_bad_release_not_counted_as_false_approve() -> None:
    # 高リスク領域は確信度が高くてもハードガードで人間承認に落ちる（§7 #5）。
    sig = GateSignals(
        code=CodeSignal(
            diff_summary="x",
            changed_files=["db/migrations/x.sql"],
            risk_flags=[RiskFlag.DB_MIGRATION],
        ),
        ci=CISignal(tests_pass=True),
        requirement=RequirementAssessment(
            results=[CriterionResult(criterion="c", status=CriterionStatus.MET, confidence=0.95)]
        ),
    )
    dec = judge(sig)
    assert dec.needs_human
    # correct=No-Go の悪いリリースでも、実効判定では誤承認(FP)に数えない（KPI の頑健性）。
    cm = confusion_matrix([(dec.effective_verdict, Verdict.NO_GO)])
    assert cm.fp == 0
    assert cm.tn == 1
