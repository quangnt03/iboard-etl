"""Shared utility helpers.

Keyword arguments:
None."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from src.config import CONFIG
from tools.vnstock_history import VnStockHistoryResult, fetch_history as fetch_vnstock_history


def resolve_daily_log_path(log_path: Path) -> Path:
    """Resolve a daily log file path from a base log path.

Keyword arguments:
log_path -- The log path."""

    # Append the current date to the base filename for daily logs.
    current_date = datetime.now().strftime("%Y-%m-%d")
    return log_path.with_name(f"{log_path.stem}_{current_date}{log_path.suffix}")


def get_logger(log_path: Path, logger_name: str = "finhay.pipeline") -> logging.Logger:
    """Build or reuse a file-backed logger for the pipeline.

Keyword arguments:
log_path -- Base destination log file path.
logger_name -- Stable logger name. (default 'finhay.pipeline') (default 'finhay.pipeline')"""

    # Resolve the per-day log path and ensure the directory exists.
    daily_log_path = resolve_daily_log_path(log_path)
    daily_log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Reuse an existing file handler if it already targets the daily log file.
    resolved_path = str(daily_log_path.resolve())
    for handler in list(logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            continue
        if handler.baseFilename == resolved_path:
            return logger
        logger.removeHandler(handler)
        handler.close()

    # Attach a new file handler for the resolved daily log file.
    file_handler = logging.FileHandler(daily_log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger


def fetch_volume_history(symbol: str, source: str, length_days: int) -> VnStockHistoryResult:
    """Fetch VnStock daily volume history for a symbol.

Keyword arguments:
symbol -- Stock symbol to query.
source -- Data source name (e.g., "VCI" or "KBS").
length_days -- Lookback length in days."""

    # Delegate to the VnStock client wrapper using the configured API key.
    return fetch_vnstock_history(
        symbol=symbol,
        source=source,
        length_days=length_days,
        api_key=CONFIG.vnstock_api_key,
    )
