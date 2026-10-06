-- One clean row per contract transaction.
-- The same transaction can arrive in more than one source file (a yearly
-- archive and a later monthly pull), so keep the most recently modified copy.
with source as (
    select * from {{ source('raw', 'contract_transactions') }}
),

deduplicated as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by contract_transaction_unique_key
                order by last_modified_date::timestamptz desc nulls last, _loaded_at desc
            ) as copy_rank
        from source
    ) ranked
    where copy_rank = 1
),

typed as (
    select
        contract_transaction_unique_key                       as transaction_key,
        contract_award_unique_key                             as award_key,
        award_id_piid                                         as award_piid,
        parent_award_id_piid                                  as parent_award_piid,
        modification_number,
        modification_number <> '0'                            as is_modification,

        action_date::date                                     as action_date,
        date_trunc('month', action_date::date)::date          as action_month,
        action_date_fiscal_year::int                          as fiscal_year,
        period_of_performance_start_date::date                as performance_start_date,
        period_of_performance_current_end_date::date          as performance_current_end_date,
        period_of_performance_potential_end_date::date        as performance_potential_end_date,

        federal_action_obligation::numeric(18, 2)             as obligation_amount,
        base_and_all_options_value::numeric(18, 2)            as base_and_all_options_value,
        current_total_value_of_award::numeric(18, 2)          as current_total_value_of_award,
        potential_total_value_of_award::numeric(18, 2)        as potential_total_value_of_award,

        awarding_agency_name                                  as agency_name,
        awarding_sub_agency_name                              as sub_agency_name,
        awarding_office_code                                  as office_code,
        awarding_office_name                                  as office_name,

        recipient_uei,
        upper(trim(recipient_name))                           as recipient_name,
        coalesce(recipient_parent_uei, recipient_uei)         as parent_uei,
        upper(trim(coalesce(recipient_parent_name, recipient_name))) as parent_name_reported,
        recipient_country_code,
        recipient_state_code,
        primary_place_of_performance_country_code             as performance_country_code,
        primary_place_of_performance_state_code               as performance_state_code,

        product_or_service_code                               as psc_code,
        product_or_service_code_description                   as psc_description,
        left(product_or_service_code, 2)                      as psc_group,
        naics_code,
        naics_description,
        case
            when left(product_or_service_code, 2) in ('14', '15', '16', '17', '18', '28')
                 and naics_code like '3364%' then 'product and industry'
            when left(product_or_service_code, 2) in ('14', '15', '16', '17', '18', '28')
                 then 'product only'
            else 'industry only'
        end                                                   as scope_basis,

        award_type,
        type_of_contract_pricing                              as pricing_type,
        action_type,
        extent_competed,
        extent_competed in ('NOT COMPETED', 'NOT COMPETED UNDER SAP',
                            'NOT AVAILABLE FOR COMPETITION')  as is_not_competed,
        nullif(number_of_offers_received, '')::numeric::int   as offers_received,
        nullif(upper(trim(dod_acquisition_program_description)), 'NONE') as acquisition_program,

        transaction_description,
        usaspending_permalink,
        last_modified_date::timestamptz                       as last_modified_at,
        _source_file                                          as source_file,
        _loaded_at                                            as loaded_at
    from deduplicated
)

select
    typed.*,
    coalesce(overrides.consolidated_parent_name, typed.parent_name_reported) as parent_name
from typed
left join {{ ref('supplier_parent_overrides') }} as overrides
    on typed.parent_name_reported = overrides.recipient_parent_name
