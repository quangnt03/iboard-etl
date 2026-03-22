# Pipeline Todo

- [x] Implement CLI `main()` function with parameters for `src/ingest.py` and `src/quality_checks.py` to run in standalone mode in command line
- [ ] Write a SQL in the `src/sql/analytic_queries.sql` to calculate intraday volatility of stock and answer the question "Which stocks had the highest intraday volatility (high − low) / open price today?”
- [ ] Write a SQL in the `src/sql/analytic_queries.sql` to calculate average volume in 5-day window of stock and answer the question "How does their volume compare to their 5-day average?"
- [ ] Use Jinja and tailwindcss to create a report template in HTML (`src/templates/report.j2`), contain a dark-themed tableSorted by volatility descending, top 10. Columns: Ticker, Open, High, Low, Volatility %, Today Volume, 5-Day Avg Volume, Volume Ratio
- [ ] Reuse the above queries in `src/sql/analytic_queries.sql` and Jinja template to generate a report file named 'output/report-%YY%mm%dd.html', contain a dark-themed tableSorted by volatility descending, top 10. Columns: Ticker, Open, High, Low, Volatility %, Today Volume, 5-Day Avg Volume, Volume Ratio

- [x] Inspect repository state and documented target architecture.
- [x] Create initialization artifact plan in `artifacts/plan_pipeline_init.md`.
- [x] Identify scaffolding mismatches against the documented structure.
- [x] Create canonical `tests/` directory without deleting legacy `test/`.
- [x] Create canonical `logs/` directory without deleting legacy `log/`.
- [x] Create `artifacts/logs/` for captured verification output.
- [x] Add missing top-level entrypoint scaffold in `main.py`.
- [x] Add missing module scaffolding in `src/`.
- [x] Add missing SQL scaffolding in `sql/`.
- [x] Write Pydantic schema for API response
- [x] Create SQLite/DAO implementation artifact plan.
- [x] Create database population artifact plan.
- [x] Create three-tier refactor artifact plan.
- [x] Populate pipeline configuration: `BASE_API`, SQLite connections
- [x] Initialize SQLite connection layer and DAO CRUD operations
- [x] Refactor code into controller/service/repository layers
- [x] Initialize logging function, format, configurations, and decorators
- [x] Implement, ingestion, validation, persistence, analytics, and reporting.
- [x] Populate SQLite from `VN30.json`
- [x] Add automated tests for schemas, transforms, quality checks, and analytics.
- [x] Run `unittest` and save output under `artifacts/logs/`.
- [x] Run the pipeline entrypoint and save execution output under `artifacts/logs/`.
- [x] Add schema validation, fallback rules, retry on API Blocks (when getting 403 Forbidden)  
- [x] Add a review section summarizing results, risks, and follow-up work.

## Review

- Initialization completed.
- HTTP fetch flow now replaces JSON-file population as the primary ingestion path.
- The application uses the current 3-tier structure: controller -> service -> repository.
- Verification completed with `unittest` and a live entrypoint run.
- `pytest` was not run; the repo currently has `unittest`-based coverage for this change.
