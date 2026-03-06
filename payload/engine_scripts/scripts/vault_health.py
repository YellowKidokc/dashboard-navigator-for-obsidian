#!/usr/bin/env python3
"""
Vault Health Tool
=================
Three tools in one:
  1) Broken Link Scanner — finds [[wikilinks]] pointing to non-existent files
  2) Dead Asset Finder   — finds image/file embeds that no longer exist
  3) Vault Health Report  — full dashboard written to _VAULT_HEALTH.md

Usage:
    python vault_health.py                  (interactive menu)
    python vault_health.py --scan           (broken links only)
    python vault_health.py --assets         (dead assets only)
    python vault_health.py --report         (full health report)
    python vault_health.py --all            (everything)
    python vault_health.py --vault PATH     (specify vault path)
"""

import os
import re
import sys
import argparse
import datetime
from pathlib import Path
from collections import Counter, defaultdict

# ─── Config ───────────────────────────────────────────────────────────────────

SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules", "__pycache__"}

# Wikilink patterns
# [[Target]]  [[Target|Alias]]  [[Target#heading]]  [[Target#heading|Alias]]
WIKILINK_RE = re.compile(r'\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+?)?\]\]')

# Embed patterns  ![[image.png]]  ![[file.pdf]]
EMBED_RE = re.compile(r'!\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]')

# Markdown image  ![alt](path)
MD_IMAGE_RE = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')

# Image/asset extensions
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp",
              ".pdf", ".mp3", ".mp4", ".wav", ".ogg", ".zip", ".xlsx", ".csv"}


# ─── Vault Index ──────────────────────────────────────────────────────────────

class VaultIndex:
    """Indexes all files in the vault for fast lookup."""

    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.md_files: list[Path] = []          # all .md files
        self.all_files: list[Path] = []         # every file
        self.name_map: dict[str, list[Path]] = defaultdict(list)  # stem -> paths
        self.full_name_map: dict[str, list[Path]] = defaultdict(list)  # name+ext -> paths

        self._index()

    def _should_skip(self, path: Path) -> bool:
        parts = path.relative_to(self.vault).parts
        return any(p in SKIP_DIRS for p in parts)

    def _index(self):
        for p in self.vault.rglob("*"):
            if p.is_file() and not self._should_skip(p):
                self.all_files.append(p)
                self.name_map[p.stem.lower()].append(p)
                self.full_name_map[p.name.lower()].append(p)
                if p.suffix.lower() == ".md":
                    self.md_files.append(p)

    def resolve_wikilink(self, target: str) -> bool:
        """Check if a wikilink target resolves to any file."""
        target_clean = target.strip()
        if not target_clean:
            return True  # empty link, not a "broken" link per se

        t_lower = target_clean.lower()

        # 1. Exact match by stem (most common for [[Note Name]])
        if t_lower in self.name_map:
            return True

        # 2. Exact match by full name (for [[file.pdf]] style links)
        if t_lower in self.full_name_map:
            return True

        # 3. Check with .md appended
        if (t_lower + ".md") in self.full_name_map:
            return True
        if t_lower.replace(" ", "_") in self.name_map:
            return True
        if t_lower.replace("_", " ") in self.name_map:
            return True

        # 4. Path-style link: folder/Note Name
        if "/" in target_clean:
            # Try as relative path
            parts = target_clean.replace("\\", "/").split("/")
            leaf = parts[-1].lower()
            if leaf in self.name_map or (leaf + ".md") in self.full_name_map:
                return True
            if leaf in self.full_name_map:
                return True

        return False

    def resolve_embed(self, target: str) -> bool:
        """Check if an embed target resolves to any file."""
        target_clean = target.strip()
        if not target_clean:
            return True

        t_lower = target_clean.lower()

        # Direct name match
        if t_lower in self.full_name_map:
            return True
        if t_lower in self.name_map:
            return True

        # Path-style
        if "/" in target_clean:
            leaf = target_clean.replace("\\", "/").split("/")[-1].lower()
            if leaf in self.full_name_map:
                return True

        return False

    def find_referenced_files(self) -> set[str]:
        """Return set of all file stems/names referenced by any link or embed."""
        referenced = set()
        for md in self.md_files:
            try:
                content = md.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            for m in WIKILINK_RE.finditer(content):
                target = m.group(1).strip().lower()
                if "/" in target:
                    target = target.split("/")[-1]
                referenced.add(target)
                referenced.add(target.replace(" ", "_"))
                referenced.add(target.replace("_", " "))

            for m in EMBED_RE.finditer(content):
                target = m.group(1).strip().lower()
                if "/" in target:
                    target = target.split("/")[-1]
                referenced.add(target)

            for m in MD_IMAGE_RE.finditer(content):
                target = m.group(1).strip().lower()
                if "/" in target:
                    target = target.split("/")[-1]
                referenced.add(target)

        return referenced


# ─── Scanners ─────────────────────────────────────────────────────────────────

def scan_broken_links(index: VaultIndex) -> list[dict]:
    """Find all broken wikilinks."""
    broken = []
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel = md.relative_to(index.vault)
        for line_num, line in enumerate(content.splitlines(), 1):
            for m in WIKILINK_RE.finditer(line):
                target = m.group(1).strip()
                if not index.resolve_wikilink(target):
                    broken.append({
                        "file": str(rel),
                        "line": line_num,
                        "target": target,
                        "type": "wikilink",
                    })

    return broken


def scan_dead_assets(index: VaultIndex) -> list[dict]:
    """Find all embed references to missing files."""
    dead = []
    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        rel = md.relative_to(index.vault)
        for line_num, line in enumerate(content.splitlines(), 1):
            # ![[embeds]]
            for m in EMBED_RE.finditer(line):
                target = m.group(1).strip()
                if not index.resolve_embed(target):
                    dead.append({
                        "file": str(rel),
                        "line": line_num,
                        "target": target,
                        "type": "embed",
                    })

            # ![alt](path) markdown images
            for m in MD_IMAGE_RE.finditer(line):
                target = m.group(1).strip()
                if target.startswith("http://") or target.startswith("https://"):
                    continue  # skip external URLs
                if not index.resolve_embed(target):
                    dead.append({
                        "file": str(rel),
                        "line": line_num,
                        "target": target,
                        "type": "md_image",
                    })

    return dead


def find_orphans(index: VaultIndex) -> list[Path]:
    """Find markdown files that are never referenced by any other file."""
    referenced = index.find_referenced_files()

    orphans = []
    for md in index.md_files:
        stem_lower = md.stem.lower()
        name_lower = md.name.lower()

        # Skip common index/hub files
        if stem_lower in ("readme", "overview", "index", "_vault_health", "manifest"):
            continue

        is_referenced = (
            stem_lower in referenced
            or name_lower in referenced
            or stem_lower.replace("_", " ") in referenced
            or stem_lower.replace(" ", "_") in referenced
            or stem_lower.replace("-", "_") in referenced
            or stem_lower.replace("-", " ") in referenced
        )

        if not is_referenced:
            orphans.append(md)

    return orphans


def get_vault_stats(index: VaultIndex) -> dict:
    """Compute general vault statistics."""
    total_size = sum(f.stat().st_size for f in index.all_files)
    md_size = sum(f.stat().st_size for f in index.md_files)

    # Extension breakdown
    ext_counts = Counter()
    ext_sizes = Counter()
    for f in index.all_files:
        ext = f.suffix.lower() or "(no ext)"
        ext_counts[ext] += 1
        ext_sizes[ext] += f.stat().st_size

    # Top 10 largest files
    largest = sorted(index.all_files, key=lambda f: f.stat().st_size, reverse=True)[:15]

    # Tag frequency from YAML frontmatter
    tag_counts = Counter()
    status_counts = Counter()
    files_with_yaml = 0
    files_without_yaml = 0

    for md in index.md_files:
        try:
            content = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        # Simple YAML frontmatter extraction
        if content.startswith("---"):
            end = content.find("---", 3)
            if end > 0:
                files_with_yaml += 1
                yaml_block = content[3:end]

                # Extract tags
                for line in yaml_block.splitlines():
                    line_s = line.strip()
                    if line_s.startswith("- ") and "/" in line_s:
                        tag = line_s[2:].strip().strip("'\"")
                        tag_counts[tag] += 1
                    elif line_s.startswith("tags:"):
                        # inline tags: tags: [a, b, c]
                        bracket = line_s.find("[")
                        if bracket >= 0:
                            inner = line_s[bracket+1:line_s.find("]")]
                            for t in inner.split(","):
                                t = t.strip().strip("'\"")
                                if t:
                                    tag_counts[t] += 1

                    # Extract status
                    if line_s.startswith("status:"):
                        status = line_s.split(":", 1)[1].strip().strip("'\"")
                        if status:
                            status_counts[status] += 1
            else:
                files_without_yaml += 1
        else:
            files_without_yaml += 1

    # Folder file counts
    folder_counts = Counter()
    for f in index.all_files:
        rel = f.relative_to(index.vault)
        top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
        folder_counts[top] += 1

    return {
        "total_files": len(index.all_files),
        "md_files": len(index.md_files),
        "total_size": total_size,
        "md_size": md_size,
        "ext_counts": ext_counts.most_common(20),
        "ext_sizes": ext_sizes,
        "largest": largest,
        "tag_counts": tag_counts.most_common(30),
        "status_counts": status_counts.most_common(10),
        "files_with_yaml": files_with_yaml,
        "files_without_yaml": files_without_yaml,
        "folder_counts": folder_counts.most_common(20),
    }


# ─── Report Generator ────────────────────────────────────────────────────────

def fmt_size(n: int) -> str:
    if n >= 1_073_741_824:
        return f"{n / 1_073_741_824:.2f} GB"
    if n >= 1_048_576:
        return f"{n / 1_048_576:.1f} MB"
    if n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


def generate_report(vault_path: str, output_path: str = None):
    """Run all scans and write _VAULT_HEALTH.md"""
    vault = Path(vault_path)
    if output_path is None:
        output_path = str(vault / "_VAULT_HEALTH.md")

    print(f"Indexing vault: {vault}")
    index = VaultIndex(str(vault))
    print(f"  {len(index.all_files)} files indexed ({len(index.md_files)} markdown)")

    print("Scanning broken links...")
    broken = scan_broken_links(index)
    print(f"  {len(broken)} broken links found")

    print("Scanning dead assets...")
    dead = scan_dead_assets(index)
    print(f"  {len(dead)} dead asset references found")

    print("Finding orphans...")
    orphans = find_orphans(index)
    print(f"  {len(orphans)} orphan files found")

    print("Computing stats...")
    stats = get_vault_stats(index)

    # Build report
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []
    L = lines.append

    L(f"# Vault Health Report")
    L(f"**Generated:** {now}")
    L(f"**Vault:** `{vault}`")
    L("")

    # ── Overview
    L("## Overview")
    L("")
    L(f"| Metric | Value |")
    L(f"|--------|-------|")
    L(f"| Total files | {stats['total_files']:,} |")
    L(f"| Markdown files | {stats['md_files']:,} |")
    L(f"| Total size | {fmt_size(stats['total_size'])} |")
    L(f"| Markdown size | {fmt_size(stats['md_size'])} |")
    L(f"| Files with YAML | {stats['files_with_yaml']:,} |")
    L(f"| Files without YAML | {stats['files_without_yaml']:,} |")
    L(f"| Broken links | {len(broken):,} |")
    L(f"| Dead asset refs | {len(dead):,} |")
    L(f"| Orphan files | {len(orphans):,} |")
    L("")

    # ── Folder breakdown
    L("## Folder Breakdown")
    L("")
    L("| Folder | Files |")
    L("|--------|-------|")
    for folder, count in stats["folder_counts"]:
        L(f"| `{folder}` | {count:,} |")
    L("")

    # ── File types
    L("## File Types")
    L("")
    L("| Extension | Count | Size |")
    L("|-----------|-------|------|")
    for ext, count in stats["ext_counts"]:
        size = fmt_size(stats["ext_sizes"].get(ext, 0))
        L(f"| `{ext}` | {count:,} | {size} |")
    L("")

    # ── Largest files
    L("## Largest Files")
    L("")
    L("| Size | File |")
    L("|------|------|")
    for f in stats["largest"]:
        rel = f.relative_to(vault)
        L(f"| {fmt_size(f.stat().st_size)} | `{rel}` |")
    L("")

    # ── Broken links
    L(f"## Broken Links ({len(broken)})")
    L("")
    if broken:
        L("| File | Line | Target |")
        L("|------|------|--------|")
        shown = 0
        for b in broken:
            L(f"| `{b['file']}` | {b['line']} | `{b['target']}` |")
            shown += 1
            if shown >= 200:
                L(f"| ... | ... | *({len(broken) - 200} more)* |")
                break
    else:
        L("No broken links found.")
    L("")

    # ── Dead assets
    L(f"## Dead Asset References ({len(dead)})")
    L("")
    if dead:
        L("| File | Line | Missing Asset |")
        L("|------|------|---------------|")
        shown = 0
        for d in dead:
            L(f"| `{d['file']}` | {d['line']} | `{d['target']}` |")
            shown += 1
            if shown >= 200:
                L(f"| ... | ... | *({len(dead) - 200} more)* |")
                break
    else:
        L("No dead assets found.")
    L("")

    # ── Orphans
    L(f"## Orphan Files ({len(orphans)})")
    L("")
    if orphans:
        L("Files never referenced by any `[[wikilink]]` or embed:")
        L("")
        shown = 0
        for o in sorted(orphans, key=lambda p: p.relative_to(vault)):
            rel = o.relative_to(vault)
            L(f"- `{rel}`")
            shown += 1
            if shown >= 200:
                L(f"- *...and {len(orphans) - 200} more*")
                break
    else:
        L("No orphans found.")
    L("")

    # ── Tag frequency
    if stats["tag_counts"]:
        L("## Top Tags")
        L("")
        L("| Tag | Count |")
        L("|-----|-------|")
        for tag, count in stats["tag_counts"]:
            L(f"| `{tag}` | {count} |")
        L("")

    # ── Status breakdown
    if stats["status_counts"]:
        L("## Status Breakdown")
        L("")
        L("| Status | Count |")
        L("|--------|-------|")
        for status, count in stats["status_counts"]:
            L(f"| `{status}` | {count} |")
        L("")

    # Write report
    report_text = "\n".join(lines)
    Path(output_path).write_text(report_text, encoding="utf-8")
    print(f"\nReport saved to: {output_path}")
    print(f"  Size: {len(report_text):,} chars")

    return broken, dead, orphans, stats


def write_csv(items: list[dict], path: str, columns: list[str]):
    """Write a list of dicts to CSV."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(columns) + "\n")
        for item in items:
            row = []
            for col in columns:
                val = str(item.get(col, "")).replace('"', '""')
                row.append(f'"{val}"')
            f.write(",".join(row) + "\n")
    print(f"  CSV saved: {path} ({len(items)} rows)")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Vault Health Tool")
    parser.add_argument("--vault", default=None, help="Path to vault root")
    parser.add_argument("--scan", action="store_true", help="Scan broken links only")
    parser.add_argument("--assets", action="store_true", help="Scan dead assets only")
    parser.add_argument("--report", action="store_true", help="Full health report")
    parser.add_argument("--all", action="store_true", help="Run everything")
    parser.add_argument("--csv", action="store_true", help="Also export CSVs")
    args = parser.parse_args()

    # Determine vault path
    vault_path = args.vault
    if not vault_path:
        # Try to detect from script location
        script_dir = Path(__file__).resolve().parent
        # Walk up to find .obsidian
        check = script_dir
        for _ in range(10):
            if (check / ".obsidian").exists():
                vault_path = str(check)
                break
            check = check.parent
        if not vault_path:
            vault_path = input("Vault path: ").strip().strip('"')

    if not Path(vault_path).exists():
        print(f"ERROR: Vault not found: {vault_path}")
        sys.exit(1)

    # If no flags, show menu
    if not (args.scan or args.assets or args.report or args.all):
        print()
        print("========================================")
        print(" Vault Health Tool")
        print("========================================")
        print(f" Vault: {vault_path}")
        print()
        print(" 1) Scan broken links")
        print(" 2) Scan dead asset references")
        print(" 3) Full health report (includes everything)")
        print(" Q) Quit")
        print()
        choice = input("Select: ").strip().upper()
        if choice == "1":
            args.scan = True
        elif choice == "2":
            args.assets = True
        elif choice == "3":
            args.all = True
        else:
            print("Bye.")
            return

    vault = Path(vault_path)

    if args.all or args.report:
        broken, dead, orphans, stats = generate_report(str(vault))
        if args.csv:
            csv_dir = str(vault / "90_SYSTEM" / "engine" / "scripts")
            write_csv(broken, os.path.join(csv_dir, "broken_links.csv"),
                       ["file", "line", "target", "type"])
            write_csv(dead, os.path.join(csv_dir, "dead_assets.csv"),
                       ["file", "line", "target", "type"])
        return

    print(f"Indexing vault: {vault}")
    index = VaultIndex(str(vault))
    print(f"  {len(index.all_files)} files indexed ({len(index.md_files)} markdown)")

    if args.scan:
        print("\nScanning broken links...")
        broken = scan_broken_links(index)
        print(f"\n  {len(broken)} broken links found\n")
        for b in broken[:50]:
            print(f"  {b['file']}:{b['line']}  ->  [[{b['target']}]]")
        if len(broken) > 50:
            print(f"  ... and {len(broken) - 50} more")
        if args.csv:
            write_csv(broken, str(vault / "broken_links.csv"),
                       ["file", "line", "target", "type"])

    if args.assets:
        print("\nScanning dead assets...")
        dead = scan_dead_assets(index)
        print(f"\n  {len(dead)} dead asset references found\n")
        for d in dead[:50]:
            print(f"  {d['file']}:{d['line']}  ->  ![[{d['target']}]]")
        if len(dead) > 50:
            print(f"  ... and {len(dead) - 50} more")
        if args.csv:
            write_csv(dead, str(vault / "dead_assets.csv"),
                       ["file", "line", "target", "type"])


if __name__ == "__main__":
    main()
