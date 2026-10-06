-- One row per Product or Service Code (PSC).
with latest as (
    select distinct on (psc_code)
        psc_code, psc_description
    from {{ ref('stg_contract_transactions') }}
    order by psc_code, action_date desc
)

select
    psc_code                                                  as psc_key,
    psc_code,
    psc_description,
    left(psc_code, 2)                                         as psc_group,
    case left(psc_code, 2)
        when '14' then 'Guided missiles'
        when '15' then 'Aircraft and airframe structures'
        when '16' then 'Aircraft components and accessories'
        when '17' then 'Aircraft launching, landing and ground handling'
        when '18' then 'Space vehicles'
        when '28' then 'Engines and turbines'
        else case
            when psc_code ~ '^A' then 'Research and development'
            when psc_code ~ '^J' then 'Maintenance and repair'
            when psc_code ~ '^[B-Z]' then 'Other services'
            else 'Other products'
        end
    end                                                       as category_name,
    case
        when psc_code ~ '^A' then 'Research and development'
        when psc_code ~ '^[B-Z]' then 'Services'
        else 'Products'
    end                                                       as category_type
from latest
