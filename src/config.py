"""Application configuration loader."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from src.models.app_config import AppConfig

load_dotenv(find_dotenv(filename=".env.local"))

CONFIG = AppConfig(
    ssi_iboard_endpoint=os.getenv("BASE_URL", "https://iboard-query.ssi.com.vn/stock/group/VN30"),
    database_path=Path(os.getenv("DB_PATH", "data/stocks.db")),
    schema_path=Path(os.getenv("SCHEMA_PATH", "sql/schema.sql")),
    analytics_sql_path=Path(os.getenv("ANALYTICS_SQL_PATH", "sql/analytics_queries.sql")),
    report_template_path=Path(os.getenv("REPORT_TEMPLATE_PATH", "src/templates/report.j2")),
    report_output_dir=Path(os.getenv("REPORT_OUTPUT_DIR", "output")),
    request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30.0")),
    max_retries=int(os.getenv("MAX_RETRIES", "3")),
    retry_cooldown_seconds=float(os.getenv("RETRY_COOLDOWN_SECONDS", "2.0")),
    log_path=Path(os.getenv("LOG_PATH", "logs/pipeline.log")),
)
