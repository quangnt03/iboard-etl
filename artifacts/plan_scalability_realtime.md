# Plan: Scalable Real-Time Pipeline (1,000 Investors)

## Goal
Redesign the pipeline to serve 1,000 investor dashboards in real time (<=1s latency) with a managed cloud stack.

## Target Stack
- GCP BigQuery for analytics storage
- dbt for transformations/modeling
- Streaming/batching with PySpark or Flink
- Orchestration with Airflow
- Kafka as the event bus

## Architecture Overview
- Ingestion service pulls from the market API and publishes events to Kafka.
- Stream processor (Flink/PySpark structured streaming) computes rolling metrics and writes to BigQuery.
- dbt models build curated datasets and derived metrics.
- Cache layer (e.g., Redis) stores hot aggregates for fast dashboard reads.
- Push gateway (WebSocket/stream) delivers updates to dashboards/agents.
- Airflow schedules batch backfills, dbt runs, and health checks.

## Data Flow (High Level)
1. Fetch -> normalize -> publish to Kafka
2. Streaming compute -> BigQuery (raw + aggregates)
3. dbt -> curated models
4. Cache -> dashboard APIs
5. Push -> user dashboards/agents

## API/Schema Updates
- Define event schema for Kafka (tick, aggregate, quality flags).
- Define push payload schema for dashboards.

## Non-Functional
- SLA: <=1s end-to-end latency
- Multi-tenant isolation at delivery (filters/watchlists)
- Observability: lag, latency, error rates, delivery success

## Tests
- Load test 1,000 concurrent connections
- Failover tests for API and Kafka
- Backfill + replay verification
