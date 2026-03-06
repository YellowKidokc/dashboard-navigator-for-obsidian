import os
from datetime import datetime

# Define the target folder
target_folder = "O:\\THEOPHYSICS\\Master_Equation_Reality_Blueprint\\Master_Equation_Reality_Blueprint\\06_ADVANCED_MATHEMATICS"

# Define the YAML frontmatter template
yaml_template = """---
# Publishing Control
share: false
publish: true

# Core Metadata
title: "{title}"
description: "AI-will-generate"
author: "David Lowe"
date: "{date}"
updated: "{date}"

# AI Labeling Prompt
ai_analysis_prompt: |
  Please analyze this research note and suggest:
  1. Appropriate tags from: theophysics, quantum-consciousness, bible-prophecy, foundation-crisis, entangled-soul, universal-laws, decoherence, consciousness-interface, end-times, pear-data
  2. Research framework: Quantum-Consciousness-Prophecy, 10 Universal Laws, THEOPHYSICS, or Entangled Soul Theory
  3. Significance level: paradigm-shifting, breakthrough, important, supporting, or preliminary
  4. Prophecy correlation: high, medium, low, or none
  5. Consciousness relevance: critical, important, relevant, or none
  6. Keywords for SEO
  7. Brief description/excerpt
  Content to analyze: "{content}"

# Categorization (AI will fill these)
tags:
  - AI-will-tag
categories:
  - AI-will-categorize
type: AI-will-determine

# Research Framework (AI will suggest)
framework: AI-will-determine
significance: AI-will-assess

# Academic Metadata
draft: true
version: "1.0"

# SEO & Discovery (AI will enhance)
keywords: ["AI-will-suggest-keywords"]
slug: "{slug}"

# Display Options
math: true
mermaid: false
toc: true
comments: true

# Custom Properties (AI will evaluate)
breakthrough_level: "AI-will-assess"
prophecy_correlation: "AI-will-assess"
consciousness_relevance: "AI-will-assess"
bible_refs: ["AI-will-extract"]

# Workflow
status: "active"
priority: "medium"

# AI Processing Flag
ai_labeling_needed: true
ai_processed: false
---

"""

# Get a list of the files in the target folder
files = os.listdir(target_folder)

# Get the current date
current_date = datetime.now().strftime("%Y-%m-%d")

# Loop through the files and add the YAML frontmatter
for file_name in files:
    if file_name.endswith(".md"):
        # Get the full file path
        file_path = os.path.join(target_folder, file_name)

        # Read the content of the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Get the title from the file name
        title = os.path.splitext(file_name)[0].replace("_", " ")

        # Create the slug from the title
        slug = title.lower().replace(" ", "-")

        # Generate the YAML frontmatter
        yaml_frontmatter = yaml_template.format(
            title=title,
            date=current_date,
            content=content,
            slug=slug
        )

        # Prepend the YAML frontmatter to the file content
        new_content = yaml_frontmatter + content

        # Write the new content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"Added YAML frontmatter to '{file_name}'")
