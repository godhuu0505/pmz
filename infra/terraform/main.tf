# pmz インフラ雛形（要件 §4.2 / §5 IaC）。
# MVP では apply しない設計用スケルトン。Cloud Run（実行基盤）/ Firestore（判定ログ・監査証跡・
# 受け入れ基準正本）/ Vertex AI（Gemini 判定推論）/ Artifact Registry（イメージ）を最小構成で定義する。

locals {
  services = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com", # Gemini / Vertex AI
  ]
}

# 必要 API の有効化。
resource "google_project_service" "enabled" {
  for_each                    = toset(local.services)
  service                     = each.value
  disable_dependent_services  = false
  disable_on_destroy          = false
}

# コンテナイメージ置き場（Artifact Registry）。
resource "google_artifact_registry_repository" "pmz" {
  location      = var.region
  repository_id = "pmz"
  format        = "DOCKER"
  description   = "pmz container images"
  depends_on    = [google_project_service.enabled]
}

# 判定ログ・監査証跡・受け入れ基準正本の永続化（Firestore Native）。
resource "google_firestore_database" "pmz" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on  = [google_project_service.enabled]
}

# Cloud Run サービスの実行 SA（最小権限）。
resource "google_service_account" "pmz_run" {
  account_id   = "${var.service_name}-run"
  display_name = "pmz Cloud Run runtime"
}

# 監査証跡/判定ログを Firestore に書く権限。
resource "google_project_iam_member" "datastore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.pmz_run.email}"
}

# Gemini（Vertex AI）を呼ぶ権限。
resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.pmz_run.email}"
}

# Webhook 受信 ＋ 判定をホストする Cloud Run サービス。
resource "google_cloud_run_v2_service" "pmz" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.pmz_run.email

    containers {
      image = var.image

      env {
        name  = "PMZ_GEMINI_MODEL"
        value = var.gemini_model
      }
      env {
        name  = "PMZ_FIRESTORE_DATABASE"
        value = google_firestore_database.pmz.name
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    # オートスケール（必須要件・§4.2）。
    scaling {
      min_instance_count = 0
      max_instance_count = 4
    }
  }

  depends_on = [google_project_service.enabled]
}
