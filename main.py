"""Pipeline entrypoint for VN30 processing."""

from __future__ import annotations

from scripts.pipeline import PipelineResult, run_pipeline
from scripts.cli import main as cli_main

__all__ = ["PipelineResult", "run_pipeline"]


def main() -> int:
    """Run the CLI entrypoint."""

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
