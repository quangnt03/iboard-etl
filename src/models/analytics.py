"""Pydantic models for analytics and reporting.

Keyword arguments:
None."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict


class VolatilityRow(BaseModel):
    """Represents a volatility analytics row.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    open_price: float | None = None
    high_price: float | None = None
    low_price: float | None = None
    intraday_volatility: float | None = None


class VolumeRow(BaseModel):
    """Represents a volume analytics row.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    today_volume: float | None = None
    avg_5d_volume: float | None = None
    volume_ratio: float | None = None


class VolumeCountRow(BaseModel):
    """Represents daily volume row counts for a ticker.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    day_count: int


class ReportRow(BaseModel):
    """Represents a combined analytics row for reporting.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    ticker: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    intraday_volatility: float | None = None
    today_volume: float | None = None
    avg_5d_volume: float | None = None
    volume_ratio: float | None = None


class ReportContext(BaseModel):
    """Context payload passed into the report template.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    title: str
    subtitle: str
    generated_at: str
    source: str
    rows: list[ReportRow]
    output_path: Path
    metadata: dict[str, Any] | None = None


class ReportResult(BaseModel):
    """Result metadata for a generated report.

Keyword arguments:
None."""

    model_config = ConfigDict(from_attributes=True)

    output_path: Path
    row_count: int
