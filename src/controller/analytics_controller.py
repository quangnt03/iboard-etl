"""Controller layer for analytics reporting."""

from __future__ import annotations

from pathlib import Path

from src.config import CONFIG
from src.models.analytics import ReportResult
from src.repository.analytics_repository import create_analytics_repository
from src.service.analytics_service import AnalyticsService


class AnalyticsController:
    """Expose analytics reporting operations."""

    def __init__(self, service: AnalyticsService) -> None:
        """Initialize the controller."""

        self.service = service

    def generate_report(self, output_path: Path | None = None) -> ReportResult:
        """Generate the HTML analytics report.

        Args:
            output_path: Optional override for the output file path.

        Returns:
            ReportResult metadata for the generated report.
        """

        return self.service.generate_report(output_path)


def create_analytics_controller() -> AnalyticsController:
    """Build the default analytics controller graph."""

    repository = create_analytics_repository(CONFIG.analytics_sql_path)
    service = AnalyticsService(repository)
    return AnalyticsController(service)
