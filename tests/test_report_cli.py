import unittest

from src.analytics import build_parser, main


class TestReportCli(unittest.TestCase):
    """Unit tests for the report CLI."""

    def test_build_parser_contains_expected_flags(self) -> None:
        """Ensure the parser exposes key CLI flags."""

        parser = build_parser()
        help_text = parser.format_help()
        self.assertIn("--output-path", help_text)

    def test_main_help_exits(self) -> None:
        """Ensure --help triggers a clean exit."""

        with self.assertRaises(SystemExit) as context:
            main(["--help"])
        self.assertEqual(context.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
