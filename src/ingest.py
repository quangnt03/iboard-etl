"""HTTP ingestion helpers for VN30 payloads.

Keyword arguments:
None."""

from __future__ import annotations

import argparse
import json
import sys
import socket
import time
from pathlib import Path
from http import HTTPStatus
from typing import Any
from urllib import error, request

from pydantic import ValidationError

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config import CONFIG, AppConfig
from src.models.vn30_stock import VN30ApiResponse, VN30Record
from src.repository.vn30_repository import SQLiteConnectionManager, VN30Repository
from src.utils import get_logger


class FetchError(Exception):
    """Represent a non-recoverable VN30 fetch failure.

Keyword arguments:
None."""


class VN30Fetcher:
    """Fetch and validate VN30 data from the configured HTTP endpoint.

Keyword arguments:
None."""

    def __init__(
        self,
        api_url: str,
        timeout_seconds: float,
        max_retries: int,
        retry_cooldown_seconds: float,
    ) -> None:
        """Initialize the fetcher runtime settings.

Keyword arguments:
self -- The self.
api_url -- The api url.
timeout_seconds -- The timeout seconds.
max_retries -- The max retries.
retry_cooldown_seconds -- The retry cooldown seconds."""

        self.api_url = api_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_cooldown_seconds = retry_cooldown_seconds
        self.logger = get_logger(CONFIG.log_path)

    def fetch_payload(self) -> dict[str, Any]:
        """Execute an HTTP GET and decode the JSON payload.

Keyword arguments:
self -- The self."""

        # Prepare the HTTP request with a stable user agent for API tracking.
        http_request = request.Request(
            self.api_url,
            headers={"Accept": "application/json", "User-Agent": "finhay-test/1.0"},
            method="GET",
        )
        try:
            # Read the raw response body as text for JSON decoding.
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except socket.timeout as exc:
            self.logger.error("API timeout: source_url=%s", self.api_url)
            raise TimeoutError("VN30 API request timed out.") from exc
        except error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                self.logger.error("API timeout: source_url=%s", self.api_url)
                raise TimeoutError("VN30 API request timed out.") from exc
            self.logger.error("API transport error: source_url=%s error=%s", self.api_url, exc)
            raise
        except Exception as e:
            self.logger.error("API internal error: source_url=%s error=%s", self.api_url, exc)

        # Decode the JSON payload and validate its top-level shape.
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self.logger.error("Malformed API response: source_url=%s", self.api_url)
            raise FetchError("VN30 API returned malformed JSON.") from exc

        if not isinstance(payload, dict):
            self.logger.error("Malformed API response: source_url=%s", self.api_url)
            raise FetchError("VN30 API returned a non-object JSON payload.")
        return payload

    def parse_response(self, payload: dict[str, Any]) -> list[VN30Record]:
        """Validate the API payload into typed VN30 records.

Keyword arguments:
self -- The self.
payload -- The payload."""

        # Validate and normalize API payload with Pydantic schema.
        try:
            response = VN30ApiResponse.model_validate(payload)
        except ValidationError as exc:
            self.logger.error("Malformed API response: source_url=%s", self.api_url)
            raise FetchError("VN30 API payload failed schema validation.") from exc

        if response.code.upper() != "SUCCESS":
            self.logger.error(
                "Malformed API response: source_url=%s code=%s",
                self.api_url,
                response.code,
            )
            raise FetchError(f"VN30 API returned non-success code: {response.code}")
        if not response.data:
            self.logger.error("Empty API data: source_url=%s", self.api_url)
            raise FetchError("VN30 API returned an empty data set.")
        return response.data

    def fetch_records(self) -> list[VN30Record]:
        """Fetch records with retry handling for transient failures.

Keyword arguments:
self -- The self."""

        # Retry transient failures and log retry attempts for observability.
        last_error: Exception | None = None
        self.logger.info(
            "fetch_records_start source_url=%s max_retries=%s timeout_seconds=%s",
            self.api_url,
            self.max_retries,
            self.timeout_seconds,
        )
        for attempt in range(1, self.max_retries + 1):
            try:
                payload = self.fetch_payload()
                records = self.parse_response(payload)
                self.logger.info(
                    "fetch_records_success source_url=%s records=%s attempt=%s",
                    self.api_url,
                    len(records),
                    attempt,
                )
                return records
            except error.HTTPError as exc:
                last_error = exc
                # Retry on rate limit or server errors; fail fast otherwise.
                if not self._should_retry_http_status(exc.code) or attempt == self.max_retries:
                    raise FetchError(
                        f"VN30 API request failed with HTTP status {exc.code}."
                    ) from exc
            except (TimeoutError, error.URLError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    # Emit a distinct message for connection failures on final retry.
                    if self._is_connection_error(exc):
                        self.logger.error(
                            "API connection failed after retries: source_url=%s error=%s",
                            self.api_url,
                            exc,
                        )
                    message = (
                        "VN30 API connection failed after retries."
                        if self._is_connection_error(exc)
                        else "VN30 API request failed after retries."
                    )
                    raise FetchError(message) from exc
            except FetchError:
                raise

            # Cooldown between retries to reduce pressure on the upstream API.
            time.sleep(self.retry_cooldown_seconds)

        raise FetchError("VN30 API request failed.") from last_error

    @staticmethod
    def _should_retry_http_status(status_code: int) -> bool:
        """Return whether an HTTP status should trigger a retry.

Keyword arguments:
status_code -- The status code."""

        # Retry on rate limits and server errors.
        return status_code == HTTPStatus.TOO_MANY_REQUESTS or 500 <= status_code < 600

    @staticmethod
    def _is_connection_error(exc: Exception) -> bool:
        """Return whether an exception indicates a connection failure.

Keyword arguments:
exc -- The exception to inspect.
"""

        # URLError often wraps socket-level failures; unwrap for classification.
        if isinstance(exc, error.URLError):
            reason = exc.reason
            return isinstance(reason, (ConnectionError, OSError, socket.gaierror, socket.timeout))
        return isinstance(exc, (ConnectionError, OSError, socket.gaierror, socket.timeout))


def create_vn30_fetcher(config: AppConfig = CONFIG) -> VN30Fetcher:
    """Build the default VN30 fetcher from application config.

Keyword arguments:
config -- The config."""

    # Construct a fetcher using the centralized app configuration.
    return VN30Fetcher(
        api_url=config.ssi_iboard_endpoint,
        timeout_seconds=config.request_timeout_seconds,
        max_retries=config.max_retries,
        retry_cooldown_seconds=config.retry_cooldown_seconds,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

Keyword arguments:
None."""

    # Provide CLI overrides for API endpoint and retry behavior.
    parser = argparse.ArgumentParser(description="Fetch VN30 records from SSI iBoard API.")
    parser.add_argument("--api-url", default=CONFIG.ssi_iboard_endpoint, help="Override API URL.")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=CONFIG.request_timeout_seconds,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=CONFIG.max_retries,
        help="Maximum retry attempts for transient failures.",
    )
    parser.add_argument(
        "--retry-cooldown-seconds",
        type=float,
        default=CONFIG.retry_cooldown_seconds,
        help="Cooldown between retry attempts in seconds.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional path to write fetched records as JSON.",
    )
    parser.add_argument(
        "--no-db-write",
        action="store_true",
        help="Skip SQLite persistence after fetching.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of tickers to show in the summary output.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout summary output.",
    )
    return parser


def persist_records(records: list[VN30Record], config: AppConfig) -> int:
    """Persist fetched records to SQLite.

Keyword arguments:
records -- Records to persist.
config -- Application config providing DB paths."""

    # Initialize the SQLite connection and persist in one step.
    connection_manager = SQLiteConnectionManager(
        database_path=config.database_path,
        schema_path=config.schema_path,
    )
    connection_manager.initialize()
    repository = VN30Repository(connection_manager)
    stored_count = repository.upsert_many(records)
    logger = get_logger(CONFIG.log_path)
    logger.info(
        "persist_records_complete records=%s stored=%s database_path=%s",
        len(records),
        stored_count,
        config.database_path,
    )
    return stored_count


def main(argv: list[str] | None = None) -> int:
    """Run the ingestion CLI.

Keyword arguments:
argv -- Optional list of CLI arguments. (default None) (default None)"""

    # Parse CLI arguments and wire a fetcher with overrides.
    parser = build_parser()
    args = parser.parse_args(argv)

    config = CONFIG.model_copy(
        update={
            "ssi_iboard_endpoint": args.api_url,
            "request_timeout_seconds": args.timeout_seconds,
            "max_retries": args.max_retries,
            "retry_cooldown_seconds": args.retry_cooldown_seconds,
        }
    )
    fetcher = create_vn30_fetcher(config)

    try:
        # Fetch records from SSI with retry handling.
        records = fetcher.fetch_records()
    except FetchError as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 1

    stored_count: int | None = None
    if not args.no_db_write:
        # Persist records unless explicitly skipped.
        stored_count = persist_records(records, config)

    if args.output_json:
        # Optionally write fetched records to a JSON file for inspection.
        output_payload = [record.model_dump() for record in records]
        with open(args.output_json, "w", encoding="utf-8") as handle:
            json.dump(output_payload, handle, ensure_ascii=False, indent=2)

    if not args.quiet:
        # Print a short stdout summary for CLI users.
        tickers = [record.ticker for record in records[: args.limit]]
        stored_suffix = (
            f" Stored {stored_count} rows to SQLite." if stored_count is not None else ""
        )
        print(f"Fetched {len(records)} records.{stored_suffix}")
        if tickers:
            print("Sample tickers:", ", ".join(tickers))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
