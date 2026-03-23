# Analytics and Logging

## Analytics Logic

The analytics stage should be SQL-first.

All analytics queries should be written in:

```text
sql/analytics_queries.sql
```

This keeps SQL logic reviewable and separate from Python orchestration.

### Required metrics

- intraday volatility
- current volume
- 5-day average volume
- volume ratio versus 5-day average
- top 10 most volatile stocks

### Suggested SQL techniques

- CTEs
- joins
- aggregations
- window functions where useful

### Formulas

```text
intraday_volatility = (high_price - low_price) / nullif(open_price, 0)
volume_ratio = current_volume / nullif(avg_5d_volume, 0)
```

## HTML Report

The analytics result is rendered into:

```text
output/report-YYYYmmdd.html
```

Report format:
- Dark-themed table sorted by volatility (top 10).
- Columns: Ticker, Open, High, Low, Volatility %, Today Volume, 5-Day Avg Volume, Volume Ratio.
- Volume Ratio is computed as `today_volume / avg_5d_volume`.

## Logging

Logging should be written to:

```text
logs/pipeline.log
```

## Run Metrics Log

Each full pipeline run writes a daily metrics log:

```text
logs/run_pipeline_ddmmyy.json
```

Format:

```json
{
  "run_id": "2026-03-21T23:33:38+07:00",
  "source": "SSI iBoard API",
  "dataset": "VN30",
  "started_at": "2026-03-21T23:33:36+07:00",
  "finished_at": "2026-03-21T23:33:38+07:00",
  "duration_seconds": 2.14,
  "status": "success",
  "rows_fetched": 30,
  "rows_validated": 30,
  "rows_inserted": 30,
  "rows_skipped": 0,
  "rows_failed_validation": 0,
  "quality_failures_by_rule": {
    "no_null_prices": 0,
    "price_change_within_bounds": 0,
    "volume_positivity": 0
  },
  "artifacts": {
    "quality_report": "output/data_quality_report.json",
    "analytics_report": "output/report-20260321.html"
  }
}
```

The log should include:

- pipeline start and end time,
- rows fetched,
- rows validated,
- rows inserted,
- rows skipped,
- validation failures,
- SQL failures,
- and unexpected exceptions.

## Error Handling

The implementation should gracefully handle:

- request failures,
- timeouts,
- invalid JSON,
- empty payloads,
- type conversion failures,
- Pydantic validation failures,
- duplicate inserts,
- invalid numeric values,
- and SQL execution errors.

Preferred behavior:

- log clearly,
- skip invalid records when appropriate,
- fail loudly when the pipeline cannot continue,
- and avoid silent corruption.

Fallback behavior:
- When SQL does not return 5 daily volume rows for a ticker, the analytics layer can
  fetch VnStock history to compute the 5-day average volume.
- Control this with `USE_VNSTOCK_FALLBACK` (default `true`).
- To persist fallback rows into SQLite, set `PERSIST_VNSTOCK_FALLBACK` (default `false`).
