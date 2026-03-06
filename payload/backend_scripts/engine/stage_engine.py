# engine/stage_engine.py
"""
Stage Engine for Theophysics 110-Stage Framework
=================================================
Generates stage files with proper YAML frontmatter, UUIDs,
Griffiths cross-references, and AI instruction embedding.

Integrates with Ollama for automatic YAML generation.
"""

import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import yaml


class StageEngine:
    """
    Manages creation and maintenance of the 110-stage Theophysics framework.
    Each stage maps to physics parallels (especially Griffiths E&M for Part II).
    """
    
    # Part definitions with stage ranges
    PARTS = {
        "I": {"name": "Foundations", "range": (1, 10), "theme": "Ontological Base"},
        "II": {"name": "Divine Domain", "range": (11, 30), "theme": "God's Nature via E&M"},
        "III": {"name": "Spiritual Dynamics", "range": (31, 50), "theme": "χ-Field Mechanics"},
        "IV": {"name": "Human Ontology", "range": (51, 70), "theme": "Consciousness & Soul"},
        "V": {"name": "Material World", "range": (71, 90), "theme": "Physics Integration"},
        "VI": {"name": "Synthesis", "range": (91, 110), "theme": "χ = Christ Completion"},
    }
    
    # Griffiths E&M chapter mappings for Part II
    GRIFFITHS_MAP = {
        14: {"section": "§1.6", "topic": "Vector Fields", "note": "Trinity as ∇, ∇·, ∇×"},
        20: {"section": "§2.3", "topic": "Electric Potential", "note": "Holiness as voltage V"},
        22: {"section": "§8.1", "topic": "Poynting Vector", "note": "Glory emanation S"},
        25: {"section": "§7.2", "topic": "Magnetic Induction", "note": "Intercessory prayer"},
        29: {"section": "QM §3", "topic": "Measurement", "note": "Judgment as collapse"},
    }

    def __init__(self, settings, db_engine=None, ai_engine=None):
        self.settings = settings
        self.db = db_engine
        self.ai = ai_engine
        
        # Default output path
        if hasattr(settings, 'vault_path') and settings.vault_path:
            self.output_dir = Path(settings.vault_path) / "03_PUBLICATIONS" / "Logos Papers Axiom" / "Theophysics axioms" / "Stages"
        else:
            self.output_dir = Path("./Stages")
    
    def generate_uuid(self) -> str:
        """Generate a full 36-character UUID."""
        return str(uuid.uuid4())
    
    def generate_short_uuid(self) -> str:
        """Generate 8-character UUID for filenames."""
        return str(uuid.uuid4())[:8]
    
    def get_part_for_stage(self, stage_num: int) -> str:
        """Get part number (I-VI) for a stage number."""
        for part, info in self.PARTS.items():
            start, end = info["range"]
            if start <= stage_num <= end:
                return part
        return "?"
    
    def get_griffiths_ref(self, stage_num: int) -> Optional[Dict]:
        """Get Griffiths reference if exists for this stage."""
        return self.GRIFFITHS_MAP.get(stage_num)

    def build_frontmatter(
        self,
        stage_num: int,
        movement: str,
        physics_parallel: str = "",
        core_axiom: str = "",
        papers: List[str] = None,
        status: str = "draft"
    ) -> Dict[str, Any]:
        """
        Build YAML frontmatter for a stage file.
        """
        stage_uuid = self.generate_uuid()
        part = self.get_part_for_stage(stage_num)
        part_info = self.PARTS.get(part, {})
        griffiths = self.get_griffiths_ref(stage_num)
        
        frontmatter = {
            "uuid": stage_uuid,
            "type": "stage",
            "stage": stage_num,
            "part": part,
            "part_name": part_info.get("name", ""),
            "movement": movement,
            "physics_parallel": physics_parallel,
            "core_axiom": core_axiom,
            "papers": papers or [],
            "status": status,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "last_reviewed": datetime.now().strftime("%Y-%m-%d"),
        }
        
        # Add Griffiths reference if available
        if griffiths:
            frontmatter["griffiths"] = {
                "section": griffiths["section"],
                "topic": griffiths["topic"],
                "note": griffiths["note"]
            }
        
        return frontmatter

    def build_stage_content(
        self,
        stage_num: int,
        movement: str,
        physics_parallel: str = "",
        overview: str = "",
        axioms: List[Dict] = None,
        evidence: List[Dict] = None,
        depends_on: List[int] = None,
        enables: List[int] = None,
        dark_elements: List[str] = None,
        light_elements: List[str] = None,
        ai_instructions: str = ""
    ) -> str:
        """
        Build complete stage file content with all sections.
        """
        part = self.get_part_for_stage(stage_num)
        part_info = self.PARTS.get(part, {})
        griffiths = self.get_griffiths_ref(stage_num)
        
        # Build frontmatter
        fm = self.build_frontmatter(stage_num, movement, physics_parallel)
        frontmatter_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
        
        # Build content sections
        content = f"""---
{frontmatter_yaml.strip()}
---

# Stage {stage_num:03d}: {movement}

**Part {part} — {part_info.get('name', '')}** | {part_info.get('theme', '')}

## Overview

{overview or f"[Movement {stage_num} establishes {movement.lower()}. Expand with core insight.]"}

"""
        
        # Physics Parallel section
        content += "## Physics Parallel\n\n"
        content += "| Theophysics Concept | Physics Analog | Equation |\n"
        content += "|---------------------|----------------|----------|\n"
        content += f"| {movement} | {physics_parallel or '[TBD]'} | $ [TBD] $ |\n\n"
        
        # Griffiths reference if available
        if griffiths:
            content += f"""### Griffiths Reference

> **{griffiths['section']}**: {griffiths['topic']}
> 
> {griffiths['note']}

"""
        
        # Core Axioms section
        content += "## Core Axioms\n\n"
        content += "| ID | Axiom | UUID |\n"
        content += "|----|-------|------|\n"
        if axioms:
            for ax in axioms:
                content += f"| {ax.get('id', 'A?.?')} | {ax.get('statement', '[TBD]')} | `{ax.get('uuid', self.generate_uuid())}` |\n"
        else:
            content += f"| A{stage_num}.1 | [Primary axiom for {movement}] | `{self.generate_uuid()}` |\n"
        content += "\n"
        
        # Logical Flow (Mermaid)
        content += f"""## Logical Flow

```mermaid
flowchart TD
    subgraph Stage_{stage_num:03d}["{movement}"]
        A{stage_num}["Core Axiom"] --> T{stage_num}["Derived Theorem"]
        T{stage_num} --> C{stage_num}["Claim"]
    end
"""
        
        # Add dependency arrows if specified
        if depends_on:
            for dep in depends_on[:3]:  # Limit to 3 for readability
                content += f"    Stage_{dep:03d} --> Stage_{stage_num:03d}\n"
        
        content += "```\n\n"
        
        # Evidence Bundle
        content += "## Evidence Bundle\n\n"
        content += "| Source | Type | Strength | UUID |\n"
        content += "|--------|------|----------|------|\n"
        if evidence:
            for ev in evidence:
                content += f"| {ev.get('source', '[TBD]')} | {ev.get('type', 'empirical')} | {ev.get('strength', '⬛⬛⬛⬜⬜')} | `{ev.get('uuid', self.generate_uuid())}` |\n"
        else:
            content += f"| [Primary source] | empirical | ⬛⬛⬛⬜⬜ | `{self.generate_uuid()}` |\n"
        content += "\n"
        
        # Vault Connections
        content += "## Vault Connections\n\n"
        content += "### Depends On\n"
        if depends_on:
            for dep in depends_on:
                content += f"- [[Stage_{dep:03d}]]\n"
        else:
            content += "- [None - foundational stage]\n"
        
        content += "\n### Enables\n"
        if enables:
            for en in enables:
                content += f"- [[Stage_{en:03d}]]\n"
        else:
            content += "- [Downstream stages TBD]\n"
        content += "\n"
        
        # Dark/Light Classification
        content += "## Dark/Light Classification\n\n"
        content += "### 🌑 Dark (Unresolved)\n"
        if dark_elements:
            for d in dark_elements:
                content += f"- {d}\n"
        else:
            content += "- [Open questions for this stage]\n"
        
        content += "\n### ☀️ Light (Resolved)\n"
        if light_elements:
            for l in light_elements:
                content += f"- {l}\n"
        else:
            content += "- [Established truths from this stage]\n"
        content += "\n"
        
        # AI Instructions (embedded for context)
        content += f"""## AI Instructions

> **Context for AI assistants working on this stage:**
>
> {ai_instructions or f"This is Stage {stage_num} ({movement}). When discussing this stage, emphasize the physics parallel to {physics_parallel or 'the relevant physical concept'}. Connect to Part {part} theme: {part_info.get('theme', '')}."}

### Handling Notes
- Always cite UUID when referencing elements from this stage
- Cross-reference Griffiths E&M for Part II stages
- Maintain χ-field notation consistency

### Common Objections
1. [Anticipated objection 1]
2. [Anticipated objection 2]

"""
        
        # Navigation
        prev_stage = stage_num - 1 if stage_num > 1 else None
        next_stage = stage_num + 1 if stage_num < 110 else None
        
        content += "---\n\n"
        content += "**Navigation:** "
        if prev_stage:
            content += f"← [[Stage_{prev_stage:03d}]] | "
        content += f"[[00_MOC_Theophysics|MOC]]"
        if next_stage:
            content += f" | [[Stage_{next_stage:03d}]] →"
        content += "\n\n"
        
        # Semantic block (machine-readable)
        semantic = {
            "uuid": fm["uuid"],
            "type": "stage",
            "stage": stage_num,
            "part": part,
            "movement": movement,
            "physics_parallel": physics_parallel,
            "classifications": [
                {"content": movement, "type": "stage_title"},
                {"content": physics_parallel, "type": "physics_parallel"}
            ]
        }
        
        content += f"""%%semantic
{json.dumps(semantic, indent=2)}
%%
"""
        
        return content

    def create_stage_file(
        self,
        stage_num: int,
        movement: str,
        physics_parallel: str = "",
        **kwargs
    ) -> Path:
        """
        Create a stage file and save to disk.
        Returns path to created file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        content = self.build_stage_content(
            stage_num=stage_num,
            movement=movement,
            physics_parallel=physics_parallel,
            **kwargs
        )
        
        filename = f"Stage_{stage_num:03d}_{movement.replace(' ', '_').replace('/', '-')}.md"
        filepath = self.output_dir / filename
        
        filepath.write_text(content, encoding="utf-8")
        
        # Register in database if available
        if self.db:
            try:
                self._register_stage_in_db(stage_num, movement, filepath)
            except Exception as e:
                print(f"DB registration warning: {e}")
        
        return filepath

    def _register_stage_in_db(self, stage_num: int, movement: str, filepath: Path):
        """Register stage in database for indexing."""
        if not self.db:
            return
        
        # This would use the database_engine to store stage metadata
        # Implementation depends on your DB schema
        pass

    def batch_create_stages(self, stage_definitions: List[Dict]) -> List[Path]:
        """
        Batch create multiple stage files.
        
        stage_definitions: List of dicts with keys:
            - stage_num (required)
            - movement (required)
            - physics_parallel (optional)
            - ... other kwargs
        """
        created = []
        for stage_def in stage_definitions:
            try:
                path = self.create_stage_file(**stage_def)
                created.append(path)
                print(f"✓ Created: {path.name}")
            except Exception as e:
                print(f"✗ Error creating stage {stage_def.get('stage_num')}: {e}")
        
        return created

    def generate_yaml_with_ollama(self, note_content: str) -> Dict[str, Any]:
        """
        Use Ollama to auto-generate YAML frontmatter from note content.
        Requires Ollama to be running locally.
        """
        if not self.ai:
            return {}
        
        # Check if Ollama is available
        if hasattr(self.ai, 'ollama_available') and self.ai.ollama_available:
            prompt = f"""Analyze this note and generate YAML frontmatter.
Return ONLY valid YAML, no explanation.

Required fields:
- type: (stage/axiom/theorem/definition/claim/evidence)
- uuid: (generate a UUID)
- title: (extract main title)
- tags: (list relevant tags)
- status: (draft/review/final)
- domains: (physics/theology/information-theory/consciousness)

Note content:
{note_content[:2000]}

YAML:"""
            
            try:
                response = self.ai.generate_with_ollama(prompt)
                # Parse YAML from response
                yaml_str = response.strip()
                if yaml_str.startswith("```"):
                    yaml_str = yaml_str.split("```")[1]
                    if yaml_str.startswith("yaml"):
                        yaml_str = yaml_str[4:]
                return yaml.safe_load(yaml_str)
            except Exception as e:
                print(f"Ollama YAML generation error: {e}")
                return {}
        
        return {}


# Convenience function for direct usage
def create_stage(stage_num: int, movement: str, **kwargs) -> str:
    """Quick stage creation without full engine setup."""
    from engine.settings import SettingsManager
    settings = SettingsManager()
    settings.load()
    
    engine = StageEngine(settings)
    path = engine.create_stage_file(stage_num, movement, **kwargs)
    return str(path)
