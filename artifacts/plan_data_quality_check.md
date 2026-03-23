# Data Quality Check and JSON Report for VN30

## Summary

Add a post-retrieval quality validation stage that runs after successful fetch and writes a daily JSON report to `logs/quality_report_check_YYYY-mm-dd.json` without changing fetcher logic. Realign the JSON report schema to the new sample format (run metadata, summary, and per-rule checks).

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
- Realign report format to:
  - `run_metadata`: `run_id`, `source`, `dataset`, `generated_at`, `trading_timezone`, `records_checked`
  - `summary`: `total_rules`, `passed_rules`, `failed_rules`, `overall_status`
  - `checks`: `rule_name`, `rule_code`, `description`, `logic`, `status`, `violation_count`, `affected_tickers`, `sample_violations`
- Update quality gate reader to support new report JSON (sum violations from `checks`).
- Update unit tests and any JSON fixtures to the new report shape.
- Filter quality checks to only the latest batch, using `updated_at` (fallback `timestamp`) to select records.
- Update pipeline DB-quality path to run checks on the latest batch only.

## Output

- Daily quality report JSON in `logs/quality_report_check_YYYY-mm-dd.json`
- Includes:
  - run metadata (run id, source, dataset, generated at, timezone, records checked)
  - summary (total/passed/failed rules, overall status)
  - per-rule check results with violations and samples

## Verification

- Add unit tests for rule behavior and report generation.
- Add service/controller integration checks for quality report emission.
- Keep fetcher behavior unchanged.
- Update pipeline quality gate tests to parse new JSON format.
- Add tests to ensure quality checks only cover the latest batch.
