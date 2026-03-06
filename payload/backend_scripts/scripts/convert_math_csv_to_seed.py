"""
Convert and merge math registry seed data from canonical CSV into YAML.

Primary source:
  D:/01_Axioms/04_REFERENCE/MATH_TRANSLATION_TABLE.csv

Merge behavior:
- CSV drives translation/content fields.
- Existing YAML keeps manual governance fields when present
  (code, z2_mirror, aliases, owner_folder, and custom keys).
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml


CSV_CATEGORY_DOMAIN_MAP = {
    "constants": "CONST",
    "differentials": "DIFF",
    "fields": "FIELD",
    "functionals": "FUNC",
    "functions": "FUNC",
    "greek_letters": "GREEK",
    "integrals": "INT",
    "lagrangians": "LAGR",
    "matrices": "MATRIX",
    "notation": "NOTATION",
    "operators": "OPS",
    "spinors": "SPINOR",
    "tensors": "TENSOR",
    "variables": "VAR",
    "m_e": "VAR",
}


def clean_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def normalize_symbol(text: str) -> str:
    raw = clean_cell(text)
    raw = raw.replace("$", "")
    raw = re.sub(r"\s+", "", raw)
    return raw.lower()


def slugify_symbol(symbol: str) -> str:
    s = clean_cell(symbol)
    s = s.replace("\\", "")
    s = re.sub(r"\{.*?\}", "", s)
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    s = s.strip("_")
    return s.lower() or "symbol"


def domain_from_category(category: str) -> str:
    key = clean_cell(category).lower()
    if not key:
        return "MATH"
    return CSV_CATEGORY_DOMAIN_MAP.get(key, re.sub(r"[^A-Za-z0-9]+", "_", key).upper()[:12] or "MATH")


def build_aliases(row: Dict[str, str], existing_aliases: Optional[List[str]] = None) -> List[str]:
    alias_set: Set[str] = set(existing_aliases or [])
    basic = clean_cell(row.get("Basic_Translation"))

    candidates = [
        clean_cell(row.get("Symbol_LaTeX")),
        clean_cell(row.get("Symbol_LaTeX")).replace("\\", ""),
        clean_cell(row.get("Symbol_Display")),
        clean_cell(row.get("Math_Name")),
        re.sub(r"\s+", "_", basic.lower()).strip("_")[:40] if basic else "",
    ]
    for item in candidates:
        cleaned = clean_cell(item)
        if cleaned:
            alias_set.add(cleaned)

    return sorted(alias_set)


def load_existing_entries(seed_path: Path) -> List[Dict[str, object]]:
    if not seed_path.exists():
        return []
    data = yaml.safe_load(seed_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return []
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        return []
    return [e for e in entries if isinstance(e, dict)]


def index_existing_entries(entries: List[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    index: Dict[str, Dict[str, object]] = {}
    for entry in entries:
        symbol = normalize_symbol(str(entry.get("symbol", "")))
        if symbol:
            index[symbol] = entry
    return index


def generate_code(domain: str, symbol: str, used_codes: Set[str]) -> str:
    base = slugify_symbol(symbol)
    code = f"[{domain}:{base}]"
    i = 2
    while code in used_codes:
        code = f"[{domain}:{base}_{i}]"
        i += 1
    used_codes.add(code)
    return code


def merge_csv_into_seed(csv_path: Path, existing_entries: List[Dict[str, object]]) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
    existing_by_symbol = index_existing_entries(existing_entries)
    used_codes: Set[str] = {
        str(e.get("code", "")).strip() for e in existing_entries if str(e.get("code", "")).strip()
    }
    matched_symbols: Set[str] = set()
    merged: List[Dict[str, object]] = []

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            symbol = clean_cell(row.get("Symbol_LaTeX"))
            if not symbol:
                continue

            symbol_key = normalize_symbol(symbol)
            existing = existing_by_symbol.get(symbol_key)
            if existing:
                matched_symbols.add(symbol_key)

            category = clean_cell(row.get("Category"))
            domain = clean_cell(existing.get("domain")) if existing else ""
            if not domain:
                domain = domain_from_category(category)

            code = clean_cell(existing.get("code")) if existing else ""
            if not code:
                code = generate_code(domain, symbol, used_codes)
            else:
                used_codes.add(code)

            basic = clean_cell(row.get("Basic_Translation"))
            medium = clean_cell(row.get("Medium_Translation"))
            academic = clean_cell(row.get("Academic_Translation"))
            definition = academic or medium or basic or (clean_cell(existing.get("definition")) if existing else "")
            if not definition:
                definition = "Definition pending."
            symbol_display = clean_cell(row.get("Symbol_Display")) or (
                clean_cell(existing.get("symbol_display")) if existing else ""
            )

            merged_entry: Dict[str, object] = {}
            if existing:
                merged_entry.update(existing)

            merged_entry.update(
                {
                    "code": code,
                    "symbol": symbol,
                    "symbol_display": symbol_display,
                    "domain": domain,
                    "category": category,
                    "math_name": clean_cell(row.get("Math_Name")),
                    "definition": definition,
                    "basic_translation": basic or definition,
                    "medium_translation": medium or basic or definition,
                    "academic_translation": academic or medium or basic or definition,
                    "context_notes": clean_cell(row.get("Context_Notes")),
                    "first_appears": clean_cell(row.get("First_Appears")),
                    "aliases": build_aliases(row, existing.get("aliases") if existing else None),
                    "owner_folder": clean_cell(existing.get("owner_folder")) if existing else "04_THEOPYHISCS",
                }
            )

            if not clean_cell(str(merged_entry.get("owner_folder", ""))):
                merged_entry["owner_folder"] = "04_THEOPYHISCS"

            merged.append(merged_entry)

    carry_over = [
        e
        for e in existing_entries
        if normalize_symbol(str(e.get("symbol", "")))
        and normalize_symbol(str(e.get("symbol", ""))) not in matched_symbols
    ]

    merged.extend(carry_over)
    merged_sorted = sorted(merged, key=lambda x: str(x.get("code", "~")))

    stats = {
        "csv_rows_written": len(merged) - len(carry_over),
        "existing_carried_over": len(carry_over),
        "total_output_entries": len(merged_sorted),
        "matched_existing": len(matched_symbols),
    }
    return merged_sorted, stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge canonical math CSV into YAML registry seed.")
    parser.add_argument(
        "--csv",
        default="D:/01_Axioms/04_REFERENCE/MATH_TRANSLATION_TABLE.csv",
        help="Canonical CSV path.",
    )
    parser.add_argument(
        "--existing-seed",
        default="config/math_registry_seed.yaml",
        help="Existing YAML seed to preserve manual fields.",
    )
    parser.add_argument(
        "--output",
        default="config/math_registry_seed_v2.yaml",
        help="Output YAML path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    existing_seed = Path(args.existing_seed)
    output_path = Path(args.output)

    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    existing_entries = load_existing_entries(existing_seed)
    merged_entries, stats = merge_csv_into_seed(csv_path, existing_entries)

    payload = {
        "entries": merged_entries,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )

    print("=== CSV -> Seed Merge Complete ===")
    print(f"CSV source: {csv_path}")
    print(f"Existing seed: {existing_seed} ({len(existing_entries)} entries)")
    print(f"Output: {output_path}")
    print(
        "Stats: "
        f"csv_rows_written={stats['csv_rows_written']}, "
        f"matched_existing={stats['matched_existing']}, "
        f"existing_carried_over={stats['existing_carried_over']}, "
        f"total_output_entries={stats['total_output_entries']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
