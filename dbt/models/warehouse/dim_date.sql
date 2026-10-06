-- One row per calendar day, with federal fiscal periods (fiscal year starts 1 October).
select
    d::date                                                  as date_key,
    date_trunc('month', d)::date                             as month_start,
    extract(year from d)::int                                as calendar_year,
    extract(month from d)::int                               as calendar_month,
    extract(year from d + interval '3 months')::int          as fiscal_year,
    extract(quarter from d + interval '3 months')::int       as fiscal_quarter
from generate_series(
    date '2017-10-01',
    (select date_trunc('month', max(action_date)) + interval '1 month - 1 day'
     from {{ ref('stg_contract_transactions') }}),
    interval '1 day'
) as d
