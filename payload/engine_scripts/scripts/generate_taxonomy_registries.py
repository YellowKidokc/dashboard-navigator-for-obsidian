#!/usr/bin/env python3
"""
Generate taxonomy registries used by YAML + Excel integration.

Outputs:
  - TAG_REGISTRY_MASTER.csv
  - TARGET_WORDS_HIERARCHY.csv
  - CLASSIFICATION_LEVELS.csv

Default behavior reads existing vault notes and writes into:
  O:/_Theophysics_v3/00_SYSTEM/00System/03_Taxonomy_Naming
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


DEFAULT_VAULT_ROOT = Path(r"O:\_Theophysics_v3")
DEFAULT_OUTPUT_DIR = DEFAULT_VAULT_ROOT / "00_SYSTEM" / "00System" / "03_Taxonomy_Naming"
DEFAULT_TAG_TAXONOMY = DEFAULT_VAULT_ROOT / "99_TAG_NOTES" / "_TAG_TAXONOMY.md"
DEFAULT_TERM_INDEX = DEFAULT_VAULT_ROOT / "99_TAG_NOTES" / "00_TERM_INDEX.md"

NAMESPACE_UUID = uuid.UUID("31a4e5ea-e19a-4dfd-a642-6f299fc0046d")


def stable_uuid(kind: str, value: str) -> str:
    return str(uuid.uuid5(NAMESPACE_UUID, f"{kind}:{value.strip().lower()}"))


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s/]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate taxonomy registry CSV files")
    parser.add_argument("--vault-root", default=str(DEFAULT_VAULT_ROOT), help="Vault root path")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory")
    parser.add_argument("--tag-taxonomy", default=str(DEFAULT_TAG_TAXONOMY), help="_TAG_TAXONOMY.md path")
    parser.add_argument("--term-index", default=str(DEFAULT_TERM_INDEX), help="00_TERM_INDEX.md path")
    return parser.parse_args()


def parse_tags_from_taxonomy(path: Path) -> List[Tuple[str, str]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")

    tags: Dict[str, str] = {}

    # Matches markdown inline code style: `#axis/value`
    for match in re.findall(r"`#([a-z0-9_-]+/[a-z0-9_-]+)`", text, flags=re.IGNORECASE):
        tags[match.lower()] = "taxonomy_note"

    # Matches yaml list style in examples: - axis/value
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"^-\s+([a-z0-9_-]+/[a-z0-9_-]+)\s*$", line, flags=re.IGNORECASE)
        if m:
            tags[m.group(1).lower()] = "taxonomy_note"

    # Additional tags to support claim/evidence and quality workflows.
    seed_tags = [
        "claim/axiom",
        "claim/definition",
        "claim/lemma",
        "claim/hypothesis",
        "claim/operationalization",
        "claim/dataset_fact",
        "claim/evidence_extract",
        "claim/result",
        "claim/interpretation",
        "quality/publish_ready",
        "quality/refine",
        "quality/triage",
        "quality/archive",
        "project/core",
        "project/support",
        "project/reference",
        "system/metadata",
        "system/workflow",
        "system/verification",
        "system/falsification",
    ]
    for tag in seed_tags:
        tags[tag] = "generated_seed"

    return sorted((tag, source) for tag, source in tags.items())


def usage_rule_for_axis(axis: str) -> str:
    rules = {
        "epistemic": "exactly_one_required",
        "function": "one_or_two",
        "domain": "one_or_more_optional",
        "path": "zero_or_one_optional",
    }
    return rules.get(axis, "zero_or_more")


def build_tag_rows(entries: Sequence[Tuple[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for tag, source in entries:
        axis, value = tag.split("/", 1)
        code = f"{axis[:3].upper()}-{slugify(value)[:6].upper()}"
        rows.append(
            {
                "tag_uuid": stable_uuid("tag", tag),
                "tag": tag,
                "axis": axis,
                "tag_value": value,
                "tag_code": code,
                "usage_rule": usage_rule_for_axis(axis),
                "description": f"{axis} tag: {value}",
                "status": "active",
                "source": source,
                "updated_on": dt.date.today().isoformat(),
            }
        )
    return rows


def parse_markdown_table_row(line: str) -> List[str]:
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    return parts


def parse_term_index(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    section = ""
    out: List[Dict[str, str]] = []

    for line in lines:
        if line.startswith("## Terms with Definitions"):
            section = "defined"
            continue
        if line.startswith("## Terms Needing Definitions"):
            section = "needs_definition"
            continue
        if not section:
            continue
        if not line.strip().startswith("|"):
            continue
        if re.search(r"\|\s*-+\s*\|", line):
            continue
        parts = parse_markdown_table_row(line)

        if section == "defined" and len(parts) >= 4:
            term = parts[0]
            aliases = parts[1]
            uses = parts[2]
            definition = parts[3]
            if term.lower() == "term":
                continue
            out.append(
                {
                    "term": term,
                    "aliases": aliases,
                    "uses_count": uses,
                    "definition_note": definition,
                    "source_section": section,
                    "status": "defined",
                }
            )
        elif section == "needs_definition" and len(parts) >= 3:
            term = parts[0]
            uses = parts[1]
            source = parts[2]
            if term.lower() == "term":
                continue
            out.append(
                {
                    "term": term,
                    "aliases": "",
                    "uses_count": uses,
                    "definition_note": "",
                    "source_section": source or section,
                    "status": "needs_definition",
                }
            )
    return out


def classify_domain(term: str) -> str:
    t = term.lower()
    theology = ("god", "logos", "scripture", "grace", "trinity", "jesus", "holy", "faith", "salvation")
    physics = ("quantum", "gravity", "entropy", "thermo", "lagrang", "relativity", "cosmo", "equation", "nuclear")
    consciousness = ("mind", "conscious", "observer", "soul", "cognition")
    methods = ("falsif", "evidence", "model", "dataset", "workflow", "classification", "tag", "metadata")

    if any(k in t for k in theology):
        return "theology"
    if any(k in t for k in physics):
        return "physics"
    if any(k in t for k in consciousness):
        return "consciousness"
    if any(k in t for k in methods):
        return "method"
    return "general"


def classify_bucket(term: str) -> str:
    t = term.lower()
    if any(k in t for k in ("entropy", "coherence", "negentropy")):
        return "coherence_dynamics"
    if any(k in t for k in ("quantum", "wave", "collapse", "superposition")):
        return "quantum_constructs"
    if any(k in t for k in ("logos", "trinity", "scripture", "faith", "grace", "holy")):
        return "theological_constructs"
    if any(k in t for k in ("axiom", "lemma", "hypothesis", "falsification", "evidence")):
        return "claim_and_evidence"
    if any(k in t for k in ("tag", "classification", "metadata", "workflow", "project")):
        return "system_controls"
    return "general_terms"


def build_target_word_rows(terms: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    dedup: Dict[str, Dict[str, str]] = {}
    for row in terms:
        normalized = slugify(row["term"])
        if not normalized:
            continue
        existing = dedup.get(normalized)
        if existing is None:
            dedup[normalized] = row
            continue
        # Prefer entries that have a definition and higher use count.
        existing_defined = existing.get("status") == "defined"
        row_defined = row.get("status") == "defined"
        if row_defined and not existing_defined:
            dedup[normalized] = row
            continue
        try:
            existing_uses = int(float(existing.get("uses_count", "0")))
        except ValueError:
            existing_uses = 0
        try:
            row_uses = int(float(row.get("uses_count", "0")))
        except ValueError:
            row_uses = 0
        if row_uses > existing_uses:
            dedup[normalized] = row

    grouped_counter: Dict[Tuple[str, str], int] = defaultdict(int)
    rows: List[Dict[str, str]] = []

    for normalized, item in sorted(dedup.items()):
        term = item["term"].strip()
        domain = classify_domain(term)
        bucket = classify_bucket(term)
        grouped_counter[(domain, bucket)] += 1
        idx = grouped_counter[(domain, bucket)]
        target_key = f"{domain.upper()}|{bucket.upper()}|{normalized.upper()}|{idx:04d}"
        rows.append(
            {
                "target_word_uuid": stable_uuid("target_word", normalized),
                "target_word_key": target_key,
                "term": term,
                "normalized_term": normalized,
                "domain": domain,
                "concept_bucket": bucket,
                "term_precision": "working" if item.get("status") == "needs_definition" else "defined",
                "status": item.get("status", "defined"),
                "uses_count": item.get("uses_count", "0"),
                "aliases": item.get("aliases", ""),
                "definition_note": item.get("definition_note", ""),
                "source_section": item.get("source_section", ""),
                "updated_on": dt.date.today().isoformat(),
            }
        )
    return rows


def classification_seed() -> Dict[str, List[Tuple[str, str]]]:
    return {
        "type": [
            ("paper", "Long-form argument or manuscript"),
            ("model", "Formal model or equation-driven note"),
            ("concept", "Conceptual note"),
            ("definition", "Definition note"),
            ("note", "General working note"),
            ("dataset", "Dataset or data-source note"),
            ("evidence_extract", "Extract tied to a source"),
            ("result", "Results from an analysis"),
            ("interpretation", "Interpretive synthesis"),
        ],
        "layer": [
            ("ai", "AI collaboration layer"),
            ("system", "Knowledge architecture layer"),
            ("os", "Operating workflow layer"),
            ("project", "Project execution layer"),
            ("meta", "Meta-governance layer"),
        ],
        "status": [
            ("draft", "Early draft"),
            ("review", "In active review"),
            ("approved", "Approved baseline"),
            ("validated", "Validated against checks"),
            ("published", "Externally published"),
            ("deprecated", "Kept only for historical trace"),
            ("canonical", "Legacy label; prefer approved"),
        ],
        "maturity": [
            ("seed", "Initial idea"),
            ("developing", "Expanding and being tested"),
            ("stable", "Reliable and internally coherent"),
            ("mature", "Production quality"),
            ("legacy", "Historical reference"),
        ],
        "claim_role": [
            ("axiom", "Foundational claim"),
            ("definition", "Definition with boundaries"),
            ("lemma", "Intermediate proposition"),
            ("hypothesis", "Testable claim"),
            ("operationalization", "How a variable is measured"),
            ("dataset_fact", "Fact directly from dataset"),
            ("evidence_extract", "Verbatim extract from source"),
            ("result", "Computed or observed outcome"),
            ("interpretation", "Interpretation of results"),
            ("prediction", "Forward-looking claim"),
            ("observation", "Observed pattern"),
        ],
        "claim_strength": [
            ("proven", "Strongly established"),
            ("strong", "Strong support"),
            ("moderate", "Moderate support"),
            ("weak", "Weak support"),
            ("speculative", "Early exploration"),
        ],
        "project_role": [
            ("core", "Core dependency"),
            ("support", "Support material"),
            ("reference", "Background reference"),
        ],
        "project_stage": [
            ("planning", "Planning stage"),
            ("drafting", "Drafting stage"),
            ("review", "Review stage"),
            ("complete", "Completed stage"),
        ],
        "project_priority": [
            ("critical", "Critical priority"),
            ("high", "High priority"),
            ("medium", "Medium priority"),
            ("low", "Low priority"),
        ],
        "tqd_band": [
            ("publication_ready", "90-100"),
            ("strong", "75-89"),
            ("solid_gaps", "60-74"),
            ("salvageable", "40-59"),
            ("fundamental_problems", "<40"),
        ],
        "sqi_alert": [
            ("green", "Healthy"),
            ("yellow", "Needs attention"),
            ("red", "Critical issues"),
        ],
        "cds_zone": [
            ("publish", "Ready for publication workflow"),
            ("refine", "Refine and recheck"),
            ("triage", "Needs focused remediation"),
            ("archive", "Archive or retire"),
        ],
        "sensitivity_verdict": [
            ("load_bearing", "Critical structural element"),
            ("supporting", "Support element"),
            ("optional", "Optional element"),
        ],
        "sensitivity_topology": [
            ("hub", "High centrality"),
            ("bridge", "Connects clusters"),
            ("leaf", "Edge node"),
        ],
        "sensitivity_adversarial": [
            ("critical", "High adversarial sensitivity"),
            ("strong", "Strong adversarial sensitivity"),
            ("moderate", "Moderate adversarial sensitivity"),
            ("weak", "Low adversarial sensitivity"),
        ],
        "constraint_logic_chain": [
            ("strong", "Strong logical chain"),
            ("moderate", "Moderate logical chain"),
            ("weak", "Weak logical chain"),
        ],
        "term_precision": [
            ("approved", "Approved and stable definition"),
            ("working", "Working definition"),
            ("informal", "Informal shorthand"),
        ],
        "ckg_tier_classification": [
            ("T1", "Tier 1"),
            ("T2", "Tier 2"),
            ("T3", "Tier 3"),
            ("T4", "Tier 4"),
            ("T5", "Tier 5"),
        ],
        "tsr_tier": [
            ("excellent", "Excellent"),
            ("strong", "Strong"),
            ("good", "Good"),
            ("developing", "Developing"),
        ],
    }


def build_classification_rows(seed: Dict[str, List[Tuple[str, str]]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for group in sorted(seed.keys()):
        for index, (value, description) in enumerate(seed[group], start=1):
            rows.append(
                {
                    "classification_uuid": stable_uuid("classification", f"{group}:{value}"),
                    "classification_group": group,
                    "classification_value": value,
                    "sort_order": str(index),
                    "is_default": "false",
                    "is_active": "true",
                    "description": description,
                    "updated_on": dt.date.today().isoformat(),
                }
            )
    return rows


def write_csv(path: Path, rows: Sequence[Dict[str, str]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    tag_taxonomy = Path(args.tag_taxonomy)
    term_index = Path(args.term_index)

    tag_entries = parse_tags_from_taxonomy(tag_taxonomy)
    tag_rows = build_tag_rows(tag_entries)
    target_rows = build_target_word_rows(parse_term_index(term_index))
    class_rows = build_classification_rows(classification_seed())

    tag_csv = out_dir / "TAG_REGISTRY_MASTER.csv"
    target_csv = out_dir / "TARGET_WORDS_HIERARCHY.csv"
    class_csv = out_dir / "CLASSIFICATION_LEVELS.csv"

    write_csv(
        tag_csv,
        tag_rows,
        [
            "tag_uuid",
            "tag",
            "axis",
            "tag_value",
            "tag_code",
            "usage_rule",
            "description",
            "status",
            "source",
            "updated_on",
        ],
    )
    write_csv(
        target_csv,
        target_rows,
        [
            "target_word_uuid",
            "target_word_key",
            "term",
            "normalized_term",
            "domain",
            "concept_bucket",
            "term_precision",
            "status",
            "uses_count",
            "aliases",
            "definition_note",
            "source_section",
            "updated_on",
        ],
    )
    write_csv(
        class_csv,
        class_rows,
        [
            "classification_uuid",
            "classification_group",
            "classification_value",
            "sort_order",
            "is_default",
            "is_active",
            "description",
            "updated_on",
        ],
    )

    print(f"Wrote {tag_csv} ({len(tag_rows)} rows)")
    print(f"Wrote {target_csv} ({len(target_rows)} rows)")
    print(f"Wrote {class_csv} ({len(class_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

