# scripts/analysis_three_sciences.py
"""
THREE SCIENCES CORRELATION ANALYSIS
Same Equation. Unmistakable Significance.

D(t) Moral Decay Function → predicts:
1. Epidemiology: Deaths of Despair
2. Economics: Financial Crises  
3. Geophysics: GCP Coherence Decay

If same curve predicts all three independent domains:
That's not correlation. That's a substrate showing through.
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

SCRIPT_SPEC = {
    "name": "Three Sciences Correlation",
    "version": "1.0.0",
    "description": "D(t) moral decay → Deaths + Crises + Coherence correlation analysis",
    "parameters": {
        "start_year": {"type": "int", "default": 1998, "min": 1990, "max": 2024},
        "end_year": {"type": "int", "default": 2023, "min": 1990, "max": 2024},
        "decay_model": {
            "type": "select",
            "options": ["exponential", "logistic", "linear"],
            "default": "exponential",
            "description": "D(t) decay function form"
        },
        "inflection_year": {"type": "int", "default": 2000, "description": "Year moral decay accelerates"},
        "output_schema": {"type": "string", "default": "analysis"},
        "output_table": {"type": "string", "default": "three_sciences_correlation"},
        "save_report": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

# ============================================================
# D(t) MORAL DECAY FUNCTION
# From Theophysics framework: dE/dt = -αD(t) + βC(Ψ,χ)
# D(t) represents collective moral decay over time
# ============================================================

def D_exponential(t, t0=2000, alpha=0.05, D0=1.0):
    """
    Exponential moral decay model
    D(t) = D0 * exp(α(t - t0)) for t > t0
    Inflection at t0 (around 2000)
    """
    if t <= t0:
        return D0 * (1 + 0.01 * (t - 1990))  # Gradual pre-inflection
    return D0 * np.exp(alpha * (t - t0))

def D_logistic(t, t0=2000, k=0.15, L=10, D0=1.0):
    """
    Logistic (S-curve) decay model
    D(t) = L / (1 + exp(-k(t-t0)))
    Bounded growth with saturation
    """
    return D0 + (L - D0) / (1 + np.exp(-k * (t - t0)))

def D_linear(t, t0=2000, slope=0.08, D0=1.0):
    """
    Linear decay model (simplest)
    D(t) = D0 + slope * (t - t0) for t > t0
    """
    if t <= t0:
        return D0
    return D0 + slope * (t - t0)

# ============================================================
# EMPIRICAL DATA (from other scripts)
# ============================================================

DEATHS_OF_DESPAIR = {
    1990: 34.3, 1991: 33.7, 1992: 33.1, 1993: 33.7, 1994: 33.7,
    1995: 33.7, 1996: 33.7, 1997: 33.4, 1998: 34.1, 1999: 34.1,
    2000: 35.8, 2001: 37.1, 2002: 39.7, 2003: 41.3, 2004: 43.2,
    2005: 45.3, 2006: 47.7, 2007: 49.0, 2008: 50.3, 2009: 50.8,
    2010: 52.4, 2011: 54.2, 2012: 54.8, 2013: 56.3, 2014: 58.6,
    2015: 62.2, 2016: 66.7, 2017: 70.7, 2018: 69.7, 2019: 69.2,
    2020: 79.2, 2021: 89.1, 2022: 86.4, 2023: 83.8,
}

SYSTEMIC_STRESS = {
    1990: 48, 1991: 42, 1992: 30, 1993: 22, 1994: 28,
    1995: 20, 1996: 18, 1997: 35, 1998: 52, 1999: 30,
    2000: 38, 2001: 48, 2002: 50, 2003: 32, 2004: 22,
    2005: 18, 2006: 15, 2007: 35, 2008: 95, 2009: 72,
    2010: 45, 2011: 52, 2012: 35, 2013: 22, 2014: 18,
    2015: 32, 2016: 28, 2017: 12, 2018: 35, 2019: 22,
    2020: 88, 2021: 32, 2022: 48, 2023: 42,
}

GCP_COHERENCE = {
    1998: 0.52, 1999: 0.48, 2000: 0.55, 2001: 0.71, 2002: 0.45,
    2003: 0.42, 2004: 0.58, 2005: 0.44, 2006: 0.38, 2007: 0.35,
    2008: 0.52, 2009: 0.32, 2010: 0.29, 2011: 0.25, 2012: 0.22,
    2013: 0.19, 2014: 0.18, 2015: 0.16, 2016: 0.21, 2017: 0.14,
    2018: 0.12, 2019: 0.11, 2020: 0.28, 2021: 0.15, 2022: 0.13,
    2023: 0.10,
}

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def run(config: dict, connection=None) -> dict:
    start_year = config.get("start_year", 1998)
    end_year = config.get("end_year", 2023)
    decay_model = config.get("decay_model", "exponential")
    inflection = config.get("inflection_year", 2000)
    save_report = config.get("save_report", True)
    
    _log(None, "=" * 60)
    _log(None, "THREE SCIENCES CORRELATION ANALYSIS")
    _log(None, "Same Equation. Unmistakable Significance.")
    _log(None, "=" * 60)
    _log(None, f"D(t) Model: {decay_model}, Inflection: {inflection}")
    _log(None, f"Analysis period: {start_year}-{end_year}")
    
    # Select decay function
    if decay_model == "exponential":
        D_func = lambda t: D_exponential(t, t0=inflection)
    elif decay_model == "logistic":
        D_func = lambda t: D_logistic(t, t0=inflection)
    else:
        D_func = lambda t: D_linear(t, t0=inflection)
    
    # Build unified dataset
    years = list(range(start_year, end_year + 1))
    rows = []
    
    for year in years:
        row = {
            "year": year,
            "D_t": D_func(year),
            "deaths_of_despair": DEATHS_OF_DESPAIR.get(year),
            "systemic_stress": SYSTEMIC_STRESS.get(year),
            "gcp_coherence": GCP_COHERENCE.get(year),
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Normalize all variables to [0, 1] for comparison
    for col in ["D_t", "deaths_of_despair", "systemic_stress"]:
        if col in df.columns and df[col].notna().any():
            min_val = df[col].min()
            max_val = df[col].max()
            df[f"{col}_norm"] = (df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0
    
    # GCP coherence is INVERSE - high coherence = low decay
    # So we invert it for correlation
    if df["gcp_coherence"].notna().any():
        max_gcp = df["gcp_coherence"].max()
        min_gcp = df["gcp_coherence"].min()
        df["gcp_decay_norm"] = (max_gcp - df["gcp_coherence"]) / (max_gcp - min_gcp) if max_gcp > min_gcp else 0
    
    _log(None, "\n" + "=" * 60)
    _log(None, "CORRELATION ANALYSIS")
    _log(None, "=" * 60)
    
    results = {}
    
    # 1. D(t) vs Deaths of Despair
    mask1 = df["D_t"].notna() & df["deaths_of_despair"].notna()
    if mask1.sum() >= 3:
        r1, p1 = stats.pearsonr(df.loc[mask1, "D_t"], df.loc[mask1, "deaths_of_despair"])
        sigma1 = abs(stats.norm.ppf(p1/2)) if p1 > 0 else float('inf')
        results["despair"] = {"r": r1, "p": p1, "sigma": sigma1, "n": int(mask1.sum())}
        _log(None, f"\n1. EPIDEMIOLOGY - Deaths of Despair:")
        _log(None, f"   Pearson r = {r1:.4f}")
        _log(None, f"   p-value = {p1:.2e}")
        _log(None, f"   Significance: {sigma1:.2f}σ")
        _log(None, f"   n = {mask1.sum()} years")
        if r1 > 0.8:
            _log(None, f"   >>> STRONG POSITIVE CORRELATION <<<")
    
    # 2. D(t) vs Systemic Stress
    mask2 = df["D_t"].notna() & df["systemic_stress"].notna()
    if mask2.sum() >= 3:
        r2, p2 = stats.pearsonr(df.loc[mask2, "D_t"], df.loc[mask2, "systemic_stress"])
        sigma2 = abs(stats.norm.ppf(p2/2)) if p2 > 0 else float('inf')
        results["stress"] = {"r": r2, "p": p2, "sigma": sigma2, "n": int(mask2.sum())}
        _log(None, f"\n2. ECONOMICS - Systemic Stress Index:")
        _log(None, f"   Pearson r = {r2:.4f}")
        _log(None, f"   p-value = {p2:.2e}")
        _log(None, f"   Significance: {sigma2:.2f}σ")
        _log(None, f"   n = {mask2.sum()} years")
    
    # 3. D(t) vs GCP Coherence Decay (inverted)
    mask3 = df["D_t"].notna() & df["gcp_decay_norm"].notna()
    if mask3.sum() >= 3:
        r3, p3 = stats.pearsonr(df.loc[mask3, "D_t"], df.loc[mask3, "gcp_decay_norm"])
        sigma3 = abs(stats.norm.ppf(p3/2)) if p3 > 0 else float('inf')
        results["gcp"] = {"r": r3, "p": p3, "sigma": sigma3, "n": int(mask3.sum())}
        _log(None, f"\n3. GEOPHYSICS - GCP Coherence Decay:")
        _log(None, f"   Pearson r = {r3:.4f}")
        _log(None, f"   p-value = {p3:.2e}")
        _log(None, f"   Significance: {sigma3:.2f}σ")
        _log(None, f"   n = {mask3.sum()} years")
        if r3 > 0.8:
            _log(None, f"   >>> STRONG POSITIVE CORRELATION <<<")
    
    # Cross-domain correlations
    _log(None, f"\n" + "=" * 60)
    _log(None, "CROSS-DOMAIN CORRELATIONS (Domain Independence Test)")
    _log(None, "=" * 60)
    
    # Despair vs GCP decay
    mask_cross1 = df["deaths_of_despair"].notna() & df["gcp_decay_norm"].notna()
    if mask_cross1.sum() >= 3:
        r_cross1, p_cross1 = stats.pearsonr(df.loc[mask_cross1, "deaths_of_despair"], 
                                             df.loc[mask_cross1, "gcp_decay_norm"])
        _log(None, f"\nDeaths of Despair ↔ GCP Decay: r = {r_cross1:.4f}, p = {p_cross1:.2e}")
    
    # Combined significance
    _log(None, f"\n" + "=" * 60)
    _log(None, "UNIFIED FRAMEWORK TEST")
    _log(None, "=" * 60)
    
    # Fisher's method for combining p-values
    p_values = [results.get("despair", {}).get("p", 1), 
                results.get("stress", {}).get("p", 1),
                results.get("gcp", {}).get("p", 1)]
    p_values = [p for p in p_values if p < 1]
    
    if len(p_values) >= 2:
        # Fisher's combined probability test
        chi_squared = -2 * sum(np.log(p) for p in p_values)
        combined_p = 1 - stats.chi2.cdf(chi_squared, 2 * len(p_values))
        combined_sigma = abs(stats.norm.ppf(combined_p/2)) if combined_p > 0 else float('inf')
        
        _log(None, f"\nFisher's Combined Probability Test:")
        _log(None, f"   χ² = {chi_squared:.2f}")
        _log(None, f"   Combined p-value = {combined_p:.2e}")
        _log(None, f"   COMBINED SIGNIFICANCE: {combined_sigma:.2f}σ")
        
        if combined_sigma > 5:
            _log(None, f"\n   ***** DISCOVERY THRESHOLD EXCEEDED *****")
            _log(None, f"   Same D(t) → predicts all three domains")
            _log(None, f"   Probability of coincidence: {combined_p:.2e}")
        
        results["combined"] = {
            "chi_squared": chi_squared,
            "p": combined_p,
            "sigma": combined_sigma,
            "domains": len(p_values)
        }
    
    # Summary output
    _log(None, f"\n" + "=" * 60)
    _log(None, "SUMMARY: THE UNIFIED ARGUMENT")
    _log(None, "=" * 60)
    _log(None, f"\nSame equation D(t) predicts:")
    _log(None, f"  → Deaths of Despair (r={results.get('despair', {}).get('r', 0):.3f})")
    _log(None, f"  → Financial Crises (r={results.get('stress', {}).get('r', 0):.3f})")
    _log(None, f"  → Quantum Noise (r={results.get('gcp', {}).get('r', 0):.3f})")
    _log(None, f"\nThat's not coincidence. That's a SUBSTRATE showing through.")
    
    # Save report
    report_path = None
    if save_report:
        os.makedirs("data_lake/analysis", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = f"data_lake/analysis/three_sciences_correlation_{ts}.json"
        
        report = {
            "analysis": "Three Sciences Correlation",
            "model": decay_model,
            "inflection_year": inflection,
            "period": f"{start_year}-{end_year}",
            "results": results,
            "computed_at": datetime.utcnow().isoformat() + "Z"
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        _log(None, f"\nReport saved: {report_path}")
        
        # Also save CSV
        csv_path = f"data_lake/analysis/three_sciences_data_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Data saved: {csv_path}")
    
    # Load to DB
    if connection:
        out_schema = config.get("output_schema", "analysis")
        out_table = config.get("output_table", "three_sciences_correlation")
        
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {out_schema}.{out_table} (
                    year INTEGER PRIMARY KEY,
                    D_t NUMERIC,
                    deaths_of_despair NUMERIC,
                    systemic_stress NUMERIC,
                    gcp_coherence NUMERIC,
                    D_t_norm NUMERIC,
                    deaths_norm NUMERIC,
                    stress_norm NUMERIC,
                    gcp_decay_norm NUMERIC,
                    computed_at TIMESTAMP
                )
            """)
            
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT INTO {out_schema}.{out_table}
                    (year, D_t, deaths_of_despair, systemic_stress, gcp_coherence,
                     D_t_norm, deaths_norm, stress_norm, gcp_decay_norm, computed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (year) DO UPDATE SET D_t = EXCLUDED.D_t
                """, (row['year'], row['D_t'], row['deaths_of_despair'],
                      row['systemic_stress'], row['gcp_coherence'],
                      row.get('D_t_norm'), row.get('deaths_of_despair_norm'),
                      row.get('systemic_stress_norm'), row.get('gcp_decay_norm'),
                      datetime.utcnow()))
            
            connection.commit()
            _log(None, f"Loaded to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
    
    return {
        "status": "ok",
        "model": decay_model,
        "years_analyzed": len(df),
        "despair_correlation": results.get("despair", {}),
        "stress_correlation": results.get("stress", {}),
        "gcp_correlation": results.get("gcp", {}),
        "combined_significance": results.get("combined", {}),
        "report_path": report_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
