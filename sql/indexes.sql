-- SQLite index scaffold for stock price analytics performance.

-- Speed up time-based filtering on the raw timestamp.
CREATE INDEX IF NOT EXISTS idx_vn30_stock_timestamp
ON vn30_stock (timestamp);

-- Support ticker + time lookups (dedupe and recent history queries).
CREATE INDEX IF NOT EXISTS idx_vn30_stock_ticker_timestamp
ON vn30_stock (ticker, timestamp);
