"""
One-off historical backfill for ^GSPC (S&P 500) only, back to 2007 --
needed so fct_market_vs_delinquency has enough market history to
actually overlap with the 2008Q1 loan vintage. Other 9 tickers are
untouched; they stay on the normal trailing-1y incremental schedule in
yfinance_ext.py, since they aren't part of this specific hypothesis test.

This reuses the same PriceRecord schema and writes into the SAME
data/raw/yfinance/ folder as the regular extractor, so the existing
get_last_dates() watermark logic in yfinance_ext.py picks this up
automatically on future incremental runs -- no special-casing needed
there.

Usage:
    uv run python -m ingestion.yfinance_backfill_gspc
"""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

from ingestion.schemas import PriceRecord

RAW_DIR = Path("data/raw/yfinance")
TICKER = "^GSPC"
START_DATE = "2007-01-01"


def run():
    ingestion_timestamp = datetime.now(timezone.utc)

    print(f"Backfilling {TICKER} from {START_DATE}...")
    data = yf.Ticker(TICKER).history(start=START_DATE, interval="1d")

    if data.empty:
        raise RuntimeError(f"No data returned for {TICKER} -- check ticker/start date.")

    records = []
    for trade_date, row in data.iterrows():
        try:
            record = PriceRecord(
                ticker=TICKER,
                date=trade_date.date(),
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                adj_close=row["Close"],
                volume=int(row["Volume"]),
                ingestion_timestamp=ingestion_timestamp,
            )
            records.append(record)
        except Exception as e:
            print(f"  SKIPPED bad row for {TICKER} on {trade_date.date()}: {e}")

    if not records:
        raise RuntimeError("No valid records after validation -- nothing written.")

    df = pd.DataFrame([r.model_dump() for r in records])

    # BigQuery's Parquet loader can reject nanosecond-precision
    # timestamps (pandas' internal default) even for ordinary,
    # in-range values -- downcast explicitly to microseconds, which
    # BigQuery's TIMESTAMP type natively expects. BigQuery's TIMESTAMP
    # is always UTC internally (no separate tz concept), so dropping
    # the explicit tz marker here loses no information -- it's already
    # UTC from datetime.now(timezone.utc) in PriceRecord.
    df["ingestion_timestamp"] = (
        df["ingestion_timestamp"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .astype("datetime64[us]")
    )

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = (
        RAW_DIR
        / f"gspc_backfill_{ingestion_timestamp.strftime('%Y%m%d_%H%M%S')}.parquet"
    )
    df.to_parquet(out_path, index=False)

    print(
        f"Wrote {len(records):,} rows ({df['date'].min()} to {df['date'].max()}) to {out_path}"
    )


if __name__ == "__main__":
    run()
