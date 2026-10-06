# Business case, scope and KPI definitions

## Decision supported
A procurement or category-management lead for DoD and NASA aerospace buying needs to know **which product categories and suppliers carry the most concentration, cost, modification and schedule exposure**, so mitigation effort (second sourcing, competition, pricing review) goes where the dollars are.

## Perspective
USAspending records what federal agencies buy. "Supplier" here means a **prime contractor selling to the government**. Northrop Grumman appears in this data as a supplier. The analysis is the buyer's view of the aerospace industrial base. Prime-to-subcontractor data is a possible later extension.

## Scope
| Item | Definition |
|---|---|
| Agencies | Department of Defense and NASA (awarding agency) |
| Award types | Prime contracts: definitive contracts, purchase orders, delivery orders, BPA calls |
| Period | Federal FY2018 to present (action date on or after 2017-10-01) |
| Categories | A transaction is in scope if either rule holds. Product rule: Product or Service Code (PSC) groups 14 guided missiles, 15 aircraft and airframe structures, 16 aircraft components, 17 launch/landing/ground handling, 18 space vehicles, 28 engines and turbines. Industry rule: NAICS 3364xx, aerospace product and parts manufacturing, which adds R&D, sustainment and engineering support. Each row records which rule matched (`scope_basis`). |
| Grain | One row per contract transaction (base award or modification) |

Scope and field availability were checked against June 2024 data; see `sample_findings.md`.

## Guardrail
No supplier is labelled late, poor quality or deficient. Public contract data supports statements about spend, concentration, modifications, competition and changes in performance dates. It does not contain delivery or defect records. Every metric below is a **risk indicator**, not a performance verdict.

## Definitions
- **Supplier**: recipient parent UEI where present, otherwise recipient UEI. Names are standardized in staging.
- **Obligation**: federal action obligation on a transaction. De-obligations are negative and are kept, so all spend figures are net.
- **Category**: 4-digit PSC, rolled up to 2-digit PSC group.

## KPIs
| # | KPI | Definition | Reads as |
|---|---|---|---|
| 1 | Supplier concentration (HHI) | Sum of squared supplier shares of net obligations within a category, rolling 12 months, on a 0 to 10,000 scale | Higher means fewer suppliers hold the spend. Default bands: under 1,500 low, 1,500 to 2,500 moderate, over 2,500 high (configurable) |
| 2 | Top-4 share | Share of category obligations held by the four largest suppliers, rolling 12 months | Simple companion to HHI |
| 3 | Limited-competition share | Share of obligations on awards not competed, or competed with one offer received | Dependency on a single source |
| 4 | Modification intensity | Modifications per new award over a trailing 12 months | Categories whose awards are changed most often |
| 5 | Schedule movement | Share of modifications that move an award's current end date later by more than 30 days, trailing 12 months | Categories whose completion dates keep moving |
| 6 | Cost escalation exposure | Year-over-year change in the mapped producer price index, multiplied by trailing 12-month obligations | Dollars exposed to rising input prices |
| 7 | Supplier financial exposure | Net obligations by supplier, category and place of performance state | Where money is concentrated |
| 8 | Composite risk score | Equal-weighted average of the percentile ranks of KPIs 1, 3, 4, 5 and 6 among material categories in the same month, 0 to 100 | A ranking aid for where to look first. Weights are documented and adjustable |

Material categories are those with at least $100 million in trailing 12-month obligations. Smaller categories get no score because their shares are unstable.

Reading the score with spend. The score ignores size, so each material category also gets a priority tier from two thresholds, a score of 50 and $1 billion in trailing 12-month obligations:

| Tier | Rule |
|---|---|
| 1 Act first | score 50 or more and spend $1 billion or more |
| 2 Watch | spend $1 billion or more, score under 50 |
| 3 Review | score 50 or more, spend under $1 billion |
| 4 Monitor | everything else |

Category groups: products group on the first two characters of the PSC, research and development on the first two (separating defense from space R&D), and other services on their first letter. Group names come from the `psc_group_names` seed.

Price indices (FRED, Bureau of Labor Statistics): engines use the aircraft engine and engine parts index, aircraft components use the other aircraft parts index, and every other category uses the broad aerospace product and parts index. No missile-specific index is used, so price change separates categories only weakly.

## Success criteria
1. A named, dollar-denominated answer to: which five categories carry the most exposed spend, and why.
2. Every dashboard number traceable to a dbt model and a raw transaction.
3. Dashboards read from monthly marts, not from the transaction table.
4. Limitations stated beside the findings.
