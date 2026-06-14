output "service_url" {
  description = "Cloud Run サービスの URL（GitHub Webhook の宛先）"
  value       = google_cloud_run_v2_service.pmz.uri
}

output "artifact_registry" {
  description = "コンテナイメージのリポジトリ"
  value       = google_artifact_registry_repository.pmz.name
}

output "firestore_database" {
  description = "判定ログ・監査証跡の Firestore データベース"
  value       = google_firestore_database.pmz.name
}

output "runtime_service_account" {
  description = "Cloud Run 実行 SA"
  value       = google_service_account.pmz_run.email
}
