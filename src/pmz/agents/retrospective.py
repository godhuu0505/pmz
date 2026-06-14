"""Retrospective エージェント（要件 §3.3 (B) / §3.3.1 (3) ルール自動進化）.

確定した客観イベント（障害確定 / 要件未達確定）から見逃しを振り返り、新チェックルールを
**提案** する reader。承認権限は持たない（§7 #3）――提案を本番ルールブックへ採用するかは
Orchestrator / 学習ループ側のガバナンス判断（§3.3.1 (4)）に委ねる。

ロジック本体は ``pmz.learning.retrospective`` の純粋関数。本クラスはそれを「提案だけする
エージェント」として薄くラップし、提案と採用を分離する（学習における権限分離）。
"""

from __future__ import annotations

from pmz.agents.base import AgentRole
from pmz.learning.retrospective import is_confirmed_bad, learn_rule_from
from pmz.learning.rulebook import LearnedRule
from pmz.models import ReleaseRecord


class RetrospectiveAgent:
    """誤判定の振り返りから新ルールを提案する reader（採用権限なし）。"""

    name = "RetrospectiveAgent"
    role = AgentRole.READER

    def propose(self, record: ReleaseRecord, *, next_version: int) -> LearnedRule | None:
        """確定した見逃しなら新ルールを提案する。それ以外は ``None``（提案なし）。

        正解ラベルは客観イベントからのみ導出（自己生成ラベルで学習しない・インバリアント #6）。
        """
        if not is_confirmed_bad(record):
            return None
        return learn_rule_from(record, version=next_version)
