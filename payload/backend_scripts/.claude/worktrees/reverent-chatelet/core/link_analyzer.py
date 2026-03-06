"""
Link Analyzer for Theophysics Vault
===================================
Detects and categorizes links in markdown files:
- Internal links (wikilinks)
- External links (URLs)
- Glossary links (to LEXICON folder)
- Dual-links (terms with both glossary AND external references)

This integrates with the vault sync and CSS styling system.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class LinkInfo:
    """Information about a single link."""
    text: str  # Display text
    target: str  # Link target (path or URL)
    link_type: str  # 'internal', 'external', 'glossary'
    line_number: int = 0
    is_first_mention: bool = False


@dataclass
class TermLinks:
    """All links associated with a term/concept."""
    term: str
    glossary_link: Optional[str] = None  # Internal link to LEXICON
    external_links: List[str] = field(default_factory=list)  # URLs
    internal_links: List[str] = field(default_factory=list)  # Other internal
    
    @property
    def is_dual_link(self) -> bool:
        """True if term has both glossary AND external links."""
        return self.glossary_link is not None and len(self.external_links) > 0
    
    @property
    def link_types(self) -> List[str]:
        """List of link types available for this term."""
        types = []
        if self.glossary_link:
            types.append('glossary')
        if self.external_links:
            types.append('external')
        if self.internal_links:
            types.append('internal')
        return types


class LinkAnalyzer:
    """Analyzes links in Obsidian vault files."""
    
    # Regex patterns
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
    MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    URL_PATTERN = re.compile(r'https?://[^\s\)>\]]+')
    
    # Known academic/reference domains
    ACADEMIC_DOMAINS = {
        'plato.stanford.edu': 'Stanford Encyclopedia',
        'sep.': 'Stanford Encyclopedia',
        'arxiv.org': 'arXiv',
        'doi.org': 'DOI',
        'jstor.org': 'JSTOR',
        'wikipedia.org': 'Wikipedia',
        'ncbi.nlm.nih.gov': 'PubMed',
        'nature.com': 'Nature',
        'science.org': 'Science',
        'aps.org': 'APS Physics',
    }
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.lexicon_path = self.vault_path / "02_LIBRARY" / "4_LEXICON"
        self.glossary_terms: Set[str] = set()
        self._load_glossary_terms()
    
    def _load_glossary_terms(self):
        """Load all terms from the glossary/lexicon."""
        if not self.lexicon_path.exists():
            return
        
        for md_file in self.lexicon_path.glob("*.md"):
            term = md_file.stem.lower()
            self.glossary_terms.add(term)
            
            # Also load aliases from frontmatter
            try:
                content = md_file.read_text(encoding='utf-8')
                fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                if fm_match:
                    import yaml
                    fm = yaml.safe_load(fm_match.group(1)) or {}
                    aliases = fm.get('aliases', [])
                    if isinstance(aliases, str):
                        aliases = [aliases]
                    for alias in aliases:
                        if alias:
                            self.glossary_terms.add(alias.lower())
            except:
                pass
    
    def is_glossary_link(self, target: str) -> bool:
        """Check if a link target points to the glossary."""
        target_lower = target.lower()
        # Direct path check
        if 'lexicon' in target_lower or '4_lexicon' in target_lower:
            return True
        # Term name check
        term = Path(target).stem.lower()
        return term in self.glossary_terms
    
    def classify_external_link(self, url: str) -> str:
        """Classify an external URL by domain."""
        for domain, name in self.ACADEMIC_DOMAINS.items():
            if domain in url.lower():
                return name
        return 'external'
    
    def analyze_file(self, file_path: Path) -> Dict[str, TermLinks]:
        """
        Analyze all links in a file and group by term.
        
        Returns dict mapping term -> TermLinks
        """
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            return {}
        
        terms: Dict[str, TermLinks] = {}
        
        # Find all wikilinks
        for match in self.WIKILINK_PATTERN.finditer(content):
            target = match.group(1)
            display = match.group(2) or target
            term_key = display.lower().strip()
            
            if term_key not in terms:
                terms[term_key] = TermLinks(term=display)
            
            if self.is_glossary_link(target):
                terms[term_key].glossary_link = target
            else:
                if target not in terms[term_key].internal_links:
                    terms[term_key].internal_links.append(target)
        
        # Find all markdown links with URLs
        for match in self.MARKDOWN_LINK_PATTERN.finditer(content):
            display = match.group(1)
            url = match.group(2)
            
            if url.startswith('http'):
                term_key = display.lower().strip()
                
                if term_key not in terms:
                    terms[term_key] = TermLinks(term=display)
                
                if url not in terms[term_key].external_links:
                    terms[term_key].external_links.append(url)
        
        return terms
    
    def find_dual_links(self, file_path: Path) -> List[TermLinks]:
        """Find all terms in a file that have both glossary AND external links."""
        terms = self.analyze_file(file_path)
        return [t for t in terms.values() if t.is_dual_link]
    
    def scan_vault_for_dual_links(self) -> Dict[str, List[Dict]]:
        """
        Scan entire vault for dual-link terms.
        
        Returns dict mapping file path -> list of dual-link term info
        """
        results = {}
        
        for md_file in self.vault_path.rglob("*.md"):
            # Skip system folders
            if any(skip in str(md_file) for skip in [".obsidian", "node_modules", ".git"]):
                continue
            
            dual_links = self.find_dual_links(md_file)
            if dual_links:
                rel_path = str(md_file.relative_to(self.vault_path))
                results[rel_path] = [
                    {
                        'term': dl.term,
                        'glossary': dl.glossary_link,
                        'external': dl.external_links,
                        'external_types': [self.classify_external_link(url) for url in dl.external_links]
                    }
                    for dl in dual_links
                ]
        
        return results
    
    def generate_dual_link_report(self) -> str:
        """Generate a markdown report of all dual-link terms."""
        results = self.scan_vault_for_dual_links()
        
        lines = [
            "# Dual-Link Terms Report",
            "",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
            "Terms that have **both** a glossary definition AND external reference.",
            "These can show `[Glossary] [External]` options on hover.",
            "",
            f"**Total files with dual-links:** {len(results)}",
            "",
            "---",
            ""
        ]
        
        total_terms = 0
        for file_path, terms in sorted(results.items()):
            lines.append(f"## `{file_path}`")
            lines.append("")
            for term_info in terms:
                total_terms += 1
                lines.append(f"### {term_info['term']}")
                lines.append(f"- **Glossary:** [[{term_info['glossary']}]]")
                for url, url_type in zip(term_info['external'], term_info['external_types']):
                    lines.append(f"- **{url_type}:** [{url[:50]}...]({url})")
                lines.append("")
        
        lines.insert(9, f"**Total dual-link terms:** {total_terms}")
        
        return "\n".join(lines)
    
    def get_link_stats(self) -> Dict:
        """Get statistics about links in the vault."""
        stats = {
            'total_files': 0,
            'files_with_links': 0,
            'total_internal_links': 0,
            'total_external_links': 0,
            'total_glossary_links': 0,
            'dual_link_terms': 0,
            'external_domains': defaultdict(int)
        }
        
        for md_file in self.vault_path.rglob("*.md"):
            if any(skip in str(md_file) for skip in [".obsidian", "node_modules", ".git"]):
                continue
            
            stats['total_files'] += 1
            terms = self.analyze_file(md_file)
            
            if terms:
                stats['files_with_links'] += 1
            
            for term in terms.values():
                if term.glossary_link:
                    stats['total_glossary_links'] += 1
                stats['total_internal_links'] += len(term.internal_links)
                stats['total_external_links'] += len(term.external_links)
                
                if term.is_dual_link:
                    stats['dual_link_terms'] += 1
                
                for url in term.external_links:
                    domain = self.classify_external_link(url)
                    stats['external_domains'][domain] += 1
        
        stats['external_domains'] = dict(stats['external_domains'])
        return stats


# CLI for testing
if __name__ == "__main__":
    vault_path = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    
    print("=" * 60)
    print("LINK ANALYZER")
    print("=" * 60)
    
    analyzer = LinkAnalyzer(vault_path)
    
    print(f"\nGlossary terms loaded: {len(analyzer.glossary_terms)}")
    
    print("\nScanning vault for link statistics...")
    stats = analyzer.get_link_stats()
    
    print(f"\nTotal files: {stats['total_files']}")
    print(f"Files with links: {stats['files_with_links']}")
    print(f"Internal links: {stats['total_internal_links']}")
    print(f"Glossary links: {stats['total_glossary_links']}")
    print(f"External links: {stats['total_external_links']}")
    print(f"Dual-link terms: {stats['dual_link_terms']}")
    
    print("\nExternal link domains:")
    for domain, count in sorted(stats['external_domains'].items(), key=lambda x: -x[1])[:10]:
        print(f"  {domain}: {count}")
    
    # Generate report
    print("\nGenerating dual-link report...")
    report = analyzer.generate_dual_link_report()
    report_path = Path(vault_path) / "_TAG_NOTES" / "_DUAL_LINK_REPORT.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"Report saved to: {report_path}")
