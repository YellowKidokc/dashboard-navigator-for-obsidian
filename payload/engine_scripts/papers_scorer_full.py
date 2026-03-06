#!/usr/bin/env python3
"""
LOWE STANDARD FULL SCORER v1.0
================================
One API call. Everything scored. Excel output.

Scores papers across:
  - 44 CDCM criteria (11 dimensions x 4 sub-criteria)
  - 6 Lowe Standard criteria (FACTS/Biaxiosum/Kill/Battery/Audit/FactSheet)
  - Generates 5 falsification criteria (kill conditions)
  - Maps 3 nearest competing theories with distance scores
  - Extracts/generates FACTS summary table
  - Identifies 3 critical failures with quotes
  - Provides single most impactful revision
  - Outputs to CDCM_final Excel template + JSON

Usage:
  python papers_scorer_full.py paper.md
  python papers_scorer_full.py paper.md -o report.xlsx
  python papers_scorer_full.py paper.md --json-only

Output:
  - Excel workbook (CDCM_final format with all sheets populated)
  - JSON with complete structured data
  - Console summary with grade + flags + action items
"""
