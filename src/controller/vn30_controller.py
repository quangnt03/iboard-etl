"""Controller layer for VN30 population interfaces.

Keyword arguments:
None."""

from __future__ import annotations

from src.config import CONFIG
from src.ingest import create_vn30_fetcher
from src.models.vn30_stock import PopulationResponse
from src.repository.vn30_repository import create_vn30_repository
from src.service.vn30_service import FetchPopulationResult, VN30Service
from src.utils import get_logger


class VN30Controller:
    """Expose VN30 population operations to the application entrypoint.

Keyword arguments:
None."""

    def __init__(self, service: VN30Service) -> None:
        """Initialize the controller.

Keyword arguments:
self -- The self.
service -- The service."""

        self.service = service
        self.logger = get_logger(CONFIG.log_path)

    def fetch_and_populate(self) -> PopulationResponse:
        """Fetch data from the API and populate the database.

Keyword arguments:
self -- The self."""

        # Orchestrate the fetch+persist workflow through the service layer.
        result: FetchPopulationResult = self.service.populate_from_api()
        self.logger.info(
            "source_url=%s success=%s rows_loaded=%s rows_stored=%s quality_passed=%s quality_report_path=%s message=%s",
            result.source_url,
            result.success,
            result.loaded_count,
            result.stored_count,
            result.quality_passed,
            result.quality_report_path,
            result.message,
        )
        return PopulationResponse(
            source_url=result.source_url,
            database_path=CONFIG.database_path,
            loaded_count=result.loaded_count,
            stored_count=result.stored_count,
            success=result.success,
            message=result.message,
            quality_passed=result.quality_passed,
            quality_report_path=result.quality_report_path,
        )


def create_vn30_controller() -> VN30Controller:
    """Build the default VN30 controller wrapper.

Keyword arguments:
None."""

    # Wire repository, fetcher, and quality checker for the VN30 service.
    repository = create_vn30_repository()
    fetcher = create_vn30_fetcher()
    from src.quality_check import VN30QualityChecker

    quality_checker = VN30QualityChecker(report_directory=CONFIG.log_path.parent)
    service = VN30Service(repository, fetcher, quality_checker)
    return VN30Controller(service)
