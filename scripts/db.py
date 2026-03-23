"""Utility script to apply SQL indexes to the local SQLite database.

Keyword arguments:
None."""

import sqlite3
from pathlib import Path

# Local SQLite database path used by the pipeline.
db = Path("data/stocks.db")
# Index definitions to speed up analytics queries.
sql = Path("sql/indexes.sql").read_text(encoding="utf-8")
with sqlite3.connect(db) as conn:
    conn.executescript(sql)
