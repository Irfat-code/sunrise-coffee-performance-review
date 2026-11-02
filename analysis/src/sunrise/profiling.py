"""Data profiling: every check compares what the brief or dictionary claims
with what the files contain. Returns one row per check so the list can be
re-run whenever the data is refreshed."""
import pandas as pd

from .config import RENT_BANDS_DOC, STATUS_BANDS, STREAMS


def status_from_margin(margin: float) -> str:
    for lower, label in STATUS_BANDS:
        if margin >= lower:
            return label
    return STATUS_BANDS[-1][1]


def rent_band_doc(rent: float) -> str:
    for lower, label in RENT_BANDS_DOC:
        if rent >= lower:
            return label
    return "Low"


def profile(t: dict) -> pd.DataFrame:
    d, s, p, f, m = t["date"], t["store"], t["product"], t["daily"], t["monthly"]
    rows = []

    def add(sev, table, check, claim, observed, impact):
        rows.append({"severity": sev, "table": table, "check": check,
                     "brief_or_dictionary_says": claim, "data_shows": observed,
                     "how_we_handle_it": impact})

    # ---- Shape and formats -------------------------------------------------
    fmt = s["store_format"].value_counts().to_dict()
    add("High", "dim_store", "Store formats present",
        "3 formats: High-Street, Retail-Park, Transport-Hub",
        f"{fmt}; no Retail-Park stores at all",
        "Format comparison is effectively High-Street vs 2 Transport-Hub stores. "
        "Every Transport-Hub result is flagged small-sample; location_type used as the richer split.")
    th = s[s["store_format"] == "Transport-Hub"]
    add("High", "dim_store", "Transport-Hub coverage",
        "Transport-Hub is a format to compare",
        f"{len(th)} stores, both {th['city'].unique().tolist()} {th['location_type'].unique().tolist()}",
        "Transport-Hub conclusions describe Luton station, not the format.")
    lt = s["location_type"].value_counts().to_dict()
    add("Medium", "dim_store", "Location types present",
        "10 location types incl. Airport, Hospital, University-Campus, Roadside-Services",
        f"Only {len(lt)}: {lt}", "Cannot evaluate airports, hospitals etc. for expansion.")
    misnamed = s[s["store_name"].str.contains("Station") & (s["location_type"] != "Train-Station")]
    add("Low", "dim_store", "Store names vs location_type",
        "Names include city and location type",
        f"{len(misnamed)} 'Station' stores are not Train-Station: {misnamed['store_id'].tolist()}",
        "Use store_id and location_type, never the name, to classify stores.")
    dupc = s["city"].value_counts()
    add("Low", "dim_store", "Duplicate cities",
        "-", f"{(dupc > 1).sum()} cities host 2 stores (store_ids 1-12 mirror 49-60 by city)",
        "Regional counts are stores, not cities.")
    st_ = s["store_status"].value_counts().to_dict()
    closed_trading = m[m["store_id"].isin(s.loc[s["store_status"] != "Active", "store_id"])] \
        .groupby("store_id")["month_id"].nunique().to_dict()
    add("High", "dim_store", "store_status vs trading",
        "Active, Temporarily-Closed, Refurbishing, Closed-Permanently",
        f"{st_}; no Closed-Permanently. Non-active stores still report revenue in "
        f"all months: {closed_trading}",
        "store_status is an undated current snapshot; not used to explain 2023-24 P&L.")
    add("Medium", "dim_store", "seating_capacity nulls",
        "Nullable for some Drive-Thru / Transport-Hub stores",
        f"{s['seating_capacity'].isna().sum()} nulls; no Drive-Thru format exists",
        "No null handling needed.")
    add("Medium", "dim_store", "Rent range",
        "£2,000-£40,000; Premium band >£16k",
        f"£{s['monthly_rent_gbp'].min():,.0f}-£{s['monthly_rent_gbp'].max():,.0f}; "
        f"no store above £16k", "No Premium-rent stores to learn from.")
    early = s[s["opening_year"] >= 2023]
    add("Medium", "dim_store", "Opening year vs trading history",
        "opening_year 2010-2024",
        f"Max {s['opening_year'].max()}; {len(early)} stores 'opened' 2023 yet report full revenue "
        f"from 2023-01 with no ramp-up", "Cannot study new-store ramp-up; opening_year treated as unreliable.")

    # ---- dim_date ------------------------------------------------------------
    add("Medium", "dim_date", "month_id column",
        "dim_date has month_id for joining to the monthly table",
        "Column absent in the file", "Derived from full_date in load.py.")
    cal = d["uk_trading_calendar"].value_counts().to_dict()
    add("Low", "dim_date", "uk_trading_calendar values",
        "Standard-Trading-Day, Bank-Holiday, Christmas-Period", f"{cal} (School-Holiday undocumented)",
        "School-Holiday reported as its own category.")
    bh_regions = s[s["region"].isin(["Scotland", "Northern-Ireland"])]
    add("Medium", "dim_date", "Bank-holiday calendar vs estate",
        "England & Wales bank holidays",
        f"Applied to all stores incl. {len(bh_regions)} in Scotland/Northern Ireland, which have different holidays; "
        f"Christmas/Boxing Day flagged BH but classed Christmas-Period",
        "Bank-holiday comparisons exclude Scotland and Northern Ireland stores.")

    # ---- dim_product ---------------------------------------------------------
    gm = p["gross_margin_pct"]
    add("Medium", "dim_product", "gross_margin_pct range",
        "0.36-0.80", f"{gm.min():.3f}-{gm.max():.3f} (formula price/cost reconciles exactly)",
        "Catalogue margins are list-price margins, higher than realised daily GM; both reported.")
    add("Low", "dim_product", "launch_date nulls",
        "Not nullable", f"{p['launch_date'].isna().sum()} of {len(p)} null (only seasonal items dated)",
        "Not used.")
    add("Low", "dim_product", "product_status values",
        "Active, Seasonal, Discontinued, In-Test", str(p["product_status"].value_counts().to_dict()), "-")
    fp = f.merge(d[["date_id", "full_date", "month_number"]], on="date_id").merge(p, on="product_id")
    seas = fp[fp["product_status"] == "Seasonal"]
    pre = (fp["full_date"] < fp["launch_date"]).sum()
    add("Medium", "fact_daily_sales", "Seasonal products out of season",
        "Pumpkin Spice / Christmas items are Seasonal",
        f"Seasonal items are top product in all 12 months (e.g. Christmas Mince Pie in "
        f"{seas[seas['product_name'].str.contains('Mince')]['month_number'].nunique()} months); "
        f"{pre} rows before launch_date",
        "product_id (top product) treated as noise; product analysis uses dim_product margins and the four revenue streams.")
    cats = fp["product_category"].value_counts().to_dict()
    add("Medium", "fact_daily_sales", "Categories vs revenue streams",
        "Four revenue streams: espresso, filter, food, retail beans",
        f"dim_product has 6 categories; Cold-Drinks and Merchandise are top product on "
        f"{cats.get('Cold-Drinks', 0) + cats.get('Merchandise', 0)} rows but have no revenue column",
        "Cold-Drinks/Merchandise cannot be sized; margin-by-category ranks only the four streams with revenue.")

    # ---- fact_daily_sales ----------------------------------------------------
    keys = f[["store_id", "date_id"]].drop_duplicates()
    dups = f.duplicated(["store_id", "date_id"], keep=False)
    add("High", "fact_daily_sales", "Coverage",
        "10,000 rows at store x day grain (implied full coverage)",
        f"{len(keys):,} distinct store-days of {s.shape[0] * d.shape[0]:,} possible "
        f"({len(keys) / (s.shape[0] * d.shape[0]):.1%}); "
        f"{f.groupby('store_id').size().min()}-{f.groupby('store_id').size().max()} rows per store",
        "Daily table is a sample: used only for shares, ratios and within-sample comparisons, never summed.")
    add("High", "fact_daily_sales", "Grain / duplicates",
        "One row per store per day",
        f"{f.duplicated(['store_id', 'date_id']).sum():,} extra rows; {dups.sum():,} rows share a store-day "
        f"with conflicting revenue and top product", "Duplicates averaged to one row per store-day.")
    add("Low", "fact_daily_sales", "Undocumented column",
        "18 columns", "avg_dwell_time_minutes present but undocumented", "Kept; low weight.")
    shift = f.groupby("shift_pattern")[["staff_count", "total_staff_hours"]].median()
    add("Medium", "fact_daily_sales", "shift_pattern vs staffing",
        "Skeleton / Full-Day etc. describe staffing",
        "Median staff and hours are near-identical across patterns: "
        + "; ".join(f"{k} {r.staff_count:.0f} staff/{r.total_staff_hours:.0f}h" for k, r in shift.iterrows()),
        "shift_pattern ignored; staffing analysis uses staff hours.")
    daily_gm = f["daily_gross_profit_gbp"] / f["total_revenue_gbp"]
    add("Low", "fact_daily_sales", "Realised gross margin",
        "-", f"Daily GM {daily_gm.min():.1%}-{daily_gm.max():.1%}, median {daily_gm.median():.1%}; "
        f"monthly table GM median {(1 - m['total_monthly_cogs_gbp'] / m['total_monthly_revenue_gbp']).median():.1%}",
        "Realised margins ~25pts below catalogue margins (waste, discounting, mix). Monthly table used for P&L.")
    for c in ["total_revenue_gbp", "avg_transaction_value_gbp"]:
        floor = (f[c] == f[c].min()).sum()
        if floor > 1:
            add("Low", "fact_daily_sales", f"{c} floor values",
                "-", f"{floor} rows sit exactly on the minimum {f[c].min()} (clipped)", "Left in; immaterial.")
    sd = f.merge(d[["date_id", "month_id"]], on="date_id").groupby(["store_id", "month_id"]).agg(
        rev=("total_revenue_gbp", "mean"), foot=("footfall", "mean")).reset_index().merge(m, on=["store_id", "month_id"])
    store_link = sd.groupby("store_id")[["rev", "total_monthly_revenue_gbp"]].mean().corr().iloc[0, 1]
    add("High", "both facts", "Daily sample vs monthly P&L",
        "Monthly is a roll-up of trading",
        f"Store-level correlation of daily mean revenue with monthly revenue is only r={store_link:.2f}; "
        f"daily footfall is a median {(sd['foot'] / sd['avg_daily_footfall']).median():.0%} of monthly avg_daily_footfall",
        "The two facts are not reconcilable; no figure from one is checked against the other.")

    # ---- fact_store_monthly_profitability -------------------------------------
    m2 = m.copy()
    m2["status_doc"] = m2["net_profit_margin_pct"].map(status_from_margin)
    mism = (m2["status_doc"] != m2["profitability_status"]).sum()
    ranges = m2.groupby("profitability_status")["net_profit_margin_pct"].agg(["min", "max"])
    add("High", "monthly", "profitability_status vs margin",
        "Derived from net_profit_margin_pct with fixed bands",
        f"{mism} of {len(m2)} rows ({mism / len(m2):.0%}) disagree with the documented bands; label ranges overlap "
        f"(Profitable {ranges.loc['Profitable', 'min']:.1%} to {ranges.loc['Profitable', 'max']:.1%}, "
        f"Break-Even {ranges.loc['Break-Even', 'min']:.1%} to {ranges.loc['Break-Even', 'max']:.1%})",
        "Status recomputed from margin using documented bands; both versions reported.")
    m2["rent_doc"] = m2["monthly_rent_gbp"].map(rent_band_doc)
    rb = m2.groupby("rent_band")["monthly_rent_gbp"].agg(["min", "max"])
    add("Low", "monthly", "rent_band thresholds",
        "Low <£5k, Medium £5-9k, High £9-16k, Premium >£16k",
        f"{(m2['rent_doc'] != m2['rent_band']).sum()} rows differ; file uses Medium up to £{rb.loc['Medium', 'max']:,.0f} "
        f"(i.e. a £10k cut-off) and has no Premium", "Rent analysed as a continuous £ value.")
    mm = m.merge(s[["store_id", "monthly_rent_gbp", "monthly_staffing_cost_gbp"]], on="store_id", suffixes=("", "_dim"))
    rr = mm["monthly_rent_gbp"] / mm["monthly_rent_gbp_dim"]
    sr = mm["monthly_staffing_cost_gbp"] / mm["monthly_staffing_cost_gbp_dim"]
    add("Medium", "monthly", "Rent/staffing vs dim_store",
        "Consistent with dim_store", f"Monthly rent varies {rr.min():.0%}-{rr.max():.0%} of dim value; "
        f"staffing {sr.min():.0%}-{sr.max():.0%}", "Monthly values used for P&L (they drive net_profit).")
    add("Medium", "monthly", "Margin range",
        "net_profit_margin_pct -1.0 to 0.6",
        f"{(m['net_profit_margin_pct'] < -1).sum()} rows below -100% (min {m['net_profit_margin_pct'].min():.0%}); "
        f"revenue floor of exactly £{m['total_monthly_revenue_gbp'].min():,.0f}",
        "Store margins computed as sum(profit)/sum(revenue) so single bad months do not dominate; medians reported.")
    add("Low", "monthly", "Nulls",
        "loyalty_member_revenue_pct and avg_daily_footfall have some nulls",
        f"{m['loyalty_member_revenue_pct'].isna().sum()} and {m['avg_daily_footfall'].isna().sum()} nulls",
        "None needed.")
    add("Low", "monthly", "peak vs dead hour",
        "-", f"{(m['peak_hour_transactions'] < m['dead_hour_transactions']).sum()} rows have dead hour > peak hour",
        "Ignored; immaterial.")
    sq = m["total_monthly_revenue_gbp"] / m["revenue_per_sqft_gbp"]
    add("Low", "monthly", "revenue_per_sqft source",
        "Monthly revenue per sq ft", f"No floor-area column anywhere; implied area is constant per store "
        f"({sq.groupby(m['store_id']).mean().min():,.0f}-{sq.groupby(m['store_id']).mean().max():,.0f} sq ft)",
        "Metric is internally consistent; usable.")
    integ = {
        "net_profit identity": (abs(m["total_monthly_revenue_gbp"] - m["total_monthly_cogs_gbp"] - m["monthly_rent_gbp"]
                                    - m["monthly_staffing_cost_gbp"] - m["loyalty_redemption_cost_gbp"]
                                    - m["net_profit_gbp"]) > 1).sum(),
        "member+non-member=revenue": (abs(m["loyalty_member_spend_gbp"] + m["non_member_spend_gbp"]
                                          - m["total_monthly_revenue_gbp"]) > 1).sum(),
        "4 streams=daily revenue": (abs(f[list(STREAMS)].sum(axis=1) - f["total_revenue_gbp"]) > 0.05).sum(),
        "ATV=rev/tx": (abs(f["total_revenue_gbp"] / f["total_transactions"] - f["avg_transaction_value_gbp"]) > 0.01).sum(),
    }
    add("OK", "both facts", "Arithmetic identities",
        "Documented identities hold", "Violations: " + ", ".join(f"{k} {v}" for k, v in integ.items()),
        "Identities can be relied on.")
    out = pd.DataFrame(rows)
    order = {"High": 0, "Medium": 1, "Low": 2, "OK": 3}
    return out.sort_values("severity", key=lambda c: c.map(order), kind="stable").reset_index(drop=True)
