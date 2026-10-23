import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import yfinance as yf

from ingestion.schemas import IngestionBatch, PriceRecord

DIR = Path("data/raw/yfinance")

tickers = [
    # Commodities & Indices
    "GC=F",  # Gold
    "BTC-USD",  # Bitcoin
    "BZ=F",  # Crude Oil (Brent)
    "^GSPC",  # S&P 500
    # Individual Stocks
    "NVDA",  # NVIDIA
    "JPM",  # JPMorgan Chase
    "INTC",  # Intel Corporation
    "SPCX",  # Space Exploration Technologies (SpaceX)
    # Top Healthcare & Real Estate Stocks
    "LLY",  # Eli Lilly (Top Healthcare by Market Cap) [citation:9][citation:16]
    "PLD",  # Prologis (Top Real Estate by Market Cap) [citation:5]
]


def get_last_dates() -> dict[str, pd.Timestamp]:
    files = list(DIR.glob("*.parquet"))
    if not files:
        return {}

    existing = pd.concat(
        (pd.read_parquet(f, columns=["ticker", "date"]) for f in files),
        ignore_index=True,
    )
    return existing.groupby("ticker")["date"].max().to_dict()


def fetch_ticker(
    ticker: str,
    ingestion_timestamp: datetime,
    since: pd.Timestamp | None,
) -> list[PriceRecord]:

    if since is not None:
        next_day = since + timedelta(days=1)
        data = yf.Ticker(ticker).history(
            start=next_day.strftime("%Y-%m-%d"), interval="1d"
        )
    else:
        data = yf.Ticker(ticker).history(period="1y", interval="1d")

    if data.empty:
        print(f"No record data returned for {ticker}")
        return []

    records = []
    for trade_date, row in data.iterrows():
        try:
            record = PriceRecord(
                ticker=ticker,
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
            print(f"  SKIPPED bad row for {ticker} on {trade_date.date()}: {e}")

    return records


def run() -> IngestionBatch:
    run_id = str(uuid.uuid4())
    started_at = datetime.now(UTC)

    last_dates = get_last_dates()
    print(f"Watermarks found for {len(last_dates)} ticker(s)")

    all_records: list[PriceRecord] = []
    up_to_date_count = 0

    for ticker in tickers:
        since = last_dates.get(ticker)

        if since is not None and (since + timedelta(days=1)) >= started_at.date():
            up_to_date_count += 1
            print(f"  {ticker} already up to date (last={since})")
            continue

        print(f"fetching {ticker} (since={since})")
        all_records.extend(fetch_ticker(ticker, started_at, since))

    attempted = len(tickers) - up_to_date_count

    if not all_records and attempted > 0:
        # Tried to fetch something new and got nothing valid back --
        # that's a real failure.
        raise RuntimeError(
            f"Attempted {attempted} ticker(s) but extracted 0 valid records."
        )

    if not all_records:
        print("All tickers already up to date -- nothing to write.")
        return IngestionBatch(
            pipeline_run_id=run_id,
            source_name="yfinance",
            tickers=tickers,
            started_at=started_at,
            record_count=0,
        )

    df = pd.DataFrame([r.model_dump() for r in all_records])

    DIR.mkdir(parents=True, exist_ok=True)
    out_path = DIR / f"prices_{started_at.strftime('%Y%m%d_%H%M%S')}.parquet"
    df.to_parquet(out_path, index=False)

    batch = IngestionBatch(
        pipeline_run_id=run_id,
        source_name="yfinance",
        tickers=tickers,
        started_at=started_at,
        record_count=len(all_records),
    )

    print(f"Wrote {batch.record_count} rows to {out_path}")
    print(f"Run ID: {batch.pipeline_run_id}")

    return batch


if __name__ == "__main__":
    run()
