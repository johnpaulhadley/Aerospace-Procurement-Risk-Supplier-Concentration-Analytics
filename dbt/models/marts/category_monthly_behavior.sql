-- Category x month modification and schedule indicators on a trailing 12-month window.
-- Built at the same two levels as category_monthly_metrics.
with base as (
    select
        f.psc_key                    as psc_code,
        p.psc_group,
        f.action_month               as month_start,
        f.is_modification,
        f.end_date_moved_days
    from {{ ref('fact_contract_transactions') }} f
    join {{ ref('dim_product_service') }} p using (psc_key)
),

months as (
    select distinct month_start from base
),

{% for level, col in [('psc', 'psc_code'), ('psc_group', 'psc_group')] %}
{{ level }}_month as (
    select
        {{ col }} as category_code,
        month_start,
        count(*) filter (where not is_modification)                           as new_awards,
        count(*) filter (where is_modification)                               as modifications,
        count(*) filter (where is_modification and end_date_moved_days > 30)  as extensions
    from base
    group by 1, 2
),

{{ level }}_trailing as (
    select
        '{{ level }}'                as category_level,
        c.category_code,
        m.month_start,
        sum(c.new_awards)            as t12m_new_awards,
        sum(c.modifications)         as t12m_modifications,
        sum(c.extensions)            as t12m_extensions
    from months m
    join {{ level }}_month c
        on c.month_start between m.month_start - interval '11 months' and m.month_start
    group by 2, 3
){{ "," if not loop.last }}
{% endfor %}

select
    *,
    t12m_modifications::numeric / nullif(t12m_new_awards, 0)   as modifications_per_new_award,
    t12m_extensions::numeric / nullif(t12m_modifications, 0)   as extension_rate
from (
    select * from psc_trailing
    union all
    select * from psc_group_trailing
) u
