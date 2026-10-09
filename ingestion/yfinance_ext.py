import uuid
from datetime import datetime, timezone
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


def fetch_ticker(ticker: str, ingestion_timestamp: datetime) -> list[PriceRecord]:
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
    started_at = datetime.now(timezone.utc)

    all_records: list[PriceRecord] = []
    for ticker in tickers:
        print(f"fetching {ticker}")
        all_records.extend(fetch_ticker(ticker, started_at))

    if not all_records:
        raise RuntimeError("No valid records extracted from any ticker.")

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
