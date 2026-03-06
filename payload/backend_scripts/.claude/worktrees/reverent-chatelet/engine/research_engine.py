# engine/research_engine.py

from typing import List, Dict, Any, Set
import re
import sqlite3
from pathlib import Path


class EntityExtractor:
    """
    Extract entities from text:
    - People (names with titles, capitalization patterns)
    - Places (geographical locations)
    - Scientific terms (technical vocabulary)
    - Academic references (citations)
    """
    
    # Common titles and honorifics
    TITLES = r'(?:Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|Sir|Lord|Lady)'
    
    # Academic/scientific term patterns
    SCIENTIFIC_PATTERNS = [
        r'\b[A-Z][a-z]+ (?:theorem|principle|law|effect|constant|equation|hypothesis|theory)\b',
        r'\b(?:quantum|relativistic|electromagnetic|thermodynamic|kinetic|potential) [a-z]+\b',
    ]
    
    # Citation patterns
    CITATION_PATTERNS = [
        r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?[,\s]+\d{4})\)',  # (Author, 2020)
        r'\[(\d+)\]',  # [1]
        r'\[\^(\w+)\]',  # [^ref1]
    ]
    
    def __init__(self):
        self.person_cache: Set[str] = set()
        self.place_cache: Set[str] = set()
        self.term_cache: Set[str] = set()
    
    def extract_people(self, text: str) -> List[str]:
        """Extract person names from text."""
        people = []
        
        # Pattern 1: Title + Name
        pattern1 = re.compile(rf'{self.TITLES}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)')
        people.extend(pattern1.findall(text))
        
        # Pattern 2: Full names (First Last, First Middle Last)
        pattern2 = re.compile(r'\b([A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+)?[A-Z][a-z]+)\b')
        candidates = pattern2.findall(text)
        
        # Filter out obvious non-names
        for candidate in candidates:
            words = candidate.split()
            if len(words) >= 2 and len(words) <= 4:
                # Simple heuristic: all words capitalized, reasonable length
                if all(2 <= len(w) <= 15 for w in words):
                    people.append(candidate)
        
        return list(set(people))
    
    def extract_places(self, text: str) -> List[str]:
        """Extract geographical places."""
        places = []
        
        # Pattern: Capitalized words followed by geographical indicators
        pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:University|Institute|Laboratory|College|City|State|Country|Ocean|Sea|River|Mountain)\b')
        places.extend(pattern.findall(text))
        
        # Common place name patterns
        pattern2 = re.compile(r'\b((?:New|San|Los|North|South|East|West)\s+[A-Z][a-z]+)\b')
        places.extend(pattern2.findall(text))
        
        return list(set(places))
    
    def extract_scientific_terms(self, text: str) -> List[str]:
        """Extract scientific and technical terms."""
        terms = []
        
        for pattern_str in self.SCIENTIFIC_PATTERNS:
            pattern = re.compile(pattern_str)
            terms.extend(pattern.findall(text))
        
        # Extract capitalized technical terms
        pattern = re.compile(r'\b([A-Z][a-z]+(?:\s+[a-z]+){1,3})\b')
        candidates = pattern.findall(text)
        
        # Filter for technical terms (heuristic: contains certain keywords)
        technical_keywords = ['effect', 'theory', 'principle', 'model', 'system', 'method']
        for candidate in candidates:
            if any(kw in candidate.lower() for kw in technical_keywords):
                terms.append(candidate)
        
        return list(set(terms))
    
    def extract_citations(self, text: str) -> List[Dict[str, str]]:
        """Extract academic citations."""
        citations = []
        
        for pattern_str in self.CITATION_PATTERNS:
            pattern = re.compile(pattern_str)
            matches = pattern.findall(text)
            for match in matches:
                citations.append({
                    "reference": match,
                    "type": "inline" if "(" in pattern_str else "footnote"
                })
        
        return citations
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """Extract all entity types from text."""
        return {
            "people": self.extract_people(text),
            "places": self.extract_places(text),
            "scientific_terms": self.extract_scientific_terms(text),
            "citations": self.extract_citations(text),
        }


class ResearchLinkEngine:
    """
    Advanced research link management with:
    - Entity extraction (people, places, terms)
    - Auto-linking to research sources
    - Integration hooks for SEP, PhilPapers, arXiv
    - Citation tracking
    """
    
    def __init__(self, settings, db_engine):
        self.settings = settings
        self.db = db_engine
        self.entity_extractor = EntityExtractor()

    def add_custom_link(self, term: str, source: str, url: str):
        if not term or not url:
            return
        self.db.add_research_link(term, source, url)

    def process_text_links(self, text: str, terms: List[str]) -> str:
        """
        Wrap exact term matches with markdown links using the first
        custom link for that term if it exists, otherwise just [[term]].
        """
        links_by_term = self.db.get_research_links()

        out = text
        for term in terms:
            key = term.lower()
            targets = links_by_term.get(key, [])
            if targets:
                url = targets[0]["url"]
                md = f"[{term}]({url})"
            else:
                md = f"[[{term}]]"

            # simple word-boundary replace
            pattern = r"\b" + re.escape(term) + r"\b"
            out = re.sub(pattern, md, out)

        return out

    def extract_entities_from_vault(self) -> Dict[str, List[str]]:
        """
        Extract all entities from the entire vault.
        Returns counts and lists of people, places, scientific terms.
        """
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        c.execute("SELECT path, title FROM notes")
        notes = c.fetchall()
        conn.close()
        
        all_people = []
        all_places = []
        all_terms = []
        all_citations = []
        
        for path, title in notes:
            try:
                text = Path(path).read_text(encoding="utf-8", errors="ignore")
                entities = self.entity_extractor.extract_all(text)
                
                all_people.extend(entities["people"])
                all_places.extend(entities["places"])
                all_terms.extend(entities["scientific_terms"])
                all_citations.extend(entities["citations"])
            except Exception:
                continue
        
        return {
            "people": list(set(all_people)),
            "places": list(set(all_places)),
            "scientific_terms": list(set(all_terms)),
            "citations": all_citations,
            "counts": {
                "unique_people": len(set(all_people)),
                "unique_places": len(set(all_places)),
                "unique_terms": len(set(all_terms)),
                "total_citations": len(all_citations),
            }
        }

    def generate_research_links_for_term(self, term: str) -> List[Dict[str, str]]:
        """
        Generate potential research links for a term from common sources.
        Returns list of {source, url} dicts.
        """
        links = []
        
        # Wikipedia
        wiki_url = f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}"
        links.append({"source": "Wikipedia", "url": wiki_url})
        
        # Stanford Encyclopedia of Philosophy
        sep_url = f"https://plato.stanford.edu/search/searcher.py?query={term.replace(' ', '+')}"
        links.append({"source": "Stanford Encyclopedia", "url": sep_url})
        
        # arXiv (for scientific terms)
        arxiv_url = f"https://arxiv.org/search/?query={term.replace(' ', '+')}&searchtype=all"
        links.append({"source": "arXiv", "url": arxiv_url})
        
        # Google Scholar
        scholar_url = f"https://scholar.google.com/scholar?q={term.replace(' ', '+')}"
        links.append({"source": "Google Scholar", "url": scholar_url})
        
        # PhilPapers
        philpapers_url = f"https://philpapers.org/s/{term.replace(' ', '%20')}"
        links.append({"source": "PhilPapers", "url": philpapers_url})
        
        return links

    def auto_link_entities_in_note(self, note_path: Path) -> str:
        """
        Automatically add research links to entities found in a note.
        Returns the modified note text.
        """
        if not note_path.exists():
            return ""
        
        text = note_path.read_text(encoding="utf-8", errors="ignore")
        entities = self.entity_extractor.extract_all(text)
        
        # Build list of all entities to link
        all_entities = []
        all_entities.extend(entities["people"])
        all_entities.extend(entities["places"])
        all_entities.extend(entities["scientific_terms"])
        
        # Get existing research links from DB
        links_by_term = self.db.get_research_links()
        
        # Replace entities with links
        modified_text = text
        for entity in all_entities:
            key = entity.lower()
            if key in links_by_term:
                # Use existing research link
                url = links_by_term[key][0]["url"]
                replacement = f"[{entity}]({url})"
            else:
                # Use wiki-link
                replacement = f"[[{entity}]]"
            
            # Replace first occurrence only to avoid over-linking
            pattern = r'\b' + re.escape(entity) + r'\b'
            modified_text = re.sub(pattern, replacement, modified_text, count=1)
        
        return modified_text

    def get_research_statistics(self) -> Dict[str, Any]:
        """Get statistics about research links and entities."""
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        # Count research links by source
        c.execute("SELECT source, COUNT(*) FROM research_links GROUP BY source")
        by_source = dict(c.fetchall())
        
        # Count total terms with research links
        c.execute("SELECT COUNT(DISTINCT term) FROM research_links")
        unique_terms = c.fetchone()[0]
        
        conn.close()
        
        return {
            "by_source": by_source,
            "unique_terms_with_links": unique_terms,
            "total_links": sum(by_source.values()),
        }

