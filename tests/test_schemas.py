from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from ingestion.schemas import IngestionBatch, PriceRecord


def valid_price_record_fields(**overrides):
    base = {
        "ticker": "GC=F",
        "date": date(2026, 10, 8),
        "open": 3983,
        "low": 1284,
        "high": 2305,
        "close": 5437,
        "adj_close": 2324,
        "volume": 297512,
        "ingestion_timestamp": datetime(
            2026, 10, 8, 0, 44, 27, 666729, tzinfo=UTC
        ),
    }
    base.update(overrides)
    return base


def test_valid_price_record_is_accepted():
    rec = PriceRecord(**valid_price_record_fields())
    assert rec.open == 3983
    assert rec.low == 1284
    assert rec.high == 2305
    assert rec.close == 5437
    assert rec.adj_close == 2324


def test_ticker_is_uppercased():
    rec = PriceRecord(**valid_price_record_fields(ticker="  gc=f  "))
    assert rec.ticker == "GC=F"


def test_negative_open_is_rejected():
    with pytest.raises(ValidationError) as exc:
        PriceRecord(**valid_price_record_fields(open=-1.0))
    assert "open" in str(exc.value)


def test_zero_close_is_rejected():
    with pytest.raises(ValidationError):
        PriceRecord(**valid_price_record_fields(close=0.0))


def test_negative_volume_is_rejected():
    with pytest.raises(ValidationError):
        PriceRecord(**valid_price_record_fields(volume=-100))


def test_zero_volume_is_allowed():
    rec = PriceRecord(**valid_price_record_fields(volume=0.0))
    assert rec.volume == 0


def test_high_below_low_is_rejected():
    with pytest.raises(ValidationError):
        PriceRecord(**valid_price_record_fields(low=10, high=5))


def test_high_equal_to_low_is_allowed():
    rec = PriceRecord(**valid_price_record_fields(low=100, high=100))
    assert rec.high == rec.low == 100


def test_missing_required_field_is_rejected():
    fields = valid_price_record_fields()
    del fields["close"]
    with pytest.raises(ValidationError):
        PriceRecord(**fields)


def test_valid_ingestion_batch_is_accepted():
    started = datetime(2026, 10, 8, 0, 44, 27, tzinfo=UTC)
    batch = IngestionBatch(
        pipeline_run_id="run-2026-10-08-001",
        tickers=["GC=F", "NVDA"],
        started_at=started,
        record_count=2,
    )
    assert batch.pipeline_run_id == "run-2026-10-08-001"
    assert batch.tickers == ["GC=F", "NVDA"]
    assert batch.started_at == started
    assert batch.record_count == 2
    assert batch.source_name == "yfinance"  # default applied


def test_negative_record_count_is_rejected():
    with pytest.raises(ValidationError):
        IngestionBatch(
            pipeline_run_id="run-1",
            tickers=["AAPL"],
            started_at=datetime(2024, 1, 2, tzinfo=UTC),
            record_count=-1,
        )
