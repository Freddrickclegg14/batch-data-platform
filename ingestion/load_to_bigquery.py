from pathlib import Path

from google.cloud import bigquery, storage

PROJECT_ID = "dolapo-de-portfolio-batch"
BUCKET_NAME = "dolapo-de-portfolio-batch-staging"
DATASET = "staging"

# (local Parquet path, GCS blob name, BigQuery table name)
FILES_TO_LOAD = [
    (
        Path("data/silver/fannie_mae/loan_performance.parquet"),
        "fannie_mae/loan_performance/",
        "fannie_mae_loan_performance",
    ),
    (
        Path("data/raw/yfinance"),
        "yfinance/",
        "yfinance_prices",
    ),
]


def upload_to_gcs(
    storage_client: storage.Client, local_path: Path, blob_prefix: str
) -> list[str]:
    """Upload one file, or every .parquet file in a directory, to GCS. Returns the GCS URIs."""
    bucket = storage_client.bucket(BUCKET_NAME)
    uris = []

    if local_path.is_dir():
        files = sorted(local_path.glob("*.parquet"))
    else:
        files = [local_path]

    for f in files:
        blob_name = blob_prefix + f.name if blob_prefix.endswith("/") else blob_prefix
        blob = bucket.blob(blob_name)
        print(f"  uploading {f} -> gs://{BUCKET_NAME}/{blob_name}")
        blob.upload_from_filename(str(f))
        uris.append(f"gs://{BUCKET_NAME}/{blob_name}")

    return uris


def load_to_bq(bq_client: bigquery.Client, gcs_uris: list[str], table_name: str):
    """Load one or more GCS Parquet files into a single BigQuery table."""
    table_ref = f"{PROJECT_ID}.{DATASET}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        # Parquet carries its own schema -- BigQuery infers it directly,
        # no manual schema definition needed.
    )

    print(f"  loading {len(gcs_uris)} file(s) into {table_ref}")
    load_job = bq_client.load_table_from_uri(gcs_uris, table_ref, job_config=job_config)
    load_job.result()  # blocks until the load finishes

    table = bq_client.get_table(table_ref)
    print(
        f"  done: {table.num_rows:,} rows, {len(table.schema)} columns in {table_ref}"
    )


def run():
    storage_client = storage.Client(project=PROJECT_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)

    for local_path, blob_prefix, table_name in FILES_TO_LOAD:
        if not local_path.exists():
            print(f"SKIP: {local_path} not found")
            continue

        print(f"\n{table_name}:")
        uris = upload_to_gcs(storage_client, local_path, blob_prefix)
        load_to_bq(bq_client, uris, table_name)


if __name__ == "__main__":
    run()
