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
