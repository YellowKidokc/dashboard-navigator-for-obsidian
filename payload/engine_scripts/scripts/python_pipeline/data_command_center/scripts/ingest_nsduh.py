# scripts/ingest_nsduh.py
"""
NSDUH (National Survey on Drug Use and Health) Data Ingestion
Downloads public use files from SAMHSA
"""
from __future__ import annotations
import os
from datetime import datetime
import pandas as pd
import requests
import zipfile
import io

SCRIPT_SPEC = {
    "name": "NSDUH Drug Survey Data",
    "version": "1.0.0",
    "description": "Download NSDUH survey data from SAMHSA",
    "parameters": {
        "year": {"type": "int", "default": 2022, "min": 2015, "max": 2023},
        "file_format": {"type": "select", "options": ["csv", "stata", "sas"], "default": "csv"},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "nsduh_survey"},
        "sample_size": {"type": "int", "default": 0, "description": "0 = all rows, >0 = random sample"},
        "save_to_csv": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select", 
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

# NSDUH data access:
# https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health
# Public use files available in SAS, STATA, SPSS, Delimited formats

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def run(config: dict, connection=None) -> dict:
    year = config.get("year", 2022)
    sample_size = config.get("sample_size", 0)
    save_csv = config.get("save_to_csv", True)
    
    _log(None, f"NSDUH {year} data ingestion")
    _log(None, "Note: NSDUH PUFs must be downloaded manually from SAMHSA")
    _log(None, "https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health")
    
    # Check for local file
    local_paths = [
        f"data_lake/nsduh/NSDUH_{year}.csv",
        f"data_lake/nsduh/nsduh_{year}.csv",
        f"data_lake/nsduh/NSDUH_{year}_Tab.txt",
    ]
    
    df = None
    for path in local_paths:
        if os.path.exists(path):
            _log(None, f"Found local file: {path}")
            if path.endswith(".csv"):
                df = pd.read_csv(path, low_memory=False)
            elif path.endswith(".txt"):
                df = pd.read_csv(path, sep="\t", low_memory=False)
            break
    
    if df is None:
        return {
            "status": "manual_download_required",
            "message": f"Please download NSDUH {year} PUF from SAMHSA and place in data_lake/nsduh/",
            "url": "https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health",
        }
    
    _log(None, f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    # Sample if requested
    if sample_size > 0 and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42)
        _log(None, f"Sampled to {len(df)} rows")
    
    # Add metadata
    df["source_year"] = year
    df["ingested_at"] = datetime.utcnow().isoformat()
    
    # Save to CSV
    csv_path = None
    if save_csv:
        os.makedirs("data_lake/nsduh/processed", exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        csv_path = f"data_lake/nsduh/processed/nsduh_{year}_{ts}.csv"
        df.to_csv(csv_path, index=False)
        _log(None, f"Saved: {csv_path}")
    
    # Load to DB
    rows_loaded = 0
    if connection:
        out_schema = config.get("output_schema", "raw")
        out_table = config.get("output_table", "nsduh_survey")
        
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            # Create table (TEXT columns for flexibility)
            col_defs = [f'"{c}" TEXT' for c in df.columns]
            cursor.execute(f'CREATE TABLE IF NOT EXISTS {out_schema}."{out_table}" ({", ".join(col_defs)})')
            
            # Insert
            cols = ", ".join([f'"{c}"' for c in df.columns])
            placeholders = ", ".join(["%s"] * len(df.columns))
            
            for _, row in df.iterrows():
                cursor.execute(
                    f'INSERT INTO {out_schema}."{out_table}" ({cols}) VALUES ({placeholders})',
                    [str(v) if pd.notna(v) else None for v in row.tolist()]
                )
            
            connection.commit()
            rows_loaded = len(df)
            _log(None, f"Loaded {rows_loaded} rows to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
    
    return {
        "status": "ok",
        "year": year,
        "rows": len(df),
        "columns": len(df.columns),
        "rows_loaded": rows_loaded,
        "csv_path": csv_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
