-- One row per award, with attributes taken from its first and latest recorded action.
-- Awards signed before the data window (FY2018) have no base action here, so
-- growth and schedule measures for them start from the first action in the window.
with t as (
    select * from {{ ref('stg_contract_transactions') }}
),

ordered as (
    select
        *,
        row_number() over (partition by award_key order by action_date, modification_number)           as first_rank,
        row_number() over (partition by award_key order by action_date desc, modification_number desc) as last_rank
    from t
),

first_action as (select * from ordered where first_rank = 1),
last_action  as (select * from ordered where last_rank = 1),

totals as (
    select
        award_key,
        sum(obligation_amount)                                  as net_obligation,
        count(*)                                                as action_count,
        count(*) filter (where is_modification)                 as modification_count,
        bool_or(not is_modification)                            as has_base_action_in_window,
        max(acquisition_program)                                as acquisition_program
    from t
    group by award_key
)

select
    f.award_key                                               as contract_key,
    f.award_piid,
    f.parent_award_piid,
    md5(l.parent_name)                                        as supplier_key,
    l.psc_code                                                as psc_key,
    f.award_type,
    l.pricing_type,
    l.extent_competed,
    l.is_not_competed,
    l.offers_received,
    tot.acquisition_program,
    f.action_date                                             as first_action_date,
    l.action_date                                             as last_action_date,
    f.performance_start_date,
    f.performance_current_end_date                            as first_recorded_end_date,
    l.performance_current_end_date                            as latest_end_date,
    l.performance_current_end_date - f.performance_current_end_date as end_date_movement_days,
    f.obligation_amount                                       as first_action_obligation,
    tot.net_obligation,
    l.current_total_value_of_award,
    l.potential_total_value_of_award,
    tot.action_count,
    tot.modification_count,
    tot.has_base_action_in_window,
    f.usaspending_permalink
from first_action f
join last_action l using (award_key)
join totals tot using (award_key)
