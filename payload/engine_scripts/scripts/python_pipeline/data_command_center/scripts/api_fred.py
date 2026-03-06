# scripts/api_fred.py
"""
FRED API - Federal Reserve Economic Data
Free API key from: https://fred.stlouisfed.org/docs/api/api_key.html
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import requests

SCRIPT_SPEC = {
    "name": "FRED Economic Data",
    "version": "1.0.0",
    "description": "Download economic data from Federal Reserve FRED API",
    "parameters": {
        "series_ids": {
            "type": "string",
            "default": "UNRATE,GDP,CPIAUCSL,FEDFUNDS",
            "description": "Comma-separated series IDs (e.g., UNRATE, GDP, CPIAUCSL)"
        },
        "start_date": {"type": "string", "default": "2020-01-01"},
        "end_date": {"type": "string", "default": "2024-12-31"},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "fred_series"},
        "if_exists": {"type": "select", "options": ["append", "replace"], "default": "append"},
        "save_to_csv": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres", "d1_cloud"],
        "default": "laptop_postgres",
    },
}

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def _get_api_key() -> str:
    key = os.getenv("FRED_API_KEY", "")
    if not key:
        # Check for config file
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "api_keys.json")
        if os.path.exists(config_path):
            with open(config_path) as f:
                keys = json.load(f)
                key = keys.get("fred", "")
    return key

def run(config: dict, connection=None) -> dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("FRED_API_KEY not found. Set env var or add to config/api_keys.json")
    
    series_list = [s.strip().upper() for s in config.get("series_ids", "").split(",") if s.strip()]
    start_date = config.get("start_date", "2020-01-01")
    end_date = config.get("end_date", "2024-12-31")
    save_csv = config.get("save_to_csv", True)
    
    if not series_list:
        raise ValueError("No series IDs provided")
    
    all_data = []
    
    for series_id in series_list:
        _log(None, f"Fetching FRED series: {series_id}")
        
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date,
        }
        
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            observations = data.get("observations", [])
            for obs in observations:
                all_data.append({
                    "source": "fred",
                    "series_id": series_id,
                    "observation_date": obs.get("date"),
                    "value": float(obs.get("value")) if obs.get("value") != "." else None,
                    "ingested_at": datetime.utcnow().isoformat(),
                })
            
            _log(None, f"  → {len(observations)} observations")
            
        except Exception as e:
            _log(None, f"  ✗ Error: {e}")
    
    if not all_data:
        return {"status": "error", "message": "No data retrieved"}
    
    df = pd.DataFrame(all_data)
    
    # Save to CSV
    csv_path = None
    if save_csv:
        os.makedirs("data_lake/fred", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data_lake/fred/fred_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Saved CSV: {csv_path}")
    
    # Save to database if connection provided
    rows_loaded = 0
    if connection:
        try:
            out_schema = config.get("output_schema", "raw")
            out_table = config.get("output_table", "fred_series")
            if_exists = config.get("if_exists", "append")
            
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            # Create table if needed
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {out_schema}.{out_table} (
                    source TEXT,
                    series_id TEXT,
                    observation_date DATE,
                    value NUMERIC,
                    ingested_at TIMESTAMP,
                    PRIMARY KEY (series_id, observation_date)
                )
            """)
            
            if if_exists == "replace":
                cursor.execute(f"TRUNCATE TABLE {out_schema}.{out_table}")
            
            # Insert data
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT INTO {out_schema}.{out_table} 
                    (source, series_id, observation_date, value, ingested_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (series_id, observation_date) DO UPDATE SET value = EXCLUDED.value
                """, (row['source'], row['series_id'], row['observation_date'], row['value'], row['ingested_at']))
            
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
