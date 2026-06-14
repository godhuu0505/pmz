# ai-hackathon
DevOps × AI Agent Hackathon 2026: AI エージェントを「つくる、まわす、とどける」夏

提出作品 **GateKeeper（仮称）** — AIリリース判定ゲートキーパー × 自己改善エージェント。
要件定義は [`release-gatekeeper-agent-requirements.md`](release-gatekeeper-agent-requirements.md)。

## AI駆動開発ハーネス

本リポジトリは Claude Code で AI 駆動開発を回すための **ハーネス（足場）** を備えています。

- プロジェクトメモリ: [`CLAUDE.md`](CLAUDE.md)（MVPスコープ・設計インバリアント・コマンド・規約）
- ハーネスの設計意図と適用したベストプラクティス: [`.claude/README.md`](.claude/README.md)
- 起動フックが `uv sync` で依存を導入するため、セッション開始後すぐ `uv run pytest -q` /
  `uv run ruff check .` が通ります。

### MVP スケルトン

- `src/gatekeeper/models.py` — 合成リリース履歴のデータモデル（要件 §9.1）。
- `tests/` — pytest。lint は ruff。`uv sync` → `uv run pytest -q` で検証。

## grill-me — 要件ヒアリングスキル

オープンソースの [`grill-me`](https://github.com/mattpocock/skills) の思想をベースに、
**要件をめちゃくちゃ深掘りヒアリングする** Claude Code スキルを導入しています。

- 場所: `.claude/skills/grill-me/SKILL.md`
- 使い方: Claude Code 上で「**grill me**」「**要件をヒアリングして**」「**この企画を壁打ちして**」
  などと話しかけると起動します
- 動き: AI が実装には手を出さず、インタビュアーに徹して
  背景 → 目的 → ユーザー → スコープ → 機能/非機能要件 → 制約 → 成功指標 → リスク
  を一問ずつ徹底的に深掘りします
- 成果物: `grill-me-sessions/<plan-name>.grill.md` に決定・保留・確定要件が蓄積され、
  そのまま要件定義のドラフトになります

### クイックスタート
```
あなた:  grill me。新しい在庫管理アプリの要件を詰めたい
Claude:  まずセッション名を決めましょう。短いプラン名は?（例: inventory-app）
あなた:  inventory-app
Claude:  了解。では背景から。なぜ今これを作るのですか? — 今ある一番の痛みは?
...（一問ずつ深掘りが続く）
```
