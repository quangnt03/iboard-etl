"""Tests for the VN30 HTTP fetcher."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch
from urllib import error

from src.ingest import FetchError, VN30Fetcher


class FakeHttpResponse:
    """Simple context manager for urllib response mocking."""

    def __init__(self, payload: str) -> None:
        """Store the response payload."""

        self.payload = payload

    def read(self) -> bytes:
        """Return the payload bytes."""

        return self.payload.encode("utf-8")

    def __enter__(self) -> "FakeHttpResponse":
        """Enter the context manager."""

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit the context manager."""

        return None


class VN30FetcherTests(unittest.TestCase):
    """Cover fetcher success and retry behavior."""

    def setUp(self) -> None:
        """Create a fetcher for each test."""

        self.fetcher = VN30Fetcher(
            api_url="https://example.test/vn30",
            timeout_seconds=1.0,
            max_retries=3,
            retry_cooldown_seconds=0.0,
        )

    def test_fetch_records_success(self) -> None:
        """Return validated records on a good response."""

        payload = {
            "code": "SUCCESS",
            "message": "ok",
            "data": [
                {
                    "expectedLastUpdate": 1773972896569,
                    "stockSymbol": "ACB",
                    "refPrice": 23600,
                    "openPrice": 23400,
                    "matchedPrice": 23300,
                    "lowest": 23300,
                    "highest": 23500,
                    "avgPrice": 23345.24,
                    "priceChange": -300,
                    "priceChangePercent": -1.27,
                    "stockVol": 243800,
                }
            ],
        }

        with patch("src.ingest.request.urlopen", return_value=FakeHttpResponse(json.dumps(payload))):
            records = self.fetcher.fetch_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].ticker, "ACB")
        self.assertEqual(records[0].volume, 243800)
        self.assertEqual(records[0].market_cap, 23600 * 243800)

    def test_fetch_records_retries_http_429_then_succeeds(self) -> None:
        """Retry on 429 and succeed on a later attempt."""

        payload = {
            "code": "SUCCESS",
            "message": "ok",
            "data": [
                {
                    "expectedLastUpdate": 1773972896569,
                    "stockSymbol": "ACB",
                    "refPrice": 23600,
                    "openPrice": 23400,
                    "matchedPrice": 23300,
                    "lowest": 23300,
                    "highest": 23500,
                    "avgPrice": 23345.24,
                    "priceChange": -300,
                    "priceChangePercent": -1.27,
                    "stockVol": 243800,
                }
            ],
        }
        rate_limited = error.HTTPError(
            url=self.fetcher.api_url,
            code=429,
            msg="rate limited",
            hdrs=None,
            fp=None,
        )

        with patch(
            "src.ingest.request.urlopen",
            side_effect=[rate_limited, FakeHttpResponse(json.dumps(payload))],
        ):
            records = self.fetcher.fetch_records()

        self.assertEqual(len(records), 1)

    def test_fetch_records_raises_on_malformed_json(self) -> None:
        """Fail fast on malformed JSON."""

        with patch("src.ingest.request.urlopen", return_value=FakeHttpResponse("{bad json")):
            with self.assertRaises(FetchError):
                self.fetcher.fetch_records()

    def test_fetch_records_raises_on_empty_data(self) -> None:
        """Reject empty data responses."""

        payload = {"code": "SUCCESS", "message": "ok", "data": []}
        with patch("src.ingest.request.urlopen", return_value=FakeHttpResponse(json.dumps(payload))):
            with self.assertRaises(FetchError):
                self.fetcher.fetch_records()
