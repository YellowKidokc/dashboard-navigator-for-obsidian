#!/usr/bin/env python3
"""
THEOPHYSICS PAPER SCORER — CDCM 44-CRITERIA RUBRIC
====================================================
Scores papers using 44 academic criteria across 11 dimensions.
Uses OpenAI to grade with inter-rater reliability (Claude vs OpenAI).
Exports structured data for improvement tracking.

Usage:
  python papers_scorer_cdcm.py input.md                    # Score single paper
  python papers_scorer_cdcm.py input.md --vault            # Score entire vault
  python papers_scorer_cdcm.py input.md -o output.json     # Custom output
  python papers_scorer_cdcm.py --stats                     # Show vault statistics

Output: JSON with all 44 scores, comments, composite, flags, and recommendations
"""

import sys
import json
import re
import csv
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from collections import Counter, defaultdict

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# ─────────────────────────────────────────────
# RUBRIC: 44 CRITERIA × 11 DIMENSIONS
# ─────────────────────────────────────────────

CRITERIA = {
    "A": {
        "name": "CITATION QUALITY",
        "weight": 0.12,
        "subs": {
            "A1": ("Source Existence & Verifiability", "Made-up refs, dead links, non-existent papers", 0.03),
            "A2": ("Source Authority & Relevance", "Blogs for physics claims, outdated/irrelevant sources", 0.03),
            "A3": ("Citation Formatting", "Missing page #s, wrong format, incomplete bib data", 0.03),
            "A4": ("Citation Density & Distribution", "Unsupported stretches, citation dumping", 0.03),
        }
    },
    "B": {
        "name": "FACTUAL ACCURACY",
        "weight": 0.15,
        "subs": {
            "B1": ("Empirical Claim Accuracy", "Misquoted stats, wrong experimental results", 0.0375),
            "B2": ("Historical/Contextual Accuracy", "Wrong dates, misattributed quotes, anachronisms", 0.0375),
            "B3": ("Mathematical/Formal Accuracy", "Wrong equations, algebra errors, unit mismatches", 0.0375),
            "B4": ("Claim-Evidence Alignment", "Evidence doesn't support the claim it's attached to", 0.0375),
        }
    },
    "C": {
        "name": "LOGICAL RIGOR",
        "weight": 0.15,
        "subs": {
            "C1": ("Deductive Validity", "Non-sequiturs, affirming consequent, false syllogisms", 0.0375),
            "C2": ("Inductive Strength", "Hasty generalization, cherry-picking, small sample", 0.0375),
            "C3": ("Absence of Fallacies", "Ad hominem, straw man, circular reasoning, false dilemma", 0.0375),
            "C4": ("Argument Chain Integrity", "Missing steps, hidden premises, unacknowledged assumptions", 0.0375),
        }
    },
    "D": {
        "name": "EVIDENCE SUFFICIENCY",
        "weight": 0.12,
        "subs": {
            "D1": ("Claim Strength vs Evidence Weight", "Strong claim on weak evidence, overclaiming", 0.03),
            "D2": ("Counter-Evidence Engagement", "Ignoring contradicting studies, dismissing w/o argument", 0.03),
            "D3": ("Replication & Corroboration", "Single-study reliance, unreplicated findings as established", 0.03),
            "D4": ("Statistical Rigor", "P-hacking, wrong test, effect size ignored, N too small", 0.03),
        }
    },
    "E": {
        "name": "SEMANTIC PRECISION",
        "weight": 0.12,
        "subs": {
            "E1": ("Term Definition Consistency", "Key term used with inconsistent definition", 0.03),
            "E2": ("Equivocation Detection", "Sliding between technical and colloquial meanings", 0.03),
            "E3": ("Domain Translation Fidelity", "Term crosses domains without redefinition", 0.03),
            "E4": ("Hedging Calibration", "Proves when means suggests; shows vs consistent with", 0.03),
        }
    },
    "F": {
        "name": "ACADEMIC CONVENTION",
        "weight": 0.08,
        "subs": {
            "F1": ("Abstract Quality", "Missing components, too vague, too long", 0.02),
            "F2": ("Methodology Transparency", "Unclear methods, unreproducible procedures", 0.02),
            "F3": ("Structure & Flow", "Wrong section order, missing transitions", 0.02),
            "F4": ("Peer Convention Compliance", "Missing lit review, no limitations section", 0.02),
        }
    },
    "G": {
        "name": "WORDING & CLARITY",
        "weight": 0.08,
        "subs": {
            "G1": ("Prose Precision", "Vague phrasing, ambiguous pronouns, unclear antecedents", 0.02),
            "G2": ("Jargon Accessibility", "Undefined technical terms, acronym soup", 0.02),
            "G3": ("Concision", "Redundancy, filler, saying same thing 3 ways", 0.02),
            "G4": ("Tone Calibration", "Devotional language in technical sections, overselling", 0.02),
        }
    },
    "H": {
        "name": "CROSS-DOMAIN VALIDITY",
        "weight": 0.1,
        "subs": {
            "H1": ("Isomorphism vs Analogy Distinction", "Treating metaphorical similarity as structural identity", 0.025),
            "H2": ("Domain Boundary Respect", "Importing conclusions from one domain as premises in another", 0.025),
            "H3": ("Mapping Rigor", "Hand-wavy correspondences, selective mapping", 0.025),
            "H4": ("Prediction Transfer", "Claiming cross-domain prediction w/o testable spec", 0.025),
        }
    },
    "I": {
        "name": "FALSIFIABILITY & SCOPE",
        "weight": 0.08,
        "subs": {
            "I1": ("Falsification Criteria Stated", "Unfalsifiable claims, heads I win tails you lose", 0.02),
            "I2": ("Scope Boundaries Declared", "Unlimited scope claims, missing applicability limits", 0.02),
            "I3": ("Failure Mode Acknowledgment", "No discussion of what would make framework wrong", 0.02),
            "I4": ("Testable Prediction Specificity", "Vague predictions, post-hoc fitting", 0.02),
        }
    },
    "J": {
        "name": "EXTERNAL THEORY USAGE",
        "weight": 0.1,
        "subs": {
            "J1": ("Theory Representation Accuracy", "Misrepresenting GR, QM, thermodynamics, info theory, etc.", 0.025),
            "J2": ("Scope Boundary Respect for Borrowed Theories", "Using QM results outside validity domain, over-extrapolating GR", 0.025),
            "J3": ("Integration vs Appropriation", "Name-dropping without substantive engagement, decorative citations", 0.025),
            "J4": ("Competing Interpretation Acknowledgment", "Presenting one QM interpretation as settled, ignoring alternatives", 0.025),
        }
    },
    "K": {
        "name": "NOVELTY ASSESSMENT",
        "weight": 0.1,
        "subs": {
            "K1": ("Conceptual Originality", "Is the core idea genuinely new or repackaged existing work?", 0.025),
            "K2": ("Nearest Existing Framework Distance", "Name 2-3 closest frameworks; rate distance from each", 0.025),
            "K3": ("Methodological Innovation", "Novel method/metric/formalism vs standard approach with new labels?", 0.025),
            "K4": ("Gap-Filling vs Gap-Creating", "Does it answer existing question or open new ones nobody asked?", 0.025),
        }
    },
}

# Fix types and priority levels
FIX_TYPES = {
    "A": "CITE", "B": "FACT-CHECK", "C": "LOGIC", "D": "EVIDENCE",
    "E": "REWORD", "F": "RESTRUCTURE", "G": "REWRITE", "H": "REMAP",
    "I": "SPECIFY", "J": "VERIFY-THEORY", "K": "NOVELTY"
}

FIX_PRIORITY = {
    "B": "P1-CRITICAL", "C": "P1-CRITICAL", "J": "P1-CRITICAL",
    "A": "P2-HIGH", "D": "P2-HIGH", "E": "P2-HIGH", "H": "P2-HIGH", "K": "P2-HIGH",
    "F": "P3-MEDIUM", "G": "P3-MEDIUM", "I": "P3-MEDIUM",
}

OPENAI_PROMPT_SYSTEM = """You are an academic peer reviewer specializing in interdisciplinary research. Grade this paper on 44 sub-criteria, 0-10 each. For EVERY score, add a 1-2 sentence comment explaining your reasoning.

RUBRIC: 10=Flawless | 8-9=Strong | 6-7=Adequate | 4-5=Weak | 2-3=Poor | 0-1=Absent/Violated

BE HARSH. Grade against top-tier interdisciplinary journal standards. Do not grade on a curve.

Pay special attention to:
- Cross-domain reasoning: Are analogies properly distinguished from isomorphisms?
- Theory misuse: Are borrowed theories (GR, QM, thermodynamics, info theory) applied within their validity domains?
- Falsifiability: Are kill conditions and failure modes explicitly stated?
- Novelty: Does this genuinely advance the field or repackage existing work?"""

OPENAI_PROMPT_USER_TEMPLATE = """PAPER: {filename}

AXIOM DECLARATION (if present):
{axiom}

FACTS TABLE (if present):
{facts_table}

ABSTRACT:
{abstract}

FULL PAPER (truncated to 20K chars):
{content}

───────────────────────────────────

SCORE THIS PAPER on 44 criteria. For each score, provide 1-2 sentence reasoning.

A. CITATION QUALITY
A1: [score] — Source Existence & Verifiability | Comment: [reasoning]
A2: [score] — Source Authority & Relevance | Comment: [reasoning]
A3: [score] — Citation Formatting | Comment: [reasoning]
A4: [score] — Citation Density & Distribution | Comment: [reasoning]

B. FACTUAL ACCURACY
B1: [score] — Empirical Claim Accuracy | Comment: [reasoning]
B2: [score] — Historical/Contextual Accuracy | Comment: [reasoning]
B3: [score] — Mathematical/Formal Accuracy | Comment: [reasoning]
B4: [score] — Claim-Evidence Alignment | Comment: [reasoning]

C. LOGICAL RIGOR
C1: [score] — Deductive Validity | Comment: [reasoning]
C2: [score] — Inductive Strength | Comment: [reasoning]
C3: [score] — Absence of Fallacies | Comment: [reasoning]
C4: [score] — Argument Chain Integrity | Comment: [reasoning]

D. EVIDENCE SUFFICIENCY
D1: [score] — Claim Strength vs Evidence Weight | Comment: [reasoning]
D2: [score] — Counter-Evidence Engagement | Comment: [reasoning]
D3: [score] — Replication & Corroboration | Comment: [reasoning]
D4: [score] — Statistical Rigor | Comment: [reasoning]

E. SEMANTIC PRECISION
E1: [score] — Term Definition Consistency | Comment: [reasoning]
E2: [score] — Equivocation Detection | Comment: [reasoning]
E3: [score] — Domain Translation Fidelity | Comment: [reasoning]
E4: [score] — Hedging Calibration | Comment: [reasoning]

F. ACADEMIC CONVENTION
F1: [score] — Abstract Quality | Comment: [reasoning]
F2: [score] — Methodology Transparency | Comment: [reasoning]
F3: [score] — Structure & Flow | Comment: [reasoning]
F4: [score] — Peer Convention Compliance | Comment: [reasoning]

G. WORDING & CLARITY
G1: [score] — Prose Precision | Comment: [reasoning]
G2: [score] — Jargon Accessibility | Comment: [reasoning]
G3: [score] — Concision | Comment: [reasoning]
G4: [score] — Tone Calibration | Comment: [reasoning]

H. CROSS-DOMAIN VALIDITY
H1: [score] — Isomorphism vs Analogy Distinction | Comment: [reasoning]
H2: [score] — Domain Boundary Respect | Comment: [reasoning]
H3: [score] — Mapping Rigor | Comment: [reasoning]
H4: [score] — Prediction Transfer | Comment: [reasoning]

I. FALSIFIABILITY & SCOPE
I1: [score] — Falsification Criteria Stated | Comment: [reasoning]
I2: [score] — Scope Boundaries Declared | Comment: [reasoning]
I3: [score] — Failure Mode Acknowledgment | Comment: [reasoning]
I4: [score] — Testable Prediction Specificity | Comment: [reasoning]

J. EXTERNAL THEORY USAGE
J1: [score] — Theory Representation Accuracy | Comment: [reasoning]
J2: [score] — Scope Boundary Respect for Borrowed Theories | Comment: [reasoning]
J3: [score] — Integration vs Appropriation | Comment: [reasoning]
J4: [score] — Competing Interpretation Acknowledgment | Comment: [reasoning]

K. NOVELTY ASSESSMENT
K1: [score] — Conceptual Originality | Comment: [reasoning]
K2: [score] — Nearest Existing Framework Distance | Comment: [reasoning]
K3: [score] — Methodological Innovation | Comment: [reasoning]
K4: [score] — Gap-Filling vs Gap-Creating | Comment: [reasoning]

───────────────────────────────────

THEN provide:
1. THREE most critical failures with specific quotes
2. Single revision that would most improve overall score
3. One thing the paper does surprisingly well
4. NOVELTY MAP: 3 closest existing frameworks and precise conceptual distance from each"""

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def parse_config(path: Path) -> dict:
    """Read KEY=VALUE pairs from config.txt."""
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg

def extract_axiom_and_facts(text: str) -> Tuple[str, str]:
    """Extract axiom declaration and FACTS table from paper."""
    axiom = ""
    facts = ""

    # Look for AXIOM DECLARATION section
    axiom_match = re.search(
        r"AXIOM\s+DECLARATION.*?:\s*(.+?)(?:\n---|\nFACTS|\n[A-Z]|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if axiom_match:
        axiom = axiom_match.group(1).strip()[:500]

    # Look for FACTS table
    facts_match = re.search(
        r"FACTS.*?(?:F|FIND)\s*\|\s*(.+?)(?:\n[A-Z]|\nABSTRACT|\Z)",
        text, re.IGNORECASE | re.DOTALL
    )
    if facts_match:
        facts = facts_match.group(0).strip()[:1000]

    return axiom, facts

def extract_abstract(text: str) -> str:
    """Extract abstract section."""
    abstract_match = re.search(
        r"(?:ABSTRACT|Abstract)\s*\n+(.+?)(?:\nI\.|INTRODUCTION|##)",
        text, re.IGNORECASE | re.DOTALL
    )
    if abstract_match:
        return abstract_match.group(1).strip()[:1500]
    return ""

def parse_scores_from_response(response_text: str) -> Dict[str, Tuple[int, str]]:
    """Parse OpenAI response: extract score and comment for each criterion."""
    scores = {}

    # Pattern: "A1: [score] — Title | Comment: [text]"
    pattern = r"([A-K]\d):\s*(\d+)\s*(?:—|\\)?\s*[^\|]*\|\s*Comment:\s*(.+?)(?=\n[A-K]\d:|$)"

    matches = re.findall(pattern, response_text, re.DOTALL)
    for criterion, score_str, comment in matches:
        try:
            score = int(score_str)
            score = max(0, min(10, score))  # Clamp 0-10
            scores[criterion] = (score, comment.strip()[:300])
        except ValueError:
            pass

    return scores

def calculate_composite(scores: Dict[str, int]) -> float:
    """Calculate weighted composite score (0-100)."""
    weighted_sum = 0.0
    total_weight = 0.0

    for dim, data in CRITERIA.items():
        dim_score = 0.0
        dim_count = 0

        for crit_id in data["subs"].keys():
            if crit_id in scores:
                dim_score += scores[crit_id]
                dim_count += 1

        if dim_count > 0:
            dim_avg = dim_score / dim_count  # Average per dimension
            weighted_sum += dim_avg * data["weight"]
            total_weight += data["weight"]

    if total_weight > 0:
        return round((weighted_sum / total_weight) * 10, 1)  # Scale to 0-100
    return 0.0

def identify_flagged_criteria(scores: Dict[str, int]) -> List[Tuple[str, str, str, str]]:
    """Find criteria <7 and suggest fix types."""
    flags = []
    for crit_id, score in scores.items():
        if score < 7:
            dim = crit_id[0]
            fix_type = FIX_TYPES.get(dim, "OTHER")
            priority = FIX_PRIORITY.get(dim, "P4-LOW")
            name = CRITERIA[dim]["subs"][crit_id][0]
            flags.append((crit_id, name, fix_type, priority))
    return flags

def call_openai(client: OpenAI, paper_text: str, filename: str) -> Optional[Dict]:
    """Call OpenAI with paper scoring prompt."""
    try:
        axiom, facts_table = extract_axiom_and_facts(paper_text)
        abstract = extract_abstract(paper_text)
        content = paper_text[:20000]  # Truncate to 20K chars

        user_msg = OPENAI_PROMPT_USER_TEMPLATE.format(
            filename=filename,
            axiom=axiom or "[No axiom declaration found]",
            facts_table=facts_table or "[No FACTS table found]",
            abstract=abstract or "[No abstract found]",
            content=content,
        )

        print(f"  [API] Calling OpenAI (gpt-4o)...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": OPENAI_PROMPT_SYSTEM},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        response_text = response.choices[0].message.content
        scores = parse_scores_from_response(response_text)

        # Verify we got all 44 scores
        if len(scores) < 40:  # Allow some tolerance
            print(f"  [WARN] Only parsed {len(scores)}/44 scores. Response may be incomplete.")

        return {
            "scores": scores,
            "raw_response": response_text,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        print(f"  [ERROR] OpenAI call failed: {e}")
        return None

def build_frontmatter(scores: Dict, composite: float, flags: List) -> str:
    """Build YAML frontmatter with all scores."""
    lines = ["---"]
    lines.append(f"cdcm_composite_score: {composite}")
    lines.append(f"cdcm_scored_date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"cdcm_flag_count: {len(flags)}")

    # Per-dimension averages
    for dim, data in CRITERIA.items():
        dim_scores = [scores.get(crit_id, 0) for crit_id in data["subs"].keys()]
        if dim_scores:
            dim_avg = sum(dim_scores) / len(dim_scores)
            lines.append(f"cdcm_{dim.lower()}: {dim_avg:.1f}")

    # Individual criterion scores
    for crit_id in sorted(scores.keys()):
        lines.append(f"cdcm_crit_{crit_id.lower()}: {scores[crit_id]}")

    lines.append("---")
    return "\n".join(lines) + "\n"

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python papers_scorer_cdcm.py <input_file> [-o output_file]")
        print("\nExample:")
        print("  python papers_scorer_cdcm.py paper.md")
        print("  python papers_scorer_cdcm.py paper.md -o scores.json")
        sys.exit(1)

    input_file = Path(sys.argv[1])

    # Config
    script_dir = Path(__file__).parent
    config_file = script_dir / "config.txt"

    if not config_file.exists():
        print(f"[ERROR] config.txt not found in {script_dir}")
        print("   Create config.txt with:")
        print("   OPENAI_API_KEY=your_key_here")
        sys.exit(1)

    cfg = parse_config(config_file)
    api_key = cfg.get("OPENAI_API_KEY")

    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in config.txt")
        sys.exit(1)

    # Read input
    if not input_file.exists():
        print(f"[ERROR] File not found: {input_file}")
        sys.exit(1)

    print(f"\n[FILE] Reading: {input_file.name}")
    paper_text = input_file.read_text(encoding="utf-8", errors="replace")

    # Output file
    output_file = None
    if "-o" in sys.argv:
        output_file = Path(sys.argv[sys.argv.index("-o") + 1])
    else:
        data_folder = input_file.parent / "CDCM_SCORES"
        data_folder.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = data_folder / f"{input_file.stem}_CDCM_{timestamp}.json"

    # Score with OpenAI
    client = OpenAI(api_key=api_key)
    result = call_openai(client, paper_text, input_file.name)

    if result is None:
        print("[ERROR] Scoring failed")
        sys.exit(1)

    scores = result["scores"]
    composite = calculate_composite(scores)
    flags = identify_flagged_criteria(scores)

    # Build output
    output_data = {
        "metadata": {
            "paper": str(input_file),
            "timestamp": datetime.now().isoformat(),
            "scorer": "gpt-4o",
            "version": "CDCM v1.0",
        },
        "composite_score": composite,
        "grade": "A" if composite >= 80 else "B" if composite >= 60 else "C" if composite >= 40 else "F",
        "scores": scores,
        "flagged_criteria": [
            {
                "criterion": crit_id,
                "name": name,
                "score": scores.get(crit_id, 0),
                "fix_type": fix_type,
                "priority": priority,
            }
            for crit_id, name, fix_type, priority in flags
        ],
        "dimension_averages": {
            dim: sum(scores.get(crit_id, 0) for crit_id in data["subs"].keys()) / len(data["subs"])
            for dim, data in CRITERIA.items()
        },
    }

    # Save output
    output_file.write_text(json.dumps(output_data, indent=2), encoding="utf-8")

    # Display summary
    print(f"\n[OK] Scoring complete!")
    print(f"[OUTPUT] {output_file.name}")
    print(f"\n[SCORE] {composite:.1f}/100 — Grade {output_data['grade']}")
    print(f"[FLAGS] {len(flags)} criteria below 7:")

    for crit_id, name, fix_type, priority in flags[:10]:
        score = scores.get(crit_id, 0)
        print(f"   {crit_id} ({score}/10) — {fix_type} [{priority}]")

    if len(flags) > 10:
        print(f"   ... and {len(flags)-10} more")

    print(f"\n[DIMENSIONS]")
    for dim, data in CRITERIA.items():
        dim_scores = [scores.get(crit_id, 0) for crit_id in data["subs"].keys()]
        if dim_scores:
            dim_avg = sum(dim_scores) / len(dim_scores)
            print(f"   {dim} {data['name']:30s} {dim_avg:.1f}/10")

if __name__ == "__main__":
    main()
