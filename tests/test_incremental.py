"""
Tests for the incremental logic in ingestion/yfinance_ext.py.

These don't hit the real yfinance API -- they use pytest's monkeypatch to
replace yf.Ticker with a fake, so the tests are fast, deterministic, and
can't fail because of market hours or network issues. The goal is to catch
exactly the kind of bug we just fixed by hand: run() calling fetch_ticker
for a ticker that should have been skipped.
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from ingestion import yfinance_ext


class FakeTicker:
    calls = []  # class-level, so tests can inspect what was requested
    # Set this per-test to control whether history() returns a row or
    # stays empty. Default: one valid row, so run() can succeed.
    return_empty = False

    def __init__(self, ticker):
        self.ticker = ticker

    def history(self, **kwargs):
        FakeTicker.calls.append((self.ticker, kwargs))
        if FakeTicker.return_empty:
            return pd.DataFrame()

        # One realistic, valid row -- enough for fetch_ticker to build a
        # PriceRecord without hitting the real API.
        index = pd.DatetimeIndex([pd.Timestamp.now(tz=timezone.utc)])
        return pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Close": [102.0],
                "Volume": [1_000_000],
            },
            index=index,
        )


@pytest.fixture(autouse=True)
def reset_fake_ticker_calls():
    """Clear recorded calls between tests so they don't leak into each other."""
    FakeTicker.calls = []
    yield


@pytest.fixture
def fake_raw_dir(tmp_path, monkeypatch):
    """
    Point yfinance_ext.DIR at a temporary folder instead of the real
    data/raw/yfinance/, so tests never touch real data.
    """
    fake_dir = tmp_path / "yfinance"
    fake_dir.mkdir()
    monkeypatch.setattr(yfinance_ext, "DIR", fake_dir)
    return fake_dir


def write_watermark_file(fake_raw_dir: Path, ticker: str, last_date: date):
    """
    Write a tiny fixture Parquet file so get_last_dates() finds this
    ticker already captured up to `last_date`.
    """
    df = pd.DataFrame({"ticker": [ticker], "date": [last_date]})
    out_path = (
        fake_raw_dir / f"watermark_{ticker.replace('=', '_').replace('^', '')}.parquet"
    )
    df.to_parquet(out_path, index=False)


def test_up_to_date_ticker_is_not_fetched(fake_raw_dir, monkeypatch):
    today = datetime.now(timezone.utc).date()
    write_watermark_file(fake_raw_dir, "NVDA", today)

    monkeypatch.setattr(yfinance_ext.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(yfinance_ext, "tickers", ["NVDA"])

    batch = yfinance_ext.run()

    assert FakeTicker.calls == []  # no API call was made
    assert batch.record_count == 0


def test_stale_ticker_is_fetched_with_correct_start_date(fake_raw_dir, monkeypatch):
    last_date = datetime.now(timezone.utc).date() - timedelta(days=5)
    write_watermark_file(fake_raw_dir, "NVDA", last_date)

    monkeypatch.setattr(yfinance_ext.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(yfinance_ext, "tickers", ["NVDA"])

    yfinance_ext.run()

    assert len(FakeTicker.calls) == 1
    ticker, kwargs = FakeTicker.calls[0]
    assert ticker == "NVDA"
    expected_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    assert kwargs["start"] == expected_start


def test_new_ticker_triggers_full_year_pull(fake_raw_dir, monkeypatch):
    # No watermark file written -- get_last_dates() will find nothing.
    monkeypatch.setattr(yfinance_ext.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(yfinance_ext, "tickers", ["NVDA"])

    yfinance_ext.run()

    assert len(FakeTicker.calls) == 1
    ticker, kwargs = FakeTicker.calls[0]
    assert ticker == "NVDA"
    assert kwargs.get("period") == "1y"
    assert "start" not in kwargs


def test_all_tickers_up_to_date_does_not_raise(fake_raw_dir, monkeypatch):
    today = datetime.now(timezone.utc).date()
    write_watermark_file(fake_raw_dir, "NVDA", today)
    write_watermark_file(fake_raw_dir, "JPM", today)

    monkeypatch.setattr(yfinance_ext.yf, "Ticker", FakeTicker)
    monkeypatch.setattr(yfinance_ext, "tickers", ["NVDA", "JPM"])

    batch = yfinance_ext.run()  # should not raise

    assert FakeTicker.calls == []
    assert batch.record_count == 0
