"""Pydantic model for application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class AppConfig(BaseModel):
    """Store runtime configuration for the pipeline.

    Attributes:
        ssi_iboard_endpoint: Source API endpoint for VN30 quotes.
        database_path: SQLite database file path.
        schema_path: SQL schema file path used to initialize the database.
        analytics_sql_path: SQL file containing analytics queries.
        report_template_path: Jinja template path for HTML report.
        report_output_dir: Directory for generated HTML reports.
        request_timeout_seconds: HTTP timeout for the VN30 endpoint.
        max_retries: Maximum number of fetch attempts for transient failures.
        retry_cooldown_seconds: Delay between retry attempts.
        log_path: Application log file path.
    """

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
