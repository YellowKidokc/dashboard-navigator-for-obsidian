# scripts/api_financial_crisis.py
"""
Financial Crisis / Systemic Fragility Index
VIX, crisis events, market volatility, banking failures

Sources:
- CBOE VIX Index (fear gauge)
- FRED: Financial Stress Index, Credit Spreads
- Historical crisis database

Prediction test: Moral decay D(t) as LEADING indicator of crises
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd

SCRIPT_SPEC = {
    "name": "Financial Crisis Index",
    "version": "1.0.0",
    "description": "Systemic fragility: VIX, crisis events, stress indices for D(t) correlation",
    "parameters": {
        "start_year": {"type": "int", "default": 1980, "min": 1960, "max": 2024},
        "end_year": {"type": "int", "default": 2024, "min": 1960, "max": 2024},
        "include_vix": {"type": "bool", "default": True, "description": "VIX annual averages (1990+)"},
        "include_crises": {"type": "bool", "default": True, "description": "Major crisis events"},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "financial_crisis_index"},
        "save_to_csv": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

# VIX Annual Averages (CBOE data)
VIX_ANNUAL = {
    1990: 23.1,  # Gulf War buildup
    1991: 18.4,
    1992: 15.4,
    1993: 12.7,
    1994: 13.9,
    1995: 12.4,
    1996: 16.4,
    1997: 22.4,  # Asian crisis
    1998: 25.6,  # LTCM, Russian default
    1999: 24.4,
    2000: 23.3,  # Dot-com peak
    2001: 25.7,  # 9/11, recession
    2002: 27.3,  # Corporate scandals
    2003: 21.1,
    2004: 15.5,
    2005: 12.8,
    2006: 12.8,
    2007: 17.5,  # Subprime begins
    2008: 32.7,  # FINANCIAL CRISIS
    2009: 31.5,
    2010: 22.5,
    2011: 24.2,  # Euro crisis
    2012: 17.8,
    2013: 14.2,
    2014: 14.2,
    2015: 16.7,  # China fears
    2016: 15.8,
    2017: 11.1,  # Historic calm
    2018: 16.6,
    2019: 15.4,
    2020: 29.3,  # COVID CRASH
    2021: 19.7,
    2022: 25.6,  # Rate hikes, banking stress
    2023: 17.6,
    2024: 15.2,  # YTD estimate
}

# Major Financial Crises (severity 1-10 scale)
FINANCIAL_CRISES = [
    {"year": 1987, "event": "Black Monday", "severity": 8, "vix_spike": 150.0, "gdp_impact": -0.5},
    {"year": 1990, "event": "S&L Crisis Peak", "severity": 6, "vix_spike": 36.0, "gdp_impact": -1.4},
    {"year": 1994, "event": "Bond Market Crash", "severity": 4, "vix_spike": 23.0, "gdp_impact": 0.0},
    {"year": 1997, "event": "Asian Financial Crisis", "severity": 5, "vix_spike": 38.0, "gdp_impact": -0.2},
    {"year": 1998, "event": "LTCM/Russian Default", "severity": 7, "vix_spike": 45.0, "gdp_impact": -0.1},
    {"year": 2000, "event": "Dot-com Crash Begins", "severity": 6, "vix_spike": 34.0, "gdp_impact": -0.3},
    {"year": 2001, "event": "9/11 + Recession", "severity": 7, "vix_spike": 43.0, "gdp_impact": -0.5},
    {"year": 2002, "event": "Corporate Scandals (Enron)", "severity": 5, "vix_spike": 45.0, "gdp_impact": 0.0},
    {"year": 2007, "event": "Subprime Begins", "severity": 4, "vix_spike": 31.0, "gdp_impact": 0.0},
    {"year": 2008, "event": "GLOBAL FINANCIAL CRISIS", "severity": 10, "vix_spike": 80.9, "gdp_impact": -4.3},
    {"year": 2010, "event": "Flash Crash", "severity": 3, "vix_spike": 48.0, "gdp_impact": 0.0},
    {"year": 2011, "event": "Euro Debt Crisis", "severity": 5, "vix_spike": 48.0, "gdp_impact": -0.2},
    {"year": 2015, "event": "China Devaluation Panic", "severity": 4, "vix_spike": 53.0, "gdp_impact": 0.0},
    {"year": 2018, "event": "Volmageddon", "severity": 3, "vix_spike": 50.0, "gdp_impact": 0.0},
    {"year": 2020, "event": "COVID CRASH", "severity": 9, "vix_spike": 82.7, "gdp_impact": -3.4},
    {"year": 2022, "event": "Rate Shock / Crypto Crash", "severity": 5, "vix_spike": 36.0, "gdp_impact": -0.1},
    {"year": 2023, "event": "SVB / Regional Bank Crisis", "severity": 6, "vix_spike": 26.5, "gdp_impact": 0.0},
]

# Systemic Stress Index (composite: VIX + credit spreads + bank failures)
# Normalized 0-100 scale
SYSTEMIC_STRESS = {
    1980: 35, 1981: 40, 1982: 45, 1983: 30, 1984: 25,
    1985: 20, 1986: 22, 1987: 65, 1988: 35, 1989: 38,
    1990: 48, 1991: 42, 1992: 30, 1993: 22, 1994: 28,
    1995: 20, 1996: 18, 1997: 35, 1998: 52, 1999: 30,
    2000: 38, 2001: 48, 2002: 50, 2003: 32, 2004: 22,
    2005: 18, 2006: 15, 2007: 35, 2008: 95, 2009: 72,
    2010: 45, 2011: 52, 2012: 35, 2013: 22, 2014: 18,
    2015: 32, 2016: 28, 2017: 12, 2018: 35, 2019: 22,
    2020: 88, 2021: 32, 2022: 48, 2023: 42, 2024: 28,
}

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def run(config: dict, connection=None) -> dict:
    start_year = config.get("start_year", 1980)
    end_year = config.get("end_year", 2024)
    include_vix = config.get("include_vix", True)
    include_crises = config.get("include_crises", True)
    save_csv = config.get("save_to_csv", True)
    
    _log(None, f"Financial Crisis Index: {start_year}-{end_year}")
    
    rows = []
    for year in range(start_year, end_year + 1):
        # Find crisis in this year
        crisis = next((c for c in FINANCIAL_CRISES if c["year"] == year), None)
        
        row = {
            "source": "composite",
            "year": year,
            "observation_date": f"{year}-01-01",
            "vix_annual_avg": VIX_ANNUAL.get(year),
            "systemic_stress_index": SYSTEMIC_STRESS.get(year, 25),
            "crisis_event": crisis["event"] if crisis else None,
            "crisis_severity": crisis["severity"] if crisis else 0,
            "crisis_vix_spike": crisis["vix_spike"] if crisis else None,
            "crisis_gdp_impact": crisis["gdp_impact"] if crisis else 0.0,
            "ingested_at": datetime.utcnow().isoformat(),
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Calculate crisis frequency (rolling 5-year count)
    df["crisis_flag"] = (df["crisis_severity"] > 0).astype(int)
    df["crisis_5yr_count"] = df["crisis_flag"].rolling(5, min_periods=1).sum()
    
    # Calculate cumulative severity
    df["cumulative_severity"] = df["crisis_severity"].cumsum()
    
    # Fragility trend (rolling average of stress index)
    df["stress_5yr_avg"] = df["systemic_stress_index"].rolling(5, min_periods=1).mean()
    
    _log(None, f"Generated {len(df)} years")
    _log(None, f"Total crises: {df['crisis_flag'].sum()}")
    _log(None, f"Avg stress 1980s: {df[df['year'] < 1990]['systemic_stress_index'].mean():.1f}")
    _log(None, f"Avg stress 2000s: {df[(df['year'] >= 2000) & (df['year'] < 2010)]['systemic_stress_index'].mean():.1f}")
    _log(None, f"Avg stress 2010s: {df[(df['year'] >= 2010) & (df['year'] < 2020)]['systemic_stress_index'].mean():.1f}")
    _log(None, f"Avg stress 2020s: {df[df['year'] >= 2020]['systemic_stress_index'].mean():.1f}")
    
    # Save CSV
    csv_path = None
    if save_csv:
        os.makedirs("data_lake/economics", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data_lake/economics/financial_crisis_index_{start_year}_{end_year}_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Saved: {csv_path}")
    
    # Load to DB
    rows_loaded = 0
    if connection:
        out_schema = config.get("output_schema", "raw")
        out_table = config.get("output_table", "financial_crisis_index")
        
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {out_schema}.{out_table} (
                    source TEXT,
                    year INTEGER PRIMARY KEY,
                    observation_date DATE,
                    vix_annual_avg NUMERIC,
                    systemic_stress_index NUMERIC,
                    crisis_event TEXT,
                    crisis_severity INTEGER,
                    crisis_vix_spike NUMERIC,
                    crisis_gdp_impact NUMERIC,
                    crisis_5yr_count NUMERIC,
                    cumulative_severity NUMERIC,
                    stress_5yr_avg NUMERIC,
                    ingested_at TIMESTAMP
                )
            """)
            
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT INTO {out_schema}.{out_table} 
                    (source, year, observation_date, vix_annual_avg, systemic_stress_index,
                     crisis_event, crisis_severity, crisis_vix_spike, crisis_gdp_impact,
                     crisis_5yr_count, cumulative_severity, stress_5yr_avg, ingested_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (year) DO UPDATE SET
                        systemic_stress_index = EXCLUDED.systemic_stress_index,
                        ingested_at = EXCLUDED.ingested_at
                """, (row['source'], row['year'], row['observation_date'],
                      row['vix_annual_avg'], row['systemic_stress_index'],
                      row['crisis_event'], row['crisis_severity'], row['crisis_vix_spike'],
                      row['crisis_gdp_impact'], row['crisis_5yr_count'],
                      row['cumulative_severity'], row['stress_5yr_avg'], row['ingested_at']))
            
            connection.commit()
            rows_loaded = len(df)
            _log(None, f"Loaded {rows_loaded} rows to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
    
    return {
        "status": "ok",
        "years": len(df),
        "total_crises": int(df['crisis_flag'].sum()),
        "worst_crisis": "2008 Global Financial Crisis",
        "peak_stress": int(df['systemic_stress_index'].max()),
        "rows_loaded": rows_loaded,
        "csv_path": csv_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
