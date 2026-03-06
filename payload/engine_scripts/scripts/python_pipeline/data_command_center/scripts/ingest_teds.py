# scripts/ingest_teds.py
"""
TEDS (Treatment Episode Data Set) Ingestion
Downloads treatment admission/discharge data from SAMHSA
"""
from __future__ import annotations
import os
from datetime import datetime
import pandas as pd

SCRIPT_SPEC = {
    "name": "TEDS Treatment Episodes",
    "version": "1.0.0",
    "description": "Load TEDS substance abuse treatment data",
    "parameters": {
        "year": {"type": "int", "default": 2021, "min": 2000, "max": 2023},
        "dataset_type": {"type": "select", "options": ["admissions", "discharges"], "default": "admissions"},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "teds_episodes"},
        "sample_size": {"type": "int", "default": 0, "description": "0 = all rows"},
        "save_to_csv": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

# TEDS data: https://www.samhsa.gov/data/data-we-collect/teds-treatment-episode-data-set

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def run(config: dict, connection=None) -> dict:
    year = config.get("year", 2021)
    dataset_type = config.get("dataset_type", "admissions")
    sample_size = config.get("sample_size", 0)
    save_csv = config.get("save_to_csv", True)
    
    _log(None, f"TEDS {dataset_type} {year} ingestion")
    
    # Check for local file
    local_paths = [
        f"data_lake/teds/teds_{dataset_type}_{year}.csv",
        f"data_lake/teds/TEDS-A-{year}.csv",
        f"data_lake/teds/TEDS-D-{year}.csv",
        f"data_lake/teds/tedsa_puf_{year}.csv",
        f"data_lake/teds/tedsd_puf_{year}.csv",
    ]
    
    df = None
    for path in local_paths:
        if os.path.exists(path):
            _log(None, f"Found: {path}")
            df = pd.read_csv(path, low_memory=False)
            break
    
    if df is None:
        return {
            "status": "manual_download_required",
            "message": f"Please download TEDS {dataset_type} {year} from SAMHSA",
            "url": "https://www.samhsa.gov/data/data-we-collect/teds-treatment-episode-data-set",
            "instructions": f"Save to data_lake/teds/teds_{dataset_type}_{year}.csv",
        }
    
    _log(None, f"Loaded {len(df)} rows")
    
    # Sample
    if sample_size > 0 and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        _log(None, f"Sampled to {len(df)} rows")
    
    # Add metadata
    df["source_year"] = year
    df["dataset_type"] = dataset_type
    df["ingested_at"] = datetime.utcnow().isoformat()
    
    # Save CSV
    csv_path = None
    if save_csv:
        os.makedirs("data_lake/teds/processed", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data_lake/teds/processed/teds_{dataset_type}_{year}_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Saved: {csv_path}")
    
    # Load to DB
    rows_loaded = 0
    if connection:
        out_schema = config.get("output_schema", "raw")
        out_table = config.get("output_table", "teds_episodes")
        
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            col_defs = [f'"{c}" TEXT' for c in df.columns]
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {out_schema}."{out_table}" ({", ".join(col_defs)})')
            
            cols = ", ".join([f'"{c}"' for c in df.columns])
            placeholders = ", ".join(["%s"] * len(df.columns))
            
            for _, row in df.iterrows():
                cursor.execute(
                    f'INSERT INTO {out_schema}."{out_table}" ({cols}) VALUES ({placeholders})',
                    [str(v) if pd.notna(v) else None for v in row.tolist()]
                )
            
            connection.commit()
            rows_loaded = len(df)
            _log(None, f"Loaded to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
    
    return {
        "status": "ok",
        "year": year,
        "dataset_type": dataset_type,
        "rows": len(df),
        "rows_loaded": rows_loaded,
        "csv_path": csv_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
