#!/usr/bin/env bash
# SessionStart hook — Claude Code on the web のセッション開始時に依存をブートストラップする。
# tests / linters がセッション内で即座に実行できる状態を保証する（同期実行）。
# 設計方針: 冪等・非対話。コンテナ状態はフック完了後にキャッシュされるため uv sync を使う。
set -euo pipefail

# リモート（Claude Code on the web）でのみブートストラップする。
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$PROJECT_DIR"

# Python 依存（pydantic + dev: ruff/pytest）をインストール。stdout を汚さないよう stderr へ。
if command -v uv >/dev/null 2>&1 && [ -f pyproject.toml ]; then
  uv sync >&2

  # セッション残りの期間 .venv を PATH に載せ、`python` / `pytest` / `ruff` を直接使えるようにする。
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    {
      echo "export VIRTUAL_ENV=\"$PROJECT_DIR/.venv\""
      echo "export PATH=\"$PROJECT_DIR/.venv/bin:\$PATH\""
    } >> "$CLAUDE_ENV_FILE"
  fi
fi
