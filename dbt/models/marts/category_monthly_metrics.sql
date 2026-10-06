-- Category x month concentration metrics on a trailing 12-month window.
-- Built at two levels: the 4-digit PSC and the 2-digit PSC group.
-- Feeds the Executive and Commodity pages.
--
-- HHI = sum of squared supplier shares x 10,000. A supplier whose trailing
-- 12-month net obligation is negative (more de-obligated than obligated) is
-- treated as holding no share.
with base as (
    select
        f.supplier_key,
        f.psc_key                    as psc_code,
        p.psc_group,
        f.action_month               as month_start,
        f.obligation_amount,
        f.is_not_competed
    from {{ ref('fact_contract_transactions') }} f
    join {{ ref('dim_product_service') }} p using (psc_key)
),

months as (
    select distinct month_start from base
),

{% for level, col in [('psc', 'psc_code'), ('psc_group', 'psc_group')] %}
{{ level }}_supplier_month as (
    select {{ col }} as category_code, supplier_key, month_start,
           sum(obligation_amount) as net_obligation,
           sum(obligation_amount) filter (where is_not_competed) as not_competed_obligation
    from base
    group by 1, 2, 3
),

{{ level }}_trailing as (
    select
        m.month_start,
        s.category_code,
        s.supplier_key,
        sum(s.net_obligation)                                         as t12m_obligation,
        coalesce(sum(s.not_competed_obligation), 0)                   as t12m_not_competed,
        sum(s.net_obligation) filter (where s.month_start = m.month_start) as month_obligation
    from months m
    join {{ level }}_supplier_month s
        on s.month_start between m.month_start - interval '11 months' and m.month_start
    group by 1, 2, 3
),

{{ level }}_ranked as (
    select
        *,
        greatest(t12m_obligation, 0)
            / nullif(sum(greatest(t12m_obligation, 0)) over (partition by category_code, month_start), 0) as supplier_share,
        row_number() over (partition by category_code, month_start order by t12m_obligation desc)        as supplier_rank
    from {{ level }}_trailing
),

{{ level }}_metrics as (
    select
        '{{ level }}'                                             as category_level,
        category_code,
        month_start,
        coalesce(sum(month_obligation), 0)                        as month_obligation,
        sum(t12m_obligation)                                      as t12m_obligation,
        count(*) filter (where t12m_obligation > 0)               as t12m_supplier_count,
        round(sum(supplier_share * supplier_share) * 10000)       as hhi,
        sum(supplier_share) filter (where supplier_rank <= 4)     as top4_share,
        max(supplier_share)                                       as top_supplier_share,
        sum(t12m_not_competed) / nullif(sum(t12m_obligation), 0)  as not_competed_share
    from {{ level }}_ranked
    group by 2, 3
){{ "," if not loop.last }}
{% endfor %}

select * from psc_metrics
union all
select * from psc_group_metrics
