"""Run the full Sunrise Coffee review.

    python run_analysis.py                 # uses ../data
    python run_analysis.py --data-dir PATH --out-dir PATH
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from sunrise import loyalty, mix, profiling, report, seasonality, stores  # noqa: E402
from sunrise.config import DATA_DIR, OUTPUT_DIR  # noqa: E402
from sunrise.load import daily_store_days, load_all, monthly_enriched  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    ap.add_argument("--out-dir", type=Path, default=OUTPUT_DIR)
    args = ap.parse_args()

    t = load_all(args.data_dir)
    m = monthly_enriched(t)
    d = daily_store_days(t)

    P = profiling.profile(t)
    S = stores.run(m)
    L = loyalty.run(m, S["scorecard"], d)
    X = mix.run(d, t["product"])
    Z = seasonality.run(d, m)
    Z["_daily"] = d
    R = report.impact_ranking(S, L, Z, m)

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    report.save_tables({"data_quality": P, "stores": S, "loyalty": L, "mix": X,
                        "seasonality": {k: v for k, v in Z.items() if k != "_daily"},
                        "impact_ranking": R}, out)
    (out / "data_quality.md").write_text(report.data_quality_md(P), encoding="utf-8")
    (out / "findings.md").write_text(report.findings_md(t, P, S, L, Z, X, R, m), encoding="utf-8")
    print(f"Wrote {out / 'findings.md'}, {out / 'data_quality.md'} and tables in {out / 'tables'}")


if __name__ == "__main__":
    main()
