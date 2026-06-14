terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.40"
    }
  }

  # NOTE: 本番では GCS バックエンドを設定する（MVP 雛形では未設定）。
  # backend "gcs" {
  #   bucket = "pmz-tfstate"
  #   prefix = "pmz"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
