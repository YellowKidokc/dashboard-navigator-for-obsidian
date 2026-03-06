"""
Lexicon Engine for Theophysics Vault
====================================
Handles:
1. Word Admission Gate (LAG) - scoring new term candidates
2. Wikipedia sync - pulling matching sections for definitions
3. Missing definition detection - finding terms that need definitions
4. Structure enforcement - ensuring definitions follow CORE/CANONICAL templates

Integrates with the two-tier lexicon system:
- CORE definitions (90%) - simple, human-readable
- CANONICAL definitions (10%) - research-grade, exhaustive
"""

import re
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import time


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class FormalAnchor:
    """Mathematical/symbolic anchor for a term."""
    exists: bool
    symbol: Optional[str] = None
    equation: Optional[str] = None


@dataclass
class WordCandidate:
    """A candidate word for admission to the lexicon."""
    term: str
    replaces: List[str] = field(default_factory=list)
    structural_role: str = ""  # operator | field | process | state | metric
    loss_if_missing: str = ""  # What's lost if we don't have this term (≤12 words)
    replaced_phrases: List[str] = field(default_factory=list)  # Phrases this compresses
    formal_anchor: FormalAnchor = field(default_factory=lambda: FormalAnchor(False))
    semantic_overlap: int = 0  # 0-100 percent overlap with closest existing term
    closest_existing_term: str = ""


@dataclass
class GateResult:
    """Result of the Lexical Admission Gate evaluation."""
    necessity: int  # 0 or 1
    compression: int  # 0 or 1
    formal_anchor: int  # 0 or 1
    drift: int  # 0 or 1
    drift_class: str  # Extension | Constrained Neologism | Soft Neologism | Reject
    total: int  # 0-4
    status: str  # ADMITTED | PROVISIONAL | FAIL
    
    @property
    def passed(self) -> bool:
        return self.status in ("ADMITTED", "PROVISIONAL")


@dataclass
class WikipediaSection:
    """A section from Wikipedia."""
    title: str
    content: str
    level: int  # heading level (1, 2, 3, etc.)


@dataclass
class DefinitionAnalysis:
    """Analysis of an existing definition file."""
    path: Path
    term: str
    has_frontmatter: bool
    has_what_it_is: bool
    has_why_it_matters: bool
    has_analogy: bool
    has_plain_english: bool
    has_key_insight: bool
    has_scripture: bool
    has_wikipedia_section: bool
    is_canonical: bool
    completeness_score: float  # 0-1
    missing_sections: List[str]


# ============================================
# LEXICAL ADMISSION GATE (LAG)
# ============================================

class LexicalAdmissionGate:
    """
    Evaluates word candidates for admission to the lexicon.
    
    Four gates:
    - G1: Necessity - Is there information loss without this term?
    - G2: Compression - Does this replace ≥2 repeated explanations?
    - G3: Formal Anchor - Is there a symbol/operator/equation?
    - G4: Drift - Is semantic overlap in acceptable range?
    """
    
    def evaluate(self, word: WordCandidate) -> GateResult:
        """Evaluate a word candidate through all four gates."""
        
        # G1 — Necessity
        g1 = 1 if (word.loss_if_missing and 
                   len(word.loss_if_missing.split()) <= 12 and
                   len(word.loss_if_missing.strip()) > 0) else 0
        
        # G2 — Compression
        g2 = 1 if len(word.replaced_phrases) >= 2 else 0
        
        # G3 — Formal Anchor
        g3 = 1 if word.formal_anchor.exists else 0
        
        # G4 — Drift
        overlap = word.semantic_overlap
        if overlap >= 90:
            g4 = 1
            drift_class = "Extension"
        elif overlap >= 70:
            g4 = 1
            drift_class = "Constrained Neologism"
        elif overlap >= 50:
            g4 = 0
            drift_class = "Soft Neologism"
        else:
            g4 = 0
            drift_class = "Reject"
        
        total = g1 + g2 + g3 + g4
        
        if total == 4:
            status = "ADMITTED"
        elif total == 3:
            status = "PROVISIONAL"
        else:
            status = "FAIL"
        
        return GateResult(
            necessity=g1,
            compression=g2,
            formal_anchor=g3,
            drift=g4,
            drift_class=drift_class,
            total=total,
            status=status
        )
    
    def render_template(self, word: WordCandidate, result: GateResult) -> str:
        """Render the admission result as a markdown template."""
        
        replaced_list = "\n".join(f"  → {p}" for p in word.replaced_phrases) if word.replaced_phrases else "  → (none)"
        
        return f"""### WORD CANDIDATE: {word.term}

**Replaces / Reframes:** {", ".join(word.replaces) if word.replaces else "(none)"}
**Structural Role:** {word.structural_role or "unspecified"}

---

#### Gate Tests

**G1 — Necessity**
- Can existing terms express this *without loss*?
  {"☑ NO" if result.necessity else "☐ YES"} {"☐ NO" if result.necessity else "☑ YES"}
- Loss in ≤12 words:
  → {word.loss_if_missing or "(not specified)"}

**G2 — Compression**
- Does this term replace ≥2 repeated explanations?
  {"☑ YES" if result.compression else "☐ YES"} {"☐ NO" if result.compression else "☑ NO"}
- Replaced phrases:
{replaced_list}

**G3 — Formal Anchor**
- Is there a formal object attached? (symbol / operator / equation)
  {"☑ YES" if result.formal_anchor else "☐ YES"} {"☐ NO" if result.formal_anchor else "☑ NO"}
- Symbol/Equation: {word.formal_anchor.symbol or word.formal_anchor.equation or "(none)"}

**G4 — Drift Risk**
- Semantic overlap with closest existing term ({word.closest_existing_term or "?"}): **{word.semantic_overlap}%**
- Drift class: **{result.drift_class}**

---

#### Verdict

| Gate | Score |
|------|-------|
| Necessity | {result.necessity}/1 |
| Compression | {result.compression}/1 |
| Formal Anchor | {result.formal_anchor}/1 |
| Drift Acceptable | {result.drift}/1 |

**TOTAL:** {result.total} / 4

**STATUS:** {"☑" if result.status == "FAIL" else "☐"} FAIL (≤2) | {"☑" if result.status == "PROVISIONAL" else "☐"} PROVISIONAL (3) | {"☑" if result.status == "ADMITTED" else "☐"} ADMITTED (4)

**Next Step:**
- {"☑" if result.status == "FAIL" else "☐"} No action
- {"☑" if result.status == "PROVISIONAL" else "☐"} Review and refine
- {"☑" if result.status == "ADMITTED" else "☐"} Create CORE Lexicon entry
"""


# ============================================
# WIKIPEDIA SYNC
# ============================================

class WikipediaSync:
    """
    Syncs Wikipedia content to lexicon definitions.
    
    Pulls matching sections from Wikipedia and formats them
    for inclusion in definition files.
    """
    
    WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    WIKIPEDIA_SECTIONS_API = "https://en.wikipedia.org/w/api.php"
    
    # Map our sections to Wikipedia sections
    SECTION_MAPPING = {
        "definition": ["Definition", "Overview", "Description"],
        "physics": ["Physics", "Physical", "Mechanics", "Quantum"],
        "information": ["Information", "Information theory", "Computation"],
        "neuroscience": ["Neuroscience", "Brain", "Neural", "Cognitive"],
        "psychology": ["Psychology", "Psychological", "Mental"],
        "philosophy": ["Philosophy", "Philosophical", "Metaphysics", "Epistemology"],
        "theology": ["Theology", "Religious", "Spiritual", "Biblical"],
        "history": ["History", "Historical", "Origins", "Etymology"],
        "applications": ["Applications", "Uses", "Examples"],
        "see_also": ["See also", "Related"],
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TheophysicsLexicon/1.0 (Educational research project)'
        })
    
    def get_summary(self, term: str) -> Optional[Dict]:
        """Get Wikipedia summary for a term."""
        try:
            # Clean term for URL
            clean_term = term.replace(" ", "_")
            url = f"{self.WIKIPEDIA_API}{clean_term}"
            
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Wikipedia summary error for {term}: {e}")
            return None
    
    def get_sections(self, term: str) -> List[WikipediaSection]:
        """Get all sections from a Wikipedia article."""
        try:
            clean_term = term.replace(" ", "_")
            
            # First get the page content
            params = {
                'action': 'parse',
                'page': clean_term,
                'prop': 'sections|wikitext',
                'format': 'json'
            }
            
            response = self.session.get(self.WIKIPEDIA_SECTIONS_API, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            data = response.json()
            if 'error' in data:
                return []
            
            sections = []
            parse_data = data.get('parse', {})
            
            for section in parse_data.get('sections', []):
                sections.append(WikipediaSection(
                    title=section.get('line', ''),
                    content="",  # Would need another API call to get content
                    level=int(section.get('level', 2))
                ))
            
            return sections
            
        except Exception as e:
            print(f"Wikipedia sections error for {term}: {e}")
            return []
    
    def get_section_content(self, term: str, section_title: str) -> Optional[str]:
        """Get content of a specific Wikipedia section."""
        try:
            clean_term = term.replace(" ", "_")
            
            params = {
                'action': 'parse',
                'page': clean_term,
                'section': section_title,
                'prop': 'text',
                'format': 'json',
                'disabletoc': True
            }
            
            # First need to find section index
            sections = self.get_sections(term)
            section_index = None
            for i, s in enumerate(sections):
                if s.title.lower() == section_title.lower():
                    section_index = i + 1  # Wikipedia sections are 1-indexed
                    break
            
            if section_index is None:
                return None
            
            params['section'] = section_index
            
            response = self.session.get(self.WIKIPEDIA_SECTIONS_API, params=params, timeout=15)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if 'error' in data:
                return None
            
            # Extract text and clean HTML
            html_content = data.get('parse', {}).get('text', {}).get('*', '')
            
            # Basic HTML to text conversion
            import html
            text = re.sub(r'<[^>]+>', '', html_content)
            text = html.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:2000] if text else None  # Limit length
            
        except Exception as e:
            print(f"Wikipedia section content error: {e}")
            return None
    
    def find_matching_sections(self, term: str, our_sections: List[str]) -> Dict[str, str]:
        """
        Find Wikipedia sections that match our definition sections.
        
        Returns dict mapping our section name -> Wikipedia content
        """
        matches = {}
        
        wiki_sections = self.get_sections(term)
        wiki_section_titles = [s.title.lower() for s in wiki_sections]
        
        for our_section in our_sections:
            # Get possible Wikipedia section names for this
            possible_names = self.SECTION_MAPPING.get(our_section.lower(), [our_section])
            
            for wiki_name in possible_names:
                if wiki_name.lower() in wiki_section_titles:
                    content = self.get_section_content(term, wiki_name)
                    if content:
                        matches[our_section] = content
                        break
        
        return matches
    
    def generate_wikipedia_block(self, term: str) -> Optional[str]:
        """Generate a Wikipedia reference block for a definition."""
        summary = self.get_summary(term)
        if not summary:
            return None
        
        extract = summary.get('extract', '')
        url = summary.get('content_urls', {}).get('desktop', {}).get('page', '')
        
        if not extract:
            return None
        
        # Truncate if too long
        if len(extract) > 500:
            extract = extract[:500] + "..."
        
        return f"""## External Reference (Wikipedia)

> {extract}

---
**Source:** [{term} - Wikipedia]({url})
**Trust Level:** 2 (Human-Verified External)
**⚠️ WARNING:** This content is from Wikipedia, NOT Theophysics. Use for comparison only. Does not override Theophysics definitions.
"""
    
    def generate_blank_definition_template(self, term: str, source: str = "theophysics") -> str:
        """
        Generate a blank definition template with source clearly marked.
        
        Args:
            term: The term to define
            source: 'theophysics' (Trust Level 1), 'wikipedia' (Trust Level 2), or 'auto' (Trust Level 3)
        """
        trust_levels = {
            "theophysics": ("1", "Theophysics Original", "THE authority. Your definition."),
            "wikipedia": ("2", "Human-Verified External", "Comparison only. Does not override Theophysics."),
            "auto": ("3", "Auto-Generated", "Reference material. Verify before trusting.")
        }
        
        level, level_name, level_desc = trust_levels.get(source, trust_levels["theophysics"])
        
        now = datetime.now().isoformat()
        
        return f"""---
type: definition
status: draft
trust_level: {level}
source: {source}
created: {now}
---

# {term}

> **Trust Level {level}:** {level_name} — {level_desc}

## What It Is

<!-- ONE clear sentence. What a smart 16-year-old would understand. -->

## Why It Matters

<!-- What problem does this solve? Why should anyone care? -->

## The Analogy

*Imagine...*

<!-- A concrete, memorable comparison to everyday life. -->

## In Plain English

<!-- 2-3 paragraphs max. Walk through the concept like explaining to a friend. -->

## The Key Insight

> <!-- The one sentence you'd want someone to remember a year from now. -->

## Quick Links

- **Related:** <!-- [[Term 1]], [[Term 2]] -->
- **Used in:** <!-- Paper X -->

## Scripture Connection (Optional)

> <!-- "Verse text" — Book Chapter:Verse -->

<!-- One sentence on how this connects. -->

---

**Source:** {source.upper()}
**Trust Level:** {level} ({level_name})
"""


# ============================================
# DEFINITION ANALYZER
# ============================================

class DefinitionAnalyzer:
    """
    Analyzes existing definitions for completeness and structure.
    Identifies missing definitions and incomplete entries.
    """
    
    # Required sections for CORE definitions
    CORE_SECTIONS = [
        "What It Is",
        "Why It Matters", 
        "The Analogy",
        "In Plain English",
        "The Key Insight"
    ]
    
    # Additional sections for CANONICAL definitions
    CANONICAL_SECTIONS = [
        "Canonical Statement",
        "Axioms Required",
        "Mathematical Form",
        "Seven-Domain Mapping",
        "Trinity Connection",
        "Master Equation Position",
        "Failure Modes",
        "Worked Examples",
        "Relationships",
        "Scriptures",
        "External Comparison"
    ]
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.lexicon_path = self.vault_path / "02_LIBRARY" / "4_LEXICON"
    
    def analyze_definition(self, file_path: Path) -> DefinitionAnalysis:
        """Analyze a single definition file for completeness."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except:
            return DefinitionAnalysis(
                path=file_path,
                term=file_path.stem,
                has_frontmatter=False,
                has_what_it_is=False,
                has_why_it_matters=False,
                has_analogy=False,
                has_plain_english=False,
                has_key_insight=False,
                has_scripture=False,
                has_wikipedia_section=False,
                is_canonical="_Canonical" in file_path.name,
                completeness_score=0.0,
                missing_sections=self.CORE_SECTIONS.copy()
            )
        
        content_lower = content.lower()
        
        # Check for frontmatter
        has_frontmatter = content.startswith('---') and '---' in content[3:]
        
        # Check for sections
        has_what_it_is = "what it is" in content_lower or "## definition" in content_lower
        has_why_it_matters = "why it matters" in content_lower
        has_analogy = "analogy" in content_lower or "imagine" in content_lower
        has_plain_english = "plain english" in content_lower or "in simple terms" in content_lower
        has_key_insight = "key insight" in content_lower or "the insight" in content_lower
        has_scripture = "scripture" in content_lower or "biblical" in content_lower or re.search(r'\d+:\d+', content)
        has_wikipedia = "wikipedia" in content_lower or "trust level: 2" in content_lower
        
        is_canonical = "_Canonical" in file_path.name or "canonical" in content_lower[:500]
        
        # Calculate completeness
        checks = [has_what_it_is, has_why_it_matters, has_analogy, has_plain_english, has_key_insight]
        completeness = sum(checks) / len(checks)
        
        # Find missing sections
        missing = []
        if not has_what_it_is:
            missing.append("What It Is")
        if not has_why_it_matters:
            missing.append("Why It Matters")
        if not has_analogy:
            missing.append("The Analogy")
        if not has_plain_english:
            missing.append("In Plain English")
        if not has_key_insight:
            missing.append("The Key Insight")
        
        return DefinitionAnalysis(
            path=file_path,
            term=file_path.stem,
            has_frontmatter=has_frontmatter,
            has_what_it_is=has_what_it_is,
            has_why_it_matters=has_why_it_matters,
            has_analogy=has_analogy,
            has_plain_english=has_plain_english,
            has_key_insight=has_key_insight,
            has_scripture=has_scripture,
            has_wikipedia_section=has_wikipedia,
            is_canonical=is_canonical,
            completeness_score=completeness,
            missing_sections=missing
        )
    
    def scan_all_definitions(self) -> List[DefinitionAnalysis]:
        """Scan all definitions in the lexicon."""
        results = []
        
        if not self.lexicon_path.exists():
            return results
        
        for md_file in self.lexicon_path.glob("*.md"):
            # Skip template and system files
            if md_file.name.startswith("_"):
                continue
            
            analysis = self.analyze_definition(md_file)
            results.append(analysis)
        
        return results
    
    def find_incomplete_definitions(self, min_completeness: float = 0.6) -> List[DefinitionAnalysis]:
        """Find definitions below the completeness threshold."""
        all_defs = self.scan_all_definitions()
        return [d for d in all_defs if d.completeness_score < min_completeness]
    
    def find_missing_wikipedia(self) -> List[DefinitionAnalysis]:
        """Find definitions without Wikipedia reference sections."""
        all_defs = self.scan_all_definitions()
        return [d for d in all_defs if not d.has_wikipedia_section]


# ============================================
# MISSING TERM DETECTOR
# ============================================

class MissingTermDetector:
    """
    Scans the vault to find terms that are frequently linked
    but don't have definitions in the lexicon.
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.lexicon_path = self.vault_path / "02_LIBRARY" / "4_LEXICON"
        self.existing_terms: Set[str] = set()
        self._load_existing_terms()
    
    def _load_existing_terms(self):
        """Load all existing term names from lexicon."""
        if not self.lexicon_path.exists():
            return
        
        for md_file in self.lexicon_path.glob("*.md"):
            if not md_file.name.startswith("_"):
                term = md_file.stem.lower()
                self.existing_terms.add(term)
                
                # Also load aliases
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
                                self.existing_terms.add(alias.lower())
                except:
                    pass
    
    def scan_vault_for_linked_terms(self) -> Dict[str, int]:
        """
        Scan vault for all wikilinked terms and count occurrences.
        
        Returns dict mapping term -> link count
        """
        term_counts = defaultdict(int)
        
        for md_file in self.vault_path.rglob("*.md"):
            # Skip system folders
            if any(skip in str(md_file) for skip in [".obsidian", "node_modules", ".git"]):
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Find all wikilinks
                links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
                
                for link in links:
                    term = link.strip().lower()
                    term_counts[term] += 1
                    
            except:
                continue
        
        return dict(term_counts)
    
    def find_missing_definitions(self, min_links: int = 3) -> List[Tuple[str, int]]:
        """
        Find terms that are linked frequently but have no definition.
        
        Args:
            min_links: Minimum number of links to consider a term "missing"
            
        Returns:
            List of (term, link_count) tuples, sorted by count descending
        """
        term_counts = self.scan_vault_for_linked_terms()
        
        missing = []
        for term, count in term_counts.items():
            if count >= min_links and term not in self.existing_terms:
                # Skip obvious non-terms
                if len(term) < 2:
                    continue
                if term.startswith("http"):
                    continue
                if "/" in term and not term.startswith("02_"):
                    continue
                    
                missing.append((term, count))
        
        # Sort by count descending
        missing.sort(key=lambda x: -x[1])
        
        return missing
    
    def generate_missing_report(self, min_links: int = 3) -> str:
        """Generate a markdown report of missing definitions."""
        missing = self.find_missing_definitions(min_links)
        
        lines = [
            "# Missing Definitions Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            f"Terms linked **{min_links}+ times** without a definition in the lexicon.",
            "",
            f"**Total missing:** {len(missing)}",
            "",
            "---",
            "",
            "| Term | Link Count | Action |",
            "|------|------------|--------|",
        ]
        
        for term, count in missing[:100]:  # Top 100
            lines.append(f"| {term} | {count} | ☐ Create |")
        
        if len(missing) > 100:
            lines.append(f"\n*...and {len(missing) - 100} more*")
        
        return "\n".join(lines)


# ============================================
# MAIN LEXICON ENGINE
# ============================================

class LexiconEngine:
    """
    Main engine coordinating all lexicon operations.
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.lexicon_path = self.vault_path / "02_LIBRARY" / "4_LEXICON"
        
        self.admission_gate = LexicalAdmissionGate()
        self.wikipedia_sync = WikipediaSync()
        self.definition_analyzer = DefinitionAnalyzer(vault_path)
        self.missing_detector = MissingTermDetector(vault_path)
    
    def evaluate_word(self, word: WordCandidate) -> Tuple[GateResult, str]:
        """Evaluate a word candidate and return result + template."""
        result = self.admission_gate.evaluate(word)
        template = self.admission_gate.render_template(word, result)
        return result, template
    
    def add_wikipedia_to_definition(self, term: str) -> Optional[str]:
        """Generate Wikipedia block for a term."""
        return self.wikipedia_sync.generate_wikipedia_block(term)
    
    def create_definition_file(self, term: str, source: str = "theophysics", 
                                include_wikipedia: bool = False) -> Path:
        """
        Create a new definition file with proper source/trust level marking.
        
        Args:
            term: The term to define
            source: 'theophysics' (Trust Level 1), 'wikipedia' (Trust Level 2), or 'auto' (Trust Level 3)
            include_wikipedia: Whether to include Wikipedia reference section
            
        Returns:
            Path to the created file
        """
        # Generate template
        content = self.wikipedia_sync.generate_blank_definition_template(term, source)
        
        # Optionally add Wikipedia reference
        if include_wikipedia:
            wiki_block = self.wikipedia_sync.generate_wikipedia_block(term)
            if wiki_block:
                content += "\n" + wiki_block
        
        # Create file
        safe_name = term.replace("/", "-").replace("\\", "-").replace(":", "-")
        file_path = self.lexicon_path / f"{safe_name}.md"
        
        # Don't overwrite existing
        if file_path.exists():
            raise FileExistsError(f"Definition already exists: {file_path}")
        
        file_path.write_text(content, encoding='utf-8')
        return file_path
    
    def get_incomplete_definitions(self) -> List[DefinitionAnalysis]:
        """Get list of incomplete definitions."""
        return self.definition_analyzer.find_incomplete_definitions()
    
    def get_missing_definitions(self, min_links: int = 3) -> List[Tuple[str, int]]:
        """Get list of terms that need definitions."""
        return self.missing_detector.find_missing_definitions(min_links)
    
    def generate_full_report(self) -> str:
        """Generate comprehensive lexicon health report."""
        incomplete = self.get_incomplete_definitions()
        missing = self.get_missing_definitions()
        no_wiki = self.definition_analyzer.find_missing_wikipedia()
        
        lines = [
            "# Lexicon Health Report",
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"- **Incomplete definitions:** {len(incomplete)}",
            f"- **Missing definitions (linked 3+ times):** {len(missing)}",
            f"- **Definitions without Wikipedia:** {len(no_wiki)}",
            "",
            "---",
            "",
            "## Incomplete Definitions",
            "",
            "| Term | Completeness | Missing Sections |",
            "|------|--------------|------------------|",
        ]
        
        for d in sorted(incomplete, key=lambda x: x.completeness_score)[:20]:
            missing_str = ", ".join(d.missing_sections[:3])
            if len(d.missing_sections) > 3:
                missing_str += f" (+{len(d.missing_sections) - 3})"
            lines.append(f"| [[{d.term}]] | {d.completeness_score:.0%} | {missing_str} |")
        
        lines.extend([
            "",
            "---",
            "",
            "## Top Missing Definitions",
            "",
            "| Term | Links | Priority |",
            "|------|-------|----------|",
        ])
        
        for term, count in missing[:20]:
            priority = "HIGH" if count >= 10 else "MEDIUM" if count >= 5 else "LOW"
            lines.append(f"| {term} | {count} | {priority} |")
        
        lines.extend([
            "",
            "---",
            "",
            "## Definitions Needing Wikipedia",
            "",
        ])
        
        for d in no_wiki[:20]:
            lines.append(f"- [[{d.term}]]")
        
        return "\n".join(lines)


# ============================================
# CLI
# ============================================

if __name__ == "__main__":
    vault_path = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    
    print("=" * 60)
    print("LEXICON ENGINE")
    print("=" * 60)
    
    engine = LexiconEngine(vault_path)
    
    # Test word admission
    print("\n--- Testing Word Admission Gate ---")
    test_word = WordCandidate(
        term="Trinity Actualization",
        replaces=["Wave Function Collapse"],
        structural_role="process",
        loss_if_missing="agency and teleology",
        replaced_phrases=[
            "non-unitary conscious collapse",
            "participatory actualization"
        ],
        formal_anchor=FormalAnchor(True, "χ, Observer Operator"),
        semantic_overlap=80,
        closest_existing_term="Wave Function Collapse"
    )
    
    result, template = engine.evaluate_word(test_word)
    print(f"Status: {result.status} ({result.total}/4)")
    
    # Test Wikipedia sync
    print("\n--- Testing Wikipedia Sync ---")
    wiki_block = engine.add_wikipedia_to_definition("Entropy")
    if wiki_block:
        print("Wikipedia block generated successfully")
        print(wiki_block[:200] + "...")
    
    # Find missing definitions
    print("\n--- Finding Missing Definitions ---")
    missing = engine.get_missing_definitions(min_links=5)
    print(f"Found {len(missing)} terms linked 5+ times without definitions")
    for term, count in missing[:10]:
        print(f"  {term}: {count} links")
    
    # Find incomplete definitions
    print("\n--- Finding Incomplete Definitions ---")
    incomplete = engine.get_incomplete_definitions()
    print(f"Found {len(incomplete)} incomplete definitions")
    for d in incomplete[:5]:
        print(f"  {d.term}: {d.completeness_score:.0%} complete")
    
    # Generate report
    print("\n--- Generating Full Report ---")
    report = engine.generate_full_report()
    report_path = Path(vault_path) / "_TAG_NOTES" / "_LEXICON_HEALTH_REPORT.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"Report saved to: {report_path}")
