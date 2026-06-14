"""学習ルールとルールブック（要件 §3.3.1 (3) ルール自動進化 / §7 #4 監査証跡）.

振り返りエージェントが誤判定から起こした **新チェックルールをバージョン管理して蓄える**。
MVP のルールは「変更ファイルのディレクトリ glob で発火する」決定論マッチャに限定する
（LLM を介さず再現・監査でき、自己改善の前後比較が安定するため）。

設計インバリアント（CLAUDE.md §5）との整合:
- ルールの発火は **客観シグナル（changed_files）からのみ**。PR由来の散文には依存しない（#1）。
- ルールは追跡・巻き戻し可能なよう、由来（``created_from``）と版（``version``）を持つ（§7 #4）。
"""

from __future__ import annotations

from enum import StrEnum
from fnmatch import fnmatch

from pydantic import BaseModel, Field

from pmz.models import Archetype
from pmz.signals import GateSignals


class RuleAction(StrEnum):
    """ルール発火時のアクション（MVP は BLOCK 中心・§9.1 「検知してブロック」）。"""

    BLOCK = "block"  # No-Go で自律ブロック
    ESCALATE = "escalate"  # 人間にエスカレーション（中リスク）


class LearnedRule(BaseModel):
    """学習で追加された 1 ルール（バージョン管理つき・§3.3.1 / §7 #4）。

    ``file_globs`` のいずれかに ``changed_files`` が一致したら発火する。発火条件を
    構造化データとして持つことで、監査・再現・剪定（Phase2）を可能にする。
    """

    id: str
    version: int  # このルールが追加された時点のルールブック版（監査証跡）
    archetype: Archetype  # どの再発型から学習したか（振り返りの帰属）
    file_globs: list[str] = Field(default_factory=list)
    action: RuleAction = RuleAction.BLOCK
    description: str
    created_from: str  # 由来となった誤判定リリースの id（巻き戻し・Few-shot 参照用）

    def matches(self, signals: GateSignals) -> bool:
        """変更ファイルがこのルールの glob に一致するか（発火判定・決定論）。"""
        return any(
            fnmatch(path, glob) for path in signals.code.changed_files for glob in self.file_globs
        )


class Rulebook(BaseModel):
    """学習ルールの集合（バージョン管理・§3.3.1 (3)）。

    ルール追加のたびに ``version`` を進める。これにより「どの版で何を学んだか」を
    時系列で再現でき、自己改善の前後比較（§6.1）の土台になる。
    """

    version: int = 0
    rules: list[LearnedRule] = Field(default_factory=list)

    def add(self, rule: LearnedRule) -> None:
        """ルールを追記し版を進める（恒久化）。"""
        self.rules.append(rule)
        self.version += 1

    def matching(self, signals: GateSignals) -> list[LearnedRule]:
        """与えたシグナルで発火する全ルール（監査証跡の根拠用）。"""
        return [r for r in self.rules if r.matches(signals)]

    def has(self, archetype: Archetype, file_globs: list[str]) -> bool:
        """同型・同 glob のルールが既にあるか（入口の重複排除の簡易版・§3.3.1 (4)）。"""
        target = set(file_globs)
        return any(r.archetype is archetype and set(r.file_globs) == target for r in self.rules)
