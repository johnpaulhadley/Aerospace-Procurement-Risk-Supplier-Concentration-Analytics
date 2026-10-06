"""Export the tables the Power BI report reads to data/processed/powerbi/ as CSV.

The report is built on these files so it needs no live database connection.

Usage:
    python ingestion/export_powerbi.py
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from config import database_url

OUT = Path("data/processed/powerbi")
CONTRACT_MIN_DOLLARS = 1_000_000  # the drilldown lists awards at or above this net value

RISK_COLUMNS = """
    r.month_start, r.month_obligation, r.t12m_obligation, r.t12m_supplier_count,
    r.hhi, r.concentration_band, r.top4_share, r.top_supplier_share, r.not_competed_share,
    r.modifications_per_new_award, r.extension_rate, r.price_yoy_change,
    r.cost_escalation_exposure, r.is_material, r.risk_score, r.share_of_total_obligation,
    r.priority_tier, left(r.priority_tier, 1)::int as priority_rank
"""

EXPORTS = {
    "month": """
        select month_start,
               max(fiscal_year) as fiscal_year,
               max(fiscal_quarter) as fiscal_quarter,
               'FY' || max(fiscal_year) as fiscal_year_label,
               to_char(month_start, 'Mon YYYY') as month_label
        from warehouse.dim_date
        group by month_start order by month_start""",
    "category_group": """
        select psc_group, max(category_name) as category_name, max(category_type) as category_type,
               bool_or(is_core_aerospace_product) as is_core_aerospace_product
        from warehouse.dim_product_service
        group by psc_group order by psc_group""",
    "category_group_monthly": f"""
        select r.category_code as psc_group, {RISK_COLUMNS}
        from marts.category_risk_scores r
        where r.category_level = 'psc_group'""",
    "category_detail_monthly": f"""
        select r.category_code as psc_code, p.psc_description, p.psc_group, {RISK_COLUMNS}
        from marts.category_risk_scores r
        join warehouse.dim_product_service p on p.psc_code = r.category_code
        where r.category_level = 'psc'""",
    "supplier_monthly": """
        select supplier_key, supplier_name, psc_group, month_start, net_obligation,
               contract_count, modification_count,
               coalesce(not_competed_obligation, 0) as not_competed_obligation
        from marts.supplier_monthly_metrics""",
    "contracts": f"""
        select c.award_piid, c.supplier_name, c.psc_code, c.psc_description, p.psc_group,
               c.acquisition_program, c.award_type, c.pricing_type, c.extent_competed,
               c.is_not_competed, c.offers_received, c.first_action_date, c.last_action_date,
               c.first_recorded_end_date, c.latest_end_date, c.end_date_movement_days,
               c.first_action_obligation, c.net_obligation, c.action_count,
               c.modification_count, c.has_base_action_in_window, c.usaspending_permalink
        from marts.contract_risk_summary c
        join warehouse.dim_product_service p on p.psc_code = c.psc_code
        where abs(c.net_obligation) >= {CONTRACT_MIN_DOLLARS}""",
    "price_index": "select series_id, series_name, month_start, index_value, yoy_change from warehouse.fact_price_index",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url())
    for name, sql in EXPORTS.items():
        df = pd.read_sql(sql, engine)
        path = OUT / f"{name}.csv"
        df.to_csv(path, index=False)
        print(f"{name}.csv: {len(df):,} rows, {path.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
