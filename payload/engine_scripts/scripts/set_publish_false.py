#!/usr/bin/env python3
"""
Sets publish: false in frontmatter for all .md files in private folders.
Creates frontmatter if a file doesn't have it.

Usage:
  python set_publish_false.py --dry-run   # Preview only
  python set_publish_false.py             # Apply changes
"""

import os
import re
import argparse
from pathlib import Path

VAULT_ROOT = Path("O:/_Theophysics_v3")

PRIVATE_FOLDERS = [
    '.trash',
    '_PENDING_DELETE',
    '02_DRAFTING',
    'ZZZZ_AI_PRE_DELETE',
    '00_AI',
    '_ARCHIVE',
    '_INBOX',
    '_LOSSLESS_SUMMARY',
    'ZZZZ_AI_PRE_DELETE',
    '02_OPERATING_SYSTEM',
    '05_META_RESEARCH',
    '99_TAG_NOTES',
    'ZZZ Audio',
]

FRONTMATTER_RE = re.compile(r'^---\n(.*?)\n---', re.DOTALL)


def set_publish_false(content):
    """Add or update publish: false in frontmatter. Returns (new_content, was_changed)."""
    m = FRONTMATTER_RE.match(content)
    if m:
        yaml_block = m.group(1)
        # Already has publish: false
        if re.search(r'^publish:\s*false\s*$', yaml_block, re.MULTILINE):
            return content, False
        # Has publish: true — replace it
        if re.search(r'^publish:', yaml_block, re.MULTILINE):
            new_yaml = re.sub(r'^publish:.*$', 'publish: false', yaml_block, flags=re.MULTILINE)
        else:
            # Append to existing frontmatter
            new_yaml = yaml_block + '\npublish: false'
        new_content = content[:m.start(1)] + new_yaml + content[m.end(1):]
        return new_content, True
    else:
        # No frontmatter — prepend it
        new_content = '---\npublish: false\n---\n' + content
        return new_content, True


def process_folder(folder_path, dry_run):
    changed = 0
    skipped = 0
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            if not f.lower().endswith('.md'):
                continue
            fpath = Path(root) / f
            try:
                original = fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            new_content, was_changed = set_publish_false(original)
            if was_changed:
                changed += 1
                if not dry_run:
                    fpath.write_text(new_content, encoding='utf-8')
            else:
                skipped += 1
    return changed, skipped


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(f"=== SET publish: false IN PRIVATE FOLDERS ({mode}) ===\n")

    total_changed = 0
    total_skipped = 0

    for folder_name in PRIVATE_FOLDERS:
        folder_path = VAULT_ROOT / folder_name
        if not folder_path.exists():
            print(f"  [SKIP] {folder_name}/ — not found")
            continue
        changed, skipped = process_folder(folder_path, args.dry_run)
        total_changed += changed
        total_skipped += skipped
        action = "Would update" if args.dry_run else "Updated"
        print(f"  {folder_name}/  ->  {action} {changed} files  (already set: {skipped})")

    print(f"\nTotal: {'would update' if args.dry_run else 'updated'} {total_changed} files, {total_skipped} already had publish: false")
