"""Interactive CLI menu for VN30 pipeline operations."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import CONFIG, AppConfig  # noqa: E402
from src.ingest import FetchError, create_vn30_fetcher, persist_records  # noqa: E402
from src.quality_check import VN30QualityChecker  # noqa: E402
from src.analytics import generate_report  # noqa: E402
from scripts.pipeline import run_pipeline  # noqa: E402


@dataclass(frozen=True)
class MenuAction:
    """Represent a CLI menu action."""

    key: str
    description: str
    handler: callable


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser.

    Returns:
        ArgumentParser instance.
    """

    return argparse.ArgumentParser(description="Interactive CLI for VN30 pipeline actions.")


def prompt_yes_no(message: str, default: bool = True) -> bool:
    """Prompt for a yes/no response.

    Args:
        message: Prompt message.
        default: Default value when user presses enter.

    Returns:
        Boolean user choice.
    """

    suffix = " [Y/n]: " if default else " [y/N]: "
    while True:
        response = input(message + suffix).strip().lower()
        if not response:
            return default
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please enter y or n.")


def prompt_text(message: str, default: str | None = None) -> str | None:
    """Prompt for optional text input.

    Args:
        message: Prompt message.
        default: Default value when user presses enter.

    Returns:
        User input or default.
    """

    suffix = f" [{default}]: " if default else ": "
    response = input(message + suffix).strip()
    return response or default


def prompt_float(message: str, default: float) -> float:
    """Prompt for float input with default."""

    while True:
        response = input(f"{message} [{default}]: ").strip()
        if not response:
            return default
        try:
            return float(response)
        except ValueError:
            print("Please enter a valid number.")


def prompt_int(message: str, default: int) -> int:
    """Prompt for integer input with default."""

    while True:
        response = input(f"{message} [{default}]: ").strip()
        if not response:
            return default
        try:
            return int(response)
        except ValueError:
            print("Please enter a valid integer.")


def build_config_overrides() -> AppConfig:
    """Prompt for optional overrides and return updated config."""

    use_defaults = prompt_yes_no("Use default API settings?", default=True)
    if use_defaults:
        return CONFIG

    api_url = prompt_text("API URL", default=CONFIG.ssi_iboard_endpoint)
    timeout_seconds = prompt_float("Timeout (seconds)", CONFIG.request_timeout_seconds)
    max_retries = prompt_int("Max retries", CONFIG.max_retries)
    retry_cooldown_seconds = prompt_float("Retry cooldown (seconds)", CONFIG.retry_cooldown_seconds)
    return CONFIG.model_copy(
        update={
            "ssi_iboard_endpoint": api_url,
            "request_timeout_seconds": timeout_seconds,
            "max_retries": max_retries,
            "retry_cooldown_seconds": retry_cooldown_seconds,
        }
    )


def action_run_pipeline() -> None:
    """Run the full pipeline with quality gating."""

    config = build_config_overrides()
    result = run_pipeline(config)
    print(
        "Pipeline result:",
        f"branch={result.branch}",
        f"records_loaded={result.records_loaded}",
        f"records_stored={result.records_stored}",
        f"quality_report={result.quality_report_path}",
        f"report={result.analytics_report_path}",
    )


def action_quality_check() -> None:
    """Fetch records and run quality checks without DB writes."""

    config = build_config_overrides()
    report_dir_input = prompt_text("Report directory", default=str(CONFIG.log_path.parent))
    report_directory = Path(report_dir_input) if report_dir_input else CONFIG.log_path.parent

    fetcher = create_vn30_fetcher(config)
    try:
        records = fetcher.fetch_records()
    except FetchError as exc:
        print(f"Fetch failed: {exc}")
        return

    checker = VN30QualityChecker(report_directory=report_directory)
    report, report_path = checker.validate_and_write(records, fetcher.api_url)
    total_violations = sum(check.violation_count for check in report.checks)
    print(
        f"Quality report: {report_path} "
        f"(failed_rules={report.summary.failed_rules}, "
        f"violations={total_violations})"
    )


def action_fetch_records() -> None:
    """Fetch records and optionally persist them to SQLite."""

    config = build_config_overrides()
    skip_db_write = prompt_yes_no("Skip SQLite write?", default=False)
    fetcher = create_vn30_fetcher(config)
    try:
        records = fetcher.fetch_records()
    except FetchError as exc:
        print(f"Fetch failed: {exc}")
        return

    stored_count: int | None = None
    if not skip_db_write:
        stored_count = persist_records(records, config)

    stored_suffix = (
        f" Stored {stored_count} rows to SQLite." if stored_count is not None else ""
    )
    print(f"Fetched {len(records)} records.{stored_suffix}")


def action_generate_report() -> None:
    """Generate the analytics report from DB."""

    output_default = (
        CONFIG.report_output_dir
        / f"report-{datetime.now().strftime('%Y%m%d')}.html"
    )
    output_path_value = prompt_text("Output path", default=str(output_default))
    output_path = Path(output_path_value) if output_path_value else output_default
    result = generate_report(output_path)
    print(f"Report generated: {result.output_path} (rows={result.row_count})")


def action_exit() -> None:
    """Exit the CLI."""

    print("Exiting.")


def get_menu_actions() -> list[MenuAction]:
    """Return menu actions in order."""

    return [
        MenuAction("1", "Run full pipeline", action_run_pipeline),
        MenuAction("2", "Fetch records (optional DB write)", action_fetch_records),
        MenuAction("3", "Run quality check (fresh fetch)", action_quality_check),
        MenuAction("4", "Generate analytics report from DB", action_generate_report),
        MenuAction("5", "Exit", action_exit),
    ]


def run_menu() -> None:
    """Run the interactive menu loop."""

    actions = {action.key: action for action in get_menu_actions()}
    while True:
        print("\nVN30 CLI Menu")
        for action in actions.values():
            print(f"{action.key}) {action.description}")
        choice = input("Select an option: ").strip()
        action = actions.get(choice)
        if not action:
            print("Invalid selection. Try again.")
            continue
        action.handler()
        if action.key == "5":
            break


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    parser = build_parser()
    parser.parse_args(argv)
    run_menu()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
