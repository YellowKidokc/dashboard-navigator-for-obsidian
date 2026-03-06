"""
External Authority Linker for Theophysics Logos Papers
Finds proper nouns (people, theories, methods, formulas) and links them to authoritative external sources.

Source Priority:
1. Stanford Encyclopedia of Philosophy (SEP)
2. Internet Encyclopedia of Philosophy (IEP)
3. PhilPapers
4. arXiv
5. Wolfram MathWorld
6. Wikipedia (fallback)
"""

import re
import json
import os
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from html.parser import HTMLParser
import time


@dataclass
class ExternalLink:
    """Represents an external authority link."""
    term: str
    url: str
    source: str  # SEP, IEP, PhilPapers, arXiv, MathWorld, Wikipedia
    title: str
    description: str = ""
    fetched_at: str = ""
    
    def to_dict(self) -> dict:
        return {
            'term': self.term,
            'url': self.url,
            'source': self.source,
            'title': self.title,
            'description': self.description,
            'fetched_at': self.fetched_at
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'ExternalLink':
        return cls(**d)


class LinkDatabase:
    """Persistent storage for term -> URL mappings."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.links: Dict[str, ExternalLink] = {}
        self.load()
    
    def load(self) -> None:
        """Load links from JSON file."""
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text(encoding='utf-8'))
                self.links = {k: ExternalLink.from_dict(v) for k, v in data.items()}
            except Exception as e:
                print(f"[WARN] Could not load link database: {e}")
                self.links = {}
    
    def save(self) -> None:
        """Save links to JSON file."""
        data = {k: v.to_dict() for k, v in self.links.items()}
        self.db_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    
    def get(self, term: str) -> Optional[ExternalLink]:
        """Get link for a term (case-insensitive)."""
        return self.links.get(term.lower())
    
    def add(self, link: ExternalLink) -> None:
        """Add a link to the database."""
        self.links[link.term.lower()] = link
    
    def has(self, term: str) -> bool:
        """Check if term exists in database."""
        return term.lower() in self.links


class SourceLookup:
    """Base class for source lookups."""
    
    SOURCE_NAME = "Unknown"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'TheophysicsLinker/1.0 (academic research tool)'
        }
    
    def lookup(self, term: str) -> Optional[ExternalLink]:
        """Look up a term. Override in subclasses."""
        raise NotImplementedError
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch a URL and return content."""
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            return None


class SEPLookup(SourceLookup):
    """Stanford Encyclopedia of Philosophy lookup."""
    
    SOURCE_NAME = "SEP"
    BASE_URL = "https://plato.stanford.edu"
    
    # Known SEP entry slugs for common terms
    KNOWN_ENTRIES = {
        'albert einstein': 'einstein-philscience',
        'quantum mechanics': 'qm',
        'copenhagen interpretation': 'qm-copenhagen',
        'many worlds interpretation': 'qm-manyworlds',
        'general relativity': 'spacetime-theories',
        'special relativity': 'spacetime-theories',
        'uncertainty principle': 'qt-uncertainty',
        'wave function': 'qm-collapse',
        'consciousness': 'consciousness',
        'free will': 'freewill',
        'causation': 'causation-metaphysics',
        'time': 'time',
        'space': 'space-time',
        'information': 'information',
        'truth': 'truth',
        'knowledge': 'knowledge-analysis',
        'belief': 'belief',
        'probability': 'probability-interpret',
        'induction': 'induction-problem',
        'scientific method': 'scientific-method',
        'realism': 'scientific-realism',
        'naturalism': 'naturalism',
        'physicalism': 'physicalism',
        'dualism': 'dualism',
        'emergence': 'properties-emergent',
        'reduction': 'scientific-reduction',
        'laws of nature': 'laws-of-nature',
        'causality': 'causation-physics',
        'determinism': 'determinism-causal',
        'modal logic': 'logic-modal',
        'set theory': 'set-theory',
        'godel': 'goedel-incompleteness',
        'turing': 'turing-machine',
        'computability': 'computability-theory',
        'information theory': 'information-semantic',
        'entropy': 'information-entropy',
        'thermodynamics': 'physics-interrelate',
        'cosmology': 'cosmology-theology',
        'fine tuning': 'fine-tuning',
        'teleological argument': 'teleological-arguments',
        'ontological argument': 'ontological-arguments',
        'cosmological argument': 'cosmological-argument',
        'god': 'concepts-god',
        'evil': 'evil',
        'miracles': 'miracles',
        'faith': 'faith',
        'religion science': 'religion-science',
        'thomas aquinas': 'aquinas',
        'aristotle': 'aristotle',
        'plato': 'plato',
        'kant': 'kant',
        'descartes': 'descartes',
        'leibniz': 'leibniz',
        'spinoza': 'spinoza',
        'hume': 'hume',
        'locke': 'locke',
        'berkeley': 'berkeley',
        'whitehead': 'whitehead',
        'process philosophy': 'process-philosophy',
        'phenomenology': 'phenomenology',
    }
    
    def lookup(self, term: str) -> Optional[ExternalLink]:
        """Search SEP for a term."""
        term_lower = term.lower()
        
        # Check known entries first
        if term_lower in self.KNOWN_ENTRIES:
            slug = self.KNOWN_ENTRIES[term_lower]
            entry_url = f"{self.BASE_URL}/entries/{slug}/"
            
            # Verify it exists
            content = self._fetch_url(entry_url)
            if content and '<title>' in content:
                title_match = re.search(r'<title>([^<]+)</title>', content)
                title = title_match.group(1).replace(' (Stanford Encyclopedia of Philosophy)', '') if title_match else term
                
                return ExternalLink(
                    term=term,
                    url=entry_url,
                    source=self.SOURCE_NAME,
                    title=title.strip(),
                    fetched_at=datetime.now().isoformat()
                )
        
        # Try slug-based lookup
        slug = term_lower.replace(' ', '-').replace("'", '').replace('.', '')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        entry_url = f"{self.BASE_URL}/entries/{slug}/"
        content = self._fetch_url(entry_url)
        
        if content and '<title>' in content and '404' not in content[:500]:
            title_match = re.search(r'<title>([^<]+)</title>', content)
            title = title_match.group(1).replace(' (Stanford Encyclopedia of Philosophy)', '') if title_match else term
            
            if 'not found' not in title.lower():
                return ExternalLink(
                    term=term,
                    url=entry_url,
                    source=self.SOURCE_NAME,
                    title=title.strip(),
                    fetched_at=datetime.now().isoformat()
                )
        
        return None


class IEPLookup(SourceLookup):
    """Internet Encyclopedia of Philosophy lookup."""
    
    SOURCE_NAME = "IEP"
    BASE_URL = "https://iep.utm.edu"
    
    def lookup(self, term: str) -> Optional[ExternalLink]:
        """Search IEP for a term."""
        # IEP uses slug-based URLs
        slug = term.lower().replace(' ', '-').replace("'", '')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        # Try direct URL first
        direct_url = f"{self.BASE_URL}/{slug}/"
        content = self._fetch_url(direct_url)
        
        if content and '<title>' in content:
            # Extract title
            title_match = re.search(r'<title>([^<]+)</title>', content)
            title = title_match.group(1) if title_match else term
            
            # Check it's not a 404 page
            if '404' not in title and 'not found' not in title.lower():
                return ExternalLink(
                    term=term,
                    url=direct_url,
                    source=self.SOURCE_NAME,
                    title=title.replace(' | Internet Encyclopedia of Philosophy', '').strip(),
                    fetched_at=datetime.now().isoformat()
                )
        
        return None


class MathWorldLookup(SourceLookup):
    """Wolfram MathWorld lookup for mathematical terms."""
    
    SOURCE_NAME = "MathWorld"
    BASE_URL = "https://mathworld.wolfram.com"
    
    def lookup(self, term: str) -> Optional[ExternalLink]:
        """Search MathWorld for a term."""
        # MathWorld uses CamelCase URLs
        # "Fourier transform" -> "FourierTransform"
        slug = ''.join(word.capitalize() for word in term.split())
        slug = re.sub(r'[^a-zA-Z0-9]', '', slug)
        
        direct_url = f"{self.BASE_URL}/{slug}.html"
        content = self._fetch_url(direct_url)
        
        if content and '<title>' in content:
            title_match = re.search(r'<title>([^<]+)</title>', content)
            title = title_match.group(1) if title_match else term
            
            if 'not found' not in title.lower() and '404' not in title:
                return ExternalLink(
                    term=term,
                    url=direct_url,
                    source=self.SOURCE_NAME,
                    title=title.replace(' -- from Wolfram MathWorld', '').strip(),
                    fetched_at=datetime.now().isoformat()
                )
        
        return None


class WikipediaLookup(SourceLookup):
    """Wikipedia lookup (fallback)."""
    
    SOURCE_NAME = "Wikipedia"
    API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    def lookup(self, term: str) -> Optional[ExternalLink]:
        """Look up term on Wikipedia."""
        encoded = urllib.parse.quote(term.replace(' ', '_'))
        url = f"{self.API_URL}{encoded}"
        
        content = self._fetch_url(url)
        if not content:
            return None
        
        try:
            data = json.loads(content)
            if data.get('type') == 'standard':
                return ExternalLink(
                    term=term,
                    url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    source=self.SOURCE_NAME,
                    title=data.get('title', term),
                    description=data.get('extract', '')[:200],
                    fetched_at=datetime.now().isoformat()
                )
        except:
            pass
        
        return None


class ProperNounExtractor:
    """Extracts proper nouns from text that should be linked."""
    
    # Known patterns for proper nouns in physics/philosophy
    PERSON_PATTERNS = [
        # Full names: "Albert Einstein", "Werner Heisenberg"
        r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?)?\s+[A-Z][a-z]+)\b',
        # Last names with title: "Dr. Einstein", "Prof. Heisenberg"
        r'\b(?:Dr|Prof|Sir|Lord)\.?\s+([A-Z][a-z]+)\b',
    ]
    
    THEORY_PATTERNS = [
        # X Theory/Theorem/Principle/Law/Effect/Paradox/Equation
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Theory|Theorem|Principle|Law|Effect|Paradox|Equation|Hypothesis|Conjecture|Postulate|Axiom))\b',
        # X's Theory/Law etc
        r"\b([A-Z][a-z]+'s\s+(?:Theory|Theorem|Principle|Law|Effect|Paradox|Equation|Hypothesis|Conjecture))\b",
        # The X Interpretation/Model
        r'\b(?:the\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Interpretation|Model|Formulation|Formalism))\b',
    ]
    
    METHOD_PATTERNS = [
        # X Method/Technique/Algorithm/Transform
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Method|Technique|Algorithm|Transform|Analysis|Decomposition))\b',
    ]
    
    # Known proper nouns to always match (seed list)
    KNOWN_PEOPLE = {
        'Albert Einstein', 'Werner Heisenberg', 'Erwin Schrodinger', 'Niels Bohr',
        'Max Planck', 'Paul Dirac', 'Richard Feynman', 'John Wheeler', 'David Bohm',
        'Hugh Everett', 'John Bell', 'Roger Penrose', 'Stephen Hawking',
        'Isaac Newton', 'James Clerk Maxwell', 'Ludwig Boltzmann', 'Max Born',
        'Wolfgang Pauli', 'Enrico Fermi', 'Murray Gell-Mann', 'Eugene Wigner',
        'John von Neumann', 'Kurt Godel', 'Alan Turing', 'Claude Shannon',
        'Andrey Kolmogorov', 'Henri Poincare', 'Emmy Noether', 'Hermann Minkowski',
        'Hendrik Lorentz', 'Michael Faraday', 'Ernst Mach', 'Gottfried Leibniz',
        'Rene Descartes', 'Blaise Pascal', 'Pierre-Simon Laplace', 'Carl Friedrich Gauss',
        'Bernhard Riemann', 'David Hilbert', 'Georg Cantor', 'Bertrand Russell',
        'Alfred North Whitehead', 'Immanuel Kant', 'Aristotle', 'Plato',
        'Thomas Aquinas', 'Augustine', 'Alvin Plantinga', 'William Lane Craig',
        'Karl Popper', 'Thomas Kuhn', 'Paul Feyerabend', 'Bas van Fraassen'
    }
    
    KNOWN_THEORIES = {
        'General Relativity', 'Special Relativity', 'Quantum Mechanics',
        'Copenhagen Interpretation', 'Many Worlds Interpretation', 'Pilot Wave Theory',
        'String Theory', 'Loop Quantum Gravity', 'Standard Model',
        'Bell Theorem', 'Bell Inequality', 'EPR Paradox', 'Uncertainty Principle',
        'Pauli Exclusion Principle', 'Schrodinger Equation', 'Dirac Equation',
        'Klein-Gordon Equation', 'Maxwell Equations', 'Einstein Field Equations',
        'Friedmann Equations', 'Noether Theorem', 'Godel Incompleteness',
        'Church-Turing Thesis', 'Holographic Principle', 'Anthropic Principle',
        'Fine-Tuning Argument', 'Cosmological Argument', 'Ontological Argument',
        'Kalam Cosmological Argument', 'Moral Argument', 'Teleological Argument'
    }
    
    KNOWN_METHODS = {
        'Fourier Transform', 'Laplace Transform', 'Green Function',
        'Variational Method', 'Perturbation Theory', 'Path Integral',
        'Monte Carlo Method', 'Bayesian Inference', 'Maximum Likelihood',
        'Least Squares', 'Principal Component Analysis', 'Singular Value Decomposition'
    }
    
    def __init__(self):
        self.all_known = self.KNOWN_PEOPLE | self.KNOWN_THEORIES | self.KNOWN_METHODS
    
    def extract(self, text: str) -> Set[str]:
        """Extract all proper nouns from text."""
        found = set()
        
        # First, find all known terms
        for term in self.all_known:
            if term.lower() in text.lower():
                # Find actual case in text
                pattern = re.compile(re.escape(term), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    found.add(match.group(0))
        
        # Then use patterns to find more
        for pattern in self.PERSON_PATTERNS + self.THEORY_PATTERNS + self.METHOD_PATTERNS:
            for match in re.finditer(pattern, text):
                term = match.group(1) if match.lastindex else match.group(0)
                # Filter out common false positives
                if self._is_valid_term(term):
                    found.add(term)
        
        return found
    
    def _is_valid_term(self, term: str) -> bool:
        """Check if a term is likely a valid proper noun."""
        # Skip very short terms
        if len(term) < 4:
            return False
        
        # Skip common words that might match patterns
        skip_words = {
            'The', 'This', 'That', 'These', 'Those', 'What', 'When', 'Where',
            'Which', 'While', 'With', 'From', 'Into', 'Upon', 'Under', 'Over',
            'About', 'After', 'Before', 'Between', 'Through', 'During', 'Without',
            'Figure', 'Table', 'Section', 'Chapter', 'Paper', 'Note', 'See',
            'However', 'Therefore', 'Furthermore', 'Moreover', 'Indeed', 'Thus'
        }
        
        if term in skip_words or term.split()[0] in skip_words:
            return False
        
        return True


class AuthorityLinker:
    """Main class that orchestrates the linking process."""
    
    def __init__(self, db_path: Path):
        self.db = LinkDatabase(db_path)
        self.extractor = ProperNounExtractor()
        
        # Source lookup priority order
        self.sources = [
            SEPLookup(),
            IEPLookup(),
            MathWorldLookup(),
            WikipediaLookup(),  # Fallback
        ]
        
        self.stats = {
            'terms_found': 0,
            'terms_linked': 0,
            'from_cache': 0,
            'from_sep': 0,
            'from_iep': 0,
            'from_mathworld': 0,
            'from_wikipedia': 0,
            'not_found': 0
        }
    
    def find_link(self, term: str) -> Optional[ExternalLink]:
        """Find a link for a term, checking cache first then sources."""
        # Check cache
        cached = self.db.get(term)
        if cached:
            self.stats['from_cache'] += 1
            return cached
        
        # Try each source in priority order
        for source in self.sources:
            print(f"      Trying {source.SOURCE_NAME}...", end=" ")
            link = source.lookup(term)
            if link:
                print(f"FOUND!")
                self.db.add(link)
                self.stats[f'from_{source.SOURCE_NAME.lower()}'] = self.stats.get(f'from_{source.SOURCE_NAME.lower()}', 0) + 1
                return link
            print("not found")
            time.sleep(0.5)  # Be nice to servers
        
        self.stats['not_found'] += 1
        return None
    
    def process_document(self, doc_path: Path, link_mode: str = 'first') -> Tuple[str, List[str]]:
        """
        Process a document and add external links.
        
        Args:
            doc_path: Path to markdown file
            link_mode: 'first' (first mention only), 'all' (every mention), 'section' (first per section)
        
        Returns:
            Tuple of (processed_content, list_of_terms_linked)
        """
        content = doc_path.read_text(encoding='utf-8', errors='ignore')
        
        # Extract proper nouns
        terms = self.extractor.extract(content)
        self.stats['terms_found'] += len(terms)
        
        print(f"\n[DOC] {doc_path.name}")
        print(f"      Found {len(terms)} potential terms to link")
        
        linked_terms = []
        terms_linked_in_doc = set()  # Track what we've already linked
        
        for term in sorted(terms, key=len, reverse=True):  # Longer terms first to avoid partial matches
            link = self.find_link(term)
            if not link:
                continue
            
            # Apply link to content based on mode
            if link_mode == 'first':
                # Only link first occurrence
                pattern = re.compile(r'\b' + re.escape(term) + r'\b(?![^\[]*\])', re.IGNORECASE)
                match = pattern.search(content)
                if match and term.lower() not in terms_linked_in_doc:
                    original = match.group(0)
                    # Create styled external link
                    linked = self._create_link(original, link)
                    content = content[:match.start()] + linked + content[match.end():]
                    terms_linked_in_doc.add(term.lower())
                    linked_terms.append(term)
                    self.stats['terms_linked'] += 1
            
            elif link_mode == 'all':
                # Link every occurrence
                pattern = re.compile(r'\b' + re.escape(term) + r'\b(?![^\[]*\])(?![^\<]*\>)', re.IGNORECASE)
                
                def replace_func(m):
                    return self._create_link(m.group(0), link)
                
                new_content = pattern.sub(replace_func, content)
                if new_content != content:
                    content = new_content
                    if term.lower() not in terms_linked_in_doc:
                        linked_terms.append(term)
                        terms_linked_in_doc.add(term.lower())
                        self.stats['terms_linked'] += 1
        
        print(f"      Linked {len(linked_terms)} terms")
        
        return content, linked_terms
    
    def _create_link(self, text: str, link: ExternalLink) -> str:
        """Create a styled external link."""
        # Markdown link with title attribute showing source
        # Format: [text](url){.external-authority data-source="SEP"}
        # Or for simpler Markdown: [text](url "Source: SEP")
        return f'[{text}]({link.url} "{link.source}: {link.title}")'
    
    def save_database(self) -> None:
        """Save the link database."""
        self.db.save()
    
    def get_stats(self) -> dict:
        """Get linking statistics."""
        return self.stats.copy()


class LogosPapersLinker:
    """Process Logos Papers and add external authority links."""
    
    def __init__(self, logos_papers_path: Path, output_path: Path = None):
        self.logos_papers_path = logos_papers_path
        self.output_path = output_path or logos_papers_path.parent / "LOGOS_PAPERS_LINKED"
        
        # Database stored alongside output
        db_path = self.output_path / "_external_links_db.json"
        self.linker = AuthorityLinker(db_path)
        
        self.processed_files = []
        self.all_linked_terms = set()
    
    def process_all(self, link_mode: str = 'first', dry_run: bool = False) -> dict:
        """Process all Logos Papers."""
        # Create output directory
        if not dry_run:
            self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        md_files = list(self.logos_papers_path.glob("*.md"))
        print(f"\n{'='*60}")
        print(f"LOGOS PAPERS EXTERNAL LINKER")
        print(f"{'='*60}")
        print(f"Source: {self.logos_papers_path}")
        print(f"Output: {self.output_path}")
        print(f"Mode: {link_mode}")
        print(f"Files: {len(md_files)}")
        print(f"{'='*60}")
        
        for md_file in sorted(md_files):
            try:
                content, linked_terms = self.linker.process_document(md_file, link_mode)
                self.all_linked_terms.update(linked_terms)
                
                if not dry_run:
                    # Save processed file
                    output_file = self.output_path / md_file.name
                    output_file.write_text(content, encoding='utf-8')
                
                self.processed_files.append(md_file.name)
                
            except Exception as e:
                print(f"[ERROR] Failed to process {md_file.name}: {e}")
        
        # Save link database
        if not dry_run:
            self.linker.save_database()
            self._generate_link_report()
        
        return self.linker.get_stats()
    
    def _generate_link_report(self) -> None:
        """Generate a report of all external links."""
        report_path = self.output_path / "_EXTERNAL_LINKS_REPORT.md"
        
        stats = self.linker.get_stats()
        
        # Group links by source
        links_by_source = {}
        for link in self.linker.db.links.values():
            source = link.source
            if source not in links_by_source:
                links_by_source[source] = []
            links_by_source[source].append(link)
        
        report = f"""# External Links Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Files Processed:** {len(self.processed_files)}
- **Terms Found:** {stats['terms_found']}
- **Terms Linked:** {stats['terms_linked']}
- **From Cache:** {stats['from_cache']}
- **Not Found:** {stats['not_found']}

## Links by Source

"""
        for source in ['SEP', 'IEP', 'MathWorld', 'Wikipedia']:
            links = links_by_source.get(source, [])
            report += f"### {source} ({len(links)} links)\n\n"
            for link in sorted(links, key=lambda x: x.term.lower()):
                report += f"- [{link.term}]({link.url})\n"
            report += "\n"
        
        report += """
---
## How to Use

The linked papers use standard Markdown links with title attributes:
```markdown
[Albert Einstein](https://plato.stanford.edu/entries/einstein-philscience/ "SEP: Albert Einstein")
```

To add gold underline styling in Obsidian, add this CSS snippet:

```css
/* External authority links - gold underline */
a[href*="plato.stanford.edu"],
a[href*="iep.utm.edu"],
a[href*="mathworld.wolfram.com"],
a[href*="wikipedia.org"] {
    color: inherit;
    text-decoration: none;
    border-bottom: 2px solid #D4AF37;
    padding-bottom: 1px;
}

a[href*="plato.stanford.edu"]:hover,
a[href*="iep.utm.edu"]:hover,
a[href*="mathworld.wolfram.com"]:hover,
a[href*="wikipedia.org"]:hover {
    background-color: rgba(212, 175, 55, 0.1);
}
```

For web/Substack, use inline styles or add the CSS to your theme.
"""
        
        report_path.write_text(report, encoding='utf-8')
        print(f"\n[REPORT] Saved to: {report_path}")


# CLI interface
if __name__ == "__main__":
    import sys
    
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    # Default paths (vault-aware, portable)
    default_vault = Path(__file__).resolve().parents[3]
    vault_root = Path(os.environ.get("THEOPHYSICS_VAULT", str(default_vault)))
    if not vault_root.exists():
        vault_root = Path.cwd()

    source_candidates = [
        vault_root / "04_THEOPYHISCS" / "LOGOS_V3",
        vault_root / "05_PUBLICATIONS",
    ]
    logos_papers = next((p for p in source_candidates if p.exists()), source_candidates[0])
    output = vault_root / "05_PUBLICATIONS" / "LOGOS_PAPERS_LINKED"
    
    # Parse args
    link_mode = 'first'  # Default: only link first mention
    dry_run = False
    
    for arg in sys.argv[1:]:
        if arg == '--all':
            link_mode = 'all'
        elif arg == '--first':
            link_mode = 'first'
        elif arg == '--dry-run':
            dry_run = True
        elif arg.startswith('--source='):
            logos_papers = Path(arg.split('=')[1])
        elif arg.startswith('--output='):
            output = Path(arg.split('=')[1])
    
    # Check source exists
    if not logos_papers.exists():
        print(f"[ERROR] Source path not found: {logos_papers}")
        print("\nUsage: python external_linker.py [options]")
        print("  --first       Link first mention only (default)")
        print("  --all         Link every mention")
        print("  --dry-run     Don't write files, just scan")
        print("  --source=PATH Path to Logos Papers")
        print("  --output=PATH Output directory")
        sys.exit(1)
    
    # Run
    processor = LogosPapersLinker(logos_papers, output)
    stats = processor.process_all(link_mode=link_mode, dry_run=dry_run)
    
    print(f"\n{'='*60}")
    print("FINAL STATISTICS")
    print(f"{'='*60}")
    for key, value in stats.items():
        print(f"  {key}: {value}")
