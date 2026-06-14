"""GateKeeper (仮称) — AIリリース判定ゲートキーパー × 自己改善エージェント.

MVP スコープ: PRマージゲート。シグナルは code + CI + 要件充足（要件定義書ベース）。
詳細は ``release-gatekeeper-agent-requirements.md`` を参照。
"""

from gatekeeper.models import ReleaseRecord, Verdict

__all__ = ["ReleaseRecord", "Verdict"]
