# scripts/data_cleaner.py
"""
Robust Data Cleaner for CSV/Excel → PostgreSQL
Handles: type inference, date parsing, deduplication, column normalization
"""
from __future__ import annotations
import os
import re
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List
import pandas as pd

SCRIPT_SPEC = {
    "name": "Data Cleaner → PostgreSQL",
    "version": "1.0.0",
    "description": "Clean CSV/Excel files and load to PostgreSQL",
    "parameters": {
        "input_path": {"type": "path", "default": "", "description": "CSV or Excel file to clean"},
        "sheet_name": {"type": "string", "default": "", "description": "Excel sheet name (blank = first)"},
        "output_schema": {"type": "string", "default": "raw"},
        "output_table": {"type": "string", "default": "imported_data"},
        "if_exists": {"type": "select", "options": ["append", "replace", "fail"], "default": "append"},
        "dedupe_columns": {"type": "string", "default": "", "description": "Comma-separated key columns for dedup"},
        "date_columns": {"type": "string", "default": "", "description": "Comma-separated date columns"},
        "numeric_columns": {"type": "string", "default": "", "description": "Comma-separated numeric columns"},
        "drop_empty_rows": {"type": "bool", "default": True},
        "trim_strings": {"type": "bool", "default": True},
        "normalize_columns": {"type": "bool", "default": True},
        "infer_types": {"type": "bool", "default": True},
        "write_profile": {"type": "bool", "default": True},
    },
    "target_db": {
        "type": "select",
        "options": ["nas_postgres", "laptop_postgres"],
        "default": "laptop_postgres",
    },
}

def _log(ctx, msg: str) -> None:
    if ctx and hasattr(ctx, "log") and callable(ctx.log):
        ctx.log(msg)
    else:
        print(msg)

def _safe_col(name: str) -> str:
    """Normalize column name to postgres-safe format."""
    name = str(name).strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_{2,}", "_", name).strip("_")
    if not name:
        name = "col"
    if name[0].isdigit():
        name = f"c_{name}"
    return name

def _parse_list(s: str) -> List[str]:
    """Parse comma-separated string to list."""
    if not s:
        return []
    return [x.strip() for x in s.split(",") if x.strip()]

def _file_hash(path: str) -> str:
    """Get SHA256 of file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

def _profile_df(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate data profile."""
    profile = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "fields": {},
    }
    
    for col in df.columns:
        s = df[col]
        nulls = int(s.isna().sum())
        
        try:
            uniques = int(s.nunique(dropna=True))
        except:
            uniques = None
        
        profile["fields"][col] = {
            "dtype": str(s.dtype),
            "nulls": nulls,
            "null_pct": round(nulls / max(1, len(s)) * 100, 1),
            "uniques": uniques,
        }
    
    return profile

def run(config: dict, connection=None) -> dict:
    input_path = config.get("input_path", "")
    
    if not input_path or not os.path.exists(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}")
    
    _log(None, f"Loading file: {input_path}")
    
    # Load file
    ext = os.path.splitext(input_path.lower())[1]
    sheet_name = config.get("sheet_name", "").strip()
    
    if ext in [".xlsx", ".xlsm", ".xls"]:
        df = pd.read_excel(input_path, sheet_name=sheet_name or 0)
    elif ext in [".csv", ".tsv", ".txt"]:
        sep = "\t" if ext == ".tsv" else ","
        df = pd.read_csv(input_path, sep=sep, dtype="object", low_memory=False)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    original_cols = list(df.columns)
    original_rows = len(df)
    _log(None, f"Loaded {original_rows} rows, {len(original_cols)} columns")
    
    # Normalize column names
    if config.get("normalize_columns", True):
        df.columns = [_safe_col(c) for c in df.columns]
        _log(None, "Normalized column names")
    
    # Drop empty rows
    if config.get("drop_empty_rows", True):
        before = len(df)
        df = df.dropna(how="all")
        dropped = before - len(df)
        if dropped:
            _log(None, f"Dropped {dropped} empty rows")
    
    # Trim strings
    if config.get("trim_strings", True):
        obj_cols = [c for c in df.columns if df[c].dtype == "object"]
        for c in obj_cols:
            df[c] = df[c].astype("string").str.strip()
        _log(None, f"Trimmed {len(obj_cols)} text columns")
    
    # Coerce date columns
    date_cols = _parse_list(config.get("date_columns", ""))
    for c in date_cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
            _log(None, f"Parsed date column: {c}")
    
    # Coerce numeric columns
    num_cols = _parse_list(config.get("numeric_columns", ""))
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            _log(None, f"Parsed numeric column: {c}")
    
    # Infer types
    if config.get("infer_types", True):
        for c in df.columns:
            if df[c].dtype == "object":
                sample = df[c].dropna().astype(str).head(50)
                if sample.empty:
                    continue
                # Skip if looks like ID with leading zeros
                if any(re.match(r"^0\d+$", x) for x in sample):
                    continue
                # Try numeric
                parsed = pd.to_numeric(sample, errors="coerce")
                if parsed.notna().mean() >= 0.9:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
        _log(None, "Type inference complete")
    
    # Deduplicate
    dedupe_cols = _parse_list(config.get("dedupe_columns", ""))
    if dedupe_cols:
        missing = [c for c in dedupe_cols if c not in df.columns]
        if missing:
            _log(None, f"Warning: dedupe columns not found: {missing}")
        else:
            before = len(df)
            df = df.drop_duplicates(subset=dedupe_cols, keep="last")
            dropped = before - len(df)
            if dropped:
                _log(None, f"Dropped {dropped} duplicates on {dedupe_cols}")
    
    # Generate profile
    profile = _profile_df(df)
    profile_path = None
    
    if config.get("write_profile", True):
        os.makedirs("data_lake/profiles", exist_ok=True)
        file_hash = _file_hash(input_path)
        profile_path = f"data_lake/profiles/profile_{file_hash}.json"
        
        with open(profile_path, "w") as f:
            json.dump({
                "input_path": input_path,
                "original_columns": original_cols,
                "clean_columns": list(df.columns),
                "profile": profile,
            }, f, indent=2, default=str)
        _log(None, f"Wrote profile: {profile_path}")
    
    # Load to database
    rows_loaded = 0
    if connection:
        out_schema = config.get("output_schema", "raw")
        out_table = config.get("output_table", "imported_data")
        if_exists = config.get("if_exists", "append")
        
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {out_schema}")
            
            # Build column definitions
            col_defs = []
            for col in df.columns:
                dtype = df[col].dtype
                if pd.api.types.is_integer_dtype(dtype):
                    col_defs.append(f'"{col}" BIGINT')
                elif pd.api.types.is_float_dtype(dtype):
                    col_defs.append(f'"{col}" NUMERIC')
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    col_defs.append(f'"{col}" TIMESTAMP')
                else:
                    col_defs.append(f'"{col}" TEXT')
            
            create_sql = f'CREATE TABLE IF NOT EXISTS {out_schema}."{out_table}" ({", ".join(col_defs)})'
            cursor.execute(create_sql)
            
            if if_exists == "replace":
                cursor.execute(f'TRUNCATE TABLE {out_schema}."{out_table}"')
            
            # Insert rows
            cols = ", ".join([f'"{c}"' for c in df.columns])
            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_sql = f'INSERT INTO {out_schema}."{out_table}" ({cols}) VALUES ({placeholders})'
            
            for _, row in df.iterrows():
                values = [None if pd.isna(v) else v for v in row.tolist()]
                cursor.execute(insert_sql, values)
            
            connection.commit()
            rows_loaded = len(df)
            _log(None, f"Loaded {rows_loaded} rows to {out_schema}.{out_table}")
            
        except Exception as e:
            _log(None, f"DB Error: {e}")
            raise
    
    return {
        "status": "ok",
        "original_rows": original_rows,
        "clean_rows": len(df),
        "columns": len(df.columns),
        "rows_loaded": rows_loaded,
        "profile_path": profile_path,
        "computed_at": datetime.utcnow().isoformat() + "Z",
    }
