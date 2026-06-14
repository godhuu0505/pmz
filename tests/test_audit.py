"""監査証跡のテスト（要件 §7 #4 / §5.2）。ハッシュチェーンの改ざん検知。"""

from __future__ import annotations

from pmz.audit import GENESIS_HASH, AuditLog, input_hash
from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.data import load_synthetic_releases
from pmz.models import Verdict


def _decision() -> GateDecision:
    return GateDecision(
        verdict=Verdict.GO,
        autonomy=AutonomyLevel.AUTO_APPROVE,
        confidence=0.9,
        rationale=["客観ゲート全緑のため自律承認。"],
        fired_rules=["auto_approve"],
    )


def test_append_chains_records() -> None:
    records = load_synthetic_releases()
    log = AuditLog()
    a = log.append(
        record=records[0], decision=_decision(), agents=["X"], prompt_version="pm_req.v1"
    )
    b = log.append(
        record=records[1], decision=_decision(), agents=["X"], prompt_version="pm_req.v1"
    )
    # 1件目は genesis に、2件目は1件目に連鎖する。
    assert a.prev_hash == GENESIS_HASH
    assert b.prev_hash == a.record_hash
    assert a.seq == 0 and b.seq == 1
    assert log.verify()


def test_tamper_breaks_chain() -> None:
    records = load_synthetic_releases()
    log = AuditLog()
    log.append(record=records[0], decision=_decision(), agents=["X"], prompt_version="pm_req.v1")
    log.append(record=records[1], decision=_decision(), agents=["X"], prompt_version="pm_req.v1")
    assert log.verify()
    # 過去レコードの根拠を改ざんすると検証が失敗する（改ざん検知）。
    log.records[0].rationale.append("改ざんされた根拠")
    assert not log.verify()


def test_input_hash_is_deterministic_and_input_sensitive() -> None:
    records = load_synthetic_releases()
    assert input_hash(records[0]) == input_hash(records[0])
    assert input_hash(records[0]) != input_hash(records[1])
    assert input_hash(records[0]).startswith("sha256:")
