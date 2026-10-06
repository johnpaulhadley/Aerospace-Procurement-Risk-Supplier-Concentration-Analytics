-- One row per Product or Service Code (PSC).
with latest as (
    select distinct on (psc_code)
        psc_code, psc_description
    from {{ ref('stg_contract_transactions') }}
    order by psc_code, action_date desc
),

grouped as (
    select
        psc_code,
        psc_description,
        {{ psc_group('psc_code') }} as psc_group
    from latest
)

select
    g.psc_code                                                as psc_key,
    g.psc_code,
    g.psc_description,
    g.psc_group,
    coalesce(
        n.category_name,
        case when g.psc_code ~ '^A' then 'Other research and development' else 'Unclassified' end
    )                                                         as category_name,
    case
        when g.psc_code ~ '^A' then 'Research and development'
        when g.psc_code ~ '^[B-Z]' then 'Services'
        else 'Products'
    end                                                       as category_type,
    g.psc_group in ('14', '15', '16', '17', '18', '28')       as is_core_aerospace_product
from grouped g
left join {{ ref('psc_group_names') }} n using (psc_group)
