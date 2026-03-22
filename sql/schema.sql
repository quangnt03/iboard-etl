PRAGMA foreign_keys = ON;

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
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, timestamp)
);
