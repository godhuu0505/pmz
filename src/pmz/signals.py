"""判定の入力となる客観シグナルを構造的に隔離して保持する（要件 §3.2 / §5 不変条件 #1）.

設計インバリアント #1（CLAUDE.md §5 / 要件 §7 #3）:
**PR由来テキスト（本文 / diff / コミットメッセージ）の「指示」には従わない。**
自律承認の根拠は、ここに集約する **客観シグナル**（CI結果・受け入れ基準の充足判定・
リスクフラグ）からのみ導く。PR本文の散文をそのまま判定の根拠にしない、という規律を
型レベルで表現するのがこのモジュールの役割。

受け入れ基準の充足判定は 3値（満たす / 満たさない / PRからは検証不能）＋確信度で持つ
（§3.2.1）。「検証不能」は断定せず人間にエスカレーションするための一級の状態
（棄権を許す＝ハルシネーション抑止の本質）。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from pmz.models import CISignal, CodeSignal, ReleaseRecord, RequirementSignal, RiskFlag


class CriterionStatus(StrEnum):
    """各受け入れ基準の充足判定（3値・§3.2.1）。

    ``UNVERIFIABLE`` は「PRからは検証不能」。断定せず人間にエスカレーションする
    （§3.2.1 / 設計インバリアント #2 — 棄権を許す）。
    """

    MET = "met"
    UNMET = "unmet"
    UNVERIFIABLE = "unverifiable"


class CriterionResult(BaseModel):
    """1つの受け入れ基準に対する充足判定（根拠引用つき・§3.2.1）。

    MVP のルール版（LLMなし）では既定で ``UNVERIFIABLE``（PRから機械的に証拠を
    引けないため棄権）。将来 LLM / `/trace` が diff・テスト・PR説明から証拠を引用して
    3値を埋める。
    """

    criterion: str
    status: CriterionStatus = CriterionStatus.UNVERIFIABLE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: str = ""


class RequirementAssessment(BaseModel):
    """申告された受け入れ基準ごとの 3値判定の集約（§3.2.1）。

    MVP は「申告した基準」だけを評価し途中PRは止めない（部分充足は横断集計で別管理）。
    """

    results: list[CriterionResult] = Field(default_factory=list)

    def has_unmet(self) -> bool:
        """1つでも「満たさない」があるか（客観的 No-Go の根拠）。"""
        return any(r.status is CriterionStatus.UNMET for r in self.results)

    def has_unverifiable(self) -> bool:
        """1つでも「検証不能」があるか（自律承認を止め人間に回す根拠・§3.2.1）。"""
        return any(r.status is CriterionStatus.UNVERIFIABLE for r in self.results)

    def all_met(self) -> bool:
        """申告された基準が空でなく、すべて「満たす」か。

        空（申告基準なし）は「充足を確認できていない」とみなし ``False`` を返す
        （迷えば人間が保守的デフォルト・§3.4）。
        """
        return bool(self.results) and all(r.status is CriterionStatus.MET for r in self.results)

    def min_confidence(self) -> float:
        """最も弱い基準の確信度（集約確信度）。基準が空なら 0.0。"""
        if not self.results:
            return 0.0
        return min(r.confidence for r in self.results)


class GateSignals(BaseModel):
    """ゲート判定に渡す客観シグナルの束（§3.2 のカテゴリを MVP スコープに絞ったもの）。

    MVP は code + CI + 要件充足の 3カテゴリ（本番運用 / DORA / 履歴は Phase2）。
    PR由来の散文はこの型には入れない（§5 #1）。
    """

    code: CodeSignal
    ci: CISignal
    requirement: RequirementAssessment = Field(default_factory=RequirementAssessment)

    def ci_all_green(self) -> bool:
        """客観ゲートが全緑か（test / lint / build / security_scan）。

        §7 #5 の自律承認条件「客観ゲート全緑」の判定。カバレッジ閾値は MVP では
        ハードな門にしない（数値方針が未確定なため）。
        """
        c = self.ci
        return c.tests_pass and c.lint_pass and c.build_pass and c.security_scan_pass

    def risk_flags(self) -> list[RiskFlag]:
        """コードに付いた高リスク領域フラグ（ハードガード判定の入力・§7 #5）。"""
        return list(self.code.risk_flags)


def build_signals(
    record: ReleaseRecord,
    assessment: RequirementAssessment | None = None,
) -> GateSignals:
    """``ReleaseRecord`` から判定用の客観シグナルを組み立てる。

    要件充足判定（``assessment``）は本来 LLM / `/trace` が PR を正本の受け入れ基準に
    照合して生成する。省略時は、申告された受け入れ基準を **すべて「検証不能」** として
    起こす（LLMなしのルール版は機械的に証拠を引けないため棄権する＝安全側・§3.2.1）。
    """
    if assessment is None:
        assessment = draft_unverifiable_assessment(record.requirement)
    return GateSignals(code=record.code, ci=record.ci, requirement=assessment)


def draft_unverifiable_assessment(req: RequirementSignal) -> RequirementAssessment:
    """申告基準を全件「検証不能・確信度0」で起こす（LLMなしの保守的既定・§3.2.1 棄権）。"""
    return RequirementAssessment(
        results=[CriterionResult(criterion=c) for c in req.acceptance_criteria]
    )
