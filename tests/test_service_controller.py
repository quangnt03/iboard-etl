"""Tests for VN30 service and controller orchestration.

Keyword arguments:
None."""

from __future__ import annotations

import unittest
from pathlib import Path
from shutil import rmtree
from uuid import uuid4

from src.controller.vn30_controller import VN30Controller
from src.ingest import FetchError
from src.models.vn30_stock import VN30Record
from src.quality_check import VN30QualityChecker
from src.repository.vn30_repository import SQLiteConnectionManager, VN30Repository
from src.service.vn30_service import VN30Service


class StubFetcher:
    """Return predefined records or raise a configured error.

Keyword arguments:
None."""

    def __init__(self, records: list[VN30Record] | None = None, error_message: str | None = None) -> None:
        """Store stub behavior.

Keyword arguments:
self -- The self.
records -- (default None) (default None)
error_message -- (default None) (default None)"""

        self.api_url = "https://example.test/vn30"
        self._records = records or []
        self._error_message = error_message

    def fetch_records(self) -> list[VN30Record]:
        """Return records or raise an error.

Keyword arguments:
self -- The self."""

        if self._error_message is not None:
            raise FetchError(self._error_message)
        return self._records


class VN30ServiceControllerTests(unittest.TestCase):
    """Cover service and controller population flows.

Keyword arguments:
None."""

    def setUp(self) -> None:
        """Build a temporary SQLite-backed repository.

Keyword arguments:
self -- The self."""

        base_path = Path("artifacts/test_runtime") / str(uuid4())
        base_path.mkdir(parents=True, exist_ok=True)
        self.addCleanup(self._cleanup_workspace_temp_dir, base_path)
        connection_manager = SQLiteConnectionManager(
            database_path=base_path / "stocks.db",
            schema_path=Path("sql/schema.sql"),
        )
        connection_manager.initialize()
        self.repository = VN30Repository(connection_manager)
        self.quality_checker = VN30QualityChecker(report_directory=base_path)
        self.record = VN30Record(
            expectedLastUpdate=1773972896569,
            stockSymbol="ACB",
            refPrice=23600,
            priceChange=-300,
            priceChangePercent=-1.27,
            openPrice=23400,
            matchedPrice=23300,
            lowest=23300,
            highest=23500,
            avgPrice=23345.24,
            stockVol=243800,
        )

    def _cleanup_workspace_temp_dir(self, path: Path) -> None:
        """Remove the workspace-local temporary directory after a test.

Keyword arguments:
self -- The self.
path -- The path."""

        rmtree(path, ignore_errors=True)

    def test_service_populate_from_api_success(self) -> None:
        """Persist fetched records and report success.

Keyword arguments:
self -- The self."""

        service = VN30Service(self.repository, StubFetcher(records=[self.record]), self.quality_checker)
        result = service.populate_from_api()

        self.assertTrue(result.success)
        self.assertEqual(result.loaded_count, 1)
        self.assertEqual(result.stored_count, 1)
        self.assertIsNotNone(result.quality_report_path)
        self.assertEqual(len(self.repository.list_all()), 1)

    def test_service_populate_from_api_failure(self) -> None:
        """Return a structured failure result.

Keyword arguments:
self -- The self."""

        service = VN30Service(self.repository, StubFetcher(error_message="timeout"), self.quality_checker)
        result = service.populate_from_api()

        self.assertFalse(result.success)
        self.assertEqual(result.loaded_count, 0)
        self.assertEqual(result.stored_count, 0)
        self.assertIsNone(result.quality_report_path)
        self.assertEqual(result.message, "timeout")

    def test_repository_upsert_many_is_idempotent(self) -> None:
        """Avoid duplicates for the same ticker and timestamp.

Keyword arguments:
self -- The self."""

        self.repository.upsert_many([self.record])
        self.repository.upsert_many([self.record])

        rows = self.repository.list_all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].ticker, "ACB")

    def test_controller_fetch_and_populate(self) -> None:
        """Wrap the service result in a controller response.

Keyword arguments:
self -- The self."""

        controller = VN30Controller(
            VN30Service(self.repository, StubFetcher(records=[self.record]), self.quality_checker)
        )
        response = controller.fetch_and_populate()

        self.assertTrue(response.success)
        self.assertEqual(response.loaded_count, 1)
        self.assertIsNotNone(response.quality_report_path)
