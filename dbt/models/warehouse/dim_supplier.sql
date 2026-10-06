-- One row per consolidated parent company.
-- The key is built from the consolidated parent name because the source
-- sometimes splits one company across several parent UEIs.
with t as (
    select * from {{ ref('stg_contract_transactions') }}
),

home_state as (
    select distinct on (parent_name)
        parent_name, recipient_state_code, recipient_country_code
    from (
        select parent_name, recipient_state_code, recipient_country_code,
               sum(abs(obligation_amount)) as dollars
        from t
        group by 1, 2, 3
    ) s
    order by parent_name, dollars desc
)

select
    md5(t.parent_name)                    as supplier_key,
    t.parent_name                         as supplier_name,
    count(distinct t.parent_uei)          as parent_uei_count,
    count(distinct t.recipient_uei)       as recipient_uei_count,
    count(distinct t.recipient_name)      as recipient_name_count,
    max(h.recipient_state_code)           as primary_state_code,
    max(h.recipient_country_code)         as primary_country_code,
    min(t.action_date)                    as first_action_date,
    max(t.action_date)                    as last_action_date
from t
join home_state h using (parent_name)
group by t.parent_name
