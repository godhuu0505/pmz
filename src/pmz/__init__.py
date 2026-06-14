"""pmz — AIリリース判定ゲートキーパー × 自己改善エージェント.

名称 pmz = PM観点 × Z軸（自己改善の時間軸）。命名の理由は ``docs/requirements.md`` §1 を参照。
MVP スコープ: PRマージゲート。シグナルは code + CI + 要件充足（要件定義書ベース）。
"""

from pmz.core.decision import AutonomyLevel, GateDecision
from pmz.core.judge import judge, judge_record
from pmz.models import ReleaseRecord, Verdict
from pmz.signals import GateSignals, RequirementAssessment

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
