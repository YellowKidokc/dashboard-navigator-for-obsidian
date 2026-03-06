# engine/definition_engine.py

import sqlite3
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from .utils import extract_links, parse_yaml_block


class DefinitionEngine:
    """
    Advanced definition management with:
    - Semantic section parsing
    - Ontology node building
    - Completeness scoring
    - Entity extraction
    - Auto-linking
    """
    
    def __init__(self, settings, db_engine):
        self.settings = settings
        self.db = db_engine

    def scan_for_missing(self):
        """
        Look through all notes and find wiki-links [[term]] that
        do not yet have entries in the definitions table.
        """
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()

        c.execute("SELECT path, title, yaml, tags, links FROM notes")
        rows = c.fetchall()

        # get existing defs
        c.execute("SELECT term FROM definitions")
        existing_terms = {r[0].lower() for r in c.fetchall()}

        for path, title, yaml_str, tags_str, links_str in rows:
            # links_str is JSON of links collected by vault engine
            import json
            try:
                links = json.loads(links_str) if links_str else []
            except Exception:
                links = []

            for link in links:
                term = link.split("|")[0].strip()  # [[term|alias]] support later
                key = term.lower()
                if key not in existing_terms:
                    # create a stub definition
                    self.db.upsert_definition({
                        "term": term,
                        "aliases": [],
                        "classification": "",
                        "body": "",
                        "status": "missing",
                        "file_path": path,
                    })
                    existing_terms.add(key)

        conn.close()

    def extract_definition_from_note(self, note_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract structured definition from a note file.
        Looks for:
        - YAML frontmatter with 'definition' field
        - ## Definition section
        - First paragraph after H1
        """
        if not note_path.exists():
            return None
            
        text = note_path.read_text(encoding="utf-8", errors="ignore")
        
        # Try YAML first
        yaml_data = parse_yaml_block(text)
        if "definition" in yaml_data:
            return {
                "term": note_path.stem,
                "body": yaml_data["definition"],
                "aliases": yaml_data.get("aliases", []),
                "classification": yaml_data.get("type", ""),
            }
        
        # Look for ## Definition section
        def_match = re.search(r'## Definition\s*\n\n?(.*?)(?=\n##|\Z)', text, re.DOTALL)
        if def_match:
            return {
                "term": note_path.stem,
                "body": def_match.group(1).strip(),
                "aliases": [],
                "classification": "",
            }
        
        # Use first paragraph after title
        lines = text.split('\n')
        content_started = False
        paragraphs = []
        current = []
        
        for line in lines:
            if line.startswith('# '):
                content_started = True
                continue
            if content_started:
                if line.strip():
                    current.append(line)
                elif current:
                    paragraphs.append(' '.join(current))
                    break
        
        if paragraphs:
            return {
                "term": note_path.stem,
                "body": paragraphs[0],
                "aliases": [],
                "classification": "",
            }
        
        return None

    def calculate_completeness_score(self, definition: Dict[str, Any]) -> float:
        """
        Calculate how complete a definition is (0.0 to 1.0).
        Based on: body length, aliases, classification, links, examples
        """
        score = 0.0
        
        # Body exists and has substance (0.5)
        body = definition.get("body", "")
        if body:
            word_count = len(body.split())
            if word_count >= 10:
                score += 0.3
            if word_count >= 50:
                score += 0.2
        
        # Has classification (0.15)
        if definition.get("classification"):
            score += 0.15
        
        # Has aliases (0.15)
        aliases = definition.get("aliases", [])
        if aliases and len(aliases) > 0:
            score += 0.15
        
        # Has examples or citations (0.1)
        if "example" in body.lower() or "e.g." in body or "i.e." in body:
            score += 0.05
        if re.search(r'\[\[.+?\]\]', body):  # Has wiki links
            score += 0.05
        
        # Has references (0.1)
        if re.search(r'\[.+?\]\(.+?\)', body):  # Has markdown links
            score += 0.1
        
        return min(score, 1.0)

    def build_ontology_node(self, term: str) -> Dict[str, Any]:
        """
        Build an ontology node for a term showing:
        - Related terms (via links)
        - Parent/child relationships
        - Cross-references
        - Category membership
        """
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        # Get the definition
        c.execute("SELECT term, body, classification, aliases FROM definitions WHERE term = ?", (term,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return {"term": term, "exists": False}
        
        term, body, classification, aliases_json = row
        
        import json
        aliases = json.loads(aliases_json) if aliases_json else []
        
        # Find notes that link to this term
        c.execute("SELECT path, title FROM notes WHERE links LIKE ?", (f'%{term}%',))
        referring_notes = [{"path": r[0], "title": r[1]} for r in c.fetchall()]
        
        # Find terms this definition links to
        linked_terms = re.findall(r'\[\[(.+?)\]\]', body or "")
        
        # Find related by classification
        if classification:
            c.execute("SELECT term FROM definitions WHERE classification = ? AND term != ?", (classification, term))
            related_by_type = [r[0] for r in c.fetchall()]
        else:
            related_by_type = []
        
        conn.close()
        
        return {
            "term": term,
            "exists": True,
            "aliases": aliases,
            "classification": classification,
            "body": body,
            "referring_notes": referring_notes,
            "links_to": linked_terms,
            "related_by_type": related_by_type,
            "completeness": self.calculate_completeness_score({
                "body": body,
                "classification": classification,
                "aliases": aliases
            })
        }

    def get_definition_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the definition database."""
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        stats = {}
        
        # Total counts by status
        c.execute("SELECT status, COUNT(*) FROM definitions GROUP BY status")
        stats["by_status"] = dict(c.fetchall())
        
        # By classification
        c.execute("SELECT classification, COUNT(*) FROM definitions WHERE classification != '' GROUP BY classification")
        stats["by_classification"] = dict(c.fetchall())
        
        # Completeness distribution
        c.execute("SELECT term, body, classification, aliases FROM definitions")
        completeness_scores = []
        for row in c.fetchall():
            score = self.calculate_completeness_score({
                "body": row[1],
                "classification": row[2],
                "aliases": row[3]
            })
            completeness_scores.append(score)
        
        if completeness_scores:
            stats["avg_completeness"] = sum(completeness_scores) / len(completeness_scores)
            stats["completeness_distribution"] = {
                "0-25%": len([s for s in completeness_scores if s < 0.25]),
                "25-50%": len([s for s in completeness_scores if 0.25 <= s < 0.5]),
                "50-75%": len([s for s in completeness_scores if 0.5 <= s < 0.75]),
                "75-100%": len([s for s in completeness_scores if s >= 0.75]),
            }
        else:
            stats["avg_completeness"] = 0
            stats["completeness_distribution"] = {}
        
        conn.close()
        return stats

    def list_definitions(self) -> List[Dict[str, Any]]:
        return self.db.list_definitions()

    def save_definition(self, data: Dict[str, Any]):
        if not data["term"]:
            return
        payload = {
            "term": data["term"],
            "aliases": data.get("aliases", []),
            "classification": data.get("classification"),
            "body": data.get("body"),
            "status": "complete" if data.get("body") else "draft",
            "file_path": data.get("file_path"),
        }
        self.db.upsert_definition(payload)

    def generate_definition_stub_note(self, term: str, output_dir: Path) -> Path:
        """
        Generate a markdown note stub for a definition.
        """
        note_path = output_dir / f"{term.replace(' ', '-')}.md"
        
        template = f"""---
term: {term}
type: 
aliases: []
status: draft
---

# {term}

## Definition

[Define {term} here]

## Context

[Provide context and usage]

## Related Concepts

- [[concept1]]
- [[concept2]]

## References

[Add references and citations]

## Footnotes

"""
        note_path.write_text(template, encoding="utf-8")
        return note_path

