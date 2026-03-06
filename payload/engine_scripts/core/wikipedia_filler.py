"""
Wikipedia Definition Auto-Filler for Theophysics Glossary
Scans vault for undefined terms, fetches from Wikipedia, creates definition files with [AW] marker.
"""

import re
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
import uuid
import os

try:
    from .definition_paths import primary_definition_dir
except ImportError:
    from definition_paths import primary_definition_dir


@dataclass
class TermInfo:
    """Information about a term found in the vault."""
    term: str
    occurrences: int
    files: List[str]
    has_definition: bool = False


@dataclass
class WikiDefinition:
    """Definition fetched from Wikipedia."""
    term: str
    title: str
    summary: str
    url: str
    fetched_at: str


class WikipediaFetcher:
    """Fetches definitions from Wikipedia API."""
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    def fetch(self, term: str) -> Optional[WikiDefinition]:
        """Fetch a definition from Wikipedia."""
        # Clean up term for search
        search_term = term.replace("_", " ").strip()
        encoded = urllib.parse.quote(search_term)
        
        try:
            url = f"{self.BASE_URL}{encoded}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'TheophysicsGlossaryBot/1.0 (david@theophysics.pro)'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('type') == 'standard':
                    return WikiDefinition(
                        term=term,
                        title=data.get('title', term),
                        summary=data.get('extract', ''),
                        url=data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        fetched_at=datetime.now().isoformat()
                    )
        except Exception as e:
            print(f"  [WARN] Wikipedia lookup failed for '{term}': {e}")
        
        return None


class GlossaryScanner:
    """Scans glossary folder for existing definitions."""
    
    def __init__(self, glossary_path: Path):
        self.glossary_path = glossary_path
        self.defined_terms: Set[str] = set()
        self.aliases: Dict[str, str] = {}  # alias -> main term
    
    def scan(self) -> Set[str]:
        """Scan glossary and return set of defined terms (including aliases)."""
        self.defined_terms = set()
        self.aliases = {}
        
        for md_file in self.glossary_path.glob("*.md"):
            # Add filename (without extension) as defined term
            term = md_file.stem
            self.defined_terms.add(term.lower())
            
            # Also check for aliases in frontmatter
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                if content.startswith('---'):
                    fm_end = content.find('---', 3)
                    if fm_end > 0:
                        frontmatter = content[3:fm_end]
                        # Extract aliases
                        alias_match = re.search(r'aliases:\s*\n((?:\s*-\s*[^\n]+\n?)+)', frontmatter)
                        if alias_match:
                            for alias in re.findall(r'-\s*([^\n]+)', alias_match.group(1)):
                                alias = alias.strip().strip('"').strip("'")
                                self.defined_terms.add(alias.lower())
                                self.aliases[alias.lower()] = term
            except Exception:
                pass
        
        return self.defined_terms


class VaultTermExtractor:
    """Extracts terms from vault that might need definitions."""
    
    # Greek letters commonly used in physics
    GREEK_LETTERS = {
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
        'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron',
        'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
        'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
        'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon',
        'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa',
        'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron',
        'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon',
        'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega'
    }
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.terms: Dict[str, TermInfo] = {}
    
    def extract_from_vault(self, skip_folders: Set[str] = None) -> Dict[str, TermInfo]:
        """Extract all potential terms from vault."""
        if skip_folders is None:
            skip_folders = {'.obsidian', '.trash', '.git', 'node_modules', '__pycache__'}
        
        self.terms = {}
        
        for md_file in self.vault_path.rglob("*.md"):
            # Skip certain folders
            if any(skip in md_file.parts for skip in skip_folders):
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
                self._extract_from_content(content, str(md_file))
            except Exception:
                pass
        
        return self.terms
    
    def _extract_from_content(self, content: str, file_path: str) -> None:
        """Extract terms from content."""
        # 1. Extract wiki-links: [[Term]] or [[Term|Display]]
        for match in re.finditer(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]', content):
            term = match.group(1).strip()
            # Skip if it's a glossary anchor or contains special chars
            if term.startswith('Theophysics_Glossary') or term.startswith('_'):
                continue
            self._add_term(term, file_path)
        
        # 2. Extract Greek letters - store English name only
        for greek, name in self.GREEK_LETTERS.items():
            if greek in content:
                self._add_term(name, file_path)  # Just the English name
        
        # 3. Extract #tags
        for match in re.finditer(r'#([a-zA-Z][a-zA-Z0-9_-]+)', content):
            tag = match.group(1)
            # Convert tag to potential term (e.g., quantum-mechanics -> Quantum Mechanics)
            term = tag.replace('-', ' ').replace('_', ' ').title()
            if len(term) > 3:  # Skip short tags
                self._add_term(term, file_path)
    
    def _add_term(self, term: str, file_path: str) -> None:
        """Add a term to the collection."""
        # Normalize
        term = term.strip()
        if not term or len(term) < 2:
            return
        
        # Skip file paths and URLs
        if '\\' in term or '/' in term or '.md' in term:
            return
        
        # Skip malformed links
        if term.startswith('[') or term.startswith('_'):
            return
        
        # Skip single generic words
        skip_words = {'master', 'general', 'abstract', 'dark', 'notes', 'paper', 'index', 'image', 'file'}
        if term.lower() in skip_words:
            return
        
        key = term.lower()
        if key not in self.terms:
            self.terms[key] = TermInfo(term=term, occurrences=0, files=[])
        
        self.terms[key].occurrences += 1
        if file_path not in self.terms[key].files:
            self.terms[key].files.append(file_path)


class DefinitionGenerator:
    """Generates definition files from Wikipedia data."""
    
    TEMPLATE = '''---
aliases: {aliases}
tags:
- glossary
- theophysics
- auto-wikipedia
uuid: {uuid}
title: {title}
author: Wikipedia (auto-fetched)
type: note
created: '{created}'
updated: '{updated}'
status: needs-review
source: wikipedia
source_url: {url}
fetched_at: '{fetched_at}'
---
# {title}

## 1. Aliases
<!-- Other names, symbols, abbreviations -->
{alias_list}

## 2. Core Definition
<!-- ONE SENTENCE. What the term IS. -->
[AW] {summary_first_sentence}

## 3. Operational Definition
<!-- How this term FUNCTIONS in Theophysics -->
[AW] {summary_rest}

## 4. Ontological Context
<!-- Triad position, domain, layer -->
<!-- TODO: Fill in manually -->

## 5. Relationships
<!-- Related terms, prerequisites, contrasts -->
| Relation | Term |
|----------|------|
| Parent | |
| Children | |
| See Also | |
| Contrasts | |

## 6. Scientific Definition
<!-- Standard physics/science definition -->
[AW] {full_summary}

---
> **Source:** [Wikipedia: {title}]({url})
> **Auto-fetched:** {fetched_at}
> **Status:** ⚠️ NEEDS REVIEW - Replace [AW] sections with your own words
'''
    
    def __init__(self, glossary_path: Path):
        self.glossary_path = glossary_path
    
    def generate(self, wiki_def: WikiDefinition, aliases: List[str] = None) -> Path:
        """Generate a definition file from Wikipedia data."""
        if aliases is None:
            aliases = []
        
        # Split summary into first sentence and rest
        summary = wiki_def.summary.strip()
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        first_sentence = sentences[0] if sentences else summary
        rest = ' '.join(sentences[1:]) if len(sentences) > 1 else ''
        
        # Generate safe filename
        safe_name = re.sub(r'[<>:"/\\|?*]', '', wiki_def.title)
        safe_name = safe_name.replace(' ', ' ')  # normalize spaces
        
        # Format aliases for YAML
        if aliases:
            alias_yaml = '\n' + '\n'.join(f'- {a}' for a in aliases)
            alias_list = '\n'.join(f'- {a}' for a in aliases)
        else:
            alias_yaml = ' []'
            alias_list = '<!-- None defined -->'
        
        now = datetime.now()
        
        content = self.TEMPLATE.format(
            aliases=alias_yaml,
            uuid=str(uuid.uuid4()),
            title=wiki_def.title,
            created=now.strftime('%Y-%m-%d'),
            updated=now.strftime('%Y-%m-%d'),
            url=wiki_def.url,
            fetched_at=wiki_def.fetched_at,
            alias_list=alias_list,
            summary_first_sentence=first_sentence,
            summary_rest=rest if rest else '<!-- Expand on operational usage -->',
            full_summary=summary
        )
        
        file_path = self.glossary_path / f"{safe_name}.md"
        file_path.write_text(content, encoding='utf-8')
        
        return file_path


class WikipediaAutoFiller:
    """Main class that orchestrates the auto-fill process."""
    
    def __init__(self, vault_path: str, glossary_path: str):
        self.vault_path = Path(vault_path)
        self.glossary_path = Path(glossary_path)
        
        self.scanner = GlossaryScanner(self.glossary_path)
        self.extractor = VaultTermExtractor(self.vault_path)
        self.fetcher = WikipediaFetcher()
        self.generator = DefinitionGenerator(self.glossary_path)
        
        self.missing_terms: List[TermInfo] = []
        self.filled_terms: List[str] = []
        self.failed_terms: List[str] = []
    
    def scan_for_missing(self, min_occurrences: int = 2) -> List[TermInfo]:
        """Scan vault and find terms without definitions."""
        print("[SCAN] Scanning glossary for existing definitions...")
        defined = self.scanner.scan()
        print(f"   Found {len(defined)} defined terms (including aliases)")
        
        print("\n[SCAN] Scanning vault for terms...")
        all_terms = self.extractor.extract_from_vault()
        print(f"   Found {len(all_terms)} unique terms")
        
        # Find missing (undefined) terms
        self.missing_terms = []
        for key, info in all_terms.items():
            if key not in defined and info.occurrences >= min_occurrences:
                self.missing_terms.append(info)
        
        # Sort by occurrences (most used first)
        self.missing_terms.sort(key=lambda x: x.occurrences, reverse=True)
        
        print(f"\n[MISSING] Found {len(self.missing_terms)} undefined terms (min {min_occurrences} occurrences)")
        
        return self.missing_terms
    
    def fill_from_wikipedia(self, terms: List[TermInfo] = None, max_terms: int = 50) -> Dict:
        """Fetch definitions from Wikipedia and create files."""
        if terms is None:
            terms = self.missing_terms[:max_terms]
        
        self.filled_terms = []
        self.failed_terms = []
        
        print(f"\n[WIKI] Fetching definitions from Wikipedia for {len(terms)} terms...")
        
        for i, term_info in enumerate(terms):
            print(f"\n[{i+1}/{len(terms)}] Looking up: {term_info.term}")
            
            # Try to fetch from Wikipedia
            wiki_def = self.fetcher.fetch(term_info.term)
            
            if wiki_def and wiki_def.summary:
                # Generate definition file
                file_path = self.generator.generate(wiki_def)
                self.filled_terms.append(term_info.term)
                print(f"   [OK] Created: {file_path.name}")
            else:
                self.failed_terms.append(term_info.term)
                print(f"   [FAIL] Not found on Wikipedia")
        
        return {
            'filled': self.filled_terms,
            'failed': self.failed_terms,
            'total_scanned': len(terms)
        }
    
    def generate_report(self) -> str:
        """Generate a report of the auto-fill operation."""
        report = f"""
# Wikipedia Auto-Fill Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Terms Scanned:** {len(self.missing_terms)}
- **Successfully Filled:** {len(self.filled_terms)}
- **Failed/Not Found:** {len(self.failed_terms)}

## Successfully Filled Terms
{chr(10).join(f'- [[{t}]]' for t in self.filled_terms) or 'None'}

## Failed Terms (Not Found on Wikipedia)
{chr(10).join(f'- {t}' for t in self.failed_terms) or 'None'}

## Top Missing Terms (by usage count)
{chr(10).join(f'- {t.term} ({t.occurrences} uses)' for t in self.missing_terms[:20]) or 'None'}

---
> All auto-filled definitions are marked with [AW] and need review.
> Look for files with `status: needs-review` in frontmatter.
"""
        return report


# CLI interface
if __name__ == "__main__":
    import sys
    
    # Fix Windows console encoding
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    
    default_vault = Path(__file__).resolve().parents[3]
    vault = os.environ.get("THEOPHYSICS_VAULT", str(default_vault))
    if not Path(vault).exists():
        vault = str(Path.cwd())
    glossary = str(primary_definition_dir(Path(vault), include_global_search=False, include_archive=False))
    
    filler = WikipediaAutoFiller(vault, glossary)
    
    # Step 1: Scan for missing terms
    missing = filler.scan_for_missing(min_occurrences=3)
    
    print("\n" + "="*60)
    print("TOP 30 MISSING TERMS:")
    print("="*60)
    for i, t in enumerate(missing[:30]):
        # Safe print - replace non-ASCII
        safe_term = t.term.encode('ascii', 'replace').decode('ascii')
        print(f"{i+1:3}. {safe_term:40} ({t.occurrences} uses)")
    
    # Ask before proceeding
    if len(sys.argv) > 1 and sys.argv[1] == "--fill":
        max_fill = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        result = filler.fill_from_wikipedia(max_terms=max_fill)
        
        print("\n" + "="*60)
        print("RESULTS:")
        print("="*60)
        print(f"[OK] Filled: {len(result['filled'])}")
        print(f"[FAIL] Failed: {len(result['failed'])}")
        
        # Save report
        report = filler.generate_report()
        report_path = Path(glossary) / "_WIKIPEDIA_AUTOFILL_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        print(f"\n[REPORT] Report saved to: {report_path}")
    else:
        print("\nTo auto-fill, run:")
        print("  python wikipedia_filler.py --fill [max_terms]")
        print("  Example: python wikipedia_filler.py --fill 20")
