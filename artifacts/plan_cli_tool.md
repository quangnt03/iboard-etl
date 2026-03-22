## Plan: CLI Delegation to main.py

### Goal

Keep `scripts/cli.py` as the CLI implementation and migrate the core CLI entrypoint into `main.py` so that `main.py` delegates to `scripts/cli.py`. Preserve `run_pipeline` re-export in `main.py`.

### Scope

- Keep `scripts/pipeline.py` as the pipeline orchestration module.
- Update `main.py` to delegate to `scripts/cli.py` for the CLI entrypoint.
- Ensure `scripts/cli.py` remains CLI-only (no pipeline definition).
- Preserve `run_pipeline` import/export in `main.py` for tests.

### Steps

- [x] Extract pipeline orchestration into `scripts/pipeline.py`.
- [x] Keep `scripts/cli.py` importing from `scripts/pipeline.py`.
- [x] Update `main.py` to delegate CLI execution to `scripts/cli.py`.
- [x] Verify `main.py` still re-exports `run_pipeline`.
- [ ] Run targeted tests (`tests/test_pipeline_quality_gate.py`) if requested.

### Risks & Notes

- Avoid circular imports: `main.py` can import `scripts/cli.py`, but `scripts/cli.py` must not import `main.py`.
- Preserve `run_pipeline` signature and re-export to keep tests stable.
