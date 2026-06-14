# pmz インフラ（Terraform 雛形）

要件 §4.2（GCPサービスマッピング）/ §5（IaC）に対応する **設計用スケルトン**。
MVP では `apply` しない（GCP プロジェクト・課金が必要なため）。DevOps サイクルの
「Infrastructure as Code」要件の充足と、本番構成の意図の明文化が目的。

## 定義しているリソース

| リソース | 役割（要件） |
|----------|--------------|
| `google_cloud_run_v2_service` | エージェント本体・Webhook 受信のホスト＋オートスケール（§4.2） |
| `google_firestore_database` | 判定ログ・監査証跡・受け入れ基準正本の永続化（§4.2 / §7 #4） |
| `google_artifact_registry_repository` | コンテナイメージ |
| `google_service_account` ＋ IAM | 最小権限（Firestore 書き込み・Vertex AI 呼び出し） |
| `google_project_service` | 必要 API の有効化（run / firestore / artifactregistry / aiplatform） |

> Few-shot 類似検索のバックエンド（Elasticsearch / Vertex AI Vector Search）は
> ADR-0001 を参照。採用時に本雛形へリソースを追加する（Phase2）。

## 使い方（将来・参考）

```bash
cd infra/terraform
terraform init
terraform plan  -var project_id=YOUR_PROJECT -var image=...:TAG
terraform apply -var project_id=YOUR_PROJECT -var image=...:TAG
```

`terraform fmt -check` / `terraform validate` を CI に追加するのは Phase2。
