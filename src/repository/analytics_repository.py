"""Repository layer for analytics SQL execution."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from src.models.analytics import VolumeCountRow, VolumeRow, VolatilityRow
from src.repository.vn30_repository import SQLiteConnectionManager, create_connection_manager


class AnalyticsRepository:
    """Execute analytics SQL queries against SQLite."""

    def __init__(self, connection_manager: SQLiteConnectionManager, sql_path: Path) -> None:
        """Initialize the repository.

        Args:
            connection_manager: Shared SQLite connection manager.
            sql_path: Path to the analytics SQL file.
        """

        self.connection_manager = connection_manager
        self.sql_path = sql_path

    def fetch_intraday_volatility(self) -> list[VolatilityRow]:
        """Return volatility rows for the latest trading day."""

        query = self._load_named_query("intraday_volatility_today")
        with self.connection_manager.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [VolatilityRow.model_validate(dict(row)) for row in rows]

    def fetch_volume_vs_5d_avg(self) -> list[VolumeRow]:
        """Return volume vs 5-day average rows for the latest trading day."""

        query = self._load_named_query("volume_vs_5d_avg")
        with self.connection_manager.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [VolumeRow.model_validate(dict(row)) for row in rows]

    def fetch_volume_5d_counts(self) -> list[VolumeCountRow]:
        """Return per-ticker daily volume counts for the last 5 days."""

        query = self._load_named_query("volume_5d_counts")
        with self.connection_manager.connect() as connection:
            rows = connection.execute(query).fetchall()
        return [VolumeCountRow.model_validate(dict(row)) for row in rows]

    def _load_named_query(self, name: str) -> str:
        """Load a named SQL query from the analytics SQL file.

        Args:
            name: Identifier following the `-- name:` marker.

        Returns:
            The SQL query string.
        """

        sql_text = self.sql_path.read_text(encoding="utf-8")
        pattern = rf"-- name:\s*{re.escape(name)}\s*(.*?;)"
        match = re.search(pattern, sql_text, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            raise ValueError(f"Query named '{name}' not found in {self.sql_path}.")
        return match.group(1).strip()


def create_analytics_repository(sql_path: Path) -> AnalyticsRepository:
    """Build an analytics repository with the default connection manager."""

    connection_manager = create_connection_manager()
    return AnalyticsRepository(connection_manager, sql_path)
