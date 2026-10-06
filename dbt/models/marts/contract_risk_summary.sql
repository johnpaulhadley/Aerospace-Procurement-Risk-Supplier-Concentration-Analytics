-- One row per award with modification and schedule indicators.
-- Feeds the Contract Drilldown page. These are risk indicators, not
-- judgements of supplier performance.
select
    c.contract_key,
    c.award_piid,
    s.supplier_name,
    p.psc_code,
    p.psc_description,
    p.category_name,
    c.acquisition_program,
    c.award_type,
    c.pricing_type,
    c.extent_competed,
    c.is_not_competed,
    c.offers_received,
    c.first_action_date,
    c.last_action_date,
    c.first_recorded_end_date,
    c.latest_end_date,
    c.end_date_movement_days,
    c.first_action_obligation,
    c.net_obligation,
    c.net_obligation - c.first_action_obligation              as obligation_change_since_first_action,
    c.action_count,
    c.modification_count,
    c.has_base_action_in_window,
    c.usaspending_permalink
from {{ ref('dim_contract') }} c
join {{ ref('dim_supplier') }} s using (supplier_key)
join {{ ref('dim_product_service') }} p using (psc_key)
