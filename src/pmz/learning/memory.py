"""誤判定ケースの記憶 / Few-shot ストア（要件 §3.3.1 (3) 記憶/Few-shot）.

誤判定ケースを蓄積し、判定時に類似の過去ケースを検索してプロンプトに注入する
（即応・モデルは変えない）――の MVP 実装。LLM を使わないルール版では、
類似検索の結果を **判定根拠（rationale）への参照** として使い、「過去に痛い目を見た型だ」
という Few-shot 的な手掛かりを監査証跡に残す。

正解ラベルは **客観イベントから導出**したものだけを使う（自己生成ラベルで自己学習しない・
インバリアント #6 / §3.3.1 (1)）。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from pmz.learning._paths import parent_dir
from pmz.models import Archetype, Verdict
from pmz.signals import GateSignals


class MisjudgedCase(BaseModel):
    """蓄積する誤判定ケース（記憶の 1 エントリ）。

    ``correct_verdict`` は客観イベント由来の正解ラベル（合成データでは仕込み・§9.1）。
    """

    model_config = ConfigDict(protected_namespaces=())

    release_id: str
    archetype: Archetype | None
    predicted_verdict: Verdict
    correct_verdict: Verdict
    changed_files: list[str] = Field(default_factory=list)
    summary: str = ""


class CaseMemory(BaseModel):
    """誤判定ケースの記憶。類似検索で Few-shot 事例を返す（§3.3.1 (3)）。"""

    cases: list[MisjudgedCase] = Field(default_factory=list)

    def add(self, case: MisjudgedCase) -> None:
        self.cases.append(case)

    def similar(
        self, signals: GateSignals, *, archetype: Archetype | None = None
    ) -> list[MisjudgedCase]:
        """類似の過去ケースを検索する（MVP: 変更ファイルのディレクトリ重なり＋型一致）。

        判定時に「同じ轍を踏もうとしていないか」を示す Few-shot 事例として使う。
        """
        # ルート直下ファイル（親ディレクトリなし）は重なり判定から除外する。
        # 空文字どうしが一致して無関係な変更を誤って「類似」と拾うのを防ぐ。
        dirs = {d for d in (parent_dir(p) for p in signals.code.changed_files) if d}
        hits: list[MisjudgedCase] = []
        for c in self.cases:
            if archetype is not None and c.archetype is not archetype:
                continue
            case_dirs = {d for d in (parent_dir(p) for p in c.changed_files) if d}
            if dirs & case_dirs:
                hits.append(c)
        return hits
