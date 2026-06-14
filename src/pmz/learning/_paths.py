"""学習機構が共有するパス処理ヘルパ.

``memory`` の類似検索（親ディレクトリの重なり）と ``retrospective`` のルール
一般化（親ディレクトリの glob 化）が同じ「POSIX パスの親ディレクトリ」概念を使うため、
単一の出どころに集約してロジックの食い違いを防ぐ。
"""

from __future__ import annotations


def parent_dir(path: str) -> str:
    """POSIX パスの親ディレクトリ。区切りが無ければ空文字（ルート直下）。"""
    return path.rsplit("/", 1)[0] if "/" in path else ""


def dir_glob(path: str) -> str:
    """親ディレクトリ配下の glob に一般化（``a/b/c.py`` → ``a/b/*``）。

    ルート直下のファイル（親なし）は一般化対象にせず空文字を返す。
    """
    d = parent_dir(path)
    return f"{d}/*" if d else ""
