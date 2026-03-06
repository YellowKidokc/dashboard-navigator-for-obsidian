# engine/knowledge_acquisition_engine.py
"""
Knowledge Acquisition Engine for Theophysics Research
======================================================
Scans papers, extracts entities, and links to high-quality sources.

Priority Sources (highest to lowest quality):
1. Stanford Encyclopedia of Philosophy (SEP) - https://plato.stanford.edu
2. arXiv - https://arxiv.org (for scientific papers)
3. Internet Encyclopedia of Philosophy (IEP) - https://iep.utm.edu
4. PhilPapers - https://philpapers.org
5. Scholarpedia - https://www.scholarpedia.org
6. Wikipedia - https://en.wikipedia.org (fallback)

Features:
- PDF text extraction
- Proper name detection (scientists, philosophers)
- Scientific theory/principle/theorem extraction
- Automatic source lookup with priority
- Content download and markdown conversion
"""

import re
import json
import time
import yaml
import sqlite3
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import quote, urlparse
from datetime import datetime
import yaml

# Optional imports
try:
    import fitz  # PyMuPDF for PDF extraction
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    from markdownify import markdownify as md
    HAS_MARKDOWNIFY = True
except ImportError:
    HAS_MARKDOWNIFY = False


# =============================================================================
# CONFIGURATION
# =============================================================================

HEADERS = {
    "User-Agent": "TheophysicsResearch/2.0 (Academic Research; Obsidian Integration)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Source priority (lower number = higher priority)
SOURCE_PRIORITY = {
    "Stanford Encyclopedia of Philosophy": 1,
    "arXiv": 2,
    "Internet Encyclopedia of Philosophy": 3,
    "PhilPapers": 4,
    "Scholarpedia": 5,
    "Google Scholar": 6,
    "Wikipedia": 7,
}


# =============================================================================
# ENTITY EXTRACTION (ENHANCED)
# =============================================================================

class EnhancedEntityExtractor:
    """
    Enhanced entity extraction for academic papers.
    Extracts: names, theories, principles, theorems, equations, citations.
    """

    # Famous scientists/philosophers to prioritize (expandable)
    KNOWN_NAMES = {
        "Einstein", "Newton", "Bohr", "Heisenberg", "Schrödinger", "Planck",
        "Dirac", "Feynman", "Hawking", "Penrose", "Gödel", "Turing", "Church",
        "Aristotle", "Plato", "Kant", "Hegel", "Descartes", "Leibniz", "Spinoza",
        "Wittgenstein", "Russell", "Frege", "Quine", "Kripke", "Putnam",
        "Darwin", "Maxwell", "Faraday", "Boltzmann", "Gibbs", "Shannon",
        "Bayes", "Gauss", "Euler", "Riemann", "Hilbert", "Noether",
        "Wheeler", "Everett", "Bohm", "Bell", "Aspect", "Zeilinger",
        "Tononi", "Chalmers", "Dennett", "Searle", "Nagel", "Jackson",
        "Aquinas", "Augustine", "Anselm", "Scotus", "Ockham",
    }

    # Theory/principle suffixes
    THEORY_SUFFIXES = [
        "theory", "theorem", "principle", "law", "effect", "paradox",
        "conjecture", "hypothesis", "postulate", "axiom", "lemma",
        "equation", "formula", "constant", "model", "interpretation",
        "mechanism", "process", "phenomenon", "criterion", "bound",
    ]

    def __init__(self):
        # Build regex patterns
        suffix_pattern = "|".join(self.THEORY_SUFFIXES)

        # Pattern for "Name's Theory" or "Name Theory"
        self.named_theory_pattern = re.compile(
            rf"\b([A-Z][a-z]+(?:[-'][A-Z][a-z]+)?)\s*[\'']?s?\s+({suffix_pattern})\b",
            re.IGNORECASE
        )

        # Pattern for "Theory of X"
        self.theory_of_pattern = re.compile(
            rf"\b({suffix_pattern})\s+of\s+([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\b",
            re.IGNORECASE
        )

        # Pattern for capitalized theories
        self.capitalized_theory_pattern = re.compile(
            rf"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){{0,3}})\s+({suffix_pattern})\b"
        )

        # Person name patterns
        self.person_patterns = [
            # Title + Name
            re.compile(r'\b(?:Dr\.|Prof\.|Sir|Lord)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'),
            # First Last
            re.compile(r'\b([A-Z][a-z]{2,15})\s+([A-Z][a-z]{2,15})\b'),
            # First Middle Last
            re.compile(r'\b([A-Z][a-z]{2,15})\s+([A-Z]\.?\s+)?([A-Z][a-z]{2,15})\b'),
        ]

        # Citation patterns
        self.citation_patterns = [
            re.compile(r'\(([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?),?\s*(\d{4})\)'),
            re.compile(r'\[(\d+)\]'),
            re.compile(r'([A-Z][a-z]+)\s+\((\d{4})\)'),
        ]

    def extract_theories(self, text: str) -> List[Dict[str, str]]:
        """Extract scientific theories, principles, theorems, etc."""
        theories = []
        seen = set()

        # Named theories (e.g., "Einstein's Theory", "Bell's Theorem")
        for match in self.named_theory_pattern.finditer(text):
            name = match.group(1)
            theory_type = match.group(2).lower()
            full_name = f"{name}'s {theory_type.title()}"
            key = full_name.lower()
            if key not in seen:
                theories.append({
                    "name": full_name,
                    "type": theory_type,
                    "eponym": name,
                    "context": self._get_context(text, match.start(), match.end())
                })
                seen.add(key)

        # Theory of X (e.g., "Theory of Relativity")
        for match in self.theory_of_pattern.finditer(text):
            theory_type = match.group(1).lower()
            subject = match.group(2)
            full_name = f"{theory_type.title()} of {subject}"
            key = full_name.lower()
            if key not in seen:
                theories.append({
                    "name": full_name,
                    "type": theory_type,
                    "subject": subject,
                    "context": self._get_context(text, match.start(), match.end())
                })
                seen.add(key)

        # Capitalized theories (e.g., "Quantum Mechanics", "General Relativity")
        for match in self.capitalized_theory_pattern.finditer(text):
            prefix = match.group(1)
            suffix = match.group(2).lower()
            full_name = f"{prefix} {suffix.title()}"
            key = full_name.lower()
            if key not in seen and len(prefix) > 2:
                theories.append({
                    "name": full_name,
                    "type": suffix,
                    "context": self._get_context(text, match.start(), match.end())
                })
                seen.add(key)

        return theories

    def extract_people(self, text: str) -> List[Dict[str, str]]:
        """Extract person names, prioritizing known scientists/philosophers."""
        people = []
        seen = set()

        # First, find known names
        for known_name in self.KNOWN_NAMES:
            pattern = re.compile(rf'\b{re.escape(known_name)}\b')
            if pattern.search(text):
                if known_name.lower() not in seen:
                    people.append({
                        "name": known_name,
                        "type": "known_figure",
                        "confidence": "high"
                    })
                    seen.add(known_name.lower())

        # Then use pattern matching for unknown names
        for pattern in self.person_patterns:
            for match in pattern.finditer(text):
                full_match = match.group(0)
                # Clean up
                name = ' '.join(full_match.split())
                if name.lower() not in seen and self._is_likely_person(name):
                    people.append({
                        "name": name,
                        "type": "extracted",
                        "confidence": "medium"
                    })
                    seen.add(name.lower())

        return people

    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract academic citations."""
        citations = []

        for pattern in self.citation_patterns:
            for match in pattern.finditer(text):
                groups = match.groups()
                if len(groups) >= 2 and groups[1].isdigit():
                    citations.append({
                        "author": groups[0],
                        "year": groups[1],
                        "raw": match.group(0)
                    })
                elif len(groups) == 1 and groups[0].isdigit():
                    citations.append({
                        "reference_number": groups[0],
                        "raw": match.group(0)
                    })

        return citations

    def extract_biblical_refs(self, text: str) -> List[Dict[str, str]]:
        """Extract Biblical references (e.g., 'Ephesians 6:12')."""
        refs = []
        # Pattern: Book Chapter:Verse or "Book of X"
        pattern = re.compile(
            r'\b([1-3]?\s?[A-Z][a-z]+)\s+(\d{1,3}):(\d{1,3}(?:-\d{1,3})?)\b'
        )
        
        for match in pattern.finditer(text):
            book, chapter, verse = match.groups()
            full_ref = f"{book} {chapter}:{verse}"
            refs.append({
                "name": full_ref,
                "type": "biblical_ref",
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "context": self._get_context(text, match.start(), match.end())
            })
            
        return refs

    def extract_concepts(self, text: str) -> List[Dict[str, str]]:
        """Extract general concepts (capitalized terms, medical conditions, etc.)."""
        concepts = []
        seen = set()
        
        # Medical/Psychological terms (e.g., Depression, Anxiety)
        medical_terms = ["Depression", "Anxiety", "Trauma", "Addiction", "Schizophrenia", "Dissociation"]
        for term in medical_terms:
            if re.search(rf'\b{term}\b', text, re.IGNORECASE):
                 if term.lower() not in seen:
                    concepts.append({
                        "name": term,
                        "type": "concept",
                        "subtype": "medical/psychological"
                    })
                    seen.add(term.lower())

        return concepts

    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all entity types."""
        return {
            "theories": self.extract_theories(text),
            "people": self.extract_people(text),
            "citations": self.extract_citations(text),
            "biblical_refs": self.extract_biblical_refs(text),
            "concepts": self.extract_concepts(text),
            "timestamp": datetime.now().isoformat()
        }

    def _get_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Get surrounding context for a match."""
        ctx_start = max(0, start - window)
        ctx_end = min(len(text), end + window)
        return text[ctx_start:ctx_end].replace('\n', ' ').strip()

    def _is_likely_person(self, name: str) -> bool:
        """Heuristic check if string is likely a person name."""
        words = name.split()
        if len(words) < 2 or len(words) > 4:
            return False

        # Filter common non-names
        non_names = {'the', 'this', 'that', 'with', 'from', 'into', 'upon'}
        if any(w.lower() in non_names for w in words):
            return False

        # Check capitalization
        if not all(w[0].isupper() for w in words if len(w) > 1):
            return False

        return True


# =============================================================================
# AUTO-LINKER
# =============================================================================

class AutoLinker:
    """
    Automatically inserts wikilinks [[...]] into markdown files based on extracted entities
    and a custom terms dictionary (footnotes.yaml).
    """
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.extractor = EnhancedEntityExtractor()
        self.custom_terms = self._load_custom_terms()
        
    def _load_custom_terms(self) -> Dict[str, str]:
        """Load custom terms from 02_Config/footnotes.yaml."""
        terms = {}
        # Try multiple locations
        paths = [
            self.vault_path / "00_VAULT_SYSTEM" / "02_Config" / "footnotes.yaml",
            self.vault_path / "config" / "footnotes.yaml",
            self.vault_path / ".obsidian" / "footnotes.yaml"
        ]
        
        for path in paths:
            if path.exists():
                try:
                    loaded = yaml.safe_load(path.read_text(encoding='utf-8'))
                    if loaded and isinstance(loaded, dict):
                        terms.update(loaded)
                except Exception as e:
                    print(f"Error loading custom terms from {path}: {e}")
                    
        return terms

    def refresh_terms(self):
        """Reload custom terms."""
        self.custom_terms = self._load_custom_terms()
        
    def link_file(self, file_path: Path, link_all: bool = False) -> Tuple[bool, int]:
        """
        Scan a file and replace entities with wikilinks.
        Returns: (modified_boolean, count_of_links_added)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return False, 0
            
        original_content = content
        
        # 1. Get entities from content extraction
        entities = self.extractor.extract_all(content)
        
        # Flatten all entities into a list of "linkable items"
        linkables = set()
        for category in ["people", "theories", "biblical_refs", "concepts"]:
            for item in entities.get(category, []):
                linkables.add(item["name"])
        
        # 2. Add custom terms
        for term in self.custom_terms:
            linkables.add(term)
            
        # Convert to list and sort by length (longest first)
        linkables_list = sorted(list(linkables), key=len, reverse=True)
        
        total_links = 0
        
        for term in linkables_list:
            # Determine replacement
            if term in self.custom_terms:
                replacement = self.custom_terms[term] # e.g. "[[Target]]" or "[[Target|Label]]"
            else:
                replacement = f"[[{term}]]"
            
            # Skip if replacement is just the term itself (useless)
            if replacement == term:
                continue

            # Check if term is already linked. 
            # We want to replace 'term' with 'replacement', but NOT if it's inside [[...]] or already linked.
            
            # Escaping for regex
            term_esc = re.escape(term)
            
            # This regex attempts to find 'term' as a whole word, 
            # ensuring it's NOT preceded by '[[' and NOT followed by ']]'.
            # It also handles Markdown link syntax [Label](Url) protection to some degree if simple.
            
            pattern = re.compile(rf'(?<!\[\[)(?<!\[)\b{term_esc}\b(?!\]\])(?!\])')
            
            if link_all:
                new_content, count = pattern.subn(replacement, content)
            else:
                new_content, count = pattern.subn(replacement, content, count=1)
                
            if count > 0:
                content = new_content
                total_links += count
                    
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True, total_links
            
        return False, 0

    def scan_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Scan a file and return found linkable terms without modifying.
        Returns: Dict of {term: count} found in this file.
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            return {}
            
        # 1. Get entities
        entities = self.extractor.extract_all(content)
        
        # 2. Flatten
        linkables = set()
        for category in ["people", "theories", "biblical_refs", "concepts"]:
            for item in entities.get(category, []):
                linkables.add(item["name"])
        
        # 3. Add custom terms
        for term in self.custom_terms:
            linkables.add(term)
        
        found_counts = {}
        
        for term in linkables:
            # Check if present and unlinked
            term_esc = re.escape(term)
            pattern = re.compile(rf'(?<!\[\[)(?<!\[)\b{term_esc}\b(?!\]\])(?!\])')
            
            count = len(pattern.findall(content))
            if count > 0:
                found_counts[term] = count
                
        return found_counts

    def apply_links_to_file(self, file_path: Path, approved_terms: List[str], link_all: bool = False) -> int:
        """
        Apply links ONLY for the approved terms.
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return 0
            
        original_content = content
        
        # Sort approved terms by length (longest first)
        terms_sorted = sorted(approved_terms, key=len, reverse=True)
        total_applied = 0
        
        for term in terms_sorted:
            # Determine replacement
            if term in self.custom_terms:
                replacement = self.custom_terms[term]
            else:
                replacement = f"[[{term}]]"
            
            if replacement == term: continue
            
            term_esc = re.escape(term)
            pattern = re.compile(rf'(?<!\[\[)(?<!\[)\b{term_esc}\b(?!\]\])(?!\])')
            
            if link_all:
                new_content, count = pattern.subn(replacement, content)
            else:
                new_content, count = pattern.subn(replacement, content, count=1)
            
            if count > 0:
                content = new_content
                total_applied += count
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return total_applied
            
        return 0


# =============================================================================
# HIGH-QUALITY SOURCE LOOKUP
# =============================================================================

class SourceLookup:
    """
    Look up terms in high-quality academic sources.
    Priority: SEP > arXiv > IEP > PhilPapers > Scholarpedia > Wikipedia
    """

    def __init__(self):
        self.cache: Dict[str, Dict] = {}
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0

    def _rate_limit(self):
        """Ensure we don't hammer servers."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def lookup_term(self, term: str) -> List[Dict[str, Any]]:
        """
        Look up a term across all sources, returning results in priority order.
        """
        if term in self.cache:
            return self.cache[term]

        results = []

        # 1. Stanford Encyclopedia of Philosophy
        sep_result = self._check_sep(term)
        if sep_result:
            results.append(sep_result)

        # 2. arXiv (for scientific terms)
        arxiv_result = self._check_arxiv(term)
        if arxiv_result:
            results.append(arxiv_result)

        # 3. Internet Encyclopedia of Philosophy
        iep_result = self._check_iep(term)
        if iep_result:
            results.append(iep_result)

        # 4. PhilPapers
        philpapers_result = self._check_philpapers(term)
        if philpapers_result:
            results.append(philpapers_result)

        # 5. Scholarpedia
        scholarpedia_result = self._check_scholarpedia(term)
        if scholarpedia_result:
            results.append(scholarpedia_result)

        # 6. Google Scholar
        gs_result = self._check_google_scholar(term)
        if gs_result:
            results.append(gs_result)

        # 7. Wikipedia (fallback)
        wiki_result = self._check_wikipedia(term)
        if wiki_result:
            results.append(wiki_result)

        self.cache[term] = results
        return results

    def get_best_source(self, term: str) -> Optional[Dict[str, Any]]:
        """Get the highest-priority available source for a term."""
        results = self.lookup_term(term)
        if results:
            return min(results, key=lambda x: SOURCE_PRIORITY.get(x["source"], 99))
        return None

    def _check_sep(self, term: str) -> Optional[Dict[str, Any]]:
        """Check Stanford Encyclopedia of Philosophy."""
        self._rate_limit()

        # SEP uses lowercase, hyphenated URLs
        slug = term.lower().replace(' ', '-').replace("'", "")
        url = f"https://plato.stanford.edu/entries/{slug}/"

        try:
            response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return {
                    "source": "Stanford Encyclopedia of Philosophy",
                    "url": url,
                    "priority": SOURCE_PRIORITY["Stanford Encyclopedia of Philosophy"],
                    "verified": True
                }
        except Exception:
            pass

        # Try search
        search_url = f"https://plato.stanford.edu/search/searcher.py?query={quote(term)}"
        return {
            "source": "Stanford Encyclopedia of Philosophy",
            "url": search_url,
            "priority": SOURCE_PRIORITY["Stanford Encyclopedia of Philosophy"],
            "verified": False,
            "type": "search"
        }

    def _check_arxiv(self, term: str) -> Optional[Dict[str, Any]]:
        """Check arXiv for scientific papers."""
        search_url = f"https://arxiv.org/search/?query={quote(term)}&searchtype=all"
        return {
            "source": "arXiv",
            "url": search_url,
            "priority": SOURCE_PRIORITY["arXiv"],
            "verified": False,
            "type": "search"
        }

    def _check_iep(self, term: str) -> Optional[Dict[str, Any]]:
        """Check Internet Encyclopedia of Philosophy."""
        self._rate_limit()

        # IEP uses lowercase URLs
        slug = term.lower().replace(' ', '-').replace("'", "")
        url = f"https://iep.utm.edu/{slug}/"

        try:
            response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return {
                    "source": "Internet Encyclopedia of Philosophy",
                    "url": url,
                    "priority": SOURCE_PRIORITY["Internet Encyclopedia of Philosophy"],
                    "verified": True
                }
        except Exception:
            pass

        return None

    def _check_philpapers(self, term: str) -> Optional[Dict[str, Any]]:
        """Check PhilPapers."""
        search_url = f"https://philpapers.org/s/{quote(term)}"
        return {
            "source": "PhilPapers",
            "url": search_url,
            "priority": SOURCE_PRIORITY["PhilPapers"],
            "verified": False,
            "type": "search"
        }

    def _check_scholarpedia(self, term: str) -> Optional[Dict[str, Any]]:
        """Check Scholarpedia."""
        self._rate_limit()

        # Scholarpedia uses title case with underscores
        slug = term.replace(' ', '_')
        url = f"http://www.scholarpedia.org/article/{quote(slug)}"

        try:
            response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return {
                    "source": "Scholarpedia",
                    "url": url,
                    "priority": SOURCE_PRIORITY["Scholarpedia"],
                    "verified": True
                }
        except Exception:
            pass

        return None

    def _check_google_scholar(self, term: str) -> Optional[Dict[str, Any]]:
        """Check Google Scholar."""
        search_url = f"https://scholar.google.com/scholar?q={quote(term)}"
        return {
            "source": "Google Scholar",
            "url": search_url,
            "priority": SOURCE_PRIORITY["Google Scholar"],
            "verified": False,
            "type": "search"
        }

    def _check_wikipedia(self, term: str) -> Optional[Dict[str, Any]]:
        """Check Wikipedia (fallback)."""
        self._rate_limit()

        slug = term.replace(' ', '_')
        url = f"https://en.wikipedia.org/wiki/{quote(slug)}"

        try:
            response = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                return {
                    "source": "Wikipedia",
                    "url": response.url,  # Use final URL after redirects
                    "priority": SOURCE_PRIORITY["Wikipedia"],
                    "verified": True
                }
        except Exception:
            pass

        return None


# =============================================================================
# CONTENT DOWNLOADER
# =============================================================================

class ContentDownloader:
    """
    Download and convert content from academic sources to markdown.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.output_dir / "sep").mkdir(exist_ok=True)
        (self.output_dir / "arxiv").mkdir(exist_ok=True)
        (self.output_dir / "iep").mkdir(exist_ok=True)
        (self.output_dir / "wikipedia").mkdir(exist_ok=True)
        (self.output_dir / "other").mkdir(exist_ok=True)

    def download(self, url: str, term: str) -> Optional[Path]:
        """Download content from URL and convert to markdown."""
        if not HAS_BS4 or not HAS_MARKDOWNIFY:
            return None

        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code != 200:
                return None

            # Determine source type and output directory
            domain = urlparse(url).netloc
            if 'plato.stanford.edu' in domain:
                subdir = "sep"
            elif 'arxiv.org' in domain:
                subdir = "arxiv"
            elif 'iep.utm.edu' in domain:
                subdir = "iep"
            elif 'wikipedia.org' in domain:
                subdir = "wikipedia"
            else:
                subdir = "other"

            # Parse and convert to markdown
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove scripts, styles, etc.
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()

            # Get main content based on source
            main_content = self._extract_main_content(soup, domain)

            if main_content:
                markdown_content = md(str(main_content), heading_style="ATX")

                # Clean up
                markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)

                # Add header
                title = soup.find('title')
                title_text = title.get_text().strip() if title else term
                header = f"# {title_text}\n\nSource: {url}\nDownloaded: {datetime.now().isoformat()}\n\n---\n\n"

                # Save
                safe_name = re.sub(r'[<>:"/\\|?*]', '', term)[:100]
                output_path = self.output_dir / subdir / f"{safe_name}.md"
                output_path.write_text(header + markdown_content, encoding='utf-8')

                return output_path

        except Exception as e:
            print(f"Download error for {term}: {e}")

        return None

    def _extract_main_content(self, soup, domain: str):
        """Extract main content based on source."""
        if 'plato.stanford.edu' in domain:
            # SEP uses #aueditable for main content
            return soup.find('div', id='aueditable') or soup.find('div', id='content')
        elif 'iep.utm.edu' in domain:
            return soup.find('article') or soup.find('div', class_='entry-content')
        elif 'wikipedia.org' in domain:
            return soup.find('div', id='mw-content-text')
        elif 'scholarpedia.org' in domain:
            return soup.find('div', id='mw-content-text')
        else:
            # Generic
            for selector in ['main', 'article', '#content', '.content']:
                content = soup.select_one(selector)
                if content:
                    return content
            return soup.find('body')


# =============================================================================
# PDF SCANNER
# =============================================================================

class PDFScanner:
    """Scan PDFs and extract text for entity extraction."""

    def __init__(self):
        if not HAS_PYMUPDF:
            print("WARNING: PyMuPDF not installed. PDF scanning disabled.")

    def extract_text(self, pdf_path: Path) -> str:
        """Extract text from a PDF file."""
        if not HAS_PYMUPDF:
            return ""

        try:
            doc = fitz.open(pdf_path)
            text_parts = []

            for page in doc:
                text_parts.append(page.get_text())

            doc.close()
            return '\n\n'.join(text_parts)

        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

    def scan_directory(self, directory: Path) -> List[Dict[str, Any]]:
        """Scan all PDFs in a directory."""
        results = []

        for pdf_file in directory.glob("**/*.pdf"):
            text = self.extract_text(pdf_file)
            if text:
                results.append({
                    "path": str(pdf_file),
                    "filename": pdf_file.name,
                    "text_length": len(text),
                    "text": text
                })

        return results


# =============================================================================
# MAIN ENGINE
# =============================================================================

class KnowledgeAcquisitionEngine:
    """
    Main engine for knowledge acquisition.
    Integrates: entity extraction, source lookup, content download.
    """

    def __init__(self, db_engine=None, output_dir: Path = None):
        self.db = db_engine
        self.extractor = EnhancedEntityExtractor()
        self.source_lookup = SourceLookup()
        self.downloader = ContentDownloader(output_dir or Path("./knowledge_base"))
        self.pdf_scanner = PDFScanner()

        # Results tracking
        self.extraction_results = []
        self.download_queue = []

    def scan_paper(self, path: Path) -> Dict[str, Any]:
        """
        Scan a paper (PDF or markdown) and extract all entities.
        """
        if path.suffix.lower() == '.pdf':
            text = self.pdf_scanner.extract_text(path)
        else:
            text = path.read_text(encoding='utf-8', errors='ignore')

        if not text:
            return {"error": "Could not extract text", "path": str(path)}

        # Extract entities
        entities = self.extractor.extract_all(text)
        entities["source_file"] = str(path)

        self.extraction_results.append(entities)
        return entities

    def scan_directory(self, directory: Path, extensions: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scan all papers in a directory.
        """
        if extensions is None:
            extensions = ['.pdf', '.md', '.txt']

        results = []

        for ext in extensions:
            for file_path in directory.glob(f"**/*{ext}"):
                result = self.scan_paper(file_path)
                results.append(result)

        return results

    def lookup_and_link(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up extracted entities in high-quality sources.
        """
        linked = {
            "theories": [],
            "people": [],
        }

        # Look up theories
        for theory in entities.get("theories", []):
            sources = self.source_lookup.lookup_term(theory["name"])
            best = self.source_lookup.get_best_source(theory["name"])
            linked["theories"].append({
                **theory,
                "sources": sources,
                "best_source": best
            })

        # Look up people
        for person in entities.get("people", []):
            sources = self.source_lookup.lookup_term(person["name"])
            best = self.source_lookup.get_best_source(person["name"])
            linked["people"].append({
                **person,
                "sources": sources,
                "best_source": best
            })

        return linked

    def download_best_sources(self, linked_entities: Dict[str, Any]) -> List[Path]:
        """
        Download content from the best available sources.
        """
        downloaded = []

        for entity_type in ["theories", "people"]:
            for entity in linked_entities.get(entity_type, []):
                best = entity.get("best_source")
                if best and best.get("verified"):
                    path = self.downloader.download(best["url"], entity["name"])
                    if path:
                        downloaded.append(path)

        return downloaded

    def process_paper(self, path: Path, download: bool = True) -> Dict[str, Any]:
        """
        Full pipeline: scan -> lookup -> optionally download.
        """
        # Step 1: Extract entities
        entities = self.scan_paper(path)

        if "error" in entities:
            return entities

        # Step 2: Look up sources
        linked = self.lookup_and_link(entities)

        # Step 3: Download if requested
        downloaded_paths = []
        if download:
            downloaded_paths = self.download_best_sources(linked)

        return {
            "source_file": str(path),
            "entities": entities,
            "linked": linked,
            "downloaded": [str(p) for p in downloaded_paths],
            "summary": {
                "theories_found": len(entities.get("theories", [])),
                "people_found": len(entities.get("people", [])),
                "citations_found": len(entities.get("citations", [])),
                "sources_downloaded": len(downloaded_paths),
            }
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get extraction statistics."""
        all_theories = []
        all_people = []
        all_citations = []

        for result in self.extraction_results:
            all_theories.extend(result.get("theories", []))
            all_people.extend(result.get("people", []))
            all_citations.extend(result.get("citations", []))

        # Count unique
        unique_theories = {t["name"] for t in all_theories}
        unique_people = {p["name"] for p in all_people}

        return {
            "papers_scanned": len(self.extraction_results),
            "total_theories": len(all_theories),
            "unique_theories": len(unique_theories),
            "total_people": len(all_people),
            "unique_people": len(unique_people),
            "total_citations": len(all_citations),
            "theory_types": self._count_by_key(all_theories, "type"),
        }

    def _count_by_key(self, items: List[Dict], key: str) -> Dict[str, int]:
        """Count items by a specific key."""
        counts = {}
        for item in items:
            val = item.get(key, "unknown")
            counts[val] = counts.get(val, 0) + 1
        return counts


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def scan_papers_in_directory(directory: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Convenience function to scan all papers in a directory.
    """
    dir_path = Path(directory)
    out_path = Path(output_dir) if output_dir else dir_path / "knowledge_base"

    engine = KnowledgeAcquisitionEngine(output_dir=out_path)

    results = []
    for pdf in dir_path.glob("**/*.pdf"):
        result = engine.process_paper(pdf, download=False)
        results.append(result)

    for md_file in dir_path.glob("**/*.md"):
        if "knowledge_base" not in str(md_file):  # Skip output
            result = engine.process_paper(md_file, download=False)
            results.append(result)

    return {
        "results": results,
        "statistics": engine.get_statistics()
    }


if __name__ == "__main__":
    # Quick test
    print("Knowledge Acquisition Engine")
    print("=" * 50)

    engine = KnowledgeAcquisitionEngine()

    # Test entity extraction
    test_text = """
    Einstein's Theory of General Relativity revolutionized our understanding
    of gravity. Building on the work of Newton and Maxwell, Einstein showed
    that spacetime itself is curved by mass and energy. Bell's Theorem later
    proved the non-local nature of quantum mechanics (Bell, 1964).
    Penrose and Hawking extended these ideas to black holes.
    """

    entities = engine.extractor.extract_all(test_text)
    print("\nExtracted Entities:")
    print(f"  Theories: {[t['name'] for t in entities['theories']]}")
    print(f"  People: {[p['name'] for p in entities['people']]}")
    print(f"  Citations: {entities['citations']}")

    # Test source lookup
    print("\nSource Lookup for 'General Relativity':")
    sources = engine.source_lookup.lookup_term("General Relativity")
    for src in sources:
        print(f"  [{src['priority']}] {src['source']}: {src['url'][:60]}...")
