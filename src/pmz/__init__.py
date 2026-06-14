"""pmz — AIリリース判定ゲートキーパー × 自己改善エージェント.

名称 pmz = PM観点 × Z軸（自己改善の時間軸）。命名の理由は ``docs/requirements.md`` §1 を参照。
MVP スコープ: PRマージゲート。シグナルは code + CI + 要件充足（要件定義書ベース）。
"""

from pmz.models import ReleaseRecord, Verdict

__all__ = ["ReleaseRecord", "Verdict"]
