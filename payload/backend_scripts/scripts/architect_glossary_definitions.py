#!/usr/bin/env python3
"""
Glossary Definition Architect
=============================

Builds structured glossary drafts from existing Theophysics glossary notes.

What it does:
- Scans existing glossary markdown files.
- Extracts term basics (name, aliases, first definition, links, axioms, laws).
- Generates structured CORE drafts.
- Auto-selects CANONICAL candidates and generates canonical drafts.
- Optionally enriches with Wikipedia summary/comparison blocks.
- Writes a migration report (JSON + CSV).

Safe by default:
- Writes to a staging folder (`_STRUCTURED_DRAFTS`) and never overwrites
  source notes unless `--overwrite` is explicitly enabled.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


DEFAULT_GLOSSARY_DIR = Path(r"O:/_Theophysics_v3/00_SYSTEM/Glossary")
DEFAULT_OUTPUT_SUBDIR = "_STRUCTURED_DRAFTS"


SCRIPTURE_RE = re.compile(
    r"\b(?:[1-3]\s*)?"
    r"(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|"
    r"1\s*Samuel|2\s*Samuel|1\s*Kings|2\s*Kings|1\s*Chronicles|2\s*Chronicles|"
    r"Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs?|Ecclesiastes|Song of Songs|"
    r"Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|"
    r"Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|"
    r"Matthew|Mark|Luke|John|Acts|Romans|1\s*Corinthians|2\s*Corinthians|"
    r"Galatians|Ephesians|Philippians|Colossians|1\s*Thessalonians|2\s*Thessalonians|"
    r"1\s*Timothy|2\s*Timothy|Titus|Philemon|Hebrews|James|1\s*Peter|2\s*Peter|"
    r"1\s*John|2\s*John|3\s*John|Jude|Revelation)"
    r"\s+\d{1,3}:\d{1,3}(?:-\d{1,3})?\b",
    flags=re.IGNORECASE,
)

AXIOM_RE = re.compile(r"\bA\d+(?:\.\d+)?\b")
LAW_RE = re.compile(r"\bLaw\s*(?:[IVX]+|\d+)\b", flags=re.IGNORECASE)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")


SKIP_FILE_NAMES = {
    "__!!! Theophysics_Custom_Terms.md",
    "THEOPHYSICS_CUSTOM_TERMINOLOGY.md",
    "Theophysics Custom Terms.md",
    "Theophysics Custom Terms Map.md",
    "GLOSSARY.md",
    "MASTER_GLOSSARY.md",
    "Central Glossary.md",
    "00-Glossary.md",
    "00-Glossary_and_Equations.md",
    "00_MATH_SUMMARY.md",
    "index.md",
    "FRAMEWORK.md",
}


@dataclass
class NoteRecord:
    path: Path
    term: str
    content: str
    body: str
    aliases: List[str]
    first_sentence: str
    paragraphs: List[str]
    related_terms: List[str]
    scriptures: List[str]
    axioms_required: List[str]
    laws: List[str]
    has_math: bool
    inbound_links: int = 0
    outbound_links: int = 0
    canonical_candidate: bool = False
    tier_reason: str = ""
    wiki_title: str = ""
    wiki_url: str = ""
    wiki_summary: str = ""
    term_class: str = "system_specific"
    counterfactual_conflicts: List[str] = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate structured glossary drafts from existing Theophysics terms."
    )
    parser.add_argument(
        "--glossary-dir",
        type=Path,
        default=DEFAULT_GLOSSARY_DIR,
        help=f"Glossary directory (default: {DEFAULT_GLOSSARY_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output staging directory. Defaults to <glossary-dir>/_STRUCTURED_DRAFTS",
    )
    parser.add_argument(
        "--canonical-threshold",
        type=int,
        default=3,
        help="Inbound+outbound link threshold to auto-mark canonical candidates.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=0,
        help="Process only first N files (0 = all).",
    )
    parser.add_argument(
        "--with-wikipedia",
        action="store_true",
        help="Fetch Wikipedia summary/comparison data for each term.",
    )
    parser.add_argument(
        "--wiki-limit",
        type=int,
        default=0,
        help="When using --with-wikipedia, enrich only first N terms (0 = all).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output files in staging folders.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and print report only; do not write files.",
    )
    return parser.parse_args()


def normalize_term(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def should_skip(path: Path) -> bool:
    name = path.name
    stem = path.stem.lower()
    if name in SKIP_FILE_NAMES:
        return True
    if name.startswith("_"):
        return True
    if name.startswith("00_") or name.startswith("AAAA"):
        return True
    if stem in {"untitled", "untitled 1", "master index"}:
        return True
    return False


def split_frontmatter(text: str) -> Tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    lines = text.splitlines()
    if not lines:
        return "", text
    if lines[0].strip() != "---":
        return "", text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            return fm, body
    return "", text


def extract_aliases(frontmatter: str, body: str, term: str) -> List[str]:
    aliases: List[str] = []

    # Parse aliases directly from frontmatter lines to avoid accidental spillover.
    lines = frontmatter.splitlines()
    for i, ln in enumerate(lines):
        if not re.match(r"^\s*aliases\s*:", ln):
            continue
        rest = ln.split(":", 1)[1].strip()
        if rest.startswith("[") and rest.endswith("]"):
            raw = rest[1:-1]
            for part in raw.split(","):
                val = part.strip().strip("'\"")
                if val:
                    aliases.append(val)
        elif rest == "" or rest == "[]":
            j = i + 1
            while j < len(lines):
                m = re.match(r"^\s*-\s*(.+?)\s*$", lines[j])
                if not m:
                    break
                val = m.group(1).strip().strip("'\"")
                if val:
                    aliases.append(val)
                j += 1
        break

    # title-like aliases in first heading: "X (Alias / Alias2)"
    title_line = next((ln for ln in body.splitlines() if ln.startswith("# ")), "")
    if title_line:
        m = re.search(r"\(([^)]+)\)", title_line)
        if m:
            for part in re.split(r"[/,;]", m.group(1)):
                val = part.strip()
                if val and val.lower() != term.lower():
                    aliases.append(val)

    # de-dup preserve order
    deduped: List[str] = []
    seen = set()
    for a in aliases:
        key = a.lower()
        if key not in seen and key != term.lower():
            seen.add(key)
            deduped.append(a)
    return deduped


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def clean_text_lines(body: str) -> List[str]:
    lines = body.splitlines()
    out = []
    in_code = False
    for ln in lines:
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if not ln.strip():
            out.append("")
            continue
        if ln.strip() == "---":
            continue
        if ln.startswith("#"):
            continue
        if ln.strip().startswith("<!--") or ln.strip().endswith("-->"):
            continue
        if ln.lstrip().startswith(">"):
            continue
        if re.match(r"^\*\*(tags|papers|links?)\*\*:", ln.strip(), flags=re.IGNORECASE):
            continue
        if "Canonical Hub: [[00_Canonical/CANONICAL_INDEX]]" in ln:
            continue
        if "|" in ln and ln.count("|") >= 2:
            # likely table row
            continue
        out.append(ln.strip())
    return out


def extract_paragraphs(body: str) -> List[str]:
    lines = clean_text_lines(body)
    text = "\n".join(lines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs


def first_sentence(text: str) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    if not t:
        return ""
    low_signal_markers = (
        "canonical hub:",
        "[[00_canonical/canonical_index]]",
        "todo:",
        "<!--",
    )
    if any(m in t.lower() for m in low_signal_markers):
        return ""
    if len(re.findall(r"[A-Za-z]", t)) < 8:
        return ""
    m = re.match(r"(.+?[.!?])(?:\s|$)", t)
    return (m.group(1) if m else t[:220]).strip()


def is_low_signal_paragraph(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return True
    markers = (
        "canonical hub:",
        "[[00_canonical/canonical_index]]",
        "tags:",
        "papers:",
        "todo:",
        "<!--",
        "---",
    )
    if any(m in t for m in markers):
        return True
    if len(re.findall(r"[A-Za-z]", t)) < 12:
        return True
    return False


def extract_related_terms(body: str, term: str) -> List[str]:
    found = []
    for m in WIKILINK_RE.finditer(body):
        raw = m.group(1).strip()
        if not raw:
            continue
        target = Path(raw).name  # strip folder prefixes if present
        if normalize_term(target) == normalize_term(term):
            continue
        found.append(target)
    deduped = []
    seen = set()
    for r in found:
        k = normalize_term(r)
        if k and k not in seen:
            seen.add(k)
            deduped.append(r)
    return deduped[:12]


def detect_has_math(body: str) -> bool:
    if "$$" in body or "\\begin{" in body:
        return True
    equation_like = re.search(r"[A-Za-z0-9_]\s*=\s*[A-Za-z0-9_]", body)
    return bool(equation_like)


def extract_first_equation_line(body: str) -> str:
    for ln in body.splitlines():
        s = ln.strip()
        if not s:
            continue
        if "$$" in s or "\\begin{" in s:
            return s
        if re.search(r"[A-Za-z0-9_]\s*=\s*[A-Za-z0-9_]", s):
            return s
    return ""


def detect_domains(body: str, term: str) -> Dict[str, bool]:
    t = f"{term}\n{body}".lower()
    buckets = {
        "physics": ["quantum", "relativity", "thermodynamics", "field", "energy", "spacetime"],
        "information": ["information", "entropy", "compression", "signal", "shannon", "algorithmic"],
        "neuroscience": ["neural", "brain", "cortex", "neuroscience", "synapse", "fmri"],
        "psychology": ["mind", "behavior", "psychology", "cognition", "emotion", "will"],
        "sociology": ["society", "social", "culture", "collective", "group", "institution"],
        "economics": ["economics", "market", "trade", "incentive", "capital", "scarcity"],
        "theology": ["god", "grace", "logos", "trinity", "scripture", "sin", "salvation"],
    }
    return {k: any(w in t for w in words) for k, words in buckets.items()}


def fetch_wikipedia_summary(term: str) -> Tuple[str, str, str]:
    """
    Returns: (title, url, summary)
    Empty tuple fields when no match is found.
    """
    user_agent = "TheophysicsGlossaryArchitect/1.0 (definition-staging)"

    def get_json(url: str) -> Dict:
        req = Request(url, headers={"User-Agent": user_agent})
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def summary_for_title(title: str) -> Tuple[str, str, str]:
        encoded = quote(title.replace(" ", "_"))
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        data = get_json(url)
        wiki_title = data.get("title", title)
        summary = data.get("extract", "")
        page_url = (
            data.get("content_urls", {})
            .get("desktop", {})
            .get("page", f"https://en.wikipedia.org/wiki/{quote(wiki_title.replace(' ', '_'))}")
        )
        return wiki_title, page_url, summary

    try:
        return summary_for_title(term)
    except HTTPError as e:
        if e.code != 404:
            return "", "", ""
    except URLError:
        return "", "", ""
    except Exception:
        return "", "", ""

    # Search fallback
    try:
        query = quote(term)
        search_url = (
            "https://en.wikipedia.org/w/api.php?"
            f"action=query&list=search&srsearch={query}&format=json&srlimit=1"
        )
        data = get_json(search_url)
        results = data.get("query", {}).get("search", [])
        if not results:
            return "", "", ""
        top_title = results[0].get("title", "")
        if not top_title:
            return "", "", ""
        return summary_for_title(top_title)
    except Exception:
        return "", "", ""


def classify_term(term: str, wiki_title: str, wiki_summary: str) -> str:
    if not wiki_title:
        return "system_specific"
    if normalize_term(term) == normalize_term(wiki_title):
        return "standard"
    if wiki_summary:
        return "redefined"
    return "system_specific"


def infer_counterfactual_flags(
    term: str, statement: str, wiki_title: str, wiki_summary: str
) -> List[str]:
    flags: List[str] = []
    if not wiki_title:
        flags.append("No direct Wikipedia match found; likely system-specific or novel term.")
        return flags

    statement_tokens = set(re.findall(r"[A-Za-z]{4,}", statement.lower()))
    wiki_tokens = set(re.findall(r"[A-Za-z]{4,}", wiki_summary.lower()))
    if statement_tokens and wiki_tokens:
        overlap = len(statement_tokens & wiki_tokens) / max(1, len(statement_tokens))
        if overlap < 0.20:
            flags.append(
                "Low lexical overlap with Wikipedia summary; review for non-standard usage or naming drift."
            )
    if normalize_term(term) != normalize_term(wiki_title):
        flags.append(
            f"Wikipedia nearest page is '{wiki_title}', not exact term match; confirm terminology alignment."
        )
    return flags


def canonical_candidate_reason(note: NoteRecord, threshold: int) -> Tuple[bool, str]:
    structural_keywords = (
        "axiom",
        "law",
        "operator",
        "field",
        "master equation",
        "logos",
        "grace",
        "coherence",
        "trinity",
    )
    t = note.term.lower()
    degree = note.inbound_links + note.outbound_links
    keyword_hit = any(k in t for k in structural_keywords)
    if keyword_hit and degree >= threshold:
        return True, f"keyword+link_degree({degree})"
    if keyword_hit:
        return True, "structural_keyword"
    if degree >= threshold:
        return True, f"link_degree({degree})"
    return False, "core_default"


def yaml_list(name: str, values: Iterable[str], indent: int = 0) -> str:
    pad = " " * indent
    vals = list(values)
    if not vals:
        return f"{pad}{name}: []"
    lines = [f"{pad}{name}:"]
    for v in vals:
        safe = str(v).replace('"', '\\"')
        lines.append(f'{pad}  - "{safe}"')
    return "\n".join(lines)


def render_core(note: NoteRecord) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    why = note.paragraphs[1] if len(note.paragraphs) > 1 else "TODO: explain why this term matters in Theophysics."
    plain = "\n\n".join(note.paragraphs[:2]) if note.paragraphs else "TODO: add plain-English explanation."
    insight = note.first_sentence or "TODO: add one key insight sentence."
    scripture = note.scriptures[0] if note.scriptures else "TODO: add scripture connection (optional)."
    related = [f"[[{t}]]" for t in note.related_terms[:6]]
    related_line = ", ".join(related) if related else "TODO"

    wiki_block = "Wikipedia check pending."
    if note.wiki_title:
        wiki_block = (
            f"**Wikipedia Term:** {note.wiki_title}\n\n"
            f"**Summary Snapshot:**\n{note.wiki_summary or 'No summary returned.'}\n\n"
            f"**URL:** {note.wiki_url}\n\n"
            f"**Counterfactual Flags:**\n"
            + ("\n".join([f"- {x}" for x in note.counterfactual_conflicts]) if note.counterfactual_conflicts else "- None flagged.")
        )

    fm = [
        "---",
        'type: "definition"',
        'status: "draft"',
        'tier: "core"',
        f'term_class: "{note.term_class}"',
        f'wikipedia_checked: {"yes" if note.wiki_title else "no"}',
        f'source_file: "{note.path.as_posix()}"',
        f'name: "{note.term.replace(chr(34), chr(39))}"',
        yaml_list("aliases", note.aliases),
        yaml_list("axioms_required", note.axioms_required),
        yaml_list("laws", note.laws),
        yaml_list("related_terms", note.related_terms[:12]),
        f"created: {now}",
        f"updated: {now}",
        "---",
        "",
    ]

    return "\n".join(fm) + f"""# {note.term}

## Canonical Name
**Primary Term:** {note.term}

## Aliases / Synonyms
{chr(10).join([f"- {a}" for a in note.aliases]) if note.aliases else "- None captured yet"}

## What It Is

> {note.first_sentence or "TODO: add one-sentence minimal definition."}

---

## Why It Matters

{why}

---

## The Analogy

TODO: add concrete analogy for fast comprehension.

---

## In Plain English

{plain}

---

## The Key Insight

> {insight}

---

## Quick Links

- **Goes deeper:** [[{note.term}_Canonical]]
- **Related:** {related_line}

---

## Scripture Connection

{scripture}

---

## Comparative Alignment (Wikipedia)

{wiki_block}

---

## Original Source Snapshot

{note.paragraphs[0] if note.paragraphs else "No source paragraph captured."}
"""


def render_canonical(note: NoteRecord) -> str:
    now = datetime.now().strftime("%Y-%m-%d")
    domains = detect_domains(note.body, note.term)
    equation_line = extract_first_equation_line(note.body)

    fm = [
        "---",
        'type: "definition"',
        'status: "draft"',
        'tier: "canonical"',
        f'term_class: "{note.term_class}"',
        f'wikipedia_checked: {"yes" if note.wiki_title else "no"}',
        f'source_file: "{note.path.as_posix()}"',
        f'name: "{note.term.replace(chr(34), chr(39))}"',
        yaml_list("aliases", note.aliases),
        yaml_list("axioms_required", note.axioms_required),
        yaml_list("laws", note.laws),
        yaml_list("related_terms", note.related_terms[:12]),
        f"canonical_candidate_reason: \"{note.tier_reason}\"",
        f"created: {now}",
        f"updated: {now}",
        "---",
        "",
    ]

    wiki_compare = "Wikipedia check pending."
    if note.wiki_title:
        wiki_compare = (
            f"### Mainstream Definition\n"
            f"{note.wiki_summary or 'No summary returned.'}\n\n"
            f"### Source\n"
            f"{note.wiki_url}\n\n"
            f"### Counterfactual Risks Identified\n"
            + ("\n".join([f"- {x}" for x in note.counterfactual_conflicts]) if note.counterfactual_conflicts else "- None flagged.")
        )

    domain_rows = "\n".join(
        [
            f"| **{k.capitalize()}** | {'Detected from source notes' if v else 'TODO'} | TODO |"
            for k, v in domains.items()
        ]
    )

    return "\n".join(fm) + f"""# {note.term}

## 1. Canonical Statement

> {note.first_sentence or "TODO: add immutable one-sentence definition."}

## 2. Axioms Required

{chr(10).join([f"- {a}" for a in note.axioms_required]) if note.axioms_required else "- TODO"}

## 3. Mathematical Form

```text
{equation_line or "TODO: add equation / operator / logical form"}
```

**Dynamics:**
- Evolution equation: TODO
- Conservation laws: TODO
- Boundary conditions: TODO

## 4. Seven-Domain Mapping

| Domain | Interpretation | Metric |
|--------|----------------|--------|
{domain_rows}

## 5. Trinity Connection

| Aspect | Role | How It Manifests |
|--------|------|------------------|
| Father | TODO | TODO |
| Son | TODO | TODO |
| Spirit | TODO | TODO |

## 6. Master Equation Position

- Variable: TODO
- Interacts with: TODO
- Constrained by: TODO

## 7. Failure Modes

- TODO: Condition under which this definition fails.

## 8. Worked Examples

- Quantum example: TODO
- Neural example: TODO
- Social example: TODO
- Moral example: TODO

## 9. Relationships

- Parents: TODO
- Children: TODO
- Prerequisites: TODO
- Contrasts: TODO

## 10. Scriptures

{chr(10).join([f"- {s}" for s in note.scriptures]) if note.scriptures else "- TODO"}

## 11. External Comparison

{wiki_compare}

## 12. Key Insight

> {note.first_sentence or "TODO: add enduring key insight."}

## Original Source Snapshot

{note.paragraphs[0] if note.paragraphs else "No source paragraph captured."}
"""


def read_note(path: Path) -> Optional[NoteRecord]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    frontmatter, body = split_frontmatter(text)
    fallback_term = path.stem
    title = extract_title(body, fallback_term)
    term = title.strip() if title.strip() else fallback_term
    paragraphs = [p for p in extract_paragraphs(body) if not is_low_signal_paragraph(p)]
    statement = first_sentence(paragraphs[0]) if paragraphs else ""
    aliases = extract_aliases(frontmatter, body, term)
    related = extract_related_terms(body, term)
    scriptures = sorted(set(SCRIPTURE_RE.findall(body)), key=str.lower)[:8]
    axioms = sorted(set(AXIOM_RE.findall(body)))
    laws = sorted(set(LAW_RE.findall(body)))
    note = NoteRecord(
        path=path,
        term=term,
        content=text,
        body=body,
        aliases=aliases,
        first_sentence=statement,
        paragraphs=paragraphs,
        related_terms=related,
        scriptures=scriptures,
        axioms_required=axioms,
        laws=laws,
        has_math=detect_has_math(body),
        counterfactual_conflicts=[],
    )
    return note


def ensure_dir(path: Path, dry_run: bool) -> None:
    if dry_run:
        return
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str, overwrite: bool, dry_run: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    if dry_run:
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    args = parse_args()

    glossary_dir: Path = args.glossary_dir
    if not glossary_dir.exists():
        print(f"[ERROR] Glossary directory not found: {glossary_dir}")
        return 1

    output_dir = args.output_dir or (glossary_dir / DEFAULT_OUTPUT_SUBDIR)
    core_dir = output_dir / "core"
    canonical_dir = output_dir / "canonical"

    ensure_dir(output_dir, args.dry_run)
    ensure_dir(core_dir, args.dry_run)
    ensure_dir(canonical_dir, args.dry_run)

    source_files = sorted(glossary_dir.glob("*.md"))
    source_files = [p for p in source_files if not should_skip(p)]
    if args.max_files and args.max_files > 0:
        source_files = source_files[: args.max_files]

    notes: List[NoteRecord] = []
    for p in source_files:
        note = read_note(p)
        if note:
            notes.append(note)

    if not notes:
        print("[WARN] No source term files found after filters.")
        return 0

    # Build reference graph (inbound links)
    norm_to_note: Dict[str, NoteRecord] = {normalize_term(n.term): n for n in notes}
    inbound_map: Dict[str, int] = {normalize_term(n.term): 0 for n in notes}
    for n in notes:
        n.outbound_links = len(n.related_terms)
        for link in n.related_terms:
            key = normalize_term(link)
            if key in inbound_map:
                inbound_map[key] += 1
    for n in notes:
        n.inbound_links = inbound_map.get(normalize_term(n.term), 0)
        n.canonical_candidate, n.tier_reason = canonical_candidate_reason(
            n, args.canonical_threshold
        )

    # Optional Wikipedia enrichment
    if args.with_wikipedia:
        print("[INFO] Wikipedia enrichment enabled...")
        for i, n in enumerate(notes, 1):
            if args.wiki_limit and i > args.wiki_limit:
                n.term_class = "system_specific"
                n.counterfactual_conflicts = ["Wikipedia check skipped by wiki-limit setting."]
                continue
            title, url, summary = fetch_wikipedia_summary(n.term)
            n.wiki_title = title
            n.wiki_url = url
            n.wiki_summary = summary
            n.term_class = classify_term(n.term, title, summary)
            n.counterfactual_conflicts = infer_counterfactual_flags(
                n.term, n.first_sentence, title, summary
            )
            if i % 25 == 0:
                print(f"[INFO] Enriched {i}/{len(notes)} terms...")
    else:
        for n in notes:
            n.term_class = "system_specific"
            n.counterfactual_conflicts = []

    # Write staged drafts
    core_written = 0
    canonical_written = 0
    skipped_existing = 0

    for n in notes:
        safe_name = n.path.stem
        core_path = core_dir / f"{safe_name}.md"
        if write_text(core_path, render_core(n), args.overwrite, args.dry_run):
            core_written += 1
        else:
            skipped_existing += 1

        if n.canonical_candidate:
            canonical_path = canonical_dir / f"{safe_name}_Canonical.md"
            if write_text(canonical_path, render_canonical(n), args.overwrite, args.dry_run):
                canonical_written += 1
            else:
                skipped_existing += 1

    # Report
    report_rows = []
    for n in notes:
        report_rows.append(
            {
                "source_file": n.path.name,
                "term": n.term,
                "aliases_count": len(n.aliases),
                "related_terms": len(n.related_terms),
                "axioms_required": ";".join(n.axioms_required),
                "laws": ";".join(n.laws),
                "inbound_links": n.inbound_links,
                "outbound_links": n.outbound_links,
                "canonical_candidate": n.canonical_candidate,
                "canonical_reason": n.tier_reason,
                "term_class": n.term_class,
                "wikipedia_title": n.wiki_title,
                "wikipedia_url": n.wiki_url,
                "counterfactual_conflicts": " | ".join(n.counterfactual_conflicts or []),
            }
        )

    summary = {
        "timestamp": datetime.now().isoformat(),
        "glossary_dir": str(glossary_dir),
        "output_dir": str(output_dir),
        "with_wikipedia": bool(args.with_wikipedia),
        "wiki_limit": int(args.wiki_limit),
        "dry_run": bool(args.dry_run),
        "source_files_considered": len(source_files),
        "notes_processed": len(notes),
        "core_written": core_written,
        "canonical_written": canonical_written,
        "skipped_existing": skipped_existing,
    }

    if not args.dry_run:
        report_json = output_dir / "architecture_report.json"
        report_csv = output_dir / "architecture_report.csv"
        report_json.write_text(
            json.dumps({"summary": summary, "rows": report_rows}, indent=2),
            encoding="utf-8",
        )
        with report_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(report_rows[0].keys()))
            writer.writeheader()
            writer.writerows(report_rows)

    print("[DONE] Glossary architecture pass complete.")
    print(json.dumps(summary, indent=2))
    if not args.dry_run:
        print(f"[REPORT] {output_dir / 'architecture_report.json'}")
        print(f"[REPORT] {output_dir / 'architecture_report.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
