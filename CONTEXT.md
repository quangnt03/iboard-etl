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

```plaintext
project/
├── src/
│   ├── config.py
│   ├── db.py
│   ├── ingest.py
│   ├── transform.py
│   ├── quality_check.py
│   ├── analytics.py
│   ├── report.py
│   ├── schemas.py
│   └── utils.py
├── sql/
│   ├── schema.sql
│   ├── indexes.sql
│   └── analytics_queries.sql
├── output/
│   ├── data_quality_report.json
│   └── analytics_output.html
├── logs/
│   └── pipeline.log
├── tests/
│   ├── test_transform.py
│   ├── test_quality.py
│   ├── test_analytics.py
│   └── test_schemas.py
├── main.py
└── README.md
```

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
