# Architecture

```
USAspending bulk files (backfill) + USAspending API (incremental) + FRED price indices
        |
   Python ingestion (requests, pandas, SQLAlchemy)
        |
   PostgreSQL raw schema
        |
   dbt: staging -> warehouse (star schema) -> monthly marts
        |
   Power BI
```
Dagster (`orchestration/definitions.py`) models the pipeline as assets: `raw/contract_transactions` partitioned by fiscal year, `raw/price_index`, every dbt model with its tests, and `powerbi_exports`. The `full_refresh` job rebuilds everything downstream of loaded data; `monthly_refresh` reloads one fiscal year and everything after it, and a schedule runs it on the 8th of each month for the current fiscal year. PostgreSQL runs in Docker (`docker-compose.yml`).

Query-optimization measurements are added here once the marts exist.
