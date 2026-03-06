#!/usr/bin/env python3
"""
CKG Completeness Index — Weighted Structural Scoring
=====================================================
Measures how structurally complete and epistemically stable a file is.

Five CKG Tiers (20 pts each, 100 total):
  T1 Foundations     — Axioms, definitions, non-contradiction, ontological clarity
  T2 Propositions    — Claims derived, hypotheses distinguished, theorems, scope
  T3 Constraints     — Activated constraints, survival, cross-domain, limiting cases
  T4 Evidence        — Testable predictions, falsification, empirical, traceability
  T5 Integration     — Bridges, master equation map, coherence, downstream

Final Score = 5.0 + (RawScore / 100) * 4.0   →   Range: 5.0–9.0
  - Never below 5 (exists in vault = passed minimal structure)
  - Never above 9 (10 = universal closure, no paper has it)

Usage:
    python ckg_score.py                           # Interactive menu
    python ckg_score.py --score FILE              # Score single file
    python ckg_score.py --batch FOLDER            # Score all .md in folder
    python ckg_score.py --report FOLDER           # Generate summary report
    python ckg_score.py --inject FILE T1 T2 T3 T4 T5  # Manually inject scores
    python ckg_score.py --vault PATH              # Override vault root

Mode: Hybrid — AI generates initial scores, human can override.
      Evaluator field tracks who scored it.
"""

import os
import re
import sys
import json
import argparse
import datetime
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

DEFAULT_VAULT = r"O:\_Theophysics_v3"
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "__pycache__"}
VERSION = "1.0"

# ─── Tier Definitions ────────────────────────────────────────────────────────

TIERS = {
    "tier1_foundations": {
        "label": "T1 Foundations",
        "weight": 20,
        "sub_scores": [
            ("axioms_stated", "Axioms clearly stated"),
            ("definitions_unambiguous", "Definitions unambiguous"),
            ("non_contradiction", "Internal non-contradiction"),
            ("ontological_clarity", "Ontological clarity"),
        ],
    },
    "tier2_propositions": {
        "label": "T2 Propositions",
        "weight": 20,
        "sub_scores": [
            ("claims_derived", "Claims logically derived"),
            ("hypotheses_distinguished", "Hypotheses distinguished from assertions"),
            ("theorems_supported", "Theorems structurally supported"),
            ("scope_declared", "Scope boundaries declared"),
        ],
    },
    "tier3_constraints": {
        "label": "T3 Constraints",
        "weight": 20,
        "sub_scores": [
            ("constraints_declared", "Activated constraints declared"),
            ("survival_demonstrated", "Constraint survival demonstrated"),
            ("cross_domain_tension", "Cross-domain tension addressed"),
            ("limiting_cases", "Limiting cases defined"),
        ],
    },
    "tier4_evidence": {
        "label": "T4 Evidence",
        "weight": 20,
        "sub_scores": [
            ("testable_predictions", "Testable predictions present"),
            ("falsification_criteria", "Falsification criteria defined"),
            ("empirical_support", "Empirical support (if applicable)"),
            ("data_traceability", "Data integrity / traceability"),
        ],
    },
    "tier5_integration": {
        "label": "T5 Integration",
        "weight": 20,
        "sub_scores": [
            ("framework_bridges", "Bridges to other frameworks"),
            ("master_equation_map", "Map to master equation (if relevant)"),
            ("system_coherence", "System coherence maintained"),
            ("downstream_implications", "Downstream implications identified"),
        ],
    },
}

# ─── Heuristic Scoring ──────────────────────────────────────────────────────

# Keyword patterns that indicate presence of tier content
TIER_PATTERNS = {
    "tier1_foundations": {
        "axioms_stated": [r"axiom", r"postulate", r"first principle", r"A\d+\.\d+"],
        "definitions_unambiguous": [r"defin(e|ition|ed)", r":=", r"≡", r"we define"],
        "non_contradiction": [r"consistent", r"non-contradict", r"coherent", r"no contradiction"],
        "ontological_clarity": [r"ontolog", r"exists", r"being", r"substrate", r"fundamental"],
    },
    "tier2_propositions": {
        "claims_derived": [r"therefore", r"it follows", r"we derive", r"⟹", r"implies"],
        "hypotheses_distinguished": [r"hypothes[ie]s", r"conjecture", r"we propose", r"speculative"],
        "theorems_supported": [r"theorem", r"proof", r"QED", r"lemma", r"corollary"],
        "scope_declared": [r"scope", r"this paper", r"within the bounds", r"we limit", r"boundary"],
    },
    "tier3_constraints": {
        "constraints_declared": [r"constraint", r"condition", r"requirement", r"must hold"],
        "survival_demonstrated": [r"survives", r"passes", r"satisfies", r"robust"],
        "cross_domain_tension": [r"tension", r"conflict", r"resolution", r"bridge", r"reconcil"],
        "limiting_cases": [r"limit(ing)? case", r"special case", r"when.*→", r"as.*→"],
    },
    "tier4_evidence": {
        "testable_predictions": [r"predict", r"observable", r"measurement", r"experiment"],
        "falsification_criteria": [r"falsif", r"disprove", r"if.*then.*false", r"refut"],
        "empirical_support": [r"data", r"evidence", r"empirical", r"observed", r"measured"],
        "data_traceability": [r"source", r"reference", r"citation", r"traceab", r"\[\d+\]"],
    },
    "tier5_integration": {
        "framework_bridges": [r"bridge", r"connects to", r"maps to", r"relates to"],
        "master_equation_map": [r"H_Logos", r"master equation", r"χ\(", r"Hamiltonian"],
        "system_coherence": [r"coherence", r"unified", r"consistent with", r"aligns"],
        "downstream_implications": [r"implication", r"consequence", r"downstream", r"predicts"],
    },
}


def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown text."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    yaml_str = text[3:end].strip()
    body = text[end + 4:]

    # Simple YAML parser (no PyYAML dependency)
    fm = {}
    current_key = None
    for line in yaml_str.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped and not stripped.startswith("-"):
            parts = stripped.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip().strip('"').strip("'")
            if val:
                fm[key] = val
            else:
                fm[key] = {}
            current_key = key
    return fm, body


def heuristic_score_file(filepath):
    """Score a file using keyword pattern heuristics. Returns tier scores dict."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return None

    _, body = parse_frontmatter(text)
    body_lower = body.lower()

    scores = {}
    for tier_key, tier_info in TIERS.items():
        tier_total = 0
        sub_details = {}
        patterns = TIER_PATTERNS.get(tier_key, {})

        for sub_key, sub_label in tier_info["sub_scores"]:
            sub_patterns = patterns.get(sub_key, [])
            hits = 0
            for pattern in sub_patterns:
                hits += len(re.findall(pattern, body_lower))

            # Score 0-5 based on hits
            if hits == 0:
                sub_score = 0
            elif hits <= 2:
                sub_score = 2
            elif hits <= 5:
                sub_score = 3
            elif hits <= 10:
                sub_score = 4
            else:
                sub_score = 5

            sub_details[sub_key] = sub_score
            tier_total += sub_score

        scores[tier_key] = tier_total
        scores[f"{tier_key}_detail"] = sub_details

    return scores


def compute_final(scores):
    """Compute raw and final scores from tier scores."""
    raw = sum(scores.get(k, 0) for k in TIERS)
    final = round(5.0 + (raw / 100) * 4.0, 2)
    return raw, final


def build_yaml_block(scores, evaluator="AI-heuristic"):
    """Build the ckg_evaluation YAML block string."""
    raw, final = compute_final(scores)
    now = datetime.date.today().isoformat()

    lines = [
        "ckg_evaluation:",
        f"  tier1_foundations: {scores.get('tier1_foundations', 0)}",
        f"  tier2_propositions: {scores.get('tier2_propositions', 0)}",
        f"  tier3_constraints: {scores.get('tier3_constraints', 0)}",
        f"  tier4_evidence: {scores.get('tier4_evidence', 0)}",
        f"  tier5_integration: {scores.get('tier5_integration', 0)}",
        f"  raw_score: {raw}",
        f"  final_score: {final}",
        f'  evaluator: "{evaluator}"',
        f'  evaluation_version: "{VERSION}"',
        f'  evaluated_date: "{now}"',
    ]
    return "\n".join(lines)


def inject_scores(filepath, scores, evaluator="AI-heuristic"):
    """Inject ckg_evaluation block into file's YAML frontmatter."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return False

    yaml_block = build_yaml_block(scores, evaluator)

    # Remove existing ckg_evaluation block if present
    text = re.sub(
        r"ckg_evaluation:.*?(?=\n[a-zA-Z_]|\n---|\Z)",
        "",
        text,
        flags=re.DOTALL,
    )

    if text.startswith("---"):
        # Insert before closing ---
        end = text.find("\n---", 3)
        if end != -1:
            before = text[: end].rstrip()
            after = text[end:]
            text = f"{before}\n{yaml_block}{after}"
        else:
            # No closing ---, add one
            text = f"---\n{yaml_block}\n---\n{text[3:]}"
    else:
        # No frontmatter at all, add it
        text = f"---\n{yaml_block}\n---\n{text}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return True
    except Exception as e:
        print(f"  ERROR writing {filepath}: {e}")
        return False


def score_file(filepath, inject=False, evaluator="AI-heuristic"):
    """Score a single file and optionally inject."""
    scores = heuristic_score_file(filepath)
    if scores is None:
        return None

    raw, final = compute_final(scores)
    result = {
        "file": os.path.basename(filepath),
        "path": filepath,
        "tier1": scores.get("tier1_foundations", 0),
        "tier2": scores.get("tier2_propositions", 0),
        "tier3": scores.get("tier3_constraints", 0),
        "tier4": scores.get("tier4_evidence", 0),
        "tier5": scores.get("tier5_integration", 0),
        "raw": raw,
        "final": final,
    }

    if inject:
        inject_scores(filepath, scores, evaluator)

    return result


def batch_score(folder, inject=False, evaluator="AI-heuristic"):
    """Score all .md files in a folder."""
    results = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            filepath = os.path.join(root, f)
            result = score_file(filepath, inject=inject, evaluator=evaluator)
            if result:
                results.append(result)
    return results


def generate_report(results, output_path=None):
    """Generate a markdown report from scoring results."""
    if not results:
        print("No results to report.")
        return

    results.sort(key=lambda r: r["final"], reverse=True)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "---",
        'title: "CKG Completeness Report"',
        f'date_created: "{now}"',
        'type: integration',
        'status: draft',
        "---",
        "",
        "# CKG Completeness Report",
        "",
        f"> Generated: {now}  ",
        f"> Files scored: {len(results)}  ",
        f"> Score range: {min(r['final'] for r in results):.2f} – {max(r['final'] for r in results):.2f}",
        "",
        "---",
        "",
        "## Score Distribution",
        "",
        "| Range | Count | Grade |",
        "|---|---|---|",
    ]

    # Distribution buckets
    buckets = {
        "8.5–9.0": (8.5, 9.01),
        "8.0–8.5": (8.0, 8.5),
        "7.5–8.0": (7.5, 8.0),
        "7.0–7.5": (7.0, 7.5),
        "6.5–7.0": (6.5, 7.0),
        "6.0–6.5": (6.0, 6.5),
        "5.0–6.0": (5.0, 6.0),
    }
    grades = {
        "8.5–9.0": "Excellent",
        "8.0–8.5": "Strong",
        "7.5–8.0": "Good",
        "7.0–7.5": "Developing",
        "6.5–7.0": "Early",
        "6.0–6.5": "Minimal",
        "5.0–6.0": "Stub",
    }
    for label, (lo, hi) in buckets.items():
        count = sum(1 for r in results if lo <= r["final"] < hi)
        lines.append(f"| {label} | {count} | {grades[label]} |")

    lines += [
        "",
        "---",
        "",
        "## All Files (sorted by score)",
        "",
        "| File | T1 | T2 | T3 | T4 | T5 | Raw | **Final** |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        fname = r["file"]
        if len(fname) > 45:
            fname = fname[:42] + "..."
        lines.append(
            f"| {fname} | {r['tier1']} | {r['tier2']} | {r['tier3']} "
            f"| {r['tier4']} | {r['tier5']} | {r['raw']} | **{r['final']:.2f}** |"
        )

    # Red flags: any tier < 10
    lines += ["", "---", "", "## Red Flags (Tier < 10)", ""]
    flags = []
    for r in results:
        weak = []
        for tn, tk in [
            ("T1", "tier1"),
            ("T2", "tier2"),
            ("T3", "tier3"),
            ("T4", "tier4"),
            ("T5", "tier5"),
        ]:
            if r[tk] < 10:
                weak.append(f"{tn}={r[tk]}")
        if weak:
            flags.append(f"- **{r['file']}** — {', '.join(weak)}")

    if flags:
        lines.extend(flags)
    else:
        lines.append("No red flags found.")

    report = "\n".join(lines)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to: {output_path}")
    else:
        print(report)

    return report


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CKG Completeness Index — Structural scoring for Theophysics vault"
    )
    parser.add_argument("--score", metavar="FILE", help="Score a single file")
    parser.add_argument("--batch", metavar="FOLDER", help="Score all .md in folder")
    parser.add_argument("--report", metavar="FOLDER", help="Generate report for folder")
    parser.add_argument("--inject", metavar="FILE", help="Score and inject into YAML")
    parser.add_argument(
        "--inject-manual",
        nargs=6,
        metavar=("FILE", "T1", "T2", "T3", "T4", "T5"),
        help="Manually inject tier scores",
    )
    parser.add_argument("--inject-batch", metavar="FOLDER", help="Score and inject all .md")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help="Vault root path")
    parser.add_argument(
        "--output", "-o", metavar="FILE", help="Output report to file"
    )
    parser.add_argument(
        "--evaluator", default="AI-heuristic", help="Evaluator name for audit trail"
    )

    args = parser.parse_args()

    if args.score:
        result = score_file(args.score)
        if result:
            print(f"File: {result['file']}")
            print(f"  T1={result['tier1']}  T2={result['tier2']}  T3={result['tier3']}  "
                  f"T4={result['tier4']}  T5={result['tier5']}")
            print(f"  Raw: {result['raw']}/100  →  Final: {result['final']:.2f}")
        else:
            print("Could not score file.")

    elif args.inject:
        result = score_file(args.inject, inject=True, evaluator=args.evaluator)
        if result:
            print(f"Scored and injected: {result['file']} → {result['final']:.2f}")

    elif args.inject_manual:
        filepath = args.inject_manual[0]
        scores = {
            "tier1_foundations": int(args.inject_manual[1]),
            "tier2_propositions": int(args.inject_manual[2]),
            "tier3_constraints": int(args.inject_manual[3]),
            "tier4_evidence": int(args.inject_manual[4]),
            "tier5_integration": int(args.inject_manual[5]),
        }
        if inject_scores(filepath, scores, evaluator=args.evaluator):
            raw, final = compute_final(scores)
            print(f"Injected manual scores: {filepath} → {final:.2f}")

    elif args.batch:
        results = batch_score(args.batch, evaluator=args.evaluator)
        for r in sorted(results, key=lambda x: x["final"], reverse=True):
            print(f"  {r['final']:.2f}  {r['file']}")
        print(f"\n{len(results)} files scored.")

    elif args.inject_batch:
        results = batch_score(args.inject_batch, inject=True, evaluator=args.evaluator)
        for r in sorted(results, key=lambda x: x["final"], reverse=True):
            print(f"  {r['final']:.2f}  {r['file']}")
        print(f"\n{len(results)} files scored and injected.")

    elif args.report:
        results = batch_score(args.report, evaluator=args.evaluator)
        output = args.output or os.path.join(args.report, "_CKG_REPORT.md")
        generate_report(results, output)

    else:
        # Interactive menu
        print("=" * 60)
        print("  CKG Completeness Index — Theophysics Scoring Engine")
        print("=" * 60)
        print()
        print("  [1] Score a single file")
        print("  [2] Score a folder (dry run)")
        print("  [3] Score and inject into a folder")
        print("  [4] Generate report for a folder")
        print("  [5] Manual score injection")
        print("  [0] Exit")
        print()

        choice = input("  Choice: ").strip()

        if choice == "1":
            path = input("  File path: ").strip().strip('"')
            result = score_file(path)
            if result:
                print(f"\n  {result['file']}")
                print(f"  T1={result['tier1']}  T2={result['tier2']}  T3={result['tier3']}  "
                      f"T4={result['tier4']}  T5={result['tier5']}")
                print(f"  Raw: {result['raw']}/100  →  Final: {result['final']:.2f}")

        elif choice == "2":
            path = input("  Folder path: ").strip().strip('"')
            results = batch_score(path)
            for r in sorted(results, key=lambda x: x["final"], reverse=True)[:20]:
                print(f"  {r['final']:.2f}  {r['file']}")
            print(f"\n  {len(results)} files scored (top 20 shown).")

        elif choice == "3":
            path = input("  Folder path: ").strip().strip('"')
            confirm = input(f"  Inject scores into all .md in {path}? (y/n): ").strip()
            if confirm.lower() == "y":
                results = batch_score(path, inject=True)
                print(f"\n  {len(results)} files scored and injected.")

        elif choice == "4":
            path = input("  Folder path: ").strip().strip('"')
            results = batch_score(path)
            output = os.path.join(path, "_CKG_REPORT.md")
            generate_report(results, output)

        elif choice == "5":
            path = input("  File path: ").strip().strip('"')
            print("  Enter tier scores (0-20 each):")
            t1 = int(input("    T1 Foundations: "))
            t2 = int(input("    T2 Propositions: "))
            t3 = int(input("    T3 Constraints: "))
            t4 = int(input("    T4 Evidence: "))
            t5 = int(input("    T5 Integration: "))
            scores = {
                "tier1_foundations": t1,
                "tier2_propositions": t2,
                "tier3_constraints": t3,
                "tier4_evidence": t4,
                "tier5_integration": t5,
            }
            evaluator = input("  Evaluator (default: human): ").strip() or "human"
            if inject_scores(path, scores, evaluator):
                raw, final = compute_final(scores)
                print(f"\n  Injected: {final:.2f}")


if __name__ == "__main__":
    main()
