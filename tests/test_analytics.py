import re
import sqlite3
import unittest
from typing import Iterable, List, Tuple


def _load_named_query(sql_path: str, name: str) -> str:
    """Load a named SQL query from a file using `-- name: <name>` markers.

    Args:
        sql_path: Path to the SQL file.
        name: Named query identifier.

    Returns:
        The SQL query string.
    """
    with open(sql_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    pattern = rf"-- name:\s*{re.escape(name)}\s*(.*?;)"
    match = re.search(pattern, content, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        raise AssertionError(f"Query named '{name}' not found in {sql_path}.")
    return match.group(1).strip()


def _seed_rows(cursor: sqlite3.Cursor, rows: Iterable[Tuple[str, str, float, float, float]]) -> None:
    """Insert minimal rows for analytics testing.

    Args:
        cursor: SQLite cursor for inserts.
        rows: Row tuples of (timestamp, ticker, open, high, low).
    """
    cursor.executemany(
        """
        INSERT INTO vn30_stock (timestamp, ticker, open, high, low)
        VALUES (?, ?, ?, ?, ?);
        """,
        list(rows),
    )


def _setup_db() -> sqlite3.Connection:
    """Create an in-memory SQLite database with the minimal schema.

    Returns:
        A SQLite connection instance.
    """
    connection = sqlite3.connect(":memory:")
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE vn30_stock (
            timestamp TEXT NOT NULL,
            ticker TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    connection.commit()
    return connection


class TestAnalyticsQueries(unittest.TestCase):
    """Unit tests for analytics SQL queries."""

    def test_intraday_volatility_today_query_orders_by_latest_day(self) -> None:
        """Verify intraday volatility query uses the latest trade date and orders desc."""
        connection = _setup_db()
        cursor = connection.cursor()
        _seed_rows(
            cursor,
            rows=[
                ("2026-03-19T10:00:00", "AAA", 10.0, 12.0, 9.0),
                ("2026-03-19T10:00:00", "BBB", 10.0, 14.0, 9.5),
                ("2026-03-20T10:00:00", "AAA", 10.0, 15.0, 9.0),
                ("2026-03-20T10:00:00", "BBB", 10.0, 13.0, 9.0),
            ],
        )
        connection.commit()

        query = _load_named_query("sql/analytics_queries.sql", "intraday_volatility_today")
        cursor.execute(query)
        rows: List[Tuple[str, float, float, float, float]] = cursor.fetchall()

        self.assertTrue(rows, "Expected at least one result row.")
        top_row = rows[0]
        self.assertEqual(top_row[0], "AAA")
        self.assertAlmostEqual(top_row[4], 0.6, places=6)
        for row in rows:
            self.assertEqual(row[1], 10.0)
            self.assertIn(row[2], (15.0, 13.0))
            self.assertEqual(row[3], 9.0)

        connection.close()

    def test_volume_vs_5d_avg_query(self) -> None:
        """Verify 5-day average volume and ratio are computed for latest day."""
        connection = _setup_db()
        cursor = connection.cursor()
        cursor.execute("ALTER TABLE vn30_stock ADD COLUMN volume INTEGER;")
        _seed_rows(
            cursor,
            rows=[
                ("2026-03-16T10:00:00", "AAA", 10.0, 11.0, 9.5),
                ("2026-03-17T10:00:00", "AAA", 10.0, 11.0, 9.5),
                ("2026-03-18T10:00:00", "AAA", 10.0, 11.0, 9.5),
                ("2026-03-19T10:00:00", "AAA", 10.0, 11.0, 9.5),
                ("2026-03-20T10:00:00", "AAA", 10.0, 11.0, 9.5),
            ],
        )
        cursor.executemany(
            "UPDATE vn30_stock SET volume = ? WHERE timestamp = ? AND ticker = ?;",
            [
                (100, "2026-03-16T10:00:00", "AAA"),
                (110, "2026-03-17T10:00:00", "AAA"),
                (120, "2026-03-18T10:00:00", "AAA"),
                (130, "2026-03-19T10:00:00", "AAA"),
                (150, "2026-03-20T10:00:00", "AAA"),
            ],
        )
        connection.commit()

        query = _load_named_query("sql/analytics_queries.sql", "volume_vs_5d_avg")
        cursor.execute(query)
        rows: List[Tuple[str, float, float, float]] = cursor.fetchall()

        self.assertTrue(rows, "Expected at least one result row.")
        top_row = rows[0]
        self.assertEqual(top_row[0], "AAA")
        self.assertAlmostEqual(top_row[1], 150.0, places=6)
        self.assertAlmostEqual(top_row[2], 122.0, places=6)
        self.assertAlmostEqual(top_row[3], 150.0 / 122.0, places=6)

        connection.close()

    def test_volume_vs_5d_avg_fallback_single_day(self) -> None:
        """Fallback to today's volume when 5-day history is unavailable."""
        connection = _setup_db()
        cursor = connection.cursor()
        cursor.execute("ALTER TABLE vn30_stock ADD COLUMN volume INTEGER;")
        _seed_rows(
            cursor,
            rows=[
                ("2026-03-20T10:00:00", "AAA", 10.0, 11.0, 9.5),
            ],
        )
        cursor.execute(
            "UPDATE vn30_stock SET volume = ? WHERE timestamp = ? AND ticker = ?;",
            (200, "2026-03-20T10:00:00", "AAA"),
        )
        connection.commit()

        query = _load_named_query("sql/analytics_queries.sql", "volume_vs_5d_avg")
        cursor.execute(query)
        rows: List[Tuple[str, float, float, float]] = cursor.fetchall()

        self.assertTrue(rows, "Expected at least one result row.")
        top_row = rows[0]
        self.assertEqual(top_row[0], "AAA")
        self.assertAlmostEqual(top_row[1], 200.0, places=6)
        self.assertAlmostEqual(top_row[2], 200.0, places=6)
        self.assertAlmostEqual(top_row[3], 1.0, places=6)

        connection.close()


if __name__ == "__main__":
    unittest.main()
