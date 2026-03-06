#!/usr/bin/env python3
"""
Duplicate file finder for Obsidian vault.
Uses size-then-hash approach for efficiency.

Usage:
  python find_duplicates.py --report          # Find and report duplicates
  python find_duplicates.py --delete          # Delete duplicates (keeps one copy per group)
  python find_duplicates.py --delete --dry-run  # Preview deletions
"""

import os
import hashlib
import argparse
import json
from pathlib import Path
from collections import defaultdict

VAULT_ROOT = Path("O:/_Theophysics_v3")

# Skip these folders entirely (Obsidian internals)
EXCLUDE_DIRS = {'.git', '.obsidian'}

# When keeping one copy from a duplicate group, prefer paths in this order
KEEP_PRIORITY = [
    '00_Canonical',
    'MASTER_EQUATION',
    '00_AXIOMS',
    '04_THEOPYHISCS',
    '00_SYSTEM',
]


def file_hash(fpath, chunk=65536):
    h = hashlib.md5()
    try:
        with open(fpath, 'rb') as f:
            while chunk_data := f.read(chunk):
                h.update(chunk_data)
        return h.hexdigest()
    except Exception:
        return None


def pick_keeper(paths):
    """Pick which file to keep from a duplicate group."""
    # Prefer files in canonical/priority folders
    for priority in KEEP_PRIORITY:
        for p in paths:
            if priority in str(p):
                return p
    # Default: shortest path (usually least-nested)
    return min(paths, key=lambda p: len(str(p)))


def find_duplicates(vault_root, exclude_dirs):
    print("Pass 1: Grouping files by size...")
    size_groups = defaultdict(list)

    all_files = []
    for root, dirs, files in os.walk(vault_root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            fpath = Path(root) / f
            try:
                size = fpath.stat().st_size
                if size > 0:  # Skip empty files
                    size_groups[size].append(fpath)
            except Exception:
                pass

    # Only hash files that share a size with another file
    candidates = {size: paths for size, paths in size_groups.items()
                  if len(paths) > 1}

    total_candidate_files = sum(len(v) for v in candidates.values())
    total_candidate_bytes = sum(size * len(paths) for size, paths in candidates.items())
    print(f"  {total_candidate_files:,} files share sizes — hashing to confirm duplicates...")
    print(f"  ({total_candidate_bytes / 1024**3:.2f} GB to check)")

    print("\nPass 2: Hashing candidate files...")
    hash_groups = defaultdict(list)
    done = 0
    for size, paths in candidates.items():
        for fpath in paths:
            h = file_hash(fpath)
            if h:
                hash_groups[h].append(fpath)
            done += 1
            if done % 500 == 0:
                print(f"  Hashed {done:,}/{total_candidate_files:,}...")

    # Only keep groups with actual duplicates
    duplicates = {h: paths for h, paths in hash_groups.items()
                  if len(paths) > 1}

    return duplicates


def report(duplicates, vault_root):
    if not duplicates:
        print("No duplicates found!")
        return

    total_groups = len(duplicates)
    total_files = sum(len(paths) for paths in duplicates.values())
    total_waste = 0

    rows = []
    for h, paths in duplicates.items():
        size = paths[0].stat().st_size
        waste = size * (len(paths) - 1)
        total_waste += waste
        keeper = pick_keeper(paths)
        rows.append({
            'hash': h,
            'size_mb': round(size / 1024**2, 2),
            'count': len(paths),
            'waste_mb': round(waste / 1024**2, 2),
            'keeper': str(keeper.relative_to(vault_root)),
            'duplicates': [str(p.relative_to(vault_root)) for p in paths if p != keeper]
        })

    # Sort by waste descending
    rows.sort(key=lambda r: r['waste_mb'], reverse=True)

    print(f"\n=== DUPLICATE FILE REPORT ===\n")
    print(f"Duplicate groups:  {total_groups:,}")
    print(f"Total files:       {total_files:,}")
    print(f"Reclaimable space: {total_waste / 1024**3:.2f} GB\n")

    print(f"{'Size (MB)':<12} {'Copies':<8} {'Waste (MB)':<12} {'Filename'}")
    print("-" * 70)
    for r in rows[:50]:  # Show top 50
        fname = Path(r['keeper']).name
        print(f"{r['size_mb']:<12.1f} {r['count']:<8} {r['waste_mb']:<12.1f} {fname}")

    if len(rows) > 50:
        print(f"  ... and {len(rows) - 50} more groups")

    # Save full report
    report_path = vault_root / '_duplicate_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)
    print(f"\nFull report saved to: {report_path}")

    return rows


def delete_duplicates(duplicates, vault_root, dry_run=False):
    deleted_count = 0
    deleted_bytes = 0

    for h, paths in duplicates.items():
        keeper = pick_keeper(paths)
        to_delete = [p for p in paths if p != keeper]
        for p in to_delete:
            size = p.stat().st_size
            rel = p.relative_to(vault_root)
            if dry_run:
                print(f"  [DRY RUN] Would delete: {rel}")
            else:
                try:
                    p.unlink()
                    deleted_count += 1
                    deleted_bytes += size
                    print(f"  Deleted: {str(rel).encode('ascii', 'replace').decode()}")
                except Exception as e:
                    print(f"  ERROR deleting {str(rel).encode('ascii', 'replace').decode()}: {e}")

    action = "Would delete" if dry_run else "Deleted"
    print(f"\n{action} {deleted_count:,} files ({deleted_bytes / 1024**3:.2f} GB freed)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', action='store_true', help='Find and report duplicates')
    parser.add_argument('--delete', action='store_true', help='Delete duplicate files')
    parser.add_argument('--dry-run', action='store_true', help='Preview deletions')
    args = parser.parse_args()

    if not args.report and not args.delete:
        parser.print_help()
        exit()

    duplicates = find_duplicates(VAULT_ROOT, EXCLUDE_DIRS)

    if args.report or args.delete:
        rows = report(duplicates, VAULT_ROOT)

    if args.delete:
        if not rows:
            print("Nothing to delete.")
        else:
            mode = "DRY RUN" if args.dry_run else "LIVE"
            print(f"\n=== DELETING DUPLICATES ({mode}) ===\n")
            delete_duplicates(duplicates, VAULT_ROOT, dry_run=args.dry_run)
