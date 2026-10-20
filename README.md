# Batch Data Platform

A batch data engineering pipeline integrating Fannie Mae Single-Family Loan Performance data and yfinance market data, built to apply and demonstrate core data engineering practices: ingestion, validation, distributed transformation, infrastructure as code, and analytics engineering.

**Stack:** Python, PySpark, dbt, Prefect (planned orchestration), BigQuery, Terraform, Docker, uv.

## Status

- [x] Phase 1: Foundation (repo, ingestion, schemas, raw storage)
- [x] Phase 2: Core processing (Bronze -> Silver transforms)
- [x] Phase 7 (partial): Cloud infrastructure via Terraform
- [x] dbt staging + mart models, first analytical result
- [ ] Orchestration (Prefect)
- [ ] CI/CD
- [ ] Portfolio showcase page

## Layout

```
batch-data-platform/
├── ingestion/        yfinance + Fannie Mae extractors, schemas, BigQuery loader
├── spark_jobs/        PySpark Bronze -> Silver transform (Fannie Mae)
├── dbt/batch_analytics/   dbt project: staging + mart models
├── terraform/        GCP infrastructure (project, BigQuery, GCS, IAM)
├── tests/             pytest suite (schemas, incremental logic, data quality)
├── data/              local Bronze/Silver Parquet (git-ignored)
└── docs/adr/          architecture decision records
```

## Data Sources

- **yfinance**: daily price data for 10 tickers (equities, an index, gold, crude oil, Bitcoin), pulled via the `yfinance` Python library.
- **Fannie Mae Single-Family Loan Performance**: loan-level monthly performance data from Fannie Mae's Data Dynamics platform. Two acquisition quarters loaded: **2008Q1** (crisis vintage, 22.4M rows, 380,832 loans) and **2024Q1** (recent vintage, 4.4M rows), for a deliberate crisis-vs-recent contrast.

## Design Decisions

### Why these two datasets?
Fannie Mae loan performance data and yfinance market data aren't linked by a shared key -- they're brought together at the analytics layer as two independently modeled sources, not joined on a common ID.

The business connection between them is indirect, not causal. Stock markets and loan performance both respond to interest rates, broader economic conditions, and (for market prices specifically) investor sentiment -- but the effect of market movements on loan performance is small relative to direct drivers like borrower income, employment, and home prices. This project treats that relationship as a hypothesis worth testing analytically, and reports results honestly even where the result is inconclusive (see **Findings** below).

### T-1 (yesterday) processing for market data
The yfinance pipeline intentionally excludes the current trading day. Prices aren't final until a market closes, so requesting "today" returns incomplete or null data depending on the exchange and asset class. Rather than trying to account for exact market-close times per exchange, the pipeline treats each day's data as available starting the *next* run -- a standard T-1 pattern in financial data engineering, not a workaround for a scripting bug.

### No separate Silver layer for yfinance
Unlike Fannie Mae, the yfinance pipeline has no Bronze-to-Silver step. Row-level validation (price > 0, high >= low, volume >= 0, required fields present) already happens at ingestion time via the `PriceRecord` pydantic schema, before any row reaches Bronze storage. Fannie Mae's raw files are unvalidated government/GSE data, so validation has to happen as a distinct post-ingestion step working against already-written Bronze data; yfinance's validation is small and cheap enough to run inline during ingestion instead.

### Why pandas for raw ingestion, PySpark for transformation
Both sources' raw/Bronze ingestion uses pandas, not PySpark -- the extraction itself is I/O-bound (download, parse, write), not compute-heavy, and Fannie Mae's 22M+ row files are handled safely via chunked reads (200k rows/chunk) written incrementally to Parquet via pyarrow's `ParquetWriter`, avoiding out-of-memory errors without needing distributed compute. PySpark is reserved for the Fannie Mae Bronze-to-Silver transform, where the actual work -- casting 73 typed columns and running validity checks across 26.8M rows -- genuinely benefits from distributed, vectorized execution.

Row-level validation in the Silver transform uses PySpark's native column expressions (`F.when`/`F.col`), not a pydantic model per row. Pydantic validates one Python object at a time; wrapping that in a Spark UDF to validate 26.8M rows would force slow, row-by-row serialization between Spark's JVM engine and Python, defeating the purpose of using Spark at all. [Pandera](https://pandera.readthedocs.io) (which has a native Spark backend) is a possible future option for more declarative-style validation without that performance cost.

### Fannie Mae Silver: field scope
Fannie Mae's raw files carry 114 columns (per the CRT Glossary and File Layout), but only 73 are applicable to Single-Family Loan Performance data -- the other 41 are CAS/CIRT-only fields, always blank in this dataset. Those 41 are dropped at the Bronze-to-Silver step. This isn't primarily a storage optimization -- Parquet compresses all-null columns to near-nothing -- it's about reducing future BigQuery query-scan cost (billed per column touched) and unnecessary Spark processing overhead on columns that carry no information.

Of the 73 retained fields, **15 critical fields** (loan ID, reporting period, channel, UPB, interest rates, LTV, DTI, credit score, delinquency status, zero balance code, property state, occupancy status, loan age) have explicit validity checks. Rows that fail a check are **flagged, not dropped** -- a `data_quality_flag` column records the first failed check per row, preserving every row for traceability. Across both quarters, **1,372,501 rows (5.11%)** are flagged. The dbt staging layer excludes flagged rows from downstream analysis by default.

### Infrastructure trade-offs (Terraform)
- **Local Terraform state**, not a remote GCS backend. Acceptable for a personal project; a production setup would use remote state so infrastructure history survives a lost or replaced machine.
- **A static service account key** for dbt's BigQuery connection, rather than Workload Identity Federation. Pragmatic for local development; a production setup would avoid a long-lived credential entirely.
- **Least-privilege IAM**: the dbt service account has exactly `bigquery.dataEditor`, `bigquery.jobUser`, and `storage.objectViewer` on the staging bucket -- not Owner or Editor.

## Findings

### Market conditions vs. loan delinquency (preliminary)
`fct_market_vs_delinquency` tests whether an S&P 500 (`^GSPC`) decline precedes a rise in loan delinquency some months later. Early results (2008Q1 vintage, 2007-2009 window, 6-month lag) show delinquency rising **monotonically every month**, independent of whether the market that month was up or down -- including months where the market rose and delinquency still climbed.

This points to the result being dominated by **loan seasoning** (delinquency naturally rises as a loan pool ages, especially early in its life) rather than a market-timing effect, at least in this early window where 2008Q1 is the only vintage with enough history to analyze. A sharper test would control for loan age directly -- e.g. comparing delinquency at the same loan age across vintages exposed to different market conditions -- rather than comparing by calendar month alone. Noted here as an honest, current limitation rather than a finished conclusion.

## Known Limitations / Cleanup Items

- The BigQuery column `vintages_quarter` (typo) is aliased to `vintage_quarter` in the dbt staging model rather than fixed at the source, to avoid re-running the ~9-minute Spark transform for a cosmetic issue. A clean fix would correct it in `spark_jobs/fannie_mae_bronze_to_silver.py` (already done) and re-run the full Bronze-to-Silver + BigQuery load.
- yfinance's `^GSPC` ticker has extended history (back to 2007) for the market-vs-delinquency analysis; the other 9 tickers remain on the standard trailing-12-month incremental window, since they aren't part of that specific analysis.

## Setup

See `dbt/batch_analytics/` for dbt project setup and `terraform/` for infrastructure provisioning. Local Python environment managed via `uv` (`uv sync`).