# Batch Data Platform

Production-style batch pipeline integrating Fannie Mae loan performance data and yfinance market data.

Stack: Python, PySpark, dbt, Prefect (orchestration), BigQuery, AWS, Terraform, Docker, GitHub Actions.

## 

## Status

* \[ ] Phase 1: Foundation (repo, yfinance ingestion, schemas, raw storage)

## 

## Layout

* `ingestion/` source extractors (yfinance, Fannie Mae)
* `prefect/` Prefect flows and deployments
* `pyspark/` large-scale transforms (Bronze to Silver)
* `dbt/` warehouse models (staging, intermediate, marts)
* `sql/` ad hoc and validation SQL
* `tests/` unit, data, and integration tests
* `terraform/` infrastructure as code
* `docker/` container definitions
* `docs/adr/` architecture decision records
* `data/` local data (git-ignored)


### No separate Silver layer for yfinance
Unlike Fannie Mae, the yfinance pipeline has no Bronze-to-Silver step.
Row-level validation (price > 0, high >= low, volume >= 0, required
fields present) already happens at ingestion time via the `PriceRecord`
pydantic schema, before any row reaches Bronze storage. Adding a
separate Silver pass would only be re-validating data that's already
been validated once -- it wouldn't catch anything new, since nothing
invalid is written to Bronze in the first place.

This is a deliberate difference from Fannie Mae, not an oversight:
Fannie Mae's raw files are unvalidated government/GSE data, so
validation has to happen as a distinct post-ingestion step working
against already-written Bronze data. yfinance's validation is small
and cheap enough to run inline during ingestion instead.

## 

## Setup

TBD

