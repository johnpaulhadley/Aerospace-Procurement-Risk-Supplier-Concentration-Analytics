# Power BI build guide

This guide builds the four-page report from the CSV files in `data/processed/powerbi/`. Work through it in order. Expect two to three hours the first time.

## 0. Before you start

1. On the Mac, from the repo folder with the environment active:
   ```
   python ingestion/export_powerbi.py
   ```
   It writes seven CSV files to `data/processed/powerbi/`.
2. In Parallels, start Windows. If no Windows machine exists yet, Parallels offers to download and install Windows 11 when you create a new virtual machine.
3. In Windows, install **Power BI Desktop** from the Microsoft Store and sign in with your ASU account.
4. Find the files from Windows. Parallels shares the Mac home folder with Windows, normally as the network path `\\Mac\Home`. The files should be at:
   ```
   \\Mac\Home\Projects\Aerospace-Procurement-Risk-Supplier-Concentration-Analytics\data\processed\powerbi
   ```
   If that path does not open, copy the `powerbi` folder to the Windows desktop and use that copy.

## 1. Load the data

**Home > Get data > Text/CSV**, once per file. Click **Transform Data** on the first one so the Power Query editor opens, then use **New Source** for the rest.

| File | Rename the query to | Rows are |
|---|---|---|
| `month.csv` | Month | one per month |
| `category_group.csv` | Category Group | one per category group |
| `category_group_monthly.csv` | Group Monthly | category group x month |
| `category_detail_monthly.csv` | Detail Monthly | 4-digit category x month |
| `supplier_monthly.csv` | Supplier Monthly | supplier x category group x month |
| `contracts.csv` | Contracts | one per award of $1M or more |
| `price_index.csv` | Price Index | index series x month |

In Power Query, check these column types before **Close & Apply**:

- `psc_group` and `psc_code`: **Text** in every table. Power BI will guess whole number for codes like `15`, which breaks the joins to codes like `AC`. Fix this first.
- `award_piid` in Contracts: **Text**. Award IDs mix letters and digits, and Power BI guesses whole number, which turns most rows into errors. Choose **Replace current** when asked.
- If the load stalls on "Detecting relationships", cancel it and untick **File > Options and settings > Options > Current File > Data Load > Autodetect new relationships after data is loaded**.
- `month_start` and the date columns in Contracts: **Date**.
- Dollar columns: **Decimal Number**.
- `hhi`, `risk_score`, `priority_rank`, `fiscal_year`: **Whole Number**.
- Share and rate columns: **Decimal Number**.

## 2. Relationships

Open **Model view** and create these. All are one-to-many, single direction, from the first table to the second.

| From (one) | To (many) | Column |
|---|---|---|
| Month | Group Monthly | `month_start` |
| Month | Detail Monthly | `month_start` |
| Month | Supplier Monthly | `month_start` |
| Month | Price Index | `month_start` |
| Category Group | Group Monthly | `psc_group` |
| Category Group | Detail Monthly | `psc_group` |
| Category Group | Supplier Monthly | `psc_group` |
| Category Group | Contracts | `psc_group` |

Delete any other relationship Power BI created by itself. Do not mark Month as a date table: that requires one row per day, and this table has one row per month. None of the measures use built-in time calculations. Untick **Auto date/time** under **File > Options and settings > Options > Current File > Data Load**.

Sort `Month[month_label]` by `Month[month_start]` (select the column, **Column tools > Sort by column**), so months appear in calendar order.

## 3. Measures

Create an empty table to hold them: **Home > Enter data**, name it `Measures`, load it. Add each measure with **New measure**.

How the data behaves, which the measures depend on:

- `month_obligation` is additive. It can be summed across months and categories.
- `t12m_obligation`, `hhi` and the shares are trailing-12-month snapshots. They are valid for one month at a time and must never be summed across months. The snapshot measures below return blank unless exactly one month is in context.

```DAX
Total Obligation = SUM ( 'Group Monthly'[month_obligation] )

Trailing 12M Obligation =
IF ( HASONEVALUE ( 'Month'[month_start] ), SUM ( 'Group Monthly'[t12m_obligation] ) )

Concentrated Obligation =
IF (
    HASONEVALUE ( 'Month'[month_start] ),
    CALCULATE ( SUM ( 'Group Monthly'[t12m_obligation] ), 'Group Monthly'[concentration_band] = "High" )
)

Concentrated Share = DIVIDE ( [Concentrated Obligation], [Trailing 12M Obligation] )

Not Competed Share =
IF (
    HASONEVALUE ( 'Month'[month_start] ),
    DIVIDE (
        SUMX ( 'Group Monthly', 'Group Monthly'[not_competed_share] * 'Group Monthly'[t12m_obligation] ),
        SUM ( 'Group Monthly'[t12m_obligation] )
    )
)

Cost Escalation Exposure =
IF ( HASONEVALUE ( 'Month'[month_start] ), SUM ( 'Group Monthly'[cost_escalation_exposure] ) )

Tier 1 Obligation =
IF (
    HASONEVALUE ( 'Month'[month_start] ),
    CALCULATE ( SUM ( 'Detail Monthly'[t12m_obligation] ), 'Detail Monthly'[priority_rank] = 1 )
)

Tier 1 Categories =
IF (
    HASONEVALUE ( 'Month'[month_start] ),
    CALCULATE ( DISTINCTCOUNT ( 'Detail Monthly'[psc_code] ), 'Detail Monthly'[priority_rank] = 1 )
)

Tier 1 Share = DIVIDE ( [Tier 1 Obligation], [Trailing 12M Obligation] )

Group HHI = IF ( HASONEVALUE ( 'Month'[month_start] ), AVERAGE ( 'Group Monthly'[hhi] ) )

Supplier Obligation = SUM ( 'Supplier Monthly'[net_obligation] )

Supplier Share =
DIVIDE (
    [Supplier Obligation],
    CALCULATE (
        [Supplier Obligation],
        REMOVEFILTERS ( 'Supplier Monthly'[supplier_name], 'Supplier Monthly'[supplier_key] )
    )
)

Supplier Not Competed Share =
DIVIDE ( SUM ( 'Supplier Monthly'[not_competed_obligation] ), [Supplier Obligation] )

Supplier Modifications = SUM ( 'Supplier Monthly'[modification_count] )

Active Suppliers =
CALCULATE ( DISTINCTCOUNT ( 'Supplier Monthly'[supplier_key] ), 'Supplier Monthly'[net_obligation] > 0 )

Contract Value = SUM ( Contracts[net_obligation] )

Contract Count = COUNTROWS ( Contracts )
```

Format `Total Obligation`, `Trailing 12M Obligation`, `Concentrated Obligation`, `Cost Escalation Exposure`, `Tier 1 Obligation`, `Supplier Obligation` and `Contract Value` as currency with display units set to billions on cards. Format every share as a percentage with no decimals.

`Group HHI` is only meaningful with one category group in context. Use it with category group on an axis or legend, never on a card for the whole portfolio.

Check your build against the pipeline: with the month slicer on September 2025, `Trailing 12M Obligation` should read $137.2B, `Tier 1 Obligation` $89.8B and `Tier 1 Categories` 10.

## 4. Pages

Put the same title bar on every page and keep one accent colour for "high" (concentration band High, tier 1). Use colour for meaning only.

### Page 1: Executive Overview

Question it answers: where is the exposure, and is it growing?

- **Slicer:** `Month[month_label]`, single select, dropdown. Default to Sep 2025, the latest complete fiscal year. Title it "As of (trailing 12 months)".
- **Cards, one row:** `Trailing 12M Obligation`, `Concentrated Share`, `Not Competed Share`, `Tier 1 Obligation`, `Tier 1 Categories`, `Cost Escalation Exposure`.
- **Scatter chart** (the centrepiece), from Detail Monthly:
  - Values: `psc_description`. X axis: `risk_score` (average). Y axis: `t12m_obligation` (sum), logarithmic scale. Size: `t12m_obligation`. Legend: `priority_tier`.
  - Visual filter: `is_material` is True.
  - Add constant lines at X = 50 and Y = 1,000,000,000 from the Analytics pane, so the four tiers appear as quadrants.
- **Line chart:** X `Month[month_start]`, Y `Concentrated Share`. This shows the nine-year trend.
- **Table:** tier 1 categories with `psc_code`, `psc_description`, `t12m_obligation`, `hhi`, `not_competed_share`, `extension_rate`, `risk_score`. Visual filter `priority_rank` = 1, sorted by obligation.

The line chart must ignore the month slicer, or it will show one point. Select the slicer, choose **Format > Edit interactions**, and set the line chart to **None**.

### Page 2: Supplier Risk

Question it answers: who holds the spend, and how has that changed?

- **Slicers:** `Month[fiscal_year_label]` (multi-select) and `Category Group[category_name]`.
- **Bar chart:** top 15 suppliers by `Supplier Obligation`. Use a Top N visual filter on `supplier_name`.
- **Line chart:** X `Month[fiscal_year]`, Y `Supplier Share`, legend `supplier_name`, Top N filter of 6 by `Supplier Obligation`. With the missiles group selected this shows Raytheon as a separate supplier through 2020 and RTX after the merger.
- **Table:** `supplier_name`, `Supplier Obligation`, `Supplier Share`, `Supplier Not Competed Share`, `Supplier Modifications`.
- **Card:** `Active Suppliers`.

Add a text box: "Suppliers are shown under the owner at the time of each contract action. Mergers take effect on their closing date."

### Page 3: Commodity and Cost Risk

Question it answers: which categories are concentrated, uncompeted or exposed to rising prices?

- **Slicer:** `Category Group[is_core_aerospace_product]`, default True, so the page opens on the six core product groups.
- **Line chart:** X `Month[month_start]`, Y `Group HHI`, legend `Category Group[category_name]`. Add constant lines at 1,500 and 2,500.
- **Bar chart:** `Category Group[category_name]` by `Not Competed Share`, with the same single-select month slicer as page 1.
- **Line chart:** X `Month[month_start]`, Y average of `Price Index[yoy_change]`, legend `series_name`.
- **Matrix:** rows `category_name`, values `Trailing 12M Obligation`, `Group HHI`, `Not Competed Share`, `Cost Escalation Exposure`.

Add a text box: "Concentration is measured on trailing 12-month obligations and moves when large awards land. Read the trend, not a single month."

### Page 4: Contract Drilldown

Question it answers: which awards sit behind a number?

- **Slicers:** `Category Group[category_name]`, `Contracts[supplier_name]` (dropdown with search), `Contracts[acquisition_program]`, `Contracts[extent_competed]`.
- **Cards:** `Contract Count`, `Contract Value`.
- **Table:** `award_piid`, `supplier_name`, `psc_description`, `acquisition_program`, `pricing_type`, `extent_competed`, `net_obligation`, `modification_count`, `end_date_movement_days`, `first_action_date`, `latest_end_date`, `usaspending_permalink`.
- Set `usaspending_permalink` to **Column tools > Data category > Web URL**, then turn on the URL icon in the table's formatting so each row links to its public record.

Add a text box: "Awards of $1 million or more. Awards signed before FY2018 show activity from FY2018 onward only. These are public contract records, not measures of supplier performance."

## 5. Publish

1. Save the file as `dashboards/aerospace_procurement_risk.pbix` in the repo folder. The data is embedded, so the file is large and is excluded from git. The README links to the published report and screenshots instead.
2. **Home > Publish > My workspace.**
3. For a public link, open the report at app.powerbi.com and choose **File > Embed report > Publish to web (public)**. Universities often disable this for student accounts. If the option is missing or blocked, use screenshots and a short screen recording in the README.
4. Export each page as a PNG (**File > Export > Export to PDF**, or screenshots) into `images/` for the README.

## 6. Checks before sharing

- The three figures in section 3 match.
- Every snapshot card is blank when no month is selected, and filled when one is.
- No visual sums `t12m_obligation` or `hhi` across months.
- Codes such as `AC` and `J` appear in the category slicer. If only numbers appear, `psc_group` was typed as a number.
