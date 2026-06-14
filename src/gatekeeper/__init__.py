"""GateKeeper (仮称) — AIリリース判定ゲートキーパー × 自己改善エージェント.

MVP スコープ: PRマージゲート。シグナルは code + CI + 要件充足（要件定義書ベース）。
詳細は ``docs/requirements.md`` を参照。
"""

from gatekeeper.core.decision import AutonomyLevel, GateDecision
from gatekeeper.core.judge import judge, judge_record
from gatekeeper.models import ReleaseRecord, Verdict
from gatekeeper.signals import GateSignals, RequirementAssessment

__all__ = [
    "AutonomyLevel",
    "GateDecision",
    "GateSignals",
    "ReleaseRecord",
    "RequirementAssessment",
    "Verdict",
    "judge",
    "judge_record",
]
