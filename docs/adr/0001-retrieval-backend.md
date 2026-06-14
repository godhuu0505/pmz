# ADR-0001: Few-shot 類似検索のバックエンド（Elasticsearch をどう活かすか）

- ステータス: Accepted（MVP は in-memory、Phase2 で差し替え）
- 日付: 2026-06-14
- 関連: 要件 §3.3.1 (3) 記憶/Few-shot ／ §4.2 永続化 ／ `src/pmz/store/ports.py`

## 背景

自己改善ループの (3) は「誤判定ケースを蓄積し、**判定時に類似の過去ケースを検索**して
プロンプトに注入する」。これは本質的に **検索（retrieval）問題** であり、データが増えるほど
「ディレクトリ重なり一致」では弱くなる。Elasticsearch を活かせる場所はまさにここ。

## 決定

Few-shot 類似検索を **`CaseRetriever` ポート（Protocol）** として切り出す（`store/ports.py`）。
判定器 `judge()` はこのポートにのみ依存し、実装を差し替え可能にする。

- **MVP**: `pmz.learning.memory.CaseMemory`（変更ファイルのディレクトリ重なり＋型一致）。依存ゼロ・即テスト可。
- **Phase2 の選択肢**:
  1. **Elasticsearch** — `changed_files` / `diff_summary` / リリースノートの **全文検索 ＋ kNN（ベクトル）の
     ハイブリッド**で「似たリリース」を引く。運用ノウハウが豊富で、监査ログの全文検索にも再利用できる。
  2. **Vertex AI Vector Search**（GCP 既定スタックと整合・Firestore と併用）。
  3. Firestore のみ（厳密一致・前方一致中心。意味検索は弱い）。

GCP 一本化なら 2 が素直だが、**ハイブリッド検索の質と全文検索の再利用**を重視するなら 1（Elasticsearch）。
どちらでも `CaseRetriever` を実装するだけで判定ロジックは無改修。

## 理由

- **継ぎ目の分離**: 検索の良し悪しは自己改善の質に直結するが、判定の正しさとは独立。ポートで分離すれば
  バックエンド比較（ES vs Vector Search）を回帰テスト（§3.3 (C)）で評価して選べる。
- **段階移行**: MVP を止めずに、データ量が増えた段階でアダプタを注入できる。

## 影響

- `judge()` / `Orchestrator` の `memory` 引数の型は `CaseRetriever`（Protocol）。
- Elasticsearch 採用時の追加要素（Phase2）: インデックス定義、埋め込み生成、`ElasticsearchCaseRetriever`
  アダプタ、Terraform/Helm によるクラスタ（または Elastic Cloud）プロビジョニング。MVP スコープ外。
