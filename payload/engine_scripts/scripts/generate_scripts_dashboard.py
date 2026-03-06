#!/usr/bin/env python3
"""
Scripts Dashboard Generator
Scans 00_SYSTEM for all scripts (.py, .ps1, .bat, .sh) and generates
a Markdown index compatible with Obsidian Dashboard Plus.

Usage:
    python generate_scripts_dashboard.py [--vault PATH] [--output PATH]

Defaults:
    --vault   O:\\_Theophysics_v3
    --output  <vault>/Dashboards/Scripts-Dashboard.md
"""

import argparse
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_EXTS = {".py", ".ps1", ".bat", ".sh"}

# Directories to scan, relative to vault root.
# Each entry: (relative_path, friendly_label, recursive)
# Set recursive=False for parent dirs whose children have their own entries.
SCRIPT_DIRS = [
    # --- Core engine (sealed internals) ---
    ("00_SYSTEM/00_ENGINE/01_ENGINE/scripts",          "Engine — Scripts",          True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/backend_scripts",  "Engine — Backend Scripts",  True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/core",             "Engine — Core Modules",     True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/engine",           "Engine — Engine Modules",   True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/launchers",        "Engine — Launchers",        True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/ui",               "Engine — UI",               True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/utility",          "Engine — Utility",          True),
    ("00_SYSTEM/00_ENGINE/01_ENGINE/TTS_Pipeline",     "Engine — TTS Pipeline",     True),
    # --- OpenAI tool bundles ---
    ("00_SYSTEM/00_ENGINE/02_OPENAI/CALL",             "OpenAI — CALL (Tagger)",    True),
    ("00_SYSTEM/00_ENGINE/02_OPENAI/CKG",              "OpenAI — CKG Scorer",       True),
    ("00_SYSTEM/00_ENGINE/02_OPENAI/DECOMPRESS",       "OpenAI — Decompressor",     True),
    ("00_SYSTEM/00_ENGINE/02_OPENAI/DOMAIN",           "OpenAI — Domain Extractor", True),
    ("00_SYSTEM/00_ENGINE/02_OPENAI/PAPER-REVIEW",     "OpenAI — Paper Review",     True),
    ("00_SYSTEM/00_ENGINE/02_OPENAI/VAULT-RATER",      "OpenAI — Vault Rater",      True),
    # --- Vault maintenance tools ---
    ("00_SYSTEM/00_ENGINE/03_VAULT_TOOLS",             "Vault Tools",               False),
    # --- Legacy / 90 staging ---
    ("00_SYSTEM/00_ENGINE/90_LEGACY",                  "Engine — Legacy",           False),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_description(path: Path) -> str:
    """Pull a one-liner description from the file's first docstring or comment."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

    lines = text.splitlines()

    # Python: look for module docstring
    if path.suffix == ".py":
        in_doc = False
        doc_lines = []
        for line in lines[:30]:
            stripped = line.strip()
            if not in_doc:
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    marker = stripped[:3]
                    # Single-line docstring
                    if stripped.count(marker) >= 2 and len(stripped) > 6:
                        return stripped.strip(marker).strip()
                    in_doc = True
                    rest = stripped[3:].strip()
                    if rest:
                        doc_lines.append(rest)
                elif stripped.startswith("#") and not stripped.startswith("#!"):
                    return stripped.lstrip("# ").strip()
            else:
                if marker in stripped:
                    rest = stripped.replace(marker, "").strip()
                    if rest:
                        doc_lines.append(rest)
                    break
                doc_lines.append(stripped)
        if doc_lines:
            return " ".join(doc_lines).strip()

    # PowerShell: look for <# ... #> or first # comment
    elif path.suffix == ".ps1":
        for line in lines[:20]:
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                return stripped.lstrip("# ").strip()

    # Batch: look for first REM or :: comment
    elif path.suffix == ".bat":
        for line in lines[:20]:
            stripped = line.strip()
            up = stripped.upper()
            if up.startswith("REM "):
                return stripped[4:].strip()
            if stripped.startswith("::"):
                return stripped[2:].strip()

    # Shell: first # comment
    elif path.suffix == ".sh":
        for line in lines[:20]:
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                return stripped.lstrip("# ").strip()

    return ""


def human_size(nbytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if nbytes < 1024:
            return f"{nbytes:.0f} {unit}" if unit == "B" else f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} GB"


def vault_wikilink(path: Path, vault_root: Path) -> str:
    """Create an Obsidian [[wikilink]] from a file path."""
    try:
        rel = path.relative_to(vault_root)
    except ValueError:
        return path.name
    # Obsidian wikilinks use forward slashes, no extension for .md but keep for scripts
    link_path = str(rel).replace("\\", "/")
    return f"[[{link_path}|{path.name}]]"


def ext_icon(ext: str) -> str:
    icons = {
        ".py":  "🐍",
        ".ps1": "⚡",
        ".bat": "📦",
        ".sh":  "🐚",
    }
    return icons.get(ext, "📄")


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_scripts(vault_root: Path):
    """Scan all configured directories and return structured results."""
    results = defaultdict(list)

    for rel_dir, label, recursive in SCRIPT_DIRS:
        scan_path = vault_root / rel_dir.replace("/", os.sep)
        if not scan_path.is_dir():
            continue

        if recursive:
            walker = os.walk(scan_path)
        else:
            # Non-recursive: only direct children
            walker = [(str(scan_path), [], os.listdir(scan_path))]

        for root, _dirs, files in walker:
            root_path = Path(root)
            # Skip venv, __pycache__, node_modules, .git
            if any(skip in root_path.parts for skip in
                   ("venv", "__pycache__", "node_modules", ".git", "env")):
                continue

            for fname in sorted(files):
                fpath = root_path / fname
                if fpath.suffix.lower() not in SCRIPT_EXTS:
                    continue
                if not fpath.is_file():
                    continue

                stat = fpath.stat()
                desc = extract_description(fpath)
                results[label].append({
                    "path": fpath,
                    "name": fname,
                    "ext": fpath.suffix.lower(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                    "description": desc,
                })

    return results


# ---------------------------------------------------------------------------
# Dashboard Generator
# ---------------------------------------------------------------------------

def generate_dashboard(results: dict, vault_root: Path) -> str:
    """Generate Markdown dashboard content."""
    lines = []

    # YAML front matter for Dashboard Plus
    lines.append("---")
    lines.append("cssclasses:")
    lines.append("  - dashboard")
    lines.append(f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("---")
    lines.append("")

    # Header
    lines.append("# Scripts Dashboard")
    lines.append("")

    # Summary stats
    total_scripts = sum(len(v) for v in results.values())
    total_size = sum(s["size"] for v in results.values() for s in v)
    ext_counts = defaultdict(int)
    for v in results.values():
        for s in v:
            ext_counts[s["ext"]] += 1

    lines.append("> [!info] Vault Scripts Overview")
    lines.append(f"> **{total_scripts}** scripts across **{len(results)}** directories — {human_size(total_size)} total")
    lines.append(">")
    ext_summary = " | ".join(
        f"{ext_icon(ext)} `{ext}`: **{count}**"
        for ext, count in sorted(ext_counts.items(), key=lambda x: -x[1])
    )
    lines.append(f"> {ext_summary}")
    lines.append("")

    # Table of contents
    lines.append("## Sections")
    lines.append("")
    for label in results:
        anchor = label.lower().replace(" ", "-").replace("—", "").replace("--", "-").strip("-")
        count = len(results[label])
        lines.append(f"- [[#^{anchor}|{label}]] ({count})")
    lines.append("")

    # Per-section tables
    for label, scripts in results.items():
        if not scripts:
            continue

        anchor = label.lower().replace(" ", "-").replace("—", "").replace("--", "-").strip("-")
        section_size = sum(s["size"] for s in scripts)
        lines.append(f"## {label}")
        lines.append(f"^{anchor}")
        lines.append("")
        lines.append(f"> {len(scripts)} scripts — {human_size(section_size)}")
        lines.append("")

        # Table header
        lines.append("| | Script | Description | Size | Modified |")
        lines.append("|---|---|---|---|---|")

        for s in sorted(scripts, key=lambda x: x["name"].lower()):
            icon = ext_icon(s["ext"])
            link = vault_wikilink(s["path"], vault_root)
            desc = s["description"][:80] if s["description"] else "—"
            # Escape pipe characters in description
            desc = desc.replace("|", "\\|")
            size = human_size(s["size"])
            mod = s["modified"].strftime("%Y-%m-%d")
            lines.append(f"| {icon} | {link} | {desc} | {size} | {mod} |")

        lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Auto-generated by `generate_scripts_dashboard.py` on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate Scripts Dashboard for Obsidian")
    parser.add_argument("--vault", default=r"O:\_Theophysics_v3",
                        help="Vault root path")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: <vault>/Dashboards/Scripts-Dashboard.md)")
    args = parser.parse_args()

    vault_root = Path(args.vault)
    if not vault_root.is_dir():
        print(f"ERROR: Vault root not found: {vault_root}")
        return 1

    output_path = Path(args.output) if args.output else vault_root / "00_SYSTEM" / "01_ENGINE" / "legacy_scripts" / "Dashboards" / "Scripts-Dashboard.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Scanning scripts in: {vault_root}")
    results = scan_scripts(vault_root)

    total = sum(len(v) for v in results.values())
    if total == 0:
        print("WARNING: No scripts found. Check SCRIPT_DIRS configuration.")
        return 1

    for label, scripts in results.items():
        print(f"  {label}: {len(scripts)} scripts")

    dashboard = generate_dashboard(results, vault_root)
    output_path.write_text(dashboard, encoding="utf-8", newline="\n")
    print(f"\nDashboard written to: {output_path}")
    print(f"Total: {total} scripts indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
