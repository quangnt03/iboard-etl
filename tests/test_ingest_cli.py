"""Unit tests for the ingestion CLI interface.

Keyword arguments:
None."""

import unittest

from src.ingest import build_parser, main


class TestIngestCli(unittest.TestCase):
    """Unit tests for the ingest CLI.

Keyword arguments:
None."""

    def test_build_parser_contains_expected_flags(self) -> None:
        """Ensure the parser exposes key CLI flags.

Keyword arguments:
self -- The self."""
        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("--api-url", help_text)
        self.assertIn("--output-json", help_text)
        self.assertIn("--no-db-write", help_text)

    def test_main_help_exits(self) -> None:
        """Ensure --help triggers a clean exit.

Keyword arguments:
self -- The self."""
        with self.assertRaises(SystemExit) as context:
            main(["--help"])
        self.assertEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
