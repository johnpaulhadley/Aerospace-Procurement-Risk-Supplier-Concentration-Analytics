-- Supplier x PSC group x month. Feeds the Supplier Risk page.
with monthly as (
    select
        f.supplier_key,
        p.psc_group,
        f.action_month                                        as month_start,
        sum(f.obligation_amount)                              as net_obligation,
        count(distinct f.contract_key)                        as contract_count,
        count(*) filter (where f.is_modification)             as modification_count,
        sum(f.obligation_amount) filter (where f.is_not_competed) as not_competed_obligation
    from {{ ref('fact_contract_transactions') }} f
    join {{ ref('dim_product_service') }} p using (psc_key)
    group by 1, 2, 3
)

select
    m.*,
    s.supplier_name,
    sum(m.net_obligation) over (partition by m.psc_group, m.month_start)          as group_month_obligation,
    m.net_obligation
        / nullif(sum(m.net_obligation) over (partition by m.psc_group, m.month_start), 0) as share_of_group_month,
    sum(m.net_obligation) over (
        partition by m.supplier_key, m.psc_group
        order by m.month_start
        range between interval '11 months' preceding and current row
    )                                                                             as trailing_12m_obligation
from monthly m
join {{ ref('dim_supplier') }} s using (supplier_key)
