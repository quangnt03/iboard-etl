# Plan: Unchecked Tasks From tasks/todo.md

## Scope
- Source of truth: `tasks/todo.md`
- Only unchecked tasks will be planned.
- Execution will be one task at a time, with tests run after each task and user validation required before proceeding.

## Task List (Checkbox Plan)

- [x] Task 1: Add SQL for intraday volatility in `sql/analytics_queries.sql`.
  - Implement query: `(high - low) / NULLIF(open, 0)` for "today".
  - Ensure query returns required columns with clear aliases.
  - Add/adjust analytics tests to validate columns and ordering.
  - Run tests and capture logs under `artifacts/logs/`.

- [x] Task 2: Add SQL for 5-day average volume in `sql/analytics_queries.sql`.
  - Implement 5-day rolling average per ticker.
  - Add volume ratio vs today volume.
  - Add/adjust analytics tests for correctness and columns.
  - Run tests and capture logs under `artifacts/logs/`.
  - 5-day volume fallback:
    - Trigger when a ticker has fewer than 5 daily rows in SQLite for the latest window.
    - Fetch VnStock history with `Quote.history(interval="1D", length=10)` using source `VCI`.
    - Compute 5-day average from the most recent 5 rows and override `avg_5d_volume` and `volume_ratio`.
    - If VnStock returns no usable rows, keep SQLite-derived values.
    - Do not persist fallback data into SQLite.
    - Rate limit handling:
      - VnStock limits are 60 requests/minute and 3000 requests/hour.
      - On rate limit errors (HTTP 429 or `RateLimitExceed`), wait a cooldown period before retrying.
      - Use exponential backoff starting at 15 seconds (per VnStock guidance) with a max of 3 attempts.
      - If all retries fail, keep SQLite-derived values.

- [x] Task 3: Build dark-themed HTML report template using Jinja + Tailwind.
  - Update `src/templates/report.j2` to include table + styling.
  - Ensure columns match: Ticker, Open, High, Low, Volatility %, Today Volume, 5-Day Avg Volume, Volume Ratio.
  - Add a note in the report explaining `volume_ratio = today_volume / avg_5d_volume`.
  - Keep template data bindings stable and documented.
  - Add/adjust template tests if present.
  - Run tests and capture logs under `artifacts/logs/`.

- [ ] Task 4: Generate report file `output/report-%YY%mm%dd.html`.
  - Reuse SQL queries + Jinja template.
  - Ensure output file naming format and date formatting.
  - Add/adjust tests for file generation and content.
  - Run tests and capture logs under `artifacts/logs/`.

## Execution Protocol
- Ask for approval before starting Task 1.
- After each task: run tests, save logs to `artifacts/logs/`, present results.
- Wait for user validation before proceeding to the next task.
