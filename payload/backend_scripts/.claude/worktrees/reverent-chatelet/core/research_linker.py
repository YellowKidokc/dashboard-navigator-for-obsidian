"""
Research Linker - Automatically generates structured research links
for Stanford Encyclopedia, arXiv, IEP, and other academic sources.
"""

from typing import Dict, List, Optional
from pathlib import Path
import re


class ResearchLinker:
    """Manages research links for academic sources."""
    
    # Standard link templates - Full research cascade
    LINK_TEMPLATES = {
        'stanford': {
            'base_url': 'https://plato.stanford.edu/entries/',
            'format': '{base_url}{slug}/',
            'display_name': 'Stanford Encyclopedia of Philosophy',
            'examples': {
                'quantum mechanics': 'qm/',
                'general relativity': 'general-relativity/',
                'consciousness': 'consciousness/',
                'measurement problem': 'qt-measurement/',
                'copenhagen interpretation': 'qm-copenhagen/',
                'delayed-choice experiment': 'quantum-mechanics/#DelayedChoice',
            }
        },
        'iep': {
            'base_url': 'https://iep.utm.edu/',
            'format': '{base_url}{slug}/',
            'display_name': 'Internet Encyclopedia of Philosophy',
            'examples': {
                'hard problem of consciousness': 'hard-problem-of-consciousness/',
            }
        },
        'oxford': {
            'base_url': 'https://www.oxfordreference.com/view/10.1093/acref/',
            'format': '{base_url}{slug}',
            'display_name': 'Oxford Reference',
            'examples': {}
        },
        'cambridge': {
            'base_url': 'https://www.cambridge.org/core/search?q=',
            'format': '{base_url}{slug}',
            'display_name': 'Cambridge Companion',
            'examples': {}
        },
        'philpapers': {
            'base_url': 'https://philpapers.org/browse/',
            'format': '{base_url}{slug}',
            'display_name': 'PhilPapers',
            'examples': {}
        },
        'philarchive': {
            'base_url': 'https://philarchive.org/rec/',
            'format': '{base_url}{slug}',
            'display_name': 'PhilArchive',
            'examples': {}
        },
        'scholar': {
            'base_url': 'https://scholar.google.com/scholar?q=',
            'format': '{base_url}{slug}',
            'display_name': 'Google Scholar',
            'examples': {}
        },
        'jstor': {
            'base_url': 'https://www.jstor.org/action/doBasicSearch?Query=',
            'format': '{base_url}{slug}',
            'display_name': 'JSTOR',
            'examples': {}
        },
        'muse': {
            'base_url': 'https://muse.jhu.edu/search?q=',
            'format': '{base_url}{slug}',
            'display_name': 'Project MUSE',
            'examples': {}
        },
        'britannica': {
            'base_url': 'https://www.britannica.com/search?query=',
            'format': '{base_url}{slug}',
            'display_name': 'Britannica',
            'examples': {}
        },
        'arxiv': {
            'base_url': 'https://arxiv.org/abs/',
            'format': '{base_url}{paper_id}',
            'display_name': 'arXiv',
            'examples': {
                'wheeler delayed-choice': 'quant-ph/0504091',
                'participatory universe': 'quant-ph/0306072',
            }
        },
        'wikipedia': {
            'base_url': 'https://en.wikipedia.org/wiki/',
            'format': '{base_url}{slug}',
            'display_name': 'Wikipedia',
            'examples': {}
        }
    }
    
    # Default link priority order (recommended cascade)
    DEFAULT_LINK_PRIORITY = [
        'stanford', 'iep', 'oxford', 'cambridge', 'philpapers', 
        'philarchive', 'scholar', 'jstor', 'muse', 'britannica', 
        'arxiv', 'wikipedia'
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the research linker."""
        self.config_path = config_path or Path(__file__).parent.parent / 'config' / 'research_links.json'
        self.config_dir = self.config_path.parent
        self.priority_config_path = self.config_dir / 'research_priority.json'
        self.custom_links: Dict[str, Dict[str, str]] = {}
        self.link_priority: List[str] = self.DEFAULT_LINK_PRIORITY.copy()
        self._load_custom_links()
        self._load_priority_config()
    
    def _load_custom_links(self) -> None:
        """Load custom link mappings from config."""
        import json
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.custom_links = json.load(f)
            except Exception:
                self.custom_links = {}
    
    def _save_custom_links(self) -> None:
        """Save custom link mappings to config."""
        import json
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.custom_links, f, indent=2, ensure_ascii=False)
    
    def _load_priority_config(self) -> None:
        """Load priority order from config."""
        import json
        if self.priority_config_path.exists():
            try:
                with open(self.priority_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'priority' in config and isinstance(config['priority'], list):
                        # Validate all sources exist
                        valid_priority = [s for s in config['priority'] if s in self.LINK_TEMPLATES]
                        if valid_priority:
                            self.link_priority = valid_priority
            except Exception:
                pass  # Use default
    
    def _save_priority_config(self) -> None:
        """Save priority order to config."""
        import json
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.priority_config_path, 'w', encoding='utf-8') as f:
            json.dump({'priority': self.link_priority}, f, indent=2, ensure_ascii=False)
    
    def set_priority_order(self, priority: List[str]) -> None:
        """Set the priority order for link sources."""
        # Validate all sources exist
        valid_priority = [s for s in priority if s in self.LINK_TEMPLATES]
        if valid_priority:
            self.link_priority = valid_priority
            self._save_priority_config()
    
    def get_priority_order(self) -> List[str]:
        """Get current priority order."""
        return self.link_priority.copy()
    
    def generate_link(self, term: str, source: str = 'auto') -> Optional[str]:
        """
        Generate a research link for a term.
        
        Args:
            term: The term to link
            source: 'auto', 'stanford', 'arxiv', 'iep', 'wikipedia', or custom source name
        
        Returns:
            URL string or None if not found
        """
        term_lower = term.lower().strip()
        
        # Check custom links first
        if term_lower in self.custom_links:
            custom = self.custom_links[term_lower]
            if source == 'auto':
                # Return highest priority available
                for priority_source in self.LINK_PRIORITY:
                    if priority_source in custom:
                        return custom[priority_source]
                # Return first available
                if custom:
                    return list(custom.values())[0]
            elif source in custom:
                return custom[source]
        
        # Check standard templates
        if source == 'auto':
            # Try each source in priority order
            for priority_source in self.link_priority:
                link = self._try_generate_link(term_lower, priority_source)
                if link:
                    return link
        else:
            return self._try_generate_link(term_lower, source)
        
        return None
    
    def _try_generate_link(self, term: str, source: str) -> Optional[str]:
        """Try to generate a link from a specific source."""
        if source not in self.LINK_TEMPLATES:
            return None
        
        template = self.LINK_TEMPLATES[source]
        
        # Check examples first
        if term in template['examples']:
            slug = template['examples'][term]
            return template['format'].format(
                base_url=template['base_url'],
                slug=slug
            )
        
        # Try fuzzy matching
        for example_term, slug in template['examples'].items():
            if example_term in term or term in example_term:
                return template['format'].format(
                    base_url=template['base_url'],
                    slug=slug
                )
        
        # Generate from term (for sources that support it)
        if source in ['wikipedia', 'scholar', 'jstor', 'muse', 'britannica', 'oxford', 'cambridge', 'philpapers', 'philarchive']:
            # Convert term to URL-encoded format
            from urllib.parse import quote_plus
            if source == 'wikipedia':
                slug = term.replace(' ', '_').title()
            else:
                slug = quote_plus(term)
            return template['format'].format(slug=slug)
        
        return None
    
    def add_custom_link(self, term: str, source: str, url: str) -> None:
        """Add a custom link mapping."""
        term_lower = term.lower().strip()
        if term_lower not in self.custom_links:
            self.custom_links[term_lower] = {}
        self.custom_links[term_lower][source] = url
        self._save_custom_links()
    
    def get_all_links_for_term(self, term: str) -> Dict[str, str]:
        """Get all available links for a term."""
        term_lower = term.lower().strip()
        links = {}
        
        # Check custom links
        if term_lower in self.custom_links:
            links.update(self.custom_links[term_lower])
        
        # Check standard templates
        for source in self.link_priority:
            link = self._try_generate_link(term_lower, source)
            if link and source not in links:
                links[source] = link
        
        return links
    
    def format_markdown_link(self, term: str, url: str, source: Optional[str] = None) -> str:
        """Format a markdown link."""
        if source:
            return f"[{term}]({url}) ({source})"
        return f"[{term}]({url})"
    
    def process_text_for_links(self, text: str, terms: List[str]) -> str:
        """
        Process text and add research links for specified terms.
        
        Args:
            text: The text to process
            terms: List of terms to link
        
        Returns:
            Text with markdown links added
        """
        result = text
        
        for term in terms:
            # Find term in text (case-insensitive, whole word)
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            
            # Get best link for term
            link_url = self.generate_link(term)
            if link_url:
                # Replace first occurrence with linked version
                replacement = self.format_markdown_link(term, link_url)
                result = pattern.sub(replacement, result, count=1)
        
        return result
    
    def generate_link_section(self, terms: List[str], title: str = "Research Links") -> str:
        """
        Generate a markdown section with all links for given terms.
        
        Args:
            terms: List of terms to generate links for
            title: Section title
        
        Returns:
            Markdown formatted link section
        """
        lines = [f"## {title}", ""]
        
        for term in terms:
            links = self.get_all_links_for_term(term)
            if links:
                lines.append(f"### {term.title()}")
                for source, url in sorted(links.items()):
                    source_name = source.replace('_', ' ').title()
                    lines.append(f"- [{source_name}]({url})")
                lines.append("")
        
        return "\n".join(lines)

