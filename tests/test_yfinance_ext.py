from datetime import date
from pathlib import Path

import pandas as pd
import pytest


# The output directory the pipeline writes into.
OUTPUT_DIR = Path("data/raw/yfinance")

REQUIRED_COLUMNS = [
    "ticker",
    "date",
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
    "ingestion_timestamp",
    "source",
]


@pytest.fixture(scope="session")
def sample_df() -> pd.DataFrame:
    parquet_files = sorted(OUTPUT_DIR.glob("*.parquet"))
    if not parquet_files:
        pytest.skip(f"no parquet files found in {OUTPUT_DIR} -- run the pipeline first")

    latest = parquet_files[-1]
    return pd.read_parquet(latest)


def test_expected_columns_present(sample_df):
    missing = set(REQUIRED_COLUMNS) - set(sample_df.columns)
    assert not missing, f"missing columns: {missing}"


def test_no_unexpected_columns(sample_df):
    """Catches schema drift -- a new upstream column leaking into the output
    without anyone updating REQUIRED_COLUMNS."""
    extra = set(sample_df.columns) - set(REQUIRED_COLUMNS)
    assert not extra, f"unexpected columns: {extra}"


def test_no_nulls_in_required_columns(sample_df):
    null_counts = sample_df[REQUIRED_COLUMNS].isna().sum()
    nulls = null_counts[null_counts > 0]
    assert nulls.empty, f"nulls found in: {nulls.to_dict()}"


def test_no_duplicate_ticker_date_pairs(sample_df):
    """Each (ticker, date) combination should appear at most once."""
    dupes = sample_df.duplicated(subset=["ticker", "date"], keep=False)
    assert not dupes.any(), (
        f"{dupes.sum()} duplicate (ticker, date) rows found:\n"
        f"{sample_df.loc[dupes, ['ticker', 'date']].head()}"
    )


def test_all_prices_positive(sample_df):
    price_cols = ["open", "high", "low", "close", "adj_close"]
    for col in price_cols:
        bad = sample_df[col] <= 0
        assert not bad.any(), f"{bad.sum()} non-positive values in '{col}'"


def test_high_gte_low_in_output(sample_df):
    bad = sample_df["high"] < sample_df["low"]
    assert not bad.any(), (
        f"{bad.sum()} rows with high < low:\n"
        f"{sample_df.loc[bad, ['ticker', 'date', 'high', 'low']].head()}"
    )


def test_volume_non_negative(sample_df):
    bad = sample_df["volume"] < 0
    assert not bad.any(), f"{bad.sum()} rows with negative volume"


def test_dates_within_expected_range(sample_df):
    """Dates should fall within a plausible window -- no stray future
    or ancient dates. Adjust the bounds to your requested period."""
    dates = pd.to_datetime(sample_df["date"])

    assert dates.min() >= pd.Timestamp("2020-01-01"), f"date too old: {dates.min()}"
    # Allow up to tomorrow so a same-day run in a positive timezone still passes.
    upper = pd.Timestamp(date.today()) + pd.Timedelta(days=1)
    assert dates.max() <= upper, f"date in the future: {dates.max()}"


def test_ticker_symbols_are_uppercase(sample_df):
    """The schema's ticker_upper validator should have normalized these."""
    bad = sample_df["ticker"] != sample_df["ticker"].str.upper()
    assert not bad.any(), (
        f"{bad.sum()} non-uppercase tickers: "
        f"{sample_df.loc[bad, 'ticker'].unique()[:5].tolist()}"
    )


def test_source_is_expected_value(sample_df):
    """Every row should carry the same, expected source label."""
    sources = set(sample_df["source"].unique())
    assert sources == {"yfinance"}, f"unexpected sources: {sources}"
