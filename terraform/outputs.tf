output "project_id" {
  value = google_project.batch_platform.project_id
}

output "staging_bucket" {
  value = google_storage_bucket.staging.name
}

output "staging_dataset" {
  value = google_bigquery_dataset.staging.dataset_id
}

output "marts_dataset" {
  value = google_bigquery_dataset.marts.dataset_id
}

output "dbt_service_account_email" {
  value = google_service_account.dbt_runner.email
}

output "dbt_key_file_path" {
  value = local_file.dbt_runner_key_file.filename
}
