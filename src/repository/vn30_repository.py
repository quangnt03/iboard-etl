"""Repository layer for VN30 SQLite persistence."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator

from src.config import CONFIG
from src.models.vn30_stock import VN30Record, VN30Row


class SQLiteConnectionManager:
    """Create and initialize SQLite connections for the project."""

    def __init__(self, database_path: Path, schema_path: Path) -> None:
        """Initialize the manager."""

        self.database_path = database_path
        self.schema_path = schema_path

    def initialize(self) -> None:
        """Create the database file and apply the SQL schema."""

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        with self.connect() as connection:
            if self._needs_schema_reset(connection):
                connection.execute("DROP TABLE IF EXISTS vn30_stock")
            connection.executescript(schema_sql)
            connection.commit()

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a configured SQLite connection."""

        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _needs_schema_reset(connection: sqlite3.Connection) -> bool:
        """Return whether the persisted table schema differs from the current one."""

        table_exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'vn30_stock'"
        ).fetchone()
        if table_exists is None:
            return False

        columns = [
            row["name"]
            for row in connection.execute("PRAGMA table_info(vn30_stock)").fetchall()
        ]
        expected_columns = [
            "timestamp",
            "ticker",
            "price",
            "change",
            "change_pct",
            "open",
            "close",
            "low",
            "high",
            "avg",
            "volume",
            "market_cap",
        ]
        return columns != expected_columns


class VN30Repository:
    """Perform CRUD operations against the `vn30_stock` table."""

    def __init__(self, connection_manager: SQLiteConnectionManager) -> None:
        """Initialize the repository."""

        self.connection_manager = connection_manager

    def create(self, record: VN30Record) -> VN30Row:
        """Insert a new quote row."""

        payload = self._serialize_record(record)
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(f":{column}" for column in payload)

        with self.connection_manager.connect() as connection:
            connection.execute(
                f"""
                INSERT INTO vn30_stock ({columns})
                VALUES ({placeholders})
                """,
                payload,
            )
            connection.commit()
            return self.get_by_ticker_and_timestamp(
                record.ticker,
                record.timestamp,
                connection=connection,
            )

    def upsert_many(self, records: list[VN30Record]) -> int:
        """Insert or replace a batch of quote rows."""

        if not records:
            return 0

        payloads = [self._serialize_record(record) for record in records]
        columns = ", ".join(payloads[0].keys())
        placeholders = ", ".join(f":{column}" for column in payloads[0])

        with self.connection_manager.connect() as connection:
            connection.executemany(
                f"""
                INSERT OR REPLACE INTO vn30_stock ({columns})
                VALUES ({placeholders})
                """,
                payloads,
            )
            connection.commit()
        return len(payloads)

    def get_by_ticker_and_timestamp(
        self,
        ticker: str,
        timestamp: datetime,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> VN30Row:
        """Fetch a row by its natural key."""

        row = self._fetch_one(
            "SELECT * FROM vn30_stock WHERE ticker = ? AND timestamp = ?",
            (ticker, timestamp.isoformat()),
            connection=connection,
        )
        if row is None:
            raise ValueError(
                f"Row with ticker={ticker!r} and timestamp={timestamp.isoformat()!r} was not found."
            )
        return self._row_to_model(row)

    def list_all(self) -> list[VN30Row]:
        """Return all stored rows ordered by ticker and timestamp."""

        with self.connection_manager.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM vn30_stock ORDER BY ticker ASC, timestamp ASC"
            ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, ticker: str, timestamp: datetime, record: VN30Record) -> VN30Row:
        """Update an existing row."""

        payload = self._serialize_record(record)
        assignments = ", ".join(f"{column} = :{column}" for column in payload)
        payload["existing_ticker"] = ticker
        payload["existing_timestamp"] = timestamp.isoformat()

        with self.connection_manager.connect() as connection:
            cursor = connection.execute(
                f"""
                UPDATE vn30_stock
                SET {assignments}
                WHERE ticker = :existing_ticker AND timestamp = :existing_timestamp
                """,
                payload,
            )
            connection.commit()
            if cursor.rowcount == 0:
                raise ValueError(
                    f"Row with ticker={ticker!r} and timestamp={timestamp.isoformat()!r} was not found."
                )
            return self.get_by_ticker_and_timestamp(
                record.ticker,
                record.timestamp,
                connection=connection,
            )

    def delete(self, ticker: str, timestamp: datetime) -> bool:
        """Delete a row by its natural key."""

        with self.connection_manager.connect() as connection:
            cursor = connection.execute(
                "DELETE FROM vn30_stock WHERE ticker = ? AND timestamp = ?",
                (ticker, timestamp.isoformat()),
            )
            connection.commit()
        return cursor.rowcount > 0

    def _fetch_one(
        self,
        query: str,
        parameters: tuple[Any, ...],
        *,
        connection: sqlite3.Connection | None = None,
    ) -> sqlite3.Row | None:
        """Fetch a single row using an optional existing connection."""

        if connection is not None:
            return connection.execute(query, parameters).fetchone()

        with self.connection_manager.connect() as managed_connection:
            return managed_connection.execute(query, parameters).fetchone()

    @staticmethod
    def _serialize_record(record: VN30Record) -> dict[str, Any]:
        """Convert a `VN30Record` into a database-ready payload."""

        payload = record.model_dump()
        payload["timestamp"] = record.timestamp.isoformat()
        return payload

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> VN30Row:
        """Convert a SQLite row into a typed response model."""

        data = dict(row)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return VN30Row.model_validate(data)


def create_connection_manager() -> SQLiteConnectionManager:
    """Build the default SQLite connection manager from app config."""

    return SQLiteConnectionManager(
        database_path=CONFIG.database_path,
        schema_path=CONFIG.schema_path,
    )


def create_vn30_repository() -> VN30Repository:
    """Build and initialize the default repository for VN30 stock rows."""

    connection_manager = create_connection_manager()
    connection_manager.initialize()
    return VN30Repository(connection_manager)
