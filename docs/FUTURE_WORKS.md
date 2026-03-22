# Future works

## Limitations

Current MVP limitations:

- SQLite is not intended for high-concurrency production workloads
- no Airflow scheduling yet
- no dbt layer yet
- no Docker packaging by default
- no BI integration yet
- no streaming ingestion yet

The further works will include:

## Airflow

Add orchestration for:

- fetch task
- validate task
- load task
- quality task
- analytics task
- publish task

## dbt

A later dbt version would be a good fit once the project moves to PostgreSQL or a warehouse.

In that version:

- Python handles API ingestion,
- raw/staging tables are loaded,
- dbt manages transformations and tests,
- and analytics marts feed dashboards.

## PostgreSQL

Replace SQLite with PostgreSQL for stronger concurrency, more realistic production behavior, and better integration with BI tools.

## Docker

Add containerized execution for reproducibility and deployment simplicity.

## CI/CD

Add GitHub Actions or similar pipelines for:

- linting,
- tests,
- packaging,
- and deployment checks.
