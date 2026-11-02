# Python analysis behind the report

Analysis for the CCO's three decisions:

1. Which stores or regions to review or close, and which to prioritise for 2025 expansion.
2. Whether the loyalty programme earns its redemption cost.
3. Which products to grow, and how to staff for seasonality.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py            # reads ../data, writes outputs/
python -m pytest -q               # checks the analysis rules below
```

Outputs:

- `outputs/findings.md`: every number behind the write-up, plus the impact ranking.
- `outputs/data_quality.md`: each quirk or mismatch between the data and the brief or dictionary, with how it is handled.
- `outputs/tables/*.csv`: every table, ready for Power BI (gitignored, regenerate with the script).

## Analysis rules

- P&L (revenue, profit, margin, loyalty cost) comes only from `fact_store_monthly_profitability`.
- `fact_daily_sales` is a ~20% sample of store-days with duplicate store-days. It is collapsed to one row per store-day and used only for shares, ratios and within-store comparisons. It is never summed into totals.
- Every group summary reports mean and median and is flagged `small_sample` when it has fewer than 5 stores or 30 rows.
- `profitability_status` disagrees with its documented bands in 42% of rows, so status is recomputed from margin and both versions are shown.
- Store margin over a period is sum(net profit) / sum(revenue), so single bad months do not dominate.

## Layout

```
run_analysis.py          entry point
src/sunrise/config.py    paths, thresholds, small-sample rules
src/sunrise/load.py      loading, joins, daily de-duplication
src/sunrise/profiling.py data quality and brief-vs-data checks
src/sunrise/stores.py    area 1: store, format, region, rent, review list
src/sunrise/loyalty.py   area 2: loyalty economics and incrementality tests
src/sunrise/mix.py       area 3: revenue mix shares, trends, category margins
src/sunrise/seasonality.py area 4: day-of-week, bank holidays, months, staffing
src/sunrise/report.py    tables, findings.md, impact ranking
tests/test_rules.py      guards for the rules above
../data/                the five challenge CSVs (repo root)
```
