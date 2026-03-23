"""VnStock history wrapper for volume lookups.

Keyword arguments:
None."""

from __future__ import annotations

from datetime import datetime
import logging
import math
import time
from typing import Iterable

import pandas as pd
from pydantic import BaseModel, ConfigDict
from vnstock import Quote, register_user


class VnStockHistoryRow(BaseModel):
    """Represent a single OHLCV history row from VnStock.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    time: datetime
    volume: int
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    avg: float | None = None


class VnStockHistoryResult(BaseModel):
    """Represent normalized VnStock history output.

Keyword arguments:
None."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    source: str
    rows: list[VnStockHistoryRow]

_REGISTERED_API_KEY: str | None = None


def _ensure_registered(api_key: str | None) -> None:
    """Register vnstock API key once per process if provided.

Keyword arguments:
api_key -- The api key."""

    global _REGISTERED_API_KEY
    if not api_key:
        return
    if _REGISTERED_API_KEY == api_key:
        return
    try:
        register_user(api_key=api_key)
    except Exception as exc:  # noqa: BLE001 - external API error surface is inconsistent
        logging.getLogger("finhay.vnstock").warning(
            "vnstock_register_failed api_key_set=%s error=%s",
            bool(api_key),
            exc,
        )
        return
    _REGISTERED_API_KEY = api_key


def _is_rate_limit_error(exc: Exception) -> bool:
    """Detect whether an exception indicates rate limiting.

Keyword arguments:
exc -- The exception to inspect.
"""

    message = str(exc).lower()
    return (
        "ratelimit" in message
        or "rate limit" in message
        or "429" in message
    )


def _is_connection_error(exc: Exception) -> bool:
    """Detect whether an exception indicates a connection failure.

Keyword arguments:
exc -- The exception to inspect.
"""

    message = str(exc).lower()
    return any(
        token in message
        for token in (
            "connection",
            "connect",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "temporary failure",
            "name resolution error",
            "name or service not known",
            "gaierror",
            "dns",
            "connection reset",
            "refused",
            "failed to resolve",
            "getaddrinfo failed",
        )
    )


def _parse_rows(rows: Iterable[dict[str, object]]) -> list[VnStockHistoryRow]:
    """Convert raw row mappings into typed history rows.

Keyword arguments:
rows -- Iterable of raw row dictionaries with `time` and `volume`."""

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

Keyword arguments:
symbol -- Stock symbol to query.
source -- Data source name (e.g., "VCI" or "KBS").
length_days -- Lookback length in days.
api_key -- (default None) (default None)"""

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
            if _is_rate_limit_error(exc) and attempt < max_attempts:
                time.sleep(cooldown_seconds)
                cooldown_seconds *= 2
                continue
            if _is_connection_error(exc):
                logging.getLogger("finhay.vnstock").warning(
                    "vnstock_connection_failed symbol=%s source=%s error=%s",
                    symbol,
                    source,
                    exc,
                )
                return VnStockHistoryResult(symbol=symbol, source=source, rows=[])
            raise

    return VnStockHistoryResult(symbol=symbol, source=source, rows=[])
