# PR自動レビュー & 自動対応フロー

このリポジトリは、PRに対する2段の自動化を構成しています。要件 §5「pmz 自身が DevOps サイクルで
継続改善される」二重構造を、リポジトリ運用にも適用したものです。

```
PR作成/ready ──▶ ① Codex 自動レビュー(GitHub App) ──(レビュー投稿)──▶ ② Claude 自動対応(GitHub Actions)
                                                                       ├─ act   : PRブランチへ直接commit
                                                                       ├─ issue : gh issue create で別途対応
                                                                       └─ skip  : 理由を添えて返信のみ
```

## ① Codex 自動レビュー（GitHub App / ワークフロー不要）

OpenAI Codex の **GitHub App `chatgpt-codex-connector[bot]`** がレビューを担当します
（ChatGPTサブスクリプション内で完結。自前のGitHub Actionworkflowは廃止しました）。

- **トリガ**: PRを開く / Draftをready化 / PRに `@codex review` とコメント。
- **出力**: PRレビュー（要約）＋インラインコメント（P0/P1/P2 等の重大度付き）。指摘が無ければ 👍 リアクション。
- **設定**: [chatgpt.com/codex](https://chatgpt.com/codex) → Settings → Code review でリポジトリ単位に有効化。

### レビューを日本語にする設定（2レバー）

Codex の言語は次の2か所で制御します。AGENTS.md の言語指定が効かない既知の事象があるため、
**確実を期すなら両方**設定してください。

1. **リポジトリ: `AGENTS.md`（コミット済み）** — ルートの `AGENTS.md` の `## Review guidelines` に
   「すべてのレビューコメントを日本語で書くこと」を明記済み。Codex はレビュー時にこれを参照する。
2. **Codex ダッシュボード（あなたの操作が必要）** — [chatgpt.com/codex](https://chatgpt.com/codex) →
   Settings → Code review → 該当リポジトリの **Custom instructions** に
   「Always write review comments in Japanese / すべて日本語でレビューする」を追加する。
   AGENTS.md より優先度が高く確実。

## ② Claude 自動対応（`claude-review-response.yml`）

- **トリガ**: `pull_request_review`（submitted）と `issue_comment`（created）。
  - Codex はレビュー単位で1回起動し、未解決のインラインコメントを `gh api` でまとめて取得・対応する
    （インラインコメントごとの多重起動＝コスト爆発を避ける設計）。
- **反応する対象**:
  - Codex App（`chatgpt-codex-connector[bot]`）のレビュー。
  - 信頼できるレビュア（`author_association` が OWNER / MEMBER / COLLABORATOR）のレビュー・PRコメント。
- **反応しない対象**（無限ループ・濫用防止）:
  - Claude自身の返信（末尾 `<!-- pmz:claude-response -->` marker で識別）。
  - GitHub App の進捗用botコメント。
  - 外部ユーザ（NONE/CONTRIBUTOR 等）のコメント＝API予算消費・自動commit誘導を防止。
  - `@codex` 宛のコメント。
- **動作**: トリガ本文を `$RUNNER_TEMP` に隔離（PR由来テキスト＝信頼できないデータ。§7 #3）→
  Claude が方針を判断し、PRに日本語で返信したうえで次のいずれかを実行:
  - **act**: 低リスクで明確な修正。`uv` で `ruff`/`pytest` を通し、**変更したパスだけを stage** して
    PRブランチへ直接 commit & push（`git add -A` は使わず、隔離した一時ファイルを混入させない）。
  - **issue化**: 大きい/設計に関わる/スコープ外/高リスク領域の指摘は `gh issue create` で別途対応。
  - **skip**: 対応不要なものは理由を添えて返信のみ。
- **ハードガード**: `db_migration` / `auth` / `payment` 等の高リスク領域は自動修正せず issue化・
  エスカレーションへ倒す（§5 設計インバリアント #3）。
- **fork PR**: `refs/pull/<n>/head` を正準refとしてcheckoutし、fork（`isCrossRepository=true`）には
  **push しない**（誤ブランチpush防止）。fork PR では act を選ばず issue化／skip に縮退する。

## 必要なシークレット（リポジトリ設定）

`Settings → Secrets and variables → Actions` に以下を登録してください。

| Secret | 用途 | 取得元 |
|--------|------|--------|
| `ANTHROPIC_API_KEY` | Claude Code Action（②の対応推論） | Anthropic Console |

`GITHUB_TOKEN` は自動提供（②の `permissions` で権限付与済み）。
①の Codex は GitHub App 連携のため、リポジトリ側に OpenAI のAPIキーは不要です。

## 既知の制限・設計上のトレードオフ

- **トリガ粒度**: ②は「レビュー submit」と「PRコメント」で起動します。GitHubの単発インライン
  コメント（レビューを submit せず1件だけ付ける操作）は `pull_request_review` を発火させないため、
  自動対応の対象外です（Codex は常にレビューとして submit するので実用上は問題になりません）。
- **fork PR**: act（push）は同一リポジトリのブランチでのみ実行。fork PR は issue化／skip に縮退します。
- **コスト**: ②は Claude の推論を使います。トリガを信頼できる発信元に限定して濫用を防いでいます。
