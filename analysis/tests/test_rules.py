"""Guards for the analysis rules: P&L from the monthly table, daily sample never
summed into totals, medians reported, small samples flagged."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sunrise import loyalty, profiling, stores  # noqa: E402
from sunrise.load import daily_store_days, load_all, monthly_enriched  # noqa: E402


@pytest.fixture(scope="module")
def t():
    return load_all()


def test_monthly_grain_complete(t):
    m = t["monthly"]
    assert len(m) == 60 * 24
    assert not m.duplicated(["store_id", "month_id"]).any()


def test_daily_is_sample_and_deduplicated(t):
    d = daily_store_days(t)
    assert not d.duplicated(["store_id", "date_id"]).any()
    assert len(d) < 0.5 * 60 * 730  # a sample, never a basis for totals


def test_pnl_identity_holds(t):
    m = t["monthly"]
    calc = (m.total_monthly_revenue_gbp - m.total_monthly_cogs_gbp - m.monthly_rent_gbp
            - m.monthly_staffing_cost_gbp - m.loyalty_redemption_cost_gbp)
    assert (calc - m.net_profit_gbp).abs().max() < 1


def test_store_totals_match_monthly(t):
    sc = stores.store_scorecard(monthly_enriched(t))
    assert sc["net_profit_24m"].sum() == pytest.approx(t["monthly"]["net_profit_gbp"].sum())


def test_group_tables_report_median_and_flag_small_samples(t):
    r = stores.run(monthly_enriched(t))
    fmt = r["store_format"]
    assert {"median_store_margin", "mean_store_margin", "small_sample"} <= set(fmt.columns)
    assert bool(fmt.loc["Transport-Hub", "small_sample"])


def test_status_recompute_bands():
    assert profiling.status_from_margin(0.25) == "Highly-Profitable"
    assert profiling.status_from_margin(0.08) == "Profitable"
    assert profiling.status_from_margin(0.0) == "Break-Even"
    assert profiling.status_from_margin(-0.05) == "Loss-Making"
    assert profiling.status_from_margin(-0.5) == "Structural-Loss"


def test_loyalty_economics_from_monthly(t):
    e = loyalty.economics(monthly_enriched(t))
    m = t["monthly"]
    assert e["redemption_cost"].sum() == pytest.approx(m["loyalty_redemption_cost_gbp"].sum())
    assert isinstance(e, pd.DataFrame)
