"""永続化抽象層のテスト（要件 §4.2 / §8.1）。

ポート（Protocol）への構造的準拠を検証し、既定の in-memory 実装が差し替え可能な
継ぎ目（Firestore / Elasticsearch のドロップイン先）になっていることを担保する。
"""

from __future__ import annotations

from pmz.audit import AuditLog
from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.core.judge import judge
from pmz.learning.memory import CaseMemory
from pmz.learning.rulebook import LearnedRule, Rulebook
from pmz.models import Archetype, CISignal, CodeSignal, Verdict
from pmz.signals import CriterionResult, CriterionStatus, GateSignals, RequirementAssessment
from pmz.store.inmemory import InMemoryVerdictStore
from pmz.store.ports import AuditStore, CaseRetriever, VerdictStore


def test_default_impls_conform_to_ports() -> None:
    # 既定実装がポートに準拠している（＝アダプタ差し替え可能な継ぎ目になっている）。
    assert isinstance(AuditLog(), AuditStore)
    assert isinstance(CaseMemory(), CaseRetriever)
    assert isinstance(InMemoryVerdictStore(), VerdictStore)


def test_inmemory_verdict_store_roundtrip() -> None:
    store: VerdictStore = InMemoryVerdictStore()
    assert store.get("rel-01") is None
    decision = GateDecision(verdict=Verdict.GO, autonomy=AutonomyLevel.AUTO_APPROVE, confidence=0.9)
    store.save("rel-01", decision)
    assert store.get("rel-01") is decision


def test_judge_accepts_any_case_retriever() -> None:
    # CaseRetriever を実装した最小のダミーでも judge に注入できる（ポート依存の証明）。
    class RecordingRetriever:
        def __init__(self) -> None:
            self.queried = False

        def add(self, case: object) -> None:  # pragma: no cover - 未使用
            pass

        def similar(self, signals: object, *, archetype: object = None) -> list:
            self.queried = True
            return []

    retriever = RecordingRetriever()
    assert isinstance(retriever, CaseRetriever)

    book = Rulebook()
    book.add(
        LearnedRule(
            id="t",
            version=1,
            archetype=Archetype.DB_MIGRATION,
            file_globs=["db/migrations/*"],
            description="x",
            created_from="rel-07",
        )
    )
    signals = GateSignals(
        code=CodeSignal(diff_summary="x", changed_files=["db/migrations/y.sql"]),
        ci=CISignal(tests_pass=True),
        requirement=RequirementAssessment(
            results=[CriterionResult(criterion="c", status=CriterionStatus.MET, confidence=0.95)]
        ),
    )
    decision = judge(signals, rulebook=book, memory=retriever)
    assert decision.verdict is Verdict.NO_GO
    assert retriever.queried  # 学習ルール発火時に Few-shot 検索が呼ばれた
