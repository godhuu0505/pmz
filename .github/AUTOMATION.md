# PR自動レビュー & 自動対応フロー

PRに対する2段の自動化。要件 §5「pmz 自身が DevOps サイクルで継続改善される」二重構造を、
リポジトリ運用にも適用したもの。設計判断は `docs/adr/0002-ai-pr-review-automation.md` を参照。

```
PR作成/ready ──▶ ① Codex 自動レビュー(GitHub App) ──(レビュー submit)──▶ ② Claude 自動対応(GitHub Actions)
                                                                         ├─ 対応 : PRブランチへ最小修正をcommit
                                                                         ├─ issue: gh issue create で別途追跡
                                                                         └─ skip : 理由を添えて返信のみ
```

## 0. 全体像（両方サブスク枠で完結／API従量課金なし）

| 役割 | 担当 | 仕組み | 課金 |
|------|------|--------|------|
| PRレビュー**生成** | **Codex** | GitHub App（ワークフロー不要・サーバー側） | ChatGPTサブスク（Plus等） |
| レビューへの**対応・返信・修正** | **Claude** | GitHub Actions ワークフロー（必須） | Claude Pro/Maxサブスク（OAuth） |

## 1. Codex 側セットアップ（GUI・1回だけ／ワークフロー不要）

1. ブラウザで **`chatgpt.com/codex`** にアクセス（ChatGPTサブスクのアカウントでログイン）
2. **Settings → Code review** を開く
3. **「Connect to GitHub」** → Codex GitHub App（`chatgpt-codex-connector`）を対象リポジトリにインストール
4. 対象リポジトリで **Code review をON**、さらに **Automatic reviews をON**
5. 手動トリガーは PRコメントに **`@codex review`**

### レビューを日本語にする（2レバー）

1. **リポジトリ: `AGENTS.md`（コミット済み）** — ルートの `## Review guidelines` に「日本語で書く」を明記済み。
2. **Codex ダッシュボード（あなたの操作が必要・確実）** — chatgpt.com/codex → Settings → Code review →
   該当リポジトリの **Custom instructions** に「Always write review comments in Japanese」を追加。
   AGENTS.md の言語指定が無視される既知事象があるため、確実を期すならこちらを併用。

## 2. Claude 側セットアップ

### 2-1. OAuthトークン発行（API従量課金を避ける）
```bash
claude setup-token
```
→ ブラウザでPro/Maxアカウントを承認 → `sk-ant-oat...` をコピー。
> ⚠️ Anthropic Console の**APIキーは使わない**（従量課金）。必ず `claude setup-token` のOAuthトークン。

### 2-2. Claude GitHub App をインストール
- **https://github.com/apps/claude** から対象リポジトリにインストール（コメント投稿・修正コミットに必須）。

### 2-3. GitHub Secret 登録（Settings → Secrets and variables → Actions）
- Name: `CLAUDE_CODE_OAUTH_TOKEN` / Value: `sk-ant-oat...`

### 2-4. Actions 権限
- Settings → Actions → General → **Workflow permissions = Read and write**

## 3. ワークフロー（`.github/workflows/claude-review-response.yml`）

このリポジトリにコミット済み。要点:
- トリガ: `pull_request_review`（submitted）。Codexはレビュー単位でsubmitするため、Claudeがインライン指摘を
  `gh api .../pulls/<n>/comments` で集約取得して対応。
- 起動元限定: `chatgpt-codex-connector[bot]` か人間レビューのみ（`approved` と自己投稿では起動しない）。`allowed_bots` で Codex Bot を許可。
- 認証: `CLAUDE_CODE_OAUTH_TOKEN`（サブスク枠）＋ `id-token: write`（OIDC）。
- 安全規律: PR由来テキストは信頼できないデータ（§7 #3）／高リスク領域は自動修正せず issue化（§5）。

> ⚠️ `pull_request_review` イベントは**デフォルトブランチ(main)のワークフローしか実行しない**仕様。
> PRブランチに置いただけでは発火しないため、**必ず main にマージしてから**動作確認する。

## 4. ⚠️ ハマりどころ

| 症状 | 原因 | 対策 |
|------|------|------|
| ワークフローが**全く発火しない** | `pull_request_review` はデフォルトブランチのワークフローのみ実行 | **mainにマージしてから**テスト |
| `Workflow initiated by non-human actor` で失敗 | claude-code-action はBot起動をデフォルト拒否 | `allowed_bots: "chatgpt-codex-connector[bot]"` |
| OIDC認証エラーで即落ち | ビルトインApp認証に`id-token`必要 | `permissions: id-token: write` |
| `gh`/`git`が権限拒否 | Bashはデフォルト無効 | `--allowedTools "Bash(gh:*),Bash(git:*),..."` |
| triageが**赤❌**（自己再起動） | Claudeの返信/修正投稿が再びワークフローを起動 | job `if` を Codex Bot か人間のみ＋`approved`除外に限定 |
| レビューが英語 | 外枠はCodex固定テンプレ／指摘本文は AGENTS.md・ダッシュボードで日本語化 | `## Review guidelines` に日本語明記＋Custom instructions |
| Claudeが二重にレビュー | Claudeネイティブ Code Review も有効 | Codexのみにするなら claude.ai 設定で Claude の Code Review をOFF（GitHub App自体は残す） |

## 5. 動作確認

1. すべて設定し、ワークフローを **main にマージ**。
2. 小さなテストPRを作成（あえて改善余地のあるコードを入れる）。
3. `@codex review` をコメント。
4. Codexが日本語レビュー → **Claudeが自動で対応方針を返信＋必要なら修正コミット** されればOK。

## 必要なものチェックリスト

- [ ] Codex GitHub App インストール＋Automatic reviews ON（chatgpt.com/codex）
- [ ] Claude GitHub App インストール（github.com/apps/claude）
- [ ] `claude setup-token` で OAuthトークン発行 → Secret `CLAUDE_CODE_OAUTH_TOKEN`
- [ ] Actions の Workflow permissions = Read and write
- [ ] `.github/workflows/claude-review-response.yml` を main にマージ
- [ ] `AGENTS.md` に `## Review guidelines`
- [ ]（任意）Claudeネイティブ Code Review は OFF（Codexのみにする場合）
