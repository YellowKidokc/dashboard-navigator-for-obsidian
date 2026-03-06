"""
Three-tier math appendix builder for Obsidian vaults.

Tier 1: Per-paper math appendix block (capped rows, with overflow sidecar).
Tier 2: Per-top-folder _MATH_INDEX.md (registry of short codes used there).
Tier 3: Root REGISTERED_VARIABLES.md (full registry with conflict checks).

Usage example:
    python scripts/build_math_appendix_system.py ^
      --vault-root "O:/_Theophysics_v3/04_THEOPYHISCS" ^
      --seed "D:/01_Axioms/04_REFERENCE/MATH_TRANSLATION_TABLE.csv" ^
      --apply-paper-blocks
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


APPENDIX_START = "<!-- MATH_APPENDIX_START -->"
APPENDIX_END = "<!-- MATH_APPENDIX_END -->"
DEFAULT_MAX_PAPER_ROWS = 10


LATEX_TOKEN_RE = re.compile(
    r"""
    (\\[A-Za-z]+(?:_\{[^}]+\}|_[A-Za-z0-9]+)?(?:\^\{[^}]+\}|\^[A-Za-z0-9]+)?)|
    ([A-Za-z]+(?:_[A-Za-z0-9]+)?)|
    ([\u0370-\u03FF]+)
    """,
    re.VERBOSE,
)
DISPLAY_EQ_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
INLINE_EQ_RE = re.compile(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)")

LATEX_STOPWORDS = {
    "frac",
    "text",
    "left",
    "right",
    "cdot",
    "times",
    "mathrm",
    "mathcal",
    "begin",
    "end",
    "quad",
    "qquad",
    "sum",
    "int",
    "partial",
    "exp",
}

SECTION_DOMAIN_MAP = {
    "CORE SYMBOLS": "ME",
    "GRACE & SALVATION SYMBOLS": "Z2",
    "PHYSICS SYMBOLS": "EM",
    "INFORMATION THEORY SYMBOLS": "TH",
    "QUANTUM MECHANICS SYMBOLS": "QM",
}

GREEK_MAP = {
    "chi": "\\chi",
    "phi": "\\phi",
    "Phi": "\\Phi",
    "psi": "\\psi",
    "Psi": "\\Psi",
    "alpha": "\\alpha",
    "beta": "\\beta",
    "gamma": "\\gamma",
    "delta": "\\delta",
    "lambda": "\\lambda",
    "mu": "\\mu",
    "sigma": "\\sigma",
    "tau": "\\tau",
    "theta": "\\theta",
}

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


@dataclass
class RegistryEntry:
    code: str
    symbol: str
    domain: str
    definition: str
    basic_definition: str = ""
    medium_definition: str = ""
    academic_definition: str = ""
    category: str = ""
    context_notes: str = ""
    first_appears: str = ""
    math_name: str = ""
    symbol_display: str = ""
    aliases: Set[str] = field(default_factory=set)
    z2_mirror: str = ""
    owner_folder: str = ""
    source: str = "seed"

    @property
    def anchor(self) -> str:
        raw = self.code.strip("[]").replace(":", "-")
        raw = re.sub(r"[^A-Za-z0-9_-]+", "-", raw)
        return raw.lower().strip("-")


@dataclass
class PaperScanResult:
    path: Path
    top_folder: str
    equation_count: int
    codes: List[str]
    unknown_symbols: List[str]


def clean_cell(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def domain_from_category(category: str) -> str:
    key = clean_cell(category).lower()
    if not key:
        return "MATH"
    return CSV_CATEGORY_DOMAIN_MAP.get(key, re.sub(r"[^A-Za-z0-9]+", "_", key).upper()[:12] or "MATH")


def load_csv_seed_entries(seed_path: Path, existing_entries: Optional[List[RegistryEntry]] = None) -> List[RegistryEntry]:
    entries: List[RegistryEntry] = []
    existing_entries = existing_entries or []
    used_codes: Set[str] = {entry.code for entry in existing_entries if entry.code}
    existing_by_symbol = {
        normalize_token(entry.symbol): entry
        for entry in existing_entries
        if entry.symbol
    }
    matched_existing_symbols: Set[str] = set()

    with seed_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, start=1):
            symbol = clean_cell(row.get("Symbol_LaTeX"))
            if not symbol:
                continue

            symbol_display = clean_cell(row.get("Symbol_Display"))
            category = clean_cell(row.get("Category"))
            math_name = clean_cell(row.get("Math_Name"))
            basic = clean_cell(row.get("Basic_Translation"))
            medium = clean_cell(row.get("Medium_Translation"))
            academic = clean_cell(row.get("Academic_Translation"))
            context = clean_cell(row.get("Context_Notes"))
            first_appears = clean_cell(row.get("First_Appears"))

            existing = existing_by_symbol.get(normalize_token(symbol))
            if existing:
                matched_existing_symbols.add(normalize_token(symbol))

            domain = existing.domain if existing and existing.domain else domain_from_category(category)
            token_source = symbol or math_name or symbol_display or f"symbol_{idx}"
            slug = slugify_symbol(token_source)
            if not slug:
                slug = f"symbol_{idx}"
            code = existing.code if existing and existing.code else f"[{domain}:{slug}]"
            collision_ix = 2
            while code in used_codes and (not existing or code != existing.code):
                code = f"[{domain}:{slug}_{collision_ix}]"
                collision_ix += 1
            used_codes.add(code)

            aliases: Set[str] = set(existing.aliases) if existing else set()
            for alias_candidate in (
                symbol,
                symbol.replace("\\", ""),
                symbol_display,
                math_name,
                re.sub(r"\s+", "_", basic.lower()).strip("_")[:40] if basic else "",
            ):
                alias = clean_cell(alias_candidate)
                if alias:
                    aliases.add(alias)

            definition = academic or medium or basic or "Definition pending."
            entries.append(
                RegistryEntry(
                    code=code,
                    symbol=symbol,
                    symbol_display=symbol_display,
                    domain=domain,
                    category=category,
                    math_name=math_name,
                    definition=definition,
                    basic_definition=basic or definition,
                    medium_definition=medium or basic or definition,
                    academic_definition=academic or medium or basic or definition,
                    context_notes=context,
                    first_appears=first_appears,
                    aliases=aliases,
                    z2_mirror=existing.z2_mirror if existing else "",
                    owner_folder=existing.owner_folder if existing and existing.owner_folder else "04_THEOPYHISCS",
                    source=f"seed:{seed_path.name}",
                )
            )

    for entry in existing_entries:
        if normalize_token(entry.symbol) not in matched_existing_symbols:
            entries.append(entry)

    return entries


def load_seed_entries(seed_path: Optional[Path]) -> List[RegistryEntry]:
    if not seed_path or not seed_path.exists():
        return []

    data = None
    if seed_path.suffix.lower() == ".csv":
        legacy_seed_path = Path("config/math_registry_seed.yaml")
        legacy_entries = []
        if legacy_seed_path.exists():
            legacy_entries = load_seed_entries(legacy_seed_path)
        return load_csv_seed_entries(seed_path, existing_entries=legacy_entries)

    text = seed_path.read_text(encoding="utf-8")

    if seed_path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(text)
        except Exception as exc:
            raise RuntimeError(f"Failed to parse YAML seed file {seed_path}: {exc}") from exc
    else:
        data = json.loads(text)

    entries_data = data.get("entries", []) if isinstance(data, dict) else []
    out: List[RegistryEntry] = []
    for item in entries_data:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        aliases = set(str(a).strip() for a in item.get("aliases", []) if str(a).strip())
        out.append(
            RegistryEntry(
                code=code,
                symbol=str(item.get("symbol", "")).strip(),
                domain=str(item.get("domain", "")).strip().upper() or code.strip("[]").split(":", 1)[0],
                definition=str(item.get("definition", "")).strip(),
                basic_definition=str(item.get("basic_translation", item.get("definition", ""))).strip(),
                medium_definition=str(item.get("medium_translation", item.get("definition", ""))).strip(),
                academic_definition=str(item.get("academic_translation", item.get("definition", ""))).strip(),
                category=str(item.get("category", "")).strip(),
                context_notes=str(item.get("context_notes", "")).strip(),
                first_appears=str(item.get("first_appears", "")).strip(),
                math_name=str(item.get("math_name", "")).strip(),
                symbol_display=str(item.get("symbol_display", item.get("display", ""))).strip(),
                aliases=aliases,
                z2_mirror=str(item.get("z2_mirror", "")).strip(),
                owner_folder=str(item.get("owner_folder", "")).strip(),
                source=f"seed:{seed_path.name}",
            )
        )
    return out


def slugify_symbol(symbol: str) -> str:
    s = symbol.strip()
    s = s.replace("\\", "")
    s = re.sub(r"\{.*?\}", "", s)
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    s = s.strip("_")
    return s.lower() or "symbol"


def parse_glossary_table(glossary_path: Path) -> List[RegistryEntry]:
    if not glossary_path.exists():
        return []

    lines = glossary_path.read_text(encoding="utf-8").splitlines()
    current_section = ""
    entries: List[RegistryEntry] = []

    for line in lines:
        if line.startswith("## "):
            current_section = line.replace("## ", "").strip()
            continue
        if not line.startswith("|"):
            continue
        if line.startswith("| Symbol |") or line.startswith("|--------"):
            continue

        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 3:
            continue
        if current_section not in SECTION_DOMAIN_MAP:
            continue

        symbol_raw, name_raw, meaning_raw = parts[0], parts[1], parts[2]
        symbol_clean = re.sub(r"\*\*", "", symbol_raw).strip()
        symbol_main = symbol_clean.split("(", 1)[0].strip()
        domain = SECTION_DOMAIN_MAP[current_section]
        code = f"[{domain}:{slugify_symbol(symbol_main)}]"

        aliases: Set[str] = {symbol_main}
        name_token = re.sub(r"[^A-Za-z0-9_]+", "_", name_raw).strip("_")
        if name_token:
            aliases.add(name_token)
        if symbol_main in {"chi", "phi", "Phi", "psi", "Psi"}:
            aliases.add(GREEK_MAP.get(symbol_main, symbol_main))

        entries.append(
            RegistryEntry(
                code=code,
                symbol=symbol_main,
                domain=domain,
                definition=meaning_raw.strip(),
                basic_definition=meaning_raw.strip(),
                medium_definition=meaning_raw.strip(),
                academic_definition=meaning_raw.strip(),
                category=current_section,
                aliases=aliases,
                source=f"glossary:{glossary_path.name}",
            )
        )
    return entries


def normalize_token(token: str) -> str:
    t = token.strip()
    t = t.strip("$")
    t = t.replace("{", "").replace("}", "")
    t = t.replace("(", "").replace(")", "")
    t = t.replace("^", "")
    t = t.strip()
    if t.startswith("\\"):
        t = t[1:]
    return t.lower()


def normalize_conflict_symbol(symbol: str) -> str:
    """
    Normalize symbols for conflict detection, preserving case.

    This keeps meaningful distinctions such as G vs g, \\Gamma vs \\gamma,
    \\Lambda vs \\lambda while still collapsing superficial formatting noise.
    """
    s = symbol.strip()
    s = s.strip("$")
    s = s.replace("{", "").replace("}", "")
    s = s.replace("(", "").replace(")", "")
    s = s.replace("^", "")
    s = re.sub(r"\s+", "", s)
    if s.startswith("\\"):
        s = s[1:]
    return s


def build_registry(seed_entries: List[RegistryEntry], glossary_entries: List[RegistryEntry]) -> Dict[str, RegistryEntry]:
    registry: Dict[str, RegistryEntry] = {}

    for entry in glossary_entries + seed_entries:
        if not entry.code:
            continue
        if entry.code in registry:
            existing = registry[entry.code]
            # Seed entries override glossary details.
            if entry.source.startswith("seed:"):
                existing.symbol = entry.symbol or existing.symbol
                existing.domain = entry.domain or existing.domain
                existing.definition = entry.definition or existing.definition
                existing.basic_definition = entry.basic_definition or existing.basic_definition
                existing.medium_definition = entry.medium_definition or existing.medium_definition
                existing.academic_definition = entry.academic_definition or existing.academic_definition
                existing.category = entry.category or existing.category
                existing.context_notes = entry.context_notes or existing.context_notes
                existing.first_appears = entry.first_appears or existing.first_appears
                existing.math_name = entry.math_name or existing.math_name
                existing.symbol_display = entry.symbol_display or existing.symbol_display
                existing.z2_mirror = entry.z2_mirror or existing.z2_mirror
                existing.owner_folder = entry.owner_folder or existing.owner_folder
                existing.source = entry.source
            existing.aliases.update(entry.aliases)
            continue

        registry[entry.code] = entry

    # Ensure every entry has at least symbol and code suffix aliases.
    for entry in registry.values():
        entry.aliases.add(entry.symbol)
        code_suffix = entry.code.strip("[]").split(":", 1)[-1]
        entry.aliases.add(code_suffix)
        if entry.symbol in GREEK_MAP:
            entry.aliases.add(GREEK_MAP[entry.symbol])
        if not entry.basic_definition:
            entry.basic_definition = entry.definition
        if not entry.medium_definition:
            entry.medium_definition = entry.basic_definition
        if not entry.academic_definition:
            entry.academic_definition = entry.medium_definition

    return registry


def extract_equations(markdown: str) -> List[str]:
    equations: List[str] = []
    equations.extend(m.group(1) for m in DISPLAY_EQ_RE.finditer(markdown))
    for m in INLINE_EQ_RE.finditer(markdown):
        content = m.group(1).strip()
        if content and not re.fullmatch(r"\d[\d,\.]*", content):
            equations.append(content)
    return equations


def extract_symbols_from_equation(eq: str) -> List[str]:
    # Remove textual prose segments embedded in LaTeX.
    cleaned = re.sub(r"\\text\{[^}]*\}", " ", eq)
    cleaned = re.sub(r"\\mathrm\{[^}]*\}", " ", cleaned)

    symbols: Set[str] = set()
    for match in LATEX_TOKEN_RE.finditer(cleaned):
        token = match.group(0).strip()
        if not token:
            continue
        norm = normalize_token(token)
        if not norm or norm in LATEX_STOPWORDS:
            continue
        if norm.isdigit():
            continue
        if not token.startswith("\\"):
            # For plain tokens, keep variable-like forms only.
            if "_" not in token and len(norm) > 2 and norm not in {"phi", "chi", "psi"}:
                continue
        symbols.add(token)
    return sorted(symbols)


def build_alias_index(registry: Dict[str, RegistryEntry]) -> Dict[str, Set[str]]:
    alias_index: Dict[str, Set[str]] = {}
    for code, entry in registry.items():
        for alias in entry.aliases:
            norm = normalize_token(alias)
            if not norm:
                continue
            alias_index.setdefault(norm, set()).add(code)
            # Also map base before "_" for subscripted variants.
            alias_index.setdefault(norm.split("_", 1)[0], set()).add(code)
    return alias_index


def scan_papers(vault_root: Path, registry: Dict[str, RegistryEntry]) -> Tuple[List[PaperScanResult], Dict[str, Set[str]]]:
    alias_index = build_alias_index(registry)
    paper_results: List[PaperScanResult] = []
    usage_map: Dict[str, Set[str]] = {code: set() for code in registry}

    for md_file in sorted(vault_root.rglob("*.md")):
        if md_file.name.startswith("_MATH_INDEX"):
            continue
        if md_file.name == "REGISTERED_VARIABLES.md":
            continue

        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Skip unreadable files (permissions, locks, etc.).
            continue
        equations = extract_equations(content)
        found_codes: Set[str] = set()
        unknown_symbols: Set[str] = set()

        for eq in equations:
            for symbol in extract_symbols_from_equation(eq):
                norm = normalize_token(symbol)
                candidates = alias_index.get(norm, set())
                if not candidates:
                    candidates = alias_index.get(norm.split("_", 1)[0], set())
                if candidates:
                    found_codes.update(candidates)
                else:
                    unknown_symbols.add(symbol)

        rel_parts = md_file.relative_to(vault_root).parts
        top_folder = rel_parts[0] if len(rel_parts) > 1 else "_ROOT"
        result = PaperScanResult(
            path=md_file,
            top_folder=top_folder,
            equation_count=len(equations),
            codes=sorted(found_codes),
            unknown_symbols=sorted(unknown_symbols),
        )
        paper_results.append(result)

        rel_str = str(md_file.relative_to(vault_root)).replace("\\", "/")
        for code in found_codes:
            usage_map.setdefault(code, set()).add(rel_str)

    return paper_results, usage_map


def render_tier1_block(
    paper_rel: str,
    codes: List[str],
    registry: Dict[str, RegistryEntry],
    max_rows: int,
    overflow_rel: Optional[str] = None,
) -> str:
    lines = [
        APPENDIX_START,
        "## Math Appendix (Tier 1)",
        "",
        "| Code | Symbol | Definition | Registry |",
        "|---|---|---|---|",
    ]

    for code in codes[:max_rows]:
        entry = registry[code]
        definition = (entry.medium_definition or entry.definition or entry.basic_definition).replace("\n", " ").strip()
        if len(definition) > 140:
            definition = definition[:137] + "..."
        link = f"[[REGISTERED_VARIABLES#{entry.anchor}|Open]]"
        lines.append(f"| `{code}` | `{entry.symbol}` | {definition} | {link} |")

    if len(codes) > max_rows:
        lines.append("")
        if overflow_rel:
            lines.append(
                f"> [!note] Showing first {max_rows} codes. "
                f"Full list: [[{overflow_rel}|Math Appendix Overflow]]."
            )
        else:
            lines.append(f"> [!note] Showing first {max_rows} codes.")

    lines.extend(["", APPENDIX_END, ""])
    return "\n".join(lines)


def upsert_appendix_block(markdown: str, block: str) -> str:
    if APPENDIX_START in markdown and APPENDIX_END in markdown:
        pattern = re.compile(
            re.escape(APPENDIX_START) + r".*?" + re.escape(APPENDIX_END),
            re.DOTALL,
        )
        return pattern.sub(block.strip(), markdown)

    body = markdown.rstrip()
    return body + "\n\n" + block


def write_paper_blocks(
    vault_root: Path,
    paper_results: List[PaperScanResult],
    registry: Dict[str, RegistryEntry],
    max_rows: int,
    apply_changes: bool,
) -> int:
    changed = 0
    for paper in paper_results:
        if not paper.codes:
            continue

        overflow_rel = None
        if len(paper.codes) > max_rows:
            overflow_path = paper.path.with_name(f"{paper.path.stem}_MATH_APPENDIX.md")
            overflow_lines = [
                "# Math Appendix Overflow",
                "",
                f"Source: `{paper.path.name}`",
                "",
                "| Code | Symbol | Definition | Registry |",
                "|---|---|---|---|",
            ]
            for code in paper.codes:
                entry = registry[code]
                link = f"[[REGISTERED_VARIABLES#{entry.anchor}|Open]]"
                definition = entry.medium_definition or entry.definition or entry.basic_definition
                overflow_lines.append(
                    f"| `{code}` | `{entry.symbol}` | {definition} | {link} |"
                )
            overflow_content = "\n".join(overflow_lines) + "\n"
            if apply_changes:
                overflow_path.write_text(overflow_content, encoding="utf-8")
            overflow_rel = overflow_path.name

        rel_str = str(paper.path.relative_to(vault_root)).replace("\\", "/")
        block = render_tier1_block(rel_str, paper.codes, registry, max_rows, overflow_rel)
        content = paper.path.read_text(encoding="utf-8", errors="ignore")
        updated = upsert_appendix_block(content, block)
        if updated != content:
            changed += 1
            if apply_changes:
                paper.path.write_text(updated, encoding="utf-8")
    return changed


def write_folder_indexes(vault_root: Path, paper_results: List[PaperScanResult], apply_changes: bool) -> int:
    folder_codes: Dict[str, Set[str]] = {}
    folder_papers: Dict[str, Set[str]] = {}
    for paper in paper_results:
        folder_codes.setdefault(paper.top_folder, set()).update(paper.codes)
        folder_papers.setdefault(paper.top_folder, set()).add(
            str(paper.path.relative_to(vault_root)).replace("\\", "/")
        )

    written = 0
    for folder, codes in sorted(folder_codes.items()):
        if not codes:
            continue
        folder_path = vault_root if folder == "_ROOT" else vault_root / folder
        index_path = folder_path / "_MATH_INDEX.md"
        lines = [
            "# Math Index (Tier 2)",
            "",
            f"Folder: `{folder}`",
            f"Papers scanned: {len(folder_papers.get(folder, set()))}",
            "",
            "| Code | Registry |",
            "|---|---|",
        ]
        for code in sorted(codes):
            anchor = re.sub(r"[^A-Za-z0-9_-]+", "-", code.strip("[]").replace(":", "-")).lower().strip("-")
            lines.append(f"| `{code}` | [[REGISTERED_VARIABLES#{anchor}|Open]] |")

        content = "\n".join(lines) + "\n"
        written += 1
        if apply_changes:
            folder_path.mkdir(parents=True, exist_ok=True)
            index_path.write_text(content, encoding="utf-8")
    return written


def collect_conflicts(registry: Dict[str, RegistryEntry], usage_map: Dict[str, Set[str]], paper_results: List[PaperScanResult]) -> Dict[str, object]:
    symbol_groups: Dict[str, List[RegistryEntry]] = {}
    for entry in registry.values():
        key = normalize_conflict_symbol(entry.symbol)
        symbol_groups.setdefault(key, []).append(entry)

    symbol_conflicts = []
    for symbol_norm, entries in sorted(symbol_groups.items()):
        unique_defs = {e.definition.strip() for e in entries}
        unique_domains = {e.domain.strip().upper() for e in entries}
        if len(entries) > 1 and (len(unique_defs) > 1 or len(unique_domains) > 1):
            symbol_conflicts.append(
                {
                    "symbol": symbol_norm,
                    "codes": [e.code for e in entries],
                    "domains": sorted(unique_domains),
                    "definitions": sorted(unique_defs),
                }
            )

    unknown_by_paper = []
    unknown_freq: Dict[str, int] = {}
    for paper in paper_results:
        if paper.unknown_symbols:
            unknown_by_paper.append(
                {
                    "paper": str(paper.path),
                    "unknown_symbols": paper.unknown_symbols,
                }
            )
            for sym in paper.unknown_symbols:
                unknown_freq[sym] = unknown_freq.get(sym, 0) + 1

    unused_codes = sorted(code for code, papers in usage_map.items() if not papers)
    top_unknown = sorted(unknown_freq.items(), key=lambda x: x[1], reverse=True)[:100]

    return {
        "symbol_conflicts": symbol_conflicts,
        "unknown_symbols_by_paper": unknown_by_paper,
        "unknown_symbol_frequency": top_unknown,
        "unused_registry_codes": unused_codes,
        "summary": {
            "registry_entries": len(registry),
            "symbol_conflicts": len(symbol_conflicts),
            "papers_with_unknown_symbols": len(unknown_by_paper),
            "unique_unknown_symbols": len(unknown_freq),
            "unused_registry_codes": len(unused_codes),
        },
    }


def write_registry_root(
    vault_root: Path,
    registry: Dict[str, RegistryEntry],
    usage_map: Dict[str, Set[str]],
    apply_changes: bool,
) -> Path:
    out_path = vault_root / "REGISTERED_VARIABLES.md"
    lines = [
        "# Registered Variable Index (Tier 3)",
        "",
        "Registry-first rule: no symbol enters Tier 1/Tier 2 unless registered here.",
        "",
        "| Code | Symbol | Domain | Mirror | Owner Folder | Used In |",
        "|---|---|---|---|---|---|",
    ]

    for code, entry in sorted(registry.items(), key=lambda x: x[0]):
        used_count = len(usage_map.get(code, set()))
        mirror = entry.z2_mirror or "-"
        owner = entry.owner_folder or "-"
        lines.append(
            f"| `{code}` | `{entry.symbol}` | `{entry.domain}` | `{mirror}` | `{owner}` | {used_count} |"
        )

    lines.extend(["", "## Full Definitions", ""])
    for code, entry in sorted(registry.items(), key=lambda x: x[0]):
        lines.extend(
            [
                f"### {code} <a id=\"{entry.anchor}\"></a>",
                "",
                f"- Symbol: `{entry.symbol}`",
                f"- Display: `{entry.symbol_display or entry.symbol}`",
                f"- Math Name: {entry.math_name or '-'}",
                f"- Domain: `{entry.domain}`",
                f"- Category: `{entry.category or '-'}`",
                f"- Basic Translation (Tier 1 callout): {entry.basic_definition or '(missing)'}",
                f"- Medium Translation (Tier 1 appendix): {entry.medium_definition or entry.basic_definition or '(missing)'}",
                f"- Academic Translation (Tier 3 registry): {entry.academic_definition or entry.medium_definition or entry.basic_definition or '(missing)'}",
                f"- Context Notes: {entry.context_notes or '-'}",
                f"- First Appears: `{entry.first_appears or '-'}`",
                f"- Z2 Mirror: `{entry.z2_mirror or '-'}`",
                f"- Owner Folder: `{entry.owner_folder or '-'}`",
                f"- Aliases: {', '.join(f'`{a}`' for a in sorted(entry.aliases)) if entry.aliases else '-'}",
                f"- Source: `{entry.source}`",
                "",
            ]
        )

    content = "\n".join(lines) + "\n"
    if apply_changes:
        out_path.write_text(content, encoding="utf-8")
    return out_path


def write_conflict_reports(vault_root: Path, conflict_data: Dict[str, object], apply_changes: bool) -> Tuple[Path, Path]:
    md_path = vault_root / "MATH_CONFLICT_REPORT.md"
    json_path = vault_root / "MATH_CONFLICT_REPORT.json"

    summary = conflict_data.get("summary", {})
    symbol_conflicts = conflict_data.get("symbol_conflicts", [])
    unknown_symbols = conflict_data.get("unknown_symbols_by_paper", [])
    unknown_freq = conflict_data.get("unknown_symbol_frequency", [])
    unused_codes = conflict_data.get("unused_registry_codes", [])

    lines = [
        "# Math Conflict Report",
        "",
        f"- Registry entries: {summary.get('registry_entries', 0)}",
        f"- Symbol conflicts: {summary.get('symbol_conflicts', 0)}",
        f"- Papers with unknown symbols: {summary.get('papers_with_unknown_symbols', 0)}",
        f"- Unique unknown symbols: {summary.get('unique_unknown_symbols', 0)}",
        f"- Unused registry codes: {summary.get('unused_registry_codes', 0)}",
        "",
        "## Symbol Conflicts",
        "",
    ]
    if symbol_conflicts:
        for item in symbol_conflicts:
            lines.append(f"- Symbol `{item['symbol']}` -> codes: {', '.join(item['codes'])}")
    else:
        lines.append("- None")

    lines.extend(["", "## Top Unknown Symbols", ""])
    if unknown_freq:
        for symbol, count in unknown_freq[:50]:
            lines.append(f"- `{symbol}`: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Unknown Symbols By Paper", ""])
    if unknown_symbols:
        for item in unknown_symbols:
            lines.append(f"- `{item['paper']}`: {', '.join(f'`{s}`' for s in item['unknown_symbols'])}")
    else:
        lines.append("- None")

    lines.extend(["", "## Unused Registry Codes", ""])
    if unused_codes:
        for code in unused_codes:
            lines.append(f"- `{code}`")
    else:
        lines.append("- None")

    if apply_changes:
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        json_path.write_text(json.dumps(conflict_data, indent=2), encoding="utf-8")

    return md_path, json_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build three-tier math appendix architecture.")
    parser.add_argument("--vault-root", required=True, help="Vault root to scan and write outputs.")
    parser.add_argument(
        "--seed",
        default="D:/01_Axioms/04_REFERENCE/MATH_TRANSLATION_TABLE.csv",
        help="Seed registry file (CSV/YAML/JSON).",
    )
    parser.add_argument(
        "--glossary",
        default="engine/theophysics_symbol_glossary.md",
        help="Glossary markdown used as baseline registry source.",
    )
    parser.add_argument(
        "--max-paper-rows",
        type=int,
        default=DEFAULT_MAX_PAPER_ROWS,
        help="Max Tier 1 rows per paper before overflow sidecar.",
    )
    parser.add_argument(
        "--apply-paper-blocks",
        action="store_true",
        help="Actually write Tier 1 blocks into papers. Without this, scan/report only.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and print summary without writing any files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    vault_root = Path(args.vault_root)
    if not vault_root.exists():
        raise SystemExit(f"Vault root not found: {vault_root}")

    apply_changes = not args.dry_run
    seed_path = Path(args.seed) if args.seed else None
    glossary_path = Path(args.glossary) if args.glossary else Path("")

    seed_entries = load_seed_entries(seed_path)
    glossary_entries = parse_glossary_table(glossary_path)
    registry = build_registry(seed_entries, glossary_entries)

    if not registry:
        raise SystemExit("No registry entries found. Add entries to seed file or glossary.")

    paper_results, usage_map = scan_papers(vault_root, registry)
    conflict_data = collect_conflicts(registry, usage_map, paper_results)

    if apply_changes:
        write_registry_root(vault_root, registry, usage_map, apply_changes=True)
        write_folder_indexes(vault_root, paper_results, apply_changes=True)
        if args.apply_paper_blocks:
            write_paper_blocks(
                vault_root,
                paper_results,
                registry,
                max_rows=max(1, args.max_paper_rows),
                apply_changes=True,
            )
        write_conflict_reports(vault_root, conflict_data, apply_changes=True)

    print("=== Math Appendix Build Summary ===")
    print(f"Vault root: {vault_root}")
    print(f"Registry entries: {len(registry)}")
    print(f"Papers scanned: {len(paper_results)}")
    print(f"Apply changes: {apply_changes}")
    print(f"Tier 1 write enabled: {bool(args.apply_paper_blocks)}")
    print(
        "Conflicts: "
        f"{conflict_data['summary']['symbol_conflicts']} symbol conflicts, "
        f"{conflict_data['summary']['papers_with_unknown_symbols']} papers with unknown symbols, "
        f"{conflict_data['summary']['unique_unknown_symbols']} unique unknown symbols"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
