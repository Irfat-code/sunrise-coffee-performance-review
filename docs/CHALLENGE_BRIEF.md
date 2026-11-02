# DataDNA Challenge — Sunrise Coffee Chain

## 🎯 Your Role

You are a senior commercial analyst at Sunrise Coffee Chain, reporting to the Chief Commercial Officer. The business operates 60 stores across the UK, spanning High-Street, Retail-Park, and Transport-Hub formats. You have been asked to produce a comprehensive performance review covering the 2023–2024 trading period, with a focus on store profitability, loyalty programme effectiveness, and revenue mix trends ahead of next year's expansion planning cycle.

**Difficulty: Medium**

## 📊 The Scenario

Sunrise Coffee Chain has grown steadily over the past five years but the commercial team suspects that performance is diverging sharply between store formats and regions. The Chief Commercial Officer wants to know which stores and formats are genuinely driving the business forward, whether the loyalty programme is generating measurable incremental spend, and how the revenue mix across espresso drinks, filter coffee, food, and retail beans is shifting over time. Your findings will directly inform which regions get prioritised in the 2025 site selection programme and whether the loyalty scheme warrants further investment.

### Dataset Overview

- **Dimensions**: 3 dimension tables — store (60 rows), product (40 rows), date (730 rows: 2023-01-01 to 2024-12-31)
- **Facts**: 2 fact tables:
  - `fact_daily_sales` — 10,000 rows at store x day x top-product grain, capturing daily trading metrics
  - `fact_store_monthly_profitability` — 1,440 rows (60 stores x 24 months) capturing full P&amp;L, loyalty, and footfall at monthly grain
- **Start with**: Use `fact_store_monthly_profitability` for profitability and trend analysis; use `fact_daily_sales` for granular day-of-week and product-mix analysis
- **Currency**: GBP

### Key Business Metrics

- **net\_profit\_gbp** — monthly net profit after all costs (revenue minus COGS minus rent minus staffing minus loyalty redemption)
- **net\_profit\_margin\_pct** — net profit as a percentage of revenue; the primary profitability KPI
- **total\_revenue\_gbp / total\_monthly\_revenue\_gbp** — gross revenue before any deductions
- **loyalty\_adoption\_rate** — fraction of a store's customers using the loyalty app (store-level attribute)
- **loyalty\_member\_revenue\_pct** — fraction of monthly revenue attributable to loyalty members
- **loyalty\_redemption\_cost\_gbp** — cost to the business of redeeming loyalty rewards
- **daily\_gross\_profit\_gbp** — daily revenue minus cost of goods (before fixed costs)
- **revenue\_per\_sqft\_gbp** — monthly revenue efficiency metric for space utilisation

## 🔍 Analysis Areas

### 1 — Store Format and Regional Performance

Compare how High-Street, Retail-Park, and Transport-Hub formats perform on profitability, revenue per square foot, and footfall. Identify which UK regions have the strongest and weakest net profit margins, and flag any stores that may be candidates for review or closure based on `profitability_status`.

### 2 — Loyalty Programme Effectiveness

Assess whether stores with higher `loyalty_adoption_rate` generate higher `loyalty_member_revenue_pct` and `avg_transaction_value_gbp`. Determine whether loyalty redemption costs are outweighing the incremental revenue loyalty members bring, and whether the programme is more effective in certain formats or regions.

### 3 — Revenue Mix and Product Category Trends

Analyse how the four daily revenue streams — espresso, filter, food, and retail beans — are proportioned across stores, formats, and time. Identify whether the food revenue share is growing, and which product categories from `dim_product` generate the highest gross margin for the business.

### 4 — Temporal and Seasonal Patterns

Examine how trading performance changes across the week, around bank holidays, and seasonally across 2023–2024. Identify the peak trading quarters and assess how different store formats respond to seasonal demand shifts.

## ❓ Guiding Questions

Use these questions to structure your analysis. They are starting points — feel free to explore further.

### Store and Format Performance

- Which store format (High-Street, Retail-Park, Transport-Hub) delivers the highest average `net_profit_margin_pct`?
- Which UK regions show the highest concentration of `profitability_status` = Loss-Making or Structural-Loss?
- Do stores with higher `monthly_rent_gbp` necessarily generate higher `total_monthly_revenue_gbp`, or does rent erode profit disproportionately in some formats?
- Which individual stores improved their `net_profit_gbp` most from 2023 to 2024, and which have deteriorated?

### Loyalty Programme

- Is there a positive correlation between `loyalty_adoption_rate` and `loyalty_member_revenue_pct` at a store level?
- Do loyalty members spend more per transaction than non-members, based on `avg_transaction_value_gbp` relative to `loyalty_transactions`?
- What is the net value of the loyalty programme per store: loyalty member revenue contribution minus `loyalty_redemption_cost_gbp`?
- Does `loyalty_adoption_rate` vary significantly by store format or region?

### Revenue Mix

- What proportion of daily revenue comes from espresso drinks vs food vs filter coffee vs retail beans, and how does this split differ by store format?
- Which product categories in `dim_product` carry the highest `gross_margin_pct`, and are those products growing as a share of daily revenue?
- Is `retail_beans_revenue_gbp` growing as a proportion of total revenue — suggesting a stronger at-home coffee consumer base?

### Seasonal and Temporal Patterns

- How does `total_revenue_gbp` differ between weekday and weekend trading across formats?
- Do bank holidays help or hurt revenue for Transport-Hub stores compared with High-Street stores?
- Which months in 2023–2024 show the highest and lowest `net_profit_gbp` across the estate, and does the pattern repeat year-on-year?

## 💡 Impact &amp; Purpose

Your analysis should help the Sunrise Coffee commercial team:

- Identify which store formats and regions to prioritise in the 2025 expansion programme
- Decide whether the loyalty programme is generating a positive return on investment
- Understand which product categories to grow or deprioritise based on revenue mix and margin
- Anticipate seasonal trading patterns to optimise staffing and stock ordering

## 📋 Deliverables

Create a professional analytical report that includes:

1. **Executive Summary**
   - Three to five key findings with clear business implications
   - A headline recommendation for the Chief Commercial Officer
2. **Detailed Analysis**
   - Visualisations showing profitability trends, format comparisons, and revenue mix
   - Store-level performance breakdown with profitability status
   - Loyalty programme net value assessment
3. **Actionable Insights**
   - Stores or regions recommended for review
   - Whether the loyalty programme merits further investment
   - Seasonal trading recommendations for staffing and promotional planning

## 📁 Data Dictionary

See `docs/DATA_DICTIONARY.md` for full column-level documentation of all tables.

## 🚀 Getting Started

1. **Explore the dimensions first**: Review `dim_store` to understand the estate and `dim_product` to understand the product catalogue and margins
2. **Start with monthly profitability**: Use `fact_store_monthly_profitability` for a top-down view of which stores and formats are profitable
3. **Drill into daily patterns**: Use `fact_daily_sales` to explore day-of-week effects, product mix, and loyalty transaction patterns
4. **Join the tables**: Connect facts to dimensions on `store_id`, `date_id`, and `product_id` to add context to every metric
5. **Note nulls**: `seating_capacity` is nullable for some Drive-Thru and Transport-Hub formats; all other key columns are fully populated
6. **Synthesise insights**: Build your narrative around the four analysis areas, connecting findings to the business decisions they should inform

---

