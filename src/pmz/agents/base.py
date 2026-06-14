"""エージェントの役割定義（権限分離の型レベル表現・§7 #3）.

``AgentRole`` で「読むだけ（reader）」と「統合判定（orchestrator）」を区別する。
reader は ``GateDecision`` を生成・返却してはならない（承認権限なし）。この規律は
コードレビューと監査証跡（どのエージェントが寄与したか）で担保する。
"""

from __future__ import annotations

from enum import StrEnum


class AgentRole(StrEnum):
    """エージェントの権限区分（§7 #3 権限分離）。"""

    READER = "reader"  # 読むだけ・承認権限なし（構造化シグナル/所見/提案のみ）
    ORCHESTRATOR = "orchestrator"  # 構造化シグナルからのみ統合判定を下す
