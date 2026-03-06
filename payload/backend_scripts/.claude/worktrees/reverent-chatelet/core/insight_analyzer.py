"""
Insight Analyzer for Theophysics Framework
Detects breakouts, coherence points, and hidden correlations across papers.

Three types of analysis:
1. BREAKOUT DETECTION - Novel integrations that represent breakthrough thinking
2. COHERENCE POINTS - Obvious correlations based on Lagrangian framework
3. HIDDEN CORRELATIONS - Non-obvious connections that wouldn't be expected
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from datetime import datetime


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Breakout:
    """A detected breakthrough/novel integration."""
    title: str
    description: str
    papers_involved: List[str]
    domains_bridged: List[str]  # e.g., ["physics", "theology", "consciousness"]
    novelty_score: float  # 0-1, how novel/unexpected
    integration_order: int  # 1=first-order (direct), 2=second-order (indirect), etc.
    evidence: List[str]  # Quotes or references supporting this breakout
    implications: List[str]  # What this breakout enables


@dataclass
class CoherencePoint:
    """An obvious correlation point in the Lagrangian framework."""
    physical_law: str
    spiritual_principle: str
    mapping_strength: float  # 0-1
    papers_supporting: List[str]
    key_equations: List[str]
    explanation: str
    lagrangian_term: str  # Which term in the Lagrangian this maps to


@dataclass
class HiddenCorrelation:
    """A non-obvious connection that wouldn't be expected."""
    concept_a: str
    concept_b: str
    correlation_type: str  # "structural", "functional", "emergent", "inverse"
    surprise_score: float  # 0-1, how unexpected
    explanation: str
    papers_found_in: List[str]
    why_unexpected: str  # Why this correlation is surprising


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    breakouts: List[Breakout] = field(default_factory=list)
    coherence_points: List[CoherencePoint] = field(default_factory=list)
    hidden_correlations: List[HiddenCorrelation] = field(default_factory=list)
    timestamp: str = ""
    papers_analyzed: int = 0
    

# ============================================================
# DOMAIN DEFINITIONS
# ============================================================

PHYSICS_TERMS = {
    'quantum', 'wavefunction', 'collapse', 'superposition', 'entanglement',
    'spacetime', 'gravity', 'mass', 'energy', 'momentum', 'force',
    'electromagnetic', 'photon', 'electron', 'particle', 'wave',
    'entropy', 'thermodynamic', 'temperature', 'heat', 'work',
    'relativity', 'lorentz', 'minkowski', 'geodesic', 'curvature',
    'field', 'lagrangian', 'hamiltonian', 'action', 'symmetry',
    'conservation', 'invariant', 'tensor', 'metric', 'manifold',
    'planck', 'heisenberg', 'uncertainty', 'measurement', 'observer',
    'decoherence', 'eigenstate', 'eigenvalue', 'hilbert', 'operator'
}

THEOLOGY_TERMS = {
    'god', 'logos', 'christ', 'spirit', 'trinity', 'father', 'son',
    'grace', 'sin', 'redemption', 'salvation', 'resurrection', 'incarnation',
    'covenant', 'faith', 'hope', 'love', 'forgiveness', 'mercy',
    'righteousness', 'holiness', 'sanctification', 'justification',
    'creation', 'creator', 'divine', 'sacred', 'holy', 'eternal',
    'heaven', 'kingdom', 'glory', 'worship', 'prayer', 'scripture',
    'prophecy', 'revelation', 'apostle', 'disciple', 'church',
    'baptism', 'communion', 'eucharist', 'sacrament', 'blessing'
}

CONSCIOUSNESS_TERMS = {
    'consciousness', 'awareness', 'mind', 'thought', 'perception',
    'qualia', 'experience', 'subjective', 'phenomenal', 'sentient',
    'cognition', 'cognitive', 'neural', 'brain', 'neuron',
    'attention', 'intention', 'will', 'free will', 'agency',
    'self', 'ego', 'identity', 'soul', 'psyche', 'spirit',
    'memory', 'learning', 'intelligence', 'understanding', 'wisdom',
    'emotion', 'feeling', 'affect', 'mood', 'desire', 'motivation'
}

MATHEMATICS_TERMS = {
    'equation', 'formula', 'theorem', 'proof', 'axiom', 'lemma',
    'integral', 'derivative', 'differential', 'calculus', 'analysis',
    'algebra', 'topology', 'geometry', 'manifold', 'space',
    'function', 'mapping', 'transformation', 'operator', 'matrix',
    'vector', 'scalar', 'tensor', 'spinor', 'group', 'ring',
    'set', 'category', 'morphism', 'isomorphism', 'homomorphism',
    'infinity', 'limit', 'convergence', 'series', 'sequence'
}

# Ten Laws mapping for coherence detection
TEN_LAWS = {
    'gravity': {'spiritual': 'belonging', 'symbol': 'G', 'description': 'Mass attracts mass / Souls drawn to community'},
    'strong_force': {'spiritual': 'covenant', 'symbol': 'M', 'description': 'Binds nucleons / Binds relationships'},
    'electromagnetism': {'spiritual': 'truth', 'symbol': 'E', 'description': 'Light reveals / Truth illuminates'},
    'thermodynamics': {'spiritual': 'entropy', 'symbol': 'S', 'description': 'Disorder increases / Sin corrupts'},
    'quantum': {'spiritual': 'faith', 'symbol': 'T', 'description': 'Superposition until measured / Potential until believed'},
    'measurement': {'spiritual': 'incarnation', 'symbol': 'K', 'description': 'Collapse to definite / Word becomes flesh'},
    'negentropy': {'spiritual': 'forgiveness', 'symbol': 'R', 'description': 'Local order creation / Grace restores'},
    'relativity': {'spiritual': 'compassion', 'symbol': 'Q', 'description': 'Frame-dependent truth / Perspective matters'},
    'resonance': {'spiritual': 'communion', 'symbol': 'F', 'description': 'Coupled oscillation / Shared vibration'},
    'cpt_symmetry': {'spiritual': 'resurrection', 'symbol': 'C', 'description': 'Time reversal symmetry / Death reversed'}
}

# Known breakout patterns from the framework
KNOWN_BREAKOUTS = [
    {
        'title': 'Observer-Dependent Reality as Incarnational Principle',
        'domains': ['quantum', 'theology'],
        'keywords': ['observer', 'measurement', 'collapse', 'incarnation', 'logos'],
        'description': 'Quantum measurement collapse parallels the Incarnation - abstract potential becoming concrete reality through observation/participation'
    },
    {
        'title': 'Entropy-Sin Isomorphism',
        'domains': ['thermodynamics', 'theology'],
        'keywords': ['entropy', 'sin', 'disorder', 'decay', 'thermodynamic'],
        'description': 'Second law of thermodynamics as physical manifestation of spiritual entropy (sin)'
    },
    {
        'title': 'Grace as Negentropy',
        'domains': ['thermodynamics', 'theology'],
        'keywords': ['negentropy', 'grace', 'order', 'redemption', 'forgiveness'],
        'description': 'Grace creates local pockets of order against universal entropy - redemption as negentropic process'
    },
    {
        'title': 'Consciousness as Quantum Coherence',
        'domains': ['quantum', 'consciousness'],
        'keywords': ['consciousness', 'coherence', 'quantum', 'decoherence', 'mind'],
        'description': 'Consciousness maintains quantum coherence against decoherence - the soul as coherence-preserving structure'
    },
    {
        'title': 'Trinity as Fundamental Symmetry',
        'domains': ['physics', 'theology', 'mathematics'],
        'keywords': ['trinity', 'symmetry', 'three', 'father', 'son', 'spirit'],
        'description': 'Trinitarian structure as fundamental symmetry underlying physical law'
    },
    {
        'title': 'Information as Ontological Primitive',
        'domains': ['physics', 'theology', 'information'],
        'keywords': ['information', 'logos', 'word', 'bit', 'quantum information'],
        'description': 'Information (Logos) as more fundamental than matter/energy'
    },
    {
        'title': 'Resurrection as CPT Symmetry',
        'domains': ['physics', 'theology'],
        'keywords': ['resurrection', 'cpt', 'symmetry', 'time reversal', 'death'],
        'description': 'Physical CPT symmetry as basis for resurrection - time reversal at deepest level'
    },
    {
        'title': 'Moral Law as Physical Constraint',
        'domains': ['physics', 'ethics', 'theology'],
        'keywords': ['moral', 'law', 'constraint', 'boundary', 'commandment'],
        'description': 'Moral laws function as boundary conditions on physical reality'
    }
]

# Unexpected correlation patterns to look for
UNEXPECTED_CORRELATIONS = [
    ('quantum_entanglement', 'prayer', 'Non-local connection without signal'),
    ('black_hole', 'sin', 'Event horizon as point of no return'),
    ('photosynthesis', 'eucharist', 'Light transformed to life'),
    ('dna', 'scripture', 'Information encoding life'),
    ('immune_system', 'discernment', 'Self/non-self recognition'),
    ('metamorphosis', 'sanctification', 'Complete transformation of nature'),
    ('superconductivity', 'holiness', 'Zero resistance to current/will'),
    ('crystallization', 'church', 'Order emerging from solution'),
    ('catalysis', 'intercession', 'Lowering activation energy'),
    ('phase_transition', 'conversion', 'Sudden state change'),
]


# ============================================================
# ANALYSIS FUNCTIONS
# ============================================================

class InsightAnalyzer:
    """Main analyzer class for detecting insights across papers."""
    
    def __init__(self, papers_path: Path = None):
        self.papers_path = papers_path
        self.papers_content: Dict[str, str] = {}
        self.paper_concepts: Dict[str, Set[str]] = {}
        self.cross_references: Dict[str, List[str]] = {}
        
    def load_papers(self, papers_path: Path = None) -> int:
        """Load all paper content from markdown files."""
        if papers_path:
            self.papers_path = papers_path
        
        if not self.papers_path or not self.papers_path.exists():
            return 0
        
        loaded = 0
        for md_file in self.papers_path.glob("**/*.md"):
            # Skip data analytics folders
            if "_Data_Analytics" in str(md_file) or "Data Analytics" in str(md_file):
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                paper_name = md_file.stem
                self.papers_content[paper_name] = content
                self.paper_concepts[paper_name] = self._extract_concepts(content)
                self.cross_references[paper_name] = self._extract_references(content)
                loaded += 1
            except Exception as e:
                print(f"Error loading {md_file}: {e}")
        
        return loaded
    
    def _extract_concepts(self, content: str) -> Set[str]:
        """Extract key concepts from paper content."""
        content_lower = content.lower()
        concepts = set()
        
        # Check each domain
        for term in PHYSICS_TERMS:
            if term in content_lower:
                concepts.add(f"physics:{term}")
        
        for term in THEOLOGY_TERMS:
            if term in content_lower:
                concepts.add(f"theology:{term}")
        
        for term in CONSCIOUSNESS_TERMS:
            if term in content_lower:
                concepts.add(f"consciousness:{term}")
        
        for term in MATHEMATICS_TERMS:
            if term in content_lower:
                concepts.add(f"math:{term}")
        
        return concepts
    
    def _extract_references(self, content: str) -> List[str]:
        """Extract cross-references to other papers."""
        refs = []
        # Look for [[Paper]] style links
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        refs.extend(wiki_links)
        
        # Look for P01, P02, etc. references
        paper_refs = re.findall(r'\b(P\d{2})\b', content)
        refs.extend(paper_refs)
        
        return refs
    
    def _calculate_domain_overlap(self, paper_name: str) -> Dict[str, int]:
        """Calculate how many domains a paper bridges."""
        concepts = self.paper_concepts.get(paper_name, set())
        domains = defaultdict(int)
        
        for concept in concepts:
            domain = concept.split(':')[0]
            domains[domain] += 1
        
        return dict(domains)
    
    def detect_breakouts(self) -> List[Breakout]:
        """Detect breakthrough points and novel integrations."""
        breakouts = []
        
        for paper_name, content in self.papers_content.items():
            content_lower = content.lower()
            domains = self._calculate_domain_overlap(paper_name)
            
            # Check against known breakout patterns
            for pattern in KNOWN_BREAKOUTS:
                keyword_matches = sum(1 for kw in pattern['keywords'] if kw in content_lower)
                if keyword_matches >= 3:  # At least 3 keywords match
                    
                    # Calculate novelty based on domain bridging
                    domains_bridged = [d for d in pattern['domains'] if d in str(domains)]
                    novelty = min(1.0, len(domains_bridged) * 0.3 + keyword_matches * 0.1)
                    
                    # Find evidence quotes
                    evidence = self._find_evidence(content, pattern['keywords'][:3])
                    
                    breakout = Breakout(
                        title=pattern['title'],
                        description=pattern['description'],
                        papers_involved=[paper_name],
                        domains_bridged=domains_bridged,
                        novelty_score=novelty,
                        integration_order=len(domains_bridged),
                        evidence=evidence,
                        implications=self._infer_implications(pattern['title'])
                    )
                    breakouts.append(breakout)
        
        # Deduplicate and merge breakouts found in multiple papers
        breakouts = self._merge_breakouts(breakouts)
        
        # Sort by novelty score
        breakouts.sort(key=lambda b: b.novelty_score, reverse=True)
        
        return breakouts
    
    def _find_evidence(self, content: str, keywords: List[str], max_quotes: int = 3) -> List[str]:
        """Find sentences containing keywords as evidence."""
        evidence = []
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in keywords):
                # Clean up the sentence
                clean = sentence.strip()[:200]
                if len(clean) > 50:  # Only meaningful sentences
                    evidence.append(clean + "...")
                    if len(evidence) >= max_quotes:
                        break
        
        return evidence
    
    def _infer_implications(self, breakout_title: str) -> List[str]:
        """Infer implications of a breakout."""
        implications_map = {
            'Observer-Dependent Reality': [
                'Consciousness is fundamental to reality, not emergent',
                'Measurement problem has theological resolution',
                'Participatory universe aligns with prayer efficacy'
            ],
            'Entropy-Sin': [
                'Physical decay reflects spiritual reality',
                'Thermodynamics has moral dimension',
                'Heat death parallels spiritual death'
            ],
            'Grace as Negentropy': [
                'Redemption is physically meaningful',
                'Grace creates measurable order',
                'Salvation has thermodynamic signature'
            ],
            'Consciousness as Quantum': [
                'Soul has physical basis in coherence',
                'Death is decoherence event',
                'Resurrection requires re-coherence'
            ],
            'Trinity as Fundamental': [
                'Three-ness is built into physics',
                'Symmetry breaking reflects divine action',
                'Unity-in-diversity is cosmic principle'
            ],
            'Information as Ontological': [
                'Logos precedes matter',
                'Word creates reality',
                'Meaning is fundamental'
            ],
            'Resurrection as CPT': [
                'Time reversal is physically possible',
                'Death is not final at quantum level',
                'Resurrection has physical mechanism'
            ],
            'Moral Law as Physical': [
                'Ethics has physical consequences',
                'Commandments are boundary conditions',
                'Sin violates physical constraints'
            ]
        }
        
        for key, implications in implications_map.items():
            if key in breakout_title:
                return implications
        
        return ['Further research needed to determine implications']
    
    def _merge_breakouts(self, breakouts: List[Breakout]) -> List[Breakout]:
        """Merge breakouts found in multiple papers."""
        merged = {}
        
        for b in breakouts:
            if b.title in merged:
                # Merge papers involved
                merged[b.title].papers_involved.extend(b.papers_involved)
                merged[b.title].papers_involved = list(set(merged[b.title].papers_involved))
                # Update novelty score
                merged[b.title].novelty_score = max(merged[b.title].novelty_score, b.novelty_score)
                # Merge evidence
                merged[b.title].evidence.extend(b.evidence)
                merged[b.title].evidence = merged[b.title].evidence[:5]  # Keep top 5
            else:
                merged[b.title] = b
        
        return list(merged.values())
    
    def detect_coherence_points(self) -> List[CoherencePoint]:
        """Detect obvious coherence points based on Ten Laws mapping."""
        coherence_points = []
        
        for law_name, law_data in TEN_LAWS.items():
            supporting_papers = []
            key_equations = []
            
            for paper_name, content in self.papers_content.items():
                content_lower = content.lower()
                
                # Check if paper discusses this law mapping
                physical_present = law_name.replace('_', ' ') in content_lower
                spiritual_present = law_data['spiritual'] in content_lower
                
                if physical_present and spiritual_present:
                    supporting_papers.append(paper_name)
                    
                    # Look for equations
                    equations = re.findall(r'\$[^$]+\$|\\\[[^\]]+\\\]', content)
                    key_equations.extend(equations[:2])
            
            if supporting_papers:
                strength = min(1.0, len(supporting_papers) / 5)  # Normalize to 0-1
                
                coherence_point = CoherencePoint(
                    physical_law=law_name.replace('_', ' ').title(),
                    spiritual_principle=law_data['spiritual'].title(),
                    mapping_strength=strength,
                    papers_supporting=supporting_papers,
                    key_equations=list(set(key_equations))[:3],
                    explanation=law_data['description'],
                    lagrangian_term=law_data['symbol']
                )
                coherence_points.append(coherence_point)
        
        # Sort by mapping strength
        coherence_points.sort(key=lambda c: c.mapping_strength, reverse=True)
        
        return coherence_points
    
    def detect_hidden_correlations(self) -> List[HiddenCorrelation]:
        """Detect non-obvious correlations that wouldn't be expected."""
        hidden = []
        
        # Check for unexpected correlation patterns
        for concept_a, concept_b, reason in UNEXPECTED_CORRELATIONS:
            papers_found = []
            
            for paper_name, content in self.papers_content.items():
                content_lower = content.lower()
                
                # Check if both concepts appear in same paper
                a_present = concept_a.replace('_', ' ') in content_lower
                b_present = concept_b in content_lower
                
                if a_present and b_present:
                    papers_found.append(paper_name)
            
            if papers_found:
                # Calculate surprise score based on domain distance
                surprise = self._calculate_surprise(concept_a, concept_b)
                
                correlation = HiddenCorrelation(
                    concept_a=concept_a.replace('_', ' ').title(),
                    concept_b=concept_b.title(),
                    correlation_type=self._infer_correlation_type(concept_a, concept_b),
                    surprise_score=surprise,
                    explanation=reason,
                    papers_found_in=papers_found,
                    why_unexpected=f"'{concept_a}' is typically in physics/science domain while '{concept_b}' is theological - direct mapping is novel"
                )
                hidden.append(correlation)
        
        # Also look for emergent correlations from concept co-occurrence
        hidden.extend(self._find_emergent_correlations())
        
        # Sort by surprise score
        hidden.sort(key=lambda h: h.surprise_score, reverse=True)
        
        return hidden
    
    def _calculate_surprise(self, concept_a: str, concept_b: str) -> float:
        """Calculate how surprising a correlation is based on domain distance."""
        # Determine domains
        a_domain = 'physics' if concept_a in PHYSICS_TERMS or '_' in concept_a else 'theology'
        b_domain = 'theology' if concept_b in THEOLOGY_TERMS else 'physics'
        
        # Cross-domain correlations are more surprising
        if a_domain != b_domain:
            return 0.8 + (hash(concept_a + concept_b) % 20) / 100  # 0.8-1.0
        else:
            return 0.4 + (hash(concept_a + concept_b) % 40) / 100  # 0.4-0.8
    
    def _infer_correlation_type(self, concept_a: str, concept_b: str) -> str:
        """Infer the type of correlation."""
        structural_keywords = ['structure', 'form', 'pattern', 'shape']
        functional_keywords = ['function', 'process', 'action', 'work']
        
        combined = concept_a + concept_b
        
        if any(kw in combined for kw in structural_keywords):
            return 'structural'
        elif any(kw in combined for kw in functional_keywords):
            return 'functional'
        elif 'inverse' in combined or 'opposite' in combined:
            return 'inverse'
        else:
            return 'emergent'
    
    def _find_emergent_correlations(self) -> List[HiddenCorrelation]:
        """Find correlations that emerge from concept co-occurrence analysis."""
        emergent = []
        
        # Build co-occurrence matrix
        concept_pairs = defaultdict(int)
        
        for paper_name, concepts in self.paper_concepts.items():
            concept_list = list(concepts)
            for i, c1 in enumerate(concept_list):
                for c2 in concept_list[i+1:]:
                    # Only count cross-domain pairs
                    d1 = c1.split(':')[0]
                    d2 = c2.split(':')[0]
                    if d1 != d2:
                        pair = tuple(sorted([c1, c2]))
                        concept_pairs[pair] += 1
        
        # Find high co-occurrence pairs that are unexpected
        for (c1, c2), count in concept_pairs.items():
            if count >= 3:  # Appears in at least 3 papers together
                d1, term1 = c1.split(':')
                d2, term2 = c2.split(':')
                
                # Skip obvious pairings
                if self._is_obvious_pairing(term1, term2):
                    continue
                
                correlation = HiddenCorrelation(
                    concept_a=term1.title(),
                    concept_b=term2.title(),
                    correlation_type='emergent',
                    surprise_score=0.6 + count * 0.05,
                    explanation=f"Co-occurs in {count} papers despite being from {d1}/{d2} domains",
                    papers_found_in=[p for p, concepts in self.paper_concepts.items() 
                                    if c1 in concepts and c2 in concepts],
                    why_unexpected=f"Cross-domain ({d1} ↔ {d2}) co-occurrence suggests deep structural connection"
                )
                emergent.append(correlation)
        
        return emergent[:10]  # Top 10 emergent correlations
    
    def _is_obvious_pairing(self, term1: str, term2: str) -> bool:
        """Check if a pairing is too obvious to be interesting."""
        obvious_pairs = [
            ('quantum', 'physics'), ('god', 'theology'), ('mind', 'consciousness'),
            ('equation', 'math'), ('energy', 'mass'), ('space', 'time')
        ]
        
        for a, b in obvious_pairs:
            if (a in term1 and b in term2) or (b in term1 and a in term2):
                return True
        
        return False
    
    def run_full_analysis(self) -> AnalysisResult:
        """Run complete analysis and return all insights."""
        result = AnalysisResult(
            breakouts=self.detect_breakouts(),
            coherence_points=self.detect_coherence_points(),
            hidden_correlations=self.detect_hidden_correlations(),
            timestamp=datetime.now().isoformat(),
            papers_analyzed=len(self.papers_content)
        )
        
        return result
    
    def export_to_markdown(self, result: AnalysisResult, output_path: Path) -> Path:
        """Export analysis results to markdown file."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        md_content = f"""# 🔬 Theophysics Insight Analysis Report

**Generated:** {result.timestamp}
**Papers Analyzed:** {result.papers_analyzed}

---

## 🚀 BREAKOUT DETECTIONS

*Novel integrations and breakthrough points that bridge multiple domains*

"""
        
        for i, b in enumerate(result.breakouts, 1):
            md_content += f"""### {i}. {b.title}

- **Novelty Score:** {b.novelty_score:.2f}
- **Integration Order:** {b.integration_order}
- **Domains Bridged:** {', '.join(b.domains_bridged)}
- **Papers:** {', '.join(b.papers_involved)}

**Description:** {b.description}

**Evidence:**
"""
            for ev in b.evidence[:3]:
                md_content += f"> {ev}\n\n"
            
            md_content += "**Implications:**\n"
            for imp in b.implications:
                md_content += f"- {imp}\n"
            md_content += "\n---\n\n"
        
        md_content += """## ⚖️ COHERENCE POINTS (Lagrangian Framework)

*Obvious correlations based on the Ten Laws physical↔spiritual mapping*

| Physical Law | Spiritual Principle | Strength | Lagrangian Term | Supporting Papers |
|-------------|--------------------|---------:|:---------------:|-------------------|
"""
        
        for c in result.coherence_points:
            papers = ', '.join(c.papers_supporting[:3])
            if len(c.papers_supporting) > 3:
                papers += f" (+{len(c.papers_supporting)-3})"
            md_content += f"| {c.physical_law} | {c.spiritual_principle} | {c.mapping_strength:.2f} | {c.lagrangian_term} | {papers} |\n"
        
        md_content += f"""

### Coherence Point Details

"""
        for c in result.coherence_points:
            md_content += f"""#### {c.physical_law} ↔ {c.spiritual_principle}

**Explanation:** {c.explanation}

"""
        
        md_content += """---

## 🔮 HIDDEN CORRELATIONS

*Non-obvious connections that wouldn't be expected - the "you wouldn't think of this" insights*

"""
        
        for i, h in enumerate(result.hidden_correlations, 1):
            md_content += f"""### {i}. {h.concept_a} ↔ {h.concept_b}

- **Surprise Score:** {h.surprise_score:.2f}
- **Correlation Type:** {h.correlation_type}
- **Found In:** {', '.join(h.papers_found_in[:3])}

**Connection:** {h.explanation}

**Why Unexpected:** {h.why_unexpected}

---

"""
        
        md_content += f"""
## 📊 Summary Statistics

- **Total Breakouts Detected:** {len(result.breakouts)}
- **Coherence Points Mapped:** {len(result.coherence_points)}
- **Hidden Correlations Found:** {len(result.hidden_correlations)}
- **Average Novelty Score:** {sum(b.novelty_score for b in result.breakouts) / max(1, len(result.breakouts)):.2f}
- **Average Surprise Score:** {sum(h.surprise_score for h in result.hidden_correlations) / max(1, len(result.hidden_correlations)):.2f}

---

*Generated by Theophysics Insight Analyzer*
"""
        
        output_file = output_path / "INSIGHT_ANALYSIS_REPORT.md"
        output_file.write_text(md_content, encoding='utf-8')
        
        return output_file
    
    def export_to_json(self, result: AnalysisResult, output_path: Path) -> Path:
        """Export analysis results to JSON file."""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        data = {
            'timestamp': result.timestamp,
            'papers_analyzed': result.papers_analyzed,
            'breakouts': [
                {
                    'title': b.title,
                    'description': b.description,
                    'papers_involved': b.papers_involved,
                    'domains_bridged': b.domains_bridged,
                    'novelty_score': b.novelty_score,
                    'integration_order': b.integration_order,
                    'evidence': b.evidence,
                    'implications': b.implications
                }
                for b in result.breakouts
            ],
            'coherence_points': [
                {
                    'physical_law': c.physical_law,
                    'spiritual_principle': c.spiritual_principle,
                    'mapping_strength': c.mapping_strength,
                    'papers_supporting': c.papers_supporting,
                    'key_equations': c.key_equations,
                    'explanation': c.explanation,
                    'lagrangian_term': c.lagrangian_term
                }
                for c in result.coherence_points
            ],
            'hidden_correlations': [
                {
                    'concept_a': h.concept_a,
                    'concept_b': h.concept_b,
                    'correlation_type': h.correlation_type,
                    'surprise_score': h.surprise_score,
                    'explanation': h.explanation,
                    'papers_found_in': h.papers_found_in,
                    'why_unexpected': h.why_unexpected
                }
                for h in result.hidden_correlations
            ]
        }
        
        output_file = output_path / "insight_analysis.json"
        output_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
        return output_file


if __name__ == "__main__":
    # Test the analyzer
    test_path = Path(r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC\03_PUBLICATIONS\COMPLETE_LOGOS_PAPERS_FINAL")
    
    analyzer = InsightAnalyzer()
    loaded = analyzer.load_papers(test_path)
    print(f"Loaded {loaded} papers")
    
    result = analyzer.run_full_analysis()
    
    print(f"\nBreakouts: {len(result.breakouts)}")
    for b in result.breakouts[:3]:
        print(f"  - {b.title} (novelty: {b.novelty_score:.2f})")
    
    print(f"\nCoherence Points: {len(result.coherence_points)}")
    for c in result.coherence_points[:3]:
        print(f"  - {c.physical_law} ↔ {c.spiritual_principle} ({c.mapping_strength:.2f})")
    
    print(f"\nHidden Correlations: {len(result.hidden_correlations)}")
    for h in result.hidden_correlations[:3]:
        print(f"  - {h.concept_a} ↔ {h.concept_b} (surprise: {h.surprise_score:.2f})")
