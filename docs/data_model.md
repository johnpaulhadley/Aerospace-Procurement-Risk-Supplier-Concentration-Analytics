# Data model (draft, to be frozen after the sample pull)

## Layers
1. **raw**: transactions and price indices as received, plus load metadata (`_loaded_at`, `_source_file`). Never edited.
2. **staging** (dbt tables): types cast, names standardized, duplicates removed, nulls handled.
3. **warehouse** (dbt tables): star schema below.
4. **marts** (dbt tables): monthly aggregates that Power BI reads.

## Star schema
| Table | Grain | Key columns |
|---|---|---|
| `fact_contract_transactions` | one contract action | transaction key, award key, supplier key, agency key, psc key, location key, action date key, obligation amount, modification number, action type, current end date |
| `dim_contract` | one award | award id (PIID), parent award id, base award date, base amount, pricing type, extent competed, offers received, original and latest end date |
| `dim_supplier` | one supplier | UEI, parent UEI, standardized name, parent name, state, country |
| `dim_agency` | one awarding office | agency, sub-agency, office |
| `dim_product_service` | one PSC | PSC code, description, PSC group, NAICS code, mapped PPI series |
| `dim_location` | one place of performance | state, country, congressional district |
| `dim_date` | one day | date, month, calendar year, federal fiscal year and quarter |
| `fact_price_index` | one series per month | series id, month, index value |

## Marts
| Table | Grain | Feeds |
|---|---|---|
| `supplier_monthly_metrics` | supplier x category x month | Supplier Risk page |
| `category_monthly_metrics` | category x month (HHI, top-4 share, competition share, PPI change) | Executive and Commodity pages |
| `contract_risk_summary` | one award | Contract Drilldown page |
| `pipeline_health_daily` | one load day | data-quality monitoring |

## Loading and optimization
- **Backfill**: USAspending bulk download API, one job per agency per month of action date (`ingestion/bulk_download.py`), filtered to in-scope PSC groups at load.
- **Incremental**: the same API for recent months; dbt incremental models reprocess a trailing window because agencies report late and modify past actions.
- **Reconciliation**: row counts and obligation totals checked against the USAspending search API.
- **Indexing**: `fact_contract_transactions` is indexed on action date, supplier, PSC and contract keys. Source data is partitioned by fiscal-year file, and each file can be reloaded on its own.
- **Proof**: `EXPLAIN ANALYZE` timings for the same dashboard query against the fact table and against the mart, recorded in `docs/architecture.md`.

## Built so far
- `raw.contract_transactions`: 60 of the 297 source columns, stored as text, plus `_source_file` and `_loaded_at`. Reloading a file replaces its rows.
- `raw.load_log`: rows read, rows loaded and net obligations per file load.
- `staging.stg_contract_transactions`: typed, de-duplicated across overlapping files, with scope basis, competition flag, acquisition program and consolidated parent name.
- `reference.supplier_parent_overrides` (dbt seed): manual parent-name consolidation, extended as variants are found.

Checked on June 2024: 11,730 in-scope rows and $8.16B net obligations in staging, matching the independent profile; a deliberately overlapping file added 78 raw rows and none to staging.

## Warehouse and marts (built)
- Dimensions: `dim_date`, `dim_supplier`, `dim_product_service`, `dim_agency`, `dim_location`, `dim_contract`.
- Fact: `fact_contract_transactions`, with relationship tests to every dimension.
- Marts: `supplier_monthly_metrics`, `category_monthly_metrics` (trailing 12-month HHI, top-4 share and not-competed share at PSC and PSC-group level), `contract_risk_summary`.
- Tests: 44 in total, including a reconciliation of both monthly marts to the fact table and a range check on HHI.
- Known limit: small categories produce unstable shares. Dashboards should apply a minimum-dollar filter.
- `supplier_key` is a hash of the consolidated parent name, because the source splits some companies across several parent UEIs.
