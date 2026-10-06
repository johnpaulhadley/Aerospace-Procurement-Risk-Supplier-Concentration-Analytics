-- Fails if two ownership rules for the same reported name cover the same date,
-- which would duplicate transactions.
select a.reported_parent_name, a.valid_from, b.valid_from as other_valid_from
from {{ ref('supplier_ownership') }} a
join {{ ref('supplier_ownership') }} b
  on a.reported_parent_name = b.reported_parent_name
 and a.valid_from < b.valid_from
 and a.valid_to > b.valid_from
