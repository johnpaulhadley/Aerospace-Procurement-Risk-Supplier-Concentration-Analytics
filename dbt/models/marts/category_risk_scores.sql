-- Category x month risk indicators and a composite score. Feeds the Executive page.
--
-- The score is the equal-weighted average of five percentile ranks, 0 to 100,
-- ranked among material categories in the same month and level:
--   concentration (HHI), not-competed share, modifications per new award,
--   extension rate, and year-over-year producer price change.
-- A category is material when its trailing 12-month obligations are at least
-- $100 million. Others get no score, because their shares are unstable.
-- The score ranks where to look first. It is not a measure of supplier performance.
with metrics as (
    select * from {{ ref('category_monthly_metrics') }}
),

joined as (
    select
        m.category_level,
        m.category_code,
        m.month_start,
        m.month_obligation,
        m.t12m_obligation,
        m.t12m_supplier_count,
        m.hhi,
        m.top4_share,
        m.top_supplier_share,
        least(greatest(m.not_competed_share, 0), 1)             as not_competed_share,
        b.modifications_per_new_award,
        b.extension_rate,
        x.series_id                                             as price_series_id,
        x.yoy_change                                            as price_yoy_change,
        m.t12m_obligation * x.yoy_change                        as cost_escalation_exposure,
        m.t12m_obligation >= 100000000                          as is_material
    from metrics m
    left join {{ ref('category_monthly_behavior') }} b
        using (category_level, category_code, month_start)
    left join {{ ref('price_index_map') }} map
        on map.psc_group = left(m.category_code, 2)
    left join {{ ref('price_index_map') }} fallback
        on fallback.psc_group = 'DEFAULT'
    left join {{ ref('fact_price_index') }} x
        on x.series_id = coalesce(map.series_id, fallback.series_id)
       and x.month_start = m.month_start
),

ranked as (
    select
        *,
        percent_rank() over w_hhi   as hhi_rank,
        percent_rank() over w_nc    as not_competed_rank,
        percent_rank() over w_mod   as modification_rank,
        percent_rank() over w_ext   as extension_rank,
        percent_rank() over w_price as price_rank
    from joined
    where is_material
    window
        w_hhi   as (partition by category_level, month_start order by hhi),
        w_nc    as (partition by category_level, month_start order by not_competed_share),
        w_mod   as (partition by category_level, month_start order by coalesce(modifications_per_new_award, 0)),
        w_ext   as (partition by category_level, month_start order by coalesce(extension_rate, 0)),
        w_price as (partition by category_level, month_start order by coalesce(price_yoy_change, 0))
)

select
    j.*,
    case
        when j.hhi >= 2500 then 'High'
        when j.hhi >= 1500 then 'Moderate'
        when j.hhi is not null then 'Low'
    end                                                         as concentration_band,
    round(100 * (r.hhi_rank + r.not_competed_rank + r.modification_rank
                 + r.extension_rank + r.price_rank) / 5)        as risk_score
from joined j
left join ranked r using (category_level, category_code, month_start)
