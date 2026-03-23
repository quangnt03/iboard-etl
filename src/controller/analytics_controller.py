"""Controller layer for analytics reporting.

Keyword arguments:
None."""

from __future__ import annotations

from pathlib import Path

from src.config import CONFIG
from src.models.analytics import ReportResult
from src.repository.analytics_repository import create_analytics_repository
from src.service.analytics_service import AnalyticsService


class AnalyticsController:
    """Expose analytics reporting operations.

Keyword arguments:
None."""

    def __init__(self, service: AnalyticsService) -> None:
        """Initialize the controller.

Keyword arguments:
self -- The self.
service -- The service."""

        self.service = service

    def generate_report(self, output_path: Path | None = None) -> ReportResult:
        """Generate the HTML analytics report.

Keyword arguments:
self -- The self.
output_path -- Optional override for the output file path. (default None) (default None)"""

        # Delegate report generation to the service layer.
        return self.service.generate_report(output_path)


def create_analytics_controller() -> AnalyticsController:
    """Build the default analytics controller graph.

Keyword arguments:
None."""

    # Wire repository and service with config-driven settings.
    repository = create_analytics_repository(CONFIG.analytics_sql_path)
    service = AnalyticsService(
        repository,
        persist_vnstock_history=CONFIG.persist_vnstock_fallback,
        use_vnstock_fallback=CONFIG.use_vnstock_fallback,
    )
    return AnalyticsController(service)
