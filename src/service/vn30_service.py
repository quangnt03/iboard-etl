"""Service layer for VN30 ingestion and validation.

Keyword arguments:
None."""

from __future__ import annotations

from src.ingest import FetchError, VN30Fetcher
from src.quality_check import VN30QualityChecker
from src.repository.vn30_repository import VN30Repository
from src.models.vn30_stock import FetchPopulationResult
from src.utils import get_logger
from src.config import CONFIG


class VN30Service:
    """Handle VN30 payload loading, validation, and persistence orchestration.

Keyword arguments:
None."""

    def __init__(
        self,
        repository: VN30Repository,
        fetcher: VN30Fetcher,
        quality_checker: VN30QualityChecker,
    ) -> None:
        """Initialize the service.

Keyword arguments:
self -- The self.
repository -- The repository.
fetcher -- The fetcher.
quality_checker -- The quality checker."""

        self.repository = repository
        self.fetcher = fetcher
        self.quality_checker = quality_checker
        self.logger = get_logger(CONFIG.log_path)

    def populate_from_api(self) -> FetchPopulationResult:
        """Fetch VN30 records from the API and persist them to SQLite.

Keyword arguments:
self -- The self."""

        # Fetch records from SSI with retry behavior handled by the fetcher.
        try:
            records = self.fetcher.fetch_records()
        except (FetchError, ValueError) as exc:
            self.logger.error(
                "vn30_fetch_failed source_url=%s error=%s",
                self.fetcher.api_url,
                exc,
            )
            return FetchPopulationResult(
                loaded_count=0,
                stored_count=0,
                source_url=self.fetcher.api_url,
                success=False,
                message=str(exc),
                quality_passed=None,
                quality_report_path=None,
            )

        # Run quality checks before persisting to SQLite.
        quality_report, quality_report_path = self.quality_checker.validate_and_write(
            records,
            self.fetcher.api_url,
        )

        try:
            # Persist the cleaned records to SQLite.
            stored_count = self.repository.upsert_many(records)
            return FetchPopulationResult(
                loaded_count=len(records),
                stored_count=stored_count,
                source_url=self.fetcher.api_url,
                success=True,
                message="VN30 data fetched and stored successfully.",
                quality_passed=quality_report.summary.overall_status == "pass",
                quality_report_path=quality_report_path,
            )
        except ValueError as exc:
            return FetchPopulationResult(
                loaded_count=0,
                stored_count=0,
                source_url=self.fetcher.api_url,
                success=False,
                message=str(exc),
                quality_passed=quality_report.summary.overall_status == "fail",
                quality_report_path=quality_report_path,
            )
