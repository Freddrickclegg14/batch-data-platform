import subprocess
from pathlib import Path

from prefect import flow, task

DBT_PROJECT_DIR = Path("dbt/batch_analytics")


@task(retries=2, retry_delay_seconds=30, log_prints=True)
def extract_yfinance():
    from ingestion.yfinance_ext import run as yfinance_run

    batch = yfinance_run()
    print(f"yfinance: {batch.record_count} new rows")
    return batch


@task(retries=2, retry_delay_seconds=60, log_prints=True)
def load_to_bigquery():
    from ingestion.load_fannie_mae_incremental import run as load_run

    load_run()


@task(retries=1, log_prints=True)
def run_dbt_build():
    result = subprocess.run(
        ["uv", "run", "dbt", "build", "--profiles-dir", "."],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(f"dbt build failed {result.returncode}")
    return result.stdout


@flow(name="batch-market-data-pipeline", log_prints=True)
def batch_pipeline():
    extract_yfinance()
    load_to_bigquery()
    run_dbt_build()
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    batch_pipeline()
