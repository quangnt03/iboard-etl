PRAGMA foreign_keys = ON;

-- Core storage table for VN30 stock snapshots.
CREATE TABLE IF NOT EXISTS vn30_stock (
    -- Quote timestamp (ISO 8601 string).
    timestamp TEXT NOT NULL,
    -- Stock ticker symbol.
    ticker TEXT NOT NULL,
    -- Reference price at time of snapshot.
    price REAL,
    -- Absolute price change vs reference.
    change REAL,
    -- Percent price change vs reference.
    change_pct REAL,
    -- Opening price for the day.
    open REAL,
    -- Matched/closing price for the tick.
    close REAL,
    -- Lowest traded price in the session.
    low REAL,
    -- Highest traded price in the session.
    high REAL,
    -- Average traded price.
    avg REAL,
    -- Total traded volume.
    volume INTEGER,
    -- Market capitalization when available.
    market_cap REAL,
    -- Ingestion timestamp for auditing.
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Enforce uniqueness per ticker and timestamp.
    UNIQUE (ticker, timestamp)
);
