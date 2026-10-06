-- Fails if monthly obligations in either mart differ from the fact table.
with fact as (select sum(obligation_amount) as total from {{ ref('fact_contract_transactions') }}),
supplier as (select sum(net_obligation) as total from {{ ref('supplier_monthly_metrics') }}),
category as (select sum(month_obligation) as total from {{ ref('category_monthly_metrics') }} where category_level = 'psc'),
grp as (select sum(month_obligation) as total from {{ ref('category_monthly_metrics') }} where category_level = 'psc_group')
select 'supplier' as mart, supplier.total, fact.total as fact_total from supplier, fact where abs(supplier.total - fact.total) > 0.01
union all
select 'category', category.total, fact.total from category, fact where abs(category.total - fact.total) > 0.01
union all
select 'group', grp.total, fact.total from grp, fact where abs(grp.total - fact.total) > 0.01
