"""Area 4: day-of-week, bank-holiday and seasonal patterns.

Profit by month comes from the monthly table (complete). Day-level effects come
from the daily sample and are measured within store (each store-day compared
with that store's own average), so the sample's uneven store mix cannot bias them."""
import numpy as np
import pandas as pd

from .stats import corr, ols, summarise

EXCLUDE_BH_REGIONS = ["Scotland", "Northern-Ireland"]  # England & Wales calendar only


def within_store_index(d: pd.DataFrame, col: str = "total_revenue_gbp") -> pd.Series:
    return d[col] / d.groupby("store_id")[col].transform("mean")


def day_effects(d: pd.DataFrame) -> dict:
    d = d.assign(rev_index=within_store_index(d),
                 rev_per_staff_hour=d["total_revenue_gbp"] / d["total_staff_hours"],
                 day_type=np.where(d["is_weekend"], "Weekend", "Weekday"))
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = summarise(d, "day_of_week", "rev_index").reindex(order)
    dow["median_revenue_gbp"] = d.groupby("day_of_week")["total_revenue_gbp"].median().reindex(order)
    dow["median_staff_hours"] = d.groupby("day_of_week")["total_staff_hours"].median().reindex(order)
    wk = summarise(d, ["store_format", "day_type"], "rev_index")
    wk["median_revenue_gbp"] = d.groupby(["store_format", "day_type"])["total_revenue_gbp"].median()
    bh = d[~d["region"].isin(EXCLUDE_BH_REGIONS)]
    bh = bh.assign(day_class=np.where(bh["is_uk_bank_holiday"], "Bank holiday", "Other day"))
    bht = summarise(bh, ["store_format", "day_class"], "rev_index")
    bht["median_revenue_gbp"] = bh.groupby(["store_format", "day_class"])["total_revenue_gbp"].median()
    cal = summarise(d, "uk_trading_calendar", "rev_index")
    # Does labour follow demand? Within-store correlation of hours with revenue.
    w = d[["total_revenue_gbp", "total_staff_hours"]] - d.groupby("store_id")[
        ["total_revenue_gbp", "total_staff_hours"]].transform("mean")
    return {"dow": dow, "weekend_by_format": wk, "bank_holiday_by_format": bht, "calendar": cal,
            "staff_hours_vs_revenue_within_store": corr(w["total_staff_hours"], w["total_revenue_gbp"]),
            "staff_hours_by_dow_index": within_store_index(d, "total_staff_hours")
            .groupby(d["day_of_week"]).median().reindex(order)}


def monthly_patterns(m: pd.DataFrame) -> dict:
    est = m.groupby(["year", "month_number"]).agg(
        revenue=("total_monthly_revenue_gbp", "sum"), net_profit=("net_profit_gbp", "sum"),
        staffing=("monthly_staffing_cost_gbp", "sum"),
        median_store_np=("net_profit_gbp", "median"), mean_store_np=("net_profit_gbp", "mean"),
        stores=("store_id", "nunique")).reset_index()
    piv = est.pivot(index="month_number", columns="year", values="net_profit")
    q = m.groupby(["year", "quarter"]).agg(revenue=("total_monthly_revenue_gbp", "sum"),
                                           net_profit=("net_profit_gbp", "sum"),
                                           median_store_np=("net_profit_gbp", "median")).reset_index()
    # Seasonal index by format: each store-month vs that store's own mean revenue.
    mi = m.assign(rev_index=m["total_monthly_revenue_gbp"]
                  / m.groupby("store_id")["total_monthly_revenue_gbp"].transform("mean"))
    fmt = mi.groupby(["store_format", "quarter"])["rev_index"].agg(["mean", "median", "count"])
    fmt["n_stores"] = mi.groupby(["store_format", "quarter"])["store_id"].nunique()
    fmt["small_sample"] = fmt["n_stores"] < 5
    # Estate-month swing vs store-month noise.
    month_effect = summarise(mi, "month_number", "rev_index")
    w = m[["total_monthly_revenue_gbp", "monthly_staffing_cost_gbp"]] - m.groupby("store_id")[
        ["total_monthly_revenue_gbp", "monthly_staffing_cost_gbp"]].transform("mean")
    return {"estate_by_month": est, "np_pivot": piv,
            "yoy_month_pattern": corr(piv[2023], piv[2024]),
            "quarters": q, "format_quarter_index": fmt, "month_index": month_effect,
            "estate_month_range_pct": (est["revenue"].max() - est["revenue"].min()) / est["revenue"].mean(),
            "staffing_vs_revenue_within_store": corr(w["monthly_staffing_cost_gbp"], w["total_monthly_revenue_gbp"])}


def run(d: pd.DataFrame, m: pd.DataFrame) -> dict:
    r = day_effects(d)
    r.update(monthly_patterns(m))
    return r
