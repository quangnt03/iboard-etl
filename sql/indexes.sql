-- SQLite index scaffold for stock price analytics performance.

CREATE INDEX IF NOT EXISTS idx_vn30_stock_timestamp
ON vn30_stock (timestamp);

CREATE INDEX IF NOT EXISTS idx_vn30_stock_ticker_timestamp
ON vn30_stock (ticker, timestamp);
