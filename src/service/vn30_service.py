"""Service layer for VN30 ingestion and validation."""

from __future__ import annotations

from src.ingest import FetchError, VN30Fetcher
from src.quality_check import VN30QualityChecker
from src.repository.vn30_repository import VN30Repository
from src.models.vn30_stock import FetchPopulationResult


class VN30Service:
    """Handle VN30 payload loading, validation, and persistence orchestration."""

    def __init__(
        self,
        repository: VN30Repository,
        fetcher: VN30Fetcher,
        quality_checker: VN30QualityChecker,
    ) -> None:
        """Initialize the service."""

        self.repository = repository
        self.fetcher = fetcher
        self.quality_checker = quality_checker

    def populate_from_api(self) -> FetchPopulationResult:
        """Fetch VN30 records from the API and persist them to SQLite."""

        try:
            records = self.fetcher.fetch_records()
        except (FetchError, ValueError) as exc:
            return FetchPopulationResult(
                loaded_count=0,
                stored_count=0,
                source_url=self.fetcher.api_url,
                success=False,
                message=str(exc),
                quality_passed=None,
                quality_report_path=None,
            )

        quality_report, quality_report_path = self.quality_checker.validate_and_write(
            records,
            self.fetcher.api_url,
        )

        try:
            stored_count = self.repository.upsert_many(records)
            return FetchPopulationResult(
                loaded_count=len(records),
                stored_count=stored_count,
                source_url=self.fetcher.api_url,
                success=True,
                message="VN30 data fetched and stored successfully.",
                quality_passed=quality_report.summary.quality_passed,
                quality_report_path=quality_report_path,
            )
        except ValueError as exc:
            return FetchPopulationResult(
                loaded_count=0,
                stored_count=0,
                source_url=self.fetcher.api_url,
                success=False,
                message=str(exc),
                quality_passed=quality_report.summary.quality_passed,
                quality_report_path=quality_report_path,
            )
