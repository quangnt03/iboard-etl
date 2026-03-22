import sqlite3
from pathlib import Path

db = Path("data/stocks.db")
sql = Path("sql/indexes.sql").read_text(encoding="utf-8")
with sqlite3.connect(db) as conn:
    conn.executescript(sql)
