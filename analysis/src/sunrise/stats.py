"""Small statistical helpers. Every summary reports mean, median and n, and
flags groups that fall under the small-sample rules."""
import numpy as np
import pandas as pd
from scipy import stats as st

from .config import MIN_ROWS, MIN_STORES


def summarise(df: pd.DataFrame, by, col: str, store_col: str = "store_id",
              min_rows: int = MIN_ROWS) -> pd.DataFrame:
    """Group summary. For store-level frames pass min_rows=0 so only the store count is tested."""
    g = df.groupby(by)
    out = pd.DataFrame({
        "n_rows": g[col].size(),
        "n_stores": g[store_col].nunique() if store_col in df else np.nan,
        "mean": g[col].mean(),
        "median": g[col].median(),
        "std": g[col].std(),
    })
    out["small_sample"] = (out["n_stores"] < MIN_STORES) | (out["n_rows"] < min_rows)
    return out


def corr(x, y) -> dict:
    x, y = pd.Series(x), pd.Series(y)
    ok = x.notna() & y.notna()
    pr = st.pearsonr(x[ok], y[ok])
    sr = st.spearmanr(x[ok], y[ok])
    return {"n": int(ok.sum()), "pearson_r": pr.statistic, "pearson_p": pr.pvalue,
            "spearman_rho": sr.statistic, "spearman_p": sr.pvalue}


def ols(y, X, intercept: bool = True) -> pd.DataFrame:
    """Plain OLS with classical standard errors and 95% CIs."""
    X = pd.DataFrame(X).astype(float)
    if intercept:
        X.insert(0, "intercept", 1.0)
    y = np.asarray(y, dtype=float)
    beta, *_ = np.linalg.lstsq(X.values, y, rcond=None)
    resid = y - X.values @ beta
    dof = len(y) - X.shape[1]
    sigma2 = resid @ resid / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X.values.T @ X.values)))
    tcrit = st.t.ppf(0.975, dof)
    p = 2 * st.t.sf(np.abs(beta / se), dof)
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return pd.DataFrame({"coef": beta, "se": se, "ci_low": beta - tcrit * se,
                         "ci_high": beta + tcrit * se, "p": p, "n": len(y), "r2": r2},
                        index=X.columns)


def kruskal(df: pd.DataFrame, by: str, col: str) -> dict:
    groups = [g[col].dropna().values for _, g in df.groupby(by) if g[col].notna().sum() > 0]
    if len(groups) < 2:
        return {"H": np.nan, "p": np.nan, "k": len(groups)}
    r = st.kruskal(*groups)
    return {"H": r.statistic, "p": r.pvalue, "k": len(groups)}
