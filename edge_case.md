# Edge Case Plan: Real-Time Scaling for 1,000 Investor Dashboards

## Scenario

“Imagine 1,000 Finhay investors each want this data piped into their own personal AI agent dashboard. How would you redesign this pipeline to serve them all in real-time?”

## Expected Stack

- GCP BigQuery: Central data warehouse. Stores curated and historical data, supports SQL analytics, and serves as the source of truth for reporting and downstream use cases.
- dbt: Transformation layer in the warehouse. Turns raw/staged data into clean, modeled tables with tested, version-controlled SQL and documentation.
- Streaming/batching (PySpark or Flink): Compute layer for data processing. Ingests, cleans, joins, and aggregates data at scale; streaming for near-real-time, batching for periodic bulk processing.
- Orchestration (Airflow): Workflow scheduler. Defines, schedules, and monitors pipelines; manages dependencies, retries, SLAs, and alerts.
- Kafka event bus: Real-time message backbone. Decouples producers and consumers, buffers spikes, and delivers streaming data reliably to multiple downstream systems.

## Target Architecture (High Level)

1. **Ingestion**
   - A stateless fetcher service pulls SSI/VN30 data and publishes normalized events into Kafka.
2. **Streaming Compute**
   - Flink streaming jobs compute real-time aggregates (volatility, volume ratios) and write to BigQuery + cache.
3. **Batch + Modeling**
   - dbt builds curated datasets in BigQuery for analytics and historical reporting.
4. **Delivery**
   - WebSocket/stream gateway pushes updates to each dashboard with per-user filters (watchlists/alerts).
5. **Orchestration**
   - Airflow schedules backfills, dbt runs, SLA checks, and health monitoring.

## Data Flow

1. Fetch -> validate -> Kafka topic
2. Stream compute -> BigQuery (raw + aggregates)
3. dbt -> curated models
4. Cache -> push updates to dashboards

## Key Redesign Decisions

- Replace SQLite with BigQuery for scalable analytics storage.
- Use Kafka for decoupled ingestion and fanout.
- Use streaming compute for <=1s latency.
- Use dbt for consistent transformations across batch and streaming outputs.

## Multi-Tenant Strategy

- Keep core data shared across users.
- Apply personalization at the delivery layer (watchlists, alerts, filters).
- Avoid per-user compute in the core pipeline.

## Observability and Reliability

- Metrics: event lag, end-to-end latency, push success rate.
- Retry and dead-letter handling for Kafka consumers.
- Cache fallback for temporary outages.

## Rollout Plan

1. Stand up Kafka + streaming job.
2. Mirror existing SQL outputs in BigQuery.
3. Validate metrics vs current pipeline.
4. Cut over dashboards to push gateway.

## Files to Update (Current Repo)

- `src/ingest.py` (replace direct fetch->SQLite with publish->Kafka)
- `src/service/analytics_service.py` (consume streaming outputs)
- `src/repository/analytics_repository.py` (BigQuery access)
- `sql/analytics_queries.sql` (dbt models as SQL sources)
- `scripts/pipeline.py` (Airflow orchestration target)
