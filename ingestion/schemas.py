import datetime

from pydantic import BaseModel, Field, field_validator


class PriceRecord(BaseModel):
    # ---business data----
    ticker: str = Field(..., min_length=1, description="Security identifier, e.g. AAPL")
    date: datetime.date = Field(..., description="Trading date")
    open: float = Field(..., gt=0, description="Opening price")
    low: float = Field(..., gt=0, description="Lowest price")
    high: float = Field(..., gt=0, description="Highest price")
    close: float = Field(..., gt=0, description="Closing price")
    adj_close: float = Field(..., gt=0, description="Adjusted closing price")
    volume: int = Field(..., ge=0, description="Trading volume")

    # --- ingestion data----
    ingestion_timestamp: datetime.datetime = Field(
        ..., description="Pipeline capture timestamp"
    )
    source: str = Field(default="yfinance", description="Source name")

    @field_validator("high")
    @classmethod
    def high_is_highest(cls, v, info):
        low = info.data.get("low")
        if low is not None and v < low:
            raise ValueError("high must be >= low")
        return v

    @field_validator("ticker")
    @classmethod
    def ticker_upper(cls, v: str) -> str:
        return v.strip().upper()


class IngestionBatch(BaseModel):
    pipeline_run_id: str = Field(..., description="Primary ID for this run")
    source_name: str = Field(default="yfinance")
    tickers: list[str]
    started_at: datetime.datetime
    record_count: int = Field(..., ge=0)
