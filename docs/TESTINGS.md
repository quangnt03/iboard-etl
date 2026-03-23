# Test Coverage Matrix

This document enumerates each test case, the feature it targets, expected return,
and expected behavior based on the current `tests/` suite.

## `tests/test_ingest.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_fetch_records_success` | VN30 API parsing and normalization | List of 1 validated record | Parsed record has `ticker=ACB`, `volume=243800`, `market_cap=23600*243800`. |
| `test_fetch_records_retries_http_429_then_succeeds` | Retry logic on HTTP 429 | List of 1 record after retry | First 429 is retried; second response succeeds. |
| `test_fetch_records_raises_on_malformed_json` | Malformed JSON handling | `FetchError` raised | Invalid JSON fails fast. |
| `test_fetch_records_raises_on_empty_data` | Empty payload handling | `FetchError` raised | Empty `data` array is rejected. |

## `tests/test_ingest_cli.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_build_parser_contains_expected_flags` | CLI flag exposure | Help text contains flags | `--api-url`, `--output-json`, `--no-db-write` are present. |
| `test_main_help_exits` | CLI help exit | `SystemExit` code `0` | `--help` exits cleanly. |

## `tests/test_cli_menu.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_menu_actions_exist` | Menu registry | Non-empty action list | At least 3 actions, includes keys `1` and `5`. |
| `test_main_help_exits` | CLI help exit | `SystemExit` code `0` | `--help` exits cleanly. |

## `tests/test_analytics.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_intraday_volatility_today_query_orders_by_latest_day` | Intraday volatility SQL | Non-empty query results | Uses latest day, orders descending; top ticker is `AAA` with volatility `0.6`. |
| `test_volume_vs_5d_avg_query` | 5-day average volume SQL | Non-empty query results | `current_volume=150`, `avg_5d=122`, `ratio=150/122`. |
| `test_volume_vs_5d_avg_fallback_single_day` | Volume ratio fallback | Non-empty query results | With single day, `avg_5d=current_volume` and ratio `1.0`. |

## `tests/test_quality_check.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_non_null_price_rule_counts_violations` | Non-null price rule | Rule result `fail` | Violation count is `1`. |
| `test_change_pct_rule_returns_anomalous_tickers` | Change percent bounds | Rule result `fail` | `affected_tickers=["BAD"]`. |
| `test_positive_volume_rule_checks_only_trading_hours` | Trading-hours volume | Rule result `fail` | Zero volume during trading hours is flagged. |
| `test_quality_checker_writes_daily_json_report` | Report generation | Report file path | JSON file exists and includes source URL and `records_checked=1`. |
| `test_numeric_non_negative_rule_flags_negative_values` | Numeric non-negativity | Rule result `fail` | Each numeric field set to negative yields one violation. |
| `test_low_less_than_high_rule_flags_inversion` | Low/high sanity | Rule result `fail` | Low > high yields one violation. |
| `test_open_within_range_rule_flags_outliers` | Open within range | Rule result `fail` | Open outside range yields one violation. |
| `test_close_within_range_rule_flags_outliers` | Close within range | Rule result `fail` | Close outside range yields one violation. |
| `test_avg_within_range_rule_flags_outliers` | Average within range | Rule result `fail` | Average outside range yields one violation. |
| `test_ticker_not_blank_rule_flags_whitespace` | Ticker blank check | Rule result `fail` | Whitespace tickers are flagged. |
| `test_timestamp_parseable_rule_flags_non_datetime` | Timestamp type check | Rule result `fail` | Non-datetime timestamp is flagged. |
| `test_volume_non_negative_rule_flags_negative_volume` | Volume non-negativity | Rule result `fail` | Negative volume yields one violation. |
| `test_market_cap_non_negative_rule_flags_negative_market_cap` | Market cap non-negativity | Rule result `fail` | Negative market cap yields one violation. |
| `test_quality_check_uses_latest_batch_only` | Latest batch filtering | Report metadata | `records_checked=1` for the latest batch. |

## `tests/test_quality_check_cli.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_build_parser_contains_expected_flags` | CLI flag exposure | Help text contains flags | `--api-url`, `--report-dir` are present. |
| `test_main_help_exits` | CLI help exit | `SystemExit` code `0` | `--help` exits cleanly. |

## `tests/test_pipeline_quality_gate.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_clean_report_uses_db_branch` | Quality gate branch | `branch=db_quality_then_report` | Uses DB branch when report is clean; report path exists. |
| `test_missing_report_refetches` | Missing report handling | `branch=refetch_then_report` | Missing report forces refetch path. |
| `test_failed_report_refetches` | Failed report handling | `branch=refetch_then_report` | Failed report forces refetch path. |

## `tests/test_report_generation.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_generate_report_writes_file` | Report rendering | HTML file written | File exists and includes `Intraday Volatility Snapshot`. |

## `tests/test_report_template.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_template_contains_required_columns` | Template headers | Headers present | Table headers include Ticker, Open, High, Low, Volatility %, Today Volume, 5-Day Avg Volume, Volume Ratio. |

## `tests/test_report_cli.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_build_parser_contains_expected_flags` | CLI flag exposure | Help text contains flags | `--output-path` is present. |
| `test_main_help_exits` | CLI help exit | `SystemExit` code `0` | `--help` exits cleanly. |

## `tests/test_service_controller.py`

| Test Case | Test Feature | Expected Return | Expected Behavior |
| --- | --- | --- | --- |
| `test_service_populate_from_api_success` | Service happy path | Success response | `success=True`, counts set, report path set, repository has 1 row. |
| `test_service_populate_from_api_failure` | Service failure path | Failure response | `success=False`, counts are zero, report path is `None`, message is `"timeout"`. |
| `test_repository_upsert_many_is_idempotent` | Repository idempotency | Single row stored | Duplicate upserts yield one row. |
| `test_controller_fetch_and_populate` | Controller response wrapping | Success response | `success=True`, `loaded_count=1`, report path set. |
