variable "project_id" {
  description = "GCP プロジェクト ID"
  type        = string
}

variable "region" {
  description = "デプロイ先リージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "service_name" {
  description = "Cloud Run サービス名"
  type        = string
  default     = "pmz"
}

variable "image" {
  description = "Cloud Run にデプロイするコンテナイメージ（Artifact Registry のフルパス）"
  type        = string
  default     = "asia-northeast1-docker.pkg.dev/PROJECT/pmz/pmz:latest"
}

variable "gemini_model" {
  description = "判定に使う Gemini モデル ID（監査証跡の model_version に記録される）"
  type        = string
  default     = "gemini-2.5-pro"
}
