#!/usr/bin/env python3
"""
CDCM BATCH CSV EXPORTER
Create master CSV from multiple CDCM scoring results.

Usage:
  python export_cdcm_batch.py CDCM_SCORES/ -o vault_scores.csv
"""

import sys
import json
import csv
from pathlib import Path
from typing import List, Dict

def load_scores(directory: Path) -> List[Dict]:
    """Load all JSON score files from directory."""
    results = []

    if not directory.exists():
        print(f"[ERROR] Directory not found: {directory}")
        return results

    json_files = sorted(directory.glob("*_CDCM_*.json"))

    if not json_files:
        print(f"[WARN] No CDCM score files found in {directory}")
        return results

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)
            results.append(data)
        except Exception as e:
            print(f"  [WARN] Failed to load {json_file.name}: {e}")

    return results

def export_to_csv(results: List[Dict], output_file: Path):
    """Export to master CSV."""

    if not results:
        print("[ERROR] No results to export")
        return

    # Collect all criteria IDs
    all_criteria = set()
    for result in results:
        all_criteria.update(result.get("scores", {}).keys())
    all_criteria = sorted(all_criteria)

    # Build rows
    rows = []
    for result in results:
        metadata = result.get("metadata", {})
        scores = result.get("scores", {})
        composite = result.get("composite_score", 0)
        grade = result.get("grade", "?")
        flagged_criteria = result.get("flagged_criteria", [])
        dim_avgs = result.get("dimension_averages", {})

        row = {
            "Paper": metadata.get("paper", "?").split("/")[-1],
            "Date": metadata.get("timestamp", "?")[:10],
            "Scorer": metadata.get("scorer", "?"),
            "Composite": round(composite, 1),
            "Grade": grade,
            "Flags": len(flagged_criteria),
        }

        # Add all criterion scores
        for crit_id in all_criteria:
            row[f"crit_{crit_id}"] = scores.get(crit_id, "-")

        # Add dimension averages
        for dim in sorted(dim_avgs.keys()):
            row[f"dim_{dim}"] = round(dim_avgs[dim], 1)

        # Add first 3 flagged criteria
        for i, flag in enumerate(flagged_criteria[:3]):
            row[f"flag_{i+1}"] = f"{flag['criterion']}({flag['score']}/10)"
            row[f"fix_{i+1}"] = flag["fix_type"]

        rows.append(row)

    # Determine columns
    columns = ["Paper", "Date", "Scorer", "Composite", "Grade", "Flags"]
    columns.extend([f"crit_{c}" for c in all_criteria])
    columns.extend([f"dim_{d}" for d in sorted(dim_avgs.keys())])
    columns.extend([f"flag_{i}" for i in range(1, 4)])
    columns.extend([f"fix_{i}" for i in range(1, 4)])

    # Write CSV
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, restval="")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Exported {len(rows)} papers to: {output_file}")
    print(f"\n[SUMMARY]")
    print(f"  Papers scored: {len(rows)}")

    # Grade distribution
    grades = {}
    for row in rows:
        grade = row["Grade"]
        grades[grade] = grades.get(grade, 0) + 1

    for grade in sorted(grades.keys()):
        print(f"  Grade {grade}: {grades[grade]}")

    # Average composite
    composites = [r["Composite"] for r in rows]
    if composites:
        print(f"  Average composite: {sum(composites)/len(composites):.1f}/100")

def main():
    if len(sys.argv) < 2:
        print("Usage: python export_cdcm_batch.py CDCM_SCORES/ -o output.csv")
        sys.exit(1)

    directory = Path(sys.argv[1])
    output_file = None

    if "-o" in sys.argv:
        output_file = Path(sys.argv[sys.argv.index("-o") + 1])
    else:
        output_file = Path("vault_scores.csv")

    print(f"[LOAD] Reading scores from: {directory}")
    results = load_scores(directory)

    if results:
        export_to_csv(results, output_file)
    else:
        print("[ERROR] No scores loaded")
        sys.exit(1)

if __name__ == "__main__":
    main()
