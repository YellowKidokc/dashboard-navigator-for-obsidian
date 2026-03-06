"""
Theophysics Definition Management System

Handles:
- Wikipedia integration for definitions
- Definition validation and comparison
- Usage example generation
- Semantic word relationships
- Statistics tracking
- Obsidian-compatible definition file generation
- Research link generation (SEP, arXiv, PhilPapers, etc.)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import requests
from difflib import SequenceMatcher
import sys
from urllib.parse import quote

sys.path.append(str(Path(__file__).parent.parent / "core"))
from research_linker import ResearchLinker


@dataclass
class Definition:
    """Core definition data structure."""
    term: str
    aliases: List[str]
    definition_user: Optional[str]  # Your definition
    definition_wikipedia: Optional[str]  # Wikipedia definition
    usage_examples: List[str]
    related_terms: List[str]  # Semantically similar words
    
    # Statistics
    appearances_count: int = 0
    views_count: int = 0
    last_viewed: Optional[str] = None
    
    # Validation
    similarity_score: Optional[float] = None  # How similar to Wikipedia (0-1)
    discrepancies: List[str] = None  # List of noted differences
    validation_status: str = "pending"  # pending, validated, flagged
    
    # Metadata
    created_date: str = None
    last_updated: str = None
    source_files: List[str] = None  # Files where term appears
    research_links: Dict[str, str] = None
    
    def __post_init__(self):
        if self.discrepancies is None:
            self.discrepancies = []
        if self.source_files is None:
            self.source_files = []
        if self.research_links is None:
            self.research_links = {}
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()


class WikipediaAPI:
    """Fetch definitions from Wikipedia."""
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    SEARCH_URL = "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srlimit=1&srsearch="
    HEADERS = {"User-Agent": "TheophysicsDefinitionBot/1.0 (research assistant)"}

    @staticmethod
    def _fetch_summary_by_title(title: str) -> Optional[Dict]:
        term_cleaned = title.replace(" ", "_")
        url = f"{WikipediaAPI.BASE_URL}{quote(term_cleaned)}"
        response = requests.get(url, timeout=10, headers=WikipediaAPI.HEADERS)
        if response.status_code == 200:
            data = response.json()
            return {
                'extract': data.get('extract', ''),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'title': data.get('title', title)
            }
        return None
    
    @staticmethod
    def fetch_definition(term: str) -> Optional[Dict]:
        """Fetch Wikipedia summary for a term."""
        try:
            candidates = [term]
            # Helpful default disambiguation for common physics glossary terms.
            if "quantum" not in term.lower():
                candidates.append(f"Quantum {term}")

            for candidate in candidates:
                found = WikipediaAPI._fetch_summary_by_title(candidate)
                if found and found.get('extract'):
                    return found

            # Final fallback: search API, then fetch summary for best hit.
            search_url = f"{WikipediaAPI.SEARCH_URL}{quote(term)}"
            search_resp = requests.get(search_url, timeout=10, headers=WikipediaAPI.HEADERS)
            if search_resp.status_code == 200:
                search_data = search_resp.json()
                hits = search_data.get("query", {}).get("search", [])
                if hits:
                    top_title = hits[0].get("title")
                    if top_title:
                        found = WikipediaAPI._fetch_summary_by_title(top_title)
                        if found and found.get('extract'):
                            return found

            return None
        except Exception as e:
            print(f"Wikipedia fetch failed for '{term}': {e}")
            return None


class DefinitionComparator:
    """Compare user definitions with Wikipedia."""
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity score between two texts (0-1)."""
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()
        
        return SequenceMatcher(None, t1, t2).ratio()
    
    @staticmethod
    def find_discrepancies(user_def: str, wiki_def: str, term: str) -> List[str]:
        """Find potential discrepancies between definitions."""
        discrepancies = []
        
        if not user_def:
            discrepancies.append("No user definition provided")
            return discrepancies
        
        if not wiki_def:
            discrepancies.append("No Wikipedia definition found")
            return discrepancies
        
        # Length check
        len_ratio = len(user_def) / len(wiki_def) if wiki_def else 0
        if len_ratio < 0.3:
            discrepancies.append(f"User definition is much shorter ({len(user_def)} vs {len(wiki_def)} chars)")
        elif len_ratio > 3.0:
            discrepancies.append(f"User definition is much longer ({len(user_def)} vs {len(wiki_def)} chars)")
        
        # Key term presence
        term_lower = term.lower()
        if term_lower not in user_def.lower():
            discrepancies.append(f"Term '{term}' not explicitly mentioned in user definition")
        
        # Common scientific terms that should match
        key_terms = ['physics', 'energy', 'entropy', 'quantum', 'field', 'theory', 
                     'law', 'principle', 'axiom', 'measure', 'system']
        
        wiki_key_terms = [t for t in key_terms if t in wiki_def.lower()]
        user_key_terms = [t for t in key_terms if t in user_def.lower()]
        
        missing_in_user = set(wiki_key_terms) - set(user_key_terms)
        if missing_in_user:
            discrepancies.append(f"Key terms in Wikipedia but not in user def: {', '.join(missing_in_user)}")
        
        return discrepancies
    
    @staticmethod
    def validate_definition(user_def: str, wiki_def: str, term: str) -> Tuple[float, List[str], str]:
        """
        Validate a definition against Wikipedia.
        
        Returns:
            (similarity_score, discrepancies, status)
        """
        similarity = DefinitionComparator.calculate_similarity(user_def, wiki_def)
        discrepancies = DefinitionComparator.find_discrepancies(user_def, wiki_def, term)
        
        # Determine status
        if similarity > 0.7:
            status = "validated"
        elif similarity > 0.4 or len(discrepancies) <= 2:
            status = "review"
        else:
            status = "flagged"
        
        return similarity, discrepancies, status

    @staticmethod
    def alignment_verdict(status: str, similarity: Optional[float]) -> str:
        """
        Human-readable alignment verdict for publishing dashboards.
        """
        if status == "validated":
            return "ALIGNED"
        if status == "review":
            return "REVIEW"
        if status == "missing_internal":
            return "MISSING_INTERNAL"
        if status == "pending":
            return "PENDING"
        if status == "no_baseline":
            return "NO_BASELINE"
        if similarity is not None and similarity < 0.4:
            return "RED_FLAG"
        return "RED_FLAG"


class UsageExampleGenerator:
    """Generate usage examples for Theophysics context."""
    
    THEOPHYSICS_CONTEXTS = [
        "In the context of Theophysics, {term} represents...",
        "When analyzing {term} through the lens of Theophysics...",
        "The Theophysics framework treats {term} as...",
        "{term} plays a crucial role in understanding...",
        "From a Theophysics perspective, {term} can be understood as...",
    ]
    
    @staticmethod
    def generate_examples(term: str, definition: str, num_examples: int = 2) -> List[str]:
        """Generate usage examples for a term."""
        examples = []
        
        # Example 1: Basic usage
        examples.append(
            f"In the context of Theophysics, {term} represents a fundamental concept "
            f"that bridges theological principles with physical laws."
        )
        
        # Example 2: Specific application
        if 'entropy' in definition.lower():
            examples.append(
                f"When analyzing {term} through the lens of Theophysics, we observe "
                f"its relationship to information conservation and spiritual order."
            )
        elif 'energy' in definition.lower():
            examples.append(
                f"The Theophysics framework treats {term} as both a measurable quantity "
                f"and a manifestation of deeper structural principles."
            )
        else:
            examples.append(
                f"From a Theophysics perspective, {term} can be understood as "
                f"an invariant property that maintains coherence across different scales."
            )
        
        return examples[:num_examples]


class SemanticRelationFinder:
    """Find semantically related terms."""
    
    # Common Theophysics-related terms
    THEOPHYSICS_VOCABULARY = [
        # Core physics
        'energy', 'entropy', 'field', 'quantum', 'wave', 'particle', 'force',
        'momentum', 'mass', 'spacetime', 'causality', 'symmetry', 'invariance',
        
        # Thermodynamics
        'temperature', 'heat', 'work', 'equilibrium', 'disorder', 'order',
        'irreversibility', 'reversibility', 'state', 'system', 'boundary',
        
        # Information theory
        'information', 'bit', 'signal', 'noise', 'channel', 'encoding',
        'compression', 'redundancy', 'uncertainty', 'probability',
        
        # Mathematics
        'equation', 'function', 'derivative', 'integral', 'tensor', 'matrix',
        'vector', 'scalar', 'operator', 'transform', 'manifold',
        
        # Theophysics specific
        'axiom', 'logos', 'coherence', 'fidelity', 'grace', 'hope', 'love',
        'patience', 'faithfulness', 'self-control', 'peace', 'truth', 'humility',
        'goodness', 'unity', 'joy', 'wisdom', 'knowledge', 'constraint',
        
        # Structure
        'structure', 'pattern', 'organization', 'hierarchy', 'emergence',
        'complexity', 'simplicity', 'reduction', 'holism', 'parts', 'whole',
        
        # Philosophy
        'being', 'existence', 'reality', 'truth', 'meaning', 'purpose',
        'telos', 'essence', 'substance', 'property', 'relation'
    ]
    
    @staticmethod
    def find_related_terms(term: str, definition: str, num_terms: int = 40) -> List[str]:
        """
        Find semantically related terms.
        
        Uses simple keyword matching for now.
        Can be enhanced with actual NLP embeddings later.
        """
        term_lower = term.lower()
        def_lower = definition.lower()
        
        related = []
        
        # Score each vocabulary term
        scores = {}
        for vocab_term in SemanticRelationFinder.THEOPHYSICS_VOCABULARY:
            if vocab_term == term_lower:
                continue
            
            score = 0
            
            # In definition
            if vocab_term in def_lower:
                score += 10
            
            # Shared word roots (simple check)
            if any(c in vocab_term for c in term_lower.split()) or \
               any(c in term_lower for c in vocab_term.split()):
                score += 5
            
            # Category matching
            if term_lower in ['energy', 'entropy', 'force'] and vocab_term in ['energy', 'entropy', 'force', 'momentum', 'work']:
                score += 8
            
            if score > 0:
                scores[vocab_term] = score
        
        # Sort by score and return top N
        related = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [term for term, score in related[:num_terms]]


class DefinitionManager:
    """Main manager for definition system."""
    
    def __init__(self, definitions_dir: Path):
        """Initialize the definition manager."""
        self.definitions_dir = Path(definitions_dir)
        self.definitions_dir.mkdir(parents=True, exist_ok=True)
        
        self.definitions_file = self.definitions_dir / "definitions_database.json"
        self.stats_file = self.definitions_dir / "definitions_stats.json"
        self.exclusion_file = self.definitions_dir / "excluded_terms.json"
        # Governance policy: internal definition is canonical.
        # Wikipedia is external baseline only.
        self.allow_wikipedia_as_primary = False
        
        self.definitions: Dict[str, Definition] = {}
        self.research_linker = ResearchLinker()
        self.excluded_terms: List[str] = []
        self.load_definitions()
        self._load_exclusion_list()
    
    def load_definitions(self):
        """Load definitions from JSON database."""
        if self.definitions_file.exists():
            with open(self.definitions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for term, def_dict in data.items():
                    self.definitions[term] = Definition(**def_dict)
    
    def _load_exclusion_list(self) -> None:
        """Load excluded terms from config."""
        if self.exclusion_file.exists():
            try:
                with open(self.exclusion_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.excluded_terms = [term.lower() for term in data.get('excluded_terms', [])]
            except Exception:
                self.excluded_terms = []
    
    def _save_exclusion_list(self) -> None:
        """Save excluded terms to config."""
        with open(self.exclusion_file, 'w', encoding='utf-8') as f:
            json.dump({'excluded_terms': sorted(self.excluded_terms)}, f, indent=2, ensure_ascii=False)
    
    def is_excluded(self, term: str) -> bool:
        """Check if a term is in the exclusion list."""
        return term.lower().strip() in self.excluded_terms
    
    def add_to_exclusion_list(self, term: str) -> None:
        """Add a term to the exclusion list (permanently deny)."""
        term_lower = term.lower().strip()
        if term_lower not in self.excluded_terms:
            self.excluded_terms.append(term_lower)
            self._save_exclusion_list()
            print(f"[EXCLUDED] '{term}' added to exclusion list")
    
    def remove_from_exclusion_list(self, term: str) -> None:
        """Remove a term from the exclusion list."""
        term_lower = term.lower().strip()
        if term_lower in self.excluded_terms:
            self.excluded_terms.remove(term_lower)
            self._save_exclusion_list()
            print(f"[INCLUDED] '{term}' removed from exclusion list")
    
    def get_excluded_terms(self) -> List[str]:
        """Get list of all excluded terms."""
        return self.excluded_terms.copy()
    
    def clear_exclusion_list(self) -> None:
        """Clear all excluded terms."""
        self.excluded_terms = []
        self._save_exclusion_list()
    
    def save_definitions(self):
        """Save definitions to JSON database."""
        data = {term: asdict(defn) for term, defn in self.definitions.items()}
        with open(self.definitions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_or_update_definition(
        self,
        term: str,
        aliases: List[str] = None,
        user_definition: str = None,
        fetch_wikipedia: bool = True,
        generate_examples: bool = True,
        find_related: bool = True
    ) -> Optional[Definition]:
        """
        Create or update a definition.
        
        Args:
            term: The term to define
            aliases: List of alternative names/spellings
            user_definition: Your custom definition (optional)
            fetch_wikipedia: Whether to fetch Wikipedia definition
            generate_examples: Whether to generate usage examples
            find_related: Whether to find related terms
        
        Returns:
            Definition object or None if term is excluded
        """
        # Check if term is excluded
        if self.is_excluded(term):
            print(f"\n[SKIPPED] '{term}' is in exclusion list")
            return None
        
        print(f"\n{'='*60}")
        print(f"Processing definition: {term}")
        print(f"{'='*60}")
        
        # Get or create definition
        if term in self.definitions:
            defn = self.definitions[term]
            defn.last_updated = datetime.now().isoformat()
        else:
            defn = Definition(
                term=term,
                aliases=aliases or [],
                definition_user=user_definition,
                definition_wikipedia=None,
                usage_examples=[],
                related_terms=[]
            )
        
        # Update aliases if provided
        if aliases:
            defn.aliases = aliases
        
        # Update user definition if provided
        if user_definition:
            defn.definition_user = user_definition
        
        # Fetch Wikipedia definition
        if fetch_wikipedia:
            print(f"[*] Fetching Wikipedia definition...")
            wiki_data = WikipediaAPI.fetch_definition(term)
            if wiki_data:
                defn.definition_wikipedia = wiki_data['extract']
                print(f"[OK] Wikipedia definition retrieved ({len(wiki_data['extract'])} chars)")
            else:
                print(f"[!] No Wikipedia definition found")
        
        # Governance: do not silently replace missing internal definition.
        if not defn.definition_user and defn.definition_wikipedia and not self.allow_wikipedia_as_primary:
            print(f"[i] Internal definition missing. Keeping Wikipedia as baseline only.")
            defn.validation_status = "missing_internal"
            if "No user definition provided" not in defn.discrepancies:
                defn.discrepancies.append("No user definition provided")
        
        # Compare definitions if both exist
        if defn.definition_user and defn.definition_wikipedia:
            print(f"\n[*] Comparing definitions...")
            similarity, discrepancies, status = DefinitionComparator.validate_definition(
                defn.definition_user,
                defn.definition_wikipedia,
                term
            )
            defn.similarity_score = similarity
            defn.discrepancies = discrepancies
            defn.validation_status = status
            
            print(f"  Similarity: {similarity:.2%}")
            print(f"  Status: {status}")
            if discrepancies:
                print(f"  Discrepancies found:")
                for disc in discrepancies:
                    print(f"    - {disc}")
        elif defn.definition_user and not defn.definition_wikipedia:
            # Internal exists, but no baseline found externally
            defn.validation_status = "no_baseline"
            defn.similarity_score = None
        elif not defn.definition_user and not defn.definition_wikipedia:
            defn.validation_status = "pending"
        
        # Generate usage examples
        if generate_examples and defn.definition_user:
            print(f"\n[*] Generating usage examples...")
            defn.usage_examples = UsageExampleGenerator.generate_examples(
                term,
                defn.definition_user
            )
            print(f"[OK] Generated {len(defn.usage_examples)} examples")
        
        # Find related terms
        if find_related and defn.definition_user:
            print(f"\n[*] Finding related terms...")
            defn.related_terms = SemanticRelationFinder.find_related_terms(
                term,
                defn.definition_user,
                num_terms=40
            )
            print(f"[OK] Found {len(defn.related_terms)} related terms")
        
        # Generate research links (top 5 high-quality sources)
        print(f"\n[*] Generating research links...")
        defn.research_links = self.research_linker.get_top_quality_links(term, count=5)
        if defn.research_links:
            print(f"[OK] Generated {len(defn.research_links)} research links")
            for source, url in list(defn.research_links.items())[:3]:
                print(f"    - {source}: {url[:60]}...")
        else:
            print(f"[!] No research links generated")
        
        # Save
        self.definitions[term] = defn
        self.save_definitions()
        
        print(f"\n[OK] Definition for '{term}' saved successfully!")
        return defn
    
    def record_view(self, term: str):
        """Record that a definition was viewed."""
        if term in self.definitions:
            defn = self.definitions[term]
            defn.views_count += 1
            defn.last_viewed = datetime.now().isoformat()
            self.save_definitions()
    
    def record_appearance(self, term: str, source_file: str):
        """Record that a term appeared in a file."""
        if term in self.definitions:
            defn = self.definitions[term]
            defn.appearances_count += 1
            if source_file not in defn.source_files:
                defn.source_files.append(source_file)
            self.save_definitions()
    
    def generate_obsidian_file(self, term: str, output_dir: Path = None) -> Path:
        """
        Generate an Obsidian-compatible definition file.
        
        Args:
            term: The term to generate file for
            output_dir: Output directory (defaults to definitions_dir)
        
        Returns:
            Path to generated file
        """
        if term not in self.definitions:
            raise ValueError(f"Definition for '{term}' not found")
        
        defn = self.definitions[term]
        output_dir = Path(output_dir) if output_dir else self.definitions_dir / "obsidian_definitions"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = f"{term.replace(' ', '_')}.md"
        filepath = output_dir / filename
        
        # Generate content
        content = self._generate_obsidian_content(defn)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[OK] Generated Obsidian file: {filepath}")
        return filepath
    
    def _generate_obsidian_content(self, defn: Definition) -> str:
        """Generate Obsidian markdown content for a definition."""
        lines = []
        
        # Frontmatter
        lines.append("---")
        lines.append("def-type: consolidated")
        if defn.aliases:
            lines.append("aliases:")
            for alias in defn.aliases:
                lines.append(f"  - {alias}")
        lines.append(f"created: {defn.created_date}")
        lines.append(f"updated: {defn.last_updated}")
        lines.append(f"validation: {defn.validation_status}")
        if defn.similarity_score is not None:
            lines.append(f"similarity: {defn.similarity_score:.2%}")
        lines.append("---")
        lines.append("")
        
        # Term header
        lines.append(f"# {defn.term}")
        lines.append("")
        
        # Aliases (italics)
        if defn.aliases:
            lines.append(f"*{', '.join(defn.aliases)}*")
            lines.append("")
        
        # Canonical internal definition
        lines.append("**Canonical Internal Definition (Theophysics):**")
        lines.append(defn.definition_user or "*Missing - required before publish*")
        lines.append("")
        
        # External baseline definition
        if defn.definition_wikipedia:
            lines.append("**External Baseline (Wikipedia):**")
            lines.append(defn.definition_wikipedia)
            lines.append("")
        
        # Validation info
        lines.append("**Consistency Check (Internal vs External Baseline):**")
        verdict = DefinitionComparator.alignment_verdict(defn.validation_status, defn.similarity_score)
        lines.append(f"- Alignment Verdict: {verdict}")
        if defn.similarity_score is not None:
            lines.append(f"- Similarity to Wikipedia: {defn.similarity_score:.2%}")
        lines.append(f"- Status: {defn.validation_status}")
        if defn.discrepancies:
            lines.append("- Discrepancies:")
            for disc in defn.discrepancies:
                lines.append(f"  - {disc}")
        lines.append("")
        
        # Usage examples
        if defn.usage_examples:
            lines.append("**Theophysics Usage Examples:**")
            for i, example in enumerate(defn.usage_examples, 1):
                lines.append(f"{i}. {example}")
            lines.append("")
        
        # Related terms
        if defn.related_terms:
            lines.append("**Related Terms:**")
            # Display as inline list with links
            related_links = [f"[[{term}]]" for term in defn.related_terms[:30]]
            lines.append(", ".join(related_links))
            lines.append("")
        
        # Research links
        if defn.research_links:
            lines.append("**Research Links:**")
            for source, url in defn.research_links.items():
                lines.append(f"- [{source}]({url})")
            lines.append("")
        
        # Statistics
        lines.append("**Statistics:**")
        lines.append(f"- Appearances: {defn.appearances_count}")
        lines.append(f"- Views: {defn.views_count}")
        if defn.last_viewed:
            lines.append(f"- Last viewed: {defn.last_viewed}")
        if defn.source_files:
            lines.append(f"- Found in {len(defn.source_files)} files")
        lines.append("")
        
        # Divider
        lines.append("---")
        
        return "\n".join(lines)
    
    def generate_all_obsidian_files(self, output_dir: Path = None):
        """Generate Obsidian files for all definitions."""
        output_dir = Path(output_dir) if output_dir else self.definitions_dir / "obsidian_definitions"
        
        print(f"\n{'='*60}")
        print(f"Generating {len(self.definitions)} Obsidian definition files...")
        print(f"{'='*60}\n")
        
        for term in self.definitions:
            self.generate_obsidian_file(term, output_dir)
        
        print(f"\n[OK] All definition files generated in: {output_dir}")
    
    def get_report(self) -> str:
        """Generate a summary report of all definitions."""
        lines = []
        lines.append("="*60)
        lines.append("THEOPHYSICS DEFINITION DATABASE REPORT")
        lines.append("="*60)
        lines.append(f"\nTotal definitions: {len(self.definitions)}")
        
        # Status breakdown
        status_counts = {}
        for defn in self.definitions.values():
            status = defn.validation_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        lines.append("\nValidation Status:")
        for status, count in sorted(status_counts.items()):
            lines.append(f"  {status}: {count}")
        
        # Top viewed
        top_viewed = sorted(
            self.definitions.values(),
            key=lambda d: d.views_count,
            reverse=True
        )[:10]
        
        if top_viewed and top_viewed[0].views_count > 0:
            lines.append("\nTop 10 Most Viewed:")
            for i, defn in enumerate(top_viewed, 1):
                lines.append(f"  {i}. {defn.term}: {defn.views_count} views")
        
        # Top appearances
        top_appearances = sorted(
            self.definitions.values(),
            key=lambda d: d.appearances_count,
            reverse=True
        )[:10]
        
        if top_appearances and top_appearances[0].appearances_count > 0:
            lines.append("\nTop 10 Most Common Terms:")
            for i, defn in enumerate(top_appearances, 1):
                lines.append(f"  {i}. {defn.term}: {defn.appearances_count} appearances")
        
        # Flagged definitions
        flagged = [d for d in self.definitions.values() if d.validation_status == "flagged"]
        if flagged:
            lines.append(f"\n⚠️  {len(flagged)} definitions flagged for review:")
            for defn in flagged[:5]:
                lines.append(f"  - {defn.term}")
                if defn.discrepancies:
                    lines.append(f"    Reason: {defn.discrepancies[0]}")
        
        lines.append("\n" + "="*60)
        
        return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = DefinitionManager(Path("definitions"))
    
    # Example: Create some definitions
    test_terms = [
        ("Entropy", ["thermodynamic entropy", "disorder"], None),
        ("Energy", ["mechanical energy"], None),
        ("Grace", ["divine grace"], "In Theophysics, grace represents the capacity of a system to absorb entropy without catastrophic failure."),
    ]
    
    for term, aliases, user_def in test_terms:
        manager.create_or_update_definition(
            term=term,
            aliases=aliases,
            user_definition=user_def,
            fetch_wikipedia=True,
            generate_examples=True,
            find_related=True
        )
    
    # Generate report
    print("\n" + manager.get_report())
    
    # Generate Obsidian files
    manager.generate_all_obsidian_files()
