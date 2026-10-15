variable "project_id" {
  description = "Globally unique GCP project ID -- cannot be changed after creation."
  type        = string
  default     = "dolapo-de-portfolio-batch"
}

variable "project_name" {
  description = "Human-readable project display name."
  type        = string
  default     = "DE Portfolio - Batch"
}

variable "billing_account_id" {
  description = "Billing account to link this project to (the OPEN=True one)."
  type        = string
  sensitive   = true
}

variable "region" {
  description = "Default region for resources."
  type        = string
  default     = "us-central1"
}

variable "dbt_service_account_id" {
  description = "Account ID (prefix) for the dbt service account."
  type        = string
  default     = "dbt-runner"
}
