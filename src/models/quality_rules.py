from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta, timezone

from src.models.vn30_stock import QualityReport, QualityReportSummary, QualityRuleResult, VN30Record

ICT = timezone(timedelta(hours=7))

class QualityRule(ABC):
    """Base class for extensible VN30 quality rules."""

    name: str
    description: str

    @abstractmethod
    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate the provided records and return a rule result."""


class NonNullPriceRule(QualityRule):
    """Ensure every record has a non-null price."""

    name = "non_null_price"
    description = "Every record must have a non-null price."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-null prices."""

        violations = [record for record in records if record.price is None]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class ChangePctWithinBoundsRule(QualityRule):
    """Ensure percentage change stays within allowed bounds."""

    name = "change_pct_within_bounds"
    description = "change_pct must stay within ±30%."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate change percentage bounds."""

        violations = [
            record
            for record in records
            if record.change_pct is not None and not (-30 <= record.change_pct <= 30)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
            anomalous_tickers=sorted({record.ticker for record in violations}),
        )


class PositiveVolumeDuringTradingHoursRule(QualityRule):
    """Ensure positive volume during ICT trading hours."""

    name = "positive_volume_during_trading_hours"
    description = "volume must be > 0 during trading hours 09:00 - 15:00 ICT."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate positive volume during ICT trading hours."""

        violations = []
        for record in records:
            local_time = record.timestamp.astimezone(ICT).time()
            is_trading_hours = time(9, 0) <= local_time <= time(15, 0)
            if is_trading_hours and (record.volume is None or record.volume <= 0):
                violations.append(record)

        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class NumericNonNegativeRule(QualityRule):
    """Ensure numeric fields are non-negative."""

    name = "numeric_fields_non_negative"
    description = "All numeric fields must be non-negative."
    numeric_fields = (
        "price",
        "change",
        "change_pct",
        "open",
        "close",
        "low",
        "high",
        "avg",
        "volume",
        "market_cap",
    )

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-negative numeric fields."""

        violations = []
        for record in records:
            for field in self.numeric_fields:
                value = getattr(record, field)
                if value is not None and value < 0:
                    violations.append(record)
                    break

        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class LowLessThanHighRule(QualityRule):
    """Ensure low price is less than or equal to high price."""

    name = "low_lte_high"
    description = "Low price must be less than or equal to high price."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate low <= high."""

        violations = [
            record
            for record in records
            if record.low is not None and record.high is not None and record.low > record.high
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class OpenWithinRangeRule(QualityRule):
    """Ensure open price is within the low/high range."""

    name = "open_within_range"
    description = "Open price must be within [low, high]."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate open within [low, high]."""

        violations = [
            record
            for record in records
            if record.open is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.open <= record.high)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class CloseWithinRangeRule(QualityRule):
    """Ensure close price is within the low/high range."""

    name = "close_within_range"
    description = "Close price must be within [low, high]."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate close within [low, high]."""

        violations = [
            record
            for record in records
            if record.close is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.close <= record.high)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class PriceWithinRangeRule(QualityRule):
    """Ensure price is within the low/high range."""

    name = "price_within_range"
    description = "Price must be within [low, high]."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate price within [low, high]."""

        violations = [
            record
            for record in records
            if record.price is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.price <= record.high)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class AvgWithinRangeRule(QualityRule):
    """Ensure average price is within the low/high range."""

    name = "avg_within_range"
    description = "Average price must be within [low, high]."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate average within [low, high]."""

        violations = [
            record
            for record in records
            if record.avg is not None
            and record.low is not None
            and record.high is not None
            and not (record.low <= record.avg <= record.high)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class TickerNotBlankRule(QualityRule):
    """Ensure ticker is not blank."""

    name = "ticker_not_blank"
    description = "Ticker must be a non-blank string."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate non-blank tickers."""

        violations = [
            record
            for record in records
            if not isinstance(record.ticker, str) or not record.ticker.strip()
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class TimestampParseableRule(QualityRule):
    """Ensure timestamp is a datetime instance."""

    name = "timestamp_parseable"
    description = "Timestamp must be a datetime instance."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate timestamp type."""

        violations = [
            record for record in records if not isinstance(record.timestamp, datetime)
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class VolumeNonNegativeRule(QualityRule):
    """Ensure volume is non-negative."""

    name = "volume_non_negative"
    description = "Volume must be greater than or equal to 0."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate volume >= 0."""

        violations = [
            record
            for record in records
            if record.volume is None or record.volume < 0
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )


class MarketCapNonNegativeRule(QualityRule):
    """Ensure market cap is non-negative."""

    name = "market_cap_non_negative"
    description = "Market cap must be greater than or equal to 0."

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        """Validate market cap >= 0."""

        violations = [
            record
            for record in records
            if record.market_cap is None or record.market_cap < 0
        ]
        return QualityRuleResult(
            name=self.name,
            description=self.description,
            passed=len(violations) == 0,
            violation_count=len(violations),
        )
