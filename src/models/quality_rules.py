"""Quality rules for VN30 data checks.

Keyword arguments:
None."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta, timezone
from typing import Any, Callable, Iterable

from pydantic import BaseModel, ConfigDict, Field

from src.models.vn30_stock import VN30Record

ICT = timezone(timedelta(hours=7))
_SAMPLE_LIMIT = 3


class QualityRuleResult(BaseModel):
    """Represent the result of one quality validation rule.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    rule_name: str
    rule_code: str
    description: str
    logic: str
    status: str
    violation_count: int
    affected_tickers: list[str] = Field(default_factory=list)
    sample_violations: list[dict[str, Any]] = Field(default_factory=list)


class RunMetadata(BaseModel):
    """Represent metadata for a quality validation run.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    source: str
    dataset: str
    generated_at: datetime
    trading_timezone: str
    records_checked: int


class QualityReportSummary(BaseModel):
    """Represent summary statistics for a quality validation run.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    total_rules: int
    passed_rules: int
    failed_rules: int
    overall_status: str


class QualityReport(BaseModel):
    """Represent the JSON quality validation report for VN30 data.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    run_metadata: RunMetadata
    summary: QualityReportSummary
    checks: list[QualityRuleResult]


def _sample_violations(
    violations: Iterable[VN30Record],
    builder: Callable[[VN30Record], dict[str, Any]],
    limit: int = _SAMPLE_LIMIT,
) -> list[dict[str, Any]]:
    """Build sample violation dicts.

Keyword arguments:
violations -- Violating records to sample from.
builder -- Function mapping a record to a sample dict.
limit -- Maximum number of sample rows to emit."""

    # Collect a bounded sample of violation details for reporting.
    samples: list[dict[str, Any]] = []
    for record in violations:
        samples.append(builder(record))
        if len(samples) >= limit:
            break
    return samples


def _affected_tickers(violations: Iterable[VN30Record]) -> list[str]:
    """Collect unique tickers from violating records.

Keyword arguments:
violations -- Violating records."""

    # Extract unique ticker symbols for summary reporting.
    tickers = {record.ticker for record in violations if isinstance(record.ticker, str)}
    return sorted(tickers)


class QualityRule(ABC):
    """Base class for extensible VN30 quality rules.

Keyword arguments:
None."""

    rule_name: str
    rule_code: str
    description: str
    logic: str

    @abstractmethod
    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate the provided records and return a rule result.

Keyword arguments:
self -- The self.
records -- Records to validate."""


class NonNullPriceRule(QualityRule):
    """Ensure every record has a non-null price.

Keyword arguments:
None."""

    rule_name = "No NULL prices"
    rule_code = "no_null_prices"
    description = "Every record must have a non-null price."
    logic = "price IS NOT NULL"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-null prices.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where price is missing.
        violations = [record for record in records if record.price is None]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "price": record.price,
                },
            ),
        )


class ChangePctWithinBoundsRule(QualityRule):
    """Ensure percentage change stays within allowed bounds.

Keyword arguments:
None."""

    rule_name = "Price change within bounds"
    rule_code = "price_change_within_bounds"
    description = "change_pct must be within +/-30%."
    logic = "-30 <= change_pct <= 30"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate change percentage bounds.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where change_pct falls outside the allowed range.
        violations = [
            record
            for record in records
            if record.change_pct is not None and not (-30 <= record.change_pct <= 30)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "change_pct": record.change_pct,
                },
            ),
        )


class PositiveVolumeDuringTradingHoursRule(QualityRule):
    """Ensure positive volume during ICT trading hours.

Keyword arguments:
None."""

    rule_name = "Volume positivity"
    rule_code = "volume_positivity"
    description = "volume must be > 0 during trading hours 09:00 - 15:00 ICT."
    logic = "volume > 0 when local_time between 09:00 and 15:00"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate positive volume during ICT trading hours.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Scan records for zero/negative volume during trading hours.
        violations: list[VN30Record] = []
        for record in records:
            local_time = record.timestamp.astimezone(ICT).time()
            is_trading_hours = time(9, 0) <= local_time <= time(15, 0)
            if is_trading_hours and (record.volume is None or record.volume <= 0):
                violations.append(record)

        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "volume": record.volume,
                },
            ),
        )


class NumericNonNegativeRule(QualityRule):
    """Ensure numeric fields are non-negative.

Keyword arguments:
None."""

    rule_name = "All numeric fields non-negative"
    rule_code = "numeric_fields_non_negative"
    description = "All numeric fields must be non-negative."
    logic = "numeric_fields >= 0"
    numeric_fields = (
        "price",
        "open",
        "close",
        "low",
        "high",
        "avg",
        "volume",
        "market_cap",
    )

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-negative numeric fields.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Accumulate records with any negative numeric field.
        violations: list[VN30Record] = []
        sample_violations: list[dict[str, Any]] = []
        for record in records:
            for field in self.numeric_fields:
                value = getattr(record, field)
                if value is not None and value < 0:
                    violations.append(record)
                    if len(sample_violations) < _SAMPLE_LIMIT:
                        sample_violations.append(
                            {
                                "ticker": record.ticker,
                                "timestamp": record.timestamp,
                                "field": field,
                                "value": value,
                            }
                        )
                    break

        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=sample_violations,
        )


class LowLessThanHighRule(QualityRule):
    """Ensure low price is less than or equal to high price.

Keyword arguments:
None."""

    rule_name = "Low <= High"
    rule_code = "low_lte_high"
    description = "Low price must be less than or equal to high price."
    logic = "low <= high"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate low <= high.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where low exceeds high.
        violations = [
            record
            for record in records
            if record.low is not None and record.high is not None and record.low > record.high
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "low": record.low,
                    "high": record.high,
                },
            ),
        )


class OpenWithinRangeRule(QualityRule):
    """Ensure open price is within the low/high range.

Keyword arguments:
None."""

    rule_name = "Open within range"
    rule_code = "open_within_range"
    description = "Open price must be within [low, high]."
    logic = "low <= open <= high"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate open within [low, high].

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where open is outside the low/high range.
        violations = [
            record
            for record in records
            if record.open is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.open <= record.high)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "open": record.open,
                    "low": record.low,
                    "high": record.high,
                },
            ),
        )


class CloseWithinRangeRule(QualityRule):
    """Ensure close price is within the low/high range.

Keyword arguments:
None."""

    rule_name = "Close within range"
    rule_code = "close_within_range"
    description = "Close price must be within [low, high]."
    logic = "low <= close <= high"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate close within [low, high].

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where close is outside the low/high range.
        violations = [
            record
            for record in records
            if record.close is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.close <= record.high)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "close": record.close,
                    "low": record.low,
                    "high": record.high,
                },
            ),
        )


class PriceWithinRangeRule(QualityRule):
    """Ensure price is within the low/high range.

Keyword arguments:
None."""

    rule_name = "Price within range"
    rule_code = "price_within_range"
    description = "Price must be within [low, high]."
    logic = "low <= price <= high"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate price within [low, high].

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where price is outside the low/high range.
        violations = [
            record
            for record in records
            if record.price is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.price <= record.high)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "price": record.price,
                    "low": record.low,
                    "high": record.high,
                },
            ),
        )


class AvgWithinRangeRule(QualityRule):
    """Ensure average price is within the low/high range.

Keyword arguments:
None."""

    rule_name = "Average within range"
    rule_code = "avg_within_range"
    description = "Average price must be within [low, high]."
    logic = "low <= avg <= high"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate average within [low, high].

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records where avg is outside the low/high range.
        violations = [
            record
            for record in records
            if record.avg is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.avg <= record.high)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "avg": record.avg,
                    "low": record.low,
                    "high": record.high,
                },
            ),
        )


class TickerNotBlankRule(QualityRule):
    """Ensure ticker is not blank.

Keyword arguments:
None."""

    rule_name = "Ticker not blank"
    rule_code = "ticker_not_blank"
    description = "Ticker must be a non-blank string."
    logic = "ticker != ''"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-blank tickers.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records with missing or blank ticker symbols.
        violations = [
            record
            for record in records
            if not isinstance(record.ticker, str) or not record.ticker.strip()
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                },
            ),
        )


class TimestampParseableRule(QualityRule):
    """Ensure timestamp is a datetime instance.

Keyword arguments:
None."""

    rule_name = "Timestamp parseable"
    rule_code = "timestamp_parseable"
    description = "Timestamp must be a datetime instance."
    logic = "timestamp IS datetime"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate timestamp type.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records with non-datetime timestamps.
        violations = [
            record for record in records if not isinstance(record.timestamp, datetime)
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                },
            ),
        )


class VolumeNonNegativeRule(QualityRule):
    """Ensure volume is non-negative.

Keyword arguments:
None."""

    rule_name = "Volume non-negative"
    rule_code = "volume_non_negative"
    description = "Volume must be greater than or equal to 0."
    logic = "volume >= 0"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate volume >= 0.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records with missing or negative volume.
        violations = [
            record
            for record in records
            if record.volume is None or record.volume < 0
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "volume": record.volume,
                },
            ),
        )


class MarketCapNonNegativeRule(QualityRule):
    """Ensure market cap is non-negative.

Keyword arguments:
None."""

    rule_name = "Market cap non-negative"
    rule_code = "market_cap_non_negative"
    description = "Market cap must be greater than or equal to 0."
    logic = "market_cap >= 0"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate market cap >= 0.

Keyword arguments:
self -- The self.
records -- Records to validate."""

        # Flag records with missing or negative market cap.
        violations = [
            record
            for record in records
            if record.market_cap is None or record.market_cap < 0
        ]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "market_cap": record.market_cap,
                },
            ),
        )
