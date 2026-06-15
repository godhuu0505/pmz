# PR自動レビュー & 自動対応フロー

このリポジトリは、PRに対する2段の自動化を GitHub Actions で構成しています。
要件 §5「pmz 自身が DevOps サイクルで継続改善される」二重構造を、リポジトリ運用にも適用したものです。

```
PR作成 ──▶ ① Codex 自動レビュー ──(レビューコメント投稿)──▶ ② Claude 自動対応
 (codex-review.yml)                                       (claude-review-response.yml)
                                                            ├─ act   : PRブランチへ直接commit
                                                            ├─ issue : gh issue create で別途対応
                                                            └─ skip  : 理由を添えて返信のみ
```

## ① Codex 自動レビュー（`codex-review.yml`）

- **トリガ**: PRの `opened` / `reopened` / `ready_for_review` / `synchronize`（Draftは対象外）。
- **動作**: `origin/<base>...HEAD` の diff を抽出 → OpenAI Codex CLI でレビュー → PRコメントとして投稿。
- レビューコメントには `<!-- pmz:codex-review -->` marker を付与し、②がこれを拾えるようにしている。
- レビュー観点: バグ/エッジケース・セキュリティ（§7 #3 プロンプトインジェクション）・要件トレーサビリティ
  （§5 設計インバリアント、ハードガード逸脱）・テスト/lint/可読性。

## ② Claude 自動対応（`claude-review-response.yml`）

- **トリガ**: `issue_comment` / `pull_request_review_comment` / `pull_request_review`。
- **反応する対象**: Codexレビュー（marker付きbotコメント）と、人間のレビューコメント。
- **反応しない対象**:
  - Claude自身の返信（末尾の `<!-- pmz:claude-response -->` marker で識別し、無限ループを防止）。
  - Claude Action の進捗用botコメント（markerなしbotコメントは弾く）。
- **動作**: コメントを `review-comment.txt` に隔離（PR由来テキストは信頼できないデータ。§7 #3）→
  Claude が方針を判断し、PRに返信したうえで次のいずれかを実行:
  - **act**: 低リスクで明確な修正。`ruff`/`pytest` を通してから **PRブランチへ直接 commit & push**。
  - **issue化**: 大きい/設計に関わる/スコープ外/高リスク領域の指摘は `gh issue create` で別途対応。
  - **skip**: 対応不要なものは理由を添えて返信のみ。
- **ハードガード**: `db_migration` / `auth` / `payment` 等の高リスク領域は自動修正せず、必ず issue化 or
  人間エスカレーションへ倒す（§5 設計インバリアント #3）。

## 必要なシークレット（リポジトリ設定）

`Settings → Secrets and variables → Actions` に以下を登録してください。

| Secret | 用途 | 取得元 |
|--------|------|--------|
| `OPENAI_API_KEY` | Codex CLI のレビュー推論 | OpenAI Platform |
| `ANTHROPIC_API_KEY` | Claude Code Action の対応推論 | Anthropic Console |

`GITHUB_TOKEN` は GitHub が自動提供するため登録不要です（ワークフローの `permissions` で権限を付与済み）。

## 既知の制限

- **Fork からのPR**: `act`（PRブランチへのpush）は同一リポジトリのブランチでのみ成功します。
  Fork PR は push 権限がないため、Claude は issue化 または返信のみに縮退します。
- **Codex CLI のフラグ**: `--sandbox workspace-write` / `--output-last-message` を使用。CLIのバージョン更新で
  挙動が変わる場合があります（出力が空のときは stdout/ログにフォールバックします）。
- **コスト**: `synchronize` で push のたびに Codex レビューが走ります。コストを抑えたい場合は
  `codex-review.yml` の `on.pull_request.types` から `synchronize` を外してください。
