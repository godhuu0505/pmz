# ADR-0002: AI による PRレビュー自動化（Codex 生成 → Claude 対応）

- ステータス: Accepted
- 日付: 2026-06-16
- 関連: 要件 §5（pmz 自身が DevOps サイクルで継続改善される二重構造）／§7 #3（PR由来テキストの信頼境界）／
  `.github/workflows/claude-review-response.yml`／`AGENTS.md`／`.github/AUTOMATION.md`

## 背景

PR に対し「レビューを自動生成」し、その「レビューへ自動で対応・返信・修正」する2段の自動化を入れたい。
当初は自前の Codex CLI ワークフロー（`codex-review.yml` + `OPENAI_API_KEY`）と、Claude Code Action
（`ANTHROPIC_API_KEY`）で実装したが、以下の課題があった。

- API キー方式は**従量課金**が発生する（Codex/Claude とも）。
- 自前 Codex CLI ワークフローは fork PR でシークレット不達・恒久失敗、`GITHUB_TOKEN` 投稿が
  下流ワークフローを起動しない等の制約があった（Codex 自身のレビューで P1/P2 指摘）。

## 決定

**役割を 2 つのサービスに分離し、両方ともサブスクリプション枠で完結させる**（API 従量課金なし）。

| 役割 | 担当 | 仕組み | 課金 |
|------|------|--------|------|
| PRレビューの**生成** | **Codex** | GitHub App `chatgpt-codex-connector`（ワークフロー不要・サーバー側） | ChatGPT サブスク |
| レビューへの**対応・返信・修正** | **Claude** | GitHub Actions（`claude-review-response.yml`） | Claude Pro/Max サブスク（OAuth） |

主要な設計点:

1. **認証は OAuth トークン**（`claude setup-token` で発行 → Secret `CLAUDE_CODE_OAUTH_TOKEN`）。
   Anthropic Console の API キーは使わない（従量課金回避）。`id-token: write` でビルトイン App 認証(OIDC)。
2. **トリガは `pull_request_review`（submitted）に一本化**。Codex はレビュー単位で submit するため、
   インライン指摘は Claude が `gh api .../pulls/<n>/comments` で集約取得する（多重起動＝コスト爆発を回避）。
3. **起動元を限定**（ループ・濫用防止）: `chatgpt-codex-connector[bot]` か人間レビュー（`type != 'Bot'`）のみ。
   `approved` レビューや Claude 自身の投稿では起動しない。`allowed_bots` で Codex Bot 起動を明示許可。
4. **レビューは日本語**: `AGENTS.md` の `## Review guidelines` で指定。AGENTS.md の言語指定が効かない
   既知事象があるため、確実を期すなら Codex ダッシュボード（chatgpt.com/codex → Settings → Code review）の
   Custom instructions にも日本語指定を併用する。
5. **安全規律**: PR由来テキストは信頼できないデータとして扱い埋め込み指示に従わない（§7 #3）。
   db_migration / auth / payment 等の高リスク領域は自動修正せず issue 化（§5 ハードガード）。

## 理由

- **コスト**: サブスク枠で完結し API 従量課金が出ない。ハッカソンの個人運用に適する。
- **保守性**: Codex レビュー生成はサーバー側に委譲し、自前ワークフローの fork/secret/権限問題を排除。
- **DevOps 二重構造（§5）**: pmz が掲げる「PM観点でのゲート＋自己改善」の規律を、リポジトリ運用自身にも適用する。

## 影響

- 廃止: 自前 `codex-review.yml`（Codex CLI 方式）。Codex レビューは GitHub App に一本化。
- 必要シークレット: `CLAUDE_CODE_OAUTH_TOKEN`（②用）。①Codex は GitHub App 連携のため不要。
- セットアップ手順・ハマりどころは `.github/AUTOMATION.md` を参照（他リポジトリへの展開手順を含む）。
- 既知の制約: 単発インラインコメント（レビュー未submit）は `pull_request_review` を発火させないため対象外。
  Claude ネイティブの Code Review も有効な場合はレビューが二重化するため、Codex のみにするなら OFF にする。
