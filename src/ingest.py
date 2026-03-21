"""HTTP ingestion helpers for VN30 payloads."""

from __future__ import annotations

import argparse
import json
import sys
import socket
import time
from http import HTTPStatus
from typing import Any
from urllib import error, request

from pydantic import ValidationError

from src.config import CONFIG, AppConfig
from src.models.vn30_stock import VN30ApiResponse, VN30Record
from src.utils import get_logger


class FetchError(Exception):
    """Represent a non-recoverable VN30 fetch failure."""


class VN30Fetcher:
    """Fetch and validate VN30 data from the configured HTTP endpoint."""

    def __init__(
        self,
        api_url: str,
        timeout_seconds: float,
        max_retries: int,
        retry_cooldown_seconds: float,
    ) -> None:
        """Initialize the fetcher runtime settings."""

        self.api_url = api_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_cooldown_seconds = retry_cooldown_seconds
        self.logger = get_logger(CONFIG.log_path)

    def fetch_payload(self) -> dict[str, Any]:
        """Execute an HTTP GET and decode the JSON payload.

        Raises:
            TimeoutError: If the request times out.
            error.URLError: If a transport error occurs.
            error.HTTPError: If the server returns an HTTP error response.
            FetchError: If the response body is not valid JSON.
        """

        http_request = request.Request(
            self.api_url,
            headers={"Accept": "application/json", "User-Agent": "finhay-test/1.0"},
            method="GET",
        )
        try:
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

        Raises:
            FetchError: If the payload is invalid or contains unusable data.
        """

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
        """Fetch records with retry handling for transient failures."""

        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                payload = self.fetch_payload()
                return self.parse_response(payload)
            except error.HTTPError as exc:
                last_error = exc
                if not self._should_retry_http_status(exc.code) or attempt == self.max_retries:
                    raise FetchError(
                        f"VN30 API request failed with HTTP status {exc.code}."
                    ) from exc
            except (TimeoutError, error.URLError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    raise FetchError("VN30 API request failed after retries.") from exc
            except FetchError:
                raise

            time.sleep(self.retry_cooldown_seconds)

        raise FetchError("VN30 API request failed.") from last_error

    @staticmethod
    def _should_retry_http_status(status_code: int) -> bool:
        """Return whether an HTTP status should trigger a retry."""

        return status_code == HTTPStatus.TOO_MANY_REQUESTS or 500 <= status_code < 600


def create_vn30_fetcher(config: AppConfig = CONFIG) -> VN30Fetcher:
    """Build the default VN30 fetcher from application config."""

    return VN30Fetcher(
        api_url=config.ssi_iboard_endpoint,
        timeout_seconds=config.request_timeout_seconds,
        max_retries=config.max_retries,
        retry_cooldown_seconds=config.retry_cooldown_seconds,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """

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


def main(argv: list[str] | None = None) -> int:
    """Run the ingestion CLI.

    Args:
        argv: Optional list of CLI arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """

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
        records = fetcher.fetch_records()
    except FetchError as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 1

    if args.output_json:
        output_payload = [record.model_dump() for record in records]
        with open(args.output_json, "w", encoding="utf-8") as handle:
            json.dump(output_payload, handle, ensure_ascii=False, indent=2)

    if not args.quiet:
        tickers = [record.ticker for record in records[: args.limit]]
        print(f"Fetched {len(records)} records.")
        if tickers:
            print("Sample tickers:", ", ".join(tickers))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
