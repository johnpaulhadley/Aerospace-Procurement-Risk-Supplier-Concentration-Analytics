-- One row per contract action, keyed to the dimensions.
{{ config(
    indexes=[
        {'columns': ['date_key']},
        {'columns': ['supplier_key']},
        {'columns': ['psc_key']},
        {'columns': ['contract_key']},
    ]
) }}

select
    transaction_key,
    award_key                                                 as contract_key,
    md5(parent_name)                                          as supplier_key,
    md5(agency_name || '|' || sub_agency_name || '|' || coalesce(office_code, '')) as agency_key,
    psc_code                                                  as psc_key,
    md5(coalesce(performance_country_code, '') || '|' || coalesce(performance_state_code, '')) as location_key,
    action_date                                               as date_key,
    action_month,
    fiscal_year,
    modification_number,
    is_modification,
    action_type,
    scope_basis,
    is_not_competed,
    obligation_amount,
    performance_current_end_date,
    -- Days the award's current end date moved on this action, compared with the
    -- previous action on the same award. Null on an award's first action in the data.
    performance_current_end_date - lag(performance_current_end_date) over (
        partition by award_key order by action_date, modification_number
    )                                                         as end_date_moved_days
from {{ ref('stg_contract_transactions') }}
