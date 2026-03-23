import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from src.models.analytics import VolumeCountRow, VolumeRow, VolatilityRow
from src.service.analytics_service import AnalyticsService
from src.utils import VnStockHistoryResult
from tools.vnstock_history import VnStockHistoryRow


class StubAnalyticsRepository:
    """Stub repository for analytics fallback tests."""

    def __init__(
        self,
        volatility_rows: list[VolatilityRow],
        volume_rows: list[VolumeRow],
        count_rows: list[VolumeCountRow],
    ) -> None:
        """Store stubbed query results."""

        self._volatility_rows = volatility_rows
        self._volume_rows = volume_rows
        self._count_rows = count_rows

    def fetch_intraday_volatility(self) -> list[VolatilityRow]:
        """Return stubbed volatility rows."""

        return self._volatility_rows

    def fetch_volume_vs_5d_avg(self) -> list[VolumeRow]:
        """Return stubbed volume rows."""

        return self._volume_rows

    def fetch_volume_5d_counts(self) -> list[VolumeCountRow]:
        """Return stubbed volume count rows."""

        return self._count_rows


class TestAnalyticsFallback(unittest.TestCase):
    """Validate VnStock fallback behavior in analytics service."""

    def test_fallback_used_when_insufficient_rows(self) -> None:
        """Use VnStock history when SQLite has fewer than 5 daily rows."""

        repository = StubAnalyticsRepository(
            volatility_rows=[
                VolatilityRow(
                    ticker="AAA",
                    open_price=10.0,
                    high_price=12.0,
                    low_price=9.0,
                    intraday_volatility=0.3,
                )
            ],
            volume_rows=[
                VolumeRow(ticker="AAA", today_volume=100.0, avg_5d_volume=80.0, volume_ratio=1.25)
            ],
            count_rows=[VolumeCountRow(ticker="AAA", day_count=3)],
        )
        service = AnalyticsService(repository, persist_vnstock_history=False)
        rows = [
            VnStockHistoryRow(time=datetime(2026, 3, 16, tzinfo=timezone.utc), volume=10),
            VnStockHistoryRow(time=datetime(2026, 3, 17, tzinfo=timezone.utc), volume=20),
            VnStockHistoryRow(time=datetime(2026, 3, 18, tzinfo=timezone.utc), volume=30),
            VnStockHistoryRow(time=datetime(2026, 3, 19, tzinfo=timezone.utc), volume=40),
            VnStockHistoryRow(time=datetime(2026, 3, 20, tzinfo=timezone.utc), volume=50),
        ]
        history = VnStockHistoryResult(symbol="AAA", source="VCI", rows=rows)

        with patch("src.service.analytics_service.fetch_volume_history", return_value=history) as mocked:
            report_rows = service.build_report_rows()

        mocked.assert_called_once()
        self.assertEqual(len(report_rows), 1)
        self.assertAlmostEqual(report_rows[0].avg_5d_volume, 30.0)
        self.assertAlmostEqual(report_rows[0].volume_ratio, 100.0 / 30.0)

    def test_fallback_skipped_when_sufficient_rows(self) -> None:
        """Skip VnStock history when SQLite has 5 or more rows."""

        repository = StubAnalyticsRepository(
            volatility_rows=[
                VolatilityRow(
                    ticker="BBB",
                    open_price=10.0,
                    high_price=12.0,
                    low_price=9.0,
                    intraday_volatility=0.3,
                )
            ],
            volume_rows=[
                VolumeRow(ticker="BBB", today_volume=200.0, avg_5d_volume=150.0, volume_ratio=1.33)
            ],
            count_rows=[VolumeCountRow(ticker="BBB", day_count=5)],
        )
        service = AnalyticsService(repository, persist_vnstock_history=False)

        with patch("src.service.analytics_service.fetch_volume_history") as mocked:
            report_rows = service.build_report_rows()

        mocked.assert_not_called()
        self.assertEqual(len(report_rows), 1)
        self.assertAlmostEqual(report_rows[0].avg_5d_volume, 150.0)
        self.assertAlmostEqual(report_rows[0].volume_ratio, 1.33)

    def test_fallback_empty_history_keeps_sql_values(self) -> None:
        """Keep SQLite values when VnStock history is empty."""

        repository = StubAnalyticsRepository(
            volatility_rows=[
                VolatilityRow(
                    ticker="CCC",
                    open_price=10.0,
                    high_price=12.0,
                    low_price=9.0,
                    intraday_volatility=0.3,
                )
            ],
            volume_rows=[
                VolumeRow(ticker="CCC", today_volume=50.0, avg_5d_volume=40.0, volume_ratio=1.25)
            ],
            count_rows=[VolumeCountRow(ticker="CCC", day_count=2)],
        )
        service = AnalyticsService(repository, persist_vnstock_history=False)
        history = VnStockHistoryResult(symbol="CCC", source="VCI", rows=[])

        with patch("src.service.analytics_service.fetch_volume_history", return_value=history) as mocked:
            report_rows = service.build_report_rows()

        mocked.assert_called_once()
        self.assertEqual(len(report_rows), 1)
        self.assertAlmostEqual(report_rows[0].avg_5d_volume, 40.0)
        self.assertAlmostEqual(report_rows[0].volume_ratio, 1.25)


if __name__ == "__main__":
    unittest.main()
