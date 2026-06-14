"""改ざん検知可能な監査証跡（要件 §7 #4 / §5.2 / §8.1 MVP must-have ⑤）.

全判定について「入力ハッシュ / 判定 / 確信度 / 根拠 / 発火ルール / モデル・プロンプト版 /
寄与エージェント」を**追記専用**で記録し、追跡・再現・巻き戻しを可能にする。

**改ざん検知**: 各レコードは直前レコードのハッシュ（``prev_hash``）を含めて自身のハッシュ
（``record_hash``）を計算する **ハッシュチェーン**。途中の1件でも改変すると以降の連鎖が壊れ、
``verify()`` が検知する（Firestore 等への永続化は Phase2。MVP は in-memory ＋任意で JSONL）。
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.models import ReleaseRecord, Verdict

GENESIS_HASH = "0" * 64


def _sha256(blob: str) -> str:
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _canonical(payload: object) -> str:
    """安定した正規化 JSON（ハッシュ計算の決定性を担保）。"""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def input_hash(record: ReleaseRecord) -> str:
    """判定入力（code / ci / requirement）のハッシュ（入力の同定・再現用）。"""
    payload = {
        "code": record.code.model_dump(mode="json"),
        "ci": record.ci.model_dump(mode="json"),
        "requirement": record.requirement.model_dump(mode="json"),
    }
    return "sha256:" + _sha256(_canonical(payload))


class AuditRecord(BaseModel):
    """1判定の改ざん不能な監査証跡（§5.2 / §7 #4）。"""

    model_config = ConfigDict(protected_namespaces=())

    seq: int
    created_at: datetime
    release_id: str
    input_hash: str

    decision: Verdict
    autonomy: AutonomyLevel
    confidence: float
    rationale: list[str] = Field(default_factory=list)
    fired_rules: list[str] = Field(default_factory=list)
    hard_guarded: bool = False

    model_version: str
    prompt_version: str
    agents: list[str] = Field(default_factory=list)  # 寄与エージェント（権限分離の記録）

    prev_hash: str
    record_hash: str = ""

    def compute_hash(self) -> str:
        """``record_hash`` 以外の全フィールドからハッシュを計算（チェーンの要）。"""
        payload = self.model_dump(mode="json", exclude={"record_hash"})
        return _sha256(_canonical(payload))


class AuditLog:
    """追記専用のハッシュチェーン監査ログ（§7 #4）。"""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.records: list[AuditRecord] = []

    @property
    def head_hash(self) -> str:
        """末尾レコードのハッシュ（次レコードの ``prev_hash`` になる）。"""
        return self.records[-1].record_hash if self.records else GENESIS_HASH

    def append(
        self,
        *,
        record: ReleaseRecord,
        decision: GateDecision,
        agents: list[str],
        prompt_version: str,
    ) -> AuditRecord:
        """判定を 1 件追記する（前レコードに連鎖）。"""
        entry = AuditRecord(
            seq=len(self.records),
            created_at=datetime.now(UTC),
            release_id=record.id,
            input_hash=input_hash(record),
            decision=decision.verdict,
            autonomy=decision.autonomy,
            confidence=decision.confidence,
            rationale=decision.rationale,
            fired_rules=decision.fired_rules,
            hard_guarded=decision.hard_guarded,
            model_version=decision.model_version,
            prompt_version=prompt_version,
            agents=agents,
            prev_hash=self.head_hash,
        )
        entry.record_hash = entry.compute_hash()
        self.records.append(entry)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        return entry

    def verify(self) -> bool:
        """チェーン全体の整合（改ざんが無いか）を検証する。"""
        prev = GENESIS_HASH
        for entry in self.records:
            if entry.prev_hash != prev:
                return False
            if entry.record_hash != entry.compute_hash():
                return False
            prev = entry.record_hash
        return True
