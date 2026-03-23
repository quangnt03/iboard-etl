"""Integration tests for analytics report generation.

Keyword arguments:
None."""

import sqlite3
import unittest
from pathlib import Path
import shutil

from src.config import CONFIG
from src.repository.analytics_repository import AnalyticsRepository
from src.repository.vn30_repository import SQLiteConnectionManager
from src.service.analytics_service import AnalyticsService


class TestReportGeneration(unittest.TestCase):
    """Integration-style tests for report generation.

Keyword arguments:
None."""

    def test_generate_report_writes_file(self) -> None:
        """Ensure report generation writes HTML to disk.

Keyword arguments:
self -- The self."""
        base_dir = Path("artifacts") / "tmp_report_test"
        output_dir = Path("output")
        db_path = base_dir / "stocks.db"
        output_path = output_dir / "report-test.html"
        if base_dir.exists():
            shutil.rmtree(base_dir, ignore_errors=True)
        base_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._seed_database(db_path)
            connection_manager = SQLiteConnectionManager(db_path, CONFIG.schema_path)
            repository = AnalyticsRepository(connection_manager, CONFIG.analytics_sql_path)
            service = AnalyticsService(repository)
            result = service.generate_report(output_path)
            self.assertTrue(result.output_path.exists())
            content = result.output_path.read_text(encoding="utf-8")
            self.assertIn("Intraday Volatility Snapshot", content)
        finally:
            shutil.rmtree(base_dir, ignore_errors=True)
            if output_path.exists():
                output_path.unlink()

    @staticmethod
    def _seed_database(db_path: Path) -> None:
        """Create a minimal database for analytics queries.

Keyword arguments:
db_path -- The db path."""
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE vn30_stock (
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                volume INTEGER,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO vn30_stock (timestamp, ticker, open, high, low, volume)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            ("2026-03-20T10:00:00", "AAA", 10.0, 15.0, 9.0, 120),
        )
        connection.commit()
        connection.close()


if __name__ == "__main__":
    unittest.main()
