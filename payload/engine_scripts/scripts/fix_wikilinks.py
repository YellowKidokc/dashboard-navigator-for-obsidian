#!/usr/bin/env python3
"""
Obsidian Wikilink Analyzer & Fixer
Scans all .md files, finds broken links, and fixes simple cases.

Usage:
  python fix_wikilinks.py --analyze        # Report only, no changes
  python fix_wikilinks.py --fix-simple     # Fix backslashes + .md extensions
  python fix_wikilinks.py --fix-simple --dry-run  # Preview fixes
"""

import os
import re
import json
import argparse
from pathlib import Path
from collections import defaultdict

VAULT_ROOT = Path("O:/_Theophysics_v3")

# Folders excluded from scanning (private / staging)
EXCLUDE_SCAN = {'.git', '.obsidian', '.trash', '_PENDING_DELETE',
                'ZZZZ_AI_PRE_DELETE', '_ARCHIVE'}

# Wikilink pattern: [[target]] or [[target|alias]]
WIKILINK_RE = re.compile(r'\[\[([^\[\]]+)\]\]')


def build_file_index(vault_root, exclude_dirs):
    """Build a lowercase-filename -> [relative_path, ...] index."""
    index = defaultdict(list)
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and not d.startswith('.')]
        for f in files:
            if f.lower().endswith('.md'):
                rel = Path(root).relative_to(vault_root) / f
                stem = f[:-3].lower()
                index[stem].append(str(rel).replace('\\', '/'))
    return index


def extract_links(content):
    """Return list of raw link targets (before | alias)."""
    links = []
    for m in WIKILINK_RE.finditer(content):
        target = m.group(1).split('|')[0].strip()
        links.append(target)
    return links


def classify_link(target, index, vault_root):
    """
    Returns (status, suggestion)
    status: 'ok' | 'has_extension' | 'has_backslash' | 'both' | 'missing'
    """
    has_ext = target.lower().endswith('.md')
    has_bs = '\\' in target

    clean = target
    if has_ext:
        clean = clean[:-3]
    clean_fwd = clean.replace('\\', '/')

    # Check if the cleaned path resolves
    if '/' in clean_fwd:
        full = vault_root / (clean_fwd + '.md')
        exists = full.exists()
    else:
        exists = clean_fwd.lower() in index

    if exists:
        if has_ext and has_bs:
            return 'both', clean_fwd
        elif has_ext:
            return 'has_extension', clean_fwd
        elif has_bs:
            return 'has_backslash', clean_fwd
        else:
            return 'ok', None
    else:
        # Try to find by filename only
        stem = clean_fwd.split('/')[-1].lower()
        if stem in index:
            return 'missing_path', index[stem][0] if len(index[stem]) == 1 else None
        return 'missing', None


def analyze(vault_root, exclude_dirs):
    print(f"Building file index...")
    index = build_file_index(vault_root, exclude_dirs)
    print(f"  Indexed {sum(len(v) for v in index.values())} .md files\n")

    stats = defaultdict(int)
    missing_links = []
    fixable_files = set()

    md_files = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and not d.startswith('.')]
        for f in files:
            if f.lower().endswith('.md'):
                md_files.append(Path(root) / f)

    print(f"Scanning {len(md_files)} .md files for wikilinks...")

    for i, fpath in enumerate(md_files):
        if i % 1000 == 0:
            print(f"  {i}/{len(md_files)}...")
        try:
            content = fpath.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        links = extract_links(content)
        for link in links:
            status, suggestion = classify_link(link, index, vault_root)
            stats[status] += 1
            if status in ('has_extension', 'has_backslash', 'both'):
                fixable_files.add(str(fpath))
            elif status in ('missing', 'missing_path'):
                rel = str(fpath.relative_to(vault_root))
                missing_links.append({
                    'file': rel,
                    'link': link,
                    'status': status,
                    'suggestion': suggestion
                })

    print("\n=== WIKILINK ANALYSIS REPORT ===\n")
    total = sum(stats.values())
    print(f"Total wikilinks scanned: {total:,}")
    print(f"  OK (resolve correctly):          {stats['ok']:,}")
    print(f"  Fixable - .md extension:         {stats['has_extension']:,}")
    print(f"  Fixable - backslash path:        {stats['has_backslash']:,}")
    print(f"  Fixable - both issues:           {stats['both']:,}")
    print(f"  Missing (file moved/deleted):    {stats['missing']:,}")
    print(f"  Missing path (filename found):   {stats['missing_path']:,}")
    print(f"\nFiles with auto-fixable issues: {len(fixable_files):,}")
    print(f"Truly broken (needs manual fix):  {stats['missing']:,}")

    # Save full missing links report
    report_path = vault_root / '_wikilink_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': dict(stats),
            'missing_links': missing_links[:5000]  # cap at 5k entries
        }, f, indent=2)
    print(f"\nFull report saved to: {report_path}")
    print(f"(Showing first 5,000 broken links)")

    return stats, fixable_files


def fix_simple(vault_root, exclude_dirs, dry_run=False):
    """Fix .md extensions and backslashes in wikilinks."""

    def replacer(m):
        inner = m.group(1)
        parts = inner.split('|', 1)
        target = parts[0].strip()
        alias = parts[1] if len(parts) > 1 else None

        # Fix backslashes
        target = target.replace('\\', '/')
        # Remove .md extension
        if target.lower().endswith('.md'):
            target = target[:-3]

        if alias:
            return f'[[{target}|{alias}]]'
        return f'[[{target}]]'

    changed = 0
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and not d.startswith('.')]
        for f in files:
            if not f.lower().endswith('.md'):
                continue
            fpath = Path(root) / f
            try:
                original = fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            # Check if any fix needed
            has_issue = False
            for m in WIKILINK_RE.finditer(original):
                t = m.group(1).split('|')[0].strip()
                if t.lower().endswith('.md') or '\\' in t:
                    has_issue = True
                    break

            if not has_issue:
                continue

            fixed = WIKILINK_RE.sub(replacer, original)
            if fixed != original:
                changed += 1
                rel = fpath.relative_to(vault_root)
                if dry_run:
                    print(f"  [DRY RUN] Would fix: {rel}")
                else:
                    fpath.write_text(fixed, encoding='utf-8')
                    if changed <= 20:
                        print(f"  Fixed: {rel}")

    action = "Would fix" if dry_run else "Fixed"
    print(f"\n{action} {changed:,} files.")


def fix_paths(vault_root, exclude_dirs, dry_run=False):
    """Fix wikilinks where the target file exists but at a different path.
    - If exactly 1 file with that name exists: replace with [[stem]]
    - If multiple files: replace with [[correct/path]] using first match
    """
    print("Building file index...")
    index = build_file_index(vault_root, exclude_dirs)

    changed_files = 0
    changed_links = 0

    def replacer(m):
        nonlocal changed_links
        inner = m.group(1)
        parts = inner.split('|', 1)
        target = parts[0].strip()
        alias = parts[1] if len(parts) > 1 else None

        clean = target.replace('\\', '/')
        if clean.lower().endswith('.md'):
            clean = clean[:-3]

        # Only process path-based links that don't resolve
        if '/' not in clean:
            return m.group(0)

        # Check if current path already resolves
        full = vault_root / (clean + '.md')
        if full.exists():
            return m.group(0)

        # Try to find by stem
        stem = clean.split('/')[-1].lower()
        matches = index.get(stem, [])

        if not matches:
            return m.group(0)  # Truly missing

        if len(matches) == 1:
            # Unique filename — use stem only (Obsidian will find it)
            new_target = Path(matches[0]).stem
        else:
            # Multiple matches — use first match's full path
            new_target = str(Path(matches[0]))[:-3].replace('\\', '/')

        changed_links += 1
        if alias:
            return f'[[{new_target}|{alias}]]'
        return f'[[{new_target}]]'

    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs
                   and not d.startswith('.')]
        for f in files:
            if not f.lower().endswith('.md'):
                continue
            fpath = Path(root) / f
            try:
                original = fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            fixed = WIKILINK_RE.sub(replacer, original)
            if fixed != original:
                changed_files += 1
                rel = fpath.relative_to(vault_root)
                if dry_run:
                    if changed_files <= 10:
                        print(f"  [DRY RUN] Would fix: {rel}")
                else:
                    fpath.write_text(fixed, encoding='utf-8')
                    if changed_files <= 20:
                        print(f"  Fixed: {rel}")

    action = "Would fix" if dry_run else "Fixed"
    print(f"\n{action} {changed_links:,} links across {changed_files:,} files.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--analyze', action='store_true',
                        help='Analyze and report broken links')
    parser.add_argument('--fix-simple', action='store_true',
                        help='Fix .md extensions and backslashes in wikilinks')
    parser.add_argument('--fix-paths', action='store_true',
                        help='Fix links where file exists but path is wrong')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing files')
    args = parser.parse_args()

    if not args.analyze and not args.fix_simple and not args.fix_paths:
        parser.print_help()

    if args.analyze:
        analyze(VAULT_ROOT, EXCLUDE_SCAN)

    if args.fix_simple:
        mode = "DRY RUN" if args.dry_run else "LIVE"
        print(f"\n=== FIX SIMPLE ISSUES ({mode}) ===\n")
        fix_simple(VAULT_ROOT, EXCLUDE_SCAN, dry_run=args.dry_run)

    if args.fix_paths:
        mode = "DRY RUN" if args.dry_run else "LIVE"
        print(f"\n=== FIX WRONG PATHS ({mode}) ===\n")
        fix_paths(VAULT_ROOT, EXCLUDE_SCAN, dry_run=args.dry_run)
