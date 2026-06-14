"""MVP 用の in-memory アダプタ（要件 §8.1）.

``AuditLog``（監査）と ``CaseMemory``（Few-shot 検索）は既に in-memory 実装なので、
ここでは未提供の ``VerdictStore`` の in-memory 実装だけを足す。Phase2 で Firestore 等に差し替える。
"""

from __future__ import annotations

from pmz.core.decision import GateDecision


class InMemoryVerdictStore:
    """判定をプロセス内に保持する ``VerdictStore`` 実装（MVP）。"""

    def __init__(self) -> None:
        self._by_id: dict[str, GateDecision] = {}

    def save(self, release_id: str, decision: GateDecision) -> None:
        self._by_id[release_id] = decision

    def get(self, release_id: str) -> GateDecision | None:
        return self._by_id.get(release_id)

    def __len__(self) -> int:
        return len(self._by_id)
