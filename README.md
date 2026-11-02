# Sunrise Coffee: store performance review (2023-2024)

**Bottom line:** London is the one weak region. Its stores sell about as much as the typical store but pay roughly twice the rent share (about 20% of revenue against 9%), so they keep less than half the margin. The loyalty scheme costs **£0.86m a year** in rewards with no visible extra spend from members. Weekend sales run about a quarter below weekdays while staff hours stay flat, which is worth up to **£0.97m a year**.

<!-- Add links here once exported: docs/SunriseCoffee-report.pdf and screenshots/walkthrough.gif -->
No Power BI Desktop? A PDF export of the report and a short walkthrough recording are coming soon. Until then, the screenshots below show every page.

![Overview](screenshots/01-overview.png)

A Power BI report on store profitability, loyalty ROI and labour for a 60-store UK coffee chain, built for the DataDNA Dataset Challenge (October 2026). The brief casts me as a senior commercial analyst reporting to the Chief Commercial Officer. Rather than build "a dashboard", the report is organised around the three decisions the CCO has to make before the 2025 planning cycle.

## The three decisions and what the data says

### 1. Which stores or regions to review or close, and where to expand in 2025

- **London is the one weak region.** Its stores earn a median **8.7% net margin**, against **19.2%** for the typical store. Rent takes about **20% of London revenue**, more than double the estate median (~9%). If London earned the estate median margin it would add roughly **£0.56m a year**.
- **Rent does not buy revenue.** Across stores, rent and revenue are barely related (r = 0.15), but higher rent clearly cuts margin (r = -0.42). Each step up a rent quartile costs about 2-3 margin points.
- **Outside London, regions are not meaningfully different** (p = 0.21), so 2025 site selection should screen on rent as a share of expected revenue rather than on region.
- **Eight stores are flagged for review**, five of them London City-Centre sites. Only one, South London Corner, lost money over the full 24 months (-3.7%).

### 2. Does the loyalty programme earn its redemption cost?

- **Not on this evidence.** Redemption costs about **£0.86m a year** (£863k in 2024), about **10% of net profit**.
- Members spend the same per visit as non-members (spend index 0.997, where 1.0 means no difference), and stores with higher take-up earn no more revenue or margin.
- To break even, members would have to spend about **10% more** than they otherwise would. Nothing in the data shows that uplift. Recommendation: hold further investment and run a controlled test before expanding the scheme.

### 3. Which products to grow, and how to staff for seasonality

- **Mix is flat.** Espresso ~46%, food ~26%, filter ~19% and beans ~9% of sales, with no significant shift between 2023 and 2024. Catalogue margins differ by category, but realised margin is about **62% in every stream**, so there is no mix lever to pull.
- **Weekends are the staffing opportunity.** Saturday and Sunday sales run about **a quarter below weekdays**, but staff hours stay flat. Matching weekend hours to weekday productivity is worth up to roughly **£0.97m a year** (an upper bound).
- **There is no repeatable monthly seasonality.** 2023 and 2024 monthly patterns do not line up, so rotas should be planned by day of week, not by month.

## Report pages

| Page | What it answers |
|---|---|
| **Overview** | Where the business stands going into 2025: four KPI cards against the prior year, where each £1 of sales goes, and profit, margin or sales (switchable) by location and region with drill-down to stores, plus the monthly profit and margin trend. |
| **Rent & Sites** | Where to open in 2025 and which stores need a decision: site-pressure scorecard, margin by rent level, rent against margin for every store coloured by status, and a region heatmap. |
| **Loyalty & Ops** | Whether to invest more in loyalty and how to staff the week: reward cost as a share of member sales by region, sales and reward cost by take-up, sales against staff hours by day, and profit kept per £1 by product against the price list. |
| **Store Deep Dive** | One store at a time: profile and recommended action, margin, rent, loyalty and months-in-profit rings, its monthly trend against the typical store, and its cost per £1 against the estate. |

A synced Year slicer (single select, default 2024) drives every page.

| Rent & Sites | Loyalty & Ops | Store Deep Dive |
|---|---|---|
| ![Rent & Sites](screenshots/02-rent-and-sites.png) | ![Loyalty & Ops](screenshots/03-loyalty-and-ops.png) | ![Store Deep Dive](screenshots/04-store-deep-dive.png) |

## Repo layout

```
powerbi/       the Power BI project (.pbip, Report and SemanticModel folders)
data/          the five challenge CSVs, plus analysis_realised_margin.csv used by the model
docs/          the challenge brief and data dictionary
analysis/      Python analysis that produced the numbers above (see analysis/README.md)
screenshots/   page images used in this README
```

## Data notes

The data has several quirks that change how it has to be used. The full list, with how each is handled, is in [analysis/outputs/data_quality.md](analysis/outputs/data_quality.md).

- **Totals come only from the monthly P&L** (`fact_store_monthly_profitability`). The daily table is a ~20% sample of store-days, does not reconcile with the P&L (r = 0.24), and contains 1,090 duplicated store-days with conflicting values. It is used only for shares, visit values and day-of-week comparisons, with duplicates averaged so each store-day counts once.
- **Profit status is recalculated.** The file's `profitability_status` breaks its own documented bands in 42% of rows, so review status is derived from margin instead.
- **Only two formats exist.** The brief mentions three, but the data has 58 High-Street stores, 2 Transport-Hub stores (both Luton) and no Retail-Park stores, so format comparisons are flagged as small samples.
- **Non-active stores still trade.** The three Temporarily-Closed or Refurbishing stores report revenue in all 24 months.
- Medians are shown beside means, and any group with fewer than 5 stores or 30 rows is flagged as a small sample.

## How to open it

The report is saved as a **Power BI project (.pbip)**, so the model (TMDL) and report (PBIR) are plain text and diff cleanly in Git.

1. Clone or download this repo, for example to `C:\SunriseCoffee`.
2. In Power BI Desktop, make sure the project format is on: `File > Options and settings > Options > Preview features`, tick **Store semantic model using TMDL format** and **Store reports using enhanced metadata format (PBIR)**, then restart.
3. Open `powerbi/SunriseCoffee.pbip`.
4. Point it at the data: `Home > Transform data > Manage parameters`, set **DataFolder** to the repo's `data` folder with a trailing slash, for example `C:\SunriseCoffee\data\`. Then `Home > Refresh`.

## Credits

Dataset: DataDNA Dataset Challenge, October 2026 (Sunrise Coffee Chain). The brief and data dictionary are included in `docs/` for reference. Sunrise Coffee is a fictional company.
