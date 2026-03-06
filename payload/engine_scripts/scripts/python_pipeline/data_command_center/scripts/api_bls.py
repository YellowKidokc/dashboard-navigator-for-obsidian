# scripts/api_bls.py
"""
Bureau of Labor Statistics API
Free API key from: https://www.bls.gov/developers/
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import requests

SCRIPT_SPEC = {
    "name": "BLS Economic Data",
    "version": "1.0.0",
    "description": "Download employment/labor data from Bureau of Labor Statistics",
    "parameters": {
        "series_ids": {
            "type": "string",
            "default": "LNS14000000,CES0000000001,CUUR0000SA0",
            "description": "Comma-separated BLS series IDs"
        },
        "start_year": {"type": "int", "default": 2020, "min": 1900, "max": 2030},
        "end_year": {"type": "int", "default": 2024, "min": 1900, "max": 2030},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "bls_series"},
        "if_exists": {"type": "select", "options": ["append", "replace"], "default": "append"},
        "save_to_csv": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

# Common BLS Series:
# LNS14000000 - Unemployment Rate
# CES0000000001 - Total Nonfarm Employment
# CUUR0000SA0 - CPI All Urban Consumers
# LNS11300000 - Labor Force Participation Rate

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def _get_api_key() -> str:
    key = os.getenv("BLS_API_KEY", "")
    if not key:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                keys = json.load(f)
                key = keys.get("bls", "")
    return key

def run(config: dict, connection=None) -> dict:
    api_key = _get_api_key()
    
    series_list = [s.strip() for s in config.get("series_ids", "").split(",") if s.strip()]
    start_year = int(config.get("start_year", 2020))
    end_year = int(config.get("end_year", 2024))
    save_csv = config.get("save_to_csv", True)
    
    if not series_list:
        raise ValueError("No series IDs provided")
    
    _log(None, f"Fetching BLS data for {len(series_list)} series...")
    
    # BLS API v2 (with key) or v1 (without)
    if api_key:
        url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
        headers = {"Content-type": "application/json"}
        payload = json.dumps({
            "seriesid": series_list,
            "startyear": str(start_year),
            "endyear": str(end_year),
            "registrationkey": api_key,
        })
    else:
        url = "https://api.bls.gov/publicAPI/v1/timeseries/data/"
        headers = {"Content-type": "application/json"}
        payload = json.dumps({
            "seriesid": series_list,
            "startyear": str(start_year),
            "endyear": str(end_year),
        })
        _log(None, "Note: Using BLS API v1 (no key). Rate limited to 25 queries/day.")
    
    all_data = []
    
    try:
        r = requests.post(url, data=payload, headers=headers, timeout=60)
        r.raise_for_status()
        result = r.json()
        
        if result.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS API error: {result.get('message', 'Unknown error')}")
        
        for series in result.get("Results", {}).get("series", []):
            series_id = series.get("seriesID")
            for item in series.get("data", []):
                year = item.get("year")
                period = item.get("period", "M01")
                month = period.replace("M", "").zfill(2) if period.startswith("M") else "01"
                
                all_data.append({
                    "source": "bls",
                    "series_id": series_id,
                    "observation_date": f"{year}-{month}-01",
                    "value": float(item.get("value", 0)),
                    "period": period,
                    "period_name": item.get("periodName", ""),
                    "ingested_at": datetime.utcnow().isoformat(),
                })
            
            _log(None, f"  {series_id}: {len(series.get('data', []))} observations")
    
    except Exception as e:
        _log(None, f"Error: {e}")
        raise
    
    if not all_data:
        return {"status": "error", "message": "No data retrieved"}
    
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    csv_path = None
    if save_csv:
        os.makedirs("data_lake/bls", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data_lake/bls/bls_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Saved CSV: {csv_path}")
    
    # Save to database
    rows_loaded = 0
    if connection:
        try:
            out_schema = config.get("output_schema", "raw")
            out_table = config.get("output_table", "bls_series")
            
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {out_schema}.{out_table} (
                    source TEXT,
                    series_id TEXT,
                    observation_date DATE,
                    value NUMERIC,
                    period TEXT,
                    period_name TEXT,
                    ingested_at TIMESTAMP,
                    PRIMARY KEY (series_id, observation_date)
                )
            """)
            
            if config.get("if_exists") == "replace":
                cursor.execute(f"TRUNCATE TABLE {out_schema}.{out_table}")
            
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT INTO {out_schema}.{out_table} 
                    (source, series_id, observation_date, value, period, period_name, ingested_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (series_id, observation_date) DO UPDATE SET value = EXCLUDED.value
                """, tuple(row))
            
            connection.commit()
            rows_loaded = len(df)
            _log(None, f"Loaded {rows_loaded} rows to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
    
    return {
        "status": "ok",
        "series_count": len(series_list),
        "rows": len(df),
        "rows_loaded": rows_loaded,
        "csv_path": csv_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
