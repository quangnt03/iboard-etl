# Data Quality Check and JSON Report for VN30

## Summary

Add a post-retrieval quality validation stage that runs after successful fetch and writes a daily JSON report to `logs/qac_YYYY-mm-dd.json` without changing fetcher logic.

## Key Changes

- Add VN30 quality-report Pydantic models to the VN30 domain model module.
- Implement an extensible rule framework in `src/quality_check.py`.
- Add three initial rules:
  - non-null price
  - `change_pct` within `±30`
  - positive volume during 09:00–15:00 ICT
  - all numeric fields non-negative
  - `low <= high`
  - `open` within `[low, high]`
  - `close` within `[low, high]`
  - `price` within `[low, high]`
  - `avg` within `[low, high]`
  - ticker not blank (no regex enforcement)
  - timestamp parseable
  - `volume >= 0`
  - `market_cap >= 0`
- Integrate quality checking into the service flow after fetch success and before persistence result reporting.
- Extend service/controller result models with `quality_passed` and `quality_report_path`.

## Output

- Daily quality report JSON in `logs/qac_YYYY-mm-dd.json`
- Includes:
  - generation timestamp
  - source URL
  - rows checked
  - failed rule count
  - total violations
  - per-rule results

## Verification

- Add unit tests for rule behavior and report generation.
- Add service/controller integration checks for quality report emission.
- Keep fetcher behavior unchanged.
