resource "google_project" "batch_platform" {
  project_id      = var.project_id
  name            = var.project_name
  billing_account = var.billing_account_id
}

# APIs this project needs enabled before anything else can be created.
resource "google_project_service" "apis" {
  for_each = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "iam.googleapis.com",
  ])
  project = google_project.batch_platform.project_id
  service = each.value

  disable_dependent_services = false
}

# --- BigQuery datasets -------------------------------------------------

resource "google_bigquery_dataset" "staging" {
  project    = google_project.batch_platform.project_id
  dataset_id = "staging"
  location   = var.region
  description = "Silver-layer data loaded from Parquet, before dbt transforms."

  depends_on = [google_project_service.apis]
}

resource "google_bigquery_dataset" "marts" {
  project    = google_project.batch_platform.project_id
  dataset_id = "marts"
  location   = var.region
  description = "dbt-built Gold-layer models for analysis."

  depends_on = [google_project_service.apis]
}

# --- GCS staging bucket --------------------------------------------------
# Parquet files are uploaded here first, then loaded into BigQuery via
# `bq load` -- far faster than row-by-row insert for 20M+ row files.

resource "google_storage_bucket" "staging" {
  project                     = google_project.batch_platform.project_id
  name                        = "${var.project_id}-staging"
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  depends_on = [google_project_service.apis]
}

# --- Service account for dbt --------------------------------------------
# Least privilege: dbt needs to read/write BigQuery data and run query
# jobs, and read the GCS bucket during loads. Nothing broader than that.

resource "google_service_account" "dbt_runner" {
  project      = google_project.batch_platform.project_id
  account_id   = var.dbt_service_account_id
  display_name = "dbt runner (least-privilege)"

  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "dbt_bq_data_editor" {
  project = google_project.batch_platform.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

resource "google_project_iam_member" "dbt_bq_job_user" {
  project = google_project.batch_platform.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dbt_runner.email}"
}

# Why: GCS implements overwriting an existing object as delete + create
# under the hood, even for a plain "upload" call. objectCreator alone
# (create-only) isn't enough once a run re-uploads a filename that
# already exists in the bucket -- which happens on every run after the
# first, since the Fannie Mae part-file names never change.
#
# objectAdmin (create/delete/get/list) is still scoped to just THIS
# bucket via the `bucket =` argument below -- it grants nothing on any
# other bucket or resource in the project.

resource "google_storage_bucket_iam_member" "dbt_gcs_admin" {
  bucket = google_storage_bucket.staging.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dbt_runner.email}"
}

# Key file for local dbt authentication. In a real production setup this
# would be Workload Identity Federation instead of a long-lived key --
# a key file is the pragmatic choice for a local portfolio project, but
# worth naming as a trade-off in the README.
resource "google_service_account_key" "dbt_runner_key" {
  service_account_id = google_service_account.dbt_runner.name
}

resource "local_file" "dbt_runner_key_file" {
  content         = base64decode(google_service_account_key.dbt_runner_key.private_key)
  filename        = "${path.module}/dbt-runner-key.json"
  file_permission = "0600"
}
