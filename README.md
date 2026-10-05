# Aerospace Procurement Risk & Supplier Concentration Analytics

**Status: in progress.** Scope, KPI definitions and data model are drafted. Findings and dashboards will be added as they are produced.

## Business problem
The Department of Defense and NASA spend heavily on aircraft, missiles, space vehicles and engines, often with a small number of suppliers. This project uses public federal contract data to show which aerospace categories and suppliers carry the most concentration, cost, modification and schedule exposure, and where mitigation effort should go first.

## Findings and recommendations
To be written from measured results.

## Data sources and limitations
- [USAspending.gov](https://www.usaspending.gov) federal contract transactions, FY2018 to present.
- [FRED](https://fred.stlouisfed.org) producer price indices for aerospace manufacturing.
- The data is the government's view of its prime contractors. It contains no delivery or quality records, so metrics are risk indicators and not supplier performance ratings.

## Documentation
- [Business case, scope and KPI definitions](docs/business_case.md)
- [Data model](docs/data_model.md)
- [Architecture](docs/architecture.md)

## Stack
Python, PostgreSQL, dbt, Dagster, Power BI, Docker

## Run locally
```
cp .env.example .env
docker compose up -d
pip install -r requirements.txt
python ingestion/pull_sample.py --start 2025-06-01 --end 2025-06-07 --psc 1510
```
