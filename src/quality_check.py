"""Post-retrieval quality checks for VN30 data.

Keyword arguments:
None."""

from __future__ import annotations


import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config import CONFIG, AppConfig
from src.ingest import FetchError, create_vn30_fetcher
from src.models.quality_rules import (
    AvgWithinRangeRule,
    ChangePctWithinBoundsRule,
    CloseWithinRangeRule,
    LowLessThanHighRule,
    MarketCapNonNegativeRule,
    NonNullPriceRule,
    NumericNonNegativeRule,
    OpenWithinRangeRule,
    PositiveVolumeDuringTradingHoursRule,
    QualityRule,
    QualityReport,
    QualityReportSummary,
    RunMetadata,
    TickerNotBlankRule,
    TimestampParseableRule,
    VolumeNonNegativeRule,
)
from src.models.vn30_stock import VN30Record
from src.utils import get_logger

ICT = timezone(timedelta(hours=7))

class VN30QualityChecker:
    """Run VN30 post-retrieval quality validation and write JSON reports.

Keyword arguments:
None."""

    def __init__(self, report_directory: Path, rules: list[QualityRule] | None = None) -> None:
        """Initialize the quality checker.

Keyword arguments:
self -- The self.
report_directory -- The report directory.
rules -- (default None) (default None)"""

        # Store report destination and initialize rule set.
        self.report_directory = report_directory
        self.logger = get_logger(CONFIG.log_path)
        self.rules = rules or [
            NonNullPriceRule(),
            ChangePctWithinBoundsRule(),
            PositiveVolumeDuringTradingHoursRule(),
            NumericNonNegativeRule(),
            LowLessThanHighRule(),
            OpenWithinRangeRule(),
            CloseWithinRangeRule(),
            # PriceWithinRangeRule(),
            AvgWithinRangeRule(),
            TickerNotBlankRule(),
            TimestampParseableRule(),
            VolumeNonNegativeRule(),
            MarketCapNonNegativeRule(),
        ]

    def build_report(self, records: list[VN30Record], source_url: str) -> QualityReport:
        """Build a Pydantic quality report from VN30 records.

Keyword arguments:
self -- The self.
records -- The records.
source_url -- The source url."""

        # Only validate the latest batch to avoid duplicate historical checks.
        records = _latest_batch(records)
        rule_results = [rule.validate(records) for rule in self.rules]
        passed_rules = sum(1 for result in rule_results if result.status == "pass")
        failed_rules = len(rule_results) - passed_rules
        generated_at = datetime.now(tz=ICT)
        overall_status = "pass" if failed_rules == 0 else "fail"
        return QualityReport(
            run_metadata=RunMetadata(
                run_id=generated_at.isoformat(),
                source=source_url,
                dataset="VN30",
                generated_at=generated_at,
                trading_timezone="Asia/Ho_Chi_Minh",
                records_checked=len(records),
            ),
            summary=QualityReportSummary(
                total_rules=len(rule_results),
                passed_rules=passed_rules,
                failed_rules=failed_rules,
                overall_status=overall_status,
            ),
            checks=rule_results,
        )

    def report_path(self) -> Path:
        """Return the daily JSON report path.

Keyword arguments:
self -- The self."""

        # Use a date-stamped filename for daily reports.
        report_date = datetime.now(tz=ICT).strftime("%Y-%m-%d")
        return self.report_directory / f"quality_report_check_{report_date}.json"

    def write_report(self, report: QualityReport) -> Path:
        """Write the quality report to disk.

Keyword arguments:
self -- The self.
report -- The report."""

        # Persist the quality report JSON to disk.
        output_path = self.report_path()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return output_path

    def validate_and_write(self, records: list[VN30Record], source_url: str) -> tuple[QualityReport, Path]:
        """Validate records and write the daily JSON report.

Keyword arguments:
self -- The self.
records -- The records.
source_url -- The source url."""

        # Log start/end for observability and tracing.
        self.logger.info(
            "quality_check_start source_url=%s records=%s report_dir=%s",
            source_url,
            len(records),
            self.report_directory,
        )
        report = self.build_report(records, source_url)
        report_path = self.write_report(report)
        total_violations = sum(check.violation_count for check in report.checks)
        self.logger.info(
            "quality_check_complete report_path=%s failed_rules=%s violations=%s",
            report_path,
            report.summary.failed_rules,
            total_violations,
        )
        return report, report_path


def _latest_batch(records: list[VN30Record]) -> list[VN30Record]:
    """Select the latest batch of records using updated_at or timestamp.

Keyword arguments:
records -- The records."""

    # Guard against empty input to avoid max() errors.
    if not records:
        return records

    def batch_key(record: VN30Record) -> datetime:
        """Return the timestamp used to identify the latest batch.

Keyword arguments:
record -- The record."""
        # Prefer updated_at when present; fall back to timestamp.
        value = record.updated_at or record.timestamp
        if value.tzinfo is None:
            # Normalize to UTC to keep comparisons stable.
            value = value.replace(tzinfo=timezone.utc)
        return value.replace(microsecond=0)

    # Filter to the most recent batch using the normalized timestamp key.
    latest = max(batch_key(record) for record in records)
    return [record for record in records if batch_key(record) == latest]


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

Keyword arguments:
None."""

    # Provide CLI flags for API overrides and report output directory.
    parser = argparse.ArgumentParser(description="Run VN30 data quality checks.")
    parser.add_argument("--api-url", default=CONFIG.ssi_iboard_endpoint, help="Override API URL.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=CONFIG.request_timeout_seconds,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=CONFIG.max_retries,
        help="Maximum retry attempts for transient failures.",
    )
    parser.add_argument(
        "--retry-cooldown-seconds",
        type=float,
        default=CONFIG.retry_cooldown_seconds,
        help="Cooldown between retry attempts in seconds.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(CONFIG.log_path.parent),
        help="Directory to write the quality report JSON.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout summary output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the quality check CLI.

Keyword arguments:
argv -- Optional list of CLI arguments. (default None) (default None)"""

    # Parse CLI arguments and execute a quality check run.
    parser = build_parser()
    args = parser.parse_args(argv)
    logger = get_logger(CONFIG.log_path)

    config = CONFIG.model_copy(
        update={
            "ssi_iboard_endpoint": args.api_url,
            "request_timeout_seconds": args.timeout_seconds,
            "max_retries": args.max_retries,
            "retry_cooldown_seconds": args.retry_cooldown_seconds,
        }
    )
    # Fetch records from SSI before running validations.
    fetcher = create_vn30_fetcher(config)

    try:
        records = fetcher.fetch_records()
    except FetchError as exc:
        # Log fetch failure for observability and exit non-zero.
        logger.error("quality_check_fetch_failed source_url=%s error=%s", fetcher.api_url, exc)
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 1

    # Validate records and write the report to disk.
    report_directory = Path(args.report_dir)
    checker = VN30QualityChecker(report_directory=report_directory)
    report, report_path = checker.validate_and_write(records, fetcher.api_url)
    total_violations = sum(check.violation_count for check in report.checks)

    if not args.quiet:
        print(
            f"Quality report: {report_path} "
            f"(failed_rules={report.summary.failed_rules}, "
            f"violations={total_violations})"
        )
    # Log CLI completion with summary details.
    logger.info(
        "quality_check_cli_complete report_path=%s failed_rules=%s violations=%s",
        report_path,
        report.summary.failed_rules,
        total_violations,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
