"""ゲート判定の出力 ``GateDecision``（要件 §3.4 / §7 #4）.

「条件付き自律（Conditional Autonomy）」の結果を表す（§3.4）。
リスクに応じて自律度（自律実行 / 人間承認 / 自律ブロック）を変える。

§7 #4 の監査証跡として、判定の再現・追跡・巻き戻しに必要な情報を保持する:
判定（verdict）/ 自律度 / 確信度 / 根拠 / 発火ルール / ハードガード作動 / モデルバージョン。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from pmz.models import Verdict


class AutonomyLevel(StrEnum):
    """リスクに応じた自律度（§3.4 条件付き自律）。"""

    AUTO_APPROVE = "auto_approve"  # 低リスク（高信頼でGo）: 自律実行
    HUMAN_REVIEW = "human_review"  # 中リスク: 人間に承認を促す（Human-in-the-loop）
    AUTO_BLOCK = "auto_block"  # 高リスク（No-Go）: 自律ブロック


class GateDecision(BaseModel):
    """ゲートの最終出力＋監査証跡（§3.4 / §7 #4）。

    ``verdict`` は客観シグナルから導いた「あるべき判定」、``autonomy`` は実際に取る
    アクションの自律度。両者を分けることで「Go だが高リスクなので人間承認」のような
    条件付き自律を表現できる。
    """

    # `model_version` は pydantic v2 の保護名前空間（model_）に当たるため明示的に許可。
    model_config = ConfigDict(protected_namespaces=())

    verdict: Verdict
    autonomy: AutonomyLevel
    confidence: float = Field(ge=0.0, le=1.0)

    rationale: list[str] = Field(default_factory=list)  # 根拠（客観シグナル由来・§5 #1）
    fired_rules: list[str] = Field(default_factory=list)  # 発火ルール（監査証跡・§7 #4）
    hard_guarded: bool = False  # 決定論的ハードガードが作動したか（§7 #5）

    # 監査証跡: どの判定器が出したか（ルール版 / 将来は LLM のモデル名・§7 #4）。
    model_version: str = "rule-based-v0"

    @property
    def is_autonomous(self) -> bool:
        """人間を介さず自律的に動くか（自律実行 or 自律ブロック）。"""
        return self.autonomy in (AutonomyLevel.AUTO_APPROVE, AutonomyLevel.AUTO_BLOCK)

    @property
    def needs_human(self) -> bool:
        """人間の承認（Human-in-the-loop）が必要か（§3.4 中リスク / fail-to-human）。"""
        return self.autonomy is AutonomyLevel.HUMAN_REVIEW
