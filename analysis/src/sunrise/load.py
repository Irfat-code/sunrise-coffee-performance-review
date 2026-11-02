"""Load the five CSVs with explicit dtypes and the joins every module needs."""
from pathlib import Path

import pandas as pd

from .config import DATA_DIR, STREAMS


def load_all(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    data_dir = Path(data_dir)
    t = {
        "date": pd.read_csv(data_dir / "dim_date.csv", parse_dates=["full_date"]),
        "store": pd.read_csv(data_dir / "dim_store.csv"),
        "product": pd.read_csv(data_dir / "dim_product.csv", parse_dates=["launch_date"]),
        "daily": pd.read_csv(data_dir / "fact_daily_sales.csv"),
        "monthly": pd.read_csv(data_dir / "fact_store_monthly_profitability.csv"),
    }
    # dim_date has no month_id despite the dictionary; derive it for joins.
    t["date"]["month_id"] = t["date"]["full_date"].dt.strftime("%Y-%m")
    return t


def monthly_enriched(t: dict) -> pd.DataFrame:
    """Monthly P&L joined to store attributes. This is the only P&L source."""
    m = t["monthly"].merge(
        t["store"][["store_id", "store_name", "store_format", "location_type",
                    "region", "store_status", "loyalty_adoption_rate", "opening_year"]],
        on="store_id", how="left", validate="many_to_one")
    m["year"] = m["month_id"].str[:4].astype(int)
    m["month_number"] = m["month_id"].str[5:].astype(int)
    m["quarter"] = (m["month_number"] - 1) // 3 + 1
    return m


def daily_store_days(t: dict) -> pd.DataFrame:
    """Daily sample collapsed to one row per store-day.

    The table claims store x day grain but ~1,090 store-days appear twice with
    conflicting values (different top product and totals). We average the
    duplicates so no store-day is double-weighted. Rows are a ~20% sample of
    store-days: use them for ratios, shares and within-sample comparisons only,
    never for totals.
    """
    num = ["total_revenue_gbp", "total_transactions", "loyalty_transactions",
           "loyalty_redemption_cost_gbp", "footfall", "daily_gross_profit_gbp",
           "staff_count", "total_staff_hours", "avg_dwell_time_minutes",
           *STREAMS]
    d = (t["daily"].groupby(["store_id", "date_id"], as_index=False)[num].mean()
         .merge(t["date"], on="date_id", how="left", validate="many_to_one")
         .merge(t["store"][["store_id", "store_format", "location_type", "region",
                            "loyalty_adoption_rate"]],
                on="store_id", how="left", validate="many_to_one"))
    d["avg_transaction_value_gbp"] = d["total_revenue_gbp"] / d["total_transactions"]
    d["loyalty_tx_share"] = d["loyalty_transactions"] / d["total_transactions"]
    d["gross_margin"] = d["daily_gross_profit_gbp"] / d["total_revenue_gbp"]
    return d
