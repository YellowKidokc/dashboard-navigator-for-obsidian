#!/usr/bin/env python3
"""
Master Equation Reality Blueprint Organizer
Implements the THEOPHYSICS naming and organization system
"""

import os
import re
import shutil
import sys
from pathlib import Path
from datetime import datetime

# Set console encoding to handle Unicode characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

class MasterEquationOrganizer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.master_folder = self.base_path / "Master_Equation_Reality_Blueprint" / "Master_Equation_Reality_Blueprint"

        # Folder short names for Master Equation folder
        self.folder_short_names = {
            "01_DISCOVERY": "DIS",  # Discovery
            "02_FUNDAMENTAL_AXIOMS": "AXI",  # Axioms
            "03_MASTER_EQUATION": "EQ",  # Equation
            "04_SCIENTIFIC_CONVERGENCE": "CONV",  # Convergence
            "05_VARIABLE_FRAMEWORK": "VAR",  # Variables
            "06_ADVANCED_MATHEMATICS": "MATH",  # Mathematics
            "07_CORE_INSIGHTS": "INS",  # Insights
            "08_EMPIRICAL_VALIDATION": "VAL",  # Validation
            "09_APPLICATIONS": "APP",  # Applications
            "10_CONCLUSION": "CONC",  # Conclusion
            "APPENDICES": "APPX"  # Appendices
        }

        # Character mappings
        self.character_mapping = {
            "trinity": ["GF", "JC", "HS"],
            "logos": ["JC", "HS"],
            "grace": ["GF", "JC", "HS"],
            "sovereignty": ["GF"],
            "love": ["JC", "HS"],
            "consciousness": ["HS"],
            "adversary": ["ADV"],
            "sin": ["ADV"],
            "entropy": ["ADV"]
        }

    def clean_title(self, title):
        """Clean and format paper titles for descriptive names"""
        # Remove file extensions and clean up
        title = re.sub(r'\.md$', '', title)
        title = re.sub(r'[_\-\d]+', ' ', title)  # Replace underscores/hyphens with spaces
        title = re.sub(r'\s+', ' ', title).strip()  # Clean up multiple spaces

        # Keep the full descriptive title (not shortened)
        return title.title()

    def generate_folder_short_name(self, folder_name):
        """Generate folder short name based on folder"""
        return self.folder_short_names.get(folder_name, "GEN")

    def detect_characters(self, content):
        """Detect characters mentioned in content"""
        characters = set()
        content_lower = content.lower()

        for keyword, chars in self.character_mapping.items():
            if keyword in content_lower:
                characters.update(chars)

        return list(characters)

    def generate_yaml_frontmatter(self, title, folder_short_name, folder_name, content):
        """Generate YAML frontmatter for papers"""
        characters = self.detect_characters(content)

        yaml_content = f"""---
folder_series: "{folder_short_name}"
paper_number: "01"
title: "{title}"
characters: {characters}
physics_domains: ["quantum-mechanics", "field-theory", "mathematical-physics"]
spiritual_domains: ["theophysics", "trinity", "consciousness"]
publication_status: "draft"
academic_level: "graduate"
experimental_protocol: false
completion_percentage: 75
related_papers: []
deep_dive_available: true
tags: ["theophysics", "{folder_short_name.lower()}", "master-equation"]
created: "{datetime.now().strftime('%Y-%m-%d')}"
folder_source: "{folder_name}"
---

"""
        return yaml_content

    def copy_images_to_folders(self):
        """Copy images to appropriate folders"""
        print("Organizing images...")

        # Root folder images
        root_images = [
            "Law 1 Gravity Grace.png",
            "Law 2 Quantum ↔ Faith Collapse.png",
            "Law 3 Thermodynamics ↔ Sin.png",
            "Law 4 Information ↔ Truth  Logos.png",
            "Quantum Field Theory (QFT).png",
            "Quantum Mechanics Lexicon.png"
        ]

        # Copy root images to Scientific Convergence
        convergence_folder = self.master_folder / "04_SCIENTIFIC_CONVERGENCE"
        convergence_folder.mkdir(exist_ok=True)

        for img in root_images:
            src = self.master_folder / img
            if src.exists():
                dst = convergence_folder / img
                shutil.copy2(src, dst)
                print(f"  Copied {img} to 04_SCIENTIFIC_CONVERGENCE")

        # Copy SVG assets from 02_FUNDAMENTAL_AXIOMS to appropriate papers
        axioms_assets = self.master_folder / "02_FUNDAMENTAL_AXIOMS" / "Assets"
        if axioms_assets.exists():
            for svg_file in axioms_assets.glob("*.svg"):
                # Find matching paper
                paper_name = svg_file.stem.replace("_", " ").title()
                print(f"  Found SVG: {svg_file.name} - Looking for matching paper...")

                # Try to find a paper that matches this SVG
                axioms_folder = self.master_folder / "02_FUNDAMENTAL_AXIOMS"
                for md_file in axioms_folder.glob("*.md"):
                    if not md_file.name.startswith("_"):  # Skip merged files
                        content = md_file.read_text(encoding='utf-8', errors='ignore').lower()
                        if any(keyword in content for keyword in ["logos", "axiom", "principle"]):
                            # Copy SVG to same folder as paper
                            dst = md_file.parent / svg_file.name
                            shutil.copy2(svg_file, dst)
                            print(f"    Copied {svg_file.name} to {md_file.name}")
                            break

    def organize_papers(self):
        """Organize and rename papers in each folder"""
        print("Organizing papers...")

        for folder_name in os.listdir(self.master_folder):
            folder_path = self.master_folder / folder_name

            if not folder_path.is_dir() or folder_name.startswith('.'):
                continue

            print(f"\nProcessing folder: {folder_name}")

            folder_short_name = self.generate_folder_short_name(folder_name)

            # Process markdown files in folder
            md_files = list(folder_path.glob("*.md"))
            md_files = [f for f in md_files if not f.name.startswith("_")]  # Skip merged files

            for i, md_file in enumerate(md_files, 1):
                # Read content
                try:
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                except:
                    print(f"  Could not read {md_file.name}")
                    continue

                # Generate new name with folder number, ME, title, folder short name, and sequential number
                clean_title = self.clean_title(md_file.stem)

                # Extract folder number from folder name (e.g., "01_DISCOVERY" -> "01")
                folder_number = folder_name.split('_')[0] if '_' in folder_name else "XX"

                new_name = f"{folder_number}-ME-{clean_title}-{folder_short_name}-{i:02d}.md"
                new_path = md_file.parent / new_name

                # Generate YAML frontmatter
                yaml_content = self.generate_yaml_frontmatter(
                    clean_title, folder_short_name, folder_name, content
                )

                # Update content with YAML
                if not content.startswith("---"):
                    new_content = yaml_content + content
                else:
                    # Replace existing frontmatter
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        new_content = yaml_content + parts[2]
                    else:
                        new_content = yaml_content + content

                # Write new file
                new_path.write_text(new_content, encoding='utf-8')
                print(f"  Created: {new_name}")

                # Remove old file if different name
                if md_file != new_path:
                    md_file.unlink()

    def create_mocs(self):
        """Create Maps of Content for navigation"""
        print("\nCreating Maps of Content...")

        mocs_content = """# Master Equation Reality Blueprint - Navigation Hub

## 📚 Folder Series Overview
- **DIS** = Discovery (foundational insights)
- **AXI** = Axioms (fundamental principles)
- **EQ** = Equation (core mathematical framework)
- **CONV** = Convergence (scientific unification)
- **VAR** = Variables (framework components)
- **MATH** = Mathematics (advanced calculations)
- **INS** = Insights (core understandings)
- **VAL** = Validation (empirical testing)
- **APP** = Applications (practical uses)
- **CONC** = Conclusion (final synthesis)
- **APPX** = Appendices (supporting material)

## 📁 Folder Structure

### 01_DISCOVERY (DIS Series)
*Papers organized as 01-ME-[Title]-DIS-[Number].md*

### 02_FUNDAMENTAL_AXIOMS (AXI Series)
*Papers organized as 02-ME-[Title]-AXI-[Number].md*

### 03_MASTER_EQUATION (EQ Series)
*Papers organized as 03-ME-[Title]-EQ-[Number].md*

### 04_SCIENTIFIC_CONVERGENCE (CONV Series)
*Papers organized as 04-ME-[Title]-CONV-[Number].md*

### 05_VARIABLE_FRAMEWORK (VAR Series)
*Papers organized as 05-ME-[Title]-VAR-[Number].md*

### 06_ADVANCED_MATHEMATICS (MATH Series)
*Papers organized as 06-ME-[Title]-MATH-[Number].md*

### 07_CORE_INSIGHTS (INS Series)
*Papers organized as 07-ME-[Title]-INS-[Number].md*

### 08_EMPIRICAL_VALIDATION (VAL Series)
*Papers organized as 08-ME-[Title]-VAL-[Number].md*

### 09_APPLICATIONS (APP Series)
*Papers organized as 09-ME-[Title]-APP-[Number].md*

### 10_CONCLUSION (CONC Series)
*Papers organized as 10-ME-[Title]-CONC-[Number].md*

### APPENDICES (APPX Series)
*Papers organized as XX-ME-[Title]-APPX-[Number].md*

## 🏷️ Character Tags
- #GF = God Father
- #JC = Jesus Christ
- #HS = Holy Spirit
- #ADV = Adversary

## 🔗 Quick Links
- [[Master Equation Reality Blueprint - Navigation Hub]]
- [[Publication Pipeline Status]]
- [[Experimental Protocols Index]]

## 📝 Naming Convention
Format: **[FOLDER-NUMBER]-ME-[PAPER-TITLE]-[FOLDER-SHORT-NAME]-[SEQUENTIAL-NUMBER].md**
- FOLDER-NUMBER = Number of the folder (01, 02, 03, etc.)
- ME = Your initials
- PAPER-TITLE = Descriptive title of the paper
- FOLDER-SHORT-NAME = Short version of folder name (DIS, AXI, EQ, etc.)
- SEQUENTIAL-NUMBER = Sequential number within that folder (01, 02, 03, etc.)

## 📋 Examples
- 01-ME-The Pattern of Unity-DIS-01.md
- 02-ME-Logos Tripartite Principle-AXI-01.md
- 03-ME-Master Equation Forms-EQ-01.md
- 04-ME-Twelve Unified Theories-CONV-01.md
"""

        moc_path = self.master_folder / "000-MASTER-NAVIGATION-HUB.md"
        moc_path.write_text(mocs_content, encoding='utf-8')
        print(f"  Created: {moc_path.name}")

    def run_organization(self):
        """Run the complete organization process"""
        print("Starting Master Equation Organization...")
        print(f"Working in: {self.master_folder}")

        # Step 1: Copy images
        self.copy_images_to_folders()

        # Step 2: Organize papers
        self.organize_papers()

        # Step 3: Create MOCs
        self.create_mocs()

        print("\nMaster Equation organization complete!")
        print("Next steps:")
        print("  1. Review renamed papers")
        print("  2. Update cross-references")
        print("  3. Test navigation links")
        print("  4. Apply to other folders")

if __name__ == "__main__":
    organizer = MasterEquationOrganizer("O:\\THEOPHYSICS")
    organizer.run_organization()
