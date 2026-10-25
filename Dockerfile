# Packages the recurring part of the pipeline (yfinance -> BigQuery ->
# dbt), orchestrated by flows/batch_pipeline_flow.py. Does NOT include
# PySpark/Java -- the Fannie Mae Bronze-to-Silver transform is a
# one-off, manually-triggered job, not part of this scheduled flow.

FROM python:3.12-slim

# Official, documented way to get the uv binary into an image without
# needing pip to install it first.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first (not the whole repo) so Docker can
# cache the `uv sync` layer -- it only re-runs if these two files
# change, not on every code edit.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Now copy the actual code the flow needs.
COPY ingestion/ ingestion/
COPY flows/ flows/
COPY dbt/batch_analytics/ dbt/batch_analytics/
RUN cd dbt/batch_analytics && uv run dbt deps

# Credentials and dbt's profiles.yml are NOT baked into the image --
# both are mounted at `docker run` time (see README). Baking a
# credential into an image means anyone with the image has the
# credential, permanently, even after the key is rotated.

CMD ["uv", "run", "python", "-m", "flows.batch_pipeline_flow"]
