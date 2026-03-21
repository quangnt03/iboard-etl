"""Tests for VN30 quality validation and report generation."""

from __future__ import annotations

import json
import unittest
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
    PriceWithinRangeRule,
    PositiveVolumeDuringTradingHoursRule,
    TickerNotBlankRule,
    TimestampParseableRule,
    VN30QualityChecker,
    VolumeNonNegativeRule,
)


class VN30QualityCheckTests(unittest.TestCase):
    """Cover quality-rule behavior and report generation."""

    def setUp(self) -> None:
        """Prepare reusable records and a workspace-local report directory."""

        self.report_dir = Path("artifacts/test_runtime") / str(uuid4())
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.addCleanup(rmtree, self.report_dir, True)
        self.valid_record = VN30Record(
            expectedLastUpdate=1773972896569,
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
        """Count records with null price."""

        invalid_record = VN30Record(
            expectedLastUpdate=1773972896569,
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
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_change_pct_rule_returns_anomalous_tickers(self) -> None:
        """Return tickers with out-of-bounds percentage changes."""

        invalid_record = VN30Record(
            expectedLastUpdate=1773972896569,
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
        self.assertFalse(result.passed)
        self.assertEqual(result.anomalous_tickers, ["BAD"])

    def test_positive_volume_rule_checks_only_trading_hours(self) -> None:
        """Flag zero-volume records during ICT trading hours."""

        invalid_record = VN30Record(
            expectedLastUpdate=1773972896569,
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
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_quality_checker_writes_daily_json_report(self) -> None:
        """Write the quality report to a daily JSON file."""

        checker = VN30QualityChecker(report_directory=self.report_dir)
        report, report_path = checker.validate_and_write([self.valid_record], "https://example.test/vn30")

        self.assertTrue(report_path.exists())
        self.assertTrue(report_path.name.startswith("qac_"))
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["source_url"], "https://example.test/vn30")
        self.assertEqual(payload["summary"]["rows_checked"], 1)

    def test_numeric_non_negative_rule_flags_negative_values(self) -> None:
        """Flag negative numeric fields."""

        rule = NumericNonNegativeRule()
        fields = [
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
        ]
        for field in fields:
            with self.subTest(field=field):
                record = self.valid_record.model_copy(update={field: -1})
                result = rule.validate([record])
                self.assertFalse(result.passed)
                self.assertEqual(result.violation_count, 1)

    def test_low_less_than_high_rule_flags_inversion(self) -> None:
        """Flag records where low exceeds high."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 5})
        result = LowLessThanHighRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_open_within_range_rule_flags_outliers(self) -> None:
        """Flag open prices outside the low/high range."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "open": 25})
        result = OpenWithinRangeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_close_within_range_rule_flags_outliers(self) -> None:
        """Flag close prices outside the low/high range."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "close": 5})
        result = CloseWithinRangeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_price_within_range_rule_flags_outliers(self) -> None:
        """Flag reference prices outside the low/high range."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "price": 50})
        result = PriceWithinRangeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_avg_within_range_rule_flags_outliers(self) -> None:
        """Flag average prices outside the low/high range."""

        record = self.valid_record.model_copy(update={"low": 10, "high": 20, "avg": 0})
        result = AvgWithinRangeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_ticker_not_blank_rule_flags_whitespace(self) -> None:
        """Flag blank or whitespace tickers."""

        record = self.valid_record.model_copy(update={"ticker": "  "})
        result = TickerNotBlankRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_timestamp_parseable_rule_flags_non_datetime(self) -> None:
        """Flag non-datetime timestamps."""

        record = self.valid_record.model_copy(update={"timestamp": "bad"})
        result = TimestampParseableRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_volume_non_negative_rule_flags_negative_volume(self) -> None:
        """Flag negative volume values."""

        record = self.valid_record.model_copy(update={"volume": -1})
        result = VolumeNonNegativeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)

    def test_market_cap_non_negative_rule_flags_negative_market_cap(self) -> None:
        """Flag negative market cap values."""

        record = self.valid_record.model_copy(update={"market_cap": -1})
        result = MarketCapNonNegativeRule().validate([record])
        self.assertFalse(result.passed)
        self.assertEqual(result.violation_count, 1)
