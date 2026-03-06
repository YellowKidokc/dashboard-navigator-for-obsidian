#!/usr/bin/env python3
"""
Implement organized images into Papers 1, 2, 3 FINAL versions
Add image references at appropriate locations with proper paths
"""

import re
from pathlib import Path
import os

# Paths
PAPERS_DIR = Path(os.getenv("THEOPHYSICS_PAPERS_DIR", r"O:\_Theophysics_v3\05_PUBLICATIONS\Logos_Papers\COMPLETE_LOGOS_PAPERS_FINAL"))
IMAGES_BASE = Path(os.getenv("THEOPHYSICS_ASSETS_BASE", r"O:\_Theophysics_v3\_META\Assets\Images\logos papers"))

# Relative path from papers to images
IMAGE_REL_PATH = "../../../../Assets/Images/logos papers"

# Paper mappings
PAPERS = {
    1: {
        "file": "Paper-01-The-Logos-Principle-FINAL.md",
        "folder": "P1_Logos_Principle",
        "insertion_points": [
            ("## 2. BACKGROUND", "After background introduction"),
            ("### 2.1 The Measurement Problem", "After measurement problem"),
            ("### 2.2 The General Relativity", "After GR-QM schism"),
            ("## 4. THE LOGOS FIELD", "After Logos Field intro"),
            ("### 4.1 Information as Substrate", "After information substrate"),
            ("### 4.2 Quantum Superposition", "After superposition"),
            ("### 4.3 Participatory Observation", "After participatory mechanism"),
            ("## 5. THE PARTICIPATORY OBSERVATION", "After participatory section"),
            ("### 5.2 The Three-Stage Collapse", "After three-stage collapse"),
            ("### 5.3 Shared Reality", "After shared reality"),
            ("### 5.4 Entanglement", "After entanglement"),
            ("## 6. UNIFYING GR AND QM", "After GR-QM unification"),
        ]
    },
    2: {
        "file": "Paper-02-The-Quantum-Bridge-FINAL.md",
        "folder": "P2_Quantum_Bridge",
        "insertion_points": [
            ("## 🔬 Part I: The Physics Foundation", "After Part I intro"),
            ("### 1. The Observer Problem", "After observer problem"),
            ("## 🎯 Part II: The Eight Proofs", "After Part II intro"),
            ("### PROOF 1:", "After Proof 1"),
            ("### PROOF 2:", "After Proof 2"),
            ("### PROOF 3:", "After Proof 3"),
            ("### PROOF 4:", "After Proof 4"),
            ("### PROOF 5:", "After Proof 5"),
            ("### PROOF 6:", "After Proof 6"),
            ("### PROOF 7:", "After Proof 7"),
            ("### PROOF 8:", "After Proof 8"),
        ]
    },
    3: {
        "file": "Paper-03-The-Algorithm-of-Reality-FINAL.md",
        "folder": "P3_Algorithm_Reality",
        "insertion_points": [
            ("## 1. INTRODUCTION", "After introduction"),
            ("## 2. KOLMOGOROV COMPLEXITY", "After Kolmogorov section"),
            ("## 3. THE LOGOS COMPRESSION DRIVE", "After compression drive"),
            ("## 4. LANDAUER'S PRINCIPLE", "After Landauer section"),
            ("## 5. GR-QM UNIFICATION", "After GR-QM section"),
            ("## 6. BIOLOGICAL COMPRESSION", "After biological compression"),
        ]
    }
}

def get_images_for_paper(paper_num):
    """Get all images for a paper"""
    folder = IMAGES_BASE / PAPERS[paper_num]["folder"]
    if not folder.exists():
        return []

    images = sorted(folder.glob("P*.png"))
    return images

def create_image_markdown(image_path, paper_num, image_num):
    """Create markdown for an image"""
    rel_path = f"{IMAGE_REL_PATH}/{PAPERS[paper_num]['folder']}/{image_path.name}"

    # Extract descriptive name from filename
    name = image_path.stem
    # Remove P01- prefix and -## suffix
    clean_name = re.sub(rf'^P{paper_num:02d}-', '', name)
    clean_name = re.sub(r'-\d+$', '', clean_name)
    clean_name = re.sub(r'-', ' ', clean_name).title()

    return f"""
![{clean_name}]({rel_path})

**Figure {paper_num}.{image_num}: {clean_name}**

*Visualization: David Lowe & Claude (Anthropic), November 2025*

---

"""

def implement_images_in_paper(paper_num):
    """Add images to a paper at appropriate locations"""
    paper_info = PAPERS[paper_num]
    paper_path = PAPERS_DIR / paper_info["file"]

    if not paper_path.exists():
        print(f"  ⚠ Paper {paper_num}: File not found: {paper_path}")
        return

    print(f"\n  Paper {paper_num}: {paper_info['file']}")

    # Read paper
    content = paper_path.read_text(encoding='utf-8')
    original_content = content

    # Get images
    images = get_images_for_paper(paper_num)
    if not images:
        print(f"    ⚠ No images found in {paper_info['folder']}")
        return

    print(f"    Found {len(images)} images")

    # Find insertion points and add images
    image_idx = 0
    for search_text, description in paper_info["insertion_points"]:
        if image_idx >= len(images):
            break

        if search_text in content:
            # Find the position after this section
            pos = content.find(search_text)
            if pos != -1:
                # Find the end of this section (next ## or end of content)
                next_section = content.find("\n##", pos + len(search_text))
                if next_section == -1:
                    next_section = len(content)

                # Insert image after this section
                image_md = create_image_markdown(images[image_idx], paper_num, image_idx + 1)
                insert_pos = next_section
                content = content[:insert_pos] + image_md + content[insert_pos:]
                print(f"    ✓ Added image {image_idx + 1} after: {description}")
                image_idx += 1

    # Add remaining images at the end (before references/conclusion)
    if image_idx < len(images):
        # Find a good place near the end (before References or Conclusion)
        end_markers = ["## REFERENCES", "## References", "## CONCLUSION", "## Conclusion", "---\n\n##"]
        insert_pos = len(content)
        for marker in end_markers:
            pos = content.rfind(marker)
            if pos != -1:
                insert_pos = pos
                break

        for img in images[image_idx:]:
            image_md = create_image_markdown(img, paper_num, image_idx + 1)
            content = content[:insert_pos] + image_md + content[insert_pos:]
            print(f"    ✓ Added image {image_idx + 1} near end")
            image_idx += 1

    # Write back if changed
    if content != original_content:
        paper_path.write_text(content, encoding='utf-8')
        print(f"    ✓ Paper {paper_num} updated with {image_idx} images")
    else:
        print(f"    - No changes made")

def main():
    print("="*80)
    print("IMPLEMENTING IMAGES INTO PAPERS 1, 2, 3")
    print("="*80)

    for paper_num in [1, 2, 3]:
        implement_images_in_paper(paper_num)

    print("\n" + "="*80)
    print("✓ IMAGES IMPLEMENTED INTO PAPERS 1-3!")
    print("="*80)
    print("\nReady for your review before continuing to Papers 4-12")

if __name__ == "__main__":
    main()
