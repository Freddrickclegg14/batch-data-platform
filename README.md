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

## 

## Setup

TBD

