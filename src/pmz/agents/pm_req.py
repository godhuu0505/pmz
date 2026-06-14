"""PM-Req エージェント（要件 §3.2.1 / §6.2 — このプロダクトの差別化の芯）.

申告された受け入れ基準に対し 3値（満たす / 満たさない / 検証不能）＋確信度の充足判定を出す
reader。承認権限は持たない（§7 #3）。

- **正本主義**: 評価対象は人間確定の受け入れ基準のみ。LLM が基準を新造・改変しない（§3.2.1）。
- **棄権の許容**: 証拠を引けない基準は「検証不能」として断定せず人間へ（ハルシネーション抑止）。
- MVP（LLMなし）: 充足判定（``evidence``）は将来 LLM / ``/trace`` が生成する。ここでは
  与えられればそれを採用し、無ければ全件「検証不能」で棄権する（安全側の既定）。

プロンプトは将来 ``prompts/pm_req.vN.md`` に版管理し ``prompt_version`` を監査証跡へ残す（§6.3）。
"""

from __future__ import annotations

from pmz.agents.base import AgentRole
from pmz.models import RequirementSignal
from pmz.signals import RequirementAssessment, draft_unverifiable_assessment

PROMPT_VERSION = "pm_req.v1"


class PMReqAgent:
    """要件充足の 3値判定を出す reader（承認権限なし）。"""

    name = "PMReqAgent"
    role = AgentRole.READER
    prompt_version = PROMPT_VERSION

    def assess(
        self,
        requirement: RequirementSignal,
        *,
        evidence: RequirementAssessment | None = None,
    ) -> RequirementAssessment:
        """申告された受け入れ基準に対する 3値充足判定を返す。

        ``evidence``（将来 LLM / ``/trace`` の出力）があればそれを採用。無ければ
        全件「検証不能」で棄権する（§3.2.1）。
        """
        if evidence is not None:
            return evidence
        return draft_unverifiable_assessment(requirement)
