-- One row per awarding office.
select
    md5(agency_name || '|' || sub_agency_name || '|' || coalesce(office_code, '')) as agency_key,
    agency_name,
    sub_agency_name,
    office_code,
    max(office_name) as office_name
from {{ ref('stg_contract_transactions') }}
group by 1, 2, 3, 4
