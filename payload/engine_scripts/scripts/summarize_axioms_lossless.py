#!/usr/bin/env python3
"""
Build two-part lossless summaries for axiom files:
  Part 1: Straight axioms (claim chain, dependencies, formal/falsification core)
  Part 2: Court layer (objections, prosecution, cross-exam, verdict, case files)
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_AXIOMS_DIR = Path(r"O:\_Theophysics_v3\00_AXIOMS")
DEFAULT_OUT_DIR = DEFAULT_AXIOMS_DIR / "_LOSSLESS_SUMMARY"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate two-part lossless axiom summaries.")
    parser.add_argument("--axioms-dir", default=str(DEFAULT_AXIOMS_DIR), help="Path to 00_AXIOMS")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory")
    parser.add_argument("--max", type=int, default=0, help="Optional max number of axiom files")
    return parser.parse_args()


def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def strip_markdown(s: str) -> str:
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", s)
    s = re.sub(r"\[\[([^\]]+)\]\]", r"\1", s)
    s = s.replace("**", "").replace("*", "")
    return normalize(s)


def parse_frontmatter(text: str) -> Dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}

    lines = text[4:end].splitlines()
    out: Dict[str, object] = {}
    current_key = None
    for raw in lines:
        line = raw.rstrip()
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if m:
            key, value = m.group(1), m.group(2).strip()
            current_key = key
            if value == "":
                out[key] = []
                continue
            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip("'\"") for x in value[1:-1].split(",") if x.strip()]
                out[key] = items
            else:
                out[key] = value.strip("'\"")
            continue
        m2 = re.match(r"^\s*-\s+(.*)$", line)
        if m2 and current_key:
            if not isinstance(out.get(current_key), list):
                out[current_key] = []
            out[current_key].append(m2.group(1).strip().strip("'\""))
    return out


def body_after_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + 5 :]


def split_sections(body: str) -> Dict[str, str]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE))
    sections: Dict[str, str] = {}
    if not matches:
        return sections
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[name] = body[start:end].strip()
    return sections


def first_h1(body: str) -> str:
    m = re.search(r"^#\s+(.+)$", body, flags=re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_claim(formal_or_claim: str) -> str:
    if not formal_or_claim:
        return ""
    # Prefer blockquote for exact formal claim.
    m = re.search(r"^\s*>\s*(.+)$", formal_or_claim, flags=re.MULTILINE)
    if m:
        return strip_markdown(m.group(1))
    # Else first non-empty sentence-like line.
    for line in formal_or_claim.splitlines():
        s = strip_markdown(line)
        if s and not s.startswith("-") and not s.startswith("|"):
            return s
    return ""


def extract_case_files(text: str) -> List[str]:
    found: List[str] = []
    for m in re.finditer(r"CF\d{2}_[A-Za-z0-9_\-]+", text):
        cf = m.group(0)
        if cf not in found:
            found.append(cf)
    return found


def count_objections(section: str) -> int:
    if not section:
        return 0
    n = len(re.findall(r"^\s*###\s+Objection", section, flags=re.MULTILINE))
    if n > 0:
        return n
    # fallback for bullet style
    n = len(re.findall(r"^\s*-\s*Objection", section, flags=re.MULTILINE))
    return n


def prosecution_blocks(text: str) -> Tuple[str, str, str]:
    defense = ""
    cross = ""
    verdict = ""
    m_def = re.search(
        r"\*\*The Prosecutor's Defense:\*\*(.*?)(?:\*\*The Cross-Examination:\*\*|\*\*The Verdict:\*\*|$)",
        text,
        flags=re.DOTALL,
    )
    if m_def:
        defense = strip_markdown(m_def.group(1))
    m_cross = re.search(
        r"\*\*The Cross-Examination:\*\*(.*?)(?:\*\*The Verdict:\*\*|$)",
        text,
        flags=re.DOTALL,
    )
    if m_cross:
        cross = strip_markdown(m_cross.group(1))
    m_verdict = re.search(r"\*\*The Verdict:\*\*(.*?)(?:\n##|\Z)", text, flags=re.DOTALL)
    if m_verdict:
        verdict = strip_markdown(m_verdict.group(1))
    return defense, cross, verdict


def axiom_files(axioms_dir: Path) -> List[Path]:
    files = []
    for p in axioms_dir.glob("[0-9][0-9][0-9]_*.md"):
        files.append(p)
    return sorted(files, key=lambda p: int(p.name.split("_", 1)[0]))


def build_record(path: Path) -> Dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)
    body = body_after_frontmatter(text)
    sections = split_sections(body)
    title = strip_markdown(first_h1(body))

    claim = extract_claim(sections.get("The Claim", "")) or extract_claim(sections.get("Formal Statement", ""))
    defeat = strip_markdown(sections.get("Defeat Conditions", ""))
    if not defeat:
        defeat = strip_markdown(sections.get("Falsification Criteria", ""))

    objections_section = sections.get("Standard Objections", "")
    defense_summary = strip_markdown(sections.get("Defense Summary", ""))

    court_source = body
    defense, cross, verdict = prosecution_blocks(court_source)
    case_files = extract_case_files(court_source)

    return {
        "file": path.name,
        "path": str(path),
        "num": path.name.split("_", 1)[0],
        "axiom_id": str(fm.get("axiom_id", "")),
        "chain_position": str(fm.get("chain_position", "")),
        "title": title,
        "classification": str(fm.get("classification", "")),
        "domain": fm.get("domain", []) if isinstance(fm.get("domain", []), list) else [str(fm.get("domain", ""))],
        "depends_on": fm.get("depends_on", []) if isinstance(fm.get("depends_on", []), list) else [str(fm.get("depends_on", ""))],
        "enables": fm.get("enables", []) if isinstance(fm.get("enables", []), list) else [str(fm.get("enables", ""))],
        "status": str(fm.get("status", "")),
        "claim": claim,
        "defeat_conditions": defeat,
        "objections_count": count_objections(objections_section),
        "defense_summary": defense_summary,
        "prosecutor_defense": defense,
        "cross_examination": cross,
        "verdict": verdict,
        "case_files": case_files,
    }


def as_list(val: object) -> List[str]:
    if isinstance(val, list):
        return [str(x) for x in val if str(x).strip()]
    if val is None:
        return []
    s = str(val).strip()
    return [s] if s else []


def write_part1(records: List[Dict[str, object]], out: Path) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append("# LOSSLESS Axiom Summary - Part 1 (Straight Axioms)")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("Format: one compact line + structured fields per axiom.")
    lines.append("")
    for r in records:
        deps_items = as_list(r["depends_on"])
        en_items = as_list(r["enables"])
        dom_items = as_list(r["domain"])
        deps = ", ".join(deps_items)
        en = ", ".join(en_items)
        dom = ", ".join(dom_items)
        lines.append(
            f"AX|n:{r['num']}|id:{r['axiom_id']}|cp:{r['chain_position']}|class:{strip_markdown(str(r['classification']))}|status:{r['status']}"
        )
        lines.append(f"- title: {r['title']}")
        lines.append(f"- claim: {r['claim']}")
        lines.append(f"- depends_on: [{deps}]")
        lines.append(f"- enables: [{en}]")
        lines.append(f"- domain: [{dom}]")
        lines.append(f"- defeat_conditions: {r['defeat_conditions']}")
        lines.append(f"- src: {r['path']}")
        lines.append("")
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_part2(records: List[Dict[str, object]], out: Path) -> None:
    now = dt.datetime.now().isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append("# LOSSLESS Axiom Summary - Part 2 (Judge/Jury/Court Layer)")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("Court layer captures objections, prosecution, cross-exam, verdict, and case-file links.")
    lines.append("")
    for r in records:
        case_files = ", ".join(as_list(r["case_files"]))
        lines.append(
            f"CJ|n:{r['num']}|id:{r['axiom_id']}|obj_count:{r['objections_count']}|case_files:[{case_files}]"
        )
        lines.append(f"- title: {r['title']}")
        lines.append(f"- defense_summary: {r['defense_summary']}")
        lines.append(f"- prosecutor_defense: {r['prosecutor_defense']}")
        lines.append(f"- cross_examination: {r['cross_examination']}")
        lines.append(f"- verdict: {r['verdict']}")
        lines.append(f"- src: {r['path']}")
        lines.append("")
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    axioms_dir = Path(args.axioms_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = axiom_files(axioms_dir)
    if args.max and args.max > 0:
        files = files[: args.max]

    records = [build_record(f) for f in files]

    part1 = out_dir / "AXIOMS_PART1_STRAIGHT.md"
    part2 = out_dir / "AXIOMS_PART2_COURT.md"
    write_part1(records, part1)
    write_part2(records, part2)

    print(f"Summarized {len(records)} axiom files")
    print(f"Wrote {part1}")
    print(f"Wrote {part2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
