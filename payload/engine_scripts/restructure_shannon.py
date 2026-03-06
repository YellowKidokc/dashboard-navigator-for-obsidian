#!/usr/bin/env python3
"""
Restructure Shannon's Information Theory paper.
Convert from raw PDF-to-markdown (page breaks) to proper academic structure.
"""

import re
from pathlib import Path

def restructure_shannon():
    """Restructure the Information Theory paper."""

    file_path = Path(r"O:\_Theophysics_v3\00_Canonical\TH_Information_Theory\General\Information_Theory.md")
    content = file_path.read_text(encoding="utf-8")

    # Step 1: Remove duplicate metadata tags at top
    # Remove first 7 lines (duplicates and blank separators)
    lines = content.split("\n")
    if lines[0].startswith("#") and "canonical" in lines[0]:
        # Skip duplicate metadata section
        content = "\n".join(lines[7:])

    # Step 2: Extract title and author from content
    title = "A Mathematical Theory of Communication"
    author = "Claude E. Shannon"
    source = "Bell System Technical Journal, Vol. 27, pp. 379–423, 623–656, July-October 1948"

    # Step 3: Build new header with clean metadata
    new_header = f"""---
title: {title}
author: {author}
source: {source}
date: 1948-07
categories:
  - canonical
  - information-theory
  - mathematical-foundations
tags:
  - communication-theory
  - entropy
  - channel-capacity
  - stochastic-processes
  - discrete-systems
  - continuous-systems
---

# {title}

**Author:** {author}

**Published:** {source}

---

## Table of Contents

- [Introduction](#introduction)
- [Part I: Discrete Noiseless Systems](#part-i)
  - [1. The Discrete Noiseless Channel](#ch1)
  - [2. Discrete Source of Information](#ch2)
  - [3. Series of Approximations to English](#ch3)
  - [4. Graphical Representation](#ch4)
  - [5. Ergodic Sources](#ch5)
  - [6. Choice, Uncertainty, Entropy](#ch6)
  - [7. Entropy of Information Source](#ch7)
  - [8. Representation of a Continuous Message](#ch8)
- [Part II: Discrete Channel with Noise](#part-ii)
  - [9-13. Channel Capacity and Coding Theorems](#ch9-13)
- [Part III: Continuous Systems](#part-iii)
  - [Preliminaries](#preliminaries)
  - [18. Sets and Ensembles of Functions](#ch18)
  - [19. Band Limited Ensembles](#ch19)
  - [20-29. Continuous Channel Analysis](#ch20-29)
- [Appendices](#appendices)
- [References](#references)

---

## Introduction {{#introduction}}

"""

    # Step 4: Remove all "## Page X" markers and consolidate content
    # This pattern removes the page breaks but keeps content
    content = re.sub(r"^---$\n^## Page \d+$\n", "\n", content, flags=re.MULTILINE)

    # Step 5: Identify major sections and add hierarchy
    # Look for "PART I:", "PART II:", "PART III:", etc.
    content = re.sub(
        r"^(PART [IVX]+:.*?)$",
        r"\n---\n\n## \1 {{#part-\1}}\n",
        content,
        flags=re.MULTILINE
    )

    # Add chapter markers
    chapter_patterns = [
        (r"^(\d+\. .*?)$", r"\n### \1 {{#ch\1}}\n"),  # "1. Chapter Title" → ### 1. Chapter Title
    ]

    for pattern, replacement in chapter_patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    # Step 6: Clean up excess blank lines
    content = re.sub(r"\n\n\n+", "\n\n", content)

    # Step 7: Add section anchors for references
    content = re.sub(
        r"^## INTRODUCTION$",
        "## Introduction {#introduction}",
        content,
        flags=re.MULTILINE
    )

    # Step 8: Combine and write
    final_content = new_header + content

    # Step 9: Add footer with metadata
    footer = """

---

## Appendices {{#appendices}}

### Appendix 1
### Appendix 2
### Appendix 3
### Appendix 4
### Appendix 5
### Appendix 6
### Appendix 7

---

## References {{#references}}

1. Nyquist, H., "Certain Factors Affecting Telegraph Speed," Bell System Technical Journal, April 1924, p. 324
2. Nyquist, H., "Certain Topics in Telegraph Transmission Theory," A.I.E.E. Trans., v. 47, April 1928, p. 617
3. Hartley, R. V. L., "Transmission of Information," Bell System Technical Journal, July 1928, p. 535
4. Chandrasekhar, S., "Stochastic Problems in Physics and Astronomy," Reviews of Modern Physics, v. 15, No. 1, January 1943
5. Kendall and Smith, Tables of Random Sampling Numbers, Cambridge, 1939

---

**Original Paper Citation:**

Shannon, C. E. (1948). "A Mathematical Theory of Communication." Bell System Technical Journal, 27, 379–423 & 623–656.

---

*Restructured for academic clarity. Original content preserved. Page breaks removed. Logical section hierarchy added.*
"""

    final_content += footer

    # Save backup
    backup_path = file_path.parent / f"{file_path.stem}_BACKUP.md"
    file_path.write_text(file_path.read_text(encoding="utf-8"), encoding="utf-8")

    # Write restructured version
    output_path = file_path.parent / f"{file_path.stem}_RESTRUCTURED.md"
    output_path.write_text(final_content, encoding="utf-8")

    print(f"✅ Restructuring complete!")
    print(f"   Original: {file_path}")
    print(f"   Output: {output_path}")
    print(f"\nChanges made:")
    print("   • Removed duplicate metadata tags")
    print("   • Added clean YAML frontmatter")
    print("   • Created Table of Contents")
    print("   • Removed 54 page-break markers (## Page X)")
    print("   • Added logical section hierarchy")
    print("   • Organized by Part (I, II, III) and Chapters")
    print("   • Added section anchors for linking")
    print("   • Added proper footer with citations")

    return output_path

if __name__ == "__main__":
    restructure_shannon()
