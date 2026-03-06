"""
Theophysics Unified Scanner + Relationship Engine
Combines:
- Wikipedia auto-filler
- Relationship discovery (embeddings, triads, axiom consistency)
- Hidden YAML detection
- Footnote extraction
- Folder structure awareness
"""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
import hashlib

try:
    from .definition_paths import primary_definition_dir
except ImportError:
    from definition_paths import primary_definition_dir

# ============================================================================
# FOLDER STRUCTURE DEFINITION
# ============================================================================

THEOPHYSICS_STRUCTURE = {
    "00_ADMIN": {
        "description": "Project management and tracking",
        "files": ["PROJECT_CHARTER.md", "VERSION_HISTORY.md", "MASTER_INDEX.yaml", "TODO_BACKLOG.md"]
    },
    "01_AXIOMS": {
        "description": "Foundational axioms and meta-axiom methodology",
        "files": ["Ten_Master_Axioms.md", "Meta_Axiom_Method.md", "Trinity_Axiom_Set.md",
                  "Moral_Conservation_Axiom.md", "Axiom_Dependency_Map.mmd"]
    },
    "02_LAGRANGIANS": {
        "description": "Mathematical formulations and operators",
        "files": ["Lagrangian_LLC.md", "Trinity_Actualization_Operator.md", "Grace_Operator.md",
                  "Moral_Hamiltonian.md"],
        "subfolders": ["Lagrangian_Derivations"]
    },
    "03_LOGOS_PAPERS": {
        "description": "The 12 Logos Papers",
        "subfolders": [
            "P01_Logos_First_Principle", "P02_Quantum_Bridge", "P03_Algorithmic_Reality",
            "P04_Hard_Problem", "P05_Soul_Observer", "P06_Principalities_Physical_Operators",
            "P07_Grace_Counterforce", "P08_Stretched_Heavens", "P09_Moral_Universe",
            "P10_Creatio_Ex_Silico", "P11_Protocols_Verification", "P12_Decalogue_Cosmos"
        ],
        "files": ["Paper_Summaries.md"]
    },
    "04_ENIGMAS": {
        "description": "The 12 Enigmas (paradoxes/puzzles)",
        "files": [f"Enigma_{i:02d}.md" for i in range(1, 13)] + ["ENIGMA_MASTER_INDEX.md"]
    },
    "05_SUPPLEMENTAL": {
        "description": "Supporting materials and additional papers",
        "subfolders": ["Historical_Arguments", "Moral_Geometry", "Principia_Mathematica_Moralia",
                       "Liber_Quartus", "Phenomenology", "Misc_Papers"]
    },
    "06_GLOSSARY": {
        "description": "Definitions and terminology",
        "files": ["MASTER_GLOSSARY.md"],
        "subfolders": ["Terms", "AUTO_GENERATED"]
    },
    "07_DATA": {
        "description": "Datasets, charts, and exports",
        "subfolders": ["datasets", "charts", "exports", "RAW"]
    },
    "08_PYTHON_TOOLS": {
        "description": "Python automation and analysis tools",
        "subfolders": ["definition_engine", "axioms", "postgres_pipeline", "dashboard", "utilities"]
    },
    "09_POSTGRES": {
        "description": "Database schema and sync",
        "files": ["schema.sql"],
        "subfolders": ["tables", "triggers", "sync_logs"]
    },
    "10_EXPORTS": {
        "description": "Output formats for publication",
        "subfolders": ["PDF", "EPUB", "ARXIV", "PRESS"]
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class HiddenYAML:
    """Hidden YAML block found in a note."""
    content: Dict
    start_line: int
    end_line: int
    block_type: str  # 'semantic', 'meta', 'footnote-refs', etc.


@dataclass
class Footnote:
    """Footnote found in a note."""
    id: str
    content: str
    line_number: int
    referenced_at: List[int] = field(default_factory=list)


@dataclass
class NoteAnalysis:
    """Complete analysis of a single note."""
    path: str
    title: str
    folder: str
    domain: str  # Which of the 10 main folders

    # Content
    frontmatter: Dict
    body: str
    word_count: int

    # Structure
    headings: List[Tuple[int, str]]  # (level, text)
    wikilinks: List[str]
    tags: List[str]

    # Hidden elements
    hidden_yaml_blocks: List[HiddenYAML]
    footnotes: List[Footnote]

    # Extracted concepts
    greek_letters: List[str]
    equations: List[str]
    definitions_referenced: List[str]
    axioms_referenced: List[str]

    # Relationships (filled by relationship engine)
    similar_notes: List[Tuple[str, float]] = field(default_factory=list)
    triad_coverage: Dict[str, bool] = field(default_factory=dict)
    axiom_conflicts: List[str] = field(default_factory=list)
    missing_links: List[str] = field(default_factory=list)


# ============================================================================
# HIDDEN YAML EXTRACTOR
# ============================================================================

class HiddenYAMLExtractor:
    """Extracts hidden YAML blocks from notes (%%yaml ... %% or %%semantic ... %%)."""

    PATTERNS = [
        (r'%%yaml\s*\n(.*?)\n%%', 'yaml'),
        (r'%%semantic\s*\n(.*?)\n%%', 'semantic'),
        (r'%%meta\s*\n(.*?)\n%%', 'meta'),
        (r'%%footnotes\s*\n(.*?)\n%%', 'footnotes'),
        (r'%%hidden\s*\n(.*?)\n%%', 'hidden'),
    ]

    def extract(self, content: str) -> List[HiddenYAML]:
        """Extract all hidden YAML blocks from content."""
        blocks = []

        for pattern, block_type in self.PATTERNS:
            for match in re.finditer(pattern, content, re.DOTALL):
                try:
                    yaml_content = yaml.safe_load(match.group(1))
                    if yaml_content:
                        # Calculate line numbers
                        start_pos = match.start()
                        start_line = content[:start_pos].count('\n') + 1
                        end_line = start_line + match.group(0).count('\n')

                        blocks.append(HiddenYAML(
                            content=yaml_content,
                            start_line=start_line,
                            end_line=end_line,
                            block_type=block_type
                        ))
                except yaml.YAMLError:
                    pass

        return blocks


# ============================================================================
# FOOTNOTE EXTRACTOR
# ============================================================================

class FootnoteExtractor:
    """Extracts footnotes from notes."""

    # [^1]: Footnote content
    DEFINITION_PATTERN = r'^\[\^([^\]]+)\]:\s*(.+?)(?=\n\[\^|\n\n|\Z)'
    # Reference: [^1]
    REFERENCE_PATTERN = r'\[\^([^\]]+)\](?!:)'

    def extract(self, content: str) -> List[Footnote]:
        """Extract all footnotes from content."""
        footnotes = {}
        lines = content.split('\n')

        # Find footnote definitions
        for match in re.finditer(self.DEFINITION_PATTERN, content, re.MULTILINE | re.DOTALL):
            fn_id = match.group(1)
            fn_content = match.group(2).strip()
            line_num = content[:match.start()].count('\n') + 1

            footnotes[fn_id] = Footnote(
                id=fn_id,
                content=fn_content,
                line_number=line_num
            )

        # Find references
        for match in re.finditer(self.REFERENCE_PATTERN, content):
            fn_id = match.group(1)
            line_num = content[:match.start()].count('\n') + 1

            if fn_id in footnotes:
                footnotes[fn_id].referenced_at.append(line_num)

        return list(footnotes.values())


# ============================================================================
# AXIOM REFERENCE DETECTOR
# ============================================================================

class AxiomDetector:
    """Detects references to axioms in notes."""

    # The Ten Master Axioms
    AXIOMS = {
        "A1": "Law of Coherent Origin",
        "A2": "Law of Conscious Observation",
        "A3": "Law of Triadic Structure",
        "A4": "Law of Moral Conservation",
        "A5": "Law of Grace Superabundance",
        "A6": "Law of Negentropic Purpose",
        "A7": "Law of Spiritual Conflict",
        "A8": "Law of Participatory Reality",
        "A9": "Law of Prophetic Correlation",
        "A10": "Law of Final Coherence"
    }

    # Triad structure
    TRIAD = {
        "Father": ["Necessity", "Origin", "Source", "Logos", "Will"],
        "Son": ["Contingency", "Incarnation", "Bridge", "χ", "Form"],
        "Spirit": ["Relation", "Connection", "Bond", "Ψ", "Dynamic"]
    }

    def detect_axiom_references(self, content: str) -> List[str]:
        """Find which axioms are referenced in content."""
        found = []
        content_lower = content.lower()

        for ax_id, ax_name in self.AXIOMS.items():
            if ax_id.lower() in content_lower or ax_name.lower() in content_lower:
                found.append(ax_id)

        return found

    def detect_triad_coverage(self, content: str) -> Dict[str, bool]:
        """Check which parts of the Trinity are covered."""
        coverage = {}
        content_lower = content.lower()

        for person, keywords in self.TRIAD.items():
            coverage[person] = any(kw.lower() in content_lower for kw in keywords)

        return coverage

    def detect_axiom_conflicts(self, content: str) -> List[str]:
        """Detect potential conflicts with axioms."""
        conflicts = []
        content_lower = content.lower()

        # Simple heuristic: look for negations of key concepts
        conflict_patterns = [
            ("coherence is not primary", "A1"),
            ("consciousness is emergent", "A2"),
            ("randomness is fundamental", "A6"),
            ("no moral order", "A4"),
        ]

        for pattern, axiom in conflict_patterns:
            if pattern in content_lower:
                conflicts.append(f"{axiom}: '{pattern}'")

        return conflicts


# ============================================================================
# EQUATION EXTRACTOR
# ============================================================================

class EquationExtractor:
    """Extracts mathematical equations from notes."""

    # LaTeX patterns
    PATTERNS = [
        r'\$\$(.+?)\$\$',  # Display math
        r'\$([^$]+)\$',    # Inline math
        r'\\begin\{equation\}(.+?)\\end\{equation\}',
        r'\\begin\{align\}(.+?)\\end\{align\}',
    ]

    # Greek letters
    GREEK = {
        'χ': 'chi', 'Χ': 'Chi',
        'ψ': 'psi', 'Ψ': 'Psi',
        'φ': 'phi', 'Φ': 'Phi',
        'λ': 'lambda', 'Λ': 'Lambda',
        'ω': 'omega', 'Ω': 'Omega',
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
        'ε': 'epsilon', 'θ': 'theta', 'σ': 'sigma', 'τ': 'tau',
        'π': 'pi', 'μ': 'mu', 'ν': 'nu', 'ρ': 'rho', 'κ': 'kappa'
    }

    def extract_equations(self, content: str) -> List[str]:
        """Extract all equations from content."""
        equations = []
        for pattern in self.PATTERNS:
            for match in re.finditer(pattern, content, re.DOTALL):
                equations.append(match.group(1).strip())
        return equations

    def extract_greek_letters(self, content: str) -> List[str]:
        """Extract Greek letters used in content."""
        found = []
        for greek, name in self.GREEK.items():
            if greek in content:
                found.append(name)
        return list(set(found))


# ============================================================================
# UNIFIED VAULT SCANNER
# ============================================================================

class UnifiedVaultScanner:
    """Main scanner that combines all analysis capabilities."""

    SKIP_DIRS = {'.obsidian', '.trash', '.git', 'node_modules', '__pycache__', '.venv'}

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.hidden_yaml_extractor = HiddenYAMLExtractor()
        self.footnote_extractor = FootnoteExtractor()
        self.axiom_detector = AxiomDetector()
        self.equation_extractor = EquationExtractor()

        self.notes: Dict[str, NoteAnalysis] = {}
        self.folder_stats: Dict[str, Dict] = {}
        self.global_tags: Dict[str, int] = {}
        self.global_links: Dict[str, int] = {}

    def scan(self, progress_callback=None) -> Dict[str, NoteAnalysis]:
        """Scan entire vault and analyze all notes."""
        md_files = list(self.vault_path.rglob("*.md"))
        total = len(md_files)

        for i, md_file in enumerate(md_files):
            # Skip certain folders
            if any(skip in md_file.parts for skip in self.SKIP_DIRS):
                continue

            if progress_callback:
                progress_callback(i, total, str(md_file.name))

            try:
                analysis = self._analyze_note(md_file)
                if analysis:
                    self.notes[str(md_file)] = analysis
                    self._update_global_stats(analysis)
            except Exception as e:
                print(f"Error analyzing {md_file}: {e}")

        return self.notes

    def _analyze_note(self, file_path: Path) -> Optional[NoteAnalysis]:
        """Analyze a single note."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        # Parse frontmatter
        frontmatter = {}
        body = content
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    pass
                body = parts[2]

        # Determine domain (which main folder)
        rel_path = file_path.relative_to(self.vault_path)
        parts = rel_path.parts
        domain = parts[0] if parts else "root"
        folder = str(rel_path.parent)

        # Extract components
        headings = self._extract_headings(body)
        wikilinks = self._extract_wikilinks(body)
        tags = self._extract_tags(content)  # Include frontmatter
        hidden_yaml = self.hidden_yaml_extractor.extract(body)
        footnotes = self.footnote_extractor.extract(body)
        greek_letters = self.equation_extractor.extract_greek_letters(body)
        equations = self.equation_extractor.extract_equations(body)
        axioms_ref = self.axiom_detector.detect_axiom_references(body)
        triad = self.axiom_detector.detect_triad_coverage(body)
        conflicts = self.axiom_detector.detect_axiom_conflicts(body)

        # Find definition references
        def_refs = [link for link in wikilinks if 'glossary' in link.lower() or 'definition' in link.lower()]

        return NoteAnalysis(
            path=str(file_path),
            title=file_path.stem,
            folder=folder,
            domain=domain,
            frontmatter=frontmatter,
            body=body,
            word_count=len(body.split()),
            headings=headings,
            wikilinks=wikilinks,
            tags=tags,
            hidden_yaml_blocks=hidden_yaml,
            footnotes=footnotes,
            greek_letters=greek_letters,
            equations=equations,
            definitions_referenced=def_refs,
            axioms_referenced=axioms_ref,
            triad_coverage=triad,
            axiom_conflicts=conflicts
        )

    def _extract_headings(self, content: str) -> List[Tuple[int, str]]:
        """Extract headings from content."""
        headings = []
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE):
            level = len(match.group(1))
            text = match.group(2).strip()
            headings.append((level, text))
        return headings

    def _extract_wikilinks(self, content: str) -> List[str]:
        """Extract wiki-links from content."""
        links = []
        for match in re.finditer(r'\[\[([^\]|#]+)', content):
            links.append(match.group(1).strip())
        return links

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content (including frontmatter)."""
        tags = set()

        # From frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                    if 'tags' in fm:
                        if isinstance(fm['tags'], list):
                            tags.update(fm['tags'])
                        elif isinstance(fm['tags'], str):
                            tags.add(fm['tags'])
                except yaml.YAMLError:
                    pass

        # Inline tags
        for match in re.finditer(r'#([a-zA-Z][a-zA-Z0-9_-]+)', content):
            tags.add(match.group(1))

        return list(tags)

    def _update_global_stats(self, analysis: NoteAnalysis) -> None:
        """Update global statistics."""
        # Tags
        for tag in analysis.tags:
            self.global_tags[tag] = self.global_tags.get(tag, 0) + 1

        # Links
        for link in analysis.wikilinks:
            self.global_links[link] = self.global_links.get(link, 0) + 1

        # Folder stats
        if analysis.domain not in self.folder_stats:
            self.folder_stats[analysis.domain] = {
                'count': 0, 'words': 0, 'equations': 0, 'footnotes': 0, 'hidden_yaml': 0
            }

        stats = self.folder_stats[analysis.domain]
        stats['count'] += 1
        stats['words'] += analysis.word_count
        stats['equations'] += len(analysis.equations)
        stats['footnotes'] += len(analysis.footnotes)
        stats['hidden_yaml'] += len(analysis.hidden_yaml_blocks)


# ============================================================================
# RELATIONSHIP ENGINE
# ============================================================================

class RelationshipEngine:
    """Discovers relationships between notes using various methods."""

    def __init__(self, scanner: UnifiedVaultScanner):
        self.scanner = scanner
        self.similarity_threshold = 0.65

    def find_similar_by_tags(self, note_path: str, min_shared: int = 3) -> List[Tuple[str, int]]:
        """Find notes with shared tags."""
        if note_path not in self.scanner.notes:
            return []

        source_tags = set(self.scanner.notes[note_path].tags)
        similar = []

        for path, analysis in self.scanner.notes.items():
            if path == note_path:
                continue

            shared = len(source_tags & set(analysis.tags))
            if shared >= min_shared:
                similar.append((path, shared))

        return sorted(similar, key=lambda x: x[1], reverse=True)

    def find_similar_by_links(self, note_path: str, min_shared: int = 2) -> List[Tuple[str, int]]:
        """Find notes with shared outgoing links."""
        if note_path not in self.scanner.notes:
            return []

        source_links = set(self.scanner.notes[note_path].wikilinks)
        similar = []

        for path, analysis in self.scanner.notes.items():
            if path == note_path:
                continue

            shared = len(source_links & set(analysis.wikilinks))
            if shared >= min_shared:
                similar.append((path, shared))

        return sorted(similar, key=lambda x: x[1], reverse=True)

    def find_triad_gaps(self) -> Dict[str, List[str]]:
        """Find notes missing parts of the Trinity triad."""
        gaps = {"Father": [], "Son": [], "Spirit": [], "None": []}

        for path, analysis in self.scanner.notes.items():
            missing = [p for p, covered in analysis.triad_coverage.items() if not covered]

            if len(missing) == 3:
                gaps["None"].append(path)
            else:
                for m in missing:
                    gaps[m].append(path)

        return gaps

    def find_axiom_conflicts(self) -> List[Tuple[str, List[str]]]:
        """Find all notes with potential axiom conflicts."""
        conflicts = []

        for path, analysis in self.scanner.notes.items():
            if analysis.axiom_conflicts:
                conflicts.append((path, analysis.axiom_conflicts))

        return conflicts

    def find_orphan_notes(self) -> List[str]:
        """Find notes that are not linked to by any other note."""
        all_links = set()
        for analysis in self.scanner.notes.values():
            all_links.update(analysis.wikilinks)

        orphans = []
        for path, analysis in self.scanner.notes.items():
            # Check if this note's title is linked anywhere
            title = analysis.title
            if title not in all_links and title.replace('_', ' ') not in all_links:
                orphans.append(path)

        return orphans

    def find_missing_definitions(self, glossary_path: Optional[str] = None) -> List[str]:
        """Find terms used but not defined in glossary."""
        # Get defined terms
        defined = set()
        if glossary_path:
            glossary = Path(glossary_path)
        else:
            glossary = primary_definition_dir(
                self.scanner.vault_path, include_global_search=False, include_archive=False
            )
        if glossary.exists():
            for md in glossary.rglob("*.md"):
                if md.name.startswith("_"):
                    continue
                defined.add(md.stem.lower())

        # Find all unique terms referenced
        all_terms = set()
        for analysis in self.scanner.notes.values():
            all_terms.update(t.lower() for t in analysis.wikilinks)
            all_terms.update(t.lower() for t in analysis.greek_letters)

        # Missing = used but not defined, with noise filtering.
        missing = []
        for term in all_terms - defined:
            if not term or len(term) < 2:
                continue
            if term.startswith("http"):
                continue
            if "/" in term or "\\" in term:
                continue
            if "[" in term or "]" in term or "{" in term or "}" in term:
                continue
            if "#" in term:
                continue
            if ":" in term:
                continue
            if term.endswith(".md"):
                continue
            missing.append(term)

        return missing


# ============================================================================
# WORKFLOW EXPORT/SAVE
# ============================================================================

class WorkflowExporter:
    """Exports scan results and workflows for reuse."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_scan_results(self, scanner: UnifiedVaultScanner,
                           relationships: RelationshipEngine) -> Path:
        """Export complete scan results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build export data
        data = {
            "scan_timestamp": timestamp,
            "vault_path": str(scanner.vault_path),
            "total_notes": len(scanner.notes),
            "folder_stats": scanner.folder_stats,
            "global_tags": dict(sorted(scanner.global_tags.items(), key=lambda x: x[1], reverse=True)[:100]),
            "global_links": dict(sorted(scanner.global_links.items(), key=lambda x: x[1], reverse=True)[:100]),
            "notes": {}
        }

        # Serialize notes (skip non-serializable parts)
        for path, analysis in scanner.notes.items():
            data["notes"][path] = {
                "title": analysis.title,
                "folder": analysis.folder,
                "domain": analysis.domain,
                "word_count": analysis.word_count,
                "tags": analysis.tags,
                "wikilinks": analysis.wikilinks,
                "greek_letters": analysis.greek_letters,
                "axioms_referenced": analysis.axioms_referenced,
                "triad_coverage": analysis.triad_coverage,
                "axiom_conflicts": analysis.axiom_conflicts,
                "footnote_count": len(analysis.footnotes),
                "hidden_yaml_count": len(analysis.hidden_yaml_blocks),
                "equation_count": len(analysis.equations)
            }

        # Relationships
        data["relationships"] = {
            "triad_gaps": relationships.find_triad_gaps(),
            "axiom_conflicts": [(p, c) for p, c in relationships.find_axiom_conflicts()],
            "orphan_count": len(relationships.find_orphan_notes())
        }

        # Save
        output_path = self.output_dir / f"scan_results_{timestamp}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def export_folder_structure(self) -> Path:
        """Export the standard folder structure as a setup script."""
        output_path = self.output_dir / "folder_structure.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(THEOPHYSICS_STRUCTURE, f, indent=2)

        return output_path

    def export_missing_definitions_report(self, scanner: UnifiedVaultScanner,
                                          relationships: RelationshipEngine,
                                          glossary_path: Optional[str] = None) -> Path:
        """Export report of missing definitions."""
        missing = relationships.find_missing_definitions(glossary_path)

        # Count usage
        usage = {}
        for term in missing:
            usage[term] = scanner.global_links.get(term, 0)

        # Sort by usage
        sorted_missing = sorted(usage.items(), key=lambda x: x[1], reverse=True)

        # Build markdown report
        lines = [
            "# Missing Definitions Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"\nTotal missing: {len(missing)}",
            "\n## Top 50 Most Used (Undefined)",
            "\n| Term | Usage Count |",
            "|------|-------------|"
        ]

        for term, count in sorted_missing[:50]:
            lines.append(f"| {term} | {count} |")

        lines.append("\n## Full List")
        for term, count in sorted_missing:
            lines.append(f"- {term} ({count})")

        output_path = self.output_dir / "missing_definitions_report.md"
        output_path.write_text('\n'.join(lines), encoding='utf-8')

        return output_path

    def export_footnotes_index(self, scanner: UnifiedVaultScanner) -> Path:
        """Export index of all footnotes in vault."""
        footnotes_by_note = {}

        for path, analysis in scanner.notes.items():
            if analysis.footnotes:
                footnotes_by_note[path] = [
                    {
                        "id": fn.id,
                        "content": fn.content[:200] + "..." if len(fn.content) > 200 else fn.content,
                        "line": fn.line_number,
                        "references": len(fn.referenced_at)
                    }
                    for fn in analysis.footnotes
                ]

        output_path = self.output_dir / "footnotes_index.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(footnotes_by_note, f, indent=2, ensure_ascii=False)

        return output_path

    def export_hidden_yaml_index(self, scanner: UnifiedVaultScanner) -> Path:
        """Export index of all hidden YAML blocks."""
        yaml_by_note = {}

        for path, analysis in scanner.notes.items():
            if analysis.hidden_yaml_blocks:
                yaml_by_note[path] = [
                    {
                        "type": block.block_type,
                        "start_line": block.start_line,
                        "end_line": block.end_line,
                        "keys": list(block.content.keys()) if isinstance(block.content, dict) else []
                    }
                    for block in analysis.hidden_yaml_blocks
                ]

        output_path = self.output_dir / "hidden_yaml_index.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(yaml_by_note, f, indent=2, ensure_ascii=False)

        return output_path


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Main entry point for unified scanner."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    default_vault = Path(__file__).resolve().parents[3]
    vault_path = os.environ.get("THEOPHYSICS_VAULT", str(default_vault))
    if not Path(vault_path).exists():
        vault_path = str(Path.cwd())
    glossary_path = str(
        primary_definition_dir(Path(vault_path), include_global_search=False, include_archive=False)
    )
    output_dir = str(Path(vault_path) / "00_SYSTEM" / "01_ENGINE" / "exports")

    print("=" * 60)
    print("THEOPHYSICS UNIFIED SCANNER")
    print("=" * 60)

    # Initialize scanner
    print("\n[1/4] Initializing scanner...")
    scanner = UnifiedVaultScanner(vault_path)

    # Scan vault
    print("[2/4] Scanning vault...")
    def progress(i, total, filename):
        if i % 100 == 0:
            pct = int(i / total * 100)
            print(f"  {pct}% - {filename[:50]}")

    scanner.scan(progress_callback=progress)
    print(f"  Scanned {len(scanner.notes)} notes")

    # Build relationships
    print("[3/4] Analyzing relationships...")
    relationships = RelationshipEngine(scanner)

    # Export results
    print("[4/4] Exporting results...")
    exporter = WorkflowExporter(output_dir)

    results_path = exporter.export_scan_results(scanner, relationships)
    print(f"  - Scan results: {results_path}")

    structure_path = exporter.export_folder_structure()
    print(f"  - Folder structure: {structure_path}")

    missing_path = exporter.export_missing_definitions_report(scanner, relationships, glossary_path)
    print(f"  - Missing definitions: {missing_path}")

    footnotes_path = exporter.export_footnotes_index(scanner)
    print(f"  - Footnotes index: {footnotes_path}")

    yaml_path = exporter.export_hidden_yaml_index(scanner)
    print(f"  - Hidden YAML index: {yaml_path}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total notes scanned: {len(scanner.notes)}")
    print(f"Unique tags: {len(scanner.global_tags)}")
    print(f"Unique links: {len(scanner.global_links)}")

    print("\nFolder breakdown:")
    for folder, stats in sorted(scanner.folder_stats.items()):
        print(f"  {folder}: {stats['count']} notes, {stats['words']:,} words")

    # Triad gaps
    gaps = relationships.find_triad_gaps()
    print(f"\nTriad coverage gaps:")
    for person, notes in gaps.items():
        if notes:
            print(f"  Missing {person}: {len(notes)} notes")

    # Axiom conflicts
    conflicts = relationships.find_axiom_conflicts()
    if conflicts:
        print(f"\nAxiom conflicts found: {len(conflicts)} notes")
        for path, conf in conflicts[:5]:
            print(f"  - {Path(path).name}: {conf}")

    print("\n[DONE] All exports saved to:", output_dir)


if __name__ == "__main__":
    main()
