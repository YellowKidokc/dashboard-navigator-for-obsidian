"""
Claim Extractor — Parses markdown documents into structured claims.

Extracts:
  - Assertions (statements of fact or theory)
  - Definitions (term = meaning)
  - Equations (LaTeX blocks with context)
  - Axiom content (from YAML frontmatter + body)
  - Section structure (headers → content blocks)

This is the INPUT side of the contradiction detector.
Documents go in → structured claims come out → detector compares them.
"""

from __future__ import annotations

import re
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@dataclass
class DocumentClaims:
    """All extracted claims from a single document."""
    file_path: str
    file_name: str
    axiom_id: str = ""
    chain_position: int = 0
    depends_on: list = field(default_factory=list)
    stage: int = 0
    
    # Extracted content
    assertions: list = field(default_factory=list)      # plain-language claims
    definitions: list = field(default_factory=list)      # term definitions
    equations: list = field(default_factory=list)         # LaTeX blocks
    sections: dict = field(default_factory=dict)          # header → content
    yaml_metadata: dict = field(default_factory=dict)     # full frontmatter
    
    @property
    def total_claims(self) -> int:
        return len(self.assertions) + len(self.definitions) + len(self.equations)
    
    @property 
    def is_axiom(self) -> bool:
        return bool(self.axiom_id)


@dataclass
class Assertion:
    """A factual or theoretical claim."""
    text: str
    section: str = ""
    line_number: int = 0
    claim_type: str = "assertion"   # assertion, theorem, corollary, conjecture
    confidence: str = "stated"       # stated, implied, hedged


@dataclass
class Definition:
    """A term being defined."""
    term: str
    definition: str
    section: str = ""
    line_number: int = 0
    is_custom: bool = False         # True if Theophysics-specific meaning


@dataclass
class Equation:
    """A LaTeX equation with context."""
    latex: str
    display_type: str = "display"   # display ($$) or inline ($)
    section: str = ""
    line_number: int = 0
    context_before: str = ""
    context_after: str = ""
    variables: list = field(default_factory=list)


class ClaimExtractor:
    """
    Extracts structured claims from markdown documents.
    
    Rule-based extraction (no AI required):
      - YAML frontmatter parsing
      - Section header detection
      - Equation extraction (LaTeX)
      - Definition pattern matching
      - Assertion detection (sentences with strong verbs)
    
    AI-enhanced extraction (requires Ollama/OpenAI):
      - Nuanced claim extraction
      - Implicit assertion detection
      - Variable meaning inference
    """
    
    # Patterns that indicate a definition
    DEFINITION_PATTERNS = [
        r'(?:is defined as|we define|let .+ (?:be|denote|represent))',
        r'(?:refers to|means that|signifies)',
        r'(?:Definition[:.])',
        r'(?:≡|:=|def=)',
    ]
    
    # Patterns that indicate a strong assertion  
    ASSERTION_PATTERNS = [
        r'(?:therefore|thus|hence|consequently|it follows that)',
        r'(?:we (?:prove|show|demonstrate|establish) that)',
        r'(?:this (?:proves|shows|demonstrates|implies|means) that)',
        r'(?:necessarily|must be|cannot be|always|never)',
        r'(?:is (?:identical|equivalent|equal) to)',
        r'(?:if and only if|iff)',
        r'(?:contradicts|violates|is incompatible with)',
        r'(?:requires|entails|presupposes|depends on)',
    ]
    
    # Common Theophysics variables
    KNOWN_VARIABLES = {
        'χ': 'coherence (master variable)',
        'Ψ': 'consciousness / wavefunction',
        'Φ': 'physical reality / integrated information',
        'Λ': 'Logos field',
        'S': 'entropy',
        'G': 'grace / negentropy source',
        'M': 'mutual information',
        'E': 'entropy / energy',
        'T': 'time / temperature',
        'K': 'Kolmogorov complexity',
        'R': 'relationality',
        'Q': 'quantum state',
        'F': 'force / faith',
        'C': 'coherence / Christ alignment',
        'δ': 'drift',
        'α': 'decay coefficient',
        'β': 'grace coefficient',
    }
    
    def __init__(self):
        self._compiled_def_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DEFINITION_PATTERNS
        ]
        self._compiled_assert_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.ASSERTION_PATTERNS
        ]
    
    def extract_from_file(self, file_path: str) -> DocumentClaims:
        """Extract all claims from a single markdown file."""
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            return DocumentClaims(file_path=str(path), file_name=path.name)
        
        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding='latin-1')
            except:
                return DocumentClaims(file_path=str(path), file_name=path.name)
        
        doc = DocumentClaims(file_path=str(path), file_name=path.name)
        
        # Parse YAML frontmatter
        doc.yaml_metadata = self._extract_yaml(content)
        doc.axiom_id = doc.yaml_metadata.get('axiom_id', '')
        doc.chain_position = doc.yaml_metadata.get('chain_position', 0)
        doc.depends_on = doc.yaml_metadata.get('depends_on', []) or []
        doc.stage = doc.yaml_metadata.get('stage', 0)
        
        # Strip frontmatter for body parsing
        body = self._strip_yaml(content)
        
        # Parse sections
        doc.sections = self._extract_sections(body)
        
        # Extract equations
        doc.equations = self._extract_equations(body)
        
        # Extract definitions
        doc.definitions = self._extract_definitions(body)
        
        # Extract assertions
        doc.assertions = self._extract_assertions(body)
        
        return doc
    
    def extract_from_folder(self, folder_path: str, 
                             pattern: str = "*.md") -> List[DocumentClaims]:
        """Extract claims from all matching files in a folder."""
        folder = Path(folder_path)
        if not folder.exists():
            return []
        
        results = []
        for md_file in sorted(folder.glob(pattern)):
            if md_file.is_file():
                doc = self.extract_from_file(str(md_file))
                if doc.total_claims > 0:
                    results.append(doc)
        
        return results
    
    # =========================================================================
    # YAML
    # =========================================================================
    
    def _extract_yaml(self, content: str) -> dict:
        """Extract YAML frontmatter."""
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}
    
    def _strip_yaml(self, content: str) -> str:
        """Remove YAML frontmatter from content."""
        return re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, count=1, flags=re.DOTALL)
    
    # =========================================================================
    # SECTIONS
    # =========================================================================
    
    def _extract_sections(self, body: str) -> Dict[str, str]:
        """Parse markdown headers into sections."""
        sections = {}
        current_header = "_preamble"
        current_content = []
        
        for line in body.split('\n'):
            header_match = re.match(r'^(#{1,6})\s+(.+)', line)
            if header_match:
                # Save previous section
                if current_content:
                    sections[current_header] = '\n'.join(current_content).strip()
                current_header = header_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_header] = '\n'.join(current_content).strip()
        
        return sections
    
    # =========================================================================
    # EQUATIONS
    # =========================================================================
    
    def _extract_equations(self, body: str) -> List[Equation]:
        """Extract all LaTeX equations with context."""
        equations = []
        lines = body.split('\n')
        
        # Display equations: $$ ... $$
        display_pattern = re.compile(r'\$\$(.+?)\$\$', re.DOTALL)
        for match in display_pattern.finditer(body):
            latex = match.group(1).strip()
            if len(latex) < 3:  # skip trivial
                continue
            
            # Get line number
            line_num = body[:match.start()].count('\n') + 1
            
            # Get context
            ctx_before, ctx_after = self._get_context(body, match.start(), match.end())
            
            # Detect variables
            variables = self._detect_variables(latex)
            
            # Detect current section
            section = self._get_section_at_position(lines, line_num)
            
            equations.append(Equation(
                latex=latex,
                display_type="display",
                section=section,
                line_number=line_num,
                context_before=ctx_before,
                context_after=ctx_after,
                variables=variables
            ))
        
        # Inline equations: $ ... $ (skip if inside display block)
        inline_pattern = re.compile(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)')
        for match in inline_pattern.finditer(body):
            latex = match.group(1).strip()
            if len(latex) < 3:
                continue
            
            line_num = body[:match.start()].count('\n') + 1
            section = self._get_section_at_position(lines, line_num)
            variables = self._detect_variables(latex)
            
            equations.append(Equation(
                latex=latex,
                display_type="inline",
                section=section,
                line_number=line_num,
                variables=variables
            ))
        
        return equations
    
    def _detect_variables(self, latex: str) -> List[str]:
        """Find known Theophysics variables in a LaTeX string."""
        found = []
        for var in self.KNOWN_VARIABLES:
            if var in latex:
                found.append(var)
        return found
    
    def _get_context(self, body: str, start: int, end: int, 
                     chars: int = 300) -> Tuple[str, str]:
        """Get text context around a position."""
        before_start = max(0, start - chars)
        after_end = min(len(body), end + chars)
        
        ctx_before = body[before_start:start].strip()
        ctx_after = body[end:after_end].strip()
        
        # Clean to paragraph boundaries
        if '\n\n' in ctx_before:
            ctx_before = ctx_before.split('\n\n')[-1]
        if '\n\n' in ctx_after:
            ctx_after = ctx_after.split('\n\n')[0]
        
        return ctx_before, ctx_after
    
    def _get_section_at_position(self, lines: List[str], line_num: int) -> str:
        """Find which section header a line falls under."""
        current_section = "_preamble"
        for i, line in enumerate(lines):
            if i + 1 > line_num:
                break
            header_match = re.match(r'^#{1,6}\s+(.+)', line)
            if header_match:
                current_section = header_match.group(1).strip()
        return current_section
    
    # =========================================================================
    # DEFINITIONS
    # =========================================================================
    
    def _extract_definitions(self, body: str) -> List[Definition]:
        """Extract term definitions from document."""
        definitions = []
        lines = body.split('\n')
        current_section = "_preamble"
        
        for i, line in enumerate(lines):
            # Track sections
            header_match = re.match(r'^#{1,6}\s+(.+)', line)
            if header_match:
                current_section = header_match.group(1).strip()
                continue
            
            # Check definition patterns
            for pattern in self._compiled_def_patterns:
                match = pattern.search(line)
                if match:
                    # Try to extract term + definition
                    term, defn = self._parse_definition_line(line)
                    if term:
                        definitions.append(Definition(
                            term=term,
                            definition=defn,
                            section=current_section,
                            line_number=i + 1,
                            is_custom=self._is_custom_term(term)
                        ))
                    break
        
        return definitions
    
    def _parse_definition_line(self, line: str) -> Tuple[str, str]:
        """Try to extract (term, definition) from a definition line."""
        # Pattern: "X is defined as Y"
        match = re.match(r'(?:\*\*)?(.+?)(?:\*\*)?\s+(?:is defined as|we define .+ as)\s+(.+)', 
                         line, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Pattern: "Let X be/denote Y"
        match = re.match(r'[Ll]et\s+(.+?)\s+(?:be|denote|represent)\s+(.+)', line)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        
        # Pattern: "Definition: X = Y" or "**Term**: definition"
        match = re.match(r'(?:\*\*)?(.+?)(?:\*\*)?[:]\s+(.+)', line)
        if match and len(match.group(1)) < 60:
            return match.group(1).strip(), match.group(2).strip()
        
        return "", ""
    
    def _is_custom_term(self, term: str) -> bool:
        """Check if this is likely a Theophysics-specific term."""
        custom_indicators = [
            'coherence', 'logos', 'theophysics', 'chi', 'χ',
            'grace coefficient', 'drift', 'moral', 'pneumatological',
            'soteriological', 'LLC', 'master equation',
            'negative image', 'proof tetralogy',
        ]
        term_lower = term.lower()
        return any(ind in term_lower for ind in custom_indicators)
    
    # =========================================================================
    # ASSERTIONS
    # =========================================================================
    
    def _extract_assertions(self, body: str) -> List[Assertion]:
        """Extract strong factual/theoretical assertions."""
        assertions = []
        lines = body.split('\n')
        current_section = "_preamble"
        
        for i, line in enumerate(lines):
            # Track sections
            header_match = re.match(r'^#{1,6}\s+(.+)', line)
            if header_match:
                current_section = header_match.group(1).strip()
                continue
            
            # Skip empty, code blocks, list markers only
            stripped = line.strip()
            if not stripped or stripped.startswith('```') or stripped == '-':
                continue
            
            # Check assertion patterns
            for pattern in self._compiled_assert_patterns:
                if pattern.search(stripped):
                    # Determine confidence
                    confidence = self._assess_confidence(stripped)
                    claim_type = self._classify_claim(stripped)
                    
                    assertions.append(Assertion(
                        text=stripped,
                        section=current_section,
                        line_number=i + 1,
                        claim_type=claim_type,
                        confidence=confidence
                    ))
                    break  # one match per line is enough
        
        return assertions
    
    def _assess_confidence(self, text: str) -> str:
        """Assess how confidently a claim is stated."""
        hedging = ['may', 'might', 'could', 'possibly', 'perhaps', 'suggests',
                    'appears to', 'seems to', 'it is possible', 'we conjecture']
        
        for hedge in hedging:
            if hedge in text.lower():
                return "hedged"
        
        strong = ['must', 'necessarily', 'always', 'never', 'proves', 
                  'demonstrates', 'establishes', 'if and only if']
        
        for s in strong:
            if s in text.lower():
                return "stated"
        
        return "stated"  # default
    
    def _classify_claim(self, text: str) -> str:
        """Classify the type of claim."""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['theorem', 'we prove', 'proof']):
            return "theorem"
        if any(w in text_lower for w in ['corollary', 'it follows']):
            return "corollary"
        if any(w in text_lower for w in ['conjecture', 'we hypothesize']):
            return "conjecture"
        if any(w in text_lower for w in ['axiom', 'we postulate', 'assume']):
            return "axiom"
        
        return "assertion"
