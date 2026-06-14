"""永続化の抽象層（要件 §4.2 永続化 / §8.1）.

判定ログ・監査証跡・受け入れ基準正本・Few-shot 記憶の **保存と検索をポート（Protocol）で抽象化**
し、実装（アダプタ）を差し替え可能にする。

- MVP: in-memory ＋ JSONL（`pmz.store.inmemory` / 既存 `AuditLog`・`CaseMemory`）。
- Phase2: **Firestore**（判定ログ・監査証跡・正本）／
  **Elasticsearch もしくは Vertex AI Vector Search**（Few-shot 類似検索 = ``CaseRetriever``）
  をアダプタとして注入する。

> なぜ検索を別ポートにするか: 自己改善の Few-shot 検索（§3.3.1 (3)）は「過去の類似ケースを引く」
> 全文・意味検索が本質。MVP のディレクトリ重なり一致から、全文/kNN ハイブリッド（Elasticsearch）
> やベクトル検索へ、判定ロジックを触らず昇格できる継ぎ目をここに用意する。詳細は
> `docs/adr/0001-retrieval-backend.md`。
"""
