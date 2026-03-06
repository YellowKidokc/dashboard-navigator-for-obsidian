"""
Clean Tag Generator
Only keeps REAL concept words - filters out:
- Hex codes / color codes
- Compound phrases with hyphens (like "many-worlds-interpretation")
- Technical junk (refs, notes, appendix, etc.)
- Single letters / numbers
- Document structure words
"""

import re
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
from collections import defaultdict

# Words that are ALLOWED (real single-word concepts) - these bypass all filters
ALLOWED_CONCEPTS = {
    # Core Theophysics
    "logos", "trinity", "grace", "faith", "soul", "spirit", "god", "christ", "jesus",
    "father", "son", "resurrection", "redemption", "salvation", "sin", "entropy",
    "negentropy", "coherence", "consciousness", "observer", "measurement", "quantum",
    "wave", "particle", "collapse", "superposition", "entanglement", "decoherence",
    "theophysics", "equation",
    
    # Physics
    "gravity", "mass", "energy", "force", "momentum", "velocity", "acceleration",
    "spacetime", "relativity", "electromagnetic", "photon", "electron", "proton",
    "neutron", "atom", "molecule", "field", "tensor", "lagrangian", "hamiltonian",
    "thermodynamics", "temperature", "pressure", "volume", "heat",
    "physics", "cosmology", "astronomy", "mechanics", "dynamics", "kinematics",
    "hubble", "kolmogorov", "planck", "einstein", "heisenberg", "schrodinger",
    "boundary", "cosmological", "participatory", "environmental",
    
    # Math/Logic
    "equation", "function", "operator", "variable", "constant", "integral",
    "derivative", "vector", "matrix", "eigenvalue", "probability", "statistics",
    "mathematics", "algebra", "calculus", "geometry", "topology",
    
    # Philosophy
    "ontology", "epistemology", "metaphysics", "phenomenology", "hermeneutics",
    "teleology", "causality", "determinism", "freedom", "will", "mind", "body",
    "philosophy", "ethics", "logic", "reason", "belief",
    
    # Theology
    "covenant", "prophecy", "revelation", "incarnation", "atonement", "justification",
    "sanctification", "glorification", "eschatology", "soteriology", "christology",
    "pneumatology", "ecclesiology", "anthropology", "theology", "doctrine",
    
    # General concepts
    "truth", "light", "love", "hope", "peace", "joy", "wisdom", "knowledge",
    "understanding", "creation", "order", "chaos", "pattern", "structure",
    "system", "process", "transformation", "evolution", "emergence", "complexity",
    "glossary",
    
    # Papers - keep these
    "paper", "papers",
}

# Compound phrases to REJECT (X-of-Y patterns, etc.)
COMPOUND_PATTERNS = [
    r'.+-of-.+',           # physics-of-belief, faith-of-truth
    r'.+-in-.+',           # faith-in-action
    r'.+-and-.+',          # grace-and-truth
    r'.+-for-.+',          # search-for-meaning
    r'.+-to-.+',           # path-to-salvation
    r'.+-as-.+',           # christ-as-light
    r'.+-the-.+',          # beyond-the-veil
    r'.+-with-.+',         # communion-with-god
    r'.+-from-.+',         # escape-from-entropy
    r'.+-by-.+',           # justified-by-faith
    r'.+-vs-.+',           # grace-vs-entropy
    r'.+-at-.+',           # look-at-this
    r'.+-on-.+',           # based-on-faith
    r'.+-.+-.*-.+-',       # anything with 3+ hyphens
]

# Document structure / junk words to ALWAYS exclude
JUNK_PATTERNS = [
    r'^[a-f0-9]{6,}$',  # Hex codes
    r'^\d+$',  # Pure numbers
    r'^[a-z]{1,2}$',  # Single/double letters
    r'^ref-',  # References
    r'^note-',  # Notes
    r'^cite',  # Citations
    r'^appendix',  # Appendix
    r'^section',  # Sections
    r'^chapter',  # Chapters
    r'^figure',  # Figures
    r'^table-',  # Tables
    r'^page-',  # Pages
    r'^\d',  # Starts with number
]

JUNK_WORDS = {
    "abstract", "acknowledgments", "appendix", "bibliography", "conclusion",
    "contents", "context", "dashboard", "definition", "deliverables", "deploy",
    "example", "executive", "experimental", "external", "figure", "footnote",
    "header", "implementation", "index", "introduction", "metadata", "method",
    "note", "overview", "page", "paragraph", "preface", "reference", "section",
    "summary", "table", "title", "todo", "version", "draft", "final", "edit",
    "copy", "backup", "archive", "old", "new", "test", "temp", "tmp",
    "github", "plugin", "config", "settings", "options", "parameters",
    "install", "setup", "build", "run", "start", "stop", "init",
    "readme", "changelog", "license", "contributing", "authors",
    "00", "01", "02", "03", "04", "05", "06", "07", "08", "09",
    "it", "or", "we", "ii", "iv", "vi", "vl", "but", "the", "and", "for",
    # Plugin/tool names
    "enveloppe", "dataview", "obsidian", "templater", "excalidraw",
    # Reference sources (not concepts)
    "arxiv", "doi", "isbn", "pmid", "bibcode",
    # Project-specific junk
    "dorothy", "david", "lowe", "yellowkid",
    # Generic words that aren't concepts
    "dark", "general", "master", "main", "core", "base", "type", "kind",
    "status", "state", "mode", "level", "stage", "phase",
    # Acronyms / abbreviations (not real words)
    "apct", "pdf", "html", "css", "json", "yaml", "xml", "sql", "api",
    "url", "uri", "http", "https", "www", "ftp", "ssh",
}


class CleanTagGenerator:
    """Generate tag notes with smart filtering for real concepts only."""
    
    YAML_TAGS_PATTERN = re.compile(r'^tags:\s*\[([^\]]+)\]', re.MULTILINE)
    YAML_TAGS_LIST_PATTERN = re.compile(r'^tags:\s*\n((?:\s*-\s*.+\n?)+)', re.MULTILINE)
    INLINE_TAG_PATTERN = re.compile(r'#([A-Za-z][A-Za-z0-9_\-/]+)')
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
    
    def __init__(self, vault_path: str, output_folder: str = "_TAG_NOTES", 
                 min_uses: int = 10, max_hyphens: int = 0):
        self.vault_path = Path(vault_path)
        self.output_folder = self.vault_path / output_folder
        self.min_uses = min_uses
        self.max_hyphens = max_hyphens  # Max hyphens allowed (0 = single words only)
        self.tags: Dict[str, dict] = {}
        
    def _normalize(self, tag: str) -> str:
        tag = tag.lstrip('#').lower()
        return re.sub(r'[^a-z0-9\-]', '-', tag).strip('-')
    
    def _is_valid_tag(self, tag: str) -> bool:
        """Check if tag is a valid concept word - STRICT: single words only."""
        tag_lower = tag.lower().strip()
        
        # If in allowed concepts, always accept
        if tag_lower in ALLOWED_CONCEPTS:
            return True
        
        # STRICT: Any hyphen = reject (unless in allowed list above)
        if '-' in tag_lower:
            return False
        
        # Check junk patterns
        for pattern in JUNK_PATTERNS:
            if re.match(pattern, tag_lower):
                return False
        
        # Check junk words
        if tag_lower in JUNK_WORDS:
            return False
        
        # Too short
        if len(tag_lower) < 3:
            return False
        
        # Too long (probably not a real word)
        if len(tag_lower) > 20:
            return False
        
        # Check if it looks like a hex code
        if re.match(r'^[a-f0-9]+$', tag_lower) and len(tag_lower) >= 5:
            return False
        
        # Must be alphabetic (real words don't have numbers)
        if not tag_lower.isalpha():
            return False
        
        # Accept single words
        return True
    
    def _extract_yaml_tags(self, content: str) -> List[str]:
        tags = []
        fm_match = self.FRONTMATTER_PATTERN.match(content)
        if not fm_match:
            return tags
        frontmatter = fm_match.group(1)
        
        inline_match = self.YAML_TAGS_PATTERN.search(frontmatter)
        if inline_match:
            tag_str = inline_match.group(1)
            tags.extend([t.strip().strip('"\'') for t in tag_str.split(',') if t.strip()])
        
        list_match = self.YAML_TAGS_LIST_PATTERN.search(frontmatter)
        if list_match:
            for line in list_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    tag = line[1:].strip().strip('"\'')
                    if tag:
                        tags.append(tag)
        return tags
    
    def _extract_inline_tags(self, content: str) -> List[str]:
        content = self.FRONTMATTER_PATTERN.sub('', content)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        return self.INLINE_TAG_PATTERN.findall(content)
    
    def scan_vault(self):
        """Scan vault and collect tag usage."""
        exclude = ['_TAG_NOTES', '.obsidian', '.git', 'venv', '__pycache__', 'node_modules']
        md_files = list(self.vault_path.rglob('*.md'))
        
        valid_count = 0
        invalid_count = 0
        
        for file_path in md_files:
            rel_path = file_path.relative_to(self.vault_path)
            if any(part in exclude for part in rel_path.parts):
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
            except:
                continue
            
            all_tags = self._extract_yaml_tags(content) + self._extract_inline_tags(content)
            rel_str = str(rel_path)
            
            for tag in all_tags:
                norm = self._normalize(tag)
                if not norm or len(norm) < 3:
                    continue
                
                # Check if valid
                if not self._is_valid_tag(norm):
                    invalid_count += 1
                    continue
                
                valid_count += 1
                    
                if norm not in self.tags:
                    self.tags[norm] = {
                        'name': tag,
                        'count': 0,
                        'files': set(),
                        'aliases': set()
                    }
                
                self.tags[norm]['count'] += 1
                self.tags[norm]['files'].add(rel_str)
                if tag != self.tags[norm]['name']:
                    self.tags[norm]['aliases'].add(tag)
        
        print(f"Scanned {len(md_files)} files")
        print(f"Valid tag uses: {valid_count}, Filtered out: {invalid_count}")
        print(f"Unique valid tags: {len(self.tags)}")
    
    def generate_notes(self):
        """Generate notes only for tags with min_uses or more."""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Filter by min uses
        filtered = {k: v for k, v in self.tags.items() if v['count'] >= self.min_uses}
        print(f"Tags with {self.min_uses}+ uses: {len(filtered)}")
        
        # Clear old tag notes (except special files)
        for old_file in self.output_folder.glob("*.md"):
            if not old_file.name.startswith("_") and not old_file.name.startswith("SYSTEM") and not old_file.name.startswith("TRINITY") and not old_file.name.startswith("COHERENCE"):
                old_file.unlink()
        
        count = 0
        for norm, data in filtered.items():
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', data['name'])
            if len(safe_name) > 50:
                safe_name = safe_name[:50]
            
            file_path = self.output_folder / f"{safe_name}.md"
            
            files_list = sorted(data['files'])[:30]
            files_md = "\n".join([f"- [[{f}]]" for f in files_list])
            if len(data['files']) > 30:
                files_md += f"\n- ... and {len(data['files']) - 30} more"
            
            aliases = ", ".join(sorted(data['aliases']))
            
            content = f"""---
tag: "{data['name']}"
uses: {data['count']}
aliases: [{aliases}]
---

# {data['name']}

## Description
_Add description_

## Stats
- **Uses:** {data['count']}
- **Files:** {len(data['files'])}

## Files
{files_md}
"""
            file_path.write_text(content, encoding='utf-8')
            count += 1
        
        print(f"Generated {count} clean tag notes")
        return count


def main():
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    gen = CleanTagGenerator(vault, "_TAG_NOTES", min_uses=10, max_hyphens=1)
    gen.scan_vault()
    gen.generate_notes()
    
    # Show top tags
    top = sorted(gen.tags.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
    print("\nTop 20 Tags:")
    for tag, data in top:
        print(f"  {tag}: {data['count']}")


if __name__ == "__main__":
    main()
