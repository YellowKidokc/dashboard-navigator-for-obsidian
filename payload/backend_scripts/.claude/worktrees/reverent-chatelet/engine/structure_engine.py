# engine/structure_engine.py

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

FOOTNOTE_SECTION_HEADER = "## Footnotes"


class StructureEngine:
    def __init__(self, settings, db_engine):
        self.settings = settings
        self.db = db_engine

    def build_structure_for_note(self, note_path: Path):
        """
        v1: ensure the note has a basic heading and a Footnotes section.
        Later you can expand to full theorem/proof/narrative templates, etc.
        """
        if not note_path.exists():
            return

        text = note_path.read_text(encoding="utf-8", errors="ignore")

        # ensure at least one H1 title
        lines = text.splitlines()
        if not any(l.startswith("# ") for l in lines):
            title = note_path.stem.replace("-", " ")
            lines.insert(0, f"# {title}")
            lines.insert(1, "")

        # ensure Footnotes section exists
        if FOOTNOTE_SECTION_HEADER not in text:
            lines.append("")
            lines.append(FOOTNOTE_SECTION_HEADER)
            lines.append("")
            lines.append("<!-- Footnotes will be aggregated here -->")

        new_text = "\n".join(lines)
        note_path.write_text(new_text, encoding="utf-8")
    
    def build_definition_structure(
        self,
        term: str,
        symbol: str = "",
        output_dir: Path = None,
        template_path: Path = None
    ) -> Path:
        """
        Build a complete Definition 2.0 structure with all 10 sections.
        
        Args:
            term: The term to define
            symbol: Mathematical symbol (if any)
            output_dir: Where to create the file
            template_path: Custom template (optional)
        
        Returns:
            Path to created definition file
        """
        if output_dir is None:
            vault_root = Path(self.settings.get("vault_path", "."))
            output_dir = vault_root / "Definitions"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load template
        if template_path and template_path.exists():
            template = template_path.read_text(encoding='utf-8')
        else:
            # Use default template from templates directory
            default_template = Path(__file__).parent.parent / "templates" / "definition_template.md"
            if default_template.exists():
                template = default_template.read_text(encoding='utf-8')
            else:
                template = self._get_default_template()
        
        # Fill template
        slug = term.lower().replace(' ', '-').replace("'", "")
        date = datetime.now().strftime("%Y-%m-%d")
        
        content = template.replace("{{TERM_SLUG}}", slug)
        content = content.replace("{{SYMBOL}}", symbol)
        content = content.replace("{{NAME}}", term)
        content = content.replace("{{DATE}}", date)
        
        # Write file
        output_path = output_dir / f"def-{slug}.md"
        output_path.write_text(content, encoding='utf-8')
        
        return output_path
    
    def ensure_definition_sections(self, note_path: Path) -> bool:
        """
        Ensure a definition note has all 10 required sections.
        Adds missing sections without overwriting existing content.
        
        Returns:
            True if modifications were made
        """
        if not note_path.exists():
            return False
        
        text = note_path.read_text(encoding="utf-8", errors="ignore")
        
        required_sections = [
            "## 1. Canonical Definition",
            "## 2. Axioms",
            "## 3. Mathematical Structure",
            "## 4. Domain Interpretations",
            "## 5. Operationalization",
            "## 6. Failure Modes",
            "## 7. Integration Map",
            "## 8. Usage Drift Log",
            "## 9. External Comparison",
            "## 10. Notes & Examples"
        ]
        
        missing_sections = [s for s in required_sections if s not in text]
        
        if not missing_sections:
            return False
        
        # Add missing sections at the end
        lines = text.splitlines()
        
        for section in missing_sections:
            lines.append("")
            lines.append(section)
            lines.append("")
            
            # Add section-specific placeholders
            if "Canonical Definition" in section:
                lines.append("> **[Term] is ...**")
            elif "Drift Log" in section:
                lines.append("> _Auto-populated by the Definition Engine._")
                lines.append("")
                lines.append("| Date | File | Context | Deviation |")
                lines.append("|------|------|---------|-----------|")
            elif "External Comparison" in section:
                lines.append("| Source | Definition | Equation |")
                lines.append("|--------|------------|----------|")
            else:
                lines.append("[Content to be added]")
        
        new_text = "\n".join(lines)
        note_path.write_text(new_text, encoding="utf-8")
        
        return True
    
    def _get_default_template(self) -> str:
        """Fallback template if file not found."""
        return """---
type: definition
id: def-{{TERM_SLUG}}
symbol: {{SYMBOL}}
name: {{NAME}}
aliases:
  -
domains:
  - physics
  - information-theory
  - theophysics
status: draft
last_reviewed: {{DATE}}
related_terms:
  -
internet_refs:
  - label: ""
    url: ""
---

# {{SYMBOL}} — {{NAME}}

## 1. Canonical Definition

> **{{NAME}} is ...**
> *(one-sentence canonical statement)*

---

## 2. Axioms

### 2.1 Ontological (What Exists)
- **Axiom {{SYMBOL}}1:** ...

### 2.2 Mathematical (What the Variable Can/Can't Do)
- **Axiom {{SYMBOL}}2:** ...

### 2.3 Conservation & Symmetry
- **Axiom {{SYMBOL}}3:** ...

---

## 3. Mathematical Structure

### 3.1 Primary Definition Equation(s)

$$
{{SYMBOL}} = ...
$$

### 3.2 Equivalent Forms

| Domain | Form |
|--------|------|
| Physics | $ {{SYMBOL}} = ... $ |
| Information Theory | $ {{SYMBOL}} = ... $ |

### 3.3 Dynamical Form

$$
\\frac{d{{SYMBOL}}}{dt} = ...
$$

### 3.4 Thresholds & Stability

- **Critical Value:** ${{SYMBOL}}_{\\text{crit}} = ...$
- **Stability Condition:** $\\frac{d{{SYMBOL}}}{dt} < 0$ when ...

---

## 4. Domain Interpretations

### 4.1 Physics
- **Meaning:**
- **Equation:**
- **Example:**

### 4.2 Information Theory
- **Meaning:**
- **Equation:**
- **Example:**

### 4.3 Neuroscience
- **Meaning:**
- **Equation:**
- **Example:**

### 4.4 Psychology
- **Meaning:**
- **Equation:**
- **Example:**

### 4.5 Sociology / Economics
- **Meaning:**
- **Equation:**
- **Example:**

### 4.6 Theophysics / Theology
- **Meaning:**
- **Equation:**
- **Example:**

---

## 5. Operationalization

### How to Measure or Estimate {{SYMBOL}}

| Domain | Measurement Method |
|--------|-------------------|
| Individual Mind | |
| Society | |
| Physical System | |
| Experiment | |

---

## 6. Failure Modes

### What It Means for {{SYMBOL}} to "Break" or "Go Wrong"

| Domain | Failure Mode | Consequence |
|--------|-------------|-------------|
| Physics | | |
| Psychology | | |
| Society | | |

---

## 7. Integration Map

### 7.1 Appears In

- [[Master-Equation]]
- [[Paper-01-Logos-Principle]]

### 7.2 Equations Using {{SYMBOL}}

| Eq ID | File | Variables | Context |
|-------|------|-----------|---------|
| | | | |

---

## 8. Usage Drift Log

> _This section is auto-populated by the Definition Engine._

| Date | File | Context | Deviation |
|------|------|---------|-----------|
| | | | |

---

## 9. External Comparison

### 9.1 Standard Definitions

| Source | Definition | Equation |
|--------|------------|----------|
| Wikipedia | | |
| SEP | | |

### 9.2 Where Theophysics Agrees

-

### 9.3 Where Theophysics Diverges (Intentionally)

-

---

## 10. Notes & Examples

### Analogies

-

### Diagrams

-

### Open Questions

-
"""

