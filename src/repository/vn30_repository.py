"""Repository layer for VN30 SQLite persistence.

Keyword arguments:
None."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

from src.config import CONFIG
from src.models.vn30_stock import VN30Record, VN30Row


class SQLiteConnectionManager:
    """Create and initialize SQLite connections for the project.

Keyword arguments:
None."""

    def __init__(self, database_path: Path, schema_path: Path) -> None:
        """Initialize the manager.

Keyword arguments:
self -- The self.
database_path -- The database path.
schema_path -- The schema path."""

        self.database_path = database_path
        self.schema_path = schema_path

    def initialize(self) -> None:
        """Create the database file and apply the SQL schema.

Keyword arguments:
self -- The self."""

        # Ensure the database directory exists before connecting.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        with self.connect() as connection:
            # Reset schema if the persisted table structure is stale.
            if self._needs_schema_reset(connection):
                connection.execute("DROP TABLE IF EXISTS vn30_stock")
            connection.executescript(schema_sql)
            connection.commit()

    @contextmanager
    def connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a configured SQLite connection.

Keyword arguments:
self -- The self."""

        # Configure the SQLite connection with row access by name.
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _needs_schema_reset(connection: sqlite3.Connection) -> bool:
        """Return whether the persisted table schema differs from the current one.

Keyword arguments:
connection -- The connection."""

        # Check if the table exists before comparing columns.
        table_exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'vn30_stock'"
        ).fetchone()
        if table_exists is None:
            return False

        # Compare existing columns to the expected schema.
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
            "updated_at",
        ]
        return columns != expected_columns


class VN30Repository:
    """Perform CRUD operations against the `vn30_stock` table.

Keyword arguments:
None."""

    def __init__(self, connection_manager: SQLiteConnectionManager) -> None:
        """Initialize the repository.

Keyword arguments:
self -- The self.
connection_manager -- The connection manager."""

        self.connection_manager = connection_manager

    def create(self, record: VN30Record) -> VN30Row:
        """Insert a new quote row.

Keyword arguments:
self -- The self.
record -- The record."""

        # Serialize the record and build INSERT placeholders.
        payload = self._serialize_record(record)
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(f":{column}" for column in payload)

        with self.connection_manager.connect() as connection:
            # Insert and return the stored row.
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
        """Insert or replace a batch of quote rows.

Keyword arguments:
self -- The self.
records -- The records."""

        # Short-circuit when there is nothing to write.
        if not records:
            return 0

        payloads = [self._serialize_record(record) for record in records]
        columns = ", ".join(payloads[0].keys())
        placeholders = ", ".join(f":{column}" for column in payloads[0])

        with self.connection_manager.connect() as connection:
            # Use INSERT OR REPLACE to support idempotent upserts.
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
        """Fetch a row by its natural key.

Keyword arguments:
self -- The self.
ticker -- The ticker.
timestamp -- The timestamp.
connection -- (default None) (default None)"""

        # Query by natural key (ticker + timestamp).
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
        """Return all stored rows ordered by ticker and timestamp.

Keyword arguments:
self -- The self."""

        # Order results for deterministic downstream processing.
        with self.connection_manager.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM vn30_stock ORDER BY ticker ASC, timestamp ASC"
            ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def update(self, ticker: str, timestamp: datetime, record: VN30Record) -> VN30Row:
        """Update an existing row.

Keyword arguments:
self -- The self.
ticker -- The ticker.
timestamp -- The timestamp.
record -- The record."""

        # Update fields based on the provided record payload.
        payload = self._serialize_record(record)
        assignments = ", ".join(f"{column} = :{column}" for column in payload)
        payload["existing_ticker"] = ticker
        payload["existing_timestamp"] = timestamp.isoformat()

        with self.connection_manager.connect() as connection:
            # Execute update and re-fetch to return the stored row.
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
        """Delete a row by its natural key.

Keyword arguments:
self -- The self.
ticker -- The ticker.
timestamp -- The timestamp."""

        # Perform a keyed delete and return whether a row was removed.
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
        """Fetch a single row using an optional existing connection.

Keyword arguments:
self -- The self.
query -- The query.
parameters -- The parameters.
connection -- (default None) (default None)"""

        # Use the provided connection when available to avoid re-opening.
        if connection is not None:
            return connection.execute(query, parameters).fetchone()

        with self.connection_manager.connect() as managed_connection:
            return managed_connection.execute(query, parameters).fetchone()

    @staticmethod
    def _serialize_record(record: VN30Record) -> dict[str, Any]:
        """Convert a `VN30Record` into a database-ready payload.

Keyword arguments:
record -- The record."""

        # Convert to a dict and normalize timestamp fields for SQLite.
        payload = record.model_dump()
        payload["timestamp"] = record.timestamp.isoformat()
        if record.updated_at is None:
            payload["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        else:
            payload["updated_at"] = record.updated_at.isoformat()
        return payload

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> VN30Row:
        """Convert a SQLite row into a typed response model.

Keyword arguments:
row -- The row."""

        # Parse timestamp fields and validate into the response model.
        data = dict(row)
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        updated_at_value = data.get("updated_at")
        if isinstance(updated_at_value, str):
            data["updated_at"] = datetime.fromisoformat(updated_at_value)
        return VN30Row.model_validate(data)


def create_connection_manager() -> SQLiteConnectionManager:
    """Build the default SQLite connection manager from app config.

Keyword arguments:
None."""

    # Construct the connection manager using the shared app config.
    return SQLiteConnectionManager(
        database_path=CONFIG.database_path,
        schema_path=CONFIG.schema_path,
    )


def create_vn30_repository() -> VN30Repository:
    """Build and initialize the default repository for VN30 stock rows.

Keyword arguments:
None."""

    # Initialize schema and return the repository instance.
    connection_manager = create_connection_manager()
    connection_manager.initialize()
    return VN30Repository(connection_manager)
