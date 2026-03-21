"""Post-retrieval quality checks for VN30 data."""

from __future__ import annotations


from datetime import datetime,  timedelta, timezone
from pathlib import Path

from src.models.quality_rules import *
ICT = timezone(timedelta(hours=7))

class VN30QualityChecker:
    """Run VN30 post-retrieval quality validation and write JSON reports."""

    def __init__(self, report_directory: Path, rules: list[QualityRule] | None = None) -> None:
        """Initialize the quality checker."""

        self.report_directory = report_directory
        self.rules = rules or [
            NonNullPriceRule(),
            ChangePctWithinBoundsRule(),
            PositiveVolumeDuringTradingHoursRule(),
            NumericNonNegativeRule(),
            LowLessThanHighRule(),
            OpenWithinRangeRule(),
            CloseWithinRangeRule(),
            PriceWithinRangeRule(),
            AvgWithinRangeRule(),
            TickerNotBlankRule(),
            TimestampParseableRule(),
            VolumeNonNegativeRule(),
            MarketCapNonNegativeRule(),
        ]

    def build_report(self, records: list[VN30Record], source_url: str) -> QualityReport:
        """Build a Pydantic quality report from VN30 records."""

        rule_results = [rule.validate(records) for rule in self.rules]
        failed_rules = sum(1 for result in rule_results if not result.passed)
        total_violations = sum(result.violation_count for result in rule_results)
        return QualityReport(
            generated_at=datetime.now(tz=ICT),
            source_url=source_url,
            summary=QualityReportSummary(
                rows_checked=len(records),
                failed_rules=failed_rules,
                total_violations=total_violations,
                quality_passed=failed_rules == 0,
            ),
            rules=rule_results,
        )

    def report_path(self) -> Path:
        """Return the daily JSON report path."""

        report_date = datetime.now(tz=ICT).strftime("%Y-%m-%d")
        return self.report_directory / f"qac_{report_date}.json"

    def write_report(self, report: QualityReport) -> Path:
        """Write the quality report to disk."""

        output_path = self.report_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return output_path

    def validate_and_write(self, records: list[VN30Record], source_url: str) -> tuple[QualityReport, Path]:
        """Validate records and write the daily JSON report."""

        report = self.build_report(records, source_url)
        return report, self.write_report(report)

