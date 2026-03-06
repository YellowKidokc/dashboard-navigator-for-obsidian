#!/usr/bin/env python3
"""
Organize and rename all Desktop images into proper asset folders
Then implement them into the FINAL papers
"""

import os
import shutil
from pathlib import Path
import re

# Source folders on Desktop
DESKTOP_BASE = Path(os.getenv("THEOPHYSICS_DESKTOP_BASE", str(Path.home() / "Desktop")))
SOURCE_FOLDERS = {
    1: DESKTOP_BASE / "LGP_01_The_Logos_Principle",
    2: DESKTOP_BASE / "LGP_02_The_Quantum_Bridge",
    3: DESKTOP_BASE / "LGP_03_The_Algorithm_of_Reality",
    4: DESKTOP_BASE / "LGP_04_The_Hard_Problem_of_Consciousness",
    5: DESKTOP_BASE / "LGP_05_The_Soul_as_Quantum_Observer",
    6: DESKTOP_BASE / "LGP_06_A_Physics_of_Principalities",
    7: DESKTOP_BASE / "LGP_07_The_Grace_Function",
    8: DESKTOP_BASE / "LGP_08_The_Stretched_Out_Heavens",
    9: DESKTOP_BASE / "LGP_09_The_Moral_Universe",
    10: DESKTOP_BASE / "LGP_10_Creatio_ex_Silico",
    12: DESKTOP_BASE / "LGP_12_The_Decalogue_of_the_Cosmos",
}

SONNET_FOLDER = DESKTOP_BASE / "Sonnet_4.5_Pictures"

# Target asset folders
ASSETS_BASE = Path(os.getenv("THEOPHYSICS_ASSETS_BASE", r"O:\_Theophysics_v3\_META\Assets\Images\logos papers"))
TARGET_FOLDERS = {
    1: ASSETS_BASE / "P1_Logos_Principle",
    2: ASSETS_BASE / "P2_Quantum_Bridge",
    3: ASSETS_BASE / "P3_Algorithm_Reality",
    4: ASSETS_BASE / "P4_Hard_Problem",
    5: ASSETS_BASE / "P5_Soul_Observer",
    6: ASSETS_BASE / "P6_Physics_Principalities",
    7: ASSETS_BASE / "P7_Grace_Function",
    8: ASSETS_BASE / "P8_Stretched_Heavens",
    9: ASSETS_BASE / "P9_Moral_Universe",
    10: ASSETS_BASE / "P10_Creatio_ex_Silico",
    12: ASSETS_BASE / "P12_Decalogue",
}

# Papers location
PAPERS_DIR = Path(os.getenv("THEOPHYSICS_PAPERS_DIR", r"O:\_Theophysics_v3\05_PUBLICATIONS\Logos_Papers\COMPLETE_LOGOS_PAPERS_FINAL"))

def get_paper_path(paper_num):
    """Get the FINAL paper path"""
    papers = {
        1: "Paper-01-The-Logos-Principle-FINAL.md",
        2: "Paper-02-The-Quantum-Bridge-FINAL.md",
        3: "Paper-03-The-Algorithm-of-Reality-FINAL.md",
        4: "Paper-04-The-Hard-Problem-of-Consciousness-FINAL.md",
        5: "Paper-05-The-Soul-Observer-FINAL.md",
        6: "Paper-06-A-Physics-of-Principalities-FINAL.md",
        7: "Paper-07-The-Grace-Function-FINAL.md",
        8: "Paper-08-The-Stretched-Out-Heavens-FINAL.md",
        9: "Paper-09-The-Moral-Universe-FINAL.md",
        10: "Paper-10-Creatio-ex-Silico-FINAL.md",
        12: "Paper-12-The-Decalogue-of-the-Cosmos-FINAL.md",
    }
    return PAPERS_DIR / papers.get(paper_num, "")

def organize_paper_images(paper_num):
    """Organize images for a specific paper"""
    source = SOURCE_FOLDERS.get(paper_num)
    target = TARGET_FOLDERS.get(paper_num)

    if not source or not source.exists():
        print(f"  ⚠ Paper {paper_num}: Source folder not found")
        return []

    if not target:
        print(f"  ⚠ Paper {paper_num}: Target folder not defined")
        return []

    target.mkdir(parents=True, exist_ok=True)

    # Get all PNG files (including subdirectories)
    images = list(source.rglob("*.png"))

    if not images:
        print(f"  ⚠ Paper {paper_num}: No images found")
        return []

    print(f"\n  Paper {paper_num}: Found {len(images)} images")

    # Rename and move
    renamed_files = []
    for i, img_path in enumerate(sorted(images), 1):
        # Create new name: P01-Name-##.png
        # Extract descriptive name from filename (remove extension, clean up)
        base_name = img_path.stem
        # Clean up the name
        clean_name = re.sub(r'[^\w\s-]', '', base_name).strip()
        clean_name = re.sub(r'\s+', '-', clean_name)
        if not clean_name:
            clean_name = f"Image-{i:02d}"

        new_name = f"P{paper_num:02d}-{clean_name}-{i:02d}.png"
        target_path = target / new_name

        # Copy (don't move, in case we need originals)
        shutil.copy2(img_path, target_path)
        renamed_files.append((new_name, target_path))
        print(f"    → {new_name}")

    return renamed_files

def organize_sonnet_images():
    """Organize Sonnet 4.5 images - need to figure out which paper they belong to"""
    if not SONNET_FOLDER.exists():
        print("\n  ⚠ Sonnet_4.5_Pictures folder not found")
        return {}

    images = list(SONNET_FOLDER.rglob("*.png"))
    print(f"\n  Sonnet 4.5: Found {len(images)} images")
    print("  ⚠ These need manual sorting - filename analysis required")

    # Try to match by filename patterns
    distribution = {}
    for img in images:
        name = img.name.lower()
        # Try to match to papers by filename
        paper_num = None
        if 'p01' in name or 'paper1' in name or 'logos' in name:
            paper_num = 1
        elif 'p02' in name or 'paper2' in name or 'quantum' in name or 'bridge' in name:
            paper_num = 2
        elif 'p03' in name or 'paper3' in name or 'algorithm' in name:
            paper_num = 3
        elif 'p04' in name or 'paper4' in name or 'consciousness' in name:
            paper_num = 4
        elif 'p05' in name or 'paper5' in name or 'soul' in name:
            paper_num = 5
        elif 'p06' in name or 'paper6' in name or 'principalities' in name:
            paper_num = 6
        elif 'p07' in name or 'paper7' in name or 'grace' in name:
            paper_num = 7
        elif 'p08' in name or 'paper8' in name or 'heavens' in name:
            paper_num = 8
        elif 'p09' in name or 'paper9' in name or 'moral' in name:
            paper_num = 9
        elif 'p10' in name or 'paper10' in name or 'silico' in name:
            paper_num = 10
        elif 'p12' in name or 'paper12' in name or 'decalogue' in name:
            paper_num = 12

        if paper_num:
            if paper_num not in distribution:
                distribution[paper_num] = []
            distribution[paper_num].append(img)

    # Move matched images
    for paper_num, imgs in distribution.items():
        target = TARGET_FOLDERS.get(paper_num)
        if target:
            target.mkdir(parents=True, exist_ok=True)
            for i, img in enumerate(sorted(imgs), 1):
                base_name = img.stem
                clean_name = re.sub(r'[^\w\s-]', '', base_name).strip()
                clean_name = re.sub(r'\s+', '-', clean_name)
                if not clean_name:
                    clean_name = f"Sonnet-Image-{i:02d}"

                new_name = f"P{paper_num:02d}-{clean_name}-{i:02d}.png"
                target_path = target / new_name
                shutil.copy2(img, target_path)
                print(f"    Paper {paper_num}: {new_name}")

    unmatched = len(images) - sum(len(v) for v in distribution.values())
    if unmatched > 0:
        print(f"\n  ⚠ {unmatched} images couldn't be auto-matched - need manual review")

    return distribution

def main():
    print("="*80)
    print("ORGANIZING DESKTOP IMAGES INTO ASSET FOLDERS")
    print("="*80)

    all_organized = {}

    # Organize each paper's folder
    for paper_num in sorted(SOURCE_FOLDERS.keys()):
        files = organize_paper_images(paper_num)
        if files:
            all_organized[paper_num] = files

    # Organize Sonnet 4.5 images
    sonnet_dist = organize_sonnet_images()

    # Summary
    print("\n" + "="*80)
    print("ORGANIZATION SUMMARY")
    print("="*80)

    total = 0
    for paper_num in sorted(all_organized.keys()):
        count = len(all_organized[paper_num])
        total += count
        print(f"  Paper {paper_num:02d}: {count} images")

    if sonnet_dist:
        sonnet_total = sum(len(v) for v in sonnet_dist.values())
        total += sonnet_total
        print(f"  Sonnet 4.5 (distributed): {sonnet_total} images")

    print(f"\n  Total organized: {total} images")
    print("\n" + "="*80)
    print("✓ IMAGES ORGANIZED!")
    print("="*80)
    print("\nNext step: Implement images into FINAL papers (Papers 1-3 first)")

if __name__ == "__main__":
    main()
