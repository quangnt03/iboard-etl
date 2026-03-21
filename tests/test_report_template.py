import unittest


class TestReportTemplate(unittest.TestCase):
    """Basic checks for the report template structure."""

    def test_template_contains_required_columns(self) -> None:
        """Ensure the report template includes the required column headers."""
        with open("src/templates/report.j2", "r", encoding="utf-8") as handle:
            content = handle.read()

        expected_headers = [
            "Ticker",
            "Open",
            "High",
            "Low",
            "Volatility %",
            "Today Volume",
            "5-Day Avg Volume",
            "Volume Ratio",
        ]
        for header in expected_headers:
            self.assertIn(header, content)


if __name__ == "__main__":
    unittest.main()
