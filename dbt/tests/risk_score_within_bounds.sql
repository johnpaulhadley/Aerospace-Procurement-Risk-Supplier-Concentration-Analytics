-- Fails if a score is out of range, or a non-material category has a score.
select * from {{ ref('category_risk_scores') }}
where risk_score < 0 or risk_score > 100 or (not is_material and risk_score is not null)
