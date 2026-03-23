"""Unified VN30Stock domain models.

Keyword arguments:
None."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Represent a standard HTTP JSON response envelope from the upstream API.

Keyword arguments:
None."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    code: str
    message: str
    data: T


class VN30Record(BaseModel):
    """Represent the VN30Stock domain record parsed from the API.

Keyword arguments:
None."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    timestamp: datetime = Field(alias="expectedLastUpdate")
    ticker: str = Field(alias="stockSymbol")
    price: float | None = Field(default=None, alias="refPrice")
    change: float | None = Field(default=None, alias="priceChange")
    change_pct: float | None = Field(default=None, alias="priceChangePercent")
    open: float | None = Field(default=None, alias="openPrice")
    close: float | None = Field(default=None, alias="matchedPrice")
    low: float | None = Field(default=None, alias="lowest")
    high: float | None = Field(default=None, alias="highest")
    avg: float | None = Field(default=None, alias="avgPrice")
    volume: int | None = Field(default=None, alias="stockVol")
    market_cap: float | None = None
    updated_at: datetime | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_epoch_millis(cls, value: Any) -> Any:
        """Parse epoch millisecond timestamps into timezone-aware datetimes.

Keyword arguments:
cls -- The cls.
value -- The value."""

        # Accept datetime instances as-is.
        if isinstance(value, datetime):
            return value
        # Convert epoch milliseconds to a UTC datetime.
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)

    @model_validator(mode="after")
    def populate_market_cap(self) -> "VN30Record":
        """Derive market cap from reference price and stock volume.

Keyword arguments:
self -- The self."""

        # Populate market cap only when both price and volume are present.
        if self.price is not None and self.volume is not None:
            self.market_cap = self.price * self.volume
        return self


class VN30ApiResponse(ApiResponse[list[VN30Record]]):
    """Represent the VN30 API response envelope with typed quote records.

Keyword arguments:
None."""


class VN30Row(BaseModel):
    """Represent a persisted `vn30_stock` DAO row.

Keyword arguments:
None."""

    timestamp: datetime
    ticker: str
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    open: float | None = None
    close: float | None = None
    low: float | None = None
    high: float | None = None
    avg: float | None = None
    volume: int | None = None
    market_cap: float | None = None
    updated_at: datetime | None = None


class FetchPopulationResult(BaseModel):
    """Represent the result of a VN30 fetch-and-populate operation.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    loaded_count: int
    stored_count: int
    source_url: str
    success: bool
    message: str
    quality_passed: bool | None = None
    quality_report_path: Path | None = None


class PopulationResponse(BaseModel):
    """Represent the controller response for VN30 database population.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    source_url: str
    database_path: Path
    loaded_count: int
    stored_count: int
    success: bool
    message: str
    quality_passed: bool | None = None
    quality_report_path: Path | None = None
