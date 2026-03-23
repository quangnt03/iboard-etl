# Clean Code Documentation Plan

## Goal
Add concise docstrings and explanatory comments across source files to reduce maintenance and improve scalability.

## Scope
- Python sources: `src/`, `scripts/`, `tools/`, `tests/`
- SQL sources: `sql/`

## Plan
1. Inventory all `.py` files in scope and all `.sql` files in `sql/`.
2. For each Python module, add module-level docstring if missing.
3. For each Python class/function/config, add a concise Google-style docstring if missing; add brief explanatory comments only where logic is non-obvious.
4. For each SQL file, add inline comments for each CTE and metric calculation.
5. Run `unittest` and save output to `artifacts/logs/`.

## Notes
- Keep comments short and non-redundant.
- Preserve existing docstrings; only add where missing or unclear.
- Use ASCII-only comments unless the file already uses non-ASCII.
