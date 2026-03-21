# HTTP Fetch Refactor Plan

## Objective

Replace JSON file-based population with an HTTP fetch flow that reuses the current 3-tier architecture.

## Scope

1. Add runtime configuration for HTTP fetching and logging.
2. Implement a class-based fetcher in `src/ingest.py`.
3. Update service and controller layers to fetch, validate, persist, and return structured results.
4. Add basic per-run logging.
5. Add tests for fetch success, retry/failure handling, and controller/service orchestration.

## Constraints

- Keep the current narrowed VN30 schema and SQL table unchanged.
- Use class-based design within the existing controller/service/repository split.
- Use Python standard library HTTP tooling unless a project-standard client already exists.
