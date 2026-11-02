# Data Dictionary

**Theme:** Sunrise Coffee Chain — Store Performance and Loyalty Analytics
**Date Range:** 2023-01-01 to 2024-12-31
**Currency:** GBP

---

## Table of Contents

- [dim_date](#dim_date)
- [dim_store](#dim_store)
- [dim_product](#dim_product)
- [fact_daily_sales](#fact_daily_sales)
- [fact_store_monthly_profitability](#fact_store_monthly_profitability)

---

## dim_date

**Type:** DIMENSION
**Primary Key:** `date_id`
**Rows:** 730

### Description

One row per calendar day from 2023-01-01 to 2024-12-31. All derived columns (year, month, quarter, week, day of week, weekend flag) are computed directly from `full_date` so they are always consistent. The `is_uk_bank_holiday` flag reflects England & Wales bank holidays; `uk_trading_calendar` classifies each day for demand-modelling purposes.

### Columns

| Column Name | Data Type | Nullable | Unique | Description |
|---|---|---|---|---|
| `date_id` | integer | No | Yes (PK) | Sequential date surrogate key (1 = 2023-01-01) |
| `full_date` | date | No | Yes | Calendar date in ISO format (YYYY-MM-DD) |
| `year` | integer | No | No | Calendar year (2023 or 2024) |
| `month_number` | integer | No | No | Month number 1–12 |
| `month_name` | string | No | No | Full month name (e.g. January) |
| `day_of_week` | string | No | No | Full weekday name (e.g. Monday) |
| `is_weekend` | boolean | No | No | True for Saturday and Sunday |
| `is_uk_bank_holiday` | boolean | No | No | True on England & Wales public holidays |
| `quarter` | integer | No | No | Calendar quarter 1–4 |
| `week_number` | integer | No | No | ISO week number |
| `uk_trading_calendar` | string | No | No | Trading day classification: Standard-Trading-Day, Bank-Holiday, Christmas-Period |
| `month_id` | string | No | No | Year-month label used to join to fact_store_monthly_profitability (e.g. 2023-06) |

---

## dim_store

**Type:** DIMENSION
**Primary Key:** `store_id`
**Rows:** 60

### Description

One row per Sunrise Coffee store, capturing format, location, cost structure, and loyalty adoption. City and region are drawn from a coherent UK geographic lookup — every city correctly maps to its stated region.

### Columns

| Column Name | Data Type | Nullable | Unique | Description |
|---|---|---|---|---|
| `store_id` | integer | No | Yes (PK) | Unique store identifier |
| `store_name` | string | No | Yes | Display name including city and location type |
| `store_format` | string | No | No | High-Street, Retail-Park, or Transport-Hub |
| `location_type` | string | No | No | Granular sub-type: City-Centre, Suburban-High-Street, Shopping-Centre, Retail-Park, Roadside-Services, Train-Station, Airport, Bus-Terminal, Hospital, University-Campus |
| `city` | string | No | No | UK city — always geographically correct for its region |
| `region` | string | No | No | UK administrative region: London, South-East, South-West, East-of-England, East-Midlands, West-Midlands, Yorkshire-and-Humber, North-West, North-East, Scotland, Wales, Northern-Ireland |
| `store_status` | string | No | No | Active, Temporarily-Closed, Refurbishing, or Closed-Permanently |
| `monthly_rent_gbp` | float | No | No | Monthly lease cost in GBP (range: £2,000–£40,000) |
| `staff_headcount` | integer | No | No | Total staff employed at this store (range: 3–28) |
| `monthly_staffing_cost_gbp` | float | No | No | Total monthly staff wages in GBP (range: £6,000–£38,000) |
| `loyalty_adoption_rate` | float | No | No | Fraction of customers using the loyalty app (range: 0.05–0.62) |
| `seating_capacity` | integer | Yes | No | Total seats; null for some Drive-Thru and Transport-Hub formats |
| `opening_year` | integer | No | No | Year the store opened (range: 2010–2024) |

---

## dim_product

**Type:** DIMENSION
**Primary Key:** `product_id`
**Rows:** 40

### Description

One row per product in the Sunrise Coffee catalogue, spanning six coherent categories. Product names correctly correspond to their category. Margin is always positive (unit_cost_gbp < unit_price_gbp for all rows).

### Columns

| Column Name | Data Type | Nullable | Unique | Description |
|---|---|---|---|---|
| `product_id` | integer | No | Yes (PK) | Unique product identifier |
| `product_name` | string | No | Yes | Product display name |
| `product_category` | string | No | No | Espresso-Drinks, Filter-Coffee, Food, Retail-Beans, Cold-Drinks, or Merchandise |
| `unit_price_gbp` | float | No | No | Standard retail price in GBP |
| `unit_cost_gbp` | float | No | No | Cost of goods (always less than unit_price_gbp) |
| `gross_margin_pct` | float | No | No | (price − cost) / price; range 0.36–0.80 |
| `is_loyalty_eligible` | boolean | No | No | Whether purchases of this product earn loyalty points |
| `product_status` | string | No | No | Active, Seasonal, Discontinued, or In-Test |
| `launch_date` | date | No | No | Date the product was added to the catalogue |

---

## fact_daily_sales

**Type:** FACT
**Primary Key:** `daily_sale_id`
**Rows:** 10,000
**Grain:** one row per store per day (with top product recorded)

### Description

Daily trading snapshot for each store, capturing revenue, transactions, loyalty activity, footfall, and product category revenue breakdown. All derived columns are consistent with their inputs: `avg_transaction_value_gbp` = `total_revenue_gbp` / `total_transactions`; the four category revenues sum exactly to `total_revenue_gbp`; `loyalty_transactions` is always <= `total_transactions`.

### Columns

| Column Name | Data Type | Nullable | Unique | Description |
|---|---|---|---|---|
| `daily_sale_id` | integer | No | Yes (PK) | Unique daily sales record identifier |
| `store_id` | integer | No | No (FK → dim_store) | Store dimension foreign key |
| `date_id` | integer | No | No (FK → dim_date) | Date dimension foreign key |
| `product_id` | integer | No | No (FK → dim_product) | Top-selling product that day (dimension foreign key) |
| `total_revenue_gbp` | float | No | No | Total daily revenue in GBP |
| `total_transactions` | integer | No | No | Count of customer transactions that day |
| `avg_transaction_value_gbp` | float | No | No | total_revenue_gbp / total_transactions (derived consistently) |
| `loyalty_transactions` | integer | No | No | Transactions made by loyalty app members (always <= total_transactions) |
| `loyalty_redemption_cost_gbp` | float | No | No | Cost to the business of loyalty rewards redeemed that day |
| `footfall` | integer | No | No | Total customer footfall (always >= total_transactions) |
| `espresso_revenue_gbp` | float | No | No | Revenue from espresso drinks |
| `filter_revenue_gbp` | float | No | No | Revenue from filter coffee |
| `food_revenue_gbp` | float | No | No | Revenue from food items |
| `retail_beans_revenue_gbp` | float | No | No | Revenue from retail beans (espresso + filter + food + retail_beans sums to total_revenue_gbp) |
| `daily_gross_profit_gbp` | float | No | No | Revenue minus cost of goods (before rent and staffing) |
| `shift_pattern` | string | No | No | Staffing pattern that day: Early-Only, Late-Only, Split-Shift, Full-Day, Skeleton |
| `staff_count` | integer | No | No | Number of staff on shift |
| `total_staff_hours` | float | No | No | Total labour hours worked that day |

---

## fact_store_monthly_profitability

**Type:** FACT
**Primary Key:** `monthly_profit_id`
**Rows:** 1,440
**Grain:** one row per store per calendar month (60 stores × 24 months)

### Description

Monthly P&L roll-up for each store. `net_profit_gbp` is always derived as total_monthly_revenue_gbp − total_monthly_cogs_gbp − monthly_rent_gbp − monthly_staffing_cost_gbp − loyalty_redemption_cost_gbp. Loyalty member and non-member spend always sum to `total_monthly_revenue_gbp`. `profitability_status` is derived from `net_profit_margin_pct`.

### Columns

| Column Name | Data Type | Nullable | Unique | Description |
|---|---|---|---|---|
| `monthly_profit_id` | integer | No | Yes (PK) | Unique monthly profitability record identifier |
| `store_id` | integer | No | No (FK → dim_store) | Store dimension foreign key |
| `date_id` | integer | No | No (FK → dim_date) | Date dimension foreign key (maps to first day of the month) |
| `month_id` | string | No | No | Year-month string (e.g. 2023-06) for direct month-level joining |
| `total_monthly_revenue_gbp` | float | No | No | Total monthly revenue before any cost deductions |
| `total_monthly_cogs_gbp` | float | No | No | Monthly cost of goods sold |
| `monthly_rent_gbp` | float | No | No | Monthly lease cost (consistent with dim_store.monthly_rent_gbp) |
| `monthly_staffing_cost_gbp` | float | No | No | Monthly staff wages (consistent with dim_store.monthly_staffing_cost_gbp) |
| `loyalty_redemption_cost_gbp` | float | No | No | Monthly loyalty reward redemption cost |
| `net_profit_gbp` | float | No | No | Revenue − COGS − rent − staffing − loyalty redemption (always derived correctly) |
| `net_profit_margin_pct` | float | No | No | net_profit_gbp / total_monthly_revenue_gbp (range −1.0 to 0.6) |
| `avg_dwell_time_minutes` | float | No | No | Average customer dwell time in minutes (range: 2–90) |
| `loyalty_member_spend_gbp` | float | No | No | Revenue from loyalty app members |
| `non_member_spend_gbp` | float | No | No | Revenue from non-members (loyalty_member_spend + non_member_spend = total_monthly_revenue) |
| `loyalty_member_revenue_pct` | float | Yes | No | Fraction of revenue from loyalty members (0–1); null where loyalty data incomplete |
| `avg_daily_footfall` | float | Yes | No | Average daily footfall for the month |
| `revenue_per_sqft_gbp` | float | No | No | Monthly revenue per square foot of store space |
| `peak_hour_transactions` | integer | No | No | Transactions during the peak trading hour |
| `dead_hour_transactions` | integer | No | No | Transactions during the quietest hour |
| `rent_band` | string | No | No | Derived rent classification: Low (<£5k), Medium (£5k–£9k), High (£9k–£16k), Premium (>£16k) |
| `profitability_status` | string | No | No | Derived from net_profit_margin_pct: Highly-Profitable (>20%), Profitable (8–20%), Break-Even (−2–8%), Loss-Making (−15–−2%), Structural-Loss (<−15%) |

---

## Relationships

### Foreign Key Constraints

| From Table | From Column | To Table | To Column | Type |
|---|---|---|---|---|
| fact_daily_sales | `store_id` | dim_store | `store_id` | Many To One |
| fact_daily_sales | `date_id` | dim_date | `date_id` | Many To One |
| fact_daily_sales | `product_id` | dim_product | `product_id` | Many To One |
| fact_store_monthly_profitability | `store_id` | dim_store | `store_id` | Many To One |
| fact_store_monthly_profitability | `date_id` | dim_date | `date_id` | Many To One |

---

## Data Quality & Characteristics

### Logical Consistency Guarantees
- `avg_transaction_value_gbp` = `total_revenue_gbp` / `total_transactions` in every fact_daily_sales row
- `espresso_revenue_gbp` + `filter_revenue_gbp` + `food_revenue_gbp` + `retail_beans_revenue_gbp` = `total_revenue_gbp` in every fact_daily_sales row
- `loyalty_transactions` <= `total_transactions` in every fact_daily_sales row
- `loyalty_member_spend_gbp` + `non_member_spend_gbp` = `total_monthly_revenue_gbp` in every fact_store_monthly_profitability row
- `net_profit_gbp` = revenue − COGS − rent − staffing − loyalty redemption in every fact_store_monthly_profitability row
- `profitability_status` is derived from `net_profit_margin_pct`

### Missing Values
`seating_capacity` is nullable for stores without seating (some Transport-Hub formats). `loyalty_member_revenue_pct` and `avg_daily_footfall` contain a small number of nulls in fact_store_monthly_profitability where data was not recorded.

### Temporal Coverage
All dates fall within 2023-01-01 to 2024-12-31. dim_date day-of-week, weekend, and bank holiday flags are accurate for England & Wales.

---

*Dictionary generated 2026-09-24*
