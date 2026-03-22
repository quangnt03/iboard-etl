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

### Example formulas

```text
intraday_volatility = (high_price - low_price) / nullif(open_price, 0)
volume_ratio = current_volume / nullif(avg_5d_volume, 0)
```

## HTML Report

The analytics result is rendered into:

```text
output/report-YYYYmmdd.html
```

## Logging

Logging should be written to:

```text
logs/pipeline.log
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
