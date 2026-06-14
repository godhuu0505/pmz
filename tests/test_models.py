"""ReleaseRecord スキーマの基本テスト（lint/test ハーネスの動作確認も兼ねる）。"""

import pytest
from pydantic import ValidationError

from gatekeeper.models import (
    Act,
    Archetype,
    ReleaseRecord,
    RiskFlag,
    Verdict,
)

# §9.1 アーク #7: 型(i) DBマイグレーション地雷（見逃し→24h障害）。
TRAP_RECORD = {
    "id": "rel-007",
    "pr_number": 7,
    "commit_sha": "a1b2c3d",
    "timestamp": "2026-06-01T09:00:00",
    "author": "dev-a",
    "code": {
        "diff_summary": "users テーブルに NOT NULL カラムを追加するマイグレーション",
        "changed_files": ["migrations/0007_add_col.sql"],
        "risk_flags": ["db_migration"],
        "lines_changed": 42,
    },
    "ci": {"tests_pass": True, "coverage": 0.78},
    "requirement": {
        "requirement_ids": ["REQ-12"],
        "acceptance_criteria": ["既存ユーザーのログインが継続できる"],
        "release_note": "プロフィール拡張のためのスキーマ変更",
    },
    "post_events": [
        {
            "type": "incident",
            "timestamp": "2026-06-01T20:00:00",
            "linked_sha": "a1b2c3d",
            "touched_files": ["migrations/0007_add_col.sql"],
        }
    ],
    "labels": {
        "incident_axis": {"value": "fail", "confirmed_at": "2026-06-02T09:00:00"},
        "requirement_axis": {"value": "met", "status": "final"},
        "correct_verdict": "No-Go",
    },
    "arc": {
        "archetype": "db_migration",
        "act": "1_trap",
        "recurrence_group_id": "grp-db-1",
    },
}


def test_valid_record_round_trips() -> None:
    rec = ReleaseRecord.model_validate(TRAP_RECORD)
    assert rec.labels.correct_verdict is Verdict.NO_GO
    assert rec.arc.archetype is Archetype.DB_MIGRATION
    assert rec.arc.act is Act.TRAP
    assert RiskFlag.DB_MIGRATION in rec.code.risk_flags

    # JSON ラウンドトリップで等価性を保つ。
    again = ReleaseRecord.model_validate_json(rec.model_dump_json())
    assert again == rec


def test_hard_guard_detected_for_high_risk() -> None:
    rec = ReleaseRecord.model_validate(TRAP_RECORD)
    assert rec.has_hard_guard_risk() is True


def test_invalid_enum_rejected() -> None:
    bad = {**TRAP_RECORD, "labels": {**TRAP_RECORD["labels"], "correct_verdict": "maybe"}}
    with pytest.raises(ValidationError):
        ReleaseRecord.model_validate(bad)
