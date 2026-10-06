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
- [Sample pull findings](docs/sample_findings.md)
- [Power BI build guide](docs/power_bi_build_guide.md)

## Stack
Python, PostgreSQL, dbt, Dagster, Power BI, Docker

## Run locally
```
cp .env.example .env            # then set a password
docker compose up -d            # PostgreSQL
pip install -r requirements.txt
python ingestion/backfill_archive.py --start-fy 2018 --end-fy 2026   # yearly files
python ingestion/load_raw.py data/raw/archive                         # in-scope rows into PostgreSQL
python ingestion/fetch_price_index.py                                 # producer price indices from FRED
cd dbt && dbt build --profiles-dir . && cd ..                         # warehouse, marts and tests
python ingestion/export_marts.py                                      # CSVs for analysis and Power BI
```
`ingestion/bulk_download.py` pulls single months through the USAspending API for incremental loads.
