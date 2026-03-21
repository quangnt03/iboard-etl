# Pipeline Initialization Plan

## Objective

Establish a clean, implementation-ready baseline for the Finhay data pipeline before building business logic.

## Current State

- The repository contains partial `src/` stubs.
- `tasks/todo.md` and `tasks/lessons.md` are empty.
- The current folder layout does not fully match the documented target structure.
- `test/` exists, while the documented structure expects `tests/`.
- `log/` exists, while the documented structure expects `logs/`.
- `main.py`, several `src/` modules, and SQL files are missing.

## Scope For This Initialization Step

1. Create planning artifacts required by the workspace workflow.
2. Normalize repository scaffolding to match the intended project structure.
3. Avoid destructive cleanup of legacy folders until implementation confirms they are unused.

## Deliverables

- `artifacts/plan_pipeline_init.md`
- `tasks/todo.md` with checkable execution and verification steps
- `artifacts/logs/` directory for captured command output
- normalized placeholder scaffolding for:
  - `main.py`
  - missing `src/` modules
  - `sql/` files
  - `tests/` directory
  - `logs/` directory

## Decisions

- Keep legacy `test/` and `log/` directories in place for now to avoid destructive changes.
- Create the canonical `tests/` and `logs/` directories and use those going forward.
- Add minimal placeholder files where structure is missing, without implementing pipeline behavior yet.

## Risks

- The absent `.context/coding_style.md` means local style enforcement is inferred from repository instructions.
- Placeholder scaffolding reduces ambiguity, but functional implementation still needs explicit verification.

## Next Implementation Phase

1. Build configuration and utilities.
2. Implement ingestion and schema validation.
3. Implement persistence and SQL bootstrap.
4. Implement quality checks, analytics, and HTML reporting.
5. Add tests and save verification logs under `artifacts/logs/`.
