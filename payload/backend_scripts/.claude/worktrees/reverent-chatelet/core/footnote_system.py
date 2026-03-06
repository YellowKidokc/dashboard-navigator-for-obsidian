"""
Footnote System - Generates footnotes with links to academic sources and Obsidian vault.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re
from dataclasses import dataclass


@dataclass
class Footnote:
    """Represents a single footnote."""
    marker: int
    term: str
    vault_link: Optional[str] = None  # Obsidian link like [[Glossary#Term]]
    academic_links: Dict[str, str] = None  # {'stanford': 'url', 'arxiv': 'url'}
    explanation: str = ""  # Simple explanation text
    
    def __post_init__(self):
        if self.academic_links is None:
            self.academic_links = {}


class FootnoteSystem:
    """Manages footnote generation and linking."""
    
    def __init__(self, research_linker, vault_path: Optional[Path] = None):
        """
        Initialize footnote system.
        
        Args:
            research_linker: ResearchLinker instance for academic links
            vault_path: Path to Obsidian vault for glossary links
        """
        self.research_linker = research_linker
        self.vault_path = vault_path
        self.footnotes: List[Footnote] = []
        self.term_to_footnote: Dict[str, int] = {}  # Maps term to footnote marker
    
    def add_footnote(
        self,
        term: str,
        vault_link: Optional[str] = None,
        academic_sources: Optional[List[str]] = None,
        explanation: str = ""
    ) -> int:
        """
        Add a footnote for a term.
        
        Args:
            term: The term to footnote
            vault_link: Obsidian link (e.g., "[[Glossary#Logos]]")
            academic_sources: List of source names to include (e.g., ['stanford', 'arxiv'])
            explanation: Simple explanation text
        
        Returns:
            Footnote marker number
        """
        # Check if we already have this term
        if term.lower() in self.term_to_footnote:
            return self.term_to_footnote[term.lower()]
        
        # Get academic links
        academic_links = {}
        if academic_sources:
            for source in academic_sources:
                link = self.research_linker.generate_link(term, source)
                if link:
                    academic_links[source] = link
        else:
            # Auto-generate best academic link
            link = self.research_linker.generate_link(term)
            if link:
                # Determine which source it came from
                all_links = self.research_linker.get_all_links_for_term(term)
                if all_links:
                    # Use first available source
                    source = list(all_links.keys())[0]
                    academic_links[source] = all_links[source]
        
        # Generate vault link if not provided
        if not vault_link:
            vault_link = self._generate_vault_link(term)
        
        # Create footnote
        marker = len(self.footnotes) + 1
        footnote = Footnote(
            marker=marker,
            term=term,
            vault_link=vault_link,
            academic_links=academic_links,
            explanation=explanation
        )
        
        self.footnotes.append(footnote)
        self.term_to_footnote[term.lower()] = marker
        
        return marker
    
    def _generate_vault_link(self, term: str) -> str:
        """Generate an Obsidian vault link for a term."""
        # Convert term to glossary link format
        # e.g., "quantum mechanics" -> "[[Glossary#Quantum Mechanics]]"
        term_title = term.title()
        return f"[[Glossary#{term_title}]]"
    
    def process_text(
        self,
        text: str,
        terms: List[str],
        auto_explanations: bool = False
    ) -> Tuple[str, str]:
        """
        Process text and add footnotes.
        
        Args:
            text: The text to process
            terms: List of terms to footnote
            auto_explanations: Whether to auto-generate simple explanations
        
        Returns:
            Tuple of (processed_text, footnotes_section)
        """
        result_text = text
        processed_terms = set()
        
        # Process each term
        for term in terms:
            term_lower = term.lower()
            if term_lower in processed_terms:
                continue
            
            # Find term in text (case-insensitive, whole word)
            pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
            
            # Check if term already has a footnote marker
            if pattern.search(result_text):
                # Add footnote
                marker = self.add_footnote(term)
                
                # Replace first occurrence with term + marker
                def replace_with_footnote(match):
                    return f"{match.group(0)}<sup>[{marker}]</sup>"
                
                result_text = pattern.sub(replace_with_footnote, result_text, count=1)
                processed_terms.add(term_lower)
        
        # Generate footnotes section
        footnotes_section = self.generate_footnotes_section()
        
        return result_text, footnotes_section
    
    def generate_footnotes_section(self, title: str = "## Footnotes") -> str:
        """Generate the footnotes section markdown."""
        if not self.footnotes:
            return ""
        
        lines = [title, ""]
        
        for footnote in self.footnotes:
            lines.append(f"[{footnote.marker}] **{footnote.term}**")
            
            # Add explanation if present
            if footnote.explanation:
                lines.append(f"   {footnote.explanation}")
            
            # Add vault link
            if footnote.vault_link:
                lines.append(f"   📚 Vault: {footnote.vault_link}")
            
            # Add academic links
            if footnote.academic_links:
                for source, url in sorted(footnote.academic_links.items()):
                    source_name = self.research_linker.LINK_TEMPLATES.get(
                        source, {}
                    ).get('display_name', source.replace('_', ' ').title())
                    lines.append(f"   🔗 [{source_name}]({url})")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear all footnotes."""
        self.footnotes = []
        self.term_to_footnote = {}
    
    def get_footnote(self, marker: int) -> Optional[Footnote]:
        """Get a footnote by marker number."""
        for footnote in self.footnotes:
            if footnote.marker == marker:
                return footnote
        return None
    
    def export_to_markdown(self, text: str, output_path: Path) -> None:
        """Export processed text with footnotes to a markdown file."""
        processed_text, footnotes_section = self.process_text(text, [])
        
        # Combine text and footnotes
        full_content = f"{processed_text}\n\n---\n\n{footnotes_section}"
        
        output_path.write_text(full_content, encoding='utf-8')

