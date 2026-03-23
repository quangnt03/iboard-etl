"""Pipeline orchestration for VN30 data processing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.analytics import generate_report
from src.config import CONFIG, AppConfig
from src.ingest import VN30Fetcher, create_vn30_fetcher
from src.models.quality_rules import QualityReport
from src.models.run_metrics import RunMetrics, RunMetricsArtifacts
from src.models.vn30_stock import VN30Record, VN30Row
from src.quality_check import VN30QualityChecker
from src.repository.vn30_repository import SQLiteConnectionManager, VN30Repository
from src.service.vn30_service import VN30Service
from src.utils import get_logger

ICT = timezone(timedelta(hours=7))

@dataclass(frozen=True)
class PipelineResult:
    """Capture pipeline execution details."""

    branch: str
    records_loaded: int
    records_stored: int
    quality_report_path: Path | None
    analytics_report_path: Path | None


def _latest_quality_report_path(report_dir: Path) -> Path | None:
    """Return the latest quality report JSON path in the report directory."""

    candidates = sorted(report_dir.glob("quality_report_check_*.json"))
    return candidates[-1] if candidates else None


def _load_quality_summary(report_path: Path) -> dict[str, Any] | None:
    """Load summary fields from a quality report JSON file."""

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        summary = payload.get("summary", {})
        checks = payload.get("checks")
        if not isinstance(checks, list):
            total_violations = -1
        else:
            total_violations = sum(
                int(check.get("violation_count", 0))
                for check in checks
                if isinstance(check, dict)
            )
        return {
            "failed_rules": int(summary.get("failed_rules", -1)),
            "total_violations": int(total_violations),
        }
    except (OSError, ValueError, TypeError):
        return None


def _load_quality_report(report_path: Path) -> QualityReport | None:
    """Load a quality report from disk."""

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    try:
        return QualityReport.model_validate(payload)
    except ValueError:
        return None


def _quality_failure_counts(
    report: QualityReport | None,
) -> tuple[int, dict[str, int], int]:
    """Compute validation counts from a quality report."""

    if report is None:
        return 0, {}, 0

    failures = {check.rule_code: int(check.violation_count) for check in report.checks}
    failed_total = sum(failures.values())
    return int(report.run_metadata.records_checked), failures, failed_total


def _rows_to_records(rows: list[VN30Row]) -> list[VN30Record]:
    """Map VN30Row objects to VN30Record for quality checks."""

    records: list[VN30Record] = []
    for row in rows:
        timestamp = row.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        record = VN30Record(
            timestamp=timestamp,
            ticker=row.ticker,
            price=row.price,
            change=row.change,
            change_pct=row.change_pct,
            open=row.open,
            close=row.close,
            low=row.low,
            high=row.high,
            avg=row.avg,
            volume=row.volume,
            market_cap=row.market_cap,
        )
        records.append(record)
    return records


def _latest_batch(records: list[VN30Record]) -> list[VN30Record]:
    """Select the latest batch of records using updated_at or timestamp."""

    if not records:
        return records

    def batch_key(record: VN30Record) -> datetime:
        value = record.updated_at or record.timestamp
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.replace(microsecond=0)

    latest = max(batch_key(record) for record in records)
    return [record for record in records if batch_key(record) == latest]


def _build_service(config: AppConfig) -> VN30Service:
    """Build VN30Service for the provided config."""

    connection_manager = SQLiteConnectionManager(
        database_path=config.database_path,
        schema_path=config.schema_path,
    )
    connection_manager.initialize()
    repository = VN30Repository(connection_manager)
    fetcher: VN30Fetcher = create_vn30_fetcher(config)
    quality_checker = VN30QualityChecker(report_directory=config.log_path.parent)
    return VN30Service(repository, fetcher, quality_checker)


def _default_report_path(config: AppConfig) -> Path:
    """Return default analytics report output path."""

    date_stamp = datetime.now().strftime("%Y%m%d")
    return config.report_output_dir / f"report-{date_stamp}.html"


def _run_metrics_path(log_dir: Path, timestamp: datetime) -> Path:
    """Return the daily run metrics log path."""

    date_stamp = timestamp.strftime("%d%m%y")
    return log_dir / f"run_pipeline_{date_stamp}.json"


def _write_run_metrics(metrics: RunMetrics, output_path: Path, logger: Any) -> None:
    """Write the run metrics JSON payload."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(metrics.model_dump_json(indent=2), encoding="utf-8")
    logger.info("run_metrics_written path=%s status=%s", output_path, metrics.status)


def run_pipeline(config: AppConfig | None = None) -> PipelineResult:
    """Run the pipeline with quality-gated behavior."""

    runtime_config = config or CONFIG
    logger = get_logger(runtime_config.log_path)
    started_at = datetime.now(tz=ICT)
    quality_report_path: Path | None = None
    analytics_report_path: Path | None = None
    status = "success"
    rows_fetched = 0
    rows_validated = 0
    rows_inserted = 0
    rows_skipped = 0
    rows_failed_validation = 0
    failures_by_rule: dict[str, int] = {}
    source_label = "SSI iBoard API"
    report_dir = runtime_config.log_path.parent
    report_path = _latest_quality_report_path(report_dir)
    summary = _load_quality_summary(report_path) if report_path else None
    has_clean_report = (
        summary is not None
        and summary["failed_rules"] == 0
        and summary["total_violations"] == 0
    )

    try:
        service = _build_service(runtime_config)
        if has_clean_report:
            rows = service.repository.list_all()
            if rows:
                records = _rows_to_records(rows)
                records = _latest_batch(records)
                checker = VN30QualityChecker(report_directory=report_dir)
                report, quality_report_path = checker.validate_and_write(
                    records,
                    runtime_config.ssi_iboard_endpoint,
                )
                rows_fetched = len(records)
                rows_inserted = 0
                rows_skipped = 0
                rows_validated, failures_by_rule, rows_failed_validation = (
                    _quality_failure_counts(report)
                )
                analytics_result = generate_report(_default_report_path(runtime_config))
                analytics_report_path = analytics_result.output_path
                return PipelineResult(
                    branch="db_quality_then_report",
                    records_loaded=len(records),
                    records_stored=len(rows),
                    quality_report_path=quality_report_path,
                    analytics_report_path=analytics_result.output_path,
                )

        fetch_result = service.populate_from_api()
        status = "success" if fetch_result.success else "failed"
        rows_fetched = fetch_result.loaded_count
        rows_inserted = fetch_result.stored_count
        rows_skipped = max(rows_fetched - rows_inserted, 0)
        quality_report_path = fetch_result.quality_report_path
        if quality_report_path:
            report = _load_quality_report(quality_report_path)
            rows_validated, failures_by_rule, rows_failed_validation = (
                _quality_failure_counts(report)
            )
        else:
            rows_validated = rows_fetched
        analytics_result = generate_report(_default_report_path(runtime_config))
        analytics_report_path = analytics_result.output_path
        return PipelineResult(
            branch="refetch_then_report",
            records_loaded=fetch_result.loaded_count,
            records_stored=fetch_result.stored_count,
            quality_report_path=fetch_result.quality_report_path,
            analytics_report_path=analytics_result.output_path,
        )
    except Exception as exc:
        status = "failed"
        logger.exception("pipeline_failed error=%s", exc)
        raise
    finally:
        finished_at = datetime.now(tz=ICT)
        duration_seconds = round((finished_at - started_at).total_seconds(), 2)
        metrics = RunMetrics(
            run_id=finished_at.isoformat(),
            source=source_label,
            dataset="VN30",
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration_seconds,
            status=status,
            rows_fetched=rows_fetched,
            rows_validated=rows_validated,
            rows_inserted=rows_inserted,
            rows_skipped=rows_skipped,
            rows_failed_validation=rows_failed_validation,
            quality_failures_by_rule=failures_by_rule,
            artifacts=RunMetricsArtifacts(
                quality_report=str(quality_report_path) if quality_report_path else None,
                analytics_report=str(analytics_report_path) if analytics_report_path else None,
            ),
        )
        metrics_path = _run_metrics_path(report_dir, finished_at)
        _write_run_metrics(metrics, metrics_path, logger)
