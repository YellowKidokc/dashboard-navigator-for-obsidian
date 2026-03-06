#!/usr/bin/env python3
"""
Add CKG Scores to Folder Names

Finds folders with OpenAI_DATA/CKG scores and renames them with score prefix.
Format: [8.5] Folder_Name
"""

import os
import json
import csv
from pathlib import Path
import re


def find_folders_with_openai_data(root_dir):
    """Find all folders containing OpenAI_DATA subfolders"""
    folders = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'OpenAI_DATA' in dirnames:
            parent_folder = Path(dirpath)
            folders.append(parent_folder)

    return folders


def get_folder_score(folder_path):
    """Get the average final_score from OpenAI_DATA CSV or JSON"""
    openai_data = folder_path / "MAIN_PAPERS" / "OpenAI_DATA"

    if not openai_data.exists():
        openai_data = folder_path / "OpenAI_DATA"

    if not openai_data.exists():
        return None

    # Try CSV first (preferred)
    csv_files = list(openai_data.glob("CKG_Comparison_*.csv"))
    if csv_files:
        latest_csv = sorted(csv_files)[-1]
        try:
            with open(latest_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                scores = []
                for row in reader:
                    if 'final_score' in row:
                        try:
                            scores.append(float(row['final_score']))
                        except:
                            pass

                if scores:
                    avg_score = sum(scores) / len(scores)
                    return round(avg_score, 1)
        except Exception as e:
            print(f"  Error reading {latest_csv}: {e}")

    # Try JSON files if no CSV found
    json_files = list(openai_data.glob("*_CKG_*.json"))
    if json_files:
        scores = []
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Try different JSON structures
                    if 'final_score' in data:
                        scores.append(float(data['final_score']))
                    elif 'aggregate_summary' in data and 'final_score' in data['aggregate_summary']:
                        scores.append(float(data['aggregate_summary']['final_score']))
                    elif 'document_aggregate' in data and 'final_score' in data['document_aggregate']:
                        scores.append(float(data['document_aggregate']['final_score']))
            except Exception as e:
                continue

        if scores:
            avg_score = sum(scores) / len(scores)
            return round(avg_score, 1)

    return None


def remove_existing_score(folder_name):
    """Remove existing [X.X] score prefix if present"""
    # Match [X.X] or [X] at start
    pattern = r'^\[\d+\.?\d*\]\s*'
    return re.sub(pattern, '', folder_name)


def rename_folder_with_score(folder_path, score):
    """Rename folder to include score prefix"""
    parent = folder_path.parent
    old_name = folder_path.name

    # Remove any existing score
    clean_name = remove_existing_score(old_name)

    # Add new score
    new_name = f"[{score}] {clean_name}"
    new_path = parent / new_name

    # Check if already renamed
    if old_name == new_name:
        return False, f"Already has score: {old_name}"

    # Check if target exists
    if new_path.exists():
        return False, f"Target exists: {new_name}"

    try:
        folder_path.rename(new_path)
        return True, f"{old_name} -> {new_name}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    vault_root = Path("O:/_Theophysics_v3")

    print("="*60)
    print("ADD CKG SCORES TO FOLDER NAMES")
    print("="*60)
    print()

    # Find all folders with OpenAI_DATA
    print("[*] Scanning for folders with OpenAI_DATA...")
    folders = find_folders_with_openai_data(vault_root)
    print(f"[+] Found {len(folders)} folders with OpenAI_DATA\n")

    # Get scores and rename
    renamed = 0
    skipped = 0
    errors = 0

    for folder in folders:
        folder_name = folder.name

        # Skip if already processed
        if folder_name.startswith('[') and ']' in folder_name:
            print(f"[>] {folder_name} (already scored)")
            skipped += 1
            continue

        # Get score
        score = get_folder_score(folder)

        if score is None:
            # Show full path for debugging
            print(f"[-] {folder_name} (no score found)")
            print(f"    Path: {folder}")
            errors += 1
            continue

        # Rename
        success, message = rename_folder_with_score(folder, score)

        if success:
            print(f"[+] {message}")
            renamed += 1
        else:
            print(f"[-] {folder_name}: {message}")
            errors += 1

    # Summary
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"[+] Renamed: {renamed} folders")
    print(f"[>] Skipped: {skipped} folders (already scored)")
    print(f"[-] Errors:  {errors} folders")
    print()


if __name__ == '__main__':
    main()
