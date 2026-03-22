# 🧠 Project Context

> **First Principle**: AI Agent capability = context quality. Architecture = files.

## Cognitive Loop

```
Think → Act → Reflect → Evolve
 ↑                        |
 └────────────────────────┘
```

| Phase | Rule | Output |
|:------|:-----|:-------|
| **Think** | Plan before coding a whole feature. Reason through tradeoffs. | `artifacts/plan_*.md` |
| **Act** | Clean, typed, documented code. | Source files |
| **Reflect** | Test. Verify. Save evidence. | `artifacts/logs/` |
| **Evolve** | Document mistakes. Extract prevention rules. | `artifacts/error_journal.md` |

## Project Structure

```text
project/
|-- src/
|   |-- __init__.py
|   |-- analytics.py
|   |-- config.py
|   |-- db.py
|   |-- ingest.py
|   |-- quality_check.py
|   |-- analytics.py
|   |-- transform.py
|   |-- utils.py
|   |-- controller/
|   |   `-- analytics_controller.py
|   |-- models/
|   |   |-- analytics.py
|   |   |-- app_config.py
|   |   |-- quality_rules.py
|   |   `-- vn30_stock.py
|   |-- repository/
|   |   |-- analytics_repository.py
|   |   `-- vn30_repository.py
|   |-- service/
|   |   |-- analytics_service.py
|   |   `-- vn30_service.py
|   `-- templates/
|       `-- report.j2
|-- scripts/
|   `-- cli.py
|-- sql/
|   |-- analytics_queries.sql
|   |-- indexes.sql
|   `-- schema.sql
|-- output/
|   |-- data_quality_report.json
|   `-- report-YYYYmmdd.html
|-- logs/
|   `-- pipeline.log
|-- tests/
|   |-- test_analytics.py
|   |-- test_cli_menu.py
|   |-- test_ingest.py
|   |-- test_ingest_cli.py
|   |-- test_pipeline_quality_gate.py
|   |-- test_quality_check.py
|   |-- test_quality_check_cli.py
|   |-- test_report_generation.py
|   |-- test_report_cli.py
|   |-- test_report_template.py
|   `-- test_service_controller.py
|-- main.py
|-- README.md
|-- CONTEXT.md
`-- AGENTS.md
```

## Running

- Full pipeline: `python main.py`
- Interactive CLI: `python scripts/cli.py`
- Fetch + optional DB write: `python src/ingest.py`
- Quality checks (fresh fetch): `python src/quality_check.py`
- Generate report: `python src/analytics.py`

## Tests

- Run all: `.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Single file: `.venv\Scripts\python.exe -m unittest tests.test_quality_check -v`

## Coding Standards

- **Type hints** on all functions
- **Google-style docstrings** on all functions/classes
- **Pydantic** for data models
- **Tool encapsulation** for external APIs
- **No silent exceptions**

## Self-Evolution

The architecture learns from mistakes:
1. Bug found → document in `artifacts/error_journal.md`
2. Lesson generalizable → extract into `.antigravity/rules.md`
3. Before acting → scan error journal for relevant past failures
4. **Never repeat a documented mistake**
