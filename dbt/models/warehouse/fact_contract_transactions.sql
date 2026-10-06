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
    performance_current_end_date
from {{ ref('stg_contract_transactions') }}
