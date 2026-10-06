"""Export the dashboard marts and a data-quality summary to data/processed/ as CSV.

The CSVs are what the analysis notebook and Power BI read, so neither needs a
live database connection.

Usage:
    python ingestion/export_marts.py
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from config import database_url

OUT = Path("data/processed")

EXPORTS = {
    "category_monthly_metrics": "select * from marts.category_monthly_metrics",
    "supplier_monthly_metrics": "select * from marts.supplier_monthly_metrics",
    "category_risk_scores": "select * from marts.category_risk_scores",
    "fact_price_index": "select * from warehouse.fact_price_index",
    "dim_supplier": "select * from warehouse.dim_supplier",
    "dim_product_service": "select * from warehouse.dim_product_service",
    "qa_yearly_totals": """
        select fiscal_year, scope_basis, count(*) as transactions,
               count(distinct contract_key) as contracts,
               count(distinct supplier_key) as suppliers,
               sum(obligation_amount) as net_obligation,
               sum(obligation_amount) filter (where obligation_amount < 0) as deobligations,
               count(*) filter (where obligation_amount = 0) as zero_dollar_rows
        from warehouse.fact_contract_transactions
        group by 1, 2 order by 1, 2""",
    "qa_field_coverage": """
        select fiscal_year, count(*) as transactions,
               avg((extent_competed = 'NOT REPORTED')::int) as competition_not_reported_share,
               avg((offers_received is null)::int) as offers_missing_share,
               sum(obligation_amount) filter (where acquisition_program is not null)
                   / nullif(sum(obligation_amount), 0) as program_named_dollar_share
        from staging.stg_contract_transactions
        group by 1 order by 1""",
    "qa_top_suppliers": """
        select s.supplier_name, s.parent_uei_count, s.recipient_name_count,
               sum(f.obligation_amount) as net_obligation
        from warehouse.fact_contract_transactions f
        join warehouse.dim_supplier s using (supplier_key)
        group by 1, 2, 3 order by 4 desc limit 200""",
    "qa_supplier_by_year": """
        select s.supplier_name, f.fiscal_year, sum(f.obligation_amount) as net_obligation
        from warehouse.fact_contract_transactions f
        join warehouse.dim_supplier s using (supplier_key)
        group by 1, 2
        having abs(sum(f.obligation_amount)) >= 50000000
        order by 1, 2""",
    "qa_reported_names": """
        select fiscal_year, parent_name as supplier_name, parent_name_reported, parent_uei,
               recipient_name, sum(obligation_amount) as net_obligation
        from staging.stg_contract_transactions
        group by 1, 2, 3, 4, 5
        having abs(sum(obligation_amount)) >= 50000000
        order by 1, 6 desc""",
    "qa_table_sizes": """
        select schemaname || '.' || relname as table_name, n_live_tup as approx_rows,
               pg_total_relation_size(relid) as bytes
        from pg_stat_user_tables order by 3 desc""",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    engine = create_engine(database_url())
    for name, sql in EXPORTS.items():
        df = pd.read_sql(sql, engine)
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"{name}.csv: {len(df):,} rows")


if __name__ == "__main__":
    main()
