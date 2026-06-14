"""自己改善コアの単体テスト（要件 §3.3.1）。"""

from __future__ import annotations

from datetime import datetime

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
    Verdict,
)
from pmz.signals import GateSignals


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
