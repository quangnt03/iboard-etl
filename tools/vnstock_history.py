"""VnStock history wrapper for volume lookups."""

from __future__ import annotations

from datetime import datetime
import math
import time
from typing import Iterable

import pandas as pd
from pydantic import BaseModel, ConfigDict
from vnstock import Quote, register_user


class VnStockHistoryRow(BaseModel):
    """Represent a single OHLCV history row from VnStock."""

    model_config = ConfigDict(frozen=True)

    time: datetime
    volume: int
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    avg: float | None = None


class VnStockHistoryResult(BaseModel):
    """Represent normalized VnStock history output."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    source: str
    rows: list[VnStockHistoryRow]

_REGISTERED_API_KEY: str | None = None


def _ensure_registered(api_key: str | None) -> None:
    """Register vnstock API key once per process if provided."""

    global _REGISTERED_API_KEY
    if not api_key:
        return
    if _REGISTERED_API_KEY == api_key:
        return
    register_user(api_key=api_key)
    _REGISTERED_API_KEY = api_key


def _parse_rows(rows: Iterable[dict[str, object]]) -> list[VnStockHistoryRow]:
    """Convert raw row mappings into typed history rows.

    Args:
        rows: Iterable of raw row dictionaries with `time` and `volume`.

    Returns:
        List of typed history rows.
    """

    parsed: list[VnStockHistoryRow] = []
    for row in rows:
        if "time" not in row or "volume" not in row:
            continue
        normalized = dict(row)
        for key in ("open", "high", "low", "close", "avg"):
            value = normalized.get(key)
            if isinstance(value, float) and math.isnan(value):
                normalized[key] = None
        parsed.append(VnStockHistoryRow.model_validate(normalized))
    return parsed


def fetch_history(
    symbol: str,
    source: str,
    length_days: int,
    api_key: str | None = None,
) -> VnStockHistoryResult:
    """Fetch daily OHLCV history from VnStock for a symbol.

    Args:
        symbol: Stock symbol to query.
        source: Data source name (e.g., "VCI" or "KBS").
        length_days: Lookback length in days.

    Returns:
        Normalized history rows with time and volume.
    """

    _ensure_registered(api_key)
    quote = Quote(symbol=symbol, source=source)
    cooldown_seconds = 15
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            frame: pd.DataFrame = quote.history(length=length_days, interval="1D")
            if frame.empty:
                rows = []
            else:
                desired_columns = ["time", "open", "high", "low", "close", "avg", "volume"]
                available = [column for column in desired_columns if column in frame.columns]
                rows = frame[available].to_dict(orient="records")
            return VnStockHistoryResult(symbol=symbol, source=source, rows=_parse_rows(rows))
        except Exception as exc:  # noqa: BLE001 - external API error surface is inconsistent
            message = str(exc).lower()
            is_rate_limit = ( 
                "ratelimit" in message 
                or "rate limit" in message 
                or "Rate limit" in message 
                or "429" in message
            )
            if not is_rate_limit or attempt == max_attempts:
                raise
            time.sleep(cooldown_seconds)
            cooldown_seconds *= 2

    return VnStockHistoryResult(symbol=symbol, source=source, rows=[])
