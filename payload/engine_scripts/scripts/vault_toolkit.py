#!/usr/bin/env python3
"""
Vault Toolkit — Unified Obsidian Vault Analysis & Maintenance
==============================================================
One script, five modes:

  clean    — Encoding & whitespace fixes (CRLF, BOM, nulls, invisible chars)
  health   — Broken links, dead assets, orphans, largest files report
  bloat    — Find & move oversized / binary files out of vault
  graph    — NetworkX graph analysis (centrality, clusters, hubs) via obsidiantools
  full     — Run everything and produce a comprehensive report

Usage:
    python vault_toolkit.py clean  [--fix] [--filenames] [PATH]
    python vault_toolkit.py health [PATH]
    python vault_toolkit.py bloat  [--move] [--staging DIR] [PATH]
    python vault_toolkit.py graph  [--top N] [PATH]
    python vault_toolkit.py full   [PATH]
    python vault_toolkit.py        (interactive menu)

Lightweight modes (clean, health, bloat) use stdlib only.
Graph mode lazy-imports obsidiantools + pandas + networkx.
"""

import os
import re
import sys
import shutil
import argparse
import datetime
import hashlib
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# ─── Constants ────────────────────────────────────────────────────────────────

SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "__pycache__",
             ".venv", "venv", ".DUPLICATE_TRASH", ".DUPLICATE_TRASH_PHASE2"}

TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".csv",
                   ".xml", ".ini", ".ps1", ".bat", ".cmd", ".py",
                   ".ts", ".js", ".sh", ".log", ".css", ".html"}

BLOAT_EXTENSIONS = {".csv", ".docx", ".pdf", ".xlsx", ".xlsm", ".xls",
                    ".mp3", ".mp4", ".wav", ".ogg", ".zip", ".rar",
                    ".pptx", ".exe", ".dll", ".iso"}

ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp",
              ".pdf", ".mp3", ".mp4", ".wav", ".ogg", ".zip", ".xlsx", ".csv"}

INVISIBLE_CHARS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u200e": "LEFT-TO-RIGHT MARK",
    "\u200f": "RIGHT-TO-LEFT MARK",
    "\u2060": "WORD JOINER",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\ufeff": "BOM / ZERO WIDTH NO-BREAK SPACE",
    "\u00ad": "SOFT HYPHEN",
    "\u034f": "COMBINING GRAPHEME JOINER",
    "\u061c": "ARABIC LETTER MARK",
    "\u180e": "MONGOLIAN VOWEL SEPARATOR",
    "\u2028": "LINE SEPARATOR",
    "\u2029": "PARAGRAPH SEPARATOR",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2066": "LEFT-TO-RIGHT ISOLATE",
    "\u2067": "RIGHT-TO-LEFT ISOLATE",
    "\u2068": "FIRST STRONG ISOLATE",
    "\u2069": "POP DIRECTIONAL ISOLATE",
}

INVISIBLE_REGEX = re.compile("[" + "".join(INVISIBLE_CHARS.keys()) + "]")
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+?)?\]\]')
EMBED_RE = re.compile(r'!\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]')
MD_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 1: CLEAN — Encoding & Whitespace Normalizer
# ═══════════════════════════════════════════════════════════════════════════════

class CleanResult:
    def __init__(self, path: str):
        self.path = path
        self.crlf = 0
        self.bom = False
        self.nulls = 0
        self.invisible = Counter()
        self.excess_blanks = 0
        self.trailing_ws = 0
        self.no_final_newline = False
        self.error = None

    @property
    def dirty(self) -> bool:
        return (self.crlf > 0 or self.bom or self.nulls > 0 or
                len(self.invisible) > 0 or self.excess_blanks > 0 or
                self.trailing_ws > 0 or self.no_final_newline)

    def summary(self) -> str:
        parts = []
        if self.bom: parts.append("BOM")
        if self.crlf: parts.append(f"CRLF({self.crlf})")
        if self.nulls: parts.append(f"NULL({self.nulls})")
        if self.invisible:
            parts.append(f"INVIS({sum(self.invisible.values())})")
        if self.trailing_ws: parts.append(f"TRAIL({self.trailing_ws})")
        if self.excess_blanks: parts.append(f"BLANKS({self.excess_blanks})")
        if self.no_final_newline: parts.append("NO_EOF_NL")
        return " | ".join(parts) if parts else "clean"


def scan_file(filepath: str) -> CleanResult:
    result = CleanResult(filepath)
    try:
        raw = Path(filepath).read_bytes()
    except Exception as e:
        result.error = str(e)
        return result

    if raw.startswith(b"\xef\xbb\xbf"):
        result.bom = True
        raw = raw[3:]

    null_count = raw.count(b"\x00")
    if null_count:
        result.nulls = null_count
        raw = raw.replace(b"\x00", b"")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception as e:
            result.error = f"Decode failed: {e}"
            return result

    result.crlf = text.count("\r\n")

    for match in INVISIBLE_REGEX.finditer(text):
        ch = match.group()
        name = INVISIBLE_CHARS.get(ch, f"U+{ord(ch):04X}")
        result.invisible[name] += 1

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    consecutive_blanks = 0
    for line in lines:
        stripped = line.rstrip()
        if line != stripped and line.strip():
            result.trailing_ws += 1
        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks > 2:
                result.excess_blanks += 1
        else:
            consecutive_blanks = 0

    if text and not text.endswith("\n"):
        result.no_final_newline = True

    return result


def fix_file(filepath: str) -> CleanResult:
    result = scan_file(filepath)
    if result.error or not result.dirty:
        return result

    try:
        raw = Path(filepath).read_bytes()
    except Exception as e:
        result.error = str(e)
        return result

    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    raw = raw.replace(b"\x00", b"")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = INVISIBLE_REGEX.sub("", text)

    lines = text.split("\n")
    cleaned_lines = []
    consecutive_blanks = 0
    for line in lines:
        stripped = line.rstrip()
        if stripped == "":
            consecutive_blanks += 1
            if consecutive_blanks <= 2:
                cleaned_lines.append("")
        else:
            consecutive_blanks = 0
            cleaned_lines.append(stripped)

    text = "\n".join(cleaned_lines)
    text = text.rstrip("\n") + "\n"
    Path(filepath).write_bytes(text.encode("utf-8"))
    return result


def run_clean(target: str, mode: str = "scan", do_filenames: bool = False):
    target_path = Path(target)
    if not target_path.exists():
        print(f"  ERROR: Path not found: {target}")
        return

    print()
    print("=" * 70)
    print(f"  CLEAN — {'SCAN (dry run)' if mode == 'scan' else 'FIX (applying changes)'}")
    print("=" * 70)
    print(f"  Target: {target_path}")
    print("=" * 70)
    print()

    files = []
    for dirpath, dirnames, filenames in os.walk(target_path, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if Path(f).suffix.lower() in TEXT_EXTENSIONS:
                files.append(str(Path(dirpath) / f))

    print(f"  Found {len(files):,} files to process\n")
    if not files:
        print("  Nothing to do.")
        return {}

    results = []
    dirty_count = error_count = 0

    for i, fpath in enumerate(files, 1):
        r = fix_file(fpath) if mode == "fix" else scan_file(fpath)
        results.append(r)
        if r.error: error_count += 1
        elif r.dirty: dirty_count += 1
        if i % 500 == 0 or i == len(files):
            print(f"  [{i:,}/{len(files):,}] processed...", end="\r")

    print(f"  [{len(files):,}/{len(files):,}] done.          ")

    # Filename check
    if do_filenames:
        print(f"\n  Scanning filenames...")
        fn_issues = []
        for dirpath, dirnames, filenames in os.walk(target_path, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for d in dirnames:
                if d.strip() != d:
                    fn_issues.append(("folder", str(Path(dirpath) / d), d, d.strip()))
            for f in filenames:
                if f.strip() != f:
                    fn_issues.append(("file", str(Path(dirpath) / f), f, f.strip()))

        if fn_issues and mode == "fix":
            fn_issues.sort(key=lambda x: len(x[1]), reverse=True)
            fixed = 0
            for typ, path, orig, clean in fn_issues:
                old = Path(path)
                new = old.parent / clean
                if old.exists() and not new.exists():
                    try:
                        old.rename(new)
                        fixed += 1
                    except Exception as e:
                        print(f"    ERROR: {e}")
            print(f"  Fixed {fixed} filename(s)")
        elif fn_issues:
            print(f"  Found {len(fn_issues)} filename issue(s) (run with --fix to rename)")
        else:
            print("  All filenames clean!")

    # Summary
    totals = {
        "files_scanned": len(files),
        "files_dirty": dirty_count,
        "errors": error_count,
        "crlf": sum(r.crlf for r in results),
        "bom": sum(1 for r in results if r.bom),
        "nulls": sum(r.nulls for r in results),
        "invisible": sum(sum(r.invisible.values()) for r in results),
        "trailing_ws": sum(r.trailing_ws for r in results),
        "excess_blanks": sum(r.excess_blanks for r in results),
        "no_final_nl": sum(1 for r in results if r.no_final_newline),
    }

    action = "Fixed" if mode == "fix" else "Found"
    print()
    print("=" * 70)
    print(f"  CLEAN SUMMARY")
    print("=" * 70)
    print(f"  Files scanned:       {totals['files_scanned']:,}")
    print(f"  Files with issues:   {totals['files_dirty']:,}")
    print(f"  Errors:              {totals['errors']:,}")
    print(f"  {action}: CRLF:        {totals['crlf']:,}")
    print(f"  {action}: BOM:         {totals['bom']:,}")
    print(f"  {action}: Null bytes:  {totals['nulls']:,}")
    print(f"  {action}: Invisible:   {totals['invisible']:,}")
    print(f"  {action}: Trail WS:    {totals['trailing_ws']:,}")
    print(f"  {action}: Blank lines: {totals['excess_blanks']:,}")
    print(f"  {action}: Missing NL:  {totals['no_final_nl']:,}")
    print("=" * 70)
    return totals


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 2: HEALTH — Broken Links, Dead Assets, Largest Files
# ═══════════════════════════════════════════════════════════════════════════════

class VaultIndex:
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.md_files = []
        self.all_files = []
        self.name_map = defaultdict(list)
        self.full_name_map = defaultdict(list)
        self._index()

    def _index(self):
        for p in self.vault.rglob("*"):
            if p.is_file():
                parts = p.relative_to(self.vault).parts
                if any(part in SKIP_DIRS for part in parts):
                    continue
                self.all_files.append(p)
                self.name_map[p.stem.lower()].append(p)
                self.full_name_map[p.name.lower()].append(p)
                if p.suffix.lower() == ".md":
                    self.md_files.append(p)

    def resolve_wikilink(self, target: str) -> bool:
        t = target.strip().lower()
        if not t: return True
        if t in self.name_map: return True
        if t in self.full_name_map: return True
        if (t + ".md") in self.full_name_map: return True
        if t.replace(" ", "_") in self.name_map: return True
        if t.replace("_", " ") in self.name_map: return True
        if "/" in target:
            leaf = target.replace("\\", "/").split("/")[-1].lower()
            if leaf in self.name_map or leaf in self.full_name_map:
                return True
        return False

    def resolve_embed(self, target: str) -> bool:
        t = target.strip().lower()
        if not t: return True
        if t in self.full_name_map or t in self.name_map:
            return True
        if "/" in target:
            leaf = target.replace("\\", "/").split("/")[-1].lower()
            if leaf in self.full_name_map: return True
        return False


def run_health(vault_path: str):
    vault = Path(vault_path)
    print(f"\n  Indexing vault: {vault}")
    index = VaultIndex(str(vault))
    print(f"  {len(index.all_files):,} files ({len(index.md_files):,} markdown)")

    # Broken links
    print("  Scanning broken links...")
    broken = []
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except: continue
        rel = md.relative_to(vault)
        for line_num, line in enumerate(content.splitlines(), 1):
            for m in WIKILINK_RE.finditer(line):
                target = m.group(1).strip()
                if not index.resolve_wikilink(target):
                    broken.append({"file": str(rel), "line": line_num, "target": target})
    print(f"    {len(broken):,} broken links")

    # Dead assets
    print("  Scanning dead assets...")
    dead = []
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except: continue
        rel = md.relative_to(vault)
        for line_num, line in enumerate(content.splitlines(), 1):
            for m in EMBED_RE.finditer(line):
                target = m.group(1).strip()
                if not index.resolve_embed(target):
                    dead.append({"file": str(rel), "line": line_num, "target": target})
            for m in MD_IMAGE_RE.finditer(line):
                target = m.group(1).strip()
                if target.startswith("http"): continue
                if not index.resolve_embed(target):
                    dead.append({"file": str(rel), "line": line_num, "target": target})
    print(f"    {len(dead):,} dead asset refs")

    # Orphans
    print("  Finding orphans...")
    referenced = set()
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except: continue
        for m in WIKILINK_RE.finditer(content):
            t = m.group(1).strip().lower()
            if "/" in t: t = t.split("/")[-1]
            referenced.add(t)
            referenced.add(t.replace(" ", "_"))
            referenced.add(t.replace("_", " "))
        for m in EMBED_RE.finditer(content):
            t = m.group(1).strip().lower()
            if "/" in t: t = t.split("/")[-1]
            referenced.add(t)

    orphans = []
    skip_names = {"readme", "overview", "index", "_vault_health", "manifest"}
    for md in index.md_files:
        s = md.stem.lower()
        if s in skip_names: continue
        if not (s in referenced or md.name.lower() in referenced or
                s.replace("_", " ") in referenced or
                s.replace(" ", "_") in referenced or
                s.replace("-", " ") in referenced):
            orphans.append(md)
    print(f"    {len(orphans):,} orphan files")

    # Stats
    print("  Computing stats...")
    total_size = sum(f.stat().st_size for f in index.all_files)
    md_size = sum(f.stat().st_size for f in index.md_files)
    ext_counts = Counter()
    ext_sizes = Counter()
    for f in index.all_files:
        ext = f.suffix.lower() or "(no ext)"
        ext_counts[ext] += 1
        ext_sizes[ext] += f.stat().st_size

    largest = sorted(index.all_files, key=lambda f: f.stat().st_size, reverse=True)[:20]

    folder_counts = Counter()
    for f in index.all_files:
        rel = f.relative_to(vault)
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        folder_counts[top] += 1

    # YAML stats
    files_with_yaml = files_without_yaml = 0
    status_counts = Counter()
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except: continue
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                files_with_yaml += 1
                yaml_block = content[3:end]
                for line in yaml_block.splitlines():
                    ls = line.strip()
                    if ls.startswith("status:"):
                        status = ls.split(":", 1)[1].strip().strip("'\"")
                        if status: status_counts[status] += 1
            else:
                files_without_yaml += 1
        else:
            files_without_yaml += 1

    # Write report
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report_path = vault / "_VAULT_HEALTH.md"
    fmt = lambda n: (f"{n/1073741824:.2f} GB" if n >= 1073741824 else
                     f"{n/1048576:.1f} MB" if n >= 1048576 else
                     f"{n/1024:.1f} KB" if n >= 1024 else f"{n} B")

    lines = [
        f"# Vault Health Report",
        f"**Generated:** {now}  ",
        f"**Vault:** `{vault}`  ",
        f"**Tool:** vault_toolkit.py",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total files | {len(index.all_files):,} |",
        f"| Markdown files | {len(index.md_files):,} |",
        f"| Total size | {fmt(total_size)} |",
        f"| Markdown size | {fmt(md_size)} |",
        f"| Files with YAML | {files_with_yaml:,} |",
        f"| Files without YAML | {files_without_yaml:,} |",
        f"| Broken links | {len(broken):,} |",
        f"| Dead asset refs | {len(dead):,} |",
        f"| Orphan files | {len(orphans):,} |",
        "",
        "## Folder Breakdown",
        "",
        "| Folder | Files |",
        "|--------|-------|",
    ]
    for folder, count in folder_counts.most_common(25):
        lines.append(f"| `{folder}` | {count:,} |")
    lines += ["", "## File Types", "", "| Extension | Count | Size |",
              "|-----------|-------|------|"]
    for ext, count in ext_counts.most_common(25):
        lines.append(f"| `{ext}` | {count:,} | {fmt(ext_sizes.get(ext, 0))} |")
    lines += ["", "## Largest Files", "", "| Size | File |", "|------|------|"]
    for f in largest:
        rel = f.relative_to(vault)
        lines.append(f"| {fmt(f.stat().st_size)} | `{rel}` |")

    lines += [
        "",
        f"## Broken Links ({len(broken):,})",
        "",
    ]
    if broken:
        lines += ["| File | Line | Target |", "|------|------|--------|"]
        for b in broken[:200]:
            lines.append(f"| `{b['file']}` | {b['line']} | `{b['target']}` |")
        if len(broken) > 200:
            lines.append(f"| ... | ... | *({len(broken)-200:,} more)* |")
    else:
        lines.append("No broken links found.")

    lines += ["", f"## Dead Asset References ({len(dead):,})", ""]
    if dead:
        lines += ["| File | Line | Missing Asset |", "|------|------|---------------|"]
        for d in dead[:200]:
            lines.append(f"| `{d['file']}` | {d['line']} | `{d['target']}` |")
        if len(dead) > 200:
            lines.append(f"| ... | ... | *({len(dead)-200:,} more)* |")

    lines += ["", f"## Orphan Files ({len(orphans):,})", ""]
    if orphans:
        lines.append("Files never referenced by any `[[wikilink]]` or embed:")
        lines.append("")
        for o in sorted(orphans, key=lambda p: p.relative_to(vault))[:200]:
            lines.append(f"- `{o.relative_to(vault)}`")
        if len(orphans) > 200:
            lines.append(f"- *...and {len(orphans)-200:,} more*")

    if status_counts:
        lines += ["", "## Status Breakdown", "", "| Status | Count |", "|--------|-------|"]
        for status, count in status_counts.most_common(15):
            lines.append(f"| `{status}` | {count:,} |")

    lines.append("")
    report_text = "\n".join(lines)
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\n  Report saved: {report_path}")
    print(f"  ({len(report_text):,} chars)")

    return {
        "broken": len(broken), "dead": len(dead), "orphans": len(orphans),
        "total_files": len(index.all_files), "md_files": len(index.md_files),
        "total_size": total_size
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 3: BLOAT — Find & Move Oversized / Binary Files
# ═══════════════════════════════════════════════════════════════════════════════

def run_bloat(vault_path: str, move: bool = False,
              staging: str = None, size_threshold_mb: float = 1.0):
    vault = Path(vault_path)
    if staging is None:
        staging = str(vault.parent / "_VAULT_BLOAT_STAGING")
    staging_path = Path(staging)

    print(f"\n  Scanning for bloat in: {vault}")
    print(f"  Threshold: > {size_threshold_mb} MB or binary extension")

    bloat_files = []
    for dirpath, dirnames, filenames in os.walk(vault, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            fp = Path(dirpath) / f
            ext = fp.suffix.lower()
            try:
                size = fp.stat().st_size
            except:
                continue

            is_bloat_ext = ext in BLOAT_EXTENSIONS
            is_oversized = size > (size_threshold_mb * 1048576)

            if is_bloat_ext or is_oversized:
                bloat_files.append({
                    "path": fp,
                    "rel": fp.relative_to(vault),
                    "size": size,
                    "ext": ext,
                    "reason": "ext" if is_bloat_ext else "size",
                })

    bloat_files.sort(key=lambda x: -x["size"])
    total_bloat = sum(f["size"] for f in bloat_files)
    fmt = lambda n: (f"{n/1073741824:.2f} GB" if n >= 1073741824 else
                     f"{n/1048576:.1f} MB" if n >= 1048576 else
                     f"{n/1024:.1f} KB" if n >= 1024 else f"{n} B")

    # Group by extension
    ext_summary = Counter()
    ext_size = Counter()
    for f in bloat_files:
        ext_summary[f["ext"]] += 1
        ext_size[f["ext"]] += f["size"]

    print(f"\n  Found {len(bloat_files):,} bloat files ({fmt(total_bloat)})")
    print()
    print("  By extension:")
    for ext, count in ext_summary.most_common():
        print(f"    {ext:8s}  {count:4d} files  {fmt(ext_size[ext]):>10s}")

    print(f"\n  Top 20 largest:")
    for f in bloat_files[:20]:
        print(f"    {fmt(f['size']):>10s}  {f['rel']}")

    if move and bloat_files:
        print(f"\n  Moving {len(bloat_files):,} files to: {staging_path}")
        staging_path.mkdir(parents=True, exist_ok=True)
        moved = errors = 0
        moved_bytes = 0
        for f in bloat_files:
            dst = staging_path / f["rel"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(f["path"]), str(dst))
                moved += 1
                moved_bytes += f["size"]
            except Exception as e:
                print(f"    ERROR: {f['rel']}: {e}")
                errors += 1

        print(f"\n  Moved: {moved:,} files ({fmt(moved_bytes)})")
        if errors:
            print(f"  Errors: {errors}")
    elif not move and bloat_files:
        print(f"\n  Run with --move to relocate these files")

    return {"count": len(bloat_files), "total_bytes": total_bloat}


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 4: GRAPH — NetworkX Analysis via obsidiantools
# ═══════════════════════════════════════════════════════════════════════════════

def run_graph(vault_path: str, top_n: int = 25):
    print(f"\n  Loading obsidiantools...")
    try:
        import obsidiantools.api as otools
        import networkx as nx
        import pandas as pd
    except ImportError as e:
        print(f"  ERROR: Missing dependency: {e}")
        print(f"  Install with: pip install obsidiantools")
        return None

    vault = Path(vault_path)
    print(f"  Building graph for: {vault}")
    print(f"  (This may take a while on large vaults...)")

    v = otools.Vault(vault).connect()

    G = v.graph
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()

    print(f"\n  Graph: {n_nodes:,} nodes, {n_edges:,} edges")
    print(f"  Isolated notes: {len(v.isolated_notes):,}")
    print(f"  Nonexistent notes: {len(v.nonexistent_notes):,}")

    # Degree centrality (most connected)
    print(f"\n  Top {top_n} most-connected notes (by degree):")
    degree = dict(G.degree())
    top_degree = sorted(degree.items(), key=lambda x: -x[1])[:top_n]
    for name, deg in top_degree:
        print(f"    {deg:5d}  {name}")

    # In-degree (most backlinked)
    print(f"\n  Top {top_n} most-backlinked notes:")
    in_degree = dict(G.in_degree())
    top_in = sorted(in_degree.items(), key=lambda x: -x[1])[:top_n]
    for name, deg in top_in:
        print(f"    {deg:5d}  {name}")

    # PageRank
    print(f"\n  Top {top_n} by PageRank (authority):")
    try:
        pr = nx.pagerank(G)
        top_pr = sorted(pr.items(), key=lambda x: -x[1])[:top_n]
        for name, score in top_pr:
            print(f"    {score:.6f}  {name}")
    except Exception as e:
        print(f"    (PageRank failed: {e})")

    # Connected components (weakly, since directed)
    components = list(nx.weakly_connected_components(G))
    components.sort(key=len, reverse=True)
    print(f"\n  Connected components: {len(components):,}")
    print(f"    Largest: {len(components[0]):,} nodes")
    if len(components) > 1:
        print(f"    2nd: {len(components[1]):,} nodes")
    small = sum(1 for c in components if len(c) == 1)
    print(f"    Singletons: {small:,}")

    # Export metadata
    try:
        df = v.get_note_metadata()
        csv_path = vault / "00_SYSTEM" / "01_ENGINE" / "scripts" / "output" / "vault_graph_metadata.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(str(csv_path))
        print(f"\n  Metadata CSV exported: {csv_path}")
        print(f"    {len(df):,} notes × {len(df.columns)} columns")
    except Exception as e:
        print(f"\n  CSV export failed: {e}")

    return {
        "nodes": n_nodes, "edges": n_edges,
        "isolated": len(v.isolated_notes),
        "nonexistent": len(v.nonexistent_notes),
        "components": len(components),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  MODULE 5: FULL — Run Everything
# ═══════════════════════════════════════════════════════════════════════════════

def run_full(vault_path: str):
    print()
    print("=" * 70)
    print("  VAULT TOOLKIT — FULL ANALYSIS")
    print("=" * 70)

    print("\n  [1/4] Running CLEAN scan...")
    clean_stats = run_clean(vault_path, mode="scan")

    print("\n  [2/4] Running HEALTH report...")
    health_stats = run_health(vault_path)

    print("\n  [3/4] Running BLOAT scan...")
    bloat_stats = run_bloat(vault_path, move=False)

    print("\n  [4/4] Running GRAPH analysis...")
    print("  (Skipping graph in full mode — run separately with: vault_toolkit.py graph)")

    print()
    print("=" * 70)
    print("  FULL ANALYSIS COMPLETE")
    print("=" * 70)


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

def detect_vault() -> str:
    """Try to auto-detect vault path from script location."""
    script_dir = Path(__file__).resolve().parent
    check = script_dir
    for _ in range(10):
        if (check / ".obsidian").exists():
            return str(check)
        check = check.parent
    return None


def interactive_menu():
    vault = detect_vault()
    print()
    print("=" * 60)
    print("  Vault Toolkit — Unified Analysis & Maintenance")
    print("=" * 60)
    if vault:
        print(f"  Vault: {vault}")
    print()
    print("  1) Clean — Scan encoding issues (dry run)")
    print("  2) Clean — Fix encoding issues")
    print("  3) Health — Full health report")
    print("  4) Bloat — Find large / binary files")
    print("  5) Bloat — Find & MOVE large files out")
    print("  6) Graph — NetworkX analysis (slow on large vaults)")
    print("  7) Full — Run everything")
    print("  Q) Quit")
    print()
    choice = input("  Select: ").strip().upper()

    if not vault:
        vault = input("  Vault path: ").strip().strip('"')

    if choice == "1":
        run_clean(vault, mode="scan")
    elif choice == "2":
        confirm = input(f"  Fix files in {vault}? (Y/n): ").strip().lower()
        if confirm != "n":
            run_clean(vault, mode="fix", do_filenames=True)
    elif choice == "3":
        run_health(vault)
    elif choice == "4":
        run_bloat(vault, move=False)
    elif choice == "5":
        run_bloat(vault, move=True)
    elif choice == "6":
        run_graph(vault)
    elif choice == "7":
        run_full(vault)
    else:
        print("  Bye.")


def main():
    parser = argparse.ArgumentParser(
        description="Vault Toolkit — Unified Obsidian Analysis & Maintenance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
modes:
  clean    Encoding & whitespace normalizer
  health   Broken links, dead assets, orphans, file stats
  bloat    Find & move oversized / binary files
  graph    NetworkX graph analysis via obsidiantools
  full     Run clean-scan + health + bloat-scan
        """)
    parser.add_argument("mode", nargs="?", default=None,
                        choices=["clean", "health", "bloat", "graph", "full"],
                        help="Analysis mode")
    parser.add_argument("path", nargs="?", default=None,
                        help="Vault path (auto-detected if omitted)")
    parser.add_argument("--fix", action="store_true",
                        help="Apply fixes (clean mode)")
    parser.add_argument("--filenames", action="store_true",
                        help="Also fix filename spacing (clean mode)")
    parser.add_argument("--move", action="store_true",
                        help="Move bloat files to staging (bloat mode)")
    parser.add_argument("--staging", default=None,
                        help="Staging directory for bloat (default: ../_VAULT_BLOAT_STAGING)")
    parser.add_argument("--top", type=int, default=25,
                        help="Top N results for graph analysis (default: 25)")

    args = parser.parse_args()

    if args.mode is None:
        interactive_menu()
        return

    vault = args.path or detect_vault()
    if not vault:
        print("ERROR: Could not detect vault. Specify path as argument.")
        sys.exit(1)

    if not Path(vault).exists():
        print(f"ERROR: Path not found: {vault}")
        sys.exit(1)

    if args.mode == "clean":
        mode = "fix" if args.fix else "scan"
        run_clean(vault, mode=mode, do_filenames=args.filenames)
    elif args.mode == "health":
        run_health(vault)
    elif args.mode == "bloat":
        run_bloat(vault, move=args.move, staging=args.staging)
    elif args.mode == "graph":
        run_graph(vault, top_n=args.top)
    elif args.mode == "full":
        run_full(vault)


if __name__ == "__main__":
    main()
