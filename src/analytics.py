"""Report generation entrypoint."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from src.config import CONFIG
from src.controller.analytics_controller import create_analytics_controller
from src.models.analytics import ReportResult
from src.utils import get_logger


def generate_report(output_path: Path | None = None) -> ReportResult:
    """Generate the analytics report via the controller.

    Args:
        output_path: Optional override for the output file path.

    Returns:
        ReportResult metadata for the generated report.
    """

    logger = get_logger(CONFIG.log_path)
    logger.info("analytics_report_start output_path=%s", output_path or "default")
    controller = create_analytics_controller()
    result = controller.generate_report(output_path)
    logger.info(
        "analytics_report_complete output_path=%s rows=%s",
        result.output_path,
        result.row_count,
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """

    parser = argparse.ArgumentParser(description="Generate the VN30 analytics report.")
    parser.add_argument(
        "--output-path",
        help="Optional override for the output HTML path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout summary output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the report generation CLI.

    Args:
        argv: Optional list of CLI arguments.

    Returns:
        Exit code (0 for success).
    """

    parser = build_parser()
    args = parser.parse_args(argv)
    logger = get_logger(CONFIG.log_path)

    if args.output_path:
        output_path = Path(args.output_path)
    else:
        output_path = (
            CONFIG.report_output_dir
            / f"report-{datetime.now().strftime('%Y%m%d')}.html"
        )

    result = generate_report(output_path)
    if not args.quiet:
        print(f"Report generated: {result.output_path} (rows={result.row_count})")
    logger.info(
        "analytics_cli_complete output_path=%s rows=%s",
        result.output_path,
        result.row_count,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
