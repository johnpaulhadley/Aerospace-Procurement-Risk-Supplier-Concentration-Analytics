-- One row per place of performance (country and state).
select distinct
    md5(coalesce(performance_country_code, '') || '|' || coalesce(performance_state_code, '')) as location_key,
    performance_country_code as country_code,
    performance_state_code   as state_code,
    coalesce(performance_country_code = 'USA', false) as is_domestic
from {{ ref('stg_contract_transactions') }}
