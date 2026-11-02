"""Area 3: revenue mix and product category margins.

The daily table is a ~20% sample, so mix is expressed as shares (ratios within
the sample), never as summed totals."""
import pandas as pd

from .config import STREAMS
from .stats import ols, summarise


def add_shares(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    for col, cat in STREAMS.items():
        d[f"share_{cat}"] = d[col] / d["total_revenue_gbp"]
    d["t_years"] = (d["full_date"] - d["full_date"].min()).dt.days / 365.25
    d["half"] = d["year"].astype(str) + "-H" + ((d["month_number"] > 6) + 1).astype(str)
    return d


def share_table(d: pd.DataFrame, by=None) -> pd.DataFrame:
    """Mean and median of row-level shares plus the pooled (revenue-weighted) share."""
    rows = []
    groups = [("All", d)] if by is None else d.groupby(by)
    for key, g in groups:
        for col, cat in STREAMS.items():
            s = g[f"share_{cat}"]
            rows.append({"group": key, "category": cat, "n_store_days": len(g),
                         "n_stores": g["store_id"].nunique(), "mean_share": s.mean(),
                         "median_share": s.median(),
                         "pooled_share": g[col].sum() / g["total_revenue_gbp"].sum()})
    out = pd.DataFrame(rows)
    out["small_sample"] = (out["n_stores"] < 5) | (out["n_store_days"] < 30)
    return out


def share_trends(d: pd.DataFrame) -> pd.DataFrame:
    """Linear trend in each stream's share, in percentage points per year,
    with store fixed effects so changing sample composition cannot fake a trend."""
    rows = []
    for cat in STREAMS.values():
        y = d[f"share_{cat}"]
        yw = y - y.groupby(d["store_id"]).transform("mean")
        tw = d["t_years"] - d["t_years"].groupby(d["store_id"]).transform("mean")
        fit = ols(yw, pd.DataFrame({"t_years": tw}), intercept=False).loc["t_years"]
        first = y[d["year"] == 2023]
        last = y[d["year"] == 2024]
        rows.append({"category": cat, "pts_per_year": fit["coef"] * 100,
                     "ci_low": fit["ci_low"] * 100, "ci_high": fit["ci_high"] * 100, "p": fit["p"],
                     "median_2023": first.median(), "median_2024": last.median(),
                     "mean_2023": first.mean(), "mean_2024": last.mean()})
    return pd.DataFrame(rows)


def realised_stream_margins(d: pd.DataFrame) -> pd.DataFrame:
    """Gross profit regressed on the four stream revenues gives the realised
    gross margin per stream; compare with catalogue list-price margins."""
    fit = ols(d["daily_gross_profit_gbp"], d[list(STREAMS)], intercept=False)
    fit.index = [STREAMS[c] for c in fit.index]
    return fit


def run(d: pd.DataFrame, p: pd.DataFrame) -> dict:
    d = add_shares(d)
    cat = summarise(p.assign(store_id=0), "product_category", "gross_margin_pct", min_rows=0)
    cat = cat.drop(columns=["n_stores", "small_sample"]).rename(columns={"n_rows": "n_products"})
    cat["small_sample"] = cat["n_products"] < 5
    cat["has_revenue_stream"] = cat.index.isin(STREAMS.values())
    realised = realised_stream_margins(d)
    cat = cat.join(realised[["coef", "ci_low", "ci_high"]].rename(columns={
        "coef": "realised_margin", "ci_low": "realised_ci_low", "ci_high": "realised_ci_high"}))
    by_half = share_table(d, "half")
    return {
        "overall": share_table(d),
        "by_format": share_table(d, "store_format"),
        "by_location": share_table(d, "location_type"),
        "by_half": by_half,
        "trends": share_trends(d),
        "category_margins": cat.sort_values("median", ascending=False),
        # Gross profit per £100 of revenue moved into each stream.
        "gm_vs_food_share": d[["share_Food", "gross_margin"]].corr().iloc[0, 1],
        "gm_vs_filter_share": d[["share_Filter-Coffee", "gross_margin"]].corr().iloc[0, 1],
    }
