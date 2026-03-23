"""Tests for VN30 quality validation and report generation.

Keyword arguments:
None."""

from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from src.models.vn30_stock import VN30Record
from src.quality_check import (
    AvgWithinRangeRule,
    ChangePctWithinBoundsRule,
    CloseWithinRangeRule,
    LowLessThanHighRule,
    MarketCapNonNegativeRule,
    NonNullPriceRule,
    NumericNonNegativeRule,
    OpenWithinRangeRule,
    PositiveVolumeDuringTradingHoursRule,
    TickerNotBlankRule,
    TimestampParseableRule,
    VN30QualityChecker,
    VolumeNonNegativeRule,
)


class VN30QualityCheckTests(unittest.TestCase):
    """Cover quality-rule behavior and report generation.

Keyword arguments:
None."""

    def setUp(self) -> None:
        """Prepare reusable records and a workspace-local report directory.

Keyword arguments:
self -- The self."""

        self.report_dir = Path("artifacts/test_runtime") / str(uuid4())
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.addCleanup(rmtree, self.report_dir, True)
        self.valid_record = VN30Record(
            expectedLastUpdate=datetime(2024, 1, 2, 3, 0, tzinfo=timezone.utc),
            stockSymbol="ACB",
            refPrice=23600,
            priceChange=300,
            priceChangePercent=1.27,
            openPrice=23400,
            matchedPrice=23600,
            lowest=23300,
            highest=23700,
            avgPrice=23500.0,
            stockVol=243800,
        )

    def test_non_null_price_rule_counts_violations(self) -> None:
        """Count records with null price.

Keyword arguments:
self -- The self."""

        invalid_record = VN30Record(
            expectedLastUpdate=datetime(2024, 1, 2, 3, 0, tzinfo=timezone.utc),
            stockSymbol="BAD",
            refPrice=None,
            priceChange=0,
            priceChangePercent=0,
            openPrice=1,
            matchedPrice=1,
            lowest=1,
            highest=1,
            avgPrice=1,
            stockVol=100,
        )
        result = NonNullPriceRule().validate([self.valid_record, invalid_record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_change_pct_rule_returns_anomalous_tickers(self) -> None:
        """Return tickers with out-of-bounds percentage changes.

Keyword arguments:
self -- The self."""

        invalid_record = VN30Record(
            expectedLastUpdate=datetime(2024, 1, 2, 3, 0, tzinfo=timezone.utc),
            stockSymbol="BAD",
            refPrice=100,
            priceChange=40,
            priceChangePercent=40,
            openPrice=100,
            matchedPrice=100,
            lowest=100,
            highest=100,
            avgPrice=100,
            stockVol=100,
        )
        result = ChangePctWithinBoundsRule().validate([self.valid_record, invalid_record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.affected_tickers, ["BAD"])

    def test_positive_volume_rule_checks_only_trading_hours(self) -> None:
        """Flag zero-volume records during ICT trading hours.

Keyword arguments:
self -- The self."""

        invalid_record = VN30Record(
            expectedLastUpdate=datetime(2024, 1, 2, 3, 0, tzinfo=timezone.utc),
            stockSymbol="ZERO",
            refPrice=100,
            priceChange=0,
            priceChangePercent=0,
            openPrice=100,
            matchedPrice=100,
            lowest=100,
            highest=100,
            avgPrice=100,
            stockVol=0,
        )
        result = PositiveVolumeDuringTradingHoursRule().validate([invalid_record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_quality_checker_writes_daily_json_report(self) -> None:
        """Write the quality report to a daily JSON file.

Keyword arguments:
self -- The self."""

        checker = VN30QualityChecker(report_directory=self.report_dir)
        report, report_path = checker.validate_and_write([self.valid_record], "https://example.test/vn30")

        self.assertTrue(report_path.exists())
        self.assertTrue(report_path.name.startswith("quality_report_check_"))
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["run_metadata"]["source"], "https://example.test/vn30")
        self.assertEqual(payload["run_metadata"]["records_checked"], 1)

    def test_numeric_non_negative_rule_flags_negative_values(self) -> None:
        """Flag negative numeric fields.

Keyword arguments:
self -- The self."""

        rule = NumericNonNegativeRule()
        for field in rule.numeric_fields:
            with self.subTest(field=field):
                record = self.valid_record.model_copy(update={field: -1})
                result = rule.validate([record])
                self.assertEqual(result.status, "fail")
                self.assertEqual(result.violation_count, 1)

    def test_low_less_than_high_rule_flags_inversion(self) -> None:
        """Flag records where low exceeds high.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 5})
        result = LowLessThanHighRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_open_within_range_rule_flags_outliers(self) -> None:
        """Flag open prices outside the low/high range.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "open": 25})
        result = OpenWithinRangeRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_close_within_range_rule_flags_outliers(self) -> None:
        """Flag close prices outside the low/high range.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "close": 5})
        result = CloseWithinRangeRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_avg_within_range_rule_flags_outliers(self) -> None:
        """Flag average prices outside the low/high range.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "avg": 0})
        result = AvgWithinRangeRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_ticker_not_blank_rule_flags_whitespace(self) -> None:
        """Flag blank or whitespace tickers.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"ticker": "  "})
        result = TickerNotBlankRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_timestamp_parseable_rule_flags_non_datetime(self) -> None:
        """Flag non-datetime timestamps.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"timestamp": "bad"})
        result = TimestampParseableRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_volume_non_negative_rule_flags_negative_volume(self) -> None:
        """Flag negative volume values.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"volume": -1})
        result = VolumeNonNegativeRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_market_cap_non_negative_rule_flags_negative_market_cap(self) -> None:
        """Flag negative market cap values.

Keyword arguments:
self -- The self."""

        record = self.valid_record.model_copy(update={"market_cap": -1})
        result = MarketCapNonNegativeRule().validate([record])
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.violation_count, 1)

    def test_quality_check_uses_latest_batch_only(self) -> None:
        """Ensure quality checks only evaluate the latest batch.

Keyword arguments:
self -- The self."""

        older_record = self.valid_record.model_copy(
            update={
                "ticker": "OLD",
                "price": None,
                "updated_at": datetime(2024, 1, 2, 1, 0, tzinfo=timezone.utc),
            }
        )
        newer_record = self.valid_record.model_copy(
            update={
                "ticker": "NEW",
                "price": 100,
                "updated_at": datetime(2024, 1, 2, 2, 0, tzinfo=timezone.utc),
            }
        )
        checker = VN30QualityChecker(report_directory=self.report_dir)
        report, _ = checker.validate_and_write([older_record, newer_record], "https://example.test/vn30")

        self.assertEqual(report.run_metadata.records_checked, 1)
