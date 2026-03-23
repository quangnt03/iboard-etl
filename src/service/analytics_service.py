"""Service layer for analytics and reporting.

Keyword arguments:
None."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from datetime import timezone

from src.config import CONFIG
from src.models.analytics import ReportContext, ReportResult, ReportRow
from src.repository.analytics_repository import AnalyticsRepository
from src.utils import VnStockHistoryResult, fetch_volume_history, get_logger
from src.models.vn30_stock import VN30Record
from src.repository.vn30_repository import SQLiteConnectionManager, VN30Repository
from tools.vnstock_history import VnStockHistoryRow


class AnalyticsService:
    """Coordinate analytics queries and report rendering.

Keyword arguments:
None."""

    def __init__(
        self,
        repository: AnalyticsRepository,
        *,
        vn30_repository: VN30Repository | None = None,
        persist_vnstock_history: bool = False,
        use_vnstock_fallback: bool = True,
    ) -> None:
        """Initialize the service.

Keyword arguments:
self -- The self.
repository -- Analytics repository instance.
vn30_repository -- Optional VN30 repository for persistence. (default None) (default None)
persist_vnstock_history -- Whether to persist VnStock fallback rows. (default False) (default False)
use_vnstock_fallback -- Whether to enable the VnStock fallback. (default True) (default True)"""

        self.repository = repository
        self.vn30_repository = vn30_repository
        self.persist_vnstock_history = persist_vnstock_history
        self.use_vnstock_fallback = use_vnstock_fallback

    def build_report_rows(self) -> list[ReportRow]:
        """Combine volatility and volume rows into report rows.

Keyword arguments:
self -- The self."""

        # Load analytics inputs from the repository and prepare lookup maps.
        logger = get_logger(CONFIG.log_path)
        volatility_rows = self.repository.fetch_intraday_volatility()
        volume_rows = self.repository.fetch_volume_vs_5d_avg()
        volume_counts = self.repository.fetch_volume_5d_counts()
        volume_lookup = {row.ticker: row for row in volume_rows}
        count_lookup = {row.ticker: row.day_count for row in volume_counts}
        fallback_cache: dict[str, VnStockHistoryResult] = {}

        report_rows: list[ReportRow] = []
        for volatility in volatility_rows:
            volume = volume_lookup.get(volatility.ticker)
            day_count = count_lookup.get(volatility.ticker, 0)
            avg_5d_volume = volume.avg_5d_volume if volume else None
            volume_ratio = volume.volume_ratio if volume else None

            if day_count < 5 and self.use_vnstock_fallback:
                # Use VnStock history when DB lacks enough trading days.
                logger.info(
                    "vnstock_fallback_trigger ticker=%s day_count=%s",
                    volatility.ticker,
                    day_count,
                )
                history = fallback_cache.get(volatility.ticker)
                if history is None:
                    try:
                        # Fetch extra history to compute a 5-day average volume.
                        history = fetch_volume_history(
                            symbol=volatility.ticker,
                            source="VCI",
                            length_days=10,
                        )
                    except Exception:
                        # Preserve a failed fetch as an empty history snapshot.
                        history = VnStockHistoryResult(
                            symbol=volatility.ticker,
                            source="VCI",
                            rows=[],
                        )
                    fallback_cache[volatility.ticker] = history

                rows = sorted(history.rows, key=lambda row: row.time)
                if len(rows) >= 5:
                    # Compute the average volume over the last five sessions.
                    last_five = rows[-5:]
                    avg_5d_volume = sum(row.volume for row in last_five) / 5
                    if volume and volume.today_volume is not None and avg_5d_volume > 0:
                        volume_ratio = volume.today_volume / avg_5d_volume
                    logger.info(
                        "vnstock_fallback_applied ticker=%s avg_5d_volume=%s volume_ratio=%s",
                        volatility.ticker,
                        avg_5d_volume,
                        volume_ratio,
                    )
                    if self.persist_vnstock_history:
                        # Optionally persist missing history rows for future runs.
                        self._persist_fallback_rows(
                            logger,
                            volatility.ticker,
                            last_five,
                        )
                else:
                    logger.info(
                        "vnstock_fallback_insufficient_rows ticker=%s rows=%s",
                        volatility.ticker,
                        len(rows),
                    )
            report_rows.append(
                ReportRow(
                    ticker=volatility.ticker,
                    open=volatility.open_price,
                    high=volatility.high_price,
                    low=volatility.low_price,
                    intraday_volatility=volatility.intraday_volatility,
                    today_volume=volume.today_volume if volume else None,
                    avg_5d_volume=avg_5d_volume,
                    volume_ratio=volume_ratio,
                )
            )
        return report_rows

    def _persist_fallback_rows(
        self,
        logger,
        ticker: str,
        rows: list[VnStockHistoryRow],
    ) -> None:
        """Insert missing VnStock rows into SQLite for the ticker.

Keyword arguments:
self -- The self.
logger -- The logger.
ticker -- The ticker.
rows -- The rows."""

        # Skip persistence if no VN30 repository is configured.
        repository = self._get_vn30_repository()
        if repository is None:
            return

        dates = [row.time.date().isoformat() for row in rows]
        if not dates:
            return
        start_date = min(dates)
        end_date = max(dates)

        try:
            # Avoid inserting duplicates by querying existing trade dates.
            existing_dates = self._fetch_existing_dates(repository, ticker, start_date, end_date)
        except Exception as exc:  # noqa: BLE001 - best effort persistence
            logger.error(
                "vnstock_fallback_dates_failed ticker=%s error=%s",
                ticker,
                exc,
            )
            return
        records: list[VN30Record] = []
        for row in rows:
            trade_date = row.time.date().isoformat()
            if trade_date in existing_dates:
                continue
            timestamp = row.time
            if timestamp.tzinfo is None:
                # Normalize timestamps before writing to SQLite.
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            price = row.close if row.close is not None else row.open
            record = VN30Record(
                timestamp=timestamp,
                ticker=ticker,
                price=price,
                change=None,
                change_pct=None,
                open=row.open,
                close=row.close,
                low=row.low,
                high=row.high,
                avg=row.avg,
                volume=row.volume,
            )
            records.append(record)

        if not records:
            return

        try:
            # Persist the best-effort history rows.
            stored = repository.upsert_many(records)
            logger.info(
                "vnstock_fallback_persisted ticker=%s rows=%s",
                ticker,
                stored,
            )
        except Exception as exc:  # noqa: BLE001 - best effort persistence
            logger.error(
                "vnstock_fallback_persist_failed ticker=%s error=%s",
                ticker,
                exc,
            )

    def _fetch_existing_dates(
        self,
        repository: VN30Repository,
        ticker: str,
        start_date: str,
        end_date: str,
    ) -> set[str]:
        """Return existing trade dates for a ticker within a date window.

Keyword arguments:
self -- The self.
repository -- The repository.
ticker -- The ticker.
start_date -- The start date.
end_date -- The end date."""

        with repository.connection_manager.connect() as connection:
            # Query existing trade dates for the ticker within the window.
            rows = connection.execute(
                """
                SELECT DISTINCT DATE(timestamp) AS trade_date
                FROM vn30_stock
                WHERE ticker = ?
                  AND DATE(timestamp) BETWEEN ? AND ?
                """,
                (ticker, start_date, end_date),
            ).fetchall()
        return {row["trade_date"] for row in rows if row["trade_date"]}

    def _get_vn30_repository(self) -> VN30Repository | None:
        """Return a VN30 repository instance if available.

Keyword arguments:
self -- The self."""

        # Use an injected repository when available.
        if self.vn30_repository is not None:
            return self.vn30_repository

        try:
            # Lazily build a repository for fallback persistence.
            connection_manager = SQLiteConnectionManager(
                database_path=CONFIG.database_path,
                schema_path=CONFIG.schema_path,
            )
            return VN30Repository(connection_manager)
        except Exception:
            return None

    def generate_report_context(self, output_path: Path) -> ReportContext:
        """Build the report context for the template.

Keyword arguments:
self -- The self.
output_path -- Target output file path."""

        # Assemble the full report context for the template renderer.
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

Keyword arguments:
self -- The self.
context -- Report context data.
template_path -- Path to the Jinja template file."""

        # Build a Jinja environment scoped to the template directory.
        environment = Environment(
            loader=FileSystemLoader(template_path.parent),
            autoescape=select_autoescape(["html", "xml", 'jinja', 'j2']),
        )
        template = environment.get_template(template_path.name)
        return template.render(**context.model_dump())

    def generate_report(self, output_path: Path | None = None) -> ReportResult:
        """Generate the HTML report and write it to disk.

Keyword arguments:
self -- The self.
output_path -- Optional override for the output file path. (default None) (default None)"""

        # Determine output path, build context, and render HTML.
        target_path = output_path or self._default_output_path()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        context = self.generate_report_context(target_path)
        html = self.render_report(context, CONFIG.report_template_path)
        target_path.write_text(html, encoding="utf-8")
        return ReportResult(output_path=target_path, row_count=len(context.rows))

    @staticmethod
    def _default_output_path() -> Path:
        """Build the default report output path.

Keyword arguments:
None."""

        date_stamp = datetime.now().strftime("%Y%m%d")
        filename = f"report-{date_stamp}.html"
        return CONFIG.report_output_dir / filename
