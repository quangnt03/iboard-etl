"""Pydantic model for application configuration.

Keyword arguments:
None."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AppConfig(BaseModel):
    """Store runtime configuration for the pipeline.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    ssi_iboard_endpoint: str
    database_path: Path
    schema_path: Path
    analytics_sql_path: Path
    report_template_path: Path
    report_output_dir: Path
    request_timeout_seconds: float
    max_retries: int
    retry_cooldown_seconds: float
    log_path: Path
    vnstock_api_key: str | None = None
    use_vnstock_fallback: bool = True
    persist_vnstock_fallback: bool = False
