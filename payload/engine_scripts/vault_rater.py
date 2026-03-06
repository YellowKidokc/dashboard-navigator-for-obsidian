#!/usr/bin/env python3
"""
THEOPHYSICS VAULT RATER — TSR-100 Derived Hybrid Two-Pass System
=================================================================
Built for POF 2828 / David Lowe / Theophysics

Rates every .md paper in the vault using OpenAI, then:
  - Updates YAML frontmatter with scores (Dataview-ready)
  - Moves files into tier folders (A/B/C/D)
  - Outputs a master CSV of all ratings
  - Resume-capable: skips already-rated files
  - Backup-capable: can restore all moves

Architecture:
  Pass 1 (gpt-4o-mini) — Fast triage into A/B/C/D tiers
  Pass 2 (gpt-4o)      — Deep 100-point rating on A-tier only

Rating Rubric (derived from TSR-100):
  The TSR-100 rates worldviews. This adapts it to rate individual papers
  on how well they CONTRIBUTE to the framework's coherence:

  [30 pts] Framework Contribution — Does this paper advance boundary
           conditions or core axioms from De Revolutionibus Veritatis?
  [25 pts] Deductive Rigor — Math→truth chain, not apologetics retrofit.
           Falsification criteria present? Formal argument structure?
  [20 pts] Coherence Integration — Does it connect to Master Equation,
           Ten Laws, or other papers without contradiction?
  [15 pts] Completeness — Full argument vs fragment? Publication-ready?
  [10 pts] Originality — Novel contribution vs restating known ground?

Usage:
  python vault_rater.py                          # Both passes, full vault
  python vault_rater.py --dry-run                # Preview, no changes
  python vault_rater.py --pass 1                 # Triage only
  python vault_rater.py --pass 2                 # Deep-rate A-tier only
  python vault_rater.py --limit 20               # Test on 20 files
  python vault_rater.py --restore                # Undo all moves
  python vault_rater.py --stats                  # Show current ratings
  python vault_rater.py --skip-move              # Rate but don't move files
  python vault_rater.py --min-words 100          # Skip files under N words
"""

import os
import sys
import re
import json
import csv
import time
import shutil
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from collections import Counter

try:
    from openai import OpenAI, RateLimitError, APIError, AuthenticationError
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai")
    sys.exit(1)

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.txt"

DEFAULT_VAULT = r"O:\_Theophysics_v3"
TIER_FOLDERS = {"A": "_TIER_A", "B": "_TIER_B", "C": "_TIER_C", "D": "_TIER_D"}
META_DIR = "_vault_rater"          # Inside vault, holds state/csv/backups
STATE_FILE = "rating_state.json"
CSV_OUTPUT = "vault_ratings.csv"
BACKUP_LOG = "move_log.json"

# Models
MODEL_TRIAGE = "gpt-5-mini"
MODEL_DEEP = "gpt-4o"

# Cost guardrails
MAX_CHARS_PASS1 = 8000       # ~2K tokens for triage
MAX_CHARS_PASS2 = 24000      # ~6K tokens for deep rating
BATCH_DELAY = 0.2            # Seconds between API calls
MAX_RETRIES = 3
RETRY_DELAY = 5

# Pricing (USD per 1K tokens, 2025-Q2)
PRICING = {
    "gpt-4o":      (0.0025, 0.0100),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-5-mini":  (0.0003, 0.0012),
}

# Skip patterns — folders and files to never rate
SKIP_FOLDERS = {
    ".obsidian", ".git", ".trash", "_TIER_A", "_TIER_B", "_TIER_C", "_TIER_D",
    "_vault_rater", "_RATING_BACKUPS", "node_modules", ".git",
    "templates", "Templates", "_templates",
}
SKIP_FILES = {
    "README.md", "CHANGELOG.md", "LICENSE.md", "index.md",
}

# ─────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────

TRIAGE_SYSTEM = """You are rating individual papers from the Theophysics research framework.

FRAMEWORK CONTEXT:
- Master Equation: χ = ∭(G·M·E·S·T·K·R·Q·F·C)dxdydt
- Ten Universal Laws with symmetry pairs (1↔8, 2↔9, 3↔10, 4↔7, 5↔6)
- Core claim: consciousness is fundamental (not emergent)
- Physics and theology are dual projections of a single substrate (divinely ordered relational logic)
- Validated by: PEAR-LAB (6.35σ), GCP (6σ), PROP-COSMOS (5.7σ)
- Rating standard: TSR-100 (Truth Satisfaction Rating) from De Revolutionibus Veritatis

YOUR JOB: Read the paper and assign ONE tier based on its contribution to the framework.

TIER DEFINITIONS:
A = Substantial, coherent argument. Makes a real contribution — advances boundary conditions, core axioms, or integration across domains. Has structure. Worth deep analysis.
B = Decent content with real ideas but incomplete, rough, or partially developed. Identifiable contribution but needs work.
C = Fragment, note, brainstorm, or early draft. Some kernels of value but not a formed paper.
D = Duplicate, obsolete, off-topic, near-empty, or purely administrative/metadata content. No analytical value.

CRITICAL: Be honest. Most papers in any research vault are B or C. A-tier should be reserved for papers that genuinely advance the framework. D is for true junk only.

Respond with EXACTLY this JSON, nothing else:
{"tier": "B", "reason": "one sentence explaining the rating", "tags": ["consciousness", "quantum"], "word_count_estimate": 1500}"""

TRIAGE_USER = """Rate this paper:

FILENAME: {filename}
PATH: {filepath}

CONTENT (may be truncated):
{content}"""

DEEP_SYSTEM = """You are performing deep analysis of an A-tier Theophysics paper using a rubric derived from the TSR-100 (Truth Satisfaction Rating).

FRAMEWORK CONTEXT:
- Master Equation: χ = ∭(G·M·E·S·T·K·R·Q·F·C)dxdydt
- Lowe Coherence Lagrangian: LLC = χ(t)(d/dt(G+M+E+S+T+K+R+Q+F+C))² - S·χ(t)
- Ten Universal Laws with symmetry pairs (1↔8, 2↔9, 3↔10, 4↔7, 5↔6)
- Core: consciousness = fundamental, physics∧theology = dual projections, Logos field mediates
- TSR-100 boundary conditions: Necessary, Eternal, Universal, Immaterial, Coherent, Self-Grounding, Non-Deceptive, Personal
- TSR-100 core axioms (L1-L3): Information-theoretic grounding → thermodynamic necessity → theological derivation
- TSR-100 moral axioms (A11-A20): Cruciformity, moral universality, entropy-redemption mapping, sacrificial inversion
- Experimental: PEAR-LAB (6.35σ, 2.5M trials), GCP (6σ, 325+ replicas), PROP-COSMOS (5.7σ, 11/11)

RATING RUBRIC (100 points total):

[30 pts] FRAMEWORK CONTRIBUTION
  Does this paper advance specific boundary conditions or axioms from the TSR-100?
  Does it derive theological commitment from formal reasoning (not retrofit)?
  Does it function as a "blind key" fitting the framework lock?
  30 = Major advancement of multiple axioms/conditions
  20 = Solid advancement of one area
  10 = Tangential contribution
  0  = Does not advance the framework

[25 pts] DEDUCTIVE RIGOR
  Is the argument chain math→truth, not apologetics→proof-text?
  Are falsification criteria stated or implied?
  Is there formal structure (definitions, propositions, derivations)?
  25 = Publication-grade rigor with falsification criteria
  15 = Clear logical chain, minor gaps
  8  = Informal but traceable reasoning
  0  = No discernible logical structure

[20 pts] COHERENCE INTEGRATION
  Does it connect to Master Equation / Ten Laws without contradiction?
  Does it reference or build on other framework papers?
  Does it maintain consistency with established axioms?
  20 = Deep integration, extends existing framework
  12 = References framework, no contradictions
  6  = Loosely connected
  0  = Contradicts or ignores framework

[15 pts] COMPLETENESS
  Is this a full argument or a fragment?
  Could it stand alone as a publishable piece?
  Does it have abstract, argument, implications, and conclusions?
  15 = Publication-ready or near-ready
  10 = Complete argument, needs polish
  5  = Partial argument, key sections missing
  0  = Fragment or outline only

[10 pts] ORIGINALITY
  Does this say something new within the framework?
  Does it bridge domains that haven't been connected before?
  Or does it restate what's already established?
  10 = Novel insight or unprecedented connection
  6  = New angle on known territory
  3  = Competent restatement
  0  = Pure repetition

Respond with EXACTLY this JSON, nothing else:
{
  "total_score": 78,
  "framework_contribution": 22,
  "deductive_rigor": 18,
  "coherence_integration": 16,
  "completeness": 12,
  "originality": 10,
  "summary": "Two sentences: what this paper does and what makes it notable or lacking.",
  "strongest": "One sentence: the best thing about this paper.",
  "weakest": "One sentence: the biggest gap or weakness.",
  "tags": ["consciousness", "quantum-theology", "master-equation"],
  "connects_to": ["other paper names or topics this builds on"],
  "publication_ready": false
}"""

DEEP_USER = """Rate this A-tier paper in detail:

FILENAME: {filename}
PATH: {filepath}

FULL CONTENT:
{content}"""


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


def get_meta_dir(vault_path: Path) -> Path:
    """Return (and create) the metadata directory inside the vault."""
    d = vault_path / META_DIR
    d.mkdir(exist_ok=True)
    return d


def load_state(vault_path: Path) -> dict:
    """Load rating state (which files have been rated)."""
    state_path = get_meta_dir(vault_path) / STATE_FILE
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"rated": {}, "version": 1, "started": datetime.now().isoformat()}


def save_state(vault_path: Path, state: dict):
    """Persist rating state."""
    state_path = get_meta_dir(vault_path) / STATE_FILE
    state["last_updated"] = datetime.now().isoformat()
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    """Quick hash for change detection (first 4KB + size)."""
    try:
        data = path.read_bytes()[:4096]
        return hashlib.md5(data + str(path.stat().st_size).encode()).hexdigest()[:12]
    except Exception:
        return "unknown"


def count_words(text: str) -> int:
    """Rough word count."""
    return len(text.split())


def extract_frontmatter(text: str) -> Tuple[Optional[dict], str]:
    """Extract YAML frontmatter from markdown. Returns (yaml_dict, body)."""
    import re
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        body = text[match.end():]
        # Simple YAML parser (avoids PyYAML dependency)
        fm = {}
        current_key = None
        current_list = None
        for line in yaml_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # List item
            if stripped.startswith("- ") and current_key:
                if current_list is None:
                    current_list = []
                current_list.append(stripped[2:].strip().strip('"').strip("'"))
                fm[current_key] = current_list
                continue
            # Key: value
            if ":" in stripped:
                if current_list is not None:
                    current_list = None
                k, _, v = stripped.partition(":")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                current_key = k
                if v:
                    # Try numeric
                    try:
                        if "." in v:
                            fm[k] = float(v)
                        else:
                            fm[k] = int(v)
                    except ValueError:
                        if v.lower() in ("true", "yes"):
                            fm[k] = True
                        elif v.lower() in ("false", "no"):
                            fm[k] = False
                        else:
                            fm[k] = v
                    current_list = None
                else:
                    fm[k] = None
                    current_list = []  # Might be a list
        return fm, body
    return None, text


def build_frontmatter(data: dict) -> str:
    """Build YAML frontmatter string from dict."""
    lines = ["---"]
    for k, v in data.items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - \"{item}\"")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, str) and any(c in v for c in ":#{}[]|>&*!%@`,"):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def update_file_frontmatter(file_path: Path, rating_data: dict, tier: str):
    """Update or insert YAML frontmatter with rating data."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    existing_fm, body = extract_frontmatter(text)

    if existing_fm is None:
        existing_fm = {}

    # Add rating fields (prefixed to avoid collisions)
    existing_fm["vault_tier"] = tier
    existing_fm["vault_rated"] = datetime.now().strftime("%Y-%m-%d")

    if "total_score" in rating_data:
        existing_fm["tsr_score"] = rating_data["total_score"]
        existing_fm["tsr_framework"] = rating_data.get("framework_contribution", 0)
        existing_fm["tsr_rigor"] = rating_data.get("deductive_rigor", 0)
        existing_fm["tsr_coherence"] = rating_data.get("coherence_integration", 0)
        existing_fm["tsr_completeness"] = rating_data.get("completeness", 0)
        existing_fm["tsr_originality"] = rating_data.get("originality", 0)
        existing_fm["tsr_pub_ready"] = rating_data.get("publication_ready", False)

    if "reason" in rating_data:
        existing_fm["vault_reason"] = rating_data["reason"]
    if "summary" in rating_data:
        existing_fm["vault_summary"] = rating_data["summary"]
    if "strongest" in rating_data:
        existing_fm["vault_strongest"] = rating_data["strongest"]
    if "weakest" in rating_data:
        existing_fm["vault_weakest"] = rating_data["weakest"]

    if "tags" in rating_data and rating_data["tags"]:
        # Merge with existing tags
        old_tags = existing_fm.get("tags", [])
        if isinstance(old_tags, str):
            old_tags = [old_tags]
        new_tags = list(set(old_tags + rating_data["tags"]))
        existing_fm["tags"] = new_tags

    new_text = build_frontmatter(existing_fm) + body
    file_path.write_text(new_text, encoding="utf-8")


def call_openai(client: OpenAI, model: str, system: str, user: str,
                max_retries: int = MAX_RETRIES) -> Optional[dict]:
    """Call OpenAI and parse JSON response. Returns None on failure."""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=1 if model.startswith("gpt-5") or model.startswith("o") else 0.3,  # Reasoning models require temp=1
                max_tokens=500 if model == MODEL_TRIAGE else 800,
            )
            text = response.choices[0].message.content.strip()

            # Extract JSON from response (handle markdown code blocks)
            if text.startswith("```"):
                text = re.sub(r'^```(?:json)?\s*', '', text)
                text = re.sub(r'\s*```$', '', text)

            result = json.loads(text)

            # Track tokens for cost reporting
            usage = response.usage
            result["_input_tokens"] = usage.prompt_tokens if usage else 0
            result["_output_tokens"] = usage.completion_tokens if usage else 0

            return result

        except json.JSONDecodeError as e:
            print(f"    ⚠ JSON parse error (attempt {attempt+1}): {e}")
            print(f"    Raw: {text[:200]}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except RateLimitError:
            wait = RETRY_DELAY * (attempt + 1) * 2
            print(f"    ⚠ Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except APIError as e:
            print(f"    ⚠ API error: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
        except AuthenticationError:
            print("    ✖ Invalid API key!")
            return None

    return None


# ─────────────────────────────────────────────
# VAULT SCANNER
# ─────────────────────────────────────────────

def scan_vault(vault_path: Path, min_words: int = 50) -> List[Path]:
    """Find all ratable .md files in the vault."""
    files = []
    for md in sorted(vault_path.rglob("*.md")):
        # Skip excluded folders
        parts = set(md.relative_to(vault_path).parts)
        if parts & SKIP_FOLDERS:
            continue
        # Skip excluded files
        if md.name in SKIP_FILES:
            continue
        # Skip very small files
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
            _, body = extract_frontmatter(text)
            if count_words(body) < min_words:
                continue
        except Exception:
            continue
        files.append(md)
    return files


# ─────────────────────────────────────────────
# PASS 1: TRIAGE
# ─────────────────────────────────────────────

def run_triage(client: OpenAI, vault_path: Path, files: List[Path],
               state: dict, limit: Optional[int] = None) -> dict:
    """Pass 1: Quick triage of all files into A/B/C/D."""
    print(f"\n{'='*60}")
    print(f"  PASS 1 — TRIAGE ({MODEL_TRIAGE})")
    print(f"  Files to process: {len(files)}")
    print(f"{'='*60}\n")

    total_input_tokens = 0
    total_output_tokens = 0
    processed = 0
    tier_counts = Counter()

    for i, md in enumerate(files):
        if limit and processed >= limit:
            print(f"\n  ⏹ Limit reached ({limit} files)")
            break

        rel = md.relative_to(vault_path)
        file_key = str(rel)

        # Skip if already rated in this pass
        if file_key in state["rated"] and "tier" in state["rated"][file_key]:
            tier_counts[state["rated"][file_key]["tier"]] += 1
            continue

        # Read and truncate
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
            _, body = extract_frontmatter(text)
            content = body[:MAX_CHARS_PASS1]
        except Exception as e:
            print(f"  [{i+1}] ✖ Read error: {rel} — {e}")
            continue

        # Call API
        user_msg = TRIAGE_USER.format(
            filename=md.name,
            filepath=str(rel),
            content=content,
        )

        result = call_openai(client, MODEL_TRIAGE, TRIAGE_SYSTEM, user_msg)

        if result is None:
            print(f"  [{i+1}] ✖ API failed: {rel}")
            continue

        tier = result.get("tier", "C").upper()
        if tier not in "ABCD":
            tier = "C"
        reason = result.get("reason", "No reason given")
        tags = result.get("tags", [])

        total_input_tokens += result.get("_input_tokens", 0)
        total_output_tokens += result.get("_output_tokens", 0)

        # Store in state
        state["rated"][file_key] = {
            "tier": tier,
            "reason": reason,
            "tags": tags,
            "hash": file_hash(md),
            "triage_date": datetime.now().isoformat(),
        }

        tier_counts[tier] += 1
        processed += 1

        icon = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}[tier]
        print(f"  [{i+1}] {icon} {tier} — {rel}")
        print(f"         {reason[:80]}")

        # Save state every 25 files (resume safety)
        if processed % 25 == 0:
            save_state(vault_path, state)
            print(f"  💾 State saved ({processed} files)")

        time.sleep(BATCH_DELAY)

    # Final save
    save_state(vault_path, state)

    # Cost report
    in_cost = (total_input_tokens / 1000) * PRICING[MODEL_TRIAGE][0]
    out_cost = (total_output_tokens / 1000) * PRICING[MODEL_TRIAGE][1]

    print(f"\n{'='*60}")
    print(f"  PASS 1 COMPLETE")
    print(f"  Processed: {processed} files")
    print(f"  A: {tier_counts['A']}  B: {tier_counts['B']}  "
          f"C: {tier_counts['C']}  D: {tier_counts['D']}")
    print(f"  Tokens: ~{total_input_tokens:,} in / ~{total_output_tokens:,} out")
    print(f"  Est. cost: ${in_cost + out_cost:.4f}")
    print(f"{'='*60}\n")

    return state


# ─────────────────────────────────────────────
# PASS 2: DEEP RATING (A-TIER ONLY)
# ─────────────────────────────────────────────

def run_deep_rating(client: OpenAI, vault_path: Path, state: dict,
                    limit: Optional[int] = None) -> dict:
    """Pass 2: Deep 100-point rating of A-tier papers only."""

    # Collect A-tier files
    a_tier = [(k, v) for k, v in state["rated"].items()
              if v.get("tier") == "A" and "total_score" not in v]

    if not a_tier:
        print("\n  No unrated A-tier papers to deep-rate.")
        return state

    print(f"\n{'='*60}")
    print(f"  PASS 2 — DEEP RATING ({MODEL_DEEP})")
    print(f"  A-tier papers to rate: {len(a_tier)}")
    print(f"{'='*60}\n")

    total_input_tokens = 0
    total_output_tokens = 0
    processed = 0

    for file_key, info in a_tier:
        if limit and processed >= limit:
            print(f"\n  ⏹ Limit reached ({limit} files)")
            break

        md = vault_path / file_key
        if not md.exists():
            print(f"  ✖ File not found: {file_key}")
            continue

        # Read full content (up to limit)
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
            _, body = extract_frontmatter(text)
            content = body[:MAX_CHARS_PASS2]
        except Exception as e:
            print(f"  ✖ Read error: {file_key} — {e}")
            continue

        user_msg = DEEP_USER.format(
            filename=md.name,
            filepath=file_key,
            content=content,
        )

        result = call_openai(client, MODEL_DEEP, DEEP_SYSTEM, user_msg)

        if result is None:
            print(f"  ✖ API failed: {file_key}")
            continue

        total_input_tokens += result.get("_input_tokens", 0)
        total_output_tokens += result.get("_output_tokens", 0)

        # Merge deep rating into state
        for key in ["total_score", "framework_contribution", "deductive_rigor",
                     "coherence_integration", "completeness", "originality",
                     "summary", "strongest", "weakest", "connects_to",
                     "publication_ready"]:
            if key in result:
                state["rated"][file_key][key] = result[key]

        if "tags" in result:
            old = set(state["rated"][file_key].get("tags", []))
            state["rated"][file_key]["tags"] = list(old | set(result["tags"]))

        state["rated"][file_key]["deep_date"] = datetime.now().isoformat()

        score = result.get("total_score", "?")
        print(f"  🟢 {score}/100 — {file_key}")
        print(f"       {result.get('summary', '')[:100]}")

        processed += 1
        if processed % 10 == 0:
            save_state(vault_path, state)
            print(f"  💾 State saved ({processed} papers)")

        time.sleep(BATCH_DELAY)

    save_state(vault_path, state)

    in_cost = (total_input_tokens / 1000) * PRICING[MODEL_DEEP][0]
    out_cost = (total_output_tokens / 1000) * PRICING[MODEL_DEEP][1]

    print(f"\n{'='*60}")
    print(f"  PASS 2 COMPLETE")
    print(f"  Deep-rated: {processed} papers")
    print(f"  Tokens: ~{total_input_tokens:,} in / ~{total_output_tokens:,} out")
    print(f"  Est. cost: ${in_cost + out_cost:.4f}")
    print(f"{'='*60}\n")

    return state


# ─────────────────────────────────────────────
# POST-PROCESSING: FRONTMATTER + MOVES + CSV
# ─────────────────────────────────────────────

def update_frontmatter_all(vault_path: Path, state: dict):
    """Write rating data into YAML frontmatter of all rated files."""
    print("\n  📝 Updating YAML frontmatter...")
    updated = 0
    for file_key, info in state["rated"].items():
        md = vault_path / file_key
        if not md.exists():
            continue
        try:
            update_file_frontmatter(md, info, info.get("tier", "?"))
            updated += 1
        except Exception as e:
            print(f"    ⚠ Failed: {file_key} — {e}")
    print(f"  ✅ Updated {updated} files")


def move_to_tiers(vault_path: Path, state: dict) -> dict:
    """Move files into tier subfolders. Returns move log for restore."""
    print("\n  📁 Moving files to tier folders...")
    move_log = {}

    for tier_letter, folder_name in TIER_FOLDERS.items():
        (vault_path / folder_name).mkdir(exist_ok=True)

    moved = 0
    for file_key, info in state["rated"].items():
        tier = info.get("tier", "")
        if tier not in TIER_FOLDERS:
            continue

        src = vault_path / file_key
        if not src.exists():
            continue

        # Build destination preserving subdirectory structure
        dest_dir = vault_path / TIER_FOLDERS[tier] / src.parent.relative_to(vault_path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name

        if dest.exists():
            # Don't overwrite — skip
            continue

        try:
            shutil.move(str(src), str(dest))
            move_log[file_key] = str(dest.relative_to(vault_path))
            moved += 1
        except Exception as e:
            print(f"    ⚠ Move failed: {file_key} — {e}")

    # Save move log for restore
    log_path = get_meta_dir(vault_path) / BACKUP_LOG
    log_path.write_text(json.dumps(move_log, indent=2), encoding="utf-8")

    print(f"  ✅ Moved {moved} files")
    return move_log


def restore_moves(vault_path: Path):
    """Undo all tier moves using the backup log."""
    log_path = get_meta_dir(vault_path) / BACKUP_LOG
    if not log_path.exists():
        print("  No move log found. Nothing to restore.")
        return

    move_log = json.loads(log_path.read_text(encoding="utf-8"))
    restored = 0

    for original_key, moved_key in move_log.items():
        src = vault_path / moved_key
        dest = vault_path / original_key

        if not src.exists():
            continue

        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dest))
            restored += 1
        except Exception as e:
            print(f"    ⚠ Restore failed: {moved_key} → {original_key} — {e}")

    print(f"  ✅ Restored {restored} files to original locations")

    # Clean up empty tier folders
    for folder_name in TIER_FOLDERS.values():
        tier_dir = vault_path / folder_name
        if tier_dir.exists():
            try:
                # Remove empty subdirectories
                for d in sorted(tier_dir.rglob("*"), reverse=True):
                    if d.is_dir() and not any(d.iterdir()):
                        d.rmdir()
                if not any(tier_dir.iterdir()):
                    tier_dir.rmdir()
            except Exception:
                pass


def export_csv(vault_path: Path, state: dict):
    """Export all ratings to CSV."""
    csv_path = get_meta_dir(vault_path) / CSV_OUTPUT
    rows = []
    for file_key, info in sorted(state["rated"].items()):
        row = {
            "file": file_key,
            "tier": info.get("tier", ""),
            "score": info.get("total_score", ""),
            "framework": info.get("framework_contribution", ""),
            "rigor": info.get("deductive_rigor", ""),
            "coherence": info.get("coherence_integration", ""),
            "completeness": info.get("completeness", ""),
            "originality": info.get("originality", ""),
            "pub_ready": info.get("publication_ready", ""),
            "reason": info.get("reason", ""),
            "summary": info.get("summary", ""),
            "strongest": info.get("strongest", ""),
            "weakest": info.get("weakest", ""),
            "tags": "|".join(info.get("tags", [])),
        }
        rows.append(row)

    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"  📊 CSV exported: {csv_path} ({len(rows)} rows)")


def show_stats(vault_path: Path):
    """Display current rating statistics."""
    state = load_state(vault_path)
    rated = state.get("rated", {})

    if not rated:
        print("  No ratings found yet.")
        return

    tiers = Counter(v.get("tier", "?") for v in rated.values())
    scored = [v for v in rated.values() if "total_score" in v]

    print(f"\n{'='*60}")
    print(f"  VAULT RATING STATISTICS")
    print(f"{'='*60}")
    print(f"  Total rated:  {len(rated)}")
    print(f"  A-tier: {tiers.get('A', 0)}  B: {tiers.get('B', 0)}  "
          f"C: {tiers.get('C', 0)}  D: {tiers.get('D', 0)}")

    if scored:
        scores = [v["total_score"] for v in scored]
        print(f"\n  Deep-rated (A-tier): {len(scored)}")
        print(f"  Score range: {min(scores)} — {max(scores)}")
        print(f"  Average:     {sum(scores)/len(scores):.1f}")

        # Top 10
        top = sorted(scored, key=lambda v: v.get("total_score", 0), reverse=True)[:10]
        print(f"\n  TOP 10:")
        for v in top:
            key = [k for k, val in rated.items() if val is v][0]
            print(f"    {v['total_score']:3d}/100  {key}")

    print(f"{'='*60}\n")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Theophysics Vault Rater — TSR-100 Derived Rating System"
    )
    parser.add_argument("--vault", default=DEFAULT_VAULT,
                        help=f"Path to vault (default: {DEFAULT_VAULT})")
    parser.add_argument("--pass", dest="run_pass", choices=["1", "2", "both"],
                        default="both", help="Which pass to run (default: both)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max files to process (for testing)")
    parser.add_argument("--min-words", type=int, default=50,
                        help="Skip files under N words (default: 50)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would happen, no API calls or changes")
    parser.add_argument("--skip-move", action="store_true",
                        help="Rate files but don't move them to tier folders")
    parser.add_argument("--skip-frontmatter", action="store_true",
                        help="Rate files but don't update YAML frontmatter")
    parser.add_argument("--restore", action="store_true",
                        help="Undo all tier folder moves")
    parser.add_argument("--stats", action="store_true",
                        help="Show current rating statistics")
    parser.add_argument("--reset", action="store_true",
                        help="Clear all rating state (requires --confirm)")
    parser.add_argument("--confirm", action="store_true",
                        help="Confirm destructive operations")
    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        sys.exit(f"ERROR: Vault not found: {vault_path}")

    # --- Stats mode ---
    if args.stats:
        show_stats(vault_path)
        return

    # --- Restore mode ---
    if args.restore:
        print(f"\n  Restoring files in: {vault_path}")
        restore_moves(vault_path)
        return

    # --- Reset mode ---
    if args.reset:
        if not args.confirm:
            print("  ⚠ Reset requires --confirm flag. This deletes all rating state.")
            return
        state_path = get_meta_dir(vault_path) / STATE_FILE
        if state_path.exists():
            state_path.unlink()
            print("  ✅ Rating state cleared.")
        return

    # --- Config ---
    cfg = parse_config(CONFIG_PATH)
    api_key = cfg.get("OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", ""))

    if not api_key or api_key.startswith("sk-PASTE"):
        if not args.dry_run:
            sys.exit(
                "ERROR: No valid API key.\n"
                "Either set OPENAI_API_KEY= in config.txt or set the env variable."
            )

    # --- Scan vault ---
    print(f"\n  Scanning vault: {vault_path}")
    files = scan_vault(vault_path, min_words=args.min_words)
    print(f"  Found {len(files)} ratable .md files\n")

    if not files:
        print("  Nothing to rate.")
        return

    # --- Dry run ---
    if args.dry_run:
        state = load_state(vault_path)
        already = len(state.get("rated", {}))
        to_rate = len(files) - already

        # Cost estimate
        est_p1_tokens = to_rate * 2500  # ~2K input + ~500 output per file
        est_p1_cost = (est_p1_tokens / 1000) * sum(PRICING[MODEL_TRIAGE])

        est_a_count = max(1, int(to_rate * 0.15))  # Estimate 15% A-tier
        est_p2_tokens = est_a_count * 7000
        est_p2_cost = (est_p2_tokens / 1000) * sum(PRICING[MODEL_DEEP])

        print(f"  {'='*50}")
        print(f"  DRY RUN — Cost Estimate")
        print(f"  {'='*50}")
        print(f"  Total .md files:   {len(files)}")
        print(f"  Already rated:     {already}")
        print(f"  To rate (Pass 1):  {to_rate}")
        print(f"  Est. A-tier (~15%): {est_a_count}")
        print(f"")
        print(f"  Pass 1 ({MODEL_TRIAGE}):")
        print(f"    ~{est_p1_tokens:,} tokens → ${est_p1_cost:.4f}")
        print(f"  Pass 2 ({MODEL_DEEP}):")
        print(f"    ~{est_p2_tokens:,} tokens → ${est_p2_cost:.4f}")
        print(f"  TOTAL: ${est_p1_cost + est_p2_cost:.4f}")
        print(f"  {'='*50}")

        # Show sample files
        print(f"\n  Sample files to rate:")
        for f in files[:10]:
            print(f"    {f.relative_to(vault_path)}")
        if len(files) > 10:
            print(f"    ... and {len(files)-10} more")
        return

    # --- Run ---
    client = OpenAI(api_key=api_key)
    state = load_state(vault_path)

    if args.run_pass in ("1", "both"):
        state = run_triage(client, vault_path, files, state, limit=args.limit)

    if args.run_pass in ("2", "both"):
        state = run_deep_rating(client, vault_path, state, limit=args.limit)

    # --- Post-processing ---
    if not args.skip_frontmatter:
        update_frontmatter_all(vault_path, state)

    if not args.skip_move:
        move_to_tiers(vault_path, state)

    export_csv(vault_path, state)

    # --- Final stats ---
    show_stats(vault_path)

    print("  Done! Your vault is organized. 🎯\n")
    print("  Dataview queries you can use:")
    print('    TABLE vault_tier, tsr_score, tsr_rigor, vault_reason')
    print('    FROM ""')
    print('    WHERE vault_tier')
    print('    SORT tsr_score DESC')


if __name__ == "__main__":
    main()
