# CLI Manual

## Run the interactive CLI menu

Run the interactive menu (quality-gated pipeline included):

```bash
python main.py
```

Menu options:

```bash
1. Run full pipeline (quality-gated)
2. Fetch records (optional DB write)
3. Run quality check (fresh fetch)
4. Generate analytics report from DB
5. Exit
```

## Run CLI tools directly (optional)

Fetch VN30 data from the API:

```bash
python src/ingest.py --help
python src/ingest.py --api-url https://iboard-query.ssi.com.vn/stock/group/VN30
python src/ingest.py --output-json output/vn30_snapshot.json --limit 10
python src/ingest.py --no-db-write
```

Run quality checks on a fresh API fetch:

```bash
python src/quality_check.py --help
python src/quality_check.py --report-dir logs
```

Generate the analytics HTML report:

```bash
python src/analytics.py --help
python src/analytics.py --output-path output/report-YYYYmmdd.html
```

## Run the current automated tests

Run the full test suite with the project virtual environment:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run a single test module:

```bash
.venv\Scripts\python.exe -m unittest tests.test_ingest -v
```

```bash
.venv\Scripts\python.exe -m unittest tests.test_service_controller -v
```

## Testing

A lightweight `unittest` suite is included in the repository.

- `tests/test_ingest.py`
  - successful HTTP payload parsing
  - retry behavior on HTTP 429
  - malformed JSON handling
  - empty `data` handling
- `tests/test_service_controller.py`
  - service success/failure result handling
  - repository upsert idempotency
  - controller orchestration over the 3-tier flow

### How to execute tests

Run all tests:

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run one file:

```bash
.venv\Scripts\python.exe -m unittest tests.test_ingest -v
```

```bash
.venv\Scripts\python.exe -m unittest tests.test_service_controller -v
```

## Expected result

All tests should complete with `OK`.
