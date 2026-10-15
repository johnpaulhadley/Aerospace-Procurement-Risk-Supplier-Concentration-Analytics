"""Dagster definitions: the whole pipeline as assets, with a fiscal-year backfill
and a monthly schedule.

Run the UI from the repository root:
    dagster dev -m orchestration.definitions

Asset graph:
    raw/contract_transactions (one partition per fiscal year)  raw/price_index
                         \\                                     /
                           dbt models and tests (staging, warehouse, marts)
                                            |
                                     powerbi_exports
"""
import sys
from pathlib import Path

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSelection,
    Definitions,
    MaterializeResult,
    MetadataValue,
    RunRequest,
    StaticPartitionsDefinition,
    asset,
    define_asset_job,
    schedule,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ingestion"))

import backfill_archive  # noqa: E402
import export_powerbi  # noqa: E402
import fetch_price_index  # noqa: E402
import load_raw  # noqa: E402
from config import database_url  # noqa: E402  (also loads .env for dbt)

FIRST_FY, LAST_FY = 2018, 2026
fiscal_years = StaticPartitionsDefinition([str(fy) for fy in range(FIRST_FY, LAST_FY + 1)])

dbt_project = DbtProject(project_dir=ROOT / "dbt", profiles_dir=ROOT / "dbt")
dbt_project.prepare_if_dev()


@asset(
    key=AssetKey(["raw", "contract_transactions"]),
    partitions_def=fiscal_years,
    group_name="ingestion",
    description="In-scope USAspending contract transactions for one federal fiscal year, "
                "loaded into PostgreSQL. A rerun replaces that year's rows.",
)
def raw_contract_transactions(context: AssetExecutionContext) -> MaterializeResult:
    from sqlalchemy import create_engine, text

    fiscal_year = int(context.partition_key)
    paths = backfill_archive.download_year(fiscal_year)
    engine = create_engine(database_url())
    load_raw.ensure_tables(engine)
    for path in paths:
        load_raw.load_zip(engine, path)
    names = [p.name for p in paths]
    with engine.connect() as con:
        rows, net = con.execute(
            text("select coalesce(sum(rows_loaded), 0), coalesce(sum(net_obligation_loaded), 0) "
                 "from (select distinct on (source_file) * from raw.load_log "
                 "where source_file = any(:names) order by source_file, loaded_at desc) latest"),
            {"names": names},
        ).one()
    return MaterializeResult(metadata={
        "files": MetadataValue.json(names),
        "rows_loaded": int(rows),
        "net_obligation": float(net),
    })


@asset(
    key=AssetKey(["raw", "price_index"]),
    group_name="ingestion",
    description="Monthly producer price indices from FRED.",
)
def raw_price_index() -> None:
    fetch_price_index.main()


@dbt_assets(manifest=dbt_project.manifest_path)
def dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()


@asset(
    deps=[AssetKey(["marts", "category_risk_scores"]), AssetKey(["marts", "supplier_monthly_metrics"]),
          AssetKey(["marts", "contract_risk_summary"])],
    group_name="reporting",
    description="CSV files in data/processed/powerbi/ that the Power BI report reads.",
)
def powerbi_exports() -> None:
    export_powerbi.main()


full_refresh = define_asset_job(
    "full_refresh",
    selection=AssetSelection.all() - AssetSelection.keys(AssetKey(["raw", "contract_transactions"])),
    description="Rebuild prices, dbt models and exports from what is already loaded.",
)

monthly_refresh = define_asset_job(
    "monthly_refresh",
    selection=AssetSelection.all(),
    partitions_def=fiscal_years,
    description="Reload the current fiscal year, then rebuild everything downstream.",
)


@schedule(job=monthly_refresh, cron_schedule="0 6 8 * *", execution_timezone="America/Denver")
def monthly_schedule(context):
    """Runs on the 8th of each month, after USAspending refreshes its archive files."""
    when = context.scheduled_execution_time
    fiscal_year = when.year + (1 if when.month >= 10 else 0)
    fiscal_year = min(max(fiscal_year, FIRST_FY), LAST_FY)
    return RunRequest(partition_key=str(fiscal_year))


defs = Definitions(
    assets=[raw_contract_transactions, raw_price_index, dbt_models, powerbi_exports],
    jobs=[full_refresh, monthly_refresh],
    schedules=[monthly_schedule],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)
