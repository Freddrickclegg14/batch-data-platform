# Batch Data Platform

A batch data engineering pipeline integrating Fannie Mae Single-Family Loan Performance data and yfinance market data, built to apply and demonstrate core data engineering practices: ingestion, validation, distributed transformation, infrastructure as code, orchestration, and analytics engineering.

**Stack:** Python, PySpark, dbt, Prefect, BigQuery, Terraform, Docker, GitHub Actions, uv.

## Status

- [x] Phase 1: Foundation (repo, ingestion, schemas, raw storage)
- [x] Phase 2: Core processing (Bronze -> Silver transforms)
- [x] Cloud infrastructure (Terraform)
- [x] dbt staging + mart models, tests, docs
- [x] Orchestration (Prefect)
- [x] CI/CD (GitHub Actions)
- [x] Containerization (Docker)
- [ ] Portfolio showcase page

## Layout

```
batch-data-platform/
├── ingestion/          yfinance + Fannie Mae extractors, schemas, BigQuery loaders
├── spark_jobs/         PySpark Bronze -> Silver transform (Fannie Mae)
├── dbt/batch_analytics/    dbt project: staging + mart models, tests, docs
├── flows/               Prefect orchestration
├── terraform/           GCP infrastructure (project, BigQuery, GCS, IAM)
├── tests/                pytest suite (schemas, incremental logic)
├── .github/workflows/    CI (lint, tests, dbt parse)
├── Dockerfile
├── data/                 local Bronze/Silver Parquet (git-ignored)
└── docs/adr/             architecture decision records
```

## Data Sources

- **yfinance**: daily price data for 10 tickers (equities, an index, gold, crude oil, Bitcoin). `^GSPC` extended back to 2007 specifically to support the market-vs-delinquency analysis below; the other 9 stay on a standard trailing-12-month incremental window.
- **Fannie Mae Single-Family Loan Performance**: loan-level monthly performance data from Fannie Mae's Data Dynamics platform. Two acquisition quarters loaded: **2008Q1** (crisis vintage, 22,415,219 rows, 380,832 loans) and **2024Q1** (recent vintage, 4,430,015 rows) -- a deliberate crisis-vs-recent contrast.

## Design Decisions

### Why these two datasets?
Fannie Mae loan performance data and yfinance market data aren't linked by a shared key -- they're brought together at the analytics layer as two independently modeled sources. The business connection between them is indirect, not causal: stock markets and loan performance both respond to interest rates and broader economic conditions, but the effect of market movements on loan performance is small relative to direct drivers like borrower income, employment, and home prices. This project treats that relationship as a hypothesis worth testing analytically, and reports results honestly, including where a naive version of the test turned out to be confounded (see **Findings**).

### T-1 (yesterday) processing for market data
The yfinance pipeline intentionally excludes the current trading day. Prices aren't final until a market closes, so requesting "today" returns incomplete or null data depending on the exchange and asset class. The pipeline treats each day's data as available starting the *next* run -- a standard T-1 pattern in financial data engineering, not a workaround for a scripting bug.

### No separate Silver layer for yfinance
Row-level validation (price > 0, high >= low, volume >= 0, required fields present) already happens at ingestion time via the `PriceRecord` pydantic schema, before any row reaches Bronze storage. Fannie Mae's raw files are unvalidated government/GSE data, so validation has to happen as a distinct post-ingestion step working against already-written Bronze data; yfinance's validation is small and cheap enough to run inline during ingestion instead.

### Why pandas for raw ingestion, PySpark for transformation
Both sources' raw/Bronze ingestion uses pandas -- extraction is I/O-bound, not compute-heavy, and Fannie Mae's 22M+ row files are handled safely via chunked reads (200k rows/chunk) written incrementally via pyarrow's `ParquetWriter`, avoiding out-of-memory errors without needing distributed compute. PySpark is reserved for the Fannie Mae Bronze-to-Silver transform, where casting 73 typed columns and running validity checks across 26.8M rows genuinely benefits from distributed, vectorized execution.

Row-level validation in the Silver transform uses PySpark's native column expressions (`F.when`/`F.col`), not a pydantic model per row -- wrapping pydantic in a Spark UDF would force slow, row-by-row serialization between Spark's JVM engine and Python, defeating the purpose of using Spark at all.

### Fannie Mae Silver: field scope
Fannie Mae's raw files carry 114 columns, but only 73 are applicable to Single-Family Loan Performance -- the other 41 are CAS/CIRT-only fields, always blank in this dataset, and dropped at the Bronze-to-Silver step. This isn't primarily a storage optimization (Parquet compresses all-null columns to near-nothing) -- it reduces future BigQuery query-scan cost (billed per column touched) and unnecessary Spark processing overhead.

Of the 73 retained fields, **15 critical fields** (loan ID, reporting period, channel, UPB, interest rates, LTV, DTI, credit score, delinquency status, zero balance code, property state, occupancy status, loan age) have explicit validity checks, including null-safety on every check after an early version was found to silently miss nulls on 6 of the original 10 checks. Rows that fail a check are **flagged, not dropped** -- a `data_quality_flag` column records the first failed check, preserving every row for traceability. Across both quarters, **1,372,501 rows (5.11%)** are flagged; dbt's staging layer excludes flagged rows from downstream analysis by default. A runtime assertion keeps the hardcoded checks and the `CRITICAL_FIELDS` list from silently drifting apart -- it has already caught a real gap once (5 fields that were listed as critical but never actually had a check implemented).

### Infrastructure trade-offs (Terraform)
- **Local Terraform state**, not a remote GCS backend. Acceptable for a personal project; a production setup would use remote state so infrastructure history survives a lost or replaced machine.
- **A static service account key** for dbt's BigQuery connection, rather than Workload Identity Federation. Pragmatic for local/containerized development; a production setup would avoid a long-lived credential entirely.
- **Least-privilege IAM**, refined through real use (see **Containerization** below) rather than guessed upfront.

### Incremental BigQuery loading
Early iterations reloaded the entire 26.8M-row Fannie Mae table on every run via `WRITE_TRUNCATE` -- correct, but wasteful. `ingestion/load_fannie_mae_incremental.py` replaces this with a staging-table + `MERGE` pattern: new data lands in a temporary table, then only loan-months not already present (keyed on `loan_identifier` + `monthly_reporting_period`) are inserted. Existing rows are never touched, matching how Fannie Mae's actual publishing works -- each release appends new months, it doesn't revise historical ones. Re-running the incremental load against unchanged data produces a measured **0 new rows** (26,845,234 -> 26,845,234), confirmed directly against the live table, not assumed.

yfinance's BigQuery load stays a full reload each run -- its table is small, so a full reload costs nothing meaningful, and the extraction step itself is already incremental.

### Orchestration (Prefect)
`flows/batch_pipeline_flow.py` orchestrates the pipeline's recurring parts: yfinance extraction, incremental BigQuery load, and a dbt build (run + test in one pass, so a failure stops the flow before later steps run against bad data). Each step is a retryable task. The Fannie Mae Bronze-to-Silver transform is intentionally **not** part of this flow -- it's a one-off per acquisition quarter, run manually when a new quarter is added, not a recurring job.

### CI/CD
`.github/workflows/ci.yml` runs two jobs on every push: **lint + pytest** (ruff, the schema/incremental test suite -- no cloud dependency), and **dbt parse** (validates every model compiles and every `ref()`/`source()` resolves, using a dummy `profiles.yml` that never actually connects to BigQuery). Full `dbt build` deliberately stays in Prefect, not CI, to avoid needing a live GCP credential as a GitHub secret and avoid BigQuery cost on every commit.

### Containerization (Docker)
`Dockerfile` packages the recurring flow into a reproducible image -- no PySpark/Java, since the one-off Spark transform stays outside it. Credentials and `profiles.yml` are mounted at `docker run` time, never baked into the image.

Running the pipeline under its real, narrowly-scoped `dbt-runner` service account for the first time (rather than a personal `gcloud` login, which had quietly masked gaps the whole time locally) surfaced three genuine issues, each a real finding rather than a Docker-specific bug:
1. **Missing GCS write permission** -- the service account only ever had `storage.objectViewer`, since nothing had needed to *write* to the bucket under personal credentials before.
2. **Missing delete-on-overwrite permission** -- GCS implements overwriting an existing object as delete-then-recreate internally, so `objectCreator` alone wasn't enough once a run re-uploaded an existing filename. Resolved by consolidating to `roles/storage.objectAdmin`, scoped to just the one staging bucket.
3. **A hardcoded Windows path** in `profiles.yml`'s `keyfile`, left over from local `dbt init`, meaningless inside Linux. Fixed with `env_var('DBT_BQ_KEYFILE', <windows-path-default>)`, so one file works unmodified in both environments.

This is the concrete argument for testing against production-equivalent, least-privilege credentials rather than a personal account: the gaps exist either way, but only one setup finds them before they matter.

## Findings

### Market conditions vs. loan delinquency (calendar-month version -- a confounded result)
`fct_market_vs_delinquency` tests whether an S&P 500 (`^GSPC`) decline precedes a rise in loan delinquency some months later. The calendar-month version (2008Q1 vintage, 2007-2009 window, 6-month lag) showed delinquency rising **monotonically every month**, independent of whether the market that month was up or down. This pointed to the result being dominated by **loan seasoning** rather than market timing, since 2008Q1 was the only vintage with history that early -- an honest limitation, not a finished conclusion.

### Loan-age-controlled delinquency (follow-up, sharper result)
`fct_delinquency_by_loan_age` compares delinquency rate by months-since-origination instead of calendar month, directly controlling for seasoning. **Result: 2008Q1 shows a consistently higher delinquency rate than 2024Q1 at every matching loan age from month 3 onward, and the gap widens with age rather than staying constant** -- roughly **1.4x at age 3, 2.7x at age 10, and 7.2x at age 20**.

This is a materially stronger, more defensible result than the calendar-month version. Holding loan age constant rules out seasoning as the sole explanation -- a pure seasoning effect would produce similar age-aligned curves across vintages, not a widening gap. The accelerating divergence is consistent with 2008Q1 loans experiencing genuinely worse conditions (the 2008-2009 recession) as they aged, rather than just an initial quality difference at origination.

This doesn't replace the calendar-month test as a market-*timing* result (whether a specific market move precedes a specific delinquency change a few months later, which still has a thin data-overlap limitation) -- it answers a related but distinct and more tractable question: whether the crisis vintage is structurally worse than a normal one, holding loan age fixed. That question, it answers clearly.

## Known Limitations / Cleanup Items

- The BigQuery column `vintages_quarter` (typo) is aliased to `vintage_quarter` in the dbt staging model rather than fixed at the source, to avoid re-running the ~9-minute Spark transform for a cosmetic issue.
- The market-timing version of the delinquency analysis (`fct_market_vs_delinquency`) still has limited date overlap between market and loan data outside the 2007-2009 window and hasn't been re-tested with a longer market history for 2024Q1.

## Setup

See `dbt/batch_analytics/` for the dbt project and `terraform/` for infrastructure provisioning. Local Python environment managed via `uv` (`uv sync`). Run the recurring pipeline locally with `uv run python -m flows.batch_pipeline_flow`, or containerized via `docker build -t batch-pipeline .` and `docker run` (see `Dockerfile` for required mounted credentials).