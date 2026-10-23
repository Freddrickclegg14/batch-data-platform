"""
Incremental load for Fannie Mae loan performance data: loads the new
Bronze/Silver file into a TEMP staging table, then MERGEs only rows
that aren't already present (by loan_identifier + monthly_reporting_period)
into the real table. Avoids re-loading 26.8M+ unchanged rows every time
a new monthly update is published -- matches how Fannie Mae's actual
publishing cadence works (each release appends new months, doesn't
replace old ones).

Usage:
    uv run python -m ingestion.load_fannie_mae_incremental
"""

from pathlib import Path

from google.cloud import bigquery, storage

from ingestion.load_to_bigquery import DATASET, PROJECT_ID, upload_to_gcs

TARGET_TABLE = "fannie_mae_loan_performance"
STAGING_TABLE = "_staging_fannie_mae_incoming"  # temp table, dropped after merge

SILVER_PATH = Path("data/silver/fannie_mae/loan_performance.parquet")
GCS_PREFIX = "fannie_mae/loan_performance/"

MERGE_KEY_COLUMNS = ["loan_identifier", "monthly_reporting_period"]


def run():
    storage_client = storage.Client(project=PROJECT_ID)
    bq_client = bigquery.Client(project=PROJECT_ID)

    if not SILVER_PATH.exists():
        raise FileNotFoundError(f"{SILVER_PATH} not found")

    print("Uploading new/updated Fannie Mae file to GCS...")
    uris = upload_to_gcs(storage_client, SILVER_PATH, GCS_PREFIX)

    staging_ref = f"{PROJECT_ID}.{DATASET}.{STAGING_TABLE}"
    target_ref = f"{PROJECT_ID}.{DATASET}.{TARGET_TABLE}"

    print(f"Loading into temp staging table {staging_ref}...")
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    load_job = bq_client.load_table_from_uri(uris, staging_ref, job_config=job_config)
    load_job.result()
    staging_table = bq_client.get_table(staging_ref)
    print(f"  staged {staging_table.num_rows:,} rows")

    try:
        bq_client.get_table(target_ref)
        target_exists = True
    except Exception:
        target_exists = False

    if not target_exists:
        print(f"{target_ref} doesn't exist yet -- creating it from staging.")
        bq_client.copy_table(staging_ref, target_ref).result()
    else:
        on_clause = " AND ".join(f"target.{c} = source.{c}" for c in MERGE_KEY_COLUMNS)
        # Get the staging table's columns so the MERGE inserts every
        # field, not just the key columns.
        all_columns = [f.name for f in staging_table.schema]
        insert_columns = ", ".join(all_columns)
        insert_values = ", ".join(f"source.{c}" for c in all_columns)

        merge_sql = f"""
        MERGE `{target_ref}` AS target
        USING `{staging_ref}` AS source
        ON {on_clause}
        WHEN NOT MATCHED THEN
          INSERT ({insert_columns})
          VALUES ({insert_values})
        """

        print("Running MERGE (inserting only new loan-months)...")
        before = bq_client.get_table(target_ref).num_rows
        merge_job = bq_client.query(merge_sql)
        merge_job.result()
        after = bq_client.get_table(target_ref).num_rows
        print(f"  target table: {before:,} -> {after:,} rows ({after - before:,} new)")

    bq_client.delete_table(staging_ref, not_found_ok=True)
    print("Dropped temp staging table.")


if __name__ == "__main__":
    run()
