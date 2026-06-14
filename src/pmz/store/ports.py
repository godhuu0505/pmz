"""永続化ポート（Protocol）── 実装を差し替えるための継ぎ目（要件 §4.2 / §8.1）.

ここで定義する Protocol に準拠すれば、in-memory / Firestore / Elasticsearch などの
アダプタを判定・学習ロジックを変えずに注入できる。``runtime_checkable`` なので
``isinstance`` で構造的準拠を検証できる（テストで担保）。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pmz.audit import AuditRecord
from pmz.core.decision import GateDecision
from pmz.learning.memory import MisjudgedCase
from pmz.models import Archetype, ReleaseRecord
from pmz.signals import GateSignals


@runtime_checkable
class AuditStore(Protocol):
    """改ざん検知付き監査証跡の保存（§7 #4）。既定実装は ``pmz.audit.AuditLog``。

    Phase2 で Firestore の追記コレクションにアダプタを差し替える。
    """

    records: list[AuditRecord]

    def append(
        self,
        *,
        record: ReleaseRecord,
        decision: GateDecision,
        agents: list[str],
        prompt_version: str,
    ) -> AuditRecord: ...

    def verify(self) -> bool: ...


@runtime_checkable
class VerdictStore(Protocol):
    """判定（``GateDecision``）の保存・参照（§4.2 verdicts コレクション）。

    Phase2 で Firestore（``pr_number@commit_sha`` をキー）に差し替える。
    """

    def save(self, release_id: str, decision: GateDecision) -> None: ...

    def get(self, release_id: str) -> GateDecision | None: ...


@runtime_checkable
class CaseRetriever(Protocol):
    """Few-shot 用の誤判定ケース検索（§3.3.1 (3)）。既定実装は ``pmz.learning.memory.CaseMemory``。

    **Elasticsearch / Vertex AI Vector Search のドロップイン先**。判定器（``judge``）はこの
    Protocol にのみ依存するため、全文/意味検索バックエンドへ無改修で昇格できる。
    """

    def add(self, case: MisjudgedCase) -> None: ...

    def similar(
        self, signals: GateSignals, *, archetype: Archetype | None = None
    ) -> list[MisjudgedCase]: ...
