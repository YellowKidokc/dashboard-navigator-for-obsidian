import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from scipy.optimize import curve_fit
    from scipy import stats
except ImportError:  # Fallbacks are implemented below
    curve_fit = None
    stats = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = Path(__file__).resolve().parent / "COMPUTATION_OUTPUT.json"
REGISTRY_PATH = Path(__file__).resolve().parent / "DOMAIN_REGISTRY.csv"

YEAR_MIN = 1800
YEAR_MAX = 2100


def _coerce_number(value):
    if value is None:
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return np.nan
    text = text.replace(",", "")
    text = text.replace("%", "")
    text = text.replace("~", "")
    text = text.replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return np.nan


def _find_year_columns(df):
    year_cols = []
    for col in df.columns:
        if re.match(r"^(18|19|20)\d{2}$", str(col)):
            year_cols.append(col)
    return year_cols


def _find_year_series(df):
    best_col = None
    best_count = 0
    for col in df.columns:
        values = pd.to_numeric(df[col], errors="coerce")
        count = values.between(YEAR_MIN, YEAR_MAX).sum()
        if count > best_count:
            best_count = count
            best_col = col
    if best_col is None or best_count < 2:
        return None
    return best_col


def _extract_series_from_df(df, metric=None, category=None, value_column=None):
    if df is None or df.empty:
        return None

    if metric and "METRIC" in df.columns:
        df = df[df["METRIC"].astype(str).str.strip() == str(metric).strip()]
    if category and "CATEGORY" in df.columns:
        df = df[df["CATEGORY"].astype(str).str.strip() == str(category).strip()]
    if df.empty:
        return None

    if value_column and value_column in df.columns:
        year_col = None
        if "year" in df.columns:
            year_col = "year"
        else:
            year_col = _find_year_series(df)
        if year_col is None:
            return None
        work = df[[year_col, value_column]].copy()
        work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
        work[value_column] = work[value_column].map(_coerce_number)
        work = work.dropna(subset=[year_col, value_column])
        work = work[(work[year_col] >= YEAR_MIN) & (work[year_col] <= YEAR_MAX)]
        if work.empty:
            return None
        grouped = work.groupby(year_col)[value_column].mean().dropna()
        if grouped.empty:
            return None
        years = grouped.index.to_numpy(dtype=float)
        vals = grouped.values.astype(float)
        return years, vals

    year_cols = _find_year_columns(df)
    if year_cols:
        values = {}
        for col in year_cols:
            series = df[col].map(_coerce_number)
            series = series.dropna()
            if not series.empty:
                values[int(col)] = float(series.mean())
        if values:
            years = np.array(sorted(values.keys()), dtype=float)
            vals = np.array([values[int(y)] for y in years], dtype=float)
            return years, vals

    year_col = _find_year_series(df)
    if year_col is None:
        return None

    value_cols = [c for c in df.columns if c != year_col]
    numeric_cols = []
    for c in value_cols:
        series = df[c].map(_coerce_number)
        if series.notna().sum() >= 2:
            numeric_cols.append(c)

    if not numeric_cols:
        return None

    work = df[[year_col] + numeric_cols].copy()
    work[year_col] = pd.to_numeric(work[year_col], errors="coerce")
    work = work.dropna(subset=[year_col])
    if work.empty:
        return None

    for c in numeric_cols:
        work[c] = work[c].map(_coerce_number)

    work = work[(work[year_col] >= YEAR_MIN) & (work[year_col] <= YEAR_MAX)]
    if work.empty:
        return None

    work["_value"] = work[numeric_cols].mean(axis=1, skipna=True)
    grouped = work.groupby(year_col)["_value"].mean().dropna()
    if grouped.empty:
        return None

    years = grouped.index.to_numpy(dtype=float)
    vals = grouped.values.astype(float)
    return years, vals


def load_file_series(path, metric=None, category=None, value_column=None):
    suffix = path.suffix.lower()
    if suffix == ".csv":
        try:
            df = pd.read_csv(path)
        except Exception:
            df = pd.read_csv(path, encoding_errors="ignore")
        return _extract_series_from_df(df, metric=metric, category=category, value_column=value_column)
    if suffix in (".xlsx", ".xls"):
        sheets = pd.read_excel(path, sheet_name=None)
        series_list = []
        for _, sdf in sheets.items():
            extracted = _extract_series_from_df(sdf, metric=metric, category=category, value_column=value_column)
            if extracted:
                series_list.append(extracted)
        if not series_list:
            return None
        all_years = sorted({int(y) for years, _ in series_list for y in years})
        agg = {}
        for y in all_years:
            vals = []
            for years, values in series_list:
                for idx, year in enumerate(years):
                    if int(year) == int(y):
                        vals.append(values[idx])
                        break
            if vals:
                agg[y] = float(np.mean(vals))
        if not agg:
            return None
        years = np.array(sorted(agg.keys()), dtype=float)
        vals = np.array([agg[int(y)] for y in years], dtype=float)
        return years, vals
    return None


def normalize_series(values):
    vmin = np.nanmin(values)
    vmax = np.nanmax(values)
    if math.isclose(vmin, vmax):
        return None
    return (values - vmin) / (vmax - vmin)


def decay_model(t, y0, lam, t0):
    return y0 * np.exp(-lam * (t - t0))


def _fit_decay_fallback(years, values):
    years = np.array(years, dtype=float)
    values = np.array(values, dtype=float)
    values = np.where(values <= 0, 1e-6, values)

    best = None
    t_min = int(np.nanmin(years))
    t_max = int(np.nanmax(years))
    for t0 in range(t_min, t_max + 1):
        x = years - t0
        y = np.log(values)
        if np.all(np.isfinite(y)) and len(y) >= 2:
            slope, intercept = np.polyfit(x, y, 1)
            lam = max(0.0, -slope)
            y0 = max(1e-6, math.exp(intercept))
            y_pred = decay_model(years, y0, lam, t0)
            ss_res = np.sum((values - y_pred) ** 2)
            ss_tot = np.sum((values - np.mean(values)) ** 2)
            r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0
            if best is None or r2 > best[1]:
                best = ((y0, lam, float(t0)), float(r2))
    if best is None:
        raise ValueError("fit_failed")
    return best


def fit_decay(years, values):
    if curve_fit is None:
        return _fit_decay_fallback(years, values)

    y0_guess = max(0.01, float(np.nanmax(values)))
    lam_guess = 0.01
    t0_guess = float(np.nanmin(years))
    bounds = ([0.0, 0.0, float(np.nanmin(years))], [2.0, 5.0, float(np.nanmax(years))])

    popt, _ = curve_fit(decay_model, years, values, p0=[y0_guess, lam_guess, t0_guess], bounds=bounds, maxfev=10000)
    y_pred = decay_model(years, *popt)
    ss_res = np.sum((values - y_pred) ** 2)
    ss_tot = np.sum((values - np.mean(values)) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot != 0 else 0.0
    return (popt, r2)


def _normal_cdf(x, mu, sigma):
    if sigma == 0:
        return 1.0 if x >= mu else 0.0
    z = (x - mu) / (sigma * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def _ks_test_normal(sample, mu, sigma):
    n = len(sample)
    if n == 0:
        return None
    data = np.sort(sample)
    cdf_vals = np.array([_normal_cdf(x, mu, sigma) for x in data])
    ecdf = np.arange(1, n + 1) / n
    d_stat = np.max(np.abs(ecdf - cdf_vals))
    # Kolmogorov distribution approximation
    pvalue = 0.0
    for k in range(1, 100):
        term = (-1) ** (k - 1) * math.exp(-2 * (k ** 2) * (d_stat ** 2) * n)
        pvalue += term
    pvalue = max(0.0, min(1.0, 2.0 * pvalue))
    return float(pvalue)


def main():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Missing registry: {REGISTRY_PATH}")

    registry = pd.read_csv(REGISTRY_PATH)
    results = []
    missing = []
    excluded = []

    for _, row in registry.iterrows():
        domain_id = str(row.get("domain_id", "")).strip()
        domain_name = str(row.get("domain_name", "")).strip()
        source = str(row.get("source", "")).strip()
        path = str(row.get("path", "")).strip()
        include = str(row.get("include", "yes")).strip().lower()
        metric = str(row.get("metric", "")).strip()
        category = str(row.get("category", "")).strip()
        value_column = str(row.get("column", "")).strip()

        if include in ("no", "false", "0"):
            excluded.append({"domain_id": domain_id, "domain_name": domain_name, "reason": "excluded_by_registry"})
            continue

        file_path = PROJECT_ROOT / Path(path)
        if not file_path.exists():
            missing.append({"domain_id": domain_id, "domain_name": domain_name, "path": str(file_path)})
            continue

        series = load_file_series(
            file_path,
            metric=metric if metric else None,
            category=category if category else None,
            value_column=value_column if value_column else None,
        )
        if not series:
            excluded.append({"domain_id": domain_id, "domain_name": domain_name, "path": str(file_path), "reason": "no_usable_series"})
            continue

        years, values = series
        norm = normalize_series(values)
        if norm is None:
            excluded.append({"domain_id": domain_id, "domain_name": domain_name, "path": str(file_path), "reason": "no_variance"})
            continue

        try:
            params, r2 = fit_decay(years, norm)
        except Exception as exc:
            excluded.append({"domain_id": domain_id, "domain_name": domain_name, "path": str(file_path), "reason": f"fit_failed: {exc}"})
            continue

        y0, lam, t0 = params
        results.append({
            "domain_id": domain_id,
            "domain_name": domain_name,
            "source": source,
            "path": str(file_path),
            "lambda": float(lam),
            "t0": float(t0),
            "r2": float(r2),
            "n_points": int(len(years)),
        })

    lambdas = np.array([r["lambda"] for r in results], dtype=float)
    t0s = np.array([r["t0"] for r in results], dtype=float)

    summary = {
        "n_domains": int(len(results)),
        "lambda_mean": float(np.mean(lambdas)) if len(lambdas) else None,
        "lambda_std": float(np.std(lambdas, ddof=1)) if len(lambdas) > 1 else None,
        "t0_mean": float(np.mean(t0s)) if len(t0s) else None,
        "t0_std": float(np.std(t0s, ddof=1)) if len(t0s) > 1 else None,
        "ks_pvalue": None,
    }

    if len(lambdas) >= 2:
        mu = np.mean(lambdas)
        sigma = np.std(lambdas, ddof=1)
        if sigma == 0:
            summary["ks_pvalue"] = 1.0
        else:
            if stats is not None:
                _, pvalue = stats.kstest(lambdas, "norm", args=(mu, sigma))
                summary["ks_pvalue"] = float(pvalue)
            else:
                summary["ks_pvalue"] = _ks_test_normal(lambdas, mu, sigma)

    claims = {
        "lambda_claim": 0.031,
        "t0_claim": 1967.3,
        "p_claim_lt": 1e-12,
    }

    comparisons = {
        "lambda_diff": None,
        "t0_diff": None,
        "pvalue_meets_claim": None,
    }
    if summary["lambda_mean"] is not None:
        comparisons["lambda_diff"] = float(summary["lambda_mean"] - claims["lambda_claim"])
    if summary["t0_mean"] is not None:
        comparisons["t0_diff"] = float(summary["t0_mean"] - claims["t0_claim"])
    if summary["ks_pvalue"] is not None:
        comparisons["pvalue_meets_claim"] = bool(summary["ks_pvalue"] < claims["p_claim_lt"])

    output = {
        "summary": summary,
        "claims": claims,
        "comparisons": comparisons,
        "per_domain": results,
        "missing": missing,
        "excluded": excluded,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
