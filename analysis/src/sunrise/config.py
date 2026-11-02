"""Paths, documented thresholds and analysis rules in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT.parent / "data"  # repo-level data/ folder
OUTPUT_DIR = ROOT / "outputs"

# Small-sample rules: any group below these is flagged in every output table.
MIN_STORES = 5
MIN_ROWS = 30

# Documented thresholds from DATA_DICTIONARY.md. The data does not follow them
# exactly (see profiling), so statuses are recomputed from margin.
STATUS_BANDS = [  # (lower bound inclusive, label), checked top-down
    (0.20, "Highly-Profitable"),
    (0.08, "Profitable"),
    (-0.02, "Break-Even"),
    (-0.15, "Loss-Making"),
    (float("-inf"), "Structural-Loss"),
]
LOSS_STATUSES = {"Loss-Making", "Structural-Loss"}
RENT_BANDS_DOC = [(16000, "Premium"), (9000, "High"), (5000, "Medium"), (0, "Low")]

STREAMS = {
    "espresso_revenue_gbp": "Espresso-Drinks",
    "filter_revenue_gbp": "Filter-Coffee",
    "food_revenue_gbp": "Food",
    "retail_beans_revenue_gbp": "Retail-Beans",
}
