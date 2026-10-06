-- Fails if a category group with material spend has no proper name.
select distinct category_code, category_name
from {{ ref('category_risk_scores') }}
where category_level = 'psc_group' and is_material
  and (category_name is null or category_name = 'Unclassified')
