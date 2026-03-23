# Pipeline Customizations

This note summarizes the main customization points in the VN30 pipeline, where to change them, and small code snippets to get started.

## Overall step guide
1. Identify the customization area (ingestion, quality, analytics, reporting, etc.).
2. Update configuration defaults in `src/config.py` or add a new config field in `src/models/app_config.py`.
3. Modify the core logic file (service/repository/controller) listed in the section below.
4. If you change schema or query outputs, update corresponding models in `src/models/`.
5. Run the pipeline via `scripts/pipeline.py` or `main.py` to validate.

## Q&A: Common customization requests

### 1. I want to change the API source
Where to change
- `src/config.py` (update `ssi_iboard_endpoint`)
- `src/ingest.py` (`VN30Fetcher` request headers and retry behavior)
- `src/models/vn30_stock.py` (field aliases if payload shape changes)

Snippet
```python
# src/config.py
CONFIG = AppConfig(
    ssi_iboard_endpoint=os.getenv("BASE_URL", "https://new-api.example.com/vn30"),
)
```

### 2. I want to store more fields in the database
Where to change
- `sql/schema.sql` (add columns)
- `src/models/vn30_stock.py` (add fields to `VN30Record`/`VN30Row`)
- `src/repository/vn30_repository.py` (serialization is model-driven)

Snippet
```sql
-- sql/schema.sql
ALTER TABLE vn30_stock ADD COLUMN sector TEXT;
```

```python
# src/models/vn30_stock.py
class VN30Record(BaseModel):
    sector: str | None = None
```

### 3. How to add or remove quality rules
Where to change
- `src/models/quality_rules.py` (define/remove rule classes)
- `src/quality_check.py` (`VN30QualityChecker.rules` list)

Snippet
```python
# src/models/quality_rules.py
class PriceNonZeroRule(QualityRule):
    rule_name = "Price non-zero"
    rule_code = "price_non_zero"
    description = "Price must be > 0."
    logic = "price > 0"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        ...
```

```python
# src/quality_check.py
self.rules = [NonNullPriceRule(), PriceNonZeroRule()]
```

### 4. I want to add more columns in the analytic report
Where to change
- `sql/analytics_queries.sql` (add columns to queries)
- `src/models/analytics.py` (add fields to `ReportRow`)
- `src/service/analytics_service.py` (map new fields into `ReportRow`)
- `src/templates/report.j2` (render new columns)

Snippet
```python
# src/models/analytics.py
class ReportRow(BaseModel):
    pe_ratio: float | None = None
```

```jinja2
<!-- src/templates/report.j2 -->
<th>PE Ratio</th>
<td>{{ row.pe_ratio }}</td>
```

### 5. How to change log format
Where to change
- `src/utils.py` (`get_logger` formatter)

Snippet
```python
# src/utils.py
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)
```

### 6. Migrate from SQLite to PostgreSQL
Where to change
- `src/repository/vn30_repository.py` (replace sqlite3 connection code)
- `src/repository/analytics_repository.py` (connection manager and query execution)
- `src/db.py` (compatibility aliases)
- `src/config.py` and `src/models/app_config.py` (connection settings)
- SQL files under `sql/` may need Postgres-specific syntax changes

Snippet (sketch)
```python
# src/repository/vn30_repository.py
import psycopg

class PostgresConnectionManager:
    def connect(self) -> psycopg.Connection:
        return psycopg.connect(os.getenv("PG_DSN"))
```

## Configuration and environment
Where to change
- `src/config.py`
- `src/models/app_config.py`

Snippet
```python
# src/config.py
CONFIG = AppConfig(
    ssi_iboard_endpoint=os.getenv("BASE_URL", "https://...")
)
```

## Ingestion (SSI API)
Where to change
- `src/ingest.py` (`VN30Fetcher`)
- `src/service/vn30_service.py`
- `src/controller/vn30_controller.py`

Snippet
```python
# src/ingest.py
fetcher = VN30Fetcher(
    api_url="https://...",
    timeout_seconds=20,
    max_retries=5,
    retry_cooldown_seconds=3.0,
)
```

## Database schema and persistence
Where to change
- `sql/schema.sql`
- `sql/indexes.sql`
- `src/repository/vn30_repository.py`

Snippet
```sql
-- sql/schema.sql
ALTER TABLE vn30_stock ADD COLUMN sector TEXT;
```

## Quality checks
Where to change
- `src/models/quality_rules.py`
- `src/quality_check.py`

Snippet
```python
# src/models/quality_rules.py
class PriceNonZeroRule(QualityRule):
    rule_name = "Price non-zero"
    rule_code = "price_non_zero"
    description = "Price must be > 0."
    logic = "price > 0"
```

## Analytics and SQL
Where to change
- `sql/analytics_queries.sql`
- `src/repository/analytics_repository.py`
- `src/models/analytics.py`
- `src/service/analytics_service.py`

Snippet
```sql
-- sql/analytics_queries.sql
-- name: volume_vs_10d_avg
WITH ...
SELECT ...;
```

## VnStock fallback behavior
Where to change
- `tools/vnstock_history.py`
- `src/service/analytics_service.py`
- `src/config.py`

Snippet
```python
# src/config.py
use_vnstock_fallback=_parse_bool(os.getenv("USE_VNSTOCK_FALLBACK"), True)
```

## Reporting and templates
Where to change
- `src/templates/report.j2`
- `src/analytics.py`

Snippet
```jinja2
<!-- src/templates/report.j2 -->
<h1>{{ title }}</h1>
```

## Pipeline orchestration and CLI
Where to change
- `scripts/pipeline.py`
- `scripts/cli.py`
- `main.py`

Snippet
```python
# scripts/pipeline.py
result = run_pipeline()
```

## Logging and run metrics
Where to change
- `src/utils.py`
- `src/models/run_metrics.py`

Snippet
```python
# src/utils.py
logger = get_logger(CONFIG.log_path)
```

## Recommended customization workflow
1. Start with `src/config.py` for toggles and runtime paths.
2. Update SQL in `sql/analytics_queries.sql` and adjust models if you add new columns.
3. Modify `src/service/analytics_service.py` for report logic and fallback rules.
4. Update `src/templates/report.j2` to change the report layout.

If you want, I can add a brief "How to test changes" section tailored to your changes.
