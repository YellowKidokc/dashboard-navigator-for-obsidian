#!/usr/bin/env python3
"""
THEOPHYSICS THEORY EVALUATION ENGINE v2.0
==========================================
"Fruits of the Spirit" → Structural Invariant Detectors

REPLACES: fruits_scorer.py (v1 keyword matcher)
COMPATIBLE WITH: unified_coherence_scorer.py bridge

v1 counted keywords like "love", "peace", "truth" — sentiment analysis
masquerading as structural evaluation. A physics paper about quantum
decoherence scored 0.00 on six Fruits because it never said "love."

v2 detects STRUCTURAL PROPERTIES of documents:
  - Does the paper define its terms before using them? (Faithfulness)
  - Does it bound its claims? (Self-Control)
  - Does it show derivation steps? (Patience)
  - Does it handle edge cases? (Grace)
  - Can parts fail without killing the whole? (Gentleness)

These are measurable document features, not keyword sentiment.

SECTION BOUNDARY PARSER (Phase 1 fix):
  Splits documents into SCORED zones (theory content) and EXCLUDED zones
  (critique sections, appendices, changelogs). Prevents critique sections
  from contaminating coherence scores — the bug that capped Genesis papers
  at χ=3.0 when they should have scored 6.0-7.0.

IMPLEMENTATION TIERS:
  Tier 1 (Pure structural): F4, F7, F8, F9, F12 — regex on document structure
  Tier 2 (Enhanced structural): F2, F3, F10, F11 — structural + pattern analysis
  Tier 3 (Best-effort structural, LLM-augmentable): F1, F5, F6 — proxies that
    work but would benefit from LLM-assisted scoring in future versions

Score Range (unchanged from v1 for compatibility):
  +8 to +12:  Coherence-stable, long-term viable
  +3 to +7:   Partially stable, repairable
  -2 to +2:   Incoherent / incomplete
  -3 to -12:  Entropy-amplifying (will collapse)

Author: Theophysics Engine (David Lowe / Claude collaboration)
Date: 2026-02-15
"""

import re
import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from collections import Counter

# =============================================================================
# SECTION BOUNDARY PARSER
# =============================================================================
# Phase 1 fix: Split document into scored vs excluded zones BEFORE any
# Fruit detection runs. This prevents critique/appendix sections from
# contaminating theory scores.

# Headings that mark THEORY content (scored)
THEORY_HEADINGS = re.compile(
    r'^#{1,4}\s*('
    r'abstract|introduction|theory|framework|method(?:ology)?|'
    r'results?|discussion|conclusion|implications?|'
    r'predictions?|falsif(?:ication|iability)|hypothesis|'
    r'model|formul(?:ation|a)|deriv(?:ation|ing)|'
    r'overview|background|foundation|axiom|postulate|'
    r'definition|notation|setup|argument|analysis|'
    r'proof|theorem|proposition|corollary|lemma'
    r')\b',
    re.IGNORECASE | re.MULTILINE
)

# Headings that mark EXCLUDED content (not scored for theory claims)
EXCLUDE_HEADINGS = re.compile(
    r'^#{1,4}\s*('
    r'critique|objection|response|rebuttal|appendix|'
    r'notes?|acknowledg|changelog|meta|commentary|'
    r'what\s+I\s+got\s+wrong|AI\s+feedback|things\s+to\s+fix|'
    r'GPT\s+review|Claude\s+review|AI\s+review|'
    r'counter[- ]?argument|criticism|weakness(?:es)?|'
    r'limitations?\s+and\s+criticism|known\s+issues?|'
    r'editorial|revision\s+history|errata|'
    r'self[- ]?critique|self[- ]?assessment|peer\s+review|'
    r'[A-F]\.\s+[A-Z][A-Z\s]+|'  # Lettered sections A-F with ALL-CAPS: "# A. PHYSICS MISAPPLICATIONS"
    r'MISAPPLICATION|OVEREXTENSION|CATEGORY\s+ERROR|LOGICAL\s+RISK|STRUCTURAL\s+RISK|HERMENEUTICAL'
    r')',
    re.MULTILINE  # Remove IGNORECASE - we want to preserve case sensitivity for ALL-CAPS detection
)

# Trigger phrases that mark start of critique sections (even without # heading)
CRITIQUE_TRIGGERS = [
    r'^\s*Now\s+(?:AI|GPT|Claude).*(?:wrong|critique|fix|feedback)',
    r'^\s*(?:What|Here is what|Here\'s what)\s+(?:I|we)\s+(?:did|got)\s+wrong',
    r'^\s*(?:Problems?|Issues?|Flaws?)\s+(?:with|in)\s+(?:this|the)',
]

# Headings that mark DEFENSE content (scored differently)
DEFENSE_HEADINGS = re.compile(
    r'^#{1,4}\s*('
    r'defense|rebuttal|response\s+to|addressing|'
    r'why\s+this\s+(?:works|holds|stands)|'
    r'counter[- ]?response|in\s+defense\s+of'
    r')\b',
    re.IGNORECASE | re.MULTILINE
)


@dataclass
class DocumentZones:
    """Parsed document split into scored and excluded zones."""
    theory_text: str          # Main theory content (scored for all Fruits)
    critique_text: str        # Critique/appendix content (excluded from scoring)
    defense_text: str         # Defense sections (scored for defense strength)
    full_text: str            # Original complete text
    theory_word_count: int = 0
    critique_word_count: int = 0
    defense_word_count: int = 0
    total_word_count: int = 0
    sections_found: List[str] = field(default_factory=list)
    excluded_sections: List[str] = field(default_factory=list)


def parse_document_zones(text: str) -> DocumentZones:
    """
    Split document into theory, critique, and defense zones.
    
    Logic:
    1. Split on heading markers (# lines)
    2. Classify each section by heading
    3. Check for critique trigger phrases (even without headings)
    4. Default unheaded content to theory (most documents start with theory)
    5. Return separated text blocks
    """
    lines = text.split('\n')
    
    theory_lines = []
    critique_lines = []
    defense_lines = []
    
    current_zone = 'theory'  # Default: unheaded content is theory
    sections_found = []
    excluded_sections = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check for critique trigger phrases (even without # heading)
        if current_zone == 'theory':
            for trigger_pattern in CRITIQUE_TRIGGERS:
                if re.match(trigger_pattern, line, re.IGNORECASE):
                    current_zone = 'critique'
                    excluded_sections.append(f"[trigger] {stripped[:50]}")
                    critique_lines.append(line)
                    break
            else:
                # No trigger matched, continue with heading checks
                pass
            
            # If we just switched to critique via trigger, skip rest of checks
            if current_zone == 'critique' and not stripped.startswith('#'):
                continue
        
        # Check if this line is a heading
        if stripped.startswith('#'):
            if EXCLUDE_HEADINGS.match(stripped):
                current_zone = 'critique'
                excluded_sections.append(stripped.lstrip('#').strip())
            elif DEFENSE_HEADINGS.match(stripped):
                current_zone = 'defense'
                sections_found.append(f"[defense] {stripped.lstrip('#').strip()}")
            elif THEORY_HEADINGS.match(stripped):
                current_zone = 'theory'
                sections_found.append(stripped.lstrip('#').strip())
            # Unknown headings: keep current zone (don't flip on random subheadings)
        
        # Also catch blockquote critique patterns
        if current_zone == 'theory' and stripped.startswith('>'):
            # Check if blockquote contains critique language
            critique_signals = ['objection', 'counterargument', 'weakness', 
                              'the problem with', 'fails to', 'does not account']
            if any(sig in stripped.lower() for sig in critique_signals):
                critique_lines.append(line)
                continue
        
        # Route line to appropriate zone
        if current_zone == 'theory':
            theory_lines.append(line)
        elif current_zone == 'critique':
            critique_lines.append(line)
        elif current_zone == 'defense':
            defense_lines.append(line)
    
    theory_text = '\n'.join(theory_lines)
    critique_text = '\n'.join(critique_lines)
    defense_text = '\n'.join(defense_lines)
    
    return DocumentZones(
        theory_text=theory_text,
        critique_text=critique_text,
        defense_text=defense_text,
        full_text=text,
        theory_word_count=len(theory_text.split()),
        critique_word_count=len(critique_text.split()),
        defense_word_count=len(defense_text.split()),
        total_word_count=len(text.split()),
        sections_found=sections_found,
        excluded_sections=excluded_sections
    )


# =============================================================================
# DATA STRUCTURES (compatible with v1)
# =============================================================================

@dataclass
class FruitScore:
    """Score for a single fruit metric."""
    name: str
    score: float           # -1.0 to +1.0
    positive_hits: int     # Count of positive structural indicators found
    negative_hits: int     # Count of negative structural indicators found
    interpretation: str
    tier: str = ""         # "structural", "enhanced", "proxy" — transparency
    details: Dict = field(default_factory=dict)  # Diagnostic breakdown


@dataclass
class FruitsAnalysis:
    """Complete Fruits of the Spirit analysis for a theory."""
    name: str
    word_count: int

    # Individual fruit scores
    f1_grace: FruitScore = None
    f2_hope: FruitScore = None
    f3_patience: FruitScore = None
    f4_faithfulness: FruitScore = None
    f5_self_control: FruitScore = None
    f6_love: FruitScore = None
    f7_peace: FruitScore = None
    f8_truth: FruitScore = None
    f9_humility: FruitScore = None
    f10_goodness: FruitScore = None
    f11_unity: FruitScore = None
    f12_joy: FruitScore = None

    # Aggregate scores
    total_score: float = 0.0       # -12 to +12
    normalized_score: float = 0.0  # 0 to 100
    grade: str = "F"
    interpretation: str = ""
    
    # v2 additions
    zones: DocumentZones = None
    scorer_version: str = "fruits_12_v2"


# =============================================================================
# STRUCTURAL DETECTION HELPERS
# =============================================================================

def count_regex(text: str, patterns: List[str]) -> int:
    """Count total regex matches across pattern list."""
    count = 0
    text_lower = text.lower()
    for pattern in patterns:
        count += len(re.findall(pattern, text_lower, re.IGNORECASE))
    return count


def find_all_regex(text: str, patterns: List[str]) -> List[str]:
    """Return all matching strings (for diagnostics)."""
    matches = []
    text_lower = text.lower()
    for pattern in patterns:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE):
            matches.append(m.group())
    return matches


def extract_definitions(text: str) -> List[Tuple[str, str]]:
    """
    Find explicit definitions in text.
    Returns list of (term, definition_context) tuples.
    """
    patterns = [
        # "We define X as Y"
        r'(?:we\s+)?defin[e|ed|es|ing]\s+(\w[\w\s]{1,40}?)\s+as\s+(.{10,100}?)[\.\n]',
        # "X is defined as Y"
        r'(\w[\w\s]{1,40}?)\s+is\s+defined\s+as\s+(.{10,100}?)[\.\n]',
        # "Let X = Y" or "Let X be Y"
        r'[Ll]et\s+(\w[\w\s]{1,30}?)\s*[=≡:]\s*(.{10,100}?)[\.\n]',
        r'[Ll]et\s+(\w[\w\s]{1,30}?)\s+be\s+(.{10,100}?)[\.\n]',
        # "X := Y" (formal definition)
        r'(\w[\w\s]{1,30}?)\s*:=\s*(.{10,100}?)[\.\n]',
        # "where X represents/denotes Y"
        r'where\s+(\w[\w\s]{1,30}?)\s+(?:represents?|denotes?|signif(?:ies|y))\s+(.{10,100}?)[\.\n]',
        # "By X we mean Y"
        r'[Bb]y\s+["\']?(\w[\w\s]{1,30}?)["\']?\s+we\s+mean\s+(.{10,100}?)[\.\n]',
    ]
    
    definitions = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            term = m.group(1).strip()
            context = m.group(2).strip()
            if len(term) > 1 and len(context) > 5:
                definitions.append((term, context))
    
    return definitions


def extract_equations(text: str) -> List[str]:
    """Find mathematical expressions (LaTeX, inline, Unicode)."""
    patterns = [
        r'\$[^$]+\$',                          # LaTeX inline
        r'\$\$[^$]+\$\$',                      # LaTeX display
        r'\\begin\{equation\}.*?\\end\{equation\}',  # LaTeX env
        r'[A-Za-zΨΦΛχκρ]\s*[=≡≈∝→←⇒]\s*.+',  # Unicode equations
        r'∫.*d[xyzt]',                          # Integrals
        r'∑.*[=<>]',                            # Summations
        r'\b[A-Z]\([^)]+\)\s*=',                # Function definitions F(x) =
    ]
    
    equations = []
    for pattern in patterns:
        for m in re.finditer(pattern, text):
            equations.append(m.group().strip())
    
    return equations


def count_logical_connectives(text: str) -> int:
    """Count derivation markers showing logical progression."""
    patterns = [
        r'\b(?:therefore|thus|hence|consequently|it follows that)\b',
        r'\b(?:because|since|given that|assuming)\b',
        r'\b(?:first|second|third|finally|next|then)\b',
        r'\b(?:if.*then|implies that|leads to|results in)\b',
        r'\b(?:from\s+(?:this|equation|the above))\b',
        r'\b(?:combining|substituting|applying)\b',
        r'[⇒→∴⊢]',  # Logical symbols
    ]
    return count_regex(text, patterns)


def count_scope_limitations(text: str) -> int:
    """Count explicit scope-bounding statements."""
    patterns = [
        r'\b(?:does not claim|do not claim|we do not)\b',
        r'\b(?:limited to|only within|restricted to)\b',
        r'\b(?:beyond the scope|outside.*scope)\b',
        r'\b(?:this (?:does not|cannot) (?:explain|account|address))\b',
        r'\b(?:we leave|left for future|future work)\b',
        r'\b(?:not (?:a |the )?(?:complete|full|exhaustive|comprehensive) (?:account|theory|explanation))\b',
        r'\b(?:this framework does not)\b',
        r'\b(?:specifically|in particular|narrowly)\b',
        r'\bfalsifiabl[ey]\b',
        r'\btestabl[ey]\b',
    ]
    return count_regex(text, patterns)


def count_prediction_statements(text: str) -> int:
    """Count forward-looking predictive claims."""
    patterns = [
        r'\b(?:this (?:predicts|implies|suggests|entails))\b',
        r'\b(?:the (?:model|framework|theory|equation) predicts)\b',
        r'\b(?:we (?:predict|expect|anticipate))\b',
        r'\b(?:a testable (?:prediction|consequence|implication))\b',
        r'\b(?:if (?:this|the) (?:framework|model|theory) is correct)\b',
        r'\b(?:measurable (?:consequence|effect|outcome))\b',
        r'\b(?:experimentally (?:verifiable|testable|detectable))\b',
        r'\b(?:one could (?:test|measure|observe|verify))\b',
        r'\b(?:future (?:experiments?|observations?|measurements?) (?:could|should|would))\b',
    ]
    return count_regex(text, patterns)


def count_modularity_markers(text: str) -> int:
    """Count language indicating modular/separable structure."""
    patterns = [
        r'\b(?:even if.*(?:fails?|wrong|incorrect).*(?:still|remains?|holds?))\b',
        r'\b(?:independent(?:ly)? of)\b',
        r'\b(?:separable|modular|standalone|self[- ]?contained)\b',
        r'\b(?:does not depend on|not contingent)\b',
        r'\b(?:this (?:section|result|argument) (?:stands|holds) (?:regardless|independently))\b',
        r'\b(?:can be (?:rejected|falsified|modified) without)\b',
        r'\b(?:weakest|strongest|most speculative|most robust)\b',
    ]
    return count_regex(text, patterns)


def count_edge_case_handling(text: str) -> int:
    """Count explicit edge case and boundary handling."""
    patterns = [
        r'\b(?:edge case|corner case|boundary (?:case|condition))\b',
        r'\b(?:in the limit|limiting case|as.*(?:approaches|→))\b',
        r'\b(?:apparent (?:counter[- ]?example|exception|paradox))\b',
        r'\b(?:what (?:happens|about) (?:when|if))\b',
        r'\b(?:open (?:problem|question|issue))\b',
        r'\b(?:we (?:acknowledge|note|recognize) (?:that|this))\b',
        r'\b(?:uncertainty|error (?:bar|bound|margin))\b',
        r'\b(?:within (?:error|tolerance|bounds))\b',
        r'\b(?:degrades gracefully|breaks down at)\b',
        r'\b(?:this (?:does not|fails to) (?:apply|hold) (?:when|for|in))\b',
    ]
    return count_regex(text, patterns)


def count_steelman_markers(text: str) -> int:
    """Count intellectual charity / steelmanning indicators."""
    patterns = [
        r'\b(?:the (?:strongest|best|most (?:serious|compelling)) (?:objection|argument|case))\b',
        r'\b(?:a (?:serious|legitimate|valid) (?:concern|criticism|objection))\b',
        r'\b(?:(?:proponents|advocates|defenders) (?:of|would argue))\b',
        r'\b(?:to (?:be|remain) fair)\b',
        r'\b(?:one (?:could|might) (?:reasonably|legitimately) (?:argue|object|question))\b',
        r'\b(?:the (?:conventional|standard|mainstream) (?:view|position|argument))\b',
        r'\b(?:this framework (?:agrees|concurs) with)\b',
        r'\b(?:what.*gets right)\b',
        r'\b(?:credit (?:to|where))\b',
    ]
    return count_regex(text, patterns)


def count_evidence_units(text: str) -> int:
    """Count evidence citations and data references."""
    patterns = [
        r'\b(?:evidence|data|experiment|observation|measurement)\b',
        r'\bp\s*[<>=]\s*0?\.\d+',              # p-values
        r'\b\d+[.-]?σ\b',                       # sigma values
        r'\bN\s*=\s*\d+',                        # sample sizes
        r'\b(?:95|99)%\s*(?:CI|confidence)\b',   # confidence intervals
        r'\b(?:figure|fig\.?|table|tab\.?)\s*\d+', # figure/table refs
        r'\[[\d,\s-]+\]',                        # bracketed citations
        r'\b(?:et al\.?)\b',                     # academic citations
        r'\b(?:replicated|reproduced|confirmed)\b',
        r'R[²2]\s*=\s*0?\.\d+',                 # R-squared values
    ]
    return count_regex(text, patterns)


def count_hedging_vs_assertion(text: str) -> Tuple[int, int]:
    """Count calibrated language vs overclaiming."""
    hedges = [
        r'\b(?:suggests?|may|might|could|possibly|potentially)\b',
        r'\b(?:we (?:hypothesize|propose|conjecture|speculate))\b',
        r'\b(?:tentative(?:ly)?|preliminary|provisional)\b',
        r'\b(?:appears? to|seems? to)\b',
        r'\b(?:is consistent with|compatible with)\b',
    ]
    overclaims = [
        r'\b(?:proves?|proof|proven|demonstrated? (?:conclusively|definitively))\b',
        r'\b(?:obviously|clearly|undeniably|irrefutably|unquestionably)\b',
        r'\b(?:must be|can only be|the only (?:explanation|possibility))\b',
        r'\b(?:settles? (?:the|this)|puts? to rest)\b',
        r'\b(?:beyond (?:any |all )?(?:doubt|question))\b',
    ]
    return count_regex(text, hedges), count_regex(text, overclaims)


def count_cross_domain_mappings(text: str) -> int:
    """Count explicit cross-domain structural mappings (physics↔theology, etc.)."""
    patterns = [
        r'\b(?:correspond(?:s|ing)? to|maps? to|analogous to|isomorphic to)\b',
        r'\b(?:in (?:physical|spiritual|theological|mathematical) terms)\b',
        r'\b(?:physical (?:analog(?:ue)?|counterpart|equivalent))\b',
        r'\b(?:the (?:physics|theology|mathematics) (?:gives us|tells us|shows))\b',
        r'(?:→|↔|⟷|maps\s+to)',                # Mapping symbols
        r'\b(?:dual(?:ity)?|dual description|two (?:faces|sides|aspects) of)\b',
        r'\b(?:just as.*so too)\b',              # Structural parallel
        r'\b(?:the same (?:structure|pattern|logic) (?:appears|emerges|operates))\b',
    ]
    return count_regex(text, patterns)


def detect_heading_hierarchy(text: str) -> Dict[str, int]:
    """Analyze heading structure for hierarchical organization."""
    h1 = len(re.findall(r'^#\s+\S', text, re.MULTILINE))
    h2 = len(re.findall(r'^##\s+\S', text, re.MULTILINE))
    h3 = len(re.findall(r'^###\s+\S', text, re.MULTILINE))
    h4 = len(re.findall(r'^####\s+\S', text, re.MULTILINE))
    return {'h1': h1, 'h2': h2, 'h3': h3, 'h4': h4, 
            'total': h1 + h2 + h3 + h4,
            'depth': max(d for d, c in enumerate([h1, h2, h3, h4], 1) if c > 0) if any([h1, h2, h3, h4]) else 0}


def count_constructive_tools(text: str) -> int:
    """Count standalone-useful components offered to the reader."""
    patterns = [
        r'\b(?:(?:this|the) (?:framework|method|approach|tool|metric) can be (?:applied|used|adapted))\b',
        r'\b(?:regardless of|independent of|whether or not (?:one|you) (?:accept|agree))\b',
        r'\b(?:useful for|applicable to|extends to)\b',
        r'\b(?:any (?:theory|framework|researcher) (?:can|could|may))\b',
        r'\b(?:transferable|generalizable|replicable|reusable)\b',
        r'\b(?:template|recipe|procedure|protocol|algorithm|method)\b',
        r'\b(?:step[- ]?by[- ]?step|how to)\b',
    ]
    return count_regex(text, patterns)


# =============================================================================
# 12 FRUIT SCORING FUNCTIONS (STRUCTURAL DETECTORS)
# =============================================================================

def score_f1_love(text: str, word_count: int) -> FruitScore:
    """
    F1 LOVE (Agape) — Integration Under Service
    TIER: proxy (LLM-augmentable)
    
    Structural property: Cross-domain mappings that preserve structure in both
    domains, combined with reader-service orientation (building bridges others
    can walk across, not just asserting connections).
    """
    cross_domain = count_cross_domain_mappings(text)
    constructive = count_constructive_tools(text)
    
    # Reader-service language
    service_patterns = [
        r'\b(?:we (?:offer|provide|present|propose))\b',
        r'\b(?:the reader (?:can|may|will|should))\b',
        r'\b(?:for (?:clarity|accessibility|completeness))\b',
        r'\b(?:to (?:illustrate|clarify|demonstrate))\b',
    ]
    service_hits = count_regex(text, service_patterns)
    
    # Negative: pure assertion without bridge-building
    isolation_patterns = [
        r'\b(?:obviously|trivially|it is clear that)\b',
        r'\b(?:as everyone knows|needless to say)\b',
        r'\b(?:we leave (?:it )?to the reader)\b',
    ]
    isolation_hits = count_regex(text, isolation_patterns)
    
    # Normalize per 1000 words
    k = max(word_count / 1000, 1)
    pos = (cross_domain + constructive + service_hits) / k
    neg = isolation_hits / k
    
    # Score: positive density minus negative, clamped
    raw = min(pos / 4.0, 1.0) - min(neg / 2.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    interp = _interpret_score(score)
    
    return FruitScore(
        name="Love", score=round(score, 3),
        positive_hits=cross_domain + constructive + service_hits,
        negative_hits=isolation_hits,
        interpretation=interp, tier="proxy",
        details={"cross_domain_mappings": cross_domain, 
                 "constructive_tools": constructive,
                 "service_language": service_hits,
                 "isolation_language": isolation_hits}
    )


def score_f2_joy(text: str, word_count: int) -> FruitScore:
    """
    F2 JOY (Chara) — Generative Capacity
    TIER: enhanced
    
    Structural property: The theory generates testable predictions, productive
    open questions, and applications beyond its initial scope. A theory that
    generates nothing new is dead on arrival.
    """
    predictions = count_prediction_statements(text)
    
    # Open questions acknowledged as productive
    open_q_patterns = [
        r'\b(?:open question|remains to be (?:seen|determined|tested))\b',
        r'\b(?:future (?:work|research|investigation) (?:could|should|might))\b',
        r'\b(?:this raises (?:the|an?) (?:interesting|important|key) question)\b',
        r'\b(?:we do not yet know|it is not yet (?:clear|known))\b',
        r'\b(?:productive (?:direction|avenue|line of inquiry))\b',
    ]
    open_questions = count_regex(text, open_q_patterns)
    
    # Novel application markers
    application_patterns = [
        r'\b(?:application|implication|consequence|extension)\b',
        r'\b(?:this (?:extends|generalizes|applies) (?:to|beyond))\b',
        r'\b(?:unexpected(?:ly)?|surprising(?:ly)?|remarkably)\b',
        r'\b(?:new (?:insight|perspective|understanding|prediction))\b',
    ]
    applications = count_regex(text, application_patterns)
    
    # Negative: theory generates nothing beyond its premises
    sterile_patterns = [
        r'\b(?:merely restates?|tautolog|circular)\b',
        r'\b(?:no (?:new|novel|testable) (?:predictions?|consequences?|implications?))\b',
    ]
    sterile_hits = count_regex(text, sterile_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (predictions * 2 + open_questions + applications) / k  # Predictions weighted 2x
    neg = sterile_hits / k
    
    raw = min(pos / 5.0, 1.0) - min(neg / 1.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Joy", score=round(score, 3),
        positive_hits=predictions + open_questions + applications,
        negative_hits=sterile_hits,
        interpretation=_interpret_score(score), tier="enhanced",
        details={"predictions": predictions, "open_questions": open_questions,
                 "applications": applications, "sterile_markers": sterile_hits}
    )


def score_f3_peace(text: str, word_count: int) -> FruitScore:
    """
    F3 PEACE (Eirene) — Internal Non-Contradiction
    TIER: enhanced
    
    Structural property: Consistent term usage, conclusions follow from premises,
    no section contradicts another. Variable meanings don't shift mid-argument.
    
    NOTE: This MUST run on theory_text only (section parser applied before scoring).
    """
    # Positive: consistency markers
    consistency_patterns = [
        r'\b(?:as (?:defined|stated|shown) (?:above|earlier|previously|in Section))\b',
        r'\b(?:consistent(?:ly)? with)\b',
        r'\b(?:in (?:accord|agreement|line) with)\b',
        r'\b(?:recall (?:that|our|the))\b',
        r'\b(?:as we (?:established|showed|demonstrated|noted))\b',
        r'\b(?:this (?:confirms|aligns with|supports))\b',
    ]
    consistency = count_regex(text, consistency_patterns)
    
    # Negative: internal contradiction markers (in THEORY text, not critique)
    contradiction_patterns = [
        r'\b(?:however.*contradicts?|but.*(?:inconsistent|conflicts?))\b',
        r'\b(?:this (?:contradicts?|conflicts? with) (?:our|the) (?:earlier|previous))\b',
        r'\b(?:(?:paradox|tension|contradiction) (?:within|between|in))\b',
        r'\b(?:ad[- ]?hoc|patchwork|kludge)\b',
    ]
    contradictions = count_regex(text, contradiction_patterns)
    
    # Term stability: check if key terms get redefined mid-document
    definitions = extract_definitions(text)
    defined_terms = [d[0].lower().strip() for d in definitions]
    term_counter = Counter(defined_terms)
    redefined_terms = sum(1 for count in term_counter.values() if count > 1)
    
    k = max(word_count / 1000, 1)
    pos = consistency / k
    neg = (contradictions + redefined_terms * 2) / k  # Redefinitions penalized heavily
    
    raw = min(pos / 3.0, 1.0) - min(neg / 2.0, 1.0)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Peace", score=round(score, 3),
        positive_hits=consistency,
        negative_hits=contradictions + redefined_terms,
        interpretation=_interpret_score(score), tier="enhanced",
        details={"consistency_markers": consistency, 
                 "contradiction_markers": contradictions,
                 "definitions_found": len(definitions),
                 "redefined_terms": redefined_terms}
    )


def score_f4_patience(text: str, word_count: int) -> FruitScore:
    """
    F4 PATIENCE (Makrothymia) — Thoroughness of Development
    TIER: structural
    
    Structural property: Multi-step derivations with each step justified.
    Logical progression visible. Intermediate results before final claims.
    Worked examples showing framework operating.
    """
    connectives = count_logical_connectives(text)
    
    # Derivation chain markers
    derivation_patterns = [
        r'\b(?:step \d|first.*then.*(?:therefore|finally))\b',
        r'\b(?:from (?:this|equation|the above).*(?:we get|it follows|we obtain))\b',
        r'\b(?:substitut(?:e|ing)|combining|applying (?:this|the))\b',
        r'\b(?:intermediate result|working through)\b',
    ]
    derivations = count_regex(text, derivation_patterns)
    
    # Worked examples
    example_patterns = [
        r'\b(?:(?:for )?example|consider (?:the|a) (?:case|scenario))\b',
        r'\b(?:to (?:illustrate|see (?:this|how)))\b',
        r'\b(?:worked example|concrete(?:ly)?|specifically)\b',
        r'\b(?:suppose (?:that|we)|imagine|let us consider)\b',
    ]
    examples = count_regex(text, example_patterns)
    
    # Equations (derivation steps)
    equations = extract_equations(text)
    
    # Negative: assertion without derivation
    assertion_patterns = [
        r'\b(?:obviously|clearly|trivially|it is (?:well[- ]?known|obvious))\b',
        r'\b(?:the proof is (?:left|omitted|trivial|straightforward))\b',
        r'\b(?:one can (?:easily|readily) (?:see|show|verify))\b',
    ]
    assertions = count_regex(text, assertion_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (connectives + derivations * 2 + examples + len(equations) * 0.5) / k
    neg = assertions / k
    
    raw = min(pos / 6.0, 1.0) - min(neg / 2.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Patience", score=round(score, 3),
        positive_hits=connectives + derivations + examples + len(equations),
        negative_hits=assertions,
        interpretation=_interpret_score(score), tier="structural",
        details={"logical_connectives": connectives, "derivation_chains": derivations,
                 "worked_examples": examples, "equations": len(equations),
                 "skip_assertions": assertions}
    )


def score_f5_kindness(text: str, word_count: int) -> FruitScore:
    """
    F5 KINDNESS (Chrestotes) — Intellectual Charity
    TIER: proxy (LLM-augmentable)
    
    Structural property: Opposing views stated in strongest form before being
    addressed. Theory explains why someone might reasonably disagree.
    """
    steelman = count_steelman_markers(text)
    
    # Objection-response pairs
    objection_patterns = [
        r'\b(?:objection|counter[- ]?argument|(?:one|some) (?:might|could) (?:argue|object))\b',
        r'\b(?:(?:the|a) (?:critic|skeptic|opponent) (?:might|would|could))\b',
        r'\b(?:in response|we respond|addressing this)\b',
        r'\b(?:fair (?:point|concern|criticism|objection))\b',
    ]
    objections = count_regex(text, objection_patterns)
    
    # Acknowledgment of competing frameworks
    acknowledgment_patterns = [
        r'\b(?:(?:standard|conventional|mainstream|orthodox) (?:model|theory|view|physics))\b',
        r'\b(?:(?:other|alternative|competing) (?:frameworks?|theories?|models?|approaches?))\b',
        r'\b(?:(?:quantum (?:mechanics|theory)|general relativity|string theory) (?:correctly|successfully|rightly))\b',
    ]
    acknowledgments = count_regex(text, acknowledgment_patterns)
    
    # Negative: strawmanning
    strawman_patterns = [
        r'\b(?:(?:naive|simplist?ic|foolish|absurd) (?:view|claim|argument))\b',
        r'\b(?:(?:they|critics|opponents) (?:fail|refuse|cannot) (?:to )?(?:see|understand|grasp))\b',
        r'\b(?:(?:ignorant|blind|dogmatic) (?:of|to|adherence))\b',
    ]
    strawman = count_regex(text, strawman_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (steelman * 2 + objections + acknowledgments) / k
    neg = strawman * 2 / k  # Strawmanning penalized heavily
    
    raw = min(pos / 4.0, 1.0) - min(neg / 1.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Kindness", score=round(score, 3),
        positive_hits=steelman + objections + acknowledgments,
        negative_hits=strawman,
        interpretation=_interpret_score(score), tier="proxy",
        details={"steelman_markers": steelman, "objection_response_pairs": objections,
                 "competing_framework_acknowledgment": acknowledgments,
                 "strawman_markers": strawman}
    )


def score_f6_goodness(text: str, word_count: int) -> FruitScore:
    """
    F6 GOODNESS (Agathosyne) — Constructive Value
    TIER: proxy (LLM-augmentable)
    
    Structural property: Framework provides tools others can use regardless
    of accepting full theory. Methodology transferable. Intermediate results
    have standalone value.
    """
    tools = count_constructive_tools(text)
    
    # Methodology sections
    method_patterns = [
        r'\b(?:method(?:ology)?|procedure|protocol|algorithm)\b',
        r'\b(?:replicabl[ey]|reproducibl[ey]|transferabl[ey])\b',
        r'\b(?:standalone|self[- ]?contained|independent(?:ly)? useful)\b',
        r'\b(?:intermediate result|partial (?:result|finding|conclusion))\b',
        r'\b(?:even (?:without|if.*reject).*(?:useful|valuable|applicable))\b',
    ]
    methodology = count_regex(text, method_patterns)
    
    # Negative: purely destructive (tears down without building)
    destructive_patterns = [
        r'\b(?:destroy|demolish|refute|debunk|expose)\b.*(?:without|but not)',
        r'\b(?:this (?:disproves|invalidates|overturns))\b',
    ]
    destructive = count_regex(text, destructive_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (tools * 2 + methodology) / k
    neg = destructive / k
    
    raw = min(pos / 4.0, 1.0) - min(neg / 2.0, 0.3)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Goodness", score=round(score, 3),
        positive_hits=tools + methodology,
        negative_hits=destructive,
        interpretation=_interpret_score(score), tier="proxy",
        details={"constructive_tools": tools, "methodology_markers": methodology,
                 "destructive_only": destructive}
    )


def score_f7_faithfulness(text: str, word_count: int) -> FruitScore:
    """
    F7 FAITHFULNESS (Pistis) — Definitional Rigor
    TIER: structural
    
    Structural property: Terms defined before use. Variables have domains and
    ranges. Borrowed terms flagged. Consistent usage throughout.
    """
    definitions = extract_definitions(text)
    equations = extract_equations(text)
    
    # Variable definition completeness
    var_def_patterns = [
        r'\b(?:where|here)\s+\w+\s+(?:is|represents?|denotes?|=)\b',
        r'\b(?:let|define|set)\s+\w+\s*[=:≡]\b',
        r'\b(?:units?|dimension|range|domain)\s*[:=]\b',
    ]
    var_defs = count_regex(text, var_def_patterns)
    
    # Undefined variable detection (rough: equations with symbols not in definitions)
    # This is a proxy — just check if definitions exist near equations
    has_definitions = len(definitions) > 0
    has_equations = len(equations) > 0
    equation_definition_ratio = (len(definitions) / max(len(equations), 1)) if has_equations else 1.0
    
    # Borrowed term flagging
    borrow_patterns = [
        r'\b(?:in the (?:sense|usage) of|following|per|as (?:used|defined) (?:by|in))\b',
        r'\b(?:we (?:borrow|adopt|use) (?:the|this) term)\b',
        r'\b(?:not to be confused with|distinct from)\b',
    ]
    borrowed_flagged = count_regex(text, borrow_patterns)
    
    # Negative: undefined jargon
    jargon_patterns = [
        r'\b(?:scare quotes|so[- ]?called|loosely speaking)\b',
        r'\b(?:in (?:some|a) sense)\b',
    ]
    loose_terms = count_regex(text, jargon_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (len(definitions) * 2 + var_defs + borrowed_flagged + min(equation_definition_ratio, 1.0) * 3) / k
    neg = loose_terms / k
    
    raw = min(pos / 5.0, 1.0) - min(neg / 2.0, 0.3)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Faithfulness", score=round(score, 3),
        positive_hits=len(definitions) + var_defs + borrowed_flagged,
        negative_hits=loose_terms,
        interpretation=_interpret_score(score), tier="structural",
        details={"explicit_definitions": len(definitions), "variable_definitions": var_defs,
                 "borrowed_terms_flagged": borrowed_flagged, "equations": len(equations),
                 "eq_def_ratio": round(equation_definition_ratio, 2),
                 "loose_terms": loose_terms}
    )


def score_f8_gentleness(text: str, word_count: int) -> FruitScore:
    """
    F8 GENTLENESS (Prautes) — Graceful Degradation Under Attack
    TIER: structural
    
    Structural property: Explicit modularity. Clean separation between core
    and derived. Individual predictions can fail without killing framework.
    Author marks strength gradations.
    """
    modularity = count_modularity_markers(text)
    
    # Strength gradation markers
    gradation_patterns = [
        r'\b(?:(?:most|least) (?:speculative|robust|certain|established))\b',
        r'\b(?:core (?:claim|axiom|result)|derived (?:claim|prediction|consequence))\b',
        r'\b(?:primary|secondary|tertiary|auxiliary)\b',
        r'\b(?:load[- ]?bearing|decorative|optional|essential)\b',
        r'\b(?:if (?:this|Section \d+) (?:fails?|is wrong).*(?:still|remains?))\b',
    ]
    gradations = count_regex(text, gradation_patterns)
    
    # Negative: monolithic fragility
    fragile_patterns = [
        r'\b(?:(?:the )?entire (?:framework|theory|argument) (?:depends|rests|hinges) (?:on|upon))\b',
        r'\b(?:if (?:this|any) (?:fails?|is wrong).*(?:everything|all|the whole))\b',
        r'\b(?:all[- ]?or[- ]?nothing|take it or leave it)\b',
        r'\b(?:indivisible|inseparable|monolithic)\b',
    ]
    fragile = count_regex(text, fragile_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (modularity * 2 + gradations) / k
    neg = fragile * 2 / k
    
    raw = min(pos / 3.0, 1.0) - min(neg / 1.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Gentleness", score=round(score, 3),
        positive_hits=modularity + gradations,
        negative_hits=fragile,
        interpretation=_interpret_score(score), tier="structural",
        details={"modularity_markers": modularity, "strength_gradations": gradations,
                 "fragility_markers": fragile}
    )


def score_f9_self_control(text: str, word_count: int) -> FruitScore:
    """
    F9 SELF-CONTROL (Egkrateia) — Claim Bounding
    TIER: structural
    
    Structural property: Explicit scope statements. Claims calibrated to
    evidence strength. "We do not claim..." disclaimers. Careful distinction
    between "suggests" and "proves."
    """
    scope_limits = count_scope_limitations(text)
    hedges, overclaims = count_hedging_vs_assertion(text)
    
    # Speculation markers (positive when explicitly flagged)
    speculation_patterns = [
        r'\b(?:speculative(?:ly)?|conjecture|hypothesis|tentative)\b',
        r'\b(?:we (?:speculate|hypothesize|conjecture|propose))\b',
        r'\b(?:this is (?:speculative|a hypothesis|tentative|preliminary))\b',
        r'\b(?:it (?:is|remains) (?:possible|plausible) that)\b',
    ]
    labeled_speculation = count_regex(text, speculation_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (scope_limits * 2 + hedges + labeled_speculation) / k
    neg = overclaims * 2 / k
    
    raw = min(pos / 5.0, 1.0) - min(neg / 2.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Self-Control", score=round(score, 3),
        positive_hits=scope_limits + hedges + labeled_speculation,
        negative_hits=overclaims,
        interpretation=_interpret_score(score), tier="structural",
        details={"scope_limitations": scope_limits, "calibrated_hedges": hedges,
                 "labeled_speculation": labeled_speculation,
                 "overclaim_language": overclaims}
    )


def score_f10_truth(text: str, word_count: int) -> FruitScore:
    """
    F10 TRUTH (Aletheia) — Evidence-Claim Alignment
    TIER: enhanced
    
    Structural property: Citations verifiable. Data has uncertainty bounds.
    Statistical claims complete. Evidence directly supports cited claim.
    """
    evidence = count_evidence_units(text)
    
    # Statistical completeness markers
    stat_patterns = [
        r'\bp\s*[<>=]\s*0?\.\d+',              # p-values
        r'\b\d+[.-]?σ\b',                       # sigma values
        r'\bN\s*=\s*\d+',                        # sample sizes
        r'\b(?:95|99)%\s*(?:CI|confidence)\b',   # confidence intervals
        r'R[²2]\s*=\s*0?\.\d+',                 # R-squared
        r'±\s*\d',                               # uncertainty bounds
    ]
    stats = count_regex(text, stat_patterns)
    
    # Claims without evidence (rough proxy)
    claim_patterns = [
        r'\b(?:we (?:claim|assert|argue|contend|maintain) that)\b',
        r'\b(?:it is (?:true|the case|a fact) that)\b',
        r'\b(?:this (?:shows|demonstrates|proves|establishes))\b',
    ]
    claims = count_regex(text, claim_patterns)
    
    # Evidence-to-claim ratio
    ecr = evidence / max(claims, 1)
    
    # Negative: unsupported assertion
    unsupported_patterns = [
        r'\b(?:everyone knows|it is well[- ]?known|as is obvious)\b',
        r'\b(?:needless to say|goes without saying|self[- ]?evident)\b',
    ]
    unsupported = count_regex(text, unsupported_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (evidence + stats * 2 + min(ecr, 2.0) * 2) / k
    neg = unsupported / k
    
    raw = min(pos / 5.0, 1.0) - min(neg / 1.0, 0.3)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Truth", score=round(score, 3),
        positive_hits=evidence + stats,
        negative_hits=unsupported,
        interpretation=_interpret_score(score), tier="enhanced",
        details={"evidence_units": evidence, "statistical_completeness": stats,
                 "claim_count": claims, "evidence_claim_ratio": round(ecr, 2),
                 "unsupported_assertions": unsupported}
    )


def score_f11_wisdom(text: str, word_count: int) -> FruitScore:
    """
    F11 WISDOM (Sophia) — Hierarchical Understanding
    TIER: enhanced
    
    Structural property: Clear hierarchy (axioms → theorems → predictions).
    Big-picture framing before detail. Load-bearing vs decorative results
    explicitly marked. Multi-level summarizability.
    """
    hierarchy = detect_heading_hierarchy(text)
    
    # Framing language (big picture before detail)
    framing_patterns = [
        r'\b(?:the (?:key|central|main|core|essential) (?:insight|idea|claim|result))\b',
        r'\b(?:at (?:its|the) (?:core|heart|foundation))\b',
        r'\b(?:the (?:big|larger|broader) picture)\b',
        r'\b(?:in (?:summary|essence|brief))\b',
        r'\b(?:the (?:fundamental|underlying|deeper) (?:point|principle|truth))\b',
    ]
    framing = count_regex(text, framing_patterns)
    
    # Hierarchical language
    hier_patterns = [
        r'\b(?:axiom|postulate|theorem|corollary|lemma|proposition)\b',
        r'\b(?:from (?:this|these) (?:axioms?|principles?|premises?).*(?:follows?|derive|obtain))\b',
        r'\b(?:at (?:a|the) (?:higher|lower|deeper|more fundamental) level)\b',
        r'\b(?:primary|secondary|derived|foundational)\b',
    ]
    hierarchical = count_regex(text, hier_patterns)
    
    # Check for abstract/summary
    has_abstract = bool(re.search(r'^#{1,3}\s*(?:abstract|summary|overview|executive summary)\b', 
                                   text, re.IGNORECASE | re.MULTILINE))
    
    # Negative: flat structure, no hierarchy
    flat_patterns = [
        r'\b(?:and also|and another thing|additionally|furthermore|moreover)\b',
    ]
    flat_markers = count_regex(text, flat_patterns)
    
    k = max(word_count / 1000, 1)
    depth_bonus = min(hierarchy['depth'] / 3.0, 1.0)  # Deeper = more hierarchical
    abstract_bonus = 1.0 if has_abstract else 0.0
    
    pos = (framing + hierarchical + depth_bonus * 3 + abstract_bonus * 2) / k
    neg = flat_markers / (k * 3)  # Light penalty — these words aren't always bad
    
    raw = min(pos / 4.0, 1.0) - min(neg, 0.2)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Wisdom", score=round(score, 3),
        positive_hits=framing + hierarchical,
        negative_hits=flat_markers,
        interpretation=_interpret_score(score), tier="enhanced",
        details={"heading_depth": hierarchy['depth'], "heading_count": hierarchy['total'],
                 "framing_language": framing, "hierarchical_language": hierarchical,
                 "has_abstract": has_abstract, "flat_markers": flat_markers}
    )


def score_f12_grace(text: str, word_count: int) -> FruitScore:
    """
    F12 GRACE (Charis) — Error Tolerance and Recovery
    TIER: structural
    
    Structural property: Edge cases explicitly addressed. Counterexamples
    discussed and resolved or acknowledged. Framework degrades gracefully
    at boundaries. Uncertainty treated as information, not threat.
    """
    edge_cases = count_edge_case_handling(text)
    
    # Error/uncertainty as information (positive framing)
    uncertainty_positive = [
        r'\b(?:uncertainty (?:tells us|reveals|indicates|suggests))\b',
        r'\b(?:error (?:bars?|bounds?) (?:show|indicate|suggest))\b',
        r'\b(?:the (?:gap|unknown|uncertainty) (?:is|represents) (?:itself )?(?:informative|productive|useful))\b',
        r'\b(?:honest(?:ly)? (?:acknowledg|stat|report))\b',
        r'\b(?:we do not (?:yet )?know|remains? (?:open|unresolved|unclear))\b',
    ]
    uncertainty_info = count_regex(text, uncertainty_positive)
    
    # Counterexample engagement
    counter_patterns = [
        r'\b(?:counter[- ]?example|apparent (?:exception|contradiction|failure))\b',
        r'\b(?:this (?:appears? to|seems? to) (?:contradict|violate|challenge).*(?:but|however|yet))\b',
        r'\b(?:one might (?:object|point out|note) that)\b',
        r'\b(?:(?:address|resolv|handl|explain)(?:es?|ing) (?:this|the) (?:objection|challenge|problem))\b',
    ]
    counterexamples = count_regex(text, counter_patterns)
    
    # Mathematical limiting behavior
    limit_patterns = [
        r'\b(?:in the limit|as.*(?:→|approaches|goes to))\b',
        r'\b(?:reduces to|recovers?|degenerates? to)\b',
        r'\b(?:special case|limiting case|boundary (?:case|behavior))\b',
    ]
    limits = count_regex(text, limit_patterns)
    
    # Negative: brittleness under error
    brittle_patterns = [
        r'\b(?:if.*wrong.*(?:everything|entire|all).*(?:collapse|fail|invalid))\b',
        r'\b(?:cannot (?:tolerate|accommodate|handle) (?:any )?error)\b',
        r'\b(?:no room for|zero tolerance for) (?:error|mistake|deviation)\b',
    ]
    brittle = count_regex(text, brittle_patterns)
    
    k = max(word_count / 1000, 1)
    pos = (edge_cases * 2 + uncertainty_info + counterexamples + limits) / k
    neg = brittle * 2 / k
    
    raw = min(pos / 4.0, 1.0) - min(neg / 1.0, 0.5)
    score = max(-1.0, min(1.0, raw))
    
    return FruitScore(
        name="Grace", score=round(score, 3),
        positive_hits=edge_cases + uncertainty_info + counterexamples + limits,
        negative_hits=brittle,
        interpretation=_interpret_score(score), tier="structural",
        details={"edge_case_handling": edge_cases, "uncertainty_as_info": uncertainty_info,
                 "counterexample_engagement": counterexamples, "limiting_behavior": limits,
                 "brittleness_markers": brittle}
    )


# =============================================================================
# SCORE INTERPRETATION HELPERS
# =============================================================================

def _interpret_score(score: float) -> str:
    """Interpret a -1 to +1 fruit score."""
    if score > 0.5:
        return "Strong structural presence"
    elif score > 0.2:
        return "Moderate presence"
    elif score > -0.1:
        return "Weak / insufficient evidence"
    elif score > -0.5:
        return "Moderate structural deficit"
    else:
        return "Strong structural deficit"


def score_to_grade(normalized: float) -> str:
    """Convert normalized score (0-100) to letter grade."""
    if normalized >= 90: return "A"
    elif normalized >= 80: return "A-"
    elif normalized >= 75: return "B+"
    elif normalized >= 70: return "B"
    elif normalized >= 65: return "B-"
    elif normalized >= 60: return "C+"
    elif normalized >= 55: return "C"
    elif normalized >= 50: return "C-"
    elif normalized >= 45: return "D+"
    elif normalized >= 40: return "D"
    elif normalized >= 35: return "D-"
    else: return "F"


def interpret_total(score: float) -> str:
    """Interpret total score (-12 to +12)."""
    if score >= 8: return "Coherence-stable, long-term viable"
    elif score >= 3: return "Partially stable, repairable"
    elif score >= -2: return "Incoherent / incomplete"
    else: return "Entropy-amplifying (will collapse)"


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_theory_fruits(text: str, name: str = "Unknown") -> FruitsAnalysis:
    """
    Analyze a theory using the Fruits of the Spirit structural metrics.
    
    v2: Applies section boundary parsing BEFORE scoring.
    Returns complete FruitsAnalysis with all 12 fruit scores.
    """
    # Phase 1: Parse document zones
    zones = parse_document_zones(text)
    
    # Score on THEORY TEXT ONLY (not critique sections)
    scored_text = zones.theory_text
    word_count = zones.theory_word_count
    
    # Minimum viable text check
    if word_count < 50:
        # Fall back to full text if theory zone too small
        # (document may not have headings)
        scored_text = zones.full_text
        word_count = zones.total_word_count
    
    # Score each fruit on theory text
    f1 = score_f1_love(scored_text, word_count)
    f2 = score_f2_joy(scored_text, word_count)
    f3 = score_f3_peace(scored_text, word_count)
    f4 = score_f4_patience(scored_text, word_count)
    f5 = score_f5_kindness(scored_text, word_count)
    f6 = score_f6_goodness(scored_text, word_count)
    f7 = score_f7_faithfulness(scored_text, word_count)
    f8 = score_f8_gentleness(scored_text, word_count)
    f9 = score_f9_self_control(scored_text, word_count)
    f10 = score_f10_truth(scored_text, word_count)
    f11 = score_f11_wisdom(scored_text, word_count)
    f12 = score_f12_grace(scored_text, word_count)
    
    # Calculate totals
    all_scores = [f1.score, f2.score, f3.score, f4.score, f5.score, f6.score,
                  f7.score, f8.score, f9.score, f10.score, f11.score, f12.score]
    total_score = sum(all_scores)
    
    # Normalize to 0-100 scale (from -12 to +12)
    normalized_score = ((total_score + 12) / 24) * 100
    
    return FruitsAnalysis(
        name=name,
        word_count=word_count,
        f1_grace=f12,     # NOTE: f12_grace maps to the "Grace" slot
        f2_hope=f2,       # Joy/Hope mapped 
        f3_patience=f4,   # Patience
        f4_faithfulness=f7,
        f5_self_control=f9,
        f6_love=f1,
        f7_peace=f3,
        f8_truth=f10,
        f9_humility=f5,   # Kindness/intellectual charity → Humility slot
        f10_goodness=f6,
        f11_unity=f11,    # Wisdom → Unity slot  
        f12_joy=f2,       # Joy
        total_score=round(total_score, 3),
        normalized_score=round(normalized_score, 1),
        grade=score_to_grade(normalized_score),
        interpretation=interpret_total(total_score),
        zones=zones,
        scorer_version="fruits_12_v2"
    )


# =============================================================================
# FILE PROCESSING
# =============================================================================

def process_markdown_file(file_path: Path) -> Optional[FruitsAnalysis]:
    """Process a single markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if len(content.split()) < 50:
            return None
        
        # Remove YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]
        
        name = file_path.stem
        return analyze_theory_fruits(content, name)
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def process_folder(folder_path: Path) -> List[FruitsAnalysis]:
    """Process all markdown files in a folder."""
    results = []
    md_files = list(folder_path.rglob("*.md"))
    
    print(f"Processing {len(md_files)} files...")
    
    for i, file_path in enumerate(md_files):
        try:
            print(f"  [{i+1}/{len(md_files)}] {file_path.name}")
        except UnicodeEncodeError:
            print(f"  [{i+1}/{len(md_files)}] (unicode name)")
        
        result = process_markdown_file(file_path)
        if result:
            results.append(result)
    
    return results


# =============================================================================
# DETAILED DIAGNOSTIC REPORT
# =============================================================================

def generate_diagnostic_report(analysis: FruitsAnalysis) -> str:
    """Generate detailed diagnostic report for a single document."""
    lines = []
    lines.append(f"{'='*70}")
    lines.append(f"FRUITS v2 DIAGNOSTIC: {analysis.name}")
    lines.append(f"{'='*70}")
    lines.append(f"Word count (scored): {analysis.word_count}")
    
    if analysis.zones:
        z = analysis.zones
        lines.append(f"Zones: theory={z.theory_word_count}w, "
                     f"critique={z.critique_word_count}w (excluded), "
                     f"defense={z.defense_word_count}w")
        if z.excluded_sections:
            lines.append(f"Excluded sections: {', '.join(z.excluded_sections)}")
    
    lines.append(f"\nTotal: {analysis.total_score:+.3f} / 12.0")
    lines.append(f"Normalized: {analysis.normalized_score:.1f} / 100")
    lines.append(f"Grade: {analysis.grade}")
    lines.append(f"Status: {analysis.interpretation}")
    lines.append("")
    
    # Individual fruit details
    fruits = [
        ("F1  Love (Integration)", analysis.f6_love),
        ("F2  Joy (Generativity)", analysis.f12_joy),
        ("F3  Peace (Non-Contradiction)", analysis.f7_peace),
        ("F4  Patience (Thoroughness)", analysis.f3_patience),
        ("F5  Kindness (Charity)", analysis.f9_humility),
        ("F6  Goodness (Constructive)", analysis.f10_goodness),
        ("F7  Faithfulness (Rigor)", analysis.f4_faithfulness),
        ("F8  Gentleness (Modularity)", analysis.f1_grace),  
        ("F9  Self-Control (Bounding)", analysis.f5_self_control),
        ("F10 Truth (Evidence)", analysis.f8_truth),
        ("F11 Wisdom (Hierarchy)", analysis.f11_unity),
        ("F12 Grace (Error Tolerance)", analysis.f1_grace),
    ]
    
    lines.append(f"{'Fruit':<32} {'Score':>7} {'Tier':<12} {'+':<4} {'-':<4} Interpretation")
    lines.append("-" * 90)
    
    for label, fs in fruits:
        if fs:
            lines.append(f"{label:<32} {fs.score:>+7.3f} [{fs.tier:<10}] "
                        f"{fs.positive_hits:<4} {fs.negative_hits:<4} {fs.interpretation}")
            if fs.details:
                for k, v in fs.details.items():
                    lines.append(f"    {k}: {v}")
    
    return "\n".join(lines)


# =============================================================================
# COMPARISON REPORT (v1-compatible)
# =============================================================================

def generate_fruits_report(theophysics: List[FruitsAnalysis],
                           external: List[FruitsAnalysis],
                           output_path: Path):
    """Generate comprehensive Fruits comparison report (v1-compatible format)."""
    
    report = []
    report.append("=" * 80)
    report.append("FRUITS OF THE SPIRIT v2 - STRUCTURAL INVARIANT EVALUATION REPORT")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Scorer: fruits_scorer_v2 (structural detection, section-boundary-aware)")
    report.append("")
    report.append("These metrics measure STRUCTURAL PROPERTIES of documents:")
    report.append("  Definitions, derivations, scope bounding, evidence density,")
    report.append("  modularity, edge case handling — not keyword sentiment.")
    report.append("")
    
    report.append("-" * 80)
    report.append("OVERVIEW")
    report.append("-" * 80)
    report.append(f"Theophysics Documents: {len(theophysics)}")
    report.append(f"External Theories: {len(external)}")
    
    # Section boundary stats
    theo_excluded = sum(1 for t in theophysics if t.zones and t.zones.critique_word_count > 0)
    report.append(f"Theophysics docs with critique sections excluded: {theo_excluded}")
    report.append("")
    
    def avg_fruit(analyses, attr):
        if not analyses: return 0
        return sum(getattr(getattr(a, attr), 'score') for a in analyses) / len(analyses)
    
    def avg_total(analyses):
        if not analyses: return 0
        return sum(a.total_score for a in analyses) / len(analyses)
    
    def avg_normalized(analyses):
        if not analyses: return 0
        return sum(a.normalized_score for a in analyses) / len(analyses)
    
    # Comparison table
    report.append("-" * 80)
    report.append("STRUCTURAL METRIC COMPARISON")
    report.append("-" * 80)
    report.append(f"{'Fruit':<25} {'Theophysics':>12} {'External':>12} {'Winner':>10}")
    report.append("-" * 80)
    
    fruits = [
        ("F1 - Grace/ErrorTol", "f1_grace"),
        ("F2 - Joy/Generativity", "f2_hope"),
        ("F3 - Patience/Thorough", "f3_patience"),
        ("F4 - Faithfulness/Rigor", "f4_faithfulness"),
        ("F5 - Self-Control/Scope", "f5_self_control"),
        ("F6 - Love/Integration", "f6_love"),
        ("F7 - Peace/Consistency", "f7_peace"),
        ("F8 - Truth/Evidence", "f8_truth"),
        ("F9 - Kindness/Charity", "f9_humility"),
        ("F10 - Goodness/Value", "f10_goodness"),
        ("F11 - Wisdom/Hierarchy", "f11_unity"),
        ("F12 - Joy/Feedback", "f12_joy"),
    ]
    
    theo_wins = 0
    ext_wins = 0
    
    for label, attr in fruits:
        theo_val = avg_fruit(theophysics, attr)
        ext_val = avg_fruit(external, attr)
        
        if theo_val > ext_val + 0.01:
            winner = "THEO"
            theo_wins += 1
        elif ext_val > theo_val + 0.01:
            winner = "EXT"
            ext_wins += 1
        else:
            winner = "TIE"
        
        report.append(f"{label:<25} {theo_val:>12.3f} {ext_val:>12.3f} {winner:>10}")
    
    report.append("-" * 80)
    report.append(f"{'TOTAL SCORE':<25} {avg_total(theophysics):>12.3f} {avg_total(external):>12.3f}")
    report.append(f"{'NORMALIZED (0-100)':<25} {avg_normalized(theophysics):>12.1f} {avg_normalized(external):>12.1f}")
    report.append(f"{'WINS':<25} {theo_wins:>12} {ext_wins:>12}")
    report.append("")
    
    # Top performers
    report.append("-" * 80)
    report.append("TOP 15 THEOPHYSICS BY STRUCTURAL SCORE")
    report.append("-" * 80)
    
    theo_sorted = sorted(theophysics, key=lambda x: x.total_score, reverse=True)
    for i, a in enumerate(theo_sorted[:15]):
        try:
            report.append(f"  {i+1:2}. {a.name[:40]:<42} {a.total_score:>6.2f} ({a.grade})")
        except:
            report.append(f"  {i+1:2}. (name error) {a.total_score:>6.2f} ({a.grade})")
    
    report.append("")
    report.append("-" * 80)
    report.append("TOP 15 EXTERNAL BY STRUCTURAL SCORE")
    report.append("-" * 80)
    
    ext_sorted = sorted(external, key=lambda x: x.total_score, reverse=True)
    for i, a in enumerate(ext_sorted[:15]):
        try:
            report.append(f"  {i+1:2}. {a.name[:40]:<42} {a.total_score:>6.2f} ({a.grade})")
        except:
            report.append(f"  {i+1:2}. (name error) {a.total_score:>6.2f} ({a.grade})")
    
    # Summary
    report.append("")
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    
    theo_avg = avg_normalized(theophysics)
    ext_avg = avg_normalized(external)
    
    report.append(f"Theophysics Average: {theo_avg:.1f}/100 ({score_to_grade(theo_avg)})")
    report.append(f"External Average: {ext_avg:.1f}/100 ({score_to_grade(ext_avg)})")
    report.append("")
    
    if theo_avg > ext_avg:
        report.append(f"RESULT: Theophysics is {theo_avg - ext_avg:.1f} points MORE STRUCTURALLY COHERENT")
    else:
        report.append(f"RESULT: External is {ext_avg - theo_avg:.1f} points more structurally coherent")
    
    report.append(f"Theophysics wins {theo_wins} of 12 structural metrics")
    report.append("=" * 80)
    
    # Write
    report_text = "\n".join(report)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    with open(output_path / "fruits_v2_report.txt", 'w', encoding='utf-8') as f:
        f.write(report_text)
    
    # JSON export
    def analysis_to_dict(a):
        return {
            "name": a.name,
            "word_count": a.word_count,
            "total_score": a.total_score,
            "normalized_score": a.normalized_score,
            "grade": a.grade,
            "interpretation": a.interpretation,
            "scorer_version": a.scorer_version,
            "zones": {
                "theory_words": a.zones.theory_word_count if a.zones else a.word_count,
                "critique_words": a.zones.critique_word_count if a.zones else 0,
                "excluded_sections": a.zones.excluded_sections if a.zones else []
            },
            "fruits": {
                "grace": a.f1_grace.score if a.f1_grace else 0,
                "hope": a.f2_hope.score if a.f2_hope else 0,
                "patience": a.f3_patience.score if a.f3_patience else 0,
                "faithfulness": a.f4_faithfulness.score if a.f4_faithfulness else 0,
                "self_control": a.f5_self_control.score if a.f5_self_control else 0,
                "love": a.f6_love.score if a.f6_love else 0,
                "peace": a.f7_peace.score if a.f7_peace else 0,
                "truth": a.f8_truth.score if a.f8_truth else 0,
                "humility": a.f9_humility.score if a.f9_humility else 0,
                "goodness": a.f10_goodness.score if a.f10_goodness else 0,
                "unity": a.f11_unity.score if a.f11_unity else 0,
                "joy": a.f12_joy.score if a.f12_joy else 0,
            }
        }
    
    json_data = {
        "generated_at": datetime.now().isoformat(),
        "scorer_version": "fruits_12_v2",
        "theophysics_count": len(theophysics),
        "external_count": len(external),
        "theophysics_avg": theo_avg,
        "external_avg": ext_avg,
        "theo_wins": theo_wins,
        "ext_wins": ext_wins,
        "theophysics": [analysis_to_dict(a) for a in theo_sorted],
        "external": [analysis_to_dict(a) for a in ext_sorted]
    }
    
    with open(output_path / "fruits_v2_data.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    
    try:
        print(report_text)
    except UnicodeEncodeError:
        print(report_text.encode('ascii', 'replace').decode())
    
    print(f"\nReport: {output_path / 'fruits_v2_report.txt'}")
    print(f"JSON:   {output_path / 'fruits_v2_data.json'}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Portable defaults with env overrides.
    theo_folder = Path(
        os.environ.get(
            "THEO_FRUITS_THEO_FOLDER",
            r"O:\_Theophysics_v3\MASTER_EQ_CONSOLIDATED",
        )
    )
    ext_folder = Path(
        os.environ.get(
            "THEO_FRUITS_EXT_FOLDER",
            r"O:\999_IGNORE\Obsidian Data Analytics",
        )
    )
    output_path = Path(
        os.environ.get(
            "THEO_FRUITS_OUTPUT_PATH",
            r"O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\_health\fruits_output",
        )
    )
    
    # Allow single-file diagnostic mode
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            print(f"Single-file diagnostic: {target.name}")
            print("=" * 70)
            result = process_markdown_file(target)
            if result:
                print(generate_diagnostic_report(result))
            else:
                print("File too short or could not be processed.")
            sys.exit(0)
    
    print("=" * 60)
    print("FRUITS OF THE SPIRIT v2 - STRUCTURAL INVARIANT ENGINE")
    print("=" * 60)
    print()
    
    print("Analyzing Theophysics documents...")
    theo_results = process_folder(theo_folder)
    print(f"Analyzed {len(theo_results)} Theophysics documents")
    print()
    
    print("Analyzing External theories...")
    ext_results = process_folder(ext_folder)
    print(f"Analyzed {len(ext_results)} External theories")
    print()
    
    print("Generating comparison report...")
    generate_fruits_report(theo_results, ext_results, output_path)
