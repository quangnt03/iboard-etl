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

---

## Plan: Daily Run Metrics Log

### Goal

Emit a JSON metrics log file under `logs/` for each full pipeline run with filename
`run_pipeline_%dd%mm%yy.json`, matching the provided schema.

### Scope

- Only generate when running the full pipeline end-to-end.
- Store metrics in a single JSON file per day (overwrite if multiple runs on same day).
- Capture counts and rule failures from the quality check stage.
- Include artifact paths for quality report and analytics report.

### Steps

- [ ] Add a Pydantic model for the run metrics payload (schema in request).
- [ ] Extend pipeline orchestration to track:
  - start time, finish time, duration
  - rows fetched, validated, inserted, skipped, failed validation
  - quality failures by rule
- [ ] Write a JSON file to `logs/run_pipeline_%dd%mm%yy.json` after pipeline completes.
- [ ] Add logging around metrics write success/failure.
- [ ] Update docs with the new metrics log output.
- [ ] Add or extend tests if requested.

### Risks & Notes

- Ensure time formatting uses local timezone and ISO 8601.
- Avoid partial writes if the pipeline fails mid-run (still emit status=failed with best-effort metrics).
