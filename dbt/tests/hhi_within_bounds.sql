-- Fails if any concentration value falls outside its possible range.
select * from {{ ref('category_monthly_metrics') }}
where hhi < 0 or hhi > 10000 or top4_share > 1.000001 or top4_share < 0
