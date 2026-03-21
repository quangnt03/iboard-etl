"""Report generation entrypoint."""

from __future__ import annotations

from pathlib import Path

from src.controller.analytics_controller import create_analytics_controller
from src.models.analytics import ReportResult


def generate_report(output_path: Path | None = None) -> ReportResult:
    """Generate the analytics report via the controller.

    Args:
        output_path: Optional override for the output file path.

    Returns:
        ReportResult metadata for the generated report.
    """

    controller = create_analytics_controller()
    return controller.generate_report(output_path)
