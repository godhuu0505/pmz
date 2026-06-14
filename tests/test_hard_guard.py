"""決定論的ハードガードの単体テスト（要件 §7 #5 / 設計インバリアント #3）。"""

from pmz.core.hard_guard import (
    HARD_GUARDED_FLAGS,
    hard_guarded_flags,
    is_hard_guarded,
)
from pmz.models import RiskFlag


def test_all_risk_flags_are_hard_guarded() -> None:
    # db_migration / auth / payment は全て自律承認禁止対象（§7 #5）。
    assert HARD_GUARDED_FLAGS == frozenset(RiskFlag)


def test_no_flags_means_not_guarded() -> None:
    assert is_hard_guarded([]) is False
    assert hard_guarded_flags([]) == []


def test_db_migration_triggers_guard() -> None:
    assert is_hard_guarded([RiskFlag.DB_MIGRATION]) is True
    assert hard_guarded_flags([RiskFlag.DB_MIGRATION]) == [RiskFlag.DB_MIGRATION]


def test_guarded_flags_preserves_only_risky() -> None:
    flags = [RiskFlag.AUTH, RiskFlag.PAYMENT]
    assert is_hard_guarded(flags) is True
    assert hard_guarded_flags(flags) == flags
