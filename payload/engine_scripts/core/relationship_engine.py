"""
Theophysics Relationship Engine
================================
Comprehensive scanner that:
1. Knows the folder structure (Axioms, Lagrangians, Logos Papers, etc.)
2. Detects relationships between notes using embeddings
3. Finds triadic gaps (Father-Son-Spirit mappings)
4. Checks axiom consistency
5. Extracts hidden YAML and footnotes
6. Discovers connections you can't see in Obsidian
7. Exports findings for reuse
"""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict


# =============================================================================
# FOLDER STRUCTURE AWARENESS
# =============================================================================

THEOPHYSICS_STRUCTURE = {
    "00_ADMIN": {
        "type": "admin",
        "purpose": "Project management, version history, indexes",
        "expected_files": ["PROJECT_CHARTER.md", "VERSION_HISTORY.md", "MASTER_INDEX.yaml"]
    },
    "01_AXIOMS": {
        "type": "axioms",
        "purpose": "Foundational axioms and axiom dependencies",
        "expected_files": ["Ten_Master_Axioms.md", "Trinity_Axiom_Set.md", "Moral_Conservation_Axiom.md"]
    },
    "02_LAGRANGIANS": {
        "type": "math",
        "purpose": "Mathematical formulations - LLC, operators, Hamiltonians",
        "expected_files": ["Lagrangian_LLC.md", "Trinity_Actualization_Operator.md", "Grace_Operator.md"]
    },
    "02_LIBRARY": {
        "type": "library",
        "purpose": "Glossary, references, definitions",
        "subfolders": {
            "Glossary": "term definitions",
            "Master EQ": "master equation work"
        }
    },
    "03_LOGOS_PAPERS": {
        "type": "papers",
        "purpose": "The 12 Logos Papers for publication",
        "papers": {
            "P01": "Logos First Principle",
            "P02": "Quantum Bridge",
            "P03": "Algorithmic Reality",
            "P04": "Hard Problem",
            "P05": "Soul Observer",
            "P06": "Principalities Physical Operators",
            "P07": "Grace Counterforce",
            "P08": "Stretched Heavens",
            "P09": "Moral Universe",
            "P10": "Creatio Ex Silico",
            "P11": "Protocols Verification",
            "P12": "Decalogue Cosmos"
        }
    },
    "03_PUBLICATIONS": {
        "type": "publications",
        "purpose": "Published/final versions of papers"
    },
    "04_ENIGMAS": {
        "type": "enigmas",
        "purpose": "The 12 Enigmas - paradoxes and open questions"
    },
    "05_SUPPLEMENTAL": {
        "type": "supplemental",
        "purpose": "Historical arguments, moral geometry, phenomenology"
    },
    "06_GLOSSARY": {
        "type": "glossary",
        "purpose": "Master glossary and term definitions"
    },
    "07_DATA": {
        "type": "data",
        "purpose": "PEAR, GCP, PROP-COSMOS datasets and analysis"
    }
}

# =============================================================================
# TEN LAWS / AXIOMS
# =============================================================================

TEN_LAWS = {
    "L1": {"name": "Law of Algorithmic Coherence", "domain": "information", "pair": "L8"},
    "L2": {"name": "Law of Consilience", "domain": "epistemology", "pair": "L9"},
    "L3": {"name": "Law of Participatory Actualization", "domain": "ontology", "pair": "L10"},
    "L4": {"name": "Law of the Conscious Substrate", "domain": "consciousness", "pair": "L7"},
    "L5": {"name": "Law of the Soul Operator", "domain": "soul", "pair": "L6"},
    "L6": {"name": "Law of Spiritual Conflict", "domain": "warfare", "pair": "L5"},
    "L7": {"name": "Law of Moral Consequence", "domain": "ethics", "pair": "L4"},
    "L8": {"name": "Law of Negentropic Triumph", "domain": "thermodynamics", "pair": "L1"},
    "L9": {"name": "Law of Grace", "domain": "soteriology", "pair": "L2"},
    "L10": {"name": "Law of Temporal Co-Creation", "domain": "eschatology", "pair": "L3"}
}

CORE_AXIOMS = [
    "Coherence is ontologically primary",
    "The Logos Field is the substrate of reality",
    "Triadic Ontology is necessary (Father-Son-Spirit)",
    "Consciousness is fundamental, not emergent",
    "Information cannot be destroyed, only transformed",
    "Grace superabounds over sin exponentially",
    "The observer participates in reality creation",
    "Moral choices have physical consequences",
    "Time is co-created between God and creation",
    "The church functions as quantum error correction"
]

# =============================================================================
# TRIADIC ONTOLOGY
# =============================================================================

TRIADS = {
    "primary": ["Father", "Son", "Spirit"],
    "ontological": ["Necessity", "Contingency", "Relation"],
    "epistemological": ["Knower", "Known", "Knowledge"],
    "cosmological": ["Creator", "Creation", "Sustainer"],
    "soteriological": ["Judge", "Savior", "Sanctifier"],
    "moral": ["Law", "Grace", "Wisdom"]
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class NoteMetadata:
    """Extracted metadata from a note."""
    path: str
    title: str
    folder_type: str
    folder_name: str

    # YAML frontmatter
    yaml_data: Dict = field(default_factory=dict)

    # Content analysis
    word_count: int = 0
    has_equations: bool = False
    equations: List[str] = field(default_factory=list)

    # Links and tags
    wikilinks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Footnotes
    footnotes: List[Dict] = field(default_factory=list)

    # Hidden YAML blocks (%%yaml ... %%)
    hidden_yaml: List[Dict] = field(default_factory=list)

    # Semantic blocks
    semantic_blocks: List[Dict] = field(default_factory=list)

    # Law/Axiom references
    law_references: List[str] = field(default_factory=list)
    axiom_references: List[str] = field(default_factory=list)

    # Triad analysis
    triad_coverage: Dict[str, List[str]] = field(default_factory=dict)
    triad_gaps: List[str] = field(default_factory=list)

    # Greek letters used
    greek_letters: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """A discovered relationship between notes."""
    source: str
    target: str
    rel_type: str  # "similar", "contradicts", "depends_on", "triad_partner", "axiom_link"
    strength: float  # 0.0 to 1.0
    evidence: str
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ScanResult:
    """Complete scan results."""
    vault_path: str
    scanned_at: str
    total_notes: int
    notes: List[NoteMetadata]
    relationships: List[Relationship]
    axiom_violations: List[Dict]
    triad_gaps: List[Dict]
    missing_definitions: List[str]
    folder_stats: Dict[str, int]


# =============================================================================
# CONTENT EXTRACTORS
# =============================================================================

class ContentExtractor:
    """Extracts various content types from markdown."""

    # Greek letters
    GREEK = {
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
        'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'π': 'pi',
        'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 'φ': 'phi',
        'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
        'Γ': 'Gamma', 'Δ': 'Delta', 'Θ': 'Theta', 'Λ': 'Lambda',
        'Ξ': 'Xi', 'Π': 'Pi', 'Σ': 'Sigma', 'Φ': 'Phi', 'Ψ': 'Psi', 'Ω': 'Omega'
    }

    @staticmethod
    def extract_yaml_frontmatter(content: str) -> Tuple[Dict, str]:
        """Extract YAML frontmatter and return (yaml_dict, remaining_content)."""
        if not content.startswith('---'):
            return {}, content

        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_str = parts[1].strip()
                yaml_data = yaml.safe_load(yaml_str) or {}
                return yaml_data, parts[2]
        except:
            pass
        return {}, content

    @staticmethod
    def extract_hidden_yaml(content: str) -> List[Dict]:
        """Extract hidden YAML blocks: %%yaml ... %%"""
        blocks = []
        pattern = r'%%yaml\s*(.*?)\s*%%'
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            try:
                data = yaml.safe_load(match.group(1))
                if data:
                    blocks.append(data)
            except:
                pass
        return blocks

    @staticmethod
    def extract_semantic_blocks(content: str) -> List[Dict]:
        """Extract %%semantic ... %% blocks."""
        blocks = []
        pattern = r'%%semantic\s*(.*?)\s*%%'
        for match in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(match.group(1))
                blocks.append(data)
            except:
                pass
        return blocks

    @staticmethod
    def extract_footnotes(content: str) -> List[Dict]:
        """Extract footnotes [^1]: definition style."""
        footnotes = []
        # Footnote references
        refs = re.findall(r'\[\^(\w+)\](?!:)', content)
        # Footnote definitions
        defs = re.findall(r'\[\^(\w+)\]:\s*(.+?)(?=\n\[\^|\n\n|$)', content, re.DOTALL)

        for ref_id, text in defs:
            footnotes.append({
                "id": ref_id,
                "text": text.strip(),
                "used": ref_id in refs
            })
        return footnotes

    @staticmethod
    def extract_wikilinks(content: str) -> List[str]:
        """Extract [[wikilinks]]."""
        # Match [[link]] or [[link|display]] but not [[link#anchor]]
        matches = re.findall(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]', content)
        return list(set(matches))

    @staticmethod
    def extract_tags(content: str) -> List[str]:
        """Extract #tags."""
        # Skip tags in code blocks
        clean = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        clean = re.sub(r'`[^`]+`', '', clean)
        matches = re.findall(r'#([a-zA-Z][a-zA-Z0-9_/-]+)', clean)
        return list(set(matches))

    @staticmethod
    def extract_equations(content: str) -> List[str]:
        """Extract LaTeX equations."""
        equations = []
        # Block equations: $$ ... $$
        equations.extend(re.findall(r'\$\$(.+?)\$\$', content, re.DOTALL))
        # Inline equations: $ ... $ (but not $$)
        inline = re.findall(r'(?<!\$)\$([^$]+)\$(?!\$)', content)
        equations.extend(inline)
        return equations

    @staticmethod
    def extract_greek_letters(content: str) -> List[str]:
        """Find Greek letters used in content."""
        found = []
        for greek, name in ContentExtractor.GREEK.items():
            if greek in content:
                found.append(name)
        return list(set(found))

    @staticmethod
    def extract_law_references(content: str) -> List[str]:
        """Find references to the Ten Laws."""
        refs = []
        content_lower = content.lower()

        for law_id, law_info in TEN_LAWS.items():
            # Check for "L1", "Law 1", "Law I", "Law of Algorithmic Coherence"
            if law_id.lower() in content_lower:
                refs.append(law_id)
            if law_info["name"].lower() in content_lower:
                refs.append(law_id)

        return list(set(refs))

    @staticmethod
    def extract_axiom_references(content: str) -> List[str]:
        """Find references to core axioms."""
        refs = []
        content_lower = content.lower()

        for i, axiom in enumerate(CORE_AXIOMS):
            # Check for partial matches
            key_phrase = axiom.split()[0:3]  # First 3 words
            if ' '.join(key_phrase).lower() in content_lower:
                refs.append(f"A{i+1}")

        return refs

    @staticmethod
    def analyze_triad_coverage(content: str) -> Tuple[Dict[str, List[str]], List[str]]:
        """Analyze which triads are covered and find gaps."""
        coverage = {}
        gaps = []
        content_lower = content.lower()

        for triad_name, triad_elements in TRIADS.items():
            found = [e for e in triad_elements if e.lower() in content_lower]
            coverage[triad_name] = found

            # If 1 or 2 elements found but not all 3, it's a gap
            if 0 < len(found) < 3:
                missing = [e for e in triad_elements if e not in found]
                gaps.append(f"{triad_name}: missing {missing}")

        return coverage, gaps


# =============================================================================
# RELATIONSHIP DISCOVERY
# =============================================================================

class RelationshipDiscovery:
    """Discovers relationships between notes."""

    def __init__(self):
        self.use_embeddings = False
        self.model = None

    def enable_embeddings(self):
        """Enable embedding-based similarity (requires sentence-transformers)."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.use_embeddings = True
            print("[EMBEDDINGS] Loaded sentence-transformer model")
        except ImportError:
            print("[WARN] sentence-transformers not installed, using keyword matching")
            self.use_embeddings = False

    def find_similar_notes(self, notes: List[NoteMetadata], threshold: float = 0.6) -> List[Relationship]:
        """Find similar notes based on content."""
        relationships = []

        if self.use_embeddings and self.model:
            # Use embeddings
            import numpy as np

            # Build embeddings
            embeddings = {}
            for note in notes:
                # Use title + tags as representation
                text = note.title + " " + " ".join(note.tags)
                embeddings[note.path] = self.model.encode(text)

            # Compare all pairs
            paths = list(embeddings.keys())
            for i in range(len(paths)):
                for j in range(i+1, len(paths)):
                    p1, p2 = paths[i], paths[j]
                    e1, e2 = embeddings[p1], embeddings[p2]

                    # Cosine similarity
                    score = float(np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2)))

                    if score >= threshold:
                        relationships.append(Relationship(
                            source=p1,
                            target=p2,
                            rel_type="similar",
                            strength=score,
                            evidence=f"Embedding similarity: {score:.2f}"
                        ))
        else:
            # Use tag overlap
            for i, n1 in enumerate(notes):
                for n2 in notes[i+1:]:
                    if n1.tags and n2.tags:
                        overlap = set(n1.tags) & set(n2.tags)
                        if len(overlap) >= 2:
                            score = len(overlap) / max(len(n1.tags), len(n2.tags))
                            relationships.append(Relationship(
                                source=n1.path,
                                target=n2.path,
                                rel_type="similar",
                                strength=score,
                                evidence=f"Shared tags: {overlap}"
                            ))

        return relationships

    def find_law_connections(self, notes: List[NoteMetadata]) -> List[Relationship]:
        """Find notes connected through law references."""
        relationships = []

        # Group notes by laws they reference
        law_to_notes = defaultdict(list)
        for note in notes:
            for law in note.law_references:
                law_to_notes[law].append(note.path)

        # Connect notes that share law references
        for law, paths in law_to_notes.items():
            if len(paths) > 1:
                for i, p1 in enumerate(paths):
                    for p2 in paths[i+1:]:
                        relationships.append(Relationship(
                            source=p1,
                            target=p2,
                            rel_type="law_connection",
                            strength=0.7,
                            evidence=f"Both reference {law}: {TEN_LAWS[law]['name']}"
                        ))

        return relationships

    def find_triad_partners(self, notes: List[NoteMetadata]) -> List[Relationship]:
        """Find notes that could complete each other's triadic gaps."""
        relationships = []

        # For each note with gaps, find notes that have the missing elements
        for n1 in notes:
            if not n1.triad_gaps:
                continue

            for gap_info in n1.triad_gaps:
                # Parse gap: "primary: missing ['Spirit']"
                parts = gap_info.split(': missing ')
                if len(parts) != 2:
                    continue
                triad_name = parts[0]

                # Find notes that mention the missing elements
                for n2 in notes:
                    if n1.path == n2.path:
                        continue

                    coverage = n2.triad_coverage.get(triad_name, [])
                    # If n2 has what n1 is missing
                    if coverage:
                        relationships.append(Relationship(
                            source=n1.path,
                            target=n2.path,
                            rel_type="triad_partner",
                            strength=0.6,
                            evidence=f"Completes {triad_name} triad: {n2.title} has {coverage}"
                        ))

        return relationships


# =============================================================================
# MAIN SCANNER
# =============================================================================

class TheophysicsScanner:
    """
    Main scanner that combines all analysis capabilities.
    Knows the folder structure, extracts relationships, finds gaps.
    """

    SKIP_FOLDERS = {'.obsidian', '.trash', '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'Archive'}

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.extractor = ContentExtractor()
        self.discovery = RelationshipDiscovery()

        self.notes: List[NoteMetadata] = []
        self.relationships: List[Relationship] = []
        self.axiom_violations: List[Dict] = []
        self.folder_stats: Dict[str, int] = defaultdict(int)

    def identify_folder_type(self, file_path: Path) -> Tuple[str, str]:
        """Identify what type of folder this file is in."""
        rel_path = file_path.relative_to(self.vault_path)
        parts = rel_path.parts

        if not parts:
            return "root", "root"

        top_folder = parts[0]

        # Check against known structure
        for folder_name, info in THEOPHYSICS_STRUCTURE.items():
            if top_folder.startswith(folder_name.split('_')[0]):  # Match "00", "01", etc.
                return info["type"], top_folder

        return "unknown", top_folder

    def scan_note(self, file_path: Path) -> Optional[NoteMetadata]:
        """Scan a single note and extract all metadata."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except:
            return None

        # Basic info
        folder_type, folder_name = self.identify_folder_type(file_path)

        # Extract YAML frontmatter
        yaml_data, body = self.extractor.extract_yaml_frontmatter(content)

        # Extract everything
        hidden_yaml = self.extractor.extract_hidden_yaml(content)
        semantic_blocks = self.extractor.extract_semantic_blocks(content)
        footnotes = self.extractor.extract_footnotes(content)
        wikilinks = self.extractor.extract_wikilinks(body)
        tags = self.extractor.extract_tags(content)
        equations = self.extractor.extract_equations(body)
        greek = self.extractor.extract_greek_letters(content)
        law_refs = self.extractor.extract_law_references(content)
        axiom_refs = self.extractor.extract_axiom_references(content)
        triad_coverage, triad_gaps = self.extractor.analyze_triad_coverage(content)

        # Also check YAML for tags
        if 'tags' in yaml_data:
            yaml_tags = yaml_data['tags']
            if isinstance(yaml_tags, list):
                tags = list(set(tags + yaml_tags))

        return NoteMetadata(
            path=str(file_path),
            title=file_path.stem,
            folder_type=folder_type,
            folder_name=folder_name,
            yaml_data=yaml_data,
            word_count=len(body.split()),
            has_equations=len(equations) > 0,
            equations=equations[:10],  # Limit to first 10
            wikilinks=wikilinks,
            tags=tags,
            footnotes=footnotes,
            hidden_yaml=hidden_yaml,
            semantic_blocks=semantic_blocks,
            law_references=law_refs,
            axiom_references=axiom_refs,
            triad_coverage=triad_coverage,
            triad_gaps=triad_gaps,
            greek_letters=greek
        )

    def scan_vault(self, progress_callback=None) -> ScanResult:
        """Scan entire vault."""
        print(f"[SCAN] Scanning vault: {self.vault_path}")

        self.notes = []
        self.folder_stats = defaultdict(int)

        # Find all markdown files
        md_files = []
        for md_file in self.vault_path.rglob("*.md"):
            if any(skip in md_file.parts for skip in self.SKIP_FOLDERS):
                continue
            md_files.append(md_file)

        total = len(md_files)
        print(f"[SCAN] Found {total} markdown files")

        # Scan each file
        for i, md_file in enumerate(md_files):
            if progress_callback:
                progress_callback(i, total, md_file.name)

            # Progress every 500 files
            if i % 500 == 0:
                print(f"  [{i}/{total}] Scanning...")

            note = self.scan_note(md_file)
            if note:
                self.notes.append(note)
                self.folder_stats[note.folder_name] += 1

        print(f"[SCAN] Scanned {len(self.notes)} notes")

        # Discover relationships
        print("[RELATIONSHIPS] Finding similar notes...")
        self.relationships = self.discovery.find_similar_notes(self.notes)

        print("[RELATIONSHIPS] Finding law connections...")
        self.relationships.extend(self.discovery.find_law_connections(self.notes))

        print("[RELATIONSHIPS] Finding triad partners...")
        self.relationships.extend(self.discovery.find_triad_partners(self.notes))

        print(f"[RELATIONSHIPS] Found {len(self.relationships)} relationships")

        # Check for axiom violations
        self.check_axiom_consistency()

        # Build result
        return ScanResult(
            vault_path=str(self.vault_path),
            scanned_at=datetime.now().isoformat(),
            total_notes=len(self.notes),
            notes=self.notes,
            relationships=self.relationships,
            axiom_violations=self.axiom_violations,
            triad_gaps=self.get_all_triad_gaps(),
            missing_definitions=self.find_missing_definitions(),
            folder_stats=dict(self.folder_stats)
        )

    def check_axiom_consistency(self):
        """Check for potential axiom violations."""
        self.axiom_violations = []

        contradiction_markers = [
            ("not coherence", "A1", "Denies coherence primacy"),
            ("consciousness emerges", "A4", "Claims consciousness is emergent"),
            ("information destroyed", "A5", "Claims information can be destroyed"),
            ("sin greater than grace", "A6", "Inverts grace/sin relationship"),
            ("observer independent", "A7", "Denies observer participation"),
        ]

        for note in self.notes:
            try:
                content = Path(note.path).read_text(encoding='utf-8', errors='ignore').lower()

                for marker, axiom, description in contradiction_markers:
                    if marker in content:
                        self.axiom_violations.append({
                            "note": note.title,
                            "path": note.path,
                            "axiom": axiom,
                            "issue": description,
                            "marker": marker
                        })
            except:
                pass

    def get_all_triad_gaps(self) -> List[Dict]:
        """Collect all triad gaps across the vault."""
        gaps = []
        for note in self.notes:
            if note.triad_gaps:
                gaps.append({
                    "note": note.title,
                    "path": note.path,
                    "gaps": note.triad_gaps
                })
        return gaps

    def find_missing_definitions(self) -> List[str]:
        """Find terms that are linked but don't have definition files."""
        # Collect all wikilinks
        all_links = set()
        for note in self.notes:
            all_links.update(note.wikilinks)

        # Collect all note titles
        all_titles = {note.title.lower() for note in self.notes}

        # Find missing
        missing = []
        for link in all_links:
            if link.lower() not in all_titles:
                # Skip obvious non-definitions
                if '/' not in link and '\\' not in link and not link.startswith('_'):
                    missing.append(link)

        return sorted(missing)[:100]  # Top 100


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

class ScanExporter:
    """Export scan results in various formats."""

    def __init__(self, result: ScanResult, output_dir: Path):
        self.result = result
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_json(self) -> Path:
        """Export full results to JSON."""
        output_path = self.output_dir / f"scan_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Convert to serializable format
        data = {
            "vault_path": self.result.vault_path,
            "scanned_at": self.result.scanned_at,
            "total_notes": self.result.total_notes,
            "folder_stats": self.result.folder_stats,
            "relationships_count": len(self.result.relationships),
            "axiom_violations": self.result.axiom_violations,
            "triad_gaps": self.result.triad_gaps,
            "missing_definitions": self.result.missing_definitions,
            "notes_summary": [
                {
                    "title": n.title,
                    "folder": n.folder_name,
                    "type": n.folder_type,
                    "tags": n.tags,
                    "laws": n.law_references,
                    "greek": n.greek_letters,
                    "has_equations": n.has_equations,
                    "footnotes_count": len(n.footnotes),
                    "hidden_yaml_count": len(n.hidden_yaml)
                }
                for n in self.result.notes
            ],
            "relationships": [
                asdict(r) for r in self.result.relationships
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def export_markdown_report(self) -> Path:
        """Export human-readable markdown report."""
        output_path = self.output_dir / "_SCAN_REPORT.md"

        report = f"""# Theophysics Vault Scan Report
Generated: {self.result.scanned_at}

## Summary
- **Total Notes:** {self.result.total_notes}
- **Relationships Found:** {len(self.result.relationships)}
- **Axiom Violations:** {len(self.result.axiom_violations)}
- **Triad Gaps:** {len(self.result.triad_gaps)}
- **Missing Definitions:** {len(self.result.missing_definitions)}

## Folder Distribution
| Folder | Notes |
|--------|-------|
"""
        for folder, count in sorted(self.result.folder_stats.items()):
            report += f"| {folder} | {count} |\n"

        report += """
## Law References Across Vault
"""
        law_counts = defaultdict(int)
        for note in self.result.notes:
            for law in note.law_references:
                law_counts[law] += 1

        for law_id in sorted(law_counts.keys()):
            report += f"- **{law_id}** ({TEN_LAWS.get(law_id, {}).get('name', 'Unknown')}): {law_counts[law_id]} notes\n"

        report += """
## Axiom Violations
"""
        if self.result.axiom_violations:
            for v in self.result.axiom_violations[:20]:
                report += f"- **{v['note']}**: {v['issue']} ({v['axiom']})\n"
        else:
            report += "None detected.\n"

        report += """
## Triad Gaps (Notes with Incomplete Triads)
"""
        if self.result.triad_gaps:
            for g in self.result.triad_gaps[:20]:
                report += f"- **{g['note']}**: {', '.join(g['gaps'])}\n"
        else:
            report += "None detected.\n"

        report += """
## Top Missing Definitions
Terms linked but not defined:
"""
        for term in self.result.missing_definitions[:30]:
            report += f"- [[{term}]]\n"

        report += """
## Key Relationships
"""
        for rel in self.result.relationships[:30]:
            src = Path(rel.source).stem
            tgt = Path(rel.target).stem
            report += f"- **{src}** ↔ **{tgt}** ({rel.rel_type}, {rel.strength:.2f})\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        return output_path

    def export_relationships_csv(self) -> Path:
        """Export relationships to CSV for graphing tools."""
        output_path = self.output_dir / "relationships.csv"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("source,target,type,strength,evidence\n")
            for rel in self.result.relationships:
                src = Path(rel.source).stem.replace(',', ' ')
                tgt = Path(rel.target).stem.replace(',', ' ')
                evidence = rel.evidence.replace(',', ' ').replace('\n', ' ')
                f.write(f"{src},{tgt},{rel.rel_type},{rel.strength:.2f},{evidence}\n")

        return output_path


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    # Fix Windows encoding
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    default_vault = Path(__file__).resolve().parents[3]
    vault = os.environ.get("THEOPHYSICS_VAULT", str(default_vault))
    if not Path(vault).exists():
        vault = str(Path.cwd())
    output_dir = str(Path(vault) / "00_SYSTEM" / "01_ENGINE" / "exports")

    print("="*60)
    print("THEOPHYSICS RELATIONSHIP ENGINE")
    print("="*60)
    sys.stdout.flush()

    scanner = TheophysicsScanner(vault)

    # Try to enable embeddings
    if "--embeddings" in sys.argv:
        scanner.discovery.enable_embeddings()

    # Run scan
    result = scanner.scan_vault()

    # Export results
    exporter = ScanExporter(result, Path(output_dir))

    json_path = exporter.export_json()
    print(f"\n[EXPORT] JSON saved: {json_path}")

    report_path = exporter.export_markdown_report()
    print(f"[EXPORT] Report saved: {report_path}")

    csv_path = exporter.export_relationships_csv()
    print(f"[EXPORT] CSV saved: {csv_path}")

    print("\n" + "="*60)
    print("SCAN COMPLETE")
    print("="*60)
    print(f"Total Notes: {result.total_notes}")
    print(f"Relationships: {len(result.relationships)}")
    print(f"Axiom Violations: {len(result.axiom_violations)}")
    print(f"Triad Gaps: {len(result.triad_gaps)}")
    print(f"Missing Definitions: {len(result.missing_definitions)}")
