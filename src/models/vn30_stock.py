"""Unified VN30Stock domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Represent a standard HTTP JSON response envelope from the upstream API."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    code: str
    message: str
    data: T


class VN30Record(BaseModel):
    """Represent the VN30Stock domain record parsed from the API."""

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

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_epoch_millis(cls, value: Any) -> Any:
        """Parse epoch millisecond timestamps into timezone-aware datetimes."""

        if isinstance(value, datetime):
            return value
        return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)

    @model_validator(mode="after")
    def populate_market_cap(self) -> "VN30Record":
        """Derive market cap from reference price and stock volume."""

        if self.price is not None and self.volume is not None:
            self.market_cap = self.price * self.volume
        return self


class VN30ApiResponse(ApiResponse[list[VN30Record]]):
    """Represent the VN30 API response envelope with typed quote records."""


class VN30Row(BaseModel):
    """Represent a persisted `vn30_stock` DAO row."""

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


class FetchPopulationResult(BaseModel):
    """Represent the result of a VN30 fetch-and-populate operation."""

    model_config = ConfigDict(frozen=True)

    loaded_count: int
    stored_count: int
    source_url: str
    success: bool
    message: str
    quality_passed: bool | None = None
    quality_report_path: Path | None = None


class PopulationResponse(BaseModel):
    """Represent the controller response for VN30 database population."""

    model_config = ConfigDict(frozen=True)

    source_url: str
    database_path: Path
    loaded_count: int
    stored_count: int
    success: bool
    message: str
    quality_passed: bool | None = None
    quality_report_path: Path | None = None


class QualityRuleResult(BaseModel):
    """Represent the result of one quality validation rule."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    passed: bool
    violation_count: int
    anomalous_tickers: list[str] = Field(default_factory=list)


class QualityReportSummary(BaseModel):
    """Represent summary statistics for a quality validation run."""

    model_config = ConfigDict(frozen=True)

    rows_checked: int
    failed_rules: int
    total_violations: int
    quality_passed: bool


class QualityReport(BaseModel):
    """Represent the JSON quality validation report for VN30 data."""

    model_config = ConfigDict(frozen=True)

    generated_at: datetime
    source_url: str
    summary: QualityReportSummary
    rules: list[QualityRuleResult]
