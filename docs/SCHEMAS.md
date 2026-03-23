# Schemas and Validation

This document contains the schema definitions and validation rules for the VN30
pipeline.

## Pydantic Schema (data modelling)

```python
class StockRecord(BaseModel):
    ticker: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    timestamp: Optional[datetime] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
```

## SQL Schema (Database)

### `sql/schema.sql`

Contains:

- table definitions,
- column types
- primary and unique constraints,

Schema:

```sql
CREATE TABLE IF NOT EXISTS vn30_stock (
    timestamp TEXT NOT NULL,
    ticker TEXT NOT NULL,
    price REAL,
    change REAL,
    change_pct REAL,
    open REAL,
    close REAL,
    low REAL,
    high REAL,
    avg REAL,
    volume INTEGER,
    market_cap REAL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker, timestamp)
);
```

### `sql/indexes.sql`

Contains: proper indexes on `ticker` and `timestamp`, because the two fields are supposed to be queried to analyze time-series movements of VN30 Stocks.

```sql
CREATE INDEX IF NOT EXISTS idx_vn30_stock_timestamp
ON vn30_stock (timestamp);

CREATE INDEX IF NOT EXISTS idx_vn30_stock_ticker_timestamp
ON vn30_stock (ticker, timestamp);
```

### `sql/analytics_queries.sql`

Contains:

- reusable analytics queries,
- CTE-based transformations,
- aggregations,
- and ranking logic.

## API Notes

Configured endpoint: `GET https://iboard-query.ssi.com.vn/stock/group/VN30`

The live top-level response wrapper may look like:

```json
{
  "code": "SUCCESS",
  "message": "Call API /stock/group/VN30 successful",
  "data": []
}
```

## Data Validation and Normalization Strategy

### Step 1: Fetch raw payload

The ingestion layer fetches raw JSON from the API.

### Step 2: Parse each raw item with Pydantic

Each row is passed into a Pydantic model that:

- normalizes names,
- coerces numeric values,
- validates required fields,
- and returns a consistent internal record.

### Step 3: Convert validated record to database row

The validated model is converted into a structure matching the SQL storage
schema.

### Step 4: Insert into SQL table

`db.py` performs the actual insert using the SQL schema and indexes already
defined in the SQL layer.

## Data Quality Checks

The pipeline includes a dedicated data quality stage after loading.

### Minimum checks

- required fields are not null
- duplicate detection on `(ticker, timestamp)`
- numeric fields are non-negative
- `high_price >= low_price`
- `high_price >= open_price`
- `high_price >= close_price`
- `low_price <= open_price`
- `low_price <= close_price`
- stale timestamp detection

### Add more quality rules

1. Add a new `QualityRule` subclass in `src/models/quality_rules.py`.
2. Define `rule_name`, `rule_code`, `description`, and `logic`, then implement `validate(...)` to return `QualityRuleResult`.
3. Register the new rule in `VN30QualityChecker` by adding it to the default `rules` list in `src/quality_check.py`, or pass a custom list when constructing the checker.

Example skeleton:

```python
class ExampleRule(QualityRule):
    rule_name = "Example rule"
    rule_code = "example_rule"
    description = "Describe the rule in one sentence."
    logic = "some_field >= 0"

    def validate(self, records: list[VN30Record]) -> QualityRuleResult:
        violations = [record for record in records if record.some_field is not None and record.some_field < 0]
        return QualityRuleResult(
            rule_name=self.rule_name,
            rule_code=self.rule_code,
            description=self.description,
            logic=self.logic,
            status="pass" if len(violations) == 0 else "fail",
            violation_count=len(violations),
            affected_tickers=_affected_tickers(violations),
            sample_violations=_sample_violations(
                violations,
                lambda record: {
                    "ticker": record.ticker,
                    "timestamp": record.timestamp,
                    "some_field": record.some_field,
                },
            ),
        )
```

### Output

The report is written to:

```text
output/data_quality_report.json
```

Report structure:

```json
{
  "run_metadata": {
    "run_id": "2026-03-22T11:14:21.175453+07:00",
    "source": "https://iboard-query.ssi.com.vn/stock/group/VN30",
    "dataset": "VN30",
    "generated_at": "2026-03-22T11:14:21.175453+07:00",
    "trading_timezone": "Asia/Ho_Chi_Minh",
    "records_checked": 1
  },
  "summary": {
    "total_rules": 12,
    "passed_rules": 12,
    "failed_rules": 0,
    "overall_status": "pass"
  },
  "checks": [
    {
      "rule_name": "No NULL prices",
      "rule_code": "no_null_prices",
      "description": "Every record must have a non-null price.",
      "logic": "price IS NOT NULL",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Price change within bounds",
      "rule_code": "price_change_within_bounds",
      "description": "change_pct must be within +/-30%.",
      "logic": "-30 <= change_pct <= 30",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Volume positivity",
      "rule_code": "volume_positivity",
      "description": "volume must be > 0 during trading hours 09:00 - 15:00 ICT.",
      "logic": "volume > 0 when local_time between 09:00 and 15:00",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "All numeric fields non-negative",
      "rule_code": "numeric_fields_non_negative",
      "description": "All numeric fields must be non-negative.",
      "logic": "numeric_fields >= 0",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Low <= High",
      "rule_code": "low_lte_high",
      "description": "Low price must be less than or equal to high price.",
      "logic": "low <= high",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Open within range",
      "rule_code": "open_within_range",
      "description": "Open price must be within [low, high].",
      "logic": "low <= open <= high",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Close within range",
      "rule_code": "close_within_range",
      "description": "Close price must be within [low, high].",
      "logic": "low <= close <= high",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Average within range",
      "rule_code": "avg_within_range",
      "description": "Average price must be within [low, high].",
      "logic": "low <= avg <= high",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Ticker not blank",
      "rule_code": "ticker_not_blank",
      "description": "Ticker must be a non-blank string.",
      "logic": "ticker != ''",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Timestamp parseable",
      "rule_code": "timestamp_parseable",
      "description": "Timestamp must be a datetime instance.",
      "logic": "timestamp IS datetime",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Volume non-negative",
      "rule_code": "volume_non_negative",
      "description": "Volume must be greater than or equal to 0.",
      "logic": "volume >= 0",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    },
    {
      "rule_name": "Market cap non-negative",
      "rule_code": "market_cap_non_negative",
      "description": "Market cap must be greater than or equal to 0.",
      "logic": "market_cap >= 0",
      "status": "pass",
      "violation_count": 0,
      "affected_tickers": [],
      "sample_violations": []
    }
  ]
}
```
