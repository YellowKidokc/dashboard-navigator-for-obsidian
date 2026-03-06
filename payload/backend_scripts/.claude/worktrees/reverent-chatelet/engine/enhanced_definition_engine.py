# engine/enhanced_definition_engine.py
"""
Enhanced Definition Engine for Theophysics Research
=====================================================
Research-grade definition management with:
- Vault indexing and term tracking
- Usage drift detection
- Equation mapping
- External reference comparison
- AI-powered contradiction detection

Based on the 9-section definition standard:
1. Canonical Definition
2. Axioms (ontological, mathematical, conservation)
3. Mathematical Structure (equations, dynamics, thresholds)
4. Domain Interpretations
5. Operationalization
6. Failure Modes
7. Integration Map
8. Usage Drift Log
9. External Comparison
"""

import re
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, asdict
import requests

# Optional imports
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TermUsage:
    """A single usage of a term in the vault."""
    file_path: str
    context: str  # Surrounding text
    line_number: int
    usage_type: str  # 'prose', 'equation', 'definition', 'reference'
    equation_id: Optional[str] = None
    variables_in_context: Optional[List[str]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class EquationEntry:
    """An equation found in the vault."""
    eq_id: str
    file_path: str
    raw_latex: str
    variables: List[str]
    definition_notes: List[str]  # Which definition notes this relates to
    line_number: int


@dataclass
class DriftEntry:
    """A detected usage drift."""
    term: str
    file_path: str
    context: str
    canonical_definition: str
    deviation_summary: str
    severity: str  # 'compatible_expansion', 'minor_drift', 'contradiction'
    timestamp: str


@dataclass
class ExternalComparison:
    """Comparison with external source."""
    term: str
    source: str
    source_url: str
    external_definition: str
    external_equations: List[str]
    agreement_notes: str
    divergence_notes: str
    timestamp: str


# =============================================================================
# VAULT INDEXER
# =============================================================================

class VaultIndexer:
    """
    Indexes the entire vault to track term usage, equations, and definitions.
    """

    # Regex patterns
    EQUATION_BLOCK = re.compile(r'\$\$\s*(.*?)\s*\$\$', re.DOTALL)
    INLINE_MATH = re.compile(r'\$([^$]+)\$')
    EQUATION_ID = re.compile(r'%\s*id:\s*(\S+)')
    EQUATION_USES = re.compile(r'%\s*uses:\s*([^\n]+)')
    WIKILINK = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)

    # Common variable symbols in Theophysics
    THEOPHYSICS_SYMBOLS = {
        'χ': 'chi-field',
        'Φ': 'observer-phi',
        'Ψ_S': 'singular-psi',
        'Ψ': 'psi',
        'G': 'grace',
        'S': 'entropy',
        'σ': 'sigma',
        'C': 'coherence',
        'Λ': 'lambda-logos',
        'Π': 'pi-principle',
        'A': 'action',
        'H': 'hamiltonian',
        'I': 'information',
    }

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.index: Dict[str, Any] = {
            "definitions": {},  # term -> definition data
            "usages": {},       # term -> list of TermUsage
            "equations": [],    # list of EquationEntry
            "files": {},        # file_path -> metadata
            "last_indexed": None
        }

    def index_vault(self) -> Dict[str, Any]:
        """Full vault indexing."""
        self.index["definitions"] = {}
        self.index["usages"] = {}
        self.index["equations"] = []
        self.index["files"] = {}

        # Find all markdown files
        md_files = list(self.vault_path.glob("**/*.md"))

        for file_path in md_files:
            self._index_file(file_path)

        self.index["last_indexed"] = datetime.now().isoformat()
        return self.index

    def _index_file(self, file_path: Path):
        """Index a single file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return

        rel_path = str(file_path.relative_to(self.vault_path))

        # Parse frontmatter
        frontmatter = self._parse_frontmatter(content)

        # Check if this is a definition note
        if frontmatter.get('type') == 'definition':
            self._index_definition_note(rel_path, content, frontmatter)

        # Index equations
        self._index_equations(rel_path, content)

        # Index term usages
        self._index_term_usages(rel_path, content)

        # Store file metadata
        self.index["files"][rel_path] = {
            "frontmatter": frontmatter,
            "word_count": len(content.split()),
            "has_equations": bool(self.EQUATION_BLOCK.search(content)),
        }

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        """Parse YAML frontmatter."""
        match = self.FRONTMATTER.match(content)
        if not match:
            return {}

        try:
            import yaml
            return yaml.safe_load(match.group(1)) or {}
        except:
            # Simple fallback parsing
            fm = {}
            for line in match.group(1).split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    fm[key.strip()] = val.strip()
            return fm

    def _index_definition_note(self, file_path: str, content: str, frontmatter: Dict):
        """Index a definition note."""
        term_id = frontmatter.get('id', '')
        symbol = frontmatter.get('symbol', '')
        name = frontmatter.get('name', '')
        aliases = frontmatter.get('aliases', [])

        # Extract canonical definition (Section 1)
        canonical = self._extract_section(content, "1. Canonical Definition")

        # Extract axioms (Section 2)
        axioms = self._extract_section(content, "2. Axioms")

        # Build definition entry
        self.index["definitions"][term_id] = {
            "id": term_id,
            "symbol": symbol,
            "name": name,
            "aliases": aliases if isinstance(aliases, list) else [],
            "canonical_definition": canonical,
            "axioms": axioms,
            "file_path": file_path,
            "frontmatter": frontmatter,
            "searchable_terms": [name, symbol] + (aliases if isinstance(aliases, list) else [])
        }

    def _index_equations(self, file_path: str, content: str):
        """Extract and index all equations."""
        lines = content.split('\n')

        for i, line in enumerate(lines):
            # Check for equation blocks
            for match in self.EQUATION_BLOCK.finditer(content):
                eq_content = match.group(1)

                # Look for equation ID
                eq_id_match = self.EQUATION_ID.search(eq_content)
                eq_id = eq_id_match.group(1) if eq_id_match else f"eq-{file_path}-{i}"

                # Look for variable declarations
                uses_match = self.EQUATION_USES.search(eq_content)
                if uses_match:
                    variables = [v.strip() for v in uses_match.group(1).split(',')]
                else:
                    # Auto-detect variables
                    variables = self._detect_variables(eq_content)

                # Find related definition notes
                related_defs = []
                for var in variables:
                    for def_id, def_data in self.index["definitions"].items():
                        if var in def_data.get("searchable_terms", []):
                            related_defs.append(def_id)

                self.index["equations"].append(EquationEntry(
                    eq_id=eq_id,
                    file_path=file_path,
                    raw_latex=eq_content.strip(),
                    variables=variables,
                    definition_notes=related_defs,
                    line_number=i
                ))

    def _index_term_usages(self, file_path: str, content: str):
        """Index all usages of defined terms."""
        lines = content.split('\n')

        for def_id, def_data in self.index["definitions"].items():
            for search_term in def_data.get("searchable_terms", []):
                if not search_term:
                    continue

                pattern = re.compile(rf'\b{re.escape(search_term)}\b', re.IGNORECASE)

                for i, line in enumerate(lines):
                    if pattern.search(line):
                        # Determine usage type
                        if '$' in line:
                            usage_type = 'equation'
                        elif line.startswith('#'):
                            usage_type = 'heading'
                        elif '[[' in line:
                            usage_type = 'reference'
                        else:
                            usage_type = 'prose'

                        # Get context (surrounding lines)
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context = '\n'.join(lines[start:end])

                        usage = TermUsage(
                            file_path=file_path,
                            context=context,
                            line_number=i + 1,
                            usage_type=usage_type
                        )

                        if def_id not in self.index["usages"]:
                            self.index["usages"][def_id] = []
                        self.index["usages"][def_id].append(asdict(usage))

    def _detect_variables(self, latex: str) -> List[str]:
        """Auto-detect variables in LaTeX."""
        found = []
        for symbol, name in self.THEOPHYSICS_SYMBOLS.items():
            if symbol in latex:
                found.append(symbol)
        # Also look for common single-letter variables
        single_letters = re.findall(r'(?<![a-zA-Z])([A-Z])(?![a-zA-Z])', latex)
        found.extend(list(set(single_letters)))
        return found

    def _extract_section(self, content: str, heading: str) -> str:
        """Extract content under a specific heading."""
        pattern = rf'##\s*{re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def save_index(self, output_path: Path):
        """Save index to JSON."""
        # Convert dataclasses to dicts
        serializable = {
            "definitions": self.index["definitions"],
            "usages": self.index["usages"],
            "equations": [asdict(eq) if hasattr(eq, '__dataclass_fields__') else eq
                         for eq in self.index["equations"]],
            "files": self.index["files"],
            "last_indexed": self.index["last_indexed"]
        }
        output_path.write_text(json.dumps(serializable, indent=2, ensure_ascii=False), encoding='utf-8')

    def load_index(self, input_path: Path):
        """Load index from JSON."""
        if input_path.exists():
            self.index = json.loads(input_path.read_text())


# =============================================================================
# DRIFT DETECTOR
# =============================================================================

class DriftDetector:
    """
    Detects usage drift - when terms are used differently than their canonical definition.
    """

    def __init__(self, indexer: VaultIndexer, ai_engine=None):
        self.indexer = indexer
        self.ai_engine = ai_engine
        self.drift_log: List[DriftEntry] = []

    def detect_drift(self, term_id: str) -> List[DriftEntry]:
        """
        Detect drift for a specific term.
        Compares canonical definition against all usages.
        """
        definition = self.indexer.index["definitions"].get(term_id)
        if not definition:
            return []

        usages = self.indexer.index["usages"].get(term_id, [])
        canonical = definition.get("canonical_definition", "")

        if not canonical or not usages:
            return []

        drifts = []

        if self.ai_engine and self.ai_engine.is_available().get("any"):
            # Use AI for sophisticated drift detection
            drifts = self._ai_drift_detection(term_id, canonical, usages)
        else:
            # Simple heuristic-based detection
            drifts = self._heuristic_drift_detection(term_id, canonical, usages)

        self.drift_log.extend(drifts)
        return drifts

    def _ai_drift_detection(self, term_id: str, canonical: str, usages: List[Dict]) -> List[DriftEntry]:
        """Use AI to detect drift."""
        drifts = []

        # Build context for AI
        usage_contexts = [u["context"] for u in usages[:20]]  # Limit for token efficiency

        prompt = f"""Analyze how the term "{term_id}" is used across these contexts.

CANONICAL DEFINITION:
{canonical}

USAGE CONTEXTS:
{chr(10).join(f'{i+1}. {ctx[:300]}...' for i, ctx in enumerate(usage_contexts))}

For each usage that differs from the canonical definition:
1. Identify the specific deviation
2. Classify as: compatible_expansion, minor_drift, or contradiction
3. Provide a brief summary

Format: JSON array of {{context_num, deviation, severity, summary}}"""

        try:
            # This would call the AI engine
            # result = self.ai_engine.generate_completion(prompt)
            # For now, return empty
            pass
        except Exception:
            pass

        return drifts

    def _heuristic_drift_detection(self, term_id: str, canonical: str, usages: List[Dict]) -> List[DriftEntry]:
        """Simple heuristic-based drift detection."""
        drifts = []

        # Extract key terms from canonical definition
        canonical_terms = set(re.findall(r'\b\w{4,}\b', canonical.lower()))

        for usage in usages:
            context = usage.get("context", "")
            context_terms = set(re.findall(r'\b\w{4,}\b', context.lower()))

            # Check for divergence indicators
            divergence_words = {'unlike', 'contrary', 'instead', 'rather', 'however', 'but'}
            has_divergence = bool(divergence_words & context_terms)

            # Check for definition override attempts
            definition_patterns = [
                r'define[sd]?\s+as',
                r'meaning\s+here',
                r'in\s+this\s+context',
                r'we\s+use\s+.*\s+to\s+mean',
            ]
            has_override = any(re.search(p, context, re.IGNORECASE) for p in definition_patterns)

            if has_divergence or has_override:
                drifts.append(DriftEntry(
                    term=term_id,
                    file_path=usage.get("file_path", ""),
                    context=context[:500],
                    canonical_definition=canonical[:200],
                    deviation_summary="Potential usage drift detected (heuristic)",
                    severity="minor_drift" if has_divergence else "compatible_expansion",
                    timestamp=datetime.now().isoformat()
                ))

        return drifts

    def get_drift_report(self) -> Dict[str, Any]:
        """Generate a drift report."""
        by_severity = {"compatible_expansion": 0, "minor_drift": 0, "contradiction": 0}
        by_term = {}

        for drift in self.drift_log:
            by_severity[drift.severity] = by_severity.get(drift.severity, 0) + 1
            by_term[drift.term] = by_term.get(drift.term, 0) + 1

        return {
            "total_drifts": len(self.drift_log),
            "by_severity": by_severity,
            "by_term": by_term,
            "entries": [asdict(d) for d in self.drift_log]
        }


# =============================================================================
# EXTERNAL COMPARATOR
# =============================================================================

class ExternalComparator:
    """
    Compares definitions against external sources (Wikipedia, SEP, etc.)
    """

    HEADERS = {
        "User-Agent": "TheophysicsResearch/2.0 (Academic Research)"
    }

    def __init__(self):
        self.comparisons: List[ExternalComparison] = []
        self.cache: Dict[str, str] = {}

    def compare_term(self, term: str, canonical_def: str, sources: List[Dict]) -> List[ExternalComparison]:
        """
        Compare a term against external sources.
        """
        comparisons = []

        for source in sources:
            url = source.get("url", "")
            source_name = source.get("source", "")

            if not url or not source.get("verified"):
                continue

            # Fetch external content
            external_content = self._fetch_content(url)
            if not external_content:
                continue

            # Extract definition from external content
            external_def = self._extract_definition(external_content, term)

            # Extract equations
            external_eqs = self._extract_equations(external_content)

            # Generate comparison (would use AI for sophisticated analysis)
            comparison = ExternalComparison(
                term=term,
                source=source_name,
                source_url=url,
                external_definition=external_def[:500] if external_def else "",
                external_equations=external_eqs[:5],
                agreement_notes="",
                divergence_notes="",
                timestamp=datetime.now().isoformat()
            )

            comparisons.append(comparison)

        self.comparisons.extend(comparisons)
        return comparisons

    def _fetch_content(self, url: str) -> str:
        """Fetch content from URL."""
        if url in self.cache:
            return self.cache[url]

        try:
            response = requests.get(url, headers=self.HEADERS, timeout=30)
            if response.status_code == 200:
                self.cache[url] = response.text
                return response.text
        except Exception:
            pass

        return ""

    def _extract_definition(self, html: str, term: str) -> str:
        """Extract definition from HTML content."""
        if not HAS_BS4:
            return ""

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Try to find first paragraph after title
            first_p = soup.find('p')
            if first_p:
                return first_p.get_text().strip()
        except Exception:
            pass

        return ""

    def _extract_equations(self, html: str) -> List[str]:
        """Extract equations from HTML content."""
        equations = []

        # Look for LaTeX in various formats
        patterns = [
            r'\$\$(.*?)\$\$',
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'<math[^>]*>(.*?)</math>',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            equations.extend(matches)

        return equations


# =============================================================================
# MAIN ENGINE
# =============================================================================

class EnhancedDefinitionEngine:
    """
    Main engine for research-grade definition management.
    """

    def __init__(self, vault_path: Path, db_engine=None, ai_engine=None):
        self.vault_path = vault_path
        self.db = db_engine
        self.ai_engine = ai_engine

        self.indexer = VaultIndexer(vault_path)
        self.drift_detector = DriftDetector(self.indexer, ai_engine)
        self.comparator = ExternalComparator()

        # Paths
        self.index_path = vault_path / ".theophysics" / "definition_index.json"
        self.drift_path = vault_path / ".theophysics" / "drift_log.json"
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def full_index(self) -> Dict[str, Any]:
        """Run full vault indexing."""
        index = self.indexer.index_vault()
        self.indexer.save_index(self.index_path)
        return {
            "definitions_found": len(index["definitions"]),
            "equations_found": len(index["equations"]),
            "files_indexed": len(index["files"]),
            "usages_tracked": sum(len(u) for u in index["usages"].values()),
        }

    def check_drift(self, term_id: str = None) -> Dict[str, Any]:
        """Check for usage drift."""
        # Load index if not loaded
        if not self.indexer.index.get("definitions"):
            self.indexer.load_index(self.index_path)

        if term_id:
            drifts = self.drift_detector.detect_drift(term_id)
        else:
            # Check all terms
            for tid in self.indexer.index["definitions"]:
                self.drift_detector.detect_drift(tid)

        report = self.drift_detector.get_drift_report()

        # Save drift log
        self.drift_path.write_text(json.dumps(report, indent=2))

        return report

    def get_definition_status(self, term_id: str) -> Dict[str, Any]:
        """Get full status for a definition."""
        if not self.indexer.index.get("definitions"):
            self.indexer.load_index(self.index_path)

        definition = self.indexer.index["definitions"].get(term_id, {})
        usages = self.indexer.index["usages"].get(term_id, [])

        # Find equations using this term
        term_equations = []
        for eq in self.indexer.index["equations"]:
            eq_data = eq if isinstance(eq, dict) else asdict(eq)
            if term_id in eq_data.get("definition_notes", []):
                term_equations.append(eq_data)

        return {
            "definition": definition,
            "usage_count": len(usages),
            "equation_count": len(term_equations),
            "equations": term_equations,
            "sample_usages": usages[:10],
        }

    def generate_integration_map(self, term_id: str) -> str:
        """Generate markdown for Integration Map section."""
        status = self.get_definition_status(term_id)
        
        # Determine symbol
        symbol = status.get('definition', {}).get('symbol', 'this term')

        md = "## 7. Integration Map\n\n"
        
        md += "- **Appears in:**\n"
        # Get unique files
        files = set()
        for usage in status.get("sample_usages", []):
            files.add(usage.get("file_path", ""))
        
        if not files:
            md += "  - _No usages found._\n"
        else:
            for f in sorted(files):
                md += f"  - [[{Path(f).stem}]]\n"

        md += f"- **Equations using {symbol}:**\n"
        
        if not status.get("equations"):
             md += "  - _No equations found._\n"
        else:
            for eq in status.get("equations", []):
                eq_id = eq.get("eq_id", "")
                md += f"  - `{eq_id}`\n"

        return md

    def generate_drift_log_section(self, term_id: str) -> str:
        """Generate markdown for Usage Drift Log section."""
        drifts = [d for d in self.drift_detector.drift_log if d.term == term_id]

        md = "## 8. Usage Drift Log (Auto-Generated)\n\n"
        md += "> _This section is appended by the Definition Engine._  \n"
        md += "> Each entry: file, context, deviation summary.\n\n"
        
        if not drifts:
             md += "- _No drift detected._\n"
             return md

        for drift in drifts:
            date = drift.timestamp[:10] if hasattr(drift, 'timestamp') else ""
            file_name = Path(drift.file_path).stem if hasattr(drift, 'file_path') else ""
            context = drift.context[:50] + "..." if hasattr(drift, 'context') else ""
            deviation = drift.deviation_summary[:50] if hasattr(drift, 'deviation_summary') else ""
            md += f"- {date} — [[{file_name}]] — {deviation} ({context})\n"

        return md

    def create_definition_note(self, term: str, symbol: str, output_dir: Path = None) -> Path:
        """Create a new definition note from template."""
        if output_dir is None:
            output_dir = self.vault_path / "Definitions"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template_path = Path(__file__).parent.parent / "templates" / "definition_template.md"
        if template_path.exists():
            template = template_path.read_text(encoding='utf-8')
        else:
            template = self._default_template()

        # Fill in template
        slug = term.lower().replace(' ', '-')
        date = datetime.now().strftime("%Y-%m-%d")

        content = template.replace("{{TERM_SLUG}}", slug)
        content = content.replace("{{SYMBOL}}", symbol)
        content = content.replace("{{NAME}}", term)
        content = content.replace("{{DATE}}", date)

        # Write file
        output_path = output_dir / f"def-{slug}.md"
        output_path.write_text(content, encoding='utf-8')

        return output_path

    def _default_template(self) -> str:
        """Default template if file not found."""
        return """---
type: definition
id: def-{{TERM_SLUG}}
symbol: {{SYMBOL}}
name: {{NAME}}
status: draft
last_reviewed: {{DATE}}
---

# {{SYMBOL}} — {{NAME}}

## 1. Canonical Definition

> **{{NAME}} is ...**

## 2. Axioms

## 3. Mathematical Structure

## 4. Domain Interpretations

## 5. Operationalization

## 6. Failure Modes

## 7. Integration Map

## 8. Usage Drift Log

## 9. External Comparison
"""


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("Enhanced Definition Engine for Theophysics")
    print("=" * 60)

    if len(sys.argv) > 1:
        vault_path = Path(sys.argv[1])
    else:
        vault_path = Path(".")

    engine = EnhancedDefinitionEngine(vault_path)

    print(f"\nVault: {vault_path}")
    print("\nIndexing vault...")

    result = engine.full_index()

    print(f"\nResults:")
    print(f"  Definitions found: {result['definitions_found']}")
    print(f"  Equations found: {result['equations_found']}")
    print(f"  Files indexed: {result['files_indexed']}")
    print(f"  Usages tracked: {result['usages_tracked']}")

    print("\nChecking for drift...")
    drift_report = engine.check_drift()
    print(f"  Total drifts detected: {drift_report['total_drifts']}")

    print(f"\nIndex saved to: {engine.index_path}")
    print(f"Drift log saved to: {engine.drift_path}")
