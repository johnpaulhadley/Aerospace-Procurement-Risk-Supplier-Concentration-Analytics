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
Dagster schedules ingestion and dbt runs and exposes the backfill by fiscal-year partition. PostgreSQL runs in Docker (`docker-compose.yml`).

Query-optimization measurements are added here once the marts exist.
