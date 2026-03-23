-- Analytics query scaffold for volatility and volume reporting.

-- name: intraday_volatility_today
WITH latest_day AS (
    SELECT DATE(MAX(timestamp)) AS trade_date
    FROM vn30_stock
),
today_rows AS (
    SELECT
        ticker,
        timestamp,
        open,
        high,
        low
    FROM vn30_stock
    WHERE DATE(timestamp) = (SELECT trade_date FROM latest_day)
)
SELECT
    ticker,
    open AS open_price,
    high AS high_price,
    low AS low_price,
    (high - low) / NULLIF(open, 0) AS intraday_volatility
FROM today_rows
WHERE open IS NOT NULL
  AND high IS NOT NULL
  AND low IS NOT NULL
ORDER BY intraday_volatility DESC;

-- name: volume_vs_5d_avg
WITH latest_day AS (
    SELECT DATE(MAX(timestamp)) AS trade_date
    FROM vn30_stock
),
daily_volume AS (
    SELECT
        ticker,
        DATE(timestamp) AS trade_date,
        SUM(volume) AS day_volume
    FROM vn30_stock
    WHERE volume IS NOT NULL
    GROUP BY ticker, DATE(timestamp)
),
windowed AS (
    SELECT
        ticker,
        trade_date,
        day_volume,
        AVG(day_volume) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
            ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
        ) AS avg_5d_volume
    FROM daily_volume
)
SELECT
    ticker,
    day_volume AS today_volume,
    COALESCE(avg_5d_volume, day_volume) AS avg_5d_volume,
    day_volume / NULLIF(COALESCE(avg_5d_volume, day_volume), 0) AS volume_ratio
FROM windowed
WHERE trade_date = (SELECT trade_date FROM latest_day)
ORDER BY volume_ratio DESC;

-- name: volume_5d_counts
WITH latest_day AS (
    SELECT DATE(MAX(timestamp)) AS trade_date
    FROM vn30_stock
),
daily_volume AS (
    SELECT
        ticker,
        DATE(timestamp) AS trade_date
    FROM vn30_stock
    WHERE volume IS NOT NULL
    GROUP BY ticker, DATE(timestamp)
)
SELECT
    ticker,
    COUNT(*) AS day_count
FROM daily_volume
WHERE trade_date BETWEEN DATE((SELECT trade_date FROM latest_day), '-4 day')
  AND (SELECT trade_date FROM latest_day)
GROUP BY ticker;
