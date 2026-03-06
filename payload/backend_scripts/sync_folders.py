#!/usr/bin/env python3
"""
Bidirectional Folder Sync Script
Synchronizes two folders by copying missing/newer files in both directions.
"""

import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
import argparse
import sys

# Increase recursion limit for deep folders
sys.setrecursionlimit(100)

# Configuration
FOLDER_A = r"C:\Users\lowes\OneDrive\Documents\Theophysics Master"
FOLDER_B = r"C:\Users\lowes\OneDrive\Documents\Theophysics Master 1"

# Folders to completely skip during sync
SKIP_FOLDERS = {
    '.git',
    '__pycache__',
    'venv',
    '.venv',
    '.venv_edge',
    'node_modules',
    '.trash',
    '_gsdata_',
}

# File patterns to skip
SKIP_FILES = {
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    'sync_folders.py',
}

# Extensions to skip
SKIP_EXTENSIONS = {
    '.pyc',
    '.tmp',
    '.log',
}


def should_skip_folder(name: str) -> bool:
    """Check if a folder should be skipped."""
    return name in SKIP_FOLDERS or name.startswith('.')


def should_skip_file(name: str) -> bool:
    """Check if a file should be skipped."""
    if name in SKIP_FILES:
        return True
    for ext in SKIP_EXTENSIONS:
        if name.endswith(ext):
            return True
    return False


def get_all_files(root_path: str) -> dict:
    """Get all files using os.walk (safer than rglob)."""
    files = {}
    root = Path(root_path)

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out directories we want to skip (modifies in-place)
        dirnames[:] = [d for d in dirnames if not should_skip_folder(d)]

        for filename in filenames:
            if should_skip_file(filename):
                continue

            filepath = Path(dirpath) / filename
            try:
                rel_path = filepath.relative_to(root)
                stat = filepath.stat()
                files[str(rel_path)] = {
                    'path': filepath,
                    'mtime': stat.st_mtime,
                    'size': stat.st_size,
                }
            except Exception as e:
                print(f"  [WARN] Could not process {filepath}: {e}")

    return files


def sync_file(src: Path, dst: Path, rel_path: str, dry_run: bool = False) -> bool:
    """Copy a single file from src to dst."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dry_run:
            shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to copy {rel_path}: {e}")
        return False


def get_file_hash(filepath: Path) -> str:
    """Get MD5 hash of a file for comparison."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        return ""


def sync_folders(folder_a: str, folder_b: str, dry_run: bool = False, verbose: bool = True):
    """
    Bidirectional sync between two folders.
    """
    path_a = Path(folder_a)
    path_b = Path(folder_b)

    if not path_a.exists():
        print(f"[ERROR] Folder A does not exist: {folder_a}")
        return
    if not path_b.exists():
        print(f"[ERROR] Folder B does not exist: {folder_b}")
        return

    print("=" * 60)
    print("BIDIRECTIONAL FOLDER SYNC")
    print("=" * 60)
    print(f"Folder A: {folder_a}")
    print(f"Folder B: {folder_b}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print("=" * 60)

    # Scan both folders
    print("\n[1/4] Scanning Folder A...")
    files_a = get_all_files(folder_a)
    print(f"      Found {len(files_a)} files")

    print("\n[2/4] Scanning Folder B...")
    files_b = get_all_files(folder_b)
    print(f"      Found {len(files_b)} files")

    # Find differences
    only_in_a = set(files_a.keys()) - set(files_b.keys())
    only_in_b = set(files_b.keys()) - set(files_a.keys())
    in_both = set(files_a.keys()) & set(files_b.keys())

    # Track stats
    stats = {
        'a_to_b': 0,
        'b_to_a': 0,
        'conflicts_resolved': 0,
        'identical': 0,
        'errors': 0,
    }

    # Copy files only in A to B
    print(f"\n[3/4] Syncing {len(only_in_a)} files from A -> B...")
    for rel_path in sorted(only_in_a):
        src = files_a[rel_path]['path']
        dst = path_b / rel_path
        if verbose:
            print(f"  A->B: {rel_path}")
        if sync_file(src, dst, rel_path, dry_run):
            stats['a_to_b'] += 1
        else:
            stats['errors'] += 1

    # Copy files only in B to A
    print(f"\n[4/4] Syncing {len(only_in_b)} files from B -> A...")
    for rel_path in sorted(only_in_b):
        src = files_b[rel_path]['path']
        dst = path_a / rel_path
        if verbose:
            print(f"  B->A: {rel_path}")
        if sync_file(src, dst, rel_path, dry_run):
            stats['b_to_a'] += 1
        else:
            stats['errors'] += 1

    # Handle files that exist in both (check for differences)
    print(f"\n[EXTRA] Checking {len(in_both)} files in both locations...")
    for rel_path in sorted(in_both):
        info_a = files_a[rel_path]
        info_b = files_b[rel_path]

        # Same size? Check mtime
        if info_a['size'] == info_b['size']:
            if abs(info_a['mtime'] - info_b['mtime']) < 2:
                stats['identical'] += 1
                continue

        # Different - newer wins
        if info_a['mtime'] > info_b['mtime']:
            if verbose:
                print(f"  A->B (newer): {rel_path}")
            if sync_file(info_a['path'], path_b / rel_path, rel_path, dry_run):
                stats['conflicts_resolved'] += 1
        elif info_b['mtime'] > info_a['mtime']:
            if verbose:
                print(f"  B->A (newer): {rel_path}")
            if sync_file(info_b['path'], path_a / rel_path, rel_path, dry_run):
                stats['conflicts_resolved'] += 1
        else:
            stats['identical'] += 1

    # Summary
    print("\n" + "=" * 60)
    print("SYNC COMPLETE" + (" (DRY RUN)" if dry_run else ""))
    print("=" * 60)
    print(f"  Files copied A -> B:    {stats['a_to_b']}")
    print(f"  Files copied B -> A:    {stats['b_to_a']}")
    print(f"  Conflicts resolved:     {stats['conflicts_resolved']}")
    print(f"  Identical (skipped):    {stats['identical']}")
    print(f"  Errors:                 {stats['errors']}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Bidirectional folder sync')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Show what would be done without copying (default)')
    parser.add_argument('--live', action='store_true',
                        help='Actually perform the sync')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Less verbose output')

    args = parser.parse_args()
    dry_run = not args.live
    verbose = not args.quiet

    sync_folders(FOLDER_A, FOLDER_B, dry_run=dry_run, verbose=verbose)


if __name__ == '__main__':
    main()
