# HTTP Fetch Refactor Plan

## Objective

Replace JSON file-based population with an HTTP fetch flow that reuses the current 3-tier architecture.

## Scope

1. Add runtime configuration for HTTP fetching and logging.
2. Implement a class-based fetcher in `src/ingest.py`.
3. Update service and controller layers to fetch, validate, persist, and return structured results.
4. Make the fetcher CLI persist to SQLite by default, with a CLI flag to skip DB writes.
5. Add a CLI menu option to fetch records and optionally skip SQLite writes.
6. Add basic per-run logging.
7. Add trading-hours-aware fetch behavior:
   - During trading hours, always activate the fetcher to keep prices fresh.
   - Outside trading hours, check SQLite for the latest record timestamp; if not current, run the fetcher once.
8. Add an `updated_at` field in the SQLite schema to track last update time per record.
9. Add tests for fetch success, retry/failure handling, controller/service orchestration, the trading-hours/DB freshness logic, and `updated_at` persistence.

## Constraints

- Keep the current narrowed VN30 schema and SQL table unchanged.
- Use class-based design within the existing controller/service/repository split.
- Use Python standard library HTTP tooling unless a project-standard client already exists.
- Trading-hours logic should use the configured trading timezone (ICT) and be deterministic for tests (injectable clock).
- Schema update should be backward compatible for existing data (default `updated_at` when missing).
