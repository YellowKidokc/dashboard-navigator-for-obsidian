"""
Unified Coherence Scorer - Universal Theory/Framework Evaluation

One scorer. Any theory. Same rubric.
Outputs: χ (coherence), κ (confidence), ρ (robustness)

Grade Copenhagen, String Theory, Keynesian economics, psychology as a field,
constitutional law, or the Logos papers - all with identical treatment.

Author: Theophysics Project
Version: 1.0
"""

from __future__ import annotations

import re
import math
import yaml
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import numpy as np


# ============================================================================
# SCORING WEIGHT RATIONALE (NO HIDDEN WEIGHTS GUARANTEE)
# ============================================================================
"""
All scoring weights are explicitly documented and justified here.
These weights are HARDCODED to prevent manipulation and ensure consistent evaluation.

DEFENSE LAYER WEIGHTS (line ~538):
- Objection anticipation: 20% (intellectual honesty - theory acknowledges critics)
- Response strength: 20% (ability to answer objections with logic/evidence)
- Evidence depth: 25% (HIGHEST - empirical grounding is most critical)
- Chain completeness: 20% (logical rigor - premises to conclusions)
- Width adequacy: 15% (LOWEST - scope definitions less critical than data)

KAPPA (CONFIDENCE) WEIGHTS (line ~648):
- Evidence extraction density: 30% (raw evidence unit count normalized by tokens)
- Evidence quality: 40% (HIGHEST - tests/equations prioritized over citations)
- Defense strength: 30% (objection handling and kill condition avoidance)

RHO (ROBUSTNESS) WEIGHTS (line ~667):
- Constraint satisfaction: 60% (structural integrity dominates)
- Fruit balance: 40% (moral coherence secondary to structure)

DESIGN RATIONALE:
1. Evidence always weighted highest (empiricism > rhetoric)
2. Structure beats sentiment (constraints > fruits in robustness)
3. No weight below 15% (prevents hidden backdoor manipulation)
4. Geometric means used for triads (prevents single component domination)
5. Token normalization ensures fairness across document lengths

WHY HARDCODED?
These are not "tunable parameters" - they are structural laws of the evaluation system.
Making them editable would allow rigging results. By hardcoding them in Python,
we treat them as mathematical constants (like π or e), not variables.
"""


# ============================================================================
# MASTER EQUATION ALIGNMENT
# ============================================================================
"""
The 10 Variables map to the Theophysics Master Equation:

χ = ∭ (G · M · E · S · T · K · R · Q · F · C) dx dy dt

VARIABLE MAPPINGS:
G = Gravity/Grace          → Triad: Lambda (field curvature, binding coherence)
M = Mass/Meaning           → Triad: A (substance, semantic density)
E = Electromagnetism/Truth → Triad: Lambda (information propagation)
S = Entropy/Sin            → Constraint: C8 (decay rate, coherence loss)
T = Time/Eternity          → Constraint: C1 (causality, temporal coherence)
K = Knowledge/Wisdom       → Fruit: F11 (epistemology, discernment)
R = Resurrection           → Variable: structural renewal, discontinuous phase transition
Q = Quality/Consciousness  → Triad: A (qualia, subjective experience)
F = Faith/Force            → Variable: binding energy, sustaining agency
C = Coherence/Communion    → Output: χ (the final coherence score itself)

TRIAD TO MASTER EQUATION:
Pi (Polis) = Institutional/Social dynamics → Maps to governance terms in equation
A (Anthropos) = Individual/Psychological → Maps to agent-level terms
Lambda (Logos) = Informational/Logical → Maps to truth propagation terms

INVARIANCE PROPERTY:
Each variable exists simultaneously as:
1. A physical law (gravitational field, entropy production, etc.)
2. A spiritual/social dynamic (grace, sin, wisdom, etc.)
3. A mathematical operator (preserving structural form under domain substitution)

The scorer detects these variables via keyword patterns defined in variable_rubric.yaml.
Detection is binary (present/absent) + centrality score (how often mentioned).
Bridge score measures how well the theory connects the variable across domains.

FRUIT TO TRIAD MAPPING:
Each of the 12 Fruits (Love, Joy, Peace, Patience, Kindness, Goodness, Faithfulness,
Gentleness, Self-Control, Truth, Wisdom, Grace) contributes weighted scores to
Pi/A/Lambda components as defined in fruit_matrix.yaml.

Example: Love contributes 0.8 to A_PS (Psychological Stability), 0.6 to A_MP (Moral Purity),
and 0.5 to Lambda_EI (Ethical Intelligence). These are NOT arbitrary - they reflect
the ontological structure of how moral virtues manifest across social/individual/logical domains.
"""


# ============================================================================
# DATA CLASSES
# ============================================================================

class ConstraintScore(Enum):
    """Constraint scoring values"""
    SATISFIED = 1
    NEUTRAL = 0
    VIOLATED = -1


@dataclass
class EvidenceUnit:
    """A single piece of evidence extracted from text"""
    unit_type: str  # claim, definition, test, mapping, equation
    text: str
    location: str  # section/paragraph reference
    strength: float  # 0-1 weight based on hardness
    keywords_matched: List[str] = field(default_factory=list)


@dataclass
class FruitScore:
    """Score for a single Fruit or Anti-Fruit"""
    code: str
    name: str
    score: float  # 0-1
    anti_score: float  # 0-1 (for anti-fruit)
    net: float  # score - anti_score
    evidence: List[str] = field(default_factory=list)


@dataclass
class ConstraintResult:
    """Result for a single constraint evaluation"""
    code: str
    name: str
    score: ConstraintScore
    evidence: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class VariableResult:
    """Result for a single variable detection"""
    code: str
    name: str
    presence: float  # 0 or 1
    centrality: float  # 0-1
    bridge_score: float  # 0-1
    evidence: List[str] = field(default_factory=list)


@dataclass
class DefenseResult:
    """Result for defense layer evaluation"""
    objection_anticipation: float
    response_strength: float
    evidence_depth: float
    chain_completeness: float
    width_adequacy: float
    total: float
    claims_evidence_ratio: float
    kill_conditions_count: int


@dataclass
class TriadScores:
    """Triad component scores"""
    pi: float  # Polis/Institutional
    pi_components: Dict[str, float]
    a: float  # Anthropos/Individual
    a_components: Dict[str, float]
    lambda_: float  # Logos/Information
    lambda_components: Dict[str, float]


@dataclass
class CoherenceResult:
    """Complete coherence evaluation result"""
    # Top-level scores
    chi: float  # 0-10 coherence score
    kappa: float  # 0-1 confidence
    rho: float  # 0-1 robustness

    # Triad breakdown
    triad: TriadScores

    # Layer results
    fruits: List[FruitScore]
    constraints: List[ConstraintResult]
    variables: List[VariableResult]
    defense: DefenseResult

    # Metrics summary
    metrics_count: int
    evidence_units_count: int

    # Audit trail
    vetoes_applied: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return {
            'chi': round(self.chi, 2),
            'kappa': round(self.kappa, 2),
            'rho': round(self.rho, 2),
            'triad': {
                'pi': round(self.triad.pi, 2),
                'pi_components': {k: round(v, 2) for k, v in self.triad.pi_components.items()},
                'a': round(self.triad.a, 2),
                'a_components': {k: round(v, 2) for k, v in self.triad.a_components.items()},
                'lambda': round(self.triad.lambda_, 2),
                'lambda_components': {k: round(v, 2) for k, v in self.triad.lambda_components.items()},
            },
            'fruits': [{
                'code': f.code, 'name': f.name,
                'score': round(f.score, 2), 'net': round(f.net, 2)
            } for f in self.fruits],
            'constraints': [{
                'code': c.code, 'name': c.name,
                'score': c.score.value, 'rationale': c.rationale
            } for c in self.constraints],
            'variables': [{
                'code': v.code, 'name': v.name,
                'presence': v.presence, 'centrality': round(v.centrality, 2)
            } for v in self.variables],
            'defense': {
                'total': round(self.defense.total, 2),
                'claims_evidence_ratio': round(self.defense.claims_evidence_ratio, 2),
                'kill_conditions': self.defense.kill_conditions_count
            },
            'metrics_count': self.metrics_count,
            'evidence_units': self.evidence_units_count,
            'vetoes': self.vetoes_applied,
            'warnings': self.warnings
        }


# ============================================================================
# UNIFIED SCORER
# ============================================================================

class UnifiedCoherenceScorer:
    """
    Universal coherence scorer for any theory/framework/system.

    Usage:
        scorer = UnifiedCoherenceScorer()
        result = scorer.score_document(text)
        print(f"χ = {result.chi}, κ = {result.kappa}, ρ = {result.rho}")
    """

    def __init__(self, rubrics_path: Optional[Path] = None):
        """Initialize with rubric files"""
        if rubrics_path is None:
            rubrics_path = Path(__file__).parent / "rubrics"
        elif isinstance(rubrics_path, str):
            rubrics_path = Path(rubrics_path)

        self.rubrics_path = rubrics_path
        self.fruit_matrix = self._load_rubric("fruit_matrix.yaml")
        self.constraint_rubric = self._load_rubric("constraint_rubric.yaml")
        self.defense_rubric = self._load_rubric("defense_rubric.yaml")
        self.variable_rubric = self._load_rubric("variable_rubric.yaml")

        # Compile keyword patterns for efficiency
        self._compile_patterns()

    def _load_rubric(self, filename: str) -> Dict:
        """Load a YAML rubric file"""
        path = self.rubrics_path / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _compile_patterns(self):
        """Compile regex patterns from rubrics for efficient matching"""
        self.fruit_patterns = {}
        self.anti_fruit_patterns = {}
        self.variable_patterns = {}
        self.constraint_patterns = {}

        # Fruit patterns
        if self.fruit_matrix and 'fruits' in self.fruit_matrix:
            for code, fruit in self.fruit_matrix['fruits'].items():
                if 'detection_keywords' in fruit:
                    positive = fruit['detection_keywords'].get('positive', [])
                    negative = fruit['detection_keywords'].get('negative', [])
                    if positive:
                        pattern = r'\b(' + '|'.join(re.escape(k) for k in positive) + r')\b'
                        self.fruit_patterns[code] = re.compile(pattern, re.IGNORECASE)
                    if negative:
                        pattern = r'\b(' + '|'.join(re.escape(k) for k in negative) + r')\b'
                        self.anti_fruit_patterns[code] = re.compile(pattern, re.IGNORECASE)

        # Variable patterns
        if self.variable_rubric and 'variables' in self.variable_rubric:
            for code, var in self.variable_rubric['variables'].items():
                if 'detection_keywords' in var:
                    keywords = var['detection_keywords'].get('primary', [])
                    keywords += var['detection_keywords'].get('secondary', [])
                    if keywords:
                        pattern = r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'
                        self.variable_patterns[code] = re.compile(pattern, re.IGNORECASE)

    def score_document(self, text: str, title: str = "Unknown") -> CoherenceResult:
        """
        Score a document/theory for coherence.

        Args:
            text: The full text content to evaluate
            title: Optional title for reporting

        Returns:
            CoherenceResult with χ, κ, ρ and full breakdown
        """
        # Normalize text
        text = self._normalize_text(text)
        token_count = len(text.split())

        # Extract evidence units
        evidence_units = self._extract_evidence_units(text)

        # Score all layers
        fruits = self._score_fruits(text, token_count)
        constraints = self._score_constraints(text, evidence_units)
        variables = self._score_variables(text, token_count)
        defense = self._score_defense(text, evidence_units)

        # Compute triad scores from fruits
        triad = self._compute_triad(fruits, variables)

        # Compute χ (geometric mean of triads)
        chi_raw = self._compute_chi(triad)

        # Apply vetoes and floors
        chi, vetoes = self._apply_vetoes(chi_raw, constraints)

        # Compute κ (confidence)
        kappa = self._compute_kappa(evidence_units, defense, token_count)

        # Compute ρ (robustness) - simplified version
        rho = self._compute_rho(constraints, fruits)

        # Count total metrics
        metrics_count = len(fruits) * 2 + len(constraints) + len(variables) * 3 + 5

        # Collect warnings
        warnings = self._generate_warnings(fruits, constraints, variables, defense)

        return CoherenceResult(
            chi=chi,
            kappa=kappa,
            rho=rho,
            triad=triad,
            fruits=fruits,
            constraints=constraints,
            variables=variables,
            defense=defense,
            metrics_count=metrics_count,
            evidence_units_count=len(evidence_units),
            vetoes_applied=vetoes,
            warnings=warnings
        )

    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis"""
        # Remove markdown formatting
        text = re.sub(r'```[\s\S]*?```', '', text)  # Code blocks
        text = re.sub(r'`[^`]+`', '', text)  # Inline code
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        text = re.sub(r'[#*_]+', '', text)  # Headers and emphasis
        text = re.sub(r'\n+', '\n', text)  # Multiple newlines
        return text.strip()

    def _extract_evidence_units(self, text: str) -> List[EvidenceUnit]:
        """Extract evidence units from text"""
        units = []
        sentences = re.split(r'[.!?]+', text)

        # Patterns for different evidence types
        claim_patterns = [
            r'\b(therefore|thus|hence|consequently|implies|proves|demonstrates)\b',
            r'\b(claim|assert|argue|propose|hypothesis|thesis)\b'
        ]
        definition_patterns = [
            r'\b(define|definition|means|refers to|is defined as)\b',
            r':=|≡|≜'
        ]
        test_patterns = [
            r'\b(test|falsify|verify|experiment|measure|observe|predict)\b',
            r'\b(would disprove|would refute|would falsify)\b'
        ]
        equation_patterns = [
            r'[=<>≤≥≠∝∈∀∃∑∏∫]',
            r'\b(equation|formula|function|operator)\b'
        ]

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue

            # Determine type and strength
            unit_type = "claim"
            strength = 0.3

            for pattern in claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    unit_type = "claim"
                    strength = 0.5
                    break

            for pattern in definition_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    unit_type = "definition"
                    strength = 0.7
                    break

            for pattern in test_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    unit_type = "test"
                    strength = 0.9
                    break

            for pattern in equation_patterns:
                if re.search(pattern, sentence):
                    unit_type = "equation"
                    strength = 0.8
                    break

            units.append(EvidenceUnit(
                unit_type=unit_type,
                text=sentence[:200],
                location=f"sentence_{i}",
                strength=strength
            ))

        return units

    def _score_fruits(self, text: str, token_count: int) -> List[FruitScore]:
        """Score all 12 fruits and anti-fruits"""
        results = []

        if not self.fruit_matrix or 'fruits' not in self.fruit_matrix:
            return results

        for code, fruit in self.fruit_matrix['fruits'].items():
            # Count positive matches (rate-based)
            positive_count = 0
            if code in self.fruit_patterns:
                matches = self.fruit_patterns[code].findall(text)
                positive_count = len(matches)

            # Count negative matches
            negative_count = 0
            if code in self.anti_fruit_patterns:
                matches = self.anti_fruit_patterns[code].findall(text)
                negative_count = len(matches)

            # Normalize by token count (per 1000 tokens)
            rate_multiplier = 1000 / max(token_count, 100)

            # Score calculation (sigmoid-like scaling)
            positive_rate = positive_count * rate_multiplier
            negative_rate = negative_count * rate_multiplier

            # Convert to 0-1 scale with diminishing returns
            score = 1 - math.exp(-0.1 * positive_rate)
            anti_score = 1 - math.exp(-0.1 * negative_rate)

            results.append(FruitScore(
                code=code,
                name=fruit.get('name', code),
                score=score,
                anti_score=anti_score,
                net=score - anti_score
            ))

        return results

    def _score_constraints(self, text: str, evidence_units: List[EvidenceUnit]) -> List[ConstraintResult]:
        """Score all 9 constraints"""
        results = []

        if not self.constraint_rubric or 'constraints' not in self.constraint_rubric:
            return results

        for code, constraint in self.constraint_rubric['constraints'].items():
            # Get detection signals
            signals = constraint.get('detection_signals', {})
            satisfied_signals = signals.get('satisfied', [])
            violated_signals = signals.get('violated', [])

            # Check for satisfied signals
            satisfied_count = 0
            for signal in satisfied_signals:
                if re.search(re.escape(signal), text, re.IGNORECASE):
                    satisfied_count += 1

            # Check for violated signals
            violated_count = 0
            for signal in violated_signals:
                if re.search(re.escape(signal), text, re.IGNORECASE):
                    violated_count += 1

            # Determine score
            if satisfied_count > violated_count and satisfied_count > 0:
                score = ConstraintScore.SATISFIED
                rationale = f"Satisfied signals: {satisfied_count}"
            elif violated_count > satisfied_count and violated_count > 0:
                score = ConstraintScore.VIOLATED
                rationale = f"Violated signals: {violated_count}"
            else:
                score = ConstraintScore.NEUTRAL
                rationale = "Indeterminate"

            results.append(ConstraintResult(
                code=code,
                name=constraint.get('name', code),
                score=score,
                rationale=rationale
            ))

        return results

    def _score_variables(self, text: str, token_count: int) -> List[VariableResult]:
        """Score all 10 Master Equation variables"""
        results = []

        if not self.variable_rubric or 'variables' not in self.variable_rubric:
            return results

        # First pass: detect presence and count
        var_counts = {}
        for code, pattern in self.variable_patterns.items():
            matches = pattern.findall(text)
            var_counts[code] = len(matches)

        # Second pass: compute scores
        max_count = max(var_counts.values()) if var_counts else 1

        for code, var in self.variable_rubric['variables'].items():
            count = var_counts.get(code, 0)

            # Presence: binary
            presence = 1.0 if count > 0 else 0.0

            # Centrality: relative frequency
            centrality = count / max(max_count, 1)

            # Bridge score: simplified - how many other variables co-occur
            bridge_score = 0.0
            if count > 0:
                co_occurring = sum(1 for c in var_counts.values() if c > 0)
                bridge_score = min(co_occurring / 10, 1.0)

            results.append(VariableResult(
                code=code,
                name=var.get('name', code),
                presence=presence,
                centrality=centrality,
                bridge_score=bridge_score
            ))

        return results

    def _score_defense(self, text: str, evidence_units: List[EvidenceUnit]) -> DefenseResult:
        """Score defense layer (UTDGS)"""
        # Objection anticipation
        objection_patterns = [
            r'\b(however|critics|objection|counterargument|skeptics|alternatively)\b',
            r'\b(one might argue|some may say|it could be argued)\b'
        ]
        objection_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in objection_patterns)
        objection_score = min(objection_count / 10, 1.0)

        # Response strength (evidence in responses)
        response_patterns = [
            r'\b(this is addressed|in response|this objection fails|however, evidence shows)\b'
        ]
        response_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in response_patterns)
        response_score = min(response_count / 5, 1.0)

        # Evidence depth
        test_units = [u for u in evidence_units if u.unit_type == 'test']
        equation_units = [u for u in evidence_units if u.unit_type == 'equation']
        evidence_score = min((len(test_units) + len(equation_units)) / 20, 1.0)

        # Chain completeness
        chain_patterns = [r'\b(therefore|thus|hence|it follows|consequently)\b']
        chain_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in chain_patterns)
        chain_score = min(chain_count / 10, 1.0)

        # Width adequacy
        definition_units = [u for u in evidence_units if u.unit_type == 'definition']
        width_score = min(len(definition_units) / 10, 1.0)

        # Claims to evidence ratio
        claim_units = [u for u in evidence_units if u.unit_type == 'claim']
        evidence_total = len(test_units) + len(equation_units) + len(definition_units)
        cer = len(claim_units) / max(evidence_total, 1)

        # Kill conditions
        kill_patterns = [r'\b(would falsify|would disprove|would refute|if not.*then false)\b']
        kill_count = sum(len(re.findall(p, text, re.IGNORECASE)) for p in kill_patterns)

        # Total defense score (weighted)
        total = (
            objection_score * 0.20 +
            response_score * 0.20 +
            evidence_score * 0.25 +
            chain_score * 0.20 +
            width_score * 0.15
        )

        return DefenseResult(
            objection_anticipation=objection_score,
            response_strength=response_score,
            evidence_depth=evidence_score,
            chain_completeness=chain_score,
            width_adequacy=width_score,
            total=total,
            claims_evidence_ratio=cer,
            kill_conditions_count=kill_count
        )

    def _compute_triad(self, fruits: List[FruitScore], variables: List[VariableResult]) -> TriadScores:
        """Compute triad scores (Pi, A, Lambda) from fruits and variables"""
        # Initialize component scores
        pi_components = {'IT': 0.5, 'SC': 0.5, 'PI': 0.5, 'EC': 0.5}
        a_components = {'PS': 0.5, 'MP': 0.5, 'SE': 0.5, 'AE': 0.5}
        lambda_components = {'SR': 0.5, 'EI': 0.5, 'IC': 0.5, 'SM': 0.5}

        # Apply fruit contributions
        if self.fruit_matrix and 'fruits' in self.fruit_matrix:
            for fruit in fruits:
                fruit_def = self.fruit_matrix['fruits'].get(fruit.code, {})
                mapping = fruit_def.get('triad_mapping', {})

                for component, weight in mapping.items():
                    value = 0.5 + (fruit.net * weight * 0.5)  # Scale around 0.5
                    value = max(0, min(1, value))

                    if component.startswith('Pi_'):
                        key = component.replace('Pi_', '')
                        if key in pi_components:
                            pi_components[key] = (pi_components[key] + value) / 2
                    elif component.startswith('A_'):
                        key = component.replace('A_', '')
                        if key in a_components:
                            a_components[key] = (a_components[key] + value) / 2
                    elif component.startswith('Lambda_'):
                        key = component.replace('Lambda_', '')
                        if key in lambda_components:
                            lambda_components[key] = (lambda_components[key] + value) / 2

        # Compute triad totals (geometric mean of components)
        epsilon = 1e-6

        pi = math.exp(sum(math.log(v + epsilon) for v in pi_components.values()) / len(pi_components))
        a = math.exp(sum(math.log(v + epsilon) for v in a_components.values()) / len(a_components))
        lambda_ = math.exp(sum(math.log(v + epsilon) for v in lambda_components.values()) / len(lambda_components))

        return TriadScores(
            pi=pi,
            pi_components=pi_components,
            a=a,
            a_components=a_components,
            lambda_=lambda_,
            lambda_components=lambda_components
        )

    def _compute_chi(self, triad: TriadScores) -> float:
        """Compute χ as geometric mean of triads, scaled to 0-10"""
        epsilon = 1e-6
        chi_raw = math.exp((
            math.log(triad.pi + epsilon) +
            math.log(triad.a + epsilon) +
            math.log(triad.lambda_ + epsilon)
        ) / 3)

        # Scale to 0-10
        return chi_raw * 10

    def _apply_vetoes(self, chi: float, constraints: List[ConstraintResult]) -> Tuple[float, List[str]]:
        """Apply veto rules that cap χ"""
        vetoes = []

        if self.constraint_rubric and 'scoring' in self.constraint_rubric:
            veto_rules = self.constraint_rubric['scoring'].get('vetoes', [])

            for rule in veto_rules:
                constraint_code = rule.get('constraint', '')
                max_chi = rule.get('max_chi_if_violated', 10)

                for c in constraints:
                    if c.code == constraint_code and c.score == ConstraintScore.VIOLATED:
                        if chi > max_chi:
                            vetoes.append(f"{c.name} violated → χ capped at {max_chi}")
                            chi = max_chi

        return chi, vetoes

    def _compute_kappa(self, evidence_units: List[EvidenceUnit], defense: DefenseResult, token_count: int) -> float:
        """Compute κ (confidence)"""
        # Evidence density
        evidence_density = len(evidence_units) / max(token_count / 100, 1)
        kappa_extract = min(evidence_density, 1.0)

        # Evidence quality
        high_strength = [u for u in evidence_units if u.strength >= 0.7]
        kappa_evidence = len(high_strength) / max(len(evidence_units), 1)

        # Defense contribution
        kappa_defense = defense.total

        # Combined
        kappa = (kappa_extract * 0.3 + kappa_evidence * 0.4 + kappa_defense * 0.3)

        return min(max(kappa, 0), 1)

    def _compute_rho(self, constraints: List[ConstraintResult], fruits: List[FruitScore]) -> float:
        """Compute ρ (robustness) - simplified version"""
        # Constraint stability
        satisfied = sum(1 for c in constraints if c.score == ConstraintScore.SATISFIED)
        constraint_stability = satisfied / max(len(constraints), 1)

        # Fruit balance (low variance = high robustness)
        if fruits:
            net_scores = [f.net for f in fruits]
            variance = np.var(net_scores) if len(net_scores) > 1 else 0
            fruit_balance = 1 - min(variance, 1)
        else:
            fruit_balance = 0.5

        # Combined
        rho = (constraint_stability * 0.6 + fruit_balance * 0.4)

        return min(max(rho, 0), 1)

    def _generate_warnings(self, fruits: List[FruitScore], constraints: List[ConstraintResult],
                          variables: List[VariableResult], defense: DefenseResult) -> List[str]:
        """Generate warnings about potential issues"""
        warnings = []

        # Low fruit scores
        for f in fruits:
            if f.score < 0.2 and f.code in ['F8_truth', 'F7_peace', 'F5_self_control']:
                warnings.append(f"⚠️ {f.name} critically low ({f.score:.2f})")

        # Violated critical constraints
        for c in constraints:
            if c.score == ConstraintScore.VIOLATED and c.code in ['C7_consistency', 'C9_boundary_regulation']:
                warnings.append(f"⚠️ Critical constraint violated: {c.name}")

        # Missing variables
        missing = [v for v in variables if v.presence == 0]
        if len(missing) > 5:
            warnings.append(f"⚠️ {len(missing)}/10 core variables absent")

        # Defense issues
        if defense.claims_evidence_ratio > 5:
            warnings.append(f"⚠️ Claims-to-evidence ratio high ({defense.claims_evidence_ratio:.1f})")

        if defense.kill_conditions_count == 0:
            warnings.append("⚠️ No kill conditions detected - may be unfalsifiable")

        return warnings

    def generate_report(self, result: CoherenceResult, title: str = "Document") -> str:
        """Generate human-readable report"""
        lines = []

        lines.append("=" * 70)
        lines.append(f"COHERENCE ANALYSIS: {title}")
        lines.append("=" * 70)
        lines.append("")

        # Top-level scores
        lines.append(f"χ = {result.chi:.1f}  |  κ = {result.kappa:.2f}  |  ρ = {result.rho:.2f}")
        lines.append("")

        # Triad breakdown
        lines.append("TRIAD BREAKDOWN")
        lines.append("-" * 40)
        lines.append(f"  Pi (Polis):     {result.triad.pi:.2f}")
        for k, v in result.triad.pi_components.items():
            lines.append(f"    {k}: {v:.2f}")
        lines.append(f"  A (Anthropos):  {result.triad.a:.2f}")
        for k, v in result.triad.a_components.items():
            lines.append(f"    {k}: {v:.2f}")
        lines.append(f"  Λ (Logos):      {result.triad.lambda_:.2f}")
        for k, v in result.triad.lambda_components.items():
            lines.append(f"    {k}: {v:.2f}")
        lines.append("")

        # Constraints
        lines.append("STRUCTURE (9 Constraints)")
        lines.append("-" * 40)
        for c in result.constraints:
            symbol = "✓" if c.score == ConstraintScore.SATISFIED else ("✗" if c.score == ConstraintScore.VIOLATED else "-")
            lines.append(f"  [{symbol}] {c.name}: {c.score.value:+d}")
        net = sum(c.score.value for c in result.constraints)
        lines.append(f"  NET: {net:+d}/9")
        lines.append("")

        # Top fruits
        lines.append("FRUITS (Top 5 / Bottom 3)")
        lines.append("-" * 40)
        sorted_fruits = sorted(result.fruits, key=lambda f: f.net, reverse=True)
        for f in sorted_fruits[:5]:
            bar = "█" * int(f.net * 10 + 5) if f.net >= 0 else "░" * int(-f.net * 10)
            lines.append(f"  {f.name}: {f.net:+.2f} {bar}")
        lines.append("  ...")
        for f in sorted_fruits[-3:]:
            bar = "█" * int(f.net * 10 + 5) if f.net >= 0 else "░" * int(-f.net * 10)
            lines.append(f"  {f.name}: {f.net:+.2f} {bar}")
        lines.append("")

        # Variables
        lines.append("VARIABLES (10 χ Components)")
        lines.append("-" * 40)
        present = sum(1 for v in result.variables if v.presence > 0)
        lines.append(f"  Coverage: {present}/10")
        top_vars = sorted(result.variables, key=lambda v: v.centrality, reverse=True)[:5]
        for v in top_vars:
            if v.presence > 0:
                lines.append(f"  {v.name}: centrality={v.centrality:.2f}, bridge={v.bridge_score:.2f}")
        lines.append("")

        # Defense
        lines.append("DEFENSE")
        lines.append("-" * 40)
        lines.append(f"  Total: {result.defense.total:.2f}")
        lines.append(f"  Evidence Depth: {result.defense.evidence_depth:.2f}")
        lines.append(f"  Claims/Evidence: {result.defense.claims_evidence_ratio:.1f}")
        lines.append(f"  Kill Conditions: {result.defense.kill_conditions_count}")
        lines.append("")

        # Warnings
        if result.warnings:
            lines.append("WARNINGS")
            lines.append("-" * 40)
            for w in result.warnings:
                lines.append(f"  {w}")
            lines.append("")

        # Vetoes
        if result.vetoes_applied:
            lines.append("VETOES APPLIED")
            lines.append("-" * 40)
            for v in result.vetoes_applied:
                lines.append(f"  {v}")
            lines.append("")

        lines.append("=" * 70)
        lines.append(f"Metrics evaluated: {result.metrics_count}")
        lines.append(f"Evidence units: {result.evidence_units_count}")
        lines.append("=" * 70)

        return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Score a theory document from file or run test"""
    import sys
    import io
    
    # Force UTF-8 output for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    # Check for file argument
    if len(sys.argv) > 1:
        filepath = Path(sys.argv[1])
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        
        # Read file
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            title = filepath.stem
        except Exception as e:
            print(f"Error reading file: {e}")
            sys.exit(1)
        
        # Score document
        scorer = UnifiedCoherenceScorer()
        result = scorer.score_document(text, title=title)
        
        # Generate report
        report = scorer.generate_report(result, title=title)
        print(report)
        
        # Save outputs
        output_dir = filepath.parent
        report_file = output_dir / f"{title}_report.txt"
        json_file = output_dir / f"{title}_scores.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"\n\nOutputs saved:")
        print(f"  Report: {report_file}")
        print(f"  JSON: {json_file}")
        
    else:
        # Run test with sample
        sample_text = """
        # The Theory of Coherent Systems

        ## Definition
        Coherence is defined as the degree to which a system's components
        mutually reinforce rather than contradict each other.

        ## Core Claims

        Therefore, we claim that truth is the fundamental substrate of reality.
        This implies that information cannot be destroyed, only transformed.

        However, critics may argue that this is unfalsifiable.
        In response, we note that the theory would be falsified if we observed
        genuine information loss in closed systems.

        ## Evidence

        The equation χ = (Π × A × Λ)^(1/3) describes the coherence function.

        Experimental tests show that coherent systems exhibit greater resilience.
        Statistical analysis confirms p < 0.001.

        ## Conclusions

        Thus, we conclude that coherence is a measurable property of structure,
        not belief. This applies across physics, psychology, economics, and law.

        Grace, truth, and faithfulness are the primary stabilizers.
        Deception, chaos, and cynicism are the primary destabilizers.
        """

        # Initialize scorer
        scorer = UnifiedCoherenceScorer()

        # Score the sample
        result = scorer.score_document(sample_text, title="Sample Theory")

        # Generate report
        report = scorer.generate_report(result, title="Sample Theory")
        print(report)

        # Export JSON
        json_output = json.dumps(result.to_dict(), indent=2)
        print("\n\nJSON OUTPUT:")
        print(json_output)


if __name__ == "__main__":
    main()
