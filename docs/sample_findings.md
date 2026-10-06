# Sample pull findings (2026-10-05)

Checked against the live USAspending API before freezing the schema.

| Question | Finding | Consequence |
|---|---|---|
| Does the transaction search API carry the fields the KPIs need? | No. It returns about 16 summary fields. Competition, pricing type and period-of-performance dates are missing. | Search API is used for reconciliation checks only. |
| Does the bulk download API carry them? | Yes. A test job returned 297 columns per transaction. | Bulk download API is the ingestion source for both backfill and incremental loads. |
| Page size limit on search | 100 rows per page | Confirms search is unsuitable for backfill. |
| Volume in scope | About 97,000 transactions in FY2024 for DoD and NASA across PSC groups 14, 15, 16, 17, 18 and 28 (group 16: 41,174; 15: 36,729; 28: 10,735; 14: 4,194; 17: 3,985; 18: 192) | Roughly 0.8 to 0.9 million in-scope rows for FY2018 to present, if other years are similar. The raw monthly files hold every DoD and NASA contract action and are far larger. |
| Is a program field available? | `dod_acquisition_program_description` exists (for example "KC-46A"). Fill rate not yet measured. | A program level in the drilldown is possible for DoD if coverage is adequate. |
| Do suppliers need parent roll-up? | Yes. One company appears under several UEIs with a shared parent UEI. | `dim_supplier` keys on parent UEI. |

Not yet verified: PSC filter behaviour on the bulk endpoint (scope is filtered after download), fill rates of competition and program fields, and the FRED price-index series mapping.

# One-month profile: June 2024 (2026-10-05)

Source: bulk download files for DoD and NASA, action dates 2024-06-01 to 2024-06-30. One month only, so shares may differ in other periods.

## Volume and timing
| Measure | Value |
|---|---|
| Raw rows, all DoD and NASA contract actions | 297,855 (DoD 296,311; NASA 1,544) |
| In-scope rows, PSC groups 14/15/16/17/18/28 | 6,755 (2.3% of raw) |
| In-scope awards / supplier UEIs / parent UEIs | 6,372 / 1,035 / 870 |
| Net obligations, all rows | $38.4B |
| Net obligations, in scope | $6.48B |
| DoD file build and download time | about 21 minutes (641 MB unzipped) |

## Scope coverage
| Slice | Rows | Net obligations |
|---|---|---|
| PSC groups and NAICS 3364 | 5,661 | $6.06B |
| PSC groups only | 1,094 | $0.42B |
| NAICS 3364 only (R&D, sustainment, support) | 4,975 | $1.69B |

Northrop Grumman parents: $1.08B net in the month across all categories, $116M inside the PSC-only scope, $256M inside PSC or NAICS 3364.

## Field quality (in-scope rows)
| Field | Finding |
|---|---|
| Transaction key | 100% filled, no duplicates |
| Obligation amount | 488 negative rows (-$322M), 1,862 zero-dollar rows (28%) |
| Parent UEI and name | 100% filled, but parents are not fully consolidated: "LOCKHEED MARTIN CORP" and "LOCKHEED MARTIN CORPORATION", and two Northrop Grumman entities, appear as separate parents |
| Recipient names | Up to 17 distinct names under one parent UEI; 132 UEIs have more than one raw name |
| `extent_competed` | 100% filled |
| `number_of_offers_received` | 60% filled |
| `dod_acquisition_program_description` | 99% filled, but 93% of rows are "NONE"; named programs cover 67.5% of net dollars |
| `major_program` | 0.5% filled; not usable |
| `action_type` | 40% filled |
| Performance dates | 100% filled |

## Decisions these findings drive
- Backfill uses USAspending's pre-built yearly archive files; the monthly API job is kept for incremental loads.
- Limited-competition KPI is built on `extent_competed`; offers received is a secondary signal.
- Program drilldown is dollar-weighted and DoD only.
- `dim_supplier` needs a manual parent-consolidation mapping on top of parent UEI.
