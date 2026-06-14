# ai-hackathon
DevOps × AI Agent Hackathon 2026: AI エージェントを「つくる、まわす、とどける」夏

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
