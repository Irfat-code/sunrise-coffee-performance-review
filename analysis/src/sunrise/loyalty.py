"""Area 2: loyalty programme effectiveness.

The brief's "net value" (member revenue minus redemption cost) treats every
member pound as incremental. We report it, then test for incrementality three
ways: member spend index, member vs non-member ATV, and cross-store revenue vs
adoption. Programme cost and revenue come from the monthly table only."""
import pandas as pd

from .stats import corr, kruskal, ols, summarise


def economics(m: pd.DataFrame) -> pd.DataFrame:
    y = m.groupby("year").agg(revenue=("total_monthly_revenue_gbp", "sum"),
                              cogs=("total_monthly_cogs_gbp", "sum"),
                              member_revenue=("loyalty_member_spend_gbp", "sum"),
                              redemption_cost=("loyalty_redemption_cost_gbp", "sum"),
                              net_profit=("net_profit_gbp", "sum"))
    y["gross_margin"] = 1 - y["cogs"] / y["revenue"]
    y["member_revenue_share"] = y["member_revenue"] / y["revenue"]
    y["redemption_pct_member_revenue"] = y["redemption_cost"] / y["member_revenue"]
    y["redemption_pct_net_profit"] = y["redemption_cost"] / y["net_profit"]
    # Incremental revenue needed for redemption cost to pay for itself.
    y["breakeven_incremental_revenue"] = y["redemption_cost"] / y["gross_margin"]
    y["breakeven_uplift_on_member_spend"] = y["breakeven_incremental_revenue"] / (
        y["member_revenue"] - y["breakeven_incremental_revenue"])
    y["naive_net_value_brief"] = y["member_revenue"] - y["redemption_cost"]
    return y


def store_level(m: pd.DataFrame, sc: pd.DataFrame) -> pd.DataFrame:
    g = m.groupby("store_id")
    st = pd.DataFrame({
        "member_rev_pct": g["loyalty_member_spend_gbp"].sum() / g["total_monthly_revenue_gbp"].sum(),
        "member_revenue_per_year": g["loyalty_member_spend_gbp"].sum() / 2,
        "redemption_per_year": g["loyalty_redemption_cost_gbp"].sum() / 2,
        "avg_monthly_revenue": g["total_monthly_revenue_gbp"].mean(),
        "avg_monthly_np": g["net_profit_gbp"].mean(),
        "gross_margin": 1 - g["total_monthly_cogs_gbp"].sum() / g["total_monthly_revenue_gbp"].sum(),
    }).join(sc.set_index("store_id")[["store_format", "location_type", "region", "loyalty_adoption_rate",
                                      "margin_24m"]])
    # Members' share of revenue divided by their share of customers. 1.0 means a
    # member spends the same as a non-member; >1 means members spend more.
    st["member_spend_index"] = st["member_rev_pct"] / st["loyalty_adoption_rate"]
    st["naive_net_value_per_year"] = st["member_revenue_per_year"] - st["redemption_per_year"]
    st["redemption_pct_member_revenue"] = st["redemption_per_year"] / st["member_revenue_per_year"]
    # Margin-adjusted value if index-implied incremental spend is real.
    idx = st["member_spend_index"]
    st["implied_incremental_revenue"] = st["member_revenue_per_year"] * (1 - 1 / idx)
    st["implied_net_value_per_year"] = (st["implied_incremental_revenue"] * st["gross_margin"]
                                        - st["redemption_per_year"])
    return st.reset_index()


def member_atv(d: pd.DataFrame) -> dict:
    """Estimate revenue per member and per non-member transaction from the daily
    sample: revenue = a * non-member tx + b * member tx, within store."""
    x = d.assign(non_member_tx=d["total_transactions"] - d["loyalty_transactions"])
    cols = ["total_revenue_gbp", "non_member_tx", "loyalty_transactions"]
    pooled = ols(x["total_revenue_gbp"], x[["non_member_tx", "loyalty_transactions"]], intercept=False)
    w = x[cols] - x.groupby("store_id")[cols].transform("mean")
    within = ols(w["total_revenue_gbp"], w[["non_member_tx", "loyalty_transactions"]], intercept=False)
    return {"pooled": pooled, "within_store": within,
            "atv_vs_loyalty_tx_share": corr(d["loyalty_tx_share"], d["avg_transaction_value_gbp"])}


def run(m: pd.DataFrame, sc: pd.DataFrame, d: pd.DataFrame) -> dict:
    st = store_level(m, sc)
    r = {"economics": economics(m), "stores": st, "atv": member_atv(d)}
    r["adoption_vs_member_rev_pct"] = corr(st["loyalty_adoption_rate"], st["member_rev_pct"])
    r["adoption_vs_monthly_revenue"] = corr(st["loyalty_adoption_rate"], st["avg_monthly_revenue"])
    r["adoption_vs_margin"] = corr(st["loyalty_adoption_rate"], st["margin_24m"])
    r["revenue_on_adoption_ols"] = ols(st["avg_monthly_revenue"], st[["loyalty_adoption_rate"]])
    r["np_on_adoption_ols"] = ols(st["avg_monthly_np"], st[["loyalty_adoption_rate"]])
    r["spend_index_summary"] = st["member_spend_index"].describe()
    for by in ["store_format", "location_type", "region"]:
        t = summarise(st, by, "loyalty_adoption_rate", min_rows=0).rename(
            columns={"mean": "mean_adoption", "median": "median_adoption"})
        g = st.groupby(by)
        t["median_spend_index"] = g["member_spend_index"].median()
        t["median_redemption_pct_member_rev"] = g["redemption_pct_member_revenue"].median()
        t["median_naive_net_value_per_store"] = g["naive_net_value_per_year"].median()
        t["median_implied_net_value_per_store"] = g["implied_net_value_per_year"].median()
        r[by] = t.sort_values("median_adoption", ascending=False)
        r[f"{by}_kruskal_adoption"] = kruskal(st, by, "loyalty_adoption_rate")
        r[f"{by}_kruskal_index"] = kruskal(st, by, "member_spend_index")
    return r
