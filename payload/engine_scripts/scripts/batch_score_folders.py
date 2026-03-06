#!/usr/bin/env python3
"""
Batch CKG Score Multiple Folders
Creates MAIN_PAPERS/OpenAI_DATA structure and runs CKG scorer
"""

import sys
import subprocess
from pathlib import Path
import shutil

def setup_folder_structure(folder_path):
    """Create MAIN_PAPERS/OpenAI_DATA structure"""
    main_papers = folder_path / "MAIN_PAPERS"
    openai_data = main_papers / "OpenAI_DATA"
    
    main_papers.mkdir(exist_ok=True)
    openai_data.mkdir(exist_ok=True)
    
    # Move .md files to MAIN_PAPERS
    md_files = list(folder_path.glob("*.md"))
    for md_file in md_files:
        dest = main_papers / md_file.name
        if not dest.exists():
            shutil.copy2(md_file, dest)
    
    return main_papers, openai_data, len(md_files)

def score_folder(folder_path, ckg_script):
    """Score all papers in a folder"""
    print(f"\n{'='*60}")
    print(f"Processing: {folder_path.name}")
    print(f"{'='*60}")
    
    # Setup structure
    main_papers, openai_data, file_count = setup_folder_structure(folder_path)
    
    if file_count == 0:
        print(f"  [!] No .md files found in {folder_path.name}")
        return False
    
    print(f"  [+] Found {file_count} markdown files")
    print(f"  [+] Created: MAIN_PAPERS/OpenAI_DATA/")
    
    # Score each file
    for md_file in main_papers.glob("*.md"):
        print(f"\n  [*] Scoring: {md_file.name}")
        try:
            result = subprocess.run(
                ["python", str(ckg_script), str(md_file)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"      [OK] Scored successfully")
            else:
                print(f"      [!!] Error: {result.stderr[:100]}")
        except subprocess.TimeoutExpired:
            print(f"      [!!] Timeout (>2min)")
        except Exception as e:
            print(f"      [!!] Error: {e}")
    
    return True

def main():
    # Paths
    ckg_script = Path("O:/_Theophysics_v3/00_SYSTEM/01_ENGINE/scripts/Open-AI-CKG/run_ckg_scorer.py")
    unscored_dir = Path("O:/_Theophysics_v3/04_THEOPYHISCS/_Unscored_Papers")
    
    if not ckg_script.exists():
        print(f"[!!] CKG scorer not found: {ckg_script}")
        return
    
    # Small folders to score (passed as arguments or default list)
    if len(sys.argv) > 1:
        folders = sys.argv[1:]
    else:
        folders = [
            "Theopyhiscs story",
            "LAYER_3_METRICS",
            "Theophysics_AI_Notes",
            "Logic"
        ]
    
    print("="*60)
    print("BATCH CKG SCORING")
    print("="*60)
    print(f"Folders to score: {len(folders)}")
    
    for folder_name in folders:
        folder_path = unscored_dir / folder_name
        if folder_path.exists():
            score_folder(folder_path, ckg_script)
        else:
            print(f"\n[!] Folder not found: {folder_name}")
    
    print("\n" + "="*60)
    print("BATCH SCORING COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
