import json
import shutil
import sqlite3
import unittest
from pathlib import Path

from src.config import CONFIG
from main import run_pipeline


class TestPipelineQualityGate(unittest.TestCase):
    """Tests for quality-gated pipeline behavior."""

    def setUp(self) -> None:
        self.base_dir = Path("artifacts") / "tmp_quality_gate"
        self.logs_dir = self.base_dir / "logs"
        self.output_dir = self.base_dir / "output"
        self.db_path = self.base_dir / "stocks.db"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.base_dir, ignore_errors=True)

    def _seed_db(self) -> None:
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vn30_stock (
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                price REAL,
                change REAL,
                change_pct REAL,
                open REAL,
                close REAL,
                low REAL,
                high REAL,
                avg REAL,
                volume INTEGER,
                market_cap REAL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO vn30_stock (
                timestamp,
                ticker,
                price,
                change,
                change_pct,
                open,
                close,
                low,
                high,
                avg,
                volume,
                market_cap,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "2026-03-20T10:00:00+00:00",
                "AAA",
                10.0,
                0.1,
                1.0,
                9.8,
                10.0,
                9.5,
                10.5,
                10.0,
                100,
                1000.0,
                "2026-03-20T10:05:00+00:00",
            ),
        )
        connection.commit()
        connection.close()

    def _write_report(self, failed_rules: int, total_violations: int) -> Path:
        path = self.logs_dir / "quality_report_check_2026-03-20.json"
        total_rules = 1
        passed_rules = total_rules - failed_rules
        overall_status = "pass" if failed_rules == 0 else "fail"
        payload = {
            "run_metadata": {
                "run_id": "2026-03-20T10:00:00+07:00",
                "source": CONFIG.ssi_iboard_endpoint,
                "dataset": "VN30",
                "generated_at": "2026-03-20T10:00:00+07:00",
                "trading_timezone": "Asia/Ho_Chi_Minh",
                "records_checked": 1,
            },
            "summary": {
                "total_rules": total_rules,
                "passed_rules": passed_rules,
                "failed_rules": failed_rules,
                "overall_status": overall_status,
            },
            "checks": [
                {
                    "rule_name": "Dummy rule",
                    "rule_code": "dummy_rule",
                    "description": "Placeholder rule for quality gate tests.",
                    "logic": "always true",
                    "status": "pass" if total_violations == 0 else "fail",
                    "violation_count": total_violations,
                    "affected_tickers": [],
                    "sample_violations": [],
                }
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_clean_report_uses_db_branch(self) -> None:
        self._seed_db()
        self._write_report(0, 0)
        config = CONFIG.model_copy(
            update={
                "database_path": self.db_path,
                "log_path": self.logs_dir / "pipeline.log",
                "report_output_dir": self.output_dir,
            }
        )
        result = run_pipeline(config)
        self.assertEqual(result.branch, "db_quality_then_report")
        self.assertTrue(result.analytics_report_path and result.analytics_report_path.exists())

    def test_missing_report_refetches(self) -> None:
        self._seed_db()
        config = CONFIG.model_copy(
            update={
                "database_path": self.db_path,
                "log_path": self.logs_dir / "pipeline.log",
                "report_output_dir": self.output_dir,
            }
        )
        result = run_pipeline(config)
        self.assertEqual(result.branch, "refetch_then_report")

    def test_failed_report_refetches(self) -> None:
        self._seed_db()
        self._write_report(1, 2)
        config = CONFIG.model_copy(
            update={
                "database_path": self.db_path,
                "log_path": self.logs_dir / "pipeline.log",
                "report_output_dir": self.output_dir,
            }
        )
        result = run_pipeline(config)
        self.assertEqual(result.branch, "refetch_then_report")


if __name__ == "__main__":
    unittest.main()
