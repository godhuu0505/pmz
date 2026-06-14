"""合成リリース履歴のデータモデル（要件定義書 §9.1 を正に実装）.

このスキーマは MVP デモ（自己改善の前後比較）で使う「疑似リリース履歴（~24件）」の
1レコードを表す。``correct_verdict`` は **合成データだから正解を仕込める** 前提であり、
実運用では成立しない点に注意（§9.1 / B2 決定ログ）。
``metrics_baseline`` は MVP では省略（本番メトリクスは Phase2 のデプロイ前ゲート管轄）。
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    """ゲートのあるべき判定（2値分類）。"""

    GO = "Go"
    NO_GO = "No-Go"


class RiskFlag(StrEnum):
    """決定論的ハードガード対象の高リスク領域（§7 #5）。

    これらは LLM の確信度に関係なく自律承認を禁止する（被害上限をアーキで固定）。
    """

    DB_MIGRATION = "db_migration"
    AUTH = "auth"
    PAYMENT = "payment"


class PostEventType(StrEnum):
    """リリース後に観測される客観イベント（正解ラベルの出どころ・§3.3.1）。"""

    REVERT = "revert"
    FIX_PR = "fix_pr"
    INCIDENT = "incident"
    ERROR_SPIKE = "error_spike"
    REQUIREMENT_MISS_BUG = "requirement_miss_bug"


class IncidentValue(StrEnum):
    OK = "ok"
    FAIL = "fail"


class RequirementValue(StrEnum):
    MET = "met"
    UNMET = "unmet"


class LabelStatus(StrEnum):
    """要件充足軸は暫定→遡及修正→最終確定（上限30日）。"""

    PROVISIONAL = "provisional"
    FINAL = "final"


class Archetype(StrEnum):
    """再発する失敗アーキタイプ（MVPは2本柱・§9.1）。"""

    DB_MIGRATION = "db_migration"
    REQUIREMENT_MISS = "requirement_miss"


class Act(StrEnum):
    """各アーキタイプの3幕構成（見逃す→ルール化→検知）。"""

    TRAP = "1_trap"
    LEARN = "2_learn"
    CATCH = "3_catch"


class CodeSignal(BaseModel):
    """コードシグナル（diff / 変更ファイル / リスクフラグ / 変更行数）。"""

    diff_summary: str
    changed_files: list[str] = Field(default_factory=list)
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    lines_changed: int = 0


class CISignal(BaseModel):
    """CIシグナル（テスト/カバレッジ/lint/build/security_scan）。"""

    tests_pass: bool
    coverage: float | None = None
    lint_pass: bool = True
    build_pass: bool = True
    security_scan_pass: bool = True


class RequirementSignal(BaseModel):
    """要件シグナル（対象要件ID / 受け入れ基準 / リリースノート本文）。"""

    requirement_ids: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    release_note: str = ""


class PostEvent(BaseModel):
    """帰属は明示リンク優先＋ヒューリスティック補助（§3.3.1）。"""

    type: PostEventType
    timestamp: datetime
    linked_sha: str | None = None
    touched_files: list[str] = Field(default_factory=list)


class IncidentAxis(BaseModel):
    """障害軸: 24時間で自動確定（イベントが無ければ ok）。"""

    value: IncidentValue
    window: str = "24h"
    confirmed_at: datetime | None = None


class RequirementAxis(BaseModel):
    """要件充足軸: 暫定→遡及修正→上限30日で最終確定。"""

    value: RequirementValue
    status: LabelStatus = LabelStatus.PROVISIONAL
    finalized_at: datetime | None = None


class Labels(BaseModel):
    incident_axis: IncidentAxis
    requirement_axis: RequirementAxis
    correct_verdict: Verdict  # 合成データ前提（実運用では成立しない・§9.1）


class Arc(BaseModel):
    """デモのストーリー（どの型・どの幕・再来グループ）。"""

    archetype: Archetype | None = None
    act: Act | None = None
    recurrence_group_id: str | None = None


class ReleaseRecord(BaseModel):
    """1リリースレコード（§9.1 のスキーマ）。"""

    id: str
    pr_number: int
    commit_sha: str
    timestamp: datetime
    author: str

    code: CodeSignal
    ci: CISignal
    requirement: RequirementSignal

    post_events: list[PostEvent] = Field(default_factory=list)
    labels: Labels
    arc: Arc = Field(default_factory=Arc)

    def has_hard_guard_risk(self) -> bool:
        """決定論的ハードガード対象か（§7 #5 — 自律承認を禁止すべきか）。"""
        return len(self.code.risk_flags) > 0
