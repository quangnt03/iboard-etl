"""Shared utility helpers."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path


def resolve_daily_log_path(log_path: Path) -> Path:
    """Resolve a daily log file path from a base log path.

    Example:
        `logs/pipeline.log` -> `logs/pipeline_2026-03-21.log`
    """

    current_date = datetime.now().strftime("%Y-%m-%d")
    return log_path.with_name(f"{log_path.stem}_{current_date}{log_path.suffix}")


def get_logger(log_path: Path, logger_name: str = "finhay.pipeline") -> logging.Logger:
    """Build or reuse a file-backed logger for the pipeline.

    Args:
        log_path: Base destination log file path.
        logger_name: Stable logger name.

    Returns:
        A configured logger that writes to a daily log file derived from `log_path`.
    """

    daily_log_path = resolve_daily_log_path(log_path)
    daily_log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    resolved_path = str(daily_log_path.resolve())
    for handler in list(logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            continue
        if handler.baseFilename == resolved_path:
            return logger
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(daily_log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
