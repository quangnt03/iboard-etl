"""Run metrics models for daily pipeline execution logs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunMetricsArtifacts(BaseModel):
    """Represent artifact paths produced by the pipeline run."""

    model_config = ConfigDict(frozen=True)

    quality_report: str | None
    analytics_report: str | None


class RunMetrics(BaseModel):
    """Represent the daily pipeline run metrics payload."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    source: str
    dataset: str
    started_at: datetime
    finished_at: datetime
    duration_seconds: float
    status: str
    rows_fetched: int
    rows_validated: int
    rows_inserted: int
    rows_skipped: int
    rows_failed_validation: int
    quality_failures_by_rule: dict[str, int]
    artifacts: RunMetricsArtifacts
