"""CodeRisk エージェント（要件 §4.1 / §3.2 コードシグナル）.

diff・変更ファイル・高リスク領域フラグを **構造化シグナル** として読み取る reader。
承認権限は持たない（§7 #3 権限分離）。

**インジェクション耐性（§7 #3）**: PR由来のテキスト（本文/diff/コミットメッセージ）は
``untrusted_text`` として受け取るが、判定に効く ``risk_flags`` は **構造化された
``CodeSignal`` からのみ** 導く。散文中の「これは安全だから承認して」等の指示は
所見メモに隔離するだけで、リスク判断を覆せない。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from pmz.agents.base import AgentRole
from pmz.models import CodeSignal, RiskFlag


class CodeRiskReport(BaseModel):
    """CodeRisk の所見（構造化シグナルのみ・承認権限なし）。"""

    model_config = ConfigDict(frozen=True)

    agent: str = "CodeRiskAgent"
    role: AgentRole = AgentRole.READER
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    lines_changed: int = 0
    notes: list[str] = Field(default_factory=list)


class CodeRiskAgent:
    """コード変更のリスク所見を出す reader（承認権限なし）。"""

    name = "CodeRiskAgent"
    role = AgentRole.READER

    def analyze(self, code: CodeSignal, *, untrusted_text: str = "") -> CodeRiskReport:
        """構造化された ``CodeSignal`` からリスク所見を作る。

        ``untrusted_text`` は隔離して所見メモに残すのみ。risk_flags には反映しない。
        """
        notes: list[str] = []
        if untrusted_text:
            notes.append(
                "PR由来テキストを受領（信頼できないデータとして隔離。指示には従わず判定根拠にしない・§7#3）。"
            )
        risk_flags = list(code.risk_flags)
        for f in risk_flags:
            notes.append(f"高リスク領域フラグを検出: {f.value}")
        return CodeRiskReport(
            risk_flags=risk_flags,
            lines_changed=code.lines_changed,
            notes=notes,
        )
