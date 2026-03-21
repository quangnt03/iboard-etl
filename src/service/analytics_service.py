"""Service layer for analytics and reporting."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import CONFIG
from src.models.analytics import ReportContext, ReportResult, ReportRow
from src.repository.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """Coordinate analytics queries and report rendering."""

    def __init__(self, repository: AnalyticsRepository) -> None:
        """Initialize the service.

        Args:
            repository: Analytics repository instance.
        """

        self.repository = repository

    def build_report_rows(self) -> list[ReportRow]:
        """Combine volatility and volume rows into report rows."""

        volatility_rows = self.repository.fetch_intraday_volatility()
        volume_rows = self.repository.fetch_volume_vs_5d_avg()
        volume_lookup = {row.ticker: row for row in volume_rows}

        report_rows: list[ReportRow] = []
        for volatility in volatility_rows:
            volume = volume_lookup.get(volatility.ticker)
            report_rows.append(
                ReportRow(
                    ticker=volatility.ticker,
                    open=volatility.open_price,
                    high=volatility.high_price,
                    low=volatility.low_price,
                    intraday_volatility=volatility.intraday_volatility,
                    today_volume=volume.today_volume if volume else None,
                    avg_5d_volume=volume.avg_5d_volume if volume else None,
                    volume_ratio=volume.volume_ratio if volume else None,
                )
            )
        return report_rows

    def generate_report_context(self, output_path: Path) -> ReportContext:
        """Build the report context for the template.

        Args:
            output_path: Target output file path.

        Returns:
            ReportContext ready for rendering.
        """

        rows = self.build_report_rows()
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ReportContext(
            title="Intraday Volatility Snapshot",
            subtitle="Top 10 most volatile VN30 stocks with volume context.",
            generated_at=generated_at,
            source="SSI iBoard API",
            rows=rows,
            output_path=output_path,
        )

    def render_report(self, context: ReportContext, template_path: Path) -> str:
        """Render the report HTML using Jinja.

        Args:
            context: Report context data.
            template_path: Path to the Jinja template file.

        Returns:
            Rendered HTML string.
        """

        environment = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(["html", "xml", 'jinja', 'j2']),
        )
        template = environment.get_template(template_path.name)
        return template.render(**context.model_dump())

    def generate_report(self, output_path: Path | None = None) -> ReportResult:
        """Generate the HTML report and write it to disk.

        Args:
            output_path: Optional override for the output file path.

        Returns:
            ReportResult metadata.
        """

        target_path = output_path or self._default_output_path()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        context = self.generate_report_context(target_path)
        html = self.render_report(context, CONFIG.report_template_path)
        target_path.write_text(html, encoding="utf-8")
        return ReportResult(output_path=target_path, row_count=len(context.rows))

    @staticmethod
    def _default_output_path() -> Path:
        """Build the default report output path."""

        date_stamp = datetime.now().strftime("%Y%m%d")
        filename = f"report-{date_stamp}.html"
        return CONFIG.report_output_dir / filename
