"""Orchestrator エージェント（要件 §4.1 / §6.1）.

読むエージェント（CodeRisk / PM-Req）の **構造化シグナル** を集約し、決定論の ``judge()``
で最終判定を下す唯一の主体（§7 #3 権限分離 ＝ 判定は構造化シグナルからのみ）。判定後は
監査証跡を追記する（§7 #4）。

> reader が出すのは所見・シグナルのみ。``GateDecision`` を生むのはここだけ。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from pmz.agents.base import AgentRole
from pmz.agents.code_risk import CodeRiskAgent, CodeRiskReport
from pmz.agents.pm_req import PMReqAgent
from pmz.audit import AuditLog, AuditRecord
from pmz.core.decision import GateDecision
from pmz.core.judge import CONFIDENCE_THRESHOLD, judge
from pmz.learning.rulebook import Rulebook
from pmz.models import ReleaseRecord
from pmz.signals import GateSignals, RequirementAssessment

if TYPE_CHECKING:
    from pmz.store.ports import CaseRetriever


class GateResult(BaseModel):
    """オーケストレーションの結果（判定＋寄与した所見＋監査証跡）。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    decision: GateDecision
    code_risk: CodeRiskReport
    requirement: RequirementAssessment
    audit: AuditRecord | None = None


class Orchestrator:
    """構造化シグナルを統合して Go/No-Go を出す統括エージェント。"""

    name = "Orchestrator"
    role = AgentRole.ORCHESTRATOR

    def __init__(
        self,
        code_risk: CodeRiskAgent | None = None,
        pm_req: PMReqAgent | None = None,
    ) -> None:
        self.code_risk = code_risk or CodeRiskAgent()
        self.pm_req = pm_req or PMReqAgent()

    def evaluate(
        self,
        record: ReleaseRecord,
        *,
        assessment: RequirementAssessment | None = None,
        rulebook: Rulebook | None = None,
        memory: CaseRetriever | None = None,
        audit_log: AuditLog | None = None,
        threshold: float = CONFIDENCE_THRESHOLD,
    ) -> GateResult:
        """reader の所見を集約 → ``judge()`` で判定 → 監査証跡を残す。"""
        # 1) 読むエージェント: PR由来テキスト（リリースノート）は隔離して渡す（§7#3）。
        code_report = self.code_risk.analyze(
            record.code, untrusted_text=record.requirement.release_note
        )
        req_assessment = self.pm_req.assess(record.requirement, evidence=assessment)

        # 2) 統合判定: 根拠は構造化シグナルのみ（reader は承認権限を持たない）。
        signals = GateSignals(code=record.code, ci=record.ci, requirement=req_assessment)
        decision = judge(signals, threshold=threshold, rulebook=rulebook, memory=memory)

        # 3) 監査証跡（どのエージェントが寄与したか含む・§7#4）。
        audit_record = None
        if audit_log is not None:
            audit_record = audit_log.append(
                record=record,
                decision=decision,
                agents=[self.code_risk.name, self.pm_req.name, self.name],
                prompt_version=self.pm_req.prompt_version,
            )

        return GateResult(
            decision=decision,
            code_risk=code_report,
            requirement=req_assessment,
            audit=audit_record,
        )
