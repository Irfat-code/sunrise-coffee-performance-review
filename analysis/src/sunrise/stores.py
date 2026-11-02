"""Area 1: store, format and regional performance. P&L comes only from the
monthly table; store margins are sum(profit) / sum(revenue) over the period."""
import numpy as np
import pandas as pd

from .config import LOSS_STATUSES
from .profiling import status_from_margin
from .stats import corr, kruskal, summarise


def store_scorecard(m: pd.DataFrame) -> pd.DataFrame:
    m = m.assign(status_doc=m["net_profit_margin_pct"].map(status_from_margin))
    g = m.groupby("store_id")
    sc = pd.DataFrame({
        "revenue_24m": g["total_monthly_revenue_gbp"].sum(),
        "net_profit_24m": g["net_profit_gbp"].sum(),
        "median_month_margin": g["net_profit_margin_pct"].median(),
        "mean_month_margin": g["net_profit_margin_pct"].mean(),
        "rent_monthly": g["monthly_rent_gbp"].mean(),
        "rev_per_sqft": g["revenue_per_sqft_gbp"].mean(),
        "avg_daily_footfall": g["avg_daily_footfall"].mean(),
        "loss_months_doc": g["status_doc"].apply(lambda s: s.isin(LOSS_STATUSES).sum()),
        "loss_months_label": g["profitability_status"].apply(lambda s: s.isin(LOSS_STATUSES).sum()),
    })
    sc["margin_24m"] = sc["net_profit_24m"] / sc["revenue_24m"]
    sc["rent_pct_revenue"] = sc["rent_monthly"] * 24 / sc["revenue_24m"]
    for y in (2023, 2024):
        yy = m[m["year"] == y].groupby("store_id")
        sc[f"net_profit_{y}"] = yy["net_profit_gbp"].sum()
        sc[f"margin_{y}"] = sc[f"net_profit_{y}"] / yy["total_monthly_revenue_gbp"].sum()
    sc["np_change_gbp"] = sc["net_profit_2024"] - sc["net_profit_2023"]
    sc["margin_change_pts"] = sc["margin_2024"] - sc["margin_2023"]
    sc["status_24m"] = sc["margin_24m"].map(status_from_margin)
    attrs = m.drop_duplicates("store_id").set_index("store_id")[
        ["store_name", "store_format", "location_type", "region", "store_status", "loyalty_adoption_rate"]]
    return attrs.join(sc).reset_index()


def persistence(m: pd.DataFrame, sc: pd.DataFrame) -> dict:
    """How much of the store-to-store gap is stable rather than month-to-month noise."""
    store_mean = m.groupby("store_id")["net_profit_margin_pct"].transform("mean")
    between = store_mean.var()
    total = m["net_profit_margin_pct"].var()
    # Year-on-year stability of the store ranking is the key test for picking stores.
    yoy = corr(sc["margin_2023"], sc["margin_2024"])
    rev_yoy = corr(sc["net_profit_2023"], sc["net_profit_2024"])
    return {"share_of_margin_variance_between_stores": between / total,
            "margin_2023_vs_2024_spearman": yoy["spearman_rho"], "margin_yoy_p": yoy["spearman_p"],
            "np_2023_vs_2024_spearman": rev_yoy["spearman_rho"]}


def group_tables(sc: pd.DataFrame, m: pd.DataFrame) -> dict:
    out = {}
    for by in ["store_format", "location_type", "region"]:
        t = summarise(sc, by, "margin_24m", min_rows=0)
        t = t.rename(columns={"mean": "mean_store_margin", "median": "median_store_margin"})
        g = sc.groupby(by)
        t["pooled_margin"] = g["net_profit_24m"].sum() / g["revenue_24m"].sum()
        t["median_np_per_store_per_year"] = g["net_profit_24m"].median() / 2
        t["mean_np_per_store_per_year"] = g["net_profit_24m"].mean() / 2
        t["median_rev_per_sqft"] = g["rev_per_sqft"].median()
        t["median_footfall"] = g["avg_daily_footfall"].median()
        t["median_rent_pct_revenue"] = g["rent_pct_revenue"].median()
        lm = m.assign(loss_doc=m["net_profit_margin_pct"].map(status_from_margin).isin(LOSS_STATUSES),
                      loss_label=m["profitability_status"].isin(LOSS_STATUSES)).groupby(by)
        t["loss_month_share_doc"] = lm["loss_doc"].mean()
        t["loss_month_share_label"] = lm["loss_label"].mean()
        t["stores_24m_below_8pct"] = g["margin_24m"].apply(lambda s: (s < 0.08).sum())
        t["np_change_median_gbp"] = g["np_change_gbp"].median()
        out[by] = t.sort_values("median_store_margin", ascending=False)
        out[f"{by}_kruskal"] = kruskal(sc, by, "margin_24m")
    return out


def rent_effect(sc: pd.DataFrame) -> dict:
    hs = sc[sc["store_format"] == "High-Street"]
    return {
        "rent_vs_revenue_all": corr(sc["rent_monthly"], sc["revenue_24m"]),
        "rent_vs_margin_all": corr(sc["rent_monthly"], sc["margin_24m"]),
        "rent_vs_revenue_high_street": corr(hs["rent_monthly"], hs["revenue_24m"]),
        "rent_pct_rev_vs_margin": corr(sc["rent_pct_revenue"], sc["margin_24m"]),
        "rent_band_table": summarise(sc.assign(rent_q=pd.qcut(sc["rent_monthly"], 4,
                                                              labels=["Q1 low", "Q2", "Q3", "Q4 high"])),
                                     "rent_q", "margin_24m", min_rows=0),
    }


def review_candidates(sc: pd.DataFrame) -> pd.DataFrame:
    """Stores to review: below the documented Profitable floor (8%) over 24 months,
    or 6+ loss months, or a 2024 margin drop of 5+ points into sub-8% territory."""
    flag = ((sc["margin_24m"] < 0.08) | (sc["loss_months_doc"] >= 6)
            | ((sc["margin_change_pts"] <= -0.05) & (sc["margin_2024"] < 0.08)))
    cols = ["store_id", "store_name", "location_type", "region", "store_status", "margin_24m",
            "margin_2023", "margin_2024", "net_profit_24m", "loss_months_doc", "loss_months_label",
            "rent_pct_revenue"]
    return sc.loc[flag, cols].sort_values("margin_24m")


def run(m: pd.DataFrame) -> dict:
    sc = store_scorecard(m)
    r = {"scorecard": sc, "persistence": persistence(m, sc), "rent": rent_effect(sc),
         "review": review_candidates(sc)}
    r.update(group_tables(sc, m))
    r["improvers"] = sc.nlargest(5, "np_change_gbp")[["store_id", "store_name", "region", "net_profit_2023",
                                                       "net_profit_2024", "np_change_gbp"]]
    r["decliners"] = sc.nsmallest(5, "np_change_gbp")[["store_id", "store_name", "region", "net_profit_2023",
                                                        "net_profit_2024", "np_change_gbp"]]
    r["np_change_spread"] = {"median": sc["np_change_gbp"].median(), "mean": sc["np_change_gbp"].mean(),
                             "std": sc["np_change_gbp"].std()}
    # Noise benchmark: change you would see from random month-to-month variation alone.
    rng = np.random.default_rng(7)
    sims = []
    for _ in range(500):
        sh = m.copy()
        sh["year"] = sh.groupby("store_id")["year"].transform(lambda s: rng.permutation(s.values))
        y = sh.groupby(["store_id", "year"])["net_profit_gbp"].sum().unstack()
        sims.append((y[2024] - y[2023]).std())
    r["np_change_spread"]["std_if_pure_noise"] = float(np.mean(sims))
    return r
