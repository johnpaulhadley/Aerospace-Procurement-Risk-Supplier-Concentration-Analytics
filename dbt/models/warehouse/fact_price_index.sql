-- One row per price index series per month, with year-over-year change.
select
    series_id,
    series_name,
    date_trunc('month', observation_date)::date               as month_start,
    index_value,
    index_value / nullif(lag(index_value, 12) over (
        partition by series_id order by observation_date), 0) - 1 as yoy_change
from {{ source('raw', 'price_index') }}
