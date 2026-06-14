"""振り返りエージェント（要件 §3.3.1 (3) ルール自動進化 / §3.3 (B)）.

確定した **客観イベント**（24hで確定する障害軸 / 最大30日で確定する要件充足軸）から、
見逃した観点を一般化した新チェックルールを起こす。MVP は決定論ヒューリスティック版
（LLM を介さない）で、変更ファイルから「再発しやすい危険領域」の glob を抽出する。

帰属に ``arc.archetype`` を使うのは正当（振り返りは **障害確定後** に走り、post_events 等の
客観事後シグナルで型を判断できるため・§3.3.1 (1)(2)）。判定時の発火はこの glob ルール
だけを使い、型を覗き見しない（学習と推論の分離）。

> インバリアント #6: 正解ラベルは客観イベントから導出。自己生成ラベルで学習しない。
"""

from __future__ import annotations

from gatekeeper.learning.rulebook import LearnedRule, RuleAction
from gatekeeper.models import Archetype, ReleaseRecord

# db_migration 型の危険ファイルを見分けるパス標識（決定論）。
_MIGRATION_MARKERS = ("migration", "migrations")


def is_confirmed_bad(record: ReleaseRecord) -> bool:
    """客観イベントで「悪いリリースだった」と確定しているか（学習トリガ・§3.3.1 (1)）。

    障害軸 fail、または要件充足軸が unmet で最終確定（final）したケース。
    LLM 判断ではなく **自動導出された客観ラベル** のみを使う。
    """
    inc = record.labels.incident_axis
    req = record.labels.requirement_axis
    if inc.value.value == "fail":
        return True
    return req.value.value == "unmet" and req.status.value == "final"


def learn_rule_from(record: ReleaseRecord, *, version: int) -> LearnedRule | None:
    """確定した誤承認（見逃し）リリースから新ルールを起こす。

    型ごとに「再発しうる危険領域」を変更ファイルから一般化してディレクトリ glob 化する:

    - **db_migration**: パスに migration 標識を含むファイルの親ディレクトリ。
    - **requirement_miss**: 変更ファイル全件の親ディレクトリ（薄く触れて要件未達になった領域）。

    一般化できる glob が無ければ ``None``（学習見送り）。
    """
    archetype = record.arc.archetype
    if archetype is None:
        return None

    files = record.code.changed_files
    if archetype is Archetype.DB_MIGRATION:
        targets = [f for f in files if any(m in f.lower() for m in _MIGRATION_MARKERS)]
    else:
        targets = list(files)

    globs = sorted({_dir_glob(f) for f in targets if _dir_glob(f)})
    if not globs:
        return None

    return LearnedRule(
        id=f"learned-{archetype.value}-v{version}",
        version=version,
        archetype=archetype,
        file_globs=globs,
        action=RuleAction.BLOCK,
        description=(
            f"{archetype.value} 型の見逃し（{record.id}）を学習。"
            f"{', '.join(globs)} に触れる変更は再発リスクとして検知する。"
        ),
        created_from=record.id,
    )


def _dir_glob(path: str) -> str:
    """ファイルパスを親ディレクトリ配下の glob に一般化（``a/b/c.py`` → ``a/b/*``）。"""
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[0] + "/*"
