"""
Theophysics Paper Metrics Engine
=================================
Comprehensive metric system for standardized paper analysis.

Calculates 40+ baseline metrics for each paper:
- Structural metrics
- Coherence metrics  
- Wisdom vs Knowledge metrics
- Fruits of the Spirit scores
- Master Equation variables
- Breakthrough factors
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import re
import json
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class PaperMetrics:
    """40 Baseline Metrics for Every Paper"""
    
    # IDENTIFICATION
    paper_id: str = ""
    paper_name: str = ""
    version: str = ""  # Academic, Beginner, Canonical, etc.
    
    # STRUCTURAL METRICS (1-10)
    word_count: int = 0
    paragraph_count: int = 0
    section_count: int = 0
    subsection_count: int = 0
    axiom_count: int = 0
    theorem_count: int = 0
    claim_count: int = 0
    definition_count: int = 0
    equation_count: int = 0
    citation_count: int = 0
    
    # COHERENCE METRICS (11-20)
    chi_score: float = 0.0  # Overall coherence (0-10)
    coherence_terms: int = 0  # Count of coherence indicators
    entropy_terms: int = 0  # Count of entropy indicators
    structural_score: float = 0.0  # Logical structure score
    trinity_balance: float = 0.0  # Father/Son/Spirit distribution
    law_coverage: float = 0.0  # Coverage of Ten Laws (0-1)
    grace_entropy_ratio: float = 0.0  # Grace vs Entropy
    logical_density: float = 0.0  # Logic terms per 1K words
    theological_depth: float = 0.0  # Theological terms per 1K words
    integration_score: float = 0.0  # Physics-Theology integration
    
    # WISDOM VS KNOWLEDGE METRICS (21-26)
    wisdom_score: float = 0.0  # Wisdom indicators (0-10)
    knowledge_score: float = 0.0  # Knowledge indicators (0-10)
    wisdom_knowledge_ratio: float = 0.0  # W/K ratio
    revelation_count: int = 0  # Revelation/insight references
    practical_application: float = 0.0  # Practical wisdom score
    eternal_perspective: float = 0.0  # Eternal vs temporal focus
    
    # FRUITS OF THE SPIRIT - STRUCTURAL COHERENCE (27-38)
    # Each fruit measures a structural property (0-10), NOT keyword frequency
    fruit_love: float = 0.0        # Cohesion: unity across sections
    fruit_joy: float = 0.0         # Optimism: constructive orientation
    fruit_peace: float = 0.0       # Stability: internal consistency
    fruit_patience: float = 0.0    # Thoroughness: completeness
    fruit_kindness: float = 0.0    # Fairness: fair to alternatives
    fruit_goodness: float = 0.0    # Intent: builds something useful
    fruit_faithfulness: float = 0.0  # Consistency: follows own rules
    fruit_gentleness: float = 0.0  # Humility: certainty calibration
    fruit_self_control: float = 0.0  # Scope: stays within scope
    fruit_grace: float = 0.0       # Balance: proportionate treatment
    fruit_hope: float = 0.0        # Uncertainty: admits limitations
    fruit_humility: float = 0.0    # Complexity: handles difficulty

    # CHI COHERENCE SCORE (derived from 12 fruits)
    chi_coherence: float = 0.0     # Sum of 12 / 120 (0.00 - 1.00)
    chi_grade: str = ""            # Letter grade (A+ through F)

    # EPISTEMIC READINESS SCALE (maturity axis)
    epistemic_readiness: float = 0.0  # 1-10 developmental stage
    epistemic_stage: str = ""         # "Raw intuition" through "Canonical"
    
    # MASTER EQUATION VARIABLES (39-45)
    G_gravity_belonging: float = 0.0  # Gravity ↔ Belonging
    M_mass_meaning: float = 0.0  # Mass ↔ Meaning
    E_energy_engagement: float = 0.0  # Energy ↔ Engagement
    S_entropy_sin: float = 0.0  # Entropy ↔ Sin
    T_time_eternity: float = 0.0  # Time ↔ Eternity
    K_kinetic_action: float = 0.0  # Kinetic ↔ Action
    Lambda_covenant: float = 0.0  # Λ Covenant strength
    
    # BREAKTHROUGH FACTORS (46-50)
    novelty_score: float = 0.0  # Novel insights
    falsifiability: float = 0.0  # Testable predictions
    explanatory_power: float = 0.0  # Problems solved
    paradigm_shift: float = 0.0  # Paradigm-shifting potential
    reproducibility: float = 0.0  # Reproducible results

    # READABILITY METRICS (51-53)
    flesch_kincaid_grade: float = 0.0  # Grade level (lower = easier)
    gunning_fog_index: float = 0.0  # Fog index (lower = clearer)
    coleman_liau_index: float = 0.0  # Coleman-Liau grade level

    # VOCABULARY COMPLEXITY (54-56)
    type_token_ratio: float = 0.0  # Unique words / total words (0-1)
    avg_word_length: float = 0.0  # Average characters per word
    hapax_ratio: float = 0.0  # Words appearing only once / total unique

    # ARGUMENT & EVIDENCE (57-58)
    argument_density: float = 0.0  # Logical connectors per 1K words (0-10)
    claim_evidence_ratio: float = 0.0  # Claims vs evidence/support (0-10)

    # WRITING QUALITY (59-60)
    clarity_index: float = 0.0  # Overall clarity score (0-10)
    passive_voice_ratio: float = 0.0  # Fraction of passive constructions (0-1)

    # STRUCTURAL QUALITY (61-62)
    section_balance: float = 0.0  # Evenness of content distribution (0-10)
    cross_reference_density: float = 0.0  # Internal links/refs per 1K words

    # CONSISTENCY & RIGOR (63-64)
    contradiction_indicators: float = 0.0  # Opposing/hedging patterns (0-10, lower = more consistent)
    qualifier_density: float = 0.0  # Hedging language density (0-1)

    # MATURITY & COVERAGE (65-66)
    maturity_index: float = 0.0  # Overall paper maturity (0-10)
    conceptual_density: float = 0.0  # Unique concepts per 1K words

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_composite_scores(self) -> Dict[str, float]:
        """Calculate composite scores."""
        return {
            'structural_composite': (
                self.axiom_count + self.theorem_count + self.claim_count
            ) / 3 if self.axiom_count > 0 else 0,

            'coherence_composite': (
                self.chi_score + self.structural_score +
                self.trinity_balance * 10 + self.law_coverage * 10
            ) / 4,

            'wisdom_composite': (
                self.wisdom_score + self.practical_application +
                self.eternal_perspective
            ) / 3,

            'fruits_composite': self.chi_coherence * 10,  # chi 0-1 scaled to 0-10

            'master_equation_composite': (
                self.G_gravity_belonging + self.M_mass_meaning +
                self.E_energy_engagement + self.Lambda_covenant
            ) / 4,

            'breakthrough_composite': (
                self.novelty_score + self.falsifiability +
                self.explanatory_power + self.paradigm_shift +
                self.reproducibility
            ) / 5,

            'readability_composite': (
                max(0, 10 - self.flesch_kincaid_grade / 2) +
                max(0, 10 - self.gunning_fog_index / 2) +
                max(0, 10 - self.coleman_liau_index / 2)
            ) / 3,

            'writing_quality_composite': (
                self.clarity_index +
                self.argument_density +
                self.section_balance +
                max(0, 10 - self.contradiction_indicators)
            ) / 4,

            'rigor_composite': (
                self.claim_evidence_ratio +
                self.maturity_index +
                self.conceptual_density +
                self.argument_density
            ) / 4,
        }


class PaperMetricsEngine:
    """Calculate all 50 metrics for a paper."""
    
    # Wisdom indicators
    WISDOM_TERMS = {
        'wisdom': 5, 'discernment': 4, 'prudence': 4, 'understanding': 3,
        'insight': 3, 'counsel': 3, 'sound judgment': 5, 'fear of the lord': 5,
        'righteousness': 4, 'justice': 4, 'truth': 3, 'virtue': 4,
        'eternal': 4, 'transcendent': 4, 'sacred': 3, 'holy': 3,
        'covenant': 4, 'faithfulness': 4, 'obedience': 3, 'humility': 4,
    }
    
    # Knowledge indicators
    KNOWLEDGE_TERMS = {
        'data': 2, 'information': 2, 'facts': 2, 'statistics': 2,
        'analysis': 2, 'research': 2, 'study': 1, 'experiment': 2,
        'evidence': 2, 'proof': 2, 'demonstrate': 2, 'conclude': 2,
        'hypothesis': 2, 'theory': 2, 'model': 2, 'framework': 1,
    }
    
    # Fruits of the Spirit - NO LONGER keyword patterns
    # Now measured structurally (see _calc_structural_fruits method)
    
    # Master Equation variables patterns
    MASTER_EQUATION_PATTERNS = {
        'G_gravity_belonging': [r'\bbelong\w*\b', r'\bcommunity\b', r'\bunity\b', r'\btogether\b'],
        'M_mass_meaning': [r'\bmeaning\b', r'\bpurpose\b', r'\bsignificance\b', r'\bsubstance\b'],
        'E_energy_engagement': [r'\benerg\w+\b', r'\bengage\w+\b', r'\bactive\b', r'\bwork\b'],
        'S_entropy_sin': [r'\bentropy\b', r'\bdecay\b', r'\bsin\b', r'\bdisorder\b'],
        'T_time_eternity': [r'\btime\b', r'\beternal\b', r'\beternity\b', r'\btemporal\b'],
        'K_kinetic_action': [r'\baction\b', r'\bkinetic\b', r'\bmotion\b', r'\bdynamic\b'],
        'Lambda_covenant': [r'\bcovenant\b', r'\bpromise\b', r'\bbond\b', r'\bagreement\b'],
    }
    
    def analyze_paper(self, filepath: Path) -> PaperMetrics:
        """Analyze a paper and calculate all 50 metrics."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return PaperMetrics(paper_id=filepath.stem, paper_name=filepath.name)
        
        metrics = PaperMetrics(
            paper_id=filepath.stem,
            paper_name=filepath.name,
        )
        
        # Detect version
        name_lower = filepath.name.lower()
        if 'academic' in name_lower or '-a-' in name_lower:
            metrics.version = 'Academic'
        elif 'beginner' in name_lower or '-b-' in name_lower:
            metrics.version = 'Beginner'
        elif 'canonical' in name_lower:
            metrics.version = 'Canonical'
        elif 'theology' in name_lower:
            metrics.version = 'Theology'
        
        # STRUCTURAL METRICS
        metrics.word_count = len(content.split())
        metrics.paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        metrics.section_count = len(re.findall(r'^#{1,2}\s+', content, re.MULTILINE))
        metrics.subsection_count = len(re.findall(r'^#{3,4}\s+', content, re.MULTILINE))
        metrics.axiom_count = len(re.findall(r'axiom|%%tag::axiom::', content, re.IGNORECASE))
        metrics.theorem_count = len(re.findall(r'theorem|%%tag::theorem::', content, re.IGNORECASE))
        metrics.claim_count = len(re.findall(r'claim|%%tag::claim::', content, re.IGNORECASE))
        metrics.definition_count = len(re.findall(r'definition|%%tag::definition::', content, re.IGNORECASE))
        metrics.equation_count = len(re.findall(r'[χΨΦΛΩ∫∑∏∂∇]|=.*[+\-*/]', content))
        metrics.citation_count = len(re.findall(r'\([A-Z][a-z]+.*?\d{4}\)', content))
        
        # COHERENCE METRICS (simplified - full calculation would use coherence_scorer)
        content_lower = content.lower()
        coherence_hits = sum(1 for term in ['order', 'structure', 'unity', 'coherence', 'truth'] 
                           if term in content_lower)
        entropy_hits = sum(1 for term in ['chaos', 'random', 'arbitrary', 'confusion'] 
                         if term in content_lower)
        
        metrics.coherence_terms = coherence_hits
        metrics.entropy_terms = entropy_hits
        metrics.chi_score = min(10, max(0, (coherence_hits - entropy_hits) / 2 + 5))
        metrics.structural_score = min(10, len(re.findall(r'\btherefore\b|\bthus\b|\bhence\b', content_lower)))
        
        # WISDOM VS KNOWLEDGE
        wisdom_score = 0
        for term, weight in self.WISDOM_TERMS.items():
            count = content_lower.count(term)
            wisdom_score += count * weight
        
        knowledge_score = 0
        for term, weight in self.KNOWLEDGE_TERMS.items():
            count = content_lower.count(term)
            knowledge_score += count * weight
        
        # Normalize to 0-10 scale
        norm_factor = 1000 / metrics.word_count if metrics.word_count > 0 else 1
        metrics.wisdom_score = min(10, wisdom_score * norm_factor / 10)
        metrics.knowledge_score = min(10, knowledge_score * norm_factor / 10)
        metrics.wisdom_knowledge_ratio = metrics.wisdom_score / max(0.1, metrics.knowledge_score)
        
        # Revelation/insight
        metrics.revelation_count = len(re.findall(r'\brevelation\b|\binsight\b|\bbreakthrough\b', content_lower))
        metrics.practical_application = min(10, len(re.findall(r'\bapply\b|\bpractice\b|\bimplement\b', content_lower)) / 2)
        metrics.eternal_perspective = min(10, len(re.findall(r'\beternal\b|\bforever\b|\btranscend\b', content_lower)) / 2)
        
        # FRUITS OF THE SPIRIT — Structural Coherence (12 dimensions)
        sections = re.split(r'^#{1,3}\s+', content, flags=re.MULTILINE)
        sections = [s for s in sections if len(s.strip()) > 20]
        self._calc_structural_fruits(metrics, content, content_lower, sections)
        
        # MASTER EQUATION VARIABLES
        for var_name, patterns in self.MASTER_EQUATION_PATTERNS.items():
            count = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in patterns)
            score = min(10, count * norm_factor * 3)
            setattr(metrics, var_name, score)
        
        # BREAKTHROUGH FACTORS
        metrics.novelty_score = min(10, len(re.findall(r'\bnovel\b|\bnew\b|\boriginal\b', content_lower)) / 3)
        metrics.falsifiability = min(10, len(re.findall(r'\btest\b|\bpredict\b|\bfalsif\w+\b', content_lower)) / 3)
        metrics.explanatory_power = min(10, len(re.findall(r'\bexplain\b|\bsolve\b|\bresol\w+\b', content_lower)) / 3)
        metrics.paradigm_shift = min(10, len(re.findall(r'\bparadigm\b|\brevolution\b|\btransform\b', content_lower)) / 2)
        metrics.reproducibility = min(10, metrics.citation_count / 5)

        # Calculate composite scores
        metrics.trinity_balance = 0.883  # Placeholder
        metrics.law_coverage = 0.95  # Placeholder
        metrics.grace_entropy_ratio = metrics.chi_coherence * 10 / max(0.1, metrics.S_entropy_sin)
        metrics.logical_density = (metrics.axiom_count + metrics.theorem_count) / max(1, metrics.word_count / 1000)
        metrics.theological_depth = wisdom_score / max(1, metrics.word_count / 1000)
        metrics.integration_score = (metrics.equation_count + metrics.wisdom_score) / 2

        # ============================================================
        # NEW METRICS (51-66): Readability, Vocabulary, Argument,
        #   Clarity, Structure, Consistency, Maturity, Coverage
        # ============================================================
        self._calc_readability(metrics, content)
        self._calc_vocabulary_complexity(metrics, content)
        self._calc_argument_evidence(metrics, content, content_lower)
        self._calc_writing_clarity(metrics, content, content_lower)
        self._calc_section_balance(metrics, content)
        self._calc_consistency_rigor(metrics, content, content_lower)
        self._calc_maturity_coverage(metrics, content, content_lower)

        return metrics

    # ----------------------------------------------------------
    # STRUCTURAL FRUITS OF THE SPIRIT (chi Coherence Score)
    # ----------------------------------------------------------
    # Each "fruit" maps to a structural property of the paper.
    # All scored 0-10. chi = sum(12) / 120, graded A+ through F.

    CHI_GRADE_TABLE = [
        (0.95, 'A+'), (0.90, 'A'), (0.85, 'A-'),
        (0.80, 'B+'), (0.75, 'B'), (0.70, 'B-'),
        (0.65, 'C+'), (0.60, 'C'), (0.55, 'C-'),
        (0.50, 'D+'), (0.45, 'D'), (0.40, 'D-'),
        (0.0, 'F'),
    ]

    def _calc_structural_fruits(self, metrics: PaperMetrics, content: str,
                                 content_lower: str, sections: list):
        """Calculate all 12 structural fruit dimensions and chi score."""
        metrics.fruit_love = self._fruit_love_cohesion(content, content_lower, sections)
        metrics.fruit_joy = self._fruit_joy_optimism(content_lower)
        metrics.fruit_peace = self._fruit_peace_stability(content_lower, sections)
        metrics.fruit_patience = self._fruit_patience_thoroughness(metrics, content, content_lower)
        metrics.fruit_kindness = self._fruit_kindness_fairness(content_lower)
        metrics.fruit_goodness = self._fruit_goodness_intent(content_lower)
        metrics.fruit_faithfulness = self._fruit_faithfulness_consistency(content_lower, sections)
        metrics.fruit_gentleness = self._fruit_gentleness_humility(content_lower, metrics)
        metrics.fruit_self_control = self._fruit_self_control_scope(content_lower, sections)
        metrics.fruit_grace = self._fruit_grace_balance(sections)
        metrics.fruit_hope = self._fruit_hope_uncertainty(content_lower)
        metrics.fruit_humility = self._fruit_humility_complexity(content, content_lower, metrics)

        # chi coherence = sum of 12 dimensions / 120 (0.00 - 1.00)
        fruit_sum = (
            metrics.fruit_love + metrics.fruit_joy + metrics.fruit_peace +
            metrics.fruit_patience + metrics.fruit_kindness + metrics.fruit_goodness +
            metrics.fruit_faithfulness + metrics.fruit_gentleness +
            metrics.fruit_self_control + metrics.fruit_grace +
            metrics.fruit_hope + metrics.fruit_humility
        )
        metrics.chi_coherence = round(fruit_sum / 120, 4)

        # Assign letter grade
        metrics.chi_grade = 'F'
        for threshold, grade in self.CHI_GRADE_TABLE:
            if metrics.chi_coherence >= threshold:
                metrics.chi_grade = grade
                break

        # Epistemic Readiness (piggyback — needs metrics computed above)
        self._calc_epistemic_readiness(metrics, content, content_lower)

    # --- Individual fruit scorers (each returns 0-10 float) ---

    def _fruit_love_cohesion(self, content: str, content_lower: str,
                              sections: list) -> float:
        """Love = Cohesion: concept overlap / unity across sections.
        Measures how well ideas introduced early reappear later."""
        if len(sections) < 2:
            return 5.0  # Single section — neutral

        # Extract significant words (5+ chars) per section
        section_wordsets = []
        for sec in sections:
            words = set(w.lower() for w in re.findall(r'\b[a-zA-Z]{5,}\b', sec))
            if words:
                section_wordsets.append(words)

        if len(section_wordsets) < 2:
            return 5.0

        # Average Jaccard similarity between consecutive sections
        similarities = []
        for i in range(len(section_wordsets) - 1):
            a, b = section_wordsets[i], section_wordsets[i + 1]
            intersection = len(a & b)
            union = len(a | b)
            if union > 0:
                similarities.append(intersection / union)

        if not similarities:
            return 5.0

        avg_sim = sum(similarities) / len(similarities)

        # Also check first-section-to-last overlap (bookend coherence)
        first_last = section_wordsets[0] & section_wordsets[-1]
        fl_union = len(section_wordsets[0] | section_wordsets[-1])
        bookend = len(first_last) / max(1, fl_union)

        # Combined: 70% consecutive flow + 30% bookend return
        raw = avg_sim * 0.7 + bookend * 0.3
        # Scale: 0.05 similarity → 5/10, 0.20 → 10/10
        return round(min(10, max(0, raw * 50)), 2)

    def _fruit_joy_optimism(self, content_lower: str) -> float:
        """Joy = Optimism: ratio of constructive vs destructive orientation.
        Not sentiment analysis — measures whether the paper builds toward
        something vs merely tearing down."""
        constructive = len(re.findall(
            r'\bpropose[sd]?\b|\boffer[sd]?\b|\bbuild[sd]?\b|\bcreate[sd]?\b'
            r'|\bestablish\w*\b|\badvance[sd]?\b|\bcontribut\w+\b|\bsolv\w+\b'
            r'|\bimprove[sd]?\b|\benabl\w+\b|\bempow\w+\b|\bstrengthen\w*\b'
            r'|\brev[ie]al[sd]?\b|\billuminat\w+\b|\bclarif\w+\b|\bunif\w+\b'
            r'|\btherefore\b|\bthus\b|\bhence\b|\bcan\b|\bwill\b|\bshall\b',
            content_lower
        ))
        destructive = len(re.findall(
            r'\bdestroy\w*\b|\bfail\w*\b|\bwrong\b|\bcollapse\w*\b'
            r'|\bdecay\w*\b|\bcorrupt\w*\b|\brefut\w+\b|\breject\w*\b'
            r'|\bdeny\b|\bdenies\b|\bdenial\b|\bimpossib\w+\b'
            r'|\bcritic\w+\b|\bcondemn\w*\b|\babsurd\w*\b|\bflawed\b',
            content_lower
        ))
        total = constructive + destructive
        if total == 0:
            return 5.0
        ratio = constructive / total
        # 0.5 = neutral (5/10), 0.8+ = strongly constructive (8-10)
        return round(min(10, max(0, ratio * 10)), 2)

    def _fruit_peace_stability(self, content_lower: str, sections: list) -> float:
        """Peace = Stability: internal consistency / freedom from self-contradiction.
        Measures whether the paper contradicts itself within its own scope."""
        # Count contradiction signals
        contradictions = len(re.findall(
            r'\bhowever\b.*\bpreviously\b|\balthough\b.*\bearlier\b'
            r'|\bcontrary to\b.*\babove\b|\bbut\b.*\bnoted\b',
            content_lower
        ))
        # Count self-correction signals (worse than organic flow)
        self_corrections = len(re.findall(
            r'\brather\b|\binstead\b|\bcorrection\b|\bactually\b'
            r'|\bin fact\b|\bmore precisely\b|\bto clarify\b',
            content_lower
        ))
        # Count logical flow signals (positive)
        flow_signals = len(re.findall(
            r'\btherefore\b|\bthus\b|\bconsequently\b|\bit follows\b'
            r'|\baccordingly\b|\bthis means\b|\bwe see that\b',
            content_lower
        ))

        # Peace = high flow, low contradiction/correction
        penalty = contradictions * 2 + self_corrections * 0.5
        bonus = min(5, flow_signals * 0.5)
        raw = 7.0 + bonus - penalty
        return round(min(10, max(0, raw)), 2)

    def _fruit_patience_thoroughness(self, metrics: PaperMetrics, content: str,
                                      content_lower: str) -> float:
        """Patience = Thoroughness: completeness markers.
        Does the paper have proper intro, body, conclusion? Are claims supported?"""
        score = 0.0

        # Has introduction / opening framing
        if re.search(r'\bintroduction\b|\boverview\b|\babstract\b|\bpreamble\b', content_lower):
            score += 2.0
        elif re.search(r'^#{1,2}\s+', content, re.MULTILINE):
            score += 1.0  # At least has sections

        # Has conclusion / closing
        if re.search(r'\bconclusion\b|\bsummary\b|\bclosing\b|\bfinal\s+(?:remarks|thoughts)\b', content_lower):
            score += 2.0

        # Adequate length for claimed scope
        if metrics.word_count >= 2000:
            score += 1.5
        elif metrics.word_count >= 1000:
            score += 1.0
        elif metrics.word_count >= 500:
            score += 0.5

        # Has definitions for key terms
        if metrics.definition_count >= 3:
            score += 1.5
        elif metrics.definition_count >= 1:
            score += 0.75

        # Axioms or foundational claims stated explicitly
        if metrics.axiom_count >= 5:
            score += 2.0
        elif metrics.axiom_count >= 1:
            score += 1.0

        # Evidence / citations present
        if metrics.citation_count >= 5:
            score += 1.0
        elif metrics.equation_count >= 3:
            score += 0.75

        return round(min(10, score), 2)

    def _fruit_kindness_fairness(self, content_lower: str) -> float:
        """Kindness = Fairness: engagement with counterarguments / alternatives.
        Does the paper acknowledge other viewpoints, or only assert its own?"""
        # Fair engagement markers
        fair = len(re.findall(
            r'\bone might argue\b|\bsome (?:may|might|would)\b|\balternatively\b'
            r'|\bon the other hand\b|\bit could be (?:said|argued)\b'
            r'|\bopponents\b|\bcritics\b|\bobjection\b|\bcounterargument\b'
            r'|\backnowledg\w+\b|\bconcede[sd]?\b|\bgrant\w* that\b'
            r'|\brespect\w*\b|\bfair\w*\b',
            content_lower
        ))
        # Dismissive markers (reduce score)
        dismissive = len(re.findall(
            r'\bobviously\b|\bclearly wrong\b|\babsurd\b|\bridiculous\b'
            r'|\bfoolish\b|\bignorant\b|\bstupid\b|\bnonsens\w+\b',
            content_lower
        ))
        raw = 5.0 + fair * 0.8 - dismissive * 1.5
        return round(min(10, max(0, raw)), 2)

    def _fruit_goodness_intent(self, content_lower: str) -> float:
        """Goodness = Intent: constructive proposals vs pure criticism.
        Does the paper build something useful, or only tear down?"""
        # Constructive proposals
        proposals = len(re.findall(
            r'\bwe propose\b|\bthis (?:paper|work|framework)\b.*?\b(?:present|offer|develop|introduce)\b'
            r'|\bour (?:model|approach|method|framework)\b'
            r'|\bwe (?:define|establish|construct|develop|introduce|present)\b'
            r'|\bthis leads to\b|\bthe result is\b|\bwe find\b'
            r'|\baxiom\b|\btheorem\b|\bdefinition\b|\blaw\b',
            content_lower
        ))
        # Pure criticism without alternative
        pure_criticism = len(re.findall(
            r'\bthis is wrong\b|\bthis fails\b|\bthe problem with\b'
            r'|\brefuted\b|\bdebunked\b|\bdisproved\b',
            content_lower
        ))
        raw = 5.0 + proposals * 0.6 - pure_criticism * 1.0
        return round(min(10, max(0, raw)), 2)

    def _fruit_faithfulness_consistency(self, content_lower: str,
                                         sections: list) -> float:
        """Faithfulness = Consistency: does the paper follow its own rules?
        If it declares axioms or premises, does it use them throughout?"""
        # Extract declared axioms/premises in first section
        if not sections:
            return 5.0

        first_section = sections[0].lower() if sections else content_lower[:2000]
        rest = ' '.join(sections[1:]).lower() if len(sections) > 1 else content_lower[2000:]

        # Find key terms declared in the opening
        declared_terms = set(re.findall(r'\b([a-z]{5,})\b', first_section))
        # Filter to significant terms (not common English)
        common = {'which', 'there', 'their', 'would', 'could', 'should', 'about',
                   'these', 'those', 'other', 'being', 'where', 'after', 'every',
                   'under', 'might', 'while', 'still', 'never', 'often', 'since',
                   'first', 'given', 'above', 'below', 'between', 'through', 'before'}
        declared_terms -= common

        if not declared_terms or not rest:
            return 5.0

        # Check how many declared terms reappear later
        rest_words = set(re.findall(r'\b([a-z]{5,})\b', rest))
        reused = declared_terms & rest_words
        reuse_ratio = len(reused) / max(1, len(declared_terms))

        # Higher reuse = more faithful to own framework
        return round(min(10, max(0, reuse_ratio * 12)), 2)

    def _fruit_gentleness_humility(self, content_lower: str,
                                    metrics: PaperMetrics) -> float:
        """Gentleness = Humility in certainty calibration.
        Uses qualifier density — papers that appropriately hedge
        score higher than those making absolute claims everywhere."""
        # Qualifier markers (shows epistemic humility)
        qualifiers = len(re.findall(
            r'\bperhaps\b|\bpossibly\b|\bmay\b|\bmight\b'
            r'|\bsuggests?\b|\bappears?\b|\bit seems\b'
            r'|\bin some sense\b|\bone could argue\b|\btentativ\w+\b'
            r'|\bwe believe\b|\bwe think\b|\bour view\b',
            content_lower
        ))
        # Absolute/dogmatic markers (reduces score)
        absolutes = len(re.findall(
            r'\bcertainly\b|\bundeniably\b|\bwithout doubt\b|\bobviously\b'
            r'|\bclearly\b|\bindisputably\b|\bunquestionably\b'
            r'|\babsolute(?:ly)?\b|\bperfect(?:ly)?\b|\bproven\b',
            content_lower
        ))
        wc = max(1, metrics.word_count / 1000)
        q_density = qualifiers / wc
        a_density = absolutes / wc

        # Balance: some qualification is good, excess of either is bad
        raw = 5.0 + q_density * 1.5 - a_density * 2.0
        return round(min(10, max(0, raw)), 2)

    def _fruit_self_control_scope(self, content_lower: str,
                                   sections: list) -> float:
        """Self-Control = Scope: does the paper stay within its declared topic?
        Measures topic coherence — avoiding tangents and scope creep."""
        if len(sections) < 2:
            return 6.0  # Short papers get benefit of doubt

        # Extract top terms from entire document
        all_words = re.findall(r'\b[a-z]{4,}\b', content_lower)
        if not all_words:
            return 5.0

        from collections import Counter
        freq = Counter(all_words)
        # Top 20 content words = the paper's "topic signature"
        common_stop = {'this', 'that', 'with', 'from', 'have', 'been', 'were',
                        'will', 'they', 'them', 'then', 'than', 'into', 'also',
                        'each', 'which', 'their', 'there', 'would', 'could',
                        'should', 'about', 'these', 'those', 'other', 'more',
                        'some', 'what', 'when', 'only', 'your', 'such', 'does'}
        top_terms = set()
        for word, _ in freq.most_common(50):
            if word not in common_stop and len(word) >= 4:
                top_terms.add(word)
            if len(top_terms) >= 20:
                break

        if not top_terms:
            return 5.0

        # Check each section's alignment with the topic signature
        alignments = []
        for sec in sections:
            sec_words = set(re.findall(r'\b[a-z]{4,}\b', sec.lower()))
            if sec_words:
                overlap = len(sec_words & top_terms) / len(top_terms)
                alignments.append(overlap)

        if not alignments:
            return 5.0

        avg_alignment = sum(alignments) / len(alignments)
        # Low variance = consistent focus
        variance = sum((a - avg_alignment) ** 2 for a in alignments) / len(alignments)
        consistency = max(0, 1 - variance ** 0.5 * 3)

        raw = avg_alignment * 6 + consistency * 4
        return round(min(10, max(0, raw)), 2)

    def _fruit_grace_balance(self, sections: list) -> float:
        """Grace = Balance: proportionate treatment across sections.
        No section dominates excessively or is neglected."""
        if len(sections) < 2:
            return 6.0

        section_lengths = [len(s.split()) for s in sections]
        avg = sum(section_lengths) / len(section_lengths)
        if avg == 0:
            return 5.0

        # Coefficient of variation
        variance = sum((l - avg) ** 2 for l in section_lengths) / len(section_lengths)
        cv = (variance ** 0.5) / avg

        # CV of 0 = perfect balance (10), CV of 1+ = very unbalanced (0)
        return round(min(10, max(0, 10 - cv * 8)), 2)

    def _fruit_hope_uncertainty(self, content_lower: str) -> float:
        """Hope = Uncertainty acknowledgment: admits what it doesn't know.
        Papers that honestly flag limitations score higher."""
        # Limitation acknowledgment
        limitations = len(re.findall(
            r'\blimitation\w*\b|\bfuture work\b|\bfurther research\b'
            r'|\bremains to be\b|\bnot (?:yet |fully )?(?:understood|resolved|clear)\b'
            r'|\bopen question\b|\buncertain\w*\b|\bchalleng\w+\b'
            r'|\bwe do not (?:yet )?\b|\bbeyond (?:the )?scope\b'
            r'|\bmore work\b|\brequires? further\b',
            content_lower
        ))
        # Forward-looking markers (constructive uncertainty)
        forward = len(re.findall(
            r'\bfuture\b|\bremain\w*\b|\bnext step\b|\bopportunit\w+\b'
            r'|\bpotential\b|\bpossibilit\w+\b|\bpath forward\b',
            content_lower
        ))
        raw = 4.0 + limitations * 1.2 + forward * 0.5
        return round(min(10, max(0, raw)), 2)

    def _fruit_humility_complexity(self, content: str, content_lower: str,
                                    metrics: PaperMetrics) -> float:
        """Humility = Complexity engagement: handles difficult material.
        Papers that engage with genuinely hard problems score higher than
        those that only address trivial claims."""
        # Complexity indicators
        complexity = 0

        # Uses equations/formal notation
        if metrics.equation_count >= 3:
            complexity += 2.0
        elif metrics.equation_count >= 1:
            complexity += 1.0

        # Multi-step reasoning (therefore chains, if-then)
        reasoning_chains = len(re.findall(
            r'\bif\b.*\bthen\b|\bgiven\b.*\btherefore\b'
            r'|\bfrom\b.*\bit follows\b|\bsince\b.*\bwe conclude\b',
            content_lower
        ))
        complexity += min(2.0, reasoning_chains * 0.5)

        # Engages with paradoxes / tensions (sign of intellectual depth)
        paradox = len(re.findall(
            r'\bparadox\w*\b|\btension\b|\bdilemma\b|\bapori[ae]\b'
            r'|\bcontradiction\b|\bantinom\w+\b|\bduali\w+\b',
            content_lower
        ))
        complexity += min(2.0, paradox * 0.8)

        # Cross-disciplinary bridges (physics + theology, math + philosophy)
        bridges = len(re.findall(
            r'\bjust as\b.*\bso too\b|\banalog\w+\b|\bcorrespond\w+\b'
            r'|\bparallel\b|\bmap\w* onto\b|\bisomorphi\w+\b',
            content_lower
        ))
        complexity += min(2.0, bridges * 0.6)

        # Vocabulary richness as proxy for conceptual density
        if metrics.type_token_ratio > 0.4:
            complexity += 1.0
        elif metrics.type_token_ratio > 0.3:
            complexity += 0.5

        # Base of 3 (every paper gets some credit for existing)
        return round(min(10, max(0, 3.0 + complexity)), 2)

    # --- Epistemic Readiness Scale ---

    EPISTEMIC_STAGES = [
        (1.5, 1, "Raw intuition"),
        (2.5, 2, "Gut feeling"),
        (3.5, 3, "Forming idea"),
        (4.5, 4, "Informal thesis"),
        (5.5, 5, "Articulated claim"),
        (6.5, 6, "Grounded claim"),
        (7.5, 7, "Integrated framework"),
        (8.5, 8, "Robust system"),
        (9.5, 9, "Near-canonical"),
        (10.0, 10, "Canonical"),
    ]

    def _calc_epistemic_readiness(self, metrics: PaperMetrics,
                                   content: str, content_lower: str):
        """Calculate Epistemic Readiness Scale (1-10).
        Measures developmental stage, NOT quality.
        1-2 = raw intuition, 3-4 = forming ideas, 5 = articulated claim,
        6 = grounded claim, 7 = integrated, 8 = robust, 9 = near-canonical,
        10 = canonical."""
        score = 0.0

        # Factor 1: Structural maturity (0-2.5)
        # Has formal sections, definitions, axioms
        structural = 0.0
        if metrics.section_count >= 4:
            structural += 1.0
        elif metrics.section_count >= 2:
            structural += 0.5
        if metrics.definition_count >= 3:
            structural += 0.75
        if metrics.axiom_count >= 5:
            structural += 0.75
        score += min(2.5, structural)

        # Factor 2: Evidence base (0-2.0)
        evidence = 0.0
        if metrics.citation_count >= 10:
            evidence += 1.0
        elif metrics.citation_count >= 3:
            evidence += 0.5
        if metrics.equation_count >= 5:
            evidence += 0.5
        if metrics.claim_evidence_ratio >= 5:
            evidence += 0.5
        score += min(2.0, evidence)

        # Factor 3: Coherence (0-2.0) — uses chi_coherence already computed
        chi = metrics.chi_coherence
        score += min(2.0, chi * 2.5)

        # Factor 4: Completeness (0-1.5)
        complete = 0.0
        if metrics.word_count >= 3000:
            complete += 0.5
        if metrics.maturity_index >= 5:
            complete += 0.5
        if metrics.fruit_patience >= 6:  # thoroughness
            complete += 0.5
        score += min(1.5, complete)

        # Factor 5: Rigor (0-2.0)
        rigor = 0.0
        if metrics.argument_density >= 3:
            rigor += 0.5
        if metrics.fruit_faithfulness >= 5:  # consistency
            rigor += 0.5
        if metrics.fruit_humility >= 5:  # complexity engagement
            rigor += 0.5
        if metrics.qualifier_density > 0.02:  # appropriate hedging
            rigor += 0.5
        score += min(2.0, rigor)

        # Clamp to 1-10
        metrics.epistemic_readiness = round(min(10, max(1, score + 1)), 2)

        # Assign stage name
        metrics.epistemic_stage = "Raw intuition"
        for threshold, level, name in self.EPISTEMIC_STAGES:
            if metrics.epistemic_readiness < threshold:
                metrics.epistemic_stage = name
                break
        else:
            metrics.epistemic_stage = "Canonical"

    # ----------------------------------------------------------
    # New metric calculation methods (51-66)
    # ----------------------------------------------------------

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Estimate syllable count for English word."""
        word = word.lower().strip()
        if len(word) <= 2:
            return 1
        # Remove trailing silent e
        if word.endswith('e') and not word.endswith('le'):
            word = word[:-1]
        count = 0
        vowels = 'aeiouy'
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        return max(1, count)

    def _calc_readability(self, metrics: PaperMetrics, content: str):
        """Calculate Flesch-Kincaid, Gunning Fog, Coleman-Liau readability."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        num_sentences = max(1, len(sentences))

        words = re.findall(r"[a-zA-Z']+", content)
        num_words = max(1, len(words))

        total_syllables = sum(self._count_syllables(w) for w in words)
        avg_syllables = total_syllables / num_words
        avg_sentence_len = num_words / num_sentences

        # Complex words = 3+ syllables (Gunning Fog)
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        pct_complex = complex_words / num_words

        # Character count for Coleman-Liau
        total_chars = sum(len(w) for w in words)

        # Flesch-Kincaid Grade Level
        metrics.flesch_kincaid_grade = round(
            0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59, 2
        )

        # Gunning Fog Index
        metrics.gunning_fog_index = round(
            0.4 * (avg_sentence_len + 100 * pct_complex), 2
        )

        # Coleman-Liau Index
        L = (total_chars / num_words) * 100  # avg letters per 100 words
        S = (num_sentences / num_words) * 100  # avg sentences per 100 words
        metrics.coleman_liau_index = round(
            0.0588 * L - 0.296 * S - 15.8, 2
        )

    def _calc_vocabulary_complexity(self, metrics: PaperMetrics, content: str):
        """Calculate type-token ratio, avg word length, hapax legomena ratio."""
        words = [w.lower() for w in re.findall(r"[a-zA-Z']+", content) if len(w) > 1]
        if not words:
            return

        num_words = len(words)
        unique_words = set(words)
        num_unique = len(unique_words)

        # Type-token ratio (vocabulary richness)
        metrics.type_token_ratio = round(num_unique / num_words, 4)

        # Average word length
        metrics.avg_word_length = round(sum(len(w) for w in words) / num_words, 2)

        # Hapax legomena ratio (words appearing exactly once / total unique)
        from collections import Counter
        freq = Counter(words)
        hapax = sum(1 for count in freq.values() if count == 1)
        metrics.hapax_ratio = round(hapax / max(1, num_unique), 4)

    def _calc_argument_evidence(self, metrics: PaperMetrics, content: str, content_lower: str):
        """Calculate argument density and claim-to-evidence ratio."""
        wc = max(1, metrics.word_count)

        # Argument density: logical connectors per 1K words
        logical_connectors = len(re.findall(
            r'\btherefore\b|\bthus\b|\bhence\b|\bconsequently\b|\baccordingly\b'
            r'|\bbecause\b|\bsince\b|\bgiven that\b|\bit follows\b|\bimplies\b'
            r'|\bif\b.*\bthen\b|\bmoreover\b|\bfurthermore\b|\bin addition\b'
            r'|\bhowever\b|\bnevertheless\b|\bon the other hand\b|\bconversely\b'
            r'|\bin conclusion\b|\bto summarize\b|\bin summary\b',
            content_lower
        ))
        metrics.argument_density = min(10, round(logical_connectors / (wc / 1000), 2))

        # Claim-to-evidence ratio
        # Claims: assertions, declarations, stated positions
        claims = len(re.findall(
            r'\bclaim\b|\bassert\b|\bstate\b|\bdeclare\b|\bpropose\b|\bargue\b'
            r'|\bcontend\b|\bmaintain\b|\bhold that\b|\bsubmit\b',
            content_lower
        ))
        # Evidence: supporting patterns
        evidence = len(re.findall(
            r'\bevidence\b|\bdemonstrat\w+\b|\bprov\w+\b|\bshow[sn]?\b'
            r'|\bsupport\w*\b|\bconfirm\w*\b|\bverif\w+\b|\bvalidat\w+\b'
            r'|\bexampl\w+\b|\bfor instance\b|\bnamely\b|\billustrat\w+\b'
            r'|\baccording to\b|\bcit\w+\b|\bsource\b|\breference\b',
            content_lower
        ))
        # Also count citations and equations as evidence
        evidence += metrics.citation_count + min(metrics.equation_count, 10)

        # Score: higher = more evidence relative to claims (better)
        if claims == 0:
            metrics.claim_evidence_ratio = min(10, evidence / 3) if evidence > 0 else 5.0
        else:
            ratio = evidence / claims
            metrics.claim_evidence_ratio = min(10, round(ratio * 2, 2))

    def _calc_writing_clarity(self, metrics: PaperMetrics, content: str, content_lower: str):
        """Calculate clarity index and passive voice ratio."""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        num_sentences = max(1, len(sentences))
        wc = max(1, metrics.word_count)

        # Passive voice detection (approximation)
        passive_patterns = re.findall(
            r'\b(?:is|are|was|were|been|being|be)\s+(?:\w+\s+)*?'
            r'(?:ed|en|ized|ised|ated|eted|ited|uted|own|ung|orn|awn)\b',
            content_lower
        )
        passive_count = len(passive_patterns)
        metrics.passive_voice_ratio = round(min(1.0, passive_count / num_sentences), 4)

        # Sentence length variance (lower = more consistent = clearer)
        sent_lengths = [len(s.split()) for s in sentences]
        avg_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((l - avg_len) ** 2 for l in sent_lengths) / len(sent_lengths)
        std_dev = variance ** 0.5

        # Jargon/technical density (Latin/Greek-derived multi-syllable words)
        jargon_count = len(re.findall(
            r'\b\w{10,}\b',  # words 10+ characters as proxy for jargon
            content
        ))
        jargon_density = jargon_count / (wc / 1000)

        # Clarity index: combines readability, passive voice, sentence consistency, jargon
        # Higher = clearer writing
        readability_factor = max(0, 10 - metrics.flesch_kincaid_grade / 3)
        passive_penalty = metrics.passive_voice_ratio * 3
        consistency_factor = max(0, 5 - std_dev / 5)
        jargon_penalty = min(3, jargon_density / 10)

        metrics.clarity_index = round(
            max(0, min(10, readability_factor - passive_penalty + consistency_factor - jargon_penalty)),
            2
        )

    def _calc_section_balance(self, metrics: PaperMetrics, content: str):
        """Calculate section balance and cross-reference density."""
        wc = max(1, metrics.word_count)

        # Split content by headers to get section sizes
        sections = re.split(r'^#{1,3}\s+', content, flags=re.MULTILINE)
        sections = [s for s in sections if len(s.strip()) > 20]

        if len(sections) >= 2:
            section_lengths = [len(s.split()) for s in sections]
            avg_section = sum(section_lengths) / len(section_lengths)

            if avg_section > 0:
                # Coefficient of variation (lower = more balanced)
                variance = sum((l - avg_section) ** 2 for l in section_lengths) / len(section_lengths)
                cv = (variance ** 0.5) / avg_section

                # Convert to 0-10 scale (0 = perfectly unbalanced, 10 = perfectly balanced)
                metrics.section_balance = round(max(0, min(10, 10 - cv * 5)), 2)
            else:
                metrics.section_balance = 5.0
        else:
            metrics.section_balance = 5.0  # Single section = neutral

        # Cross-reference density: internal links + back-references per 1K words
        internal_links = len(re.findall(r'\[\[.*?\]\]', content))
        back_refs = len(re.findall(
            r'\b(?:as (?:noted|mentioned|discussed|shown|stated) (?:above|below|earlier|previously))\b'
            r'|\b(?:see (?:above|below|section|chapter|appendix))\b'
            r'|\b(?:refer(?:ring)? to)\b'
            r'|\bcf\.\b',
            content, re.IGNORECASE
        ))
        metrics.cross_reference_density = round((internal_links + back_refs) / (wc / 1000), 2)

    def _calc_consistency_rigor(self, metrics: PaperMetrics, content: str, content_lower: str):
        """Calculate contradiction indicators and qualifier density."""
        wc = max(1, metrics.word_count)

        # Contradiction indicators: opposing language within same paper
        contradictions = len(re.findall(
            r'\bhowever\b|\bbut\b|\bnevertheless\b|\bcontrar\w+\b'
            r'|\bin contrast\b|\bon the other hand\b|\bparadox\w*\b'
            r'|\bwhile .* also\b|\byet\b|\balthough\b',
            content_lower
        ))
        # Negation patterns that might indicate self-correction
        negations = len(re.findall(
            r'\bnot\s+(?:necessarily|always|entirely|simply)\b'
            r'|\brather than\b|\binstead of\b|\bas opposed to\b',
            content_lower
        ))
        raw_contradiction = (contradictions + negations) / (wc / 1000)
        metrics.contradiction_indicators = round(min(10, raw_contradiction), 2)

        # Qualifier/hedging density
        qualifiers = len(re.findall(
            r'\bperhaps\b|\bmaybe\b|\bpossibly\b|\bmight\b|\bcould\b'
            r'|\bseems?\b|\bappears?\b|\bsuggests?\b|\btends?\b'
            r'|\bgenerally\b|\busually\b|\boften\b|\bsomewhat\b'
            r'|\bapproximate\w*\b|\broughly\b|\bin some sense\b',
            content_lower
        ))
        metrics.qualifier_density = round(min(1.0, qualifiers / (wc / 100)), 4)

    def _calc_maturity_coverage(self, metrics: PaperMetrics, content: str, content_lower: str):
        """Calculate paper maturity index and conceptual density."""
        wc = max(1, metrics.word_count)

        # Paper Maturity Index (0-10): multi-factor assessment
        # Factor 1: Structural completeness (has intro, body, conclusion patterns)
        has_intro = 1.0 if re.search(r'\bintroduction\b|\boverview\b|\babstract\b', content_lower) else 0.0
        has_conclusion = 1.0 if re.search(r'\bconclusion\b|\bsummary\b|\bclosing\b|\bfinal\b', content_lower) else 0.0
        has_sections = min(1.0, metrics.section_count / 4)  # 4+ sections = full credit
        structural_completeness = (has_intro + has_conclusion + has_sections) / 3

        # Factor 2: Citation/evidence depth
        citation_depth = min(1.0, metrics.citation_count / 10)  # 10+ citations = full credit

        # Factor 3: Rigor markers (definitions, axioms, theorems, proofs)
        rigor_markers = (
            min(1.0, metrics.definition_count / 5) +
            min(1.0, metrics.axiom_count / 10) +
            min(1.0, metrics.theorem_count / 3) +
            min(1.0, metrics.equation_count / 10)
        ) / 4

        # Factor 4: Length adequacy (very short = immature)
        length_factor = min(1.0, wc / 2000)  # 2000+ words = full credit

        # Factor 5: Internal consistency (low contradiction = more mature)
        consistency_factor = max(0, 1 - metrics.contradiction_indicators / 10)

        metrics.maturity_index = round(
            (structural_completeness * 2.5 +
             citation_depth * 1.5 +
             rigor_markers * 2.5 +
             length_factor * 1.5 +
             consistency_factor * 2.0) * 10 / 10,
            2
        )

        # Conceptual Density: unique significant concepts per 1K words
        # Extract capitalized phrases and technical terms as "concepts"
        concepts = set()
        # Multi-word capitalized phrases (proper nouns / concept names)
        for match in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', content):
            concepts.add(match.group().lower())
        # Technical terms (words with Greek letters, math notation)
        for match in re.finditer(r'[χΨΦΛΩ]\w*|\b\w+tion\b|\b\w+ism\b|\b\w+ity\b', content):
            if len(match.group()) > 4:
                concepts.add(match.group().lower())
        # Defined terms
        for match in re.finditer(r'\*\*([^*]+)\*\*', content):
            term = match.group(1).strip().lower()
            if 2 < len(term) < 50:
                concepts.add(term)

        metrics.conceptual_density = round(min(10, len(concepts) / (wc / 1000)), 2)


def main():
    """Test the metrics engine."""
    engine = PaperMetricsEngine()
    
    # Test on a sample paper
    base_path = Path(os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3'))
    
    print("=" * 80)
    print("THEOPHYSICS PAPER METRICS ENGINE - TEST")
    print("=" * 80)
    print()
    
    # Find first paper to test
    papers_found = list(base_path.rglob("*canonical*.md"))[:1]
    
    if papers_found:
        paper = papers_found[0]
        print(f"Analyzing: {paper.name}")
        print()
        
        metrics = engine.analyze_paper(paper)
        
        # Display key metrics
        print("STRUCTURAL METRICS")
        print(f"  Words: {metrics.word_count:,}")
        print(f"  Axioms: {metrics.axiom_count}")
        print(f"  Equations: {metrics.equation_count}")
        print(f"  Citations: {metrics.citation_count}")
        print()
        
        print("COHERENCE METRICS")
        print(f"  CHI Score: {metrics.chi_score:.2f} / 10")
        print(f"  Structural Score: {metrics.structural_score:.2f} / 10")
        print()
        
        print("WISDOM VS KNOWLEDGE")
        print(f"  Wisdom Score: {metrics.wisdom_score:.2f} / 10")
        print(f"  Knowledge Score: {metrics.knowledge_score:.2f} / 10")
        print(f"  W/K Ratio: {metrics.wisdom_knowledge_ratio:.2f}")
        print()
        
        print("FRUITS OF THE SPIRIT")
        fruits = metrics.to_dict()
        for fruit in ['love', 'joy', 'peace', 'grace', 'hope', 'humility']:
            score = fruits.get(f'fruit_{fruit}', 0)
            print(f"  {fruit.title()}: {score:.2f} / 10")
        print()
        
        print("MASTER EQUATION VARIABLES")
        print(f"  G (Gravity↔Belonging): {metrics.G_gravity_belonging:.2f}")
        print(f"  Λ (Covenant): {metrics.Lambda_covenant:.2f}")
        print()
        
        print("COMPOSITE SCORES")
        composites = metrics.get_composite_scores()
        for name, score in composites.items():
            print(f"  {name}: {score:.2f}")
    else:
        print("No papers found for testing")


if __name__ == "__main__":
    main()
