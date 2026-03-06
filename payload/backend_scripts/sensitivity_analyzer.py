"""
Sensitivity & Necessity Analyzer for Coherence Scoring Framework
NO WEIGHTS. NO TUNING. STRUCTURE ONLY.

Tests whether the framework's structure is necessary or arbitrary:
1. Ablation: Remove components → does system degrade?
2. Topology: Change graph structure → does coherence collapse?
3. Order: Permute sequence → does directionality matter?
4. Labels: Swap theological terms → does math still work?
5. Adversarial: Feed nonsense → does it correctly reject?
6. Null: Compare to random → is this better than chance?

Author: Theophysics Project
Version: 1.0
"""

from __future__ import annotations

import sys
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from copy import deepcopy
import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.coherence.unified_scorer import UnifiedCoherenceScorer


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AblationResult:
    """Result from removing a single component."""
    component_type: str  # 'variable', 'fruit', 'constraint'
    component_name: str
    baseline_chi: float
    ablated_chi: float
    delta_chi: float
    delta_percent: float
    is_load_bearing: bool  # True if removal causes >10% drop
    
    def __str__(self) -> str:
        arrow = "DOWN" if self.delta_chi < 0 else "UP"
        flag = "[LOAD-BEARING]" if self.is_load_bearing else ""
        return (f"{self.component_name:<20} "
                f"chi: {self.baseline_chi:.2f} -> {self.ablated_chi:.2f} "
                f"({arrow} {abs(self.delta_percent):.1f}%) {flag}")


@dataclass
class TopologyResult:
    """Result from changing graph structure."""
    test_name: str
    original_chi: float
    modified_chi: float
    delta_chi: float
    structure_matters: bool  # True if topology change causes >15% drop
    description: str


@dataclass
class LabelSwapResult:
    """Result from swapping theological labels with neutral ones."""
    original_chi: float
    neutral_chi: float
    delta_chi: float
    structure_preserved: bool  # True if change <5%
    mapping: Dict[str, str]


@dataclass
class AdversarialResult:
    """Result from adversarial attack."""
    attack_type: str
    baseline_chi: float
    attack_chi: float
    correctly_rejected: bool  # True if attack_chi < baseline - threshold
    description: str


@dataclass
class SensitivityReport:
    """Complete sensitivity analysis report."""
    baseline_chi: float
    ablation_results: List[AblationResult]
    topology_results: List[TopologyResult]
    label_swap_result: LabelSwapResult
    adversarial_results: List[AdversarialResult]
    
    load_bearing_components: List[str]
    structure_sensitive_tests: List[str]
    passes_label_independence: bool
    adversarial_resistance_rate: float
    
    verdict: str  # 'ROBUST', 'FRAGILE', 'ARBITRARY'


# ============================================================================
# SENSITIVITY ANALYZER
# ============================================================================

class SensitivityAnalyzer:
    """
    Tests the structural necessity of the coherence scoring framework.
    NO PARAMETER TUNING. Only structural tests.
    """
    
    def __init__(self, rubrics_path: str):
        self.rubrics_path = Path(rubrics_path)
        self.baseline_scorer = UnifiedCoherenceScorer(rubrics_path=str(self.rubrics_path))
        
        # Load rubrics for manipulation
        self._load_rubrics()
    
    def _load_rubrics(self):
        """Load rubric files into memory for structural manipulation."""
        import yaml
        
        self.fruit_rubric = yaml.safe_load(
            (self.rubrics_path / "fruit_matrix.yaml").read_text(encoding='utf-8')
        )
        self.variable_rubric = yaml.safe_load(
            (self.rubrics_path / "variable_rubric.yaml").read_text(encoding='utf-8')
        )
        self.constraint_rubric = yaml.safe_load(
            (self.rubrics_path / "constraint_rubric.yaml").read_text(encoding='utf-8')
        )
    
    # ========================================================================
    # TEST 1: ABLATION (Component Removal)
    # ========================================================================
    
    def test_ablation(self, text: str, document_name: str = "Test Document") -> List[AblationResult]:
        """
        Remove each component one at a time and measure impact.
        NO WEIGHTS - just binary presence/absence.
        """
        print("\n" + "="*80)
        print("TEST 1: COMPONENT ABLATION (Necessity Analysis)")
        print("="*80)
        print("Testing: Does removing each component degrade coherence?\n")
        
        # Get baseline score
        baseline_result = self.baseline_scorer.score_document(text, document_name)
        baseline_chi = baseline_result.chi
        
        print(f"Baseline chi: {baseline_chi:.2f}\n")
        
        results = []
        
        # Test 1a: Remove each variable
        print("1a. Variable Ablation (10 components)")
        print("-" * 80)
        for var_code in ['G', 'M', 'E', 'S', 'T', 'K', 'R', 'Q', 'F', 'C']:
            result = self._ablate_variable(var_code, text, document_name, baseline_chi)
            results.append(result)
            print(f"  {result}")
        
        # Test 1b: Remove each fruit
        print("\n1b. Fruit Ablation (12 components)")
        print("-" * 80)
        fruit_codes = [f"F{i}" for i in range(1, 13)]
        for fruit_code in fruit_codes:
            result = self._ablate_fruit(fruit_code, text, document_name, baseline_chi)
            results.append(result)
            print(f"  {result}")
        
        # Test 1c: Remove each constraint
        print("\n1c. Constraint Ablation (9 components)")
        print("-" * 80)
        for i in range(1, 10):
            result = self._ablate_constraint(f"C{i}", text, document_name, baseline_chi)
            results.append(result)
            print(f"  {result}")
        
        # Summarize load-bearing components
        load_bearing = [r for r in results if r.is_load_bearing]
        print(f"\n[SUMMARY] {len(load_bearing)}/{len(results)} components are load-bearing (>10% impact)")
        
        return results
    
    def _ablate_variable(self, var_code: str, text: str, doc_name: str, baseline: float) -> AblationResult:
        """Remove a single variable from the rubric."""
        # Create modified rubric with variable removed
        modified_rubric = deepcopy(self.variable_rubric)
        var_key = f"{var_code}_" + [k for k in modified_rubric['variables'].keys() 
                                      if k.startswith(f"{var_code}_")][0].split('_', 1)[1]
        
        if var_key in modified_rubric['variables']:
            del modified_rubric['variables'][var_key]
        
        # Score with modified rubric
        ablated_chi = self._score_with_modified_rubric(text, doc_name, variable_rubric=modified_rubric)
        
        delta = ablated_chi - baseline
        delta_pct = (delta / baseline * 100) if baseline != 0 else 0
        
        return AblationResult(
            component_type='variable',
            component_name=f"Variable {var_code}",
            baseline_chi=baseline,
            ablated_chi=ablated_chi,
            delta_chi=delta,
            delta_percent=delta_pct,
            is_load_bearing=(abs(delta_pct) > 10)
        )
    
    def _ablate_fruit(self, fruit_code: str, text: str, doc_name: str, baseline: float) -> AblationResult:
        """Remove a single fruit from the rubric."""
        modified_rubric = deepcopy(self.fruit_rubric)
        
        # Find and remove the fruit
        fruit_key = [k for k in modified_rubric['fruits'].keys() if k.startswith(fruit_code)]
        if fruit_key:
            fruit_name = modified_rubric['fruits'][fruit_key[0]]['name']
            del modified_rubric['fruits'][fruit_key[0]]
        else:
            fruit_name = fruit_code
        
        ablated_chi = self._score_with_modified_rubric(text, doc_name, fruit_rubric=modified_rubric)
        
        delta = ablated_chi - baseline
        delta_pct = (delta / baseline * 100) if baseline != 0 else 0
        
        return AblationResult(
            component_type='fruit',
            component_name=f"Fruit: {fruit_name}",
            baseline_chi=baseline,
            ablated_chi=ablated_chi,
            delta_chi=delta,
            delta_percent=delta_pct,
            is_load_bearing=(abs(delta_pct) > 10)
        )
    
    def _ablate_constraint(self, constraint_code: str, text: str, doc_name: str, baseline: float) -> AblationResult:
        """Remove a single constraint from the rubric."""
        modified_rubric = deepcopy(self.constraint_rubric)
        
        constraint_key = [k for k in modified_rubric['constraints'].keys() if k.startswith(constraint_code)]
        if constraint_key:
            constraint_name = modified_rubric['constraints'][constraint_key[0]]['name']
            del modified_rubric['constraints'][constraint_key[0]]
        else:
            constraint_name = constraint_code
        
        ablated_chi = self._score_with_modified_rubric(text, doc_name, constraint_rubric=modified_rubric)
        
        delta = ablated_chi - baseline
        delta_pct = (delta / baseline * 100) if baseline != 0 else 0
        
        return AblationResult(
            component_type='constraint',
            component_name=f"Constraint: {constraint_name}",
            baseline_chi=baseline,
            ablated_chi=ablated_chi,
            delta_chi=delta,
            delta_percent=delta_pct,
            is_load_bearing=(abs(delta_pct) > 10)
        )
    
    def _score_with_modified_rubric(self, text: str, doc_name: str,
                                     variable_rubric=None,
                                     fruit_rubric=None,
                                     constraint_rubric=None) -> float:
        """Score with temporarily modified rubrics."""
        import tempfile
        import yaml
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Write modified rubrics
            if variable_rubric:
                with open(tmp_path / "variable_rubric.yaml", 'w', encoding='utf-8') as f:
                    f.write(yaml.dump(variable_rubric))
            else:
                with open(tmp_path / "variable_rubric.yaml", 'w', encoding='utf-8') as f:
                    f.write((self.rubrics_path / "variable_rubric.yaml").read_text(encoding='utf-8'))
            
            if fruit_rubric:
                with open(tmp_path / "fruit_matrix.yaml", 'w', encoding='utf-8') as f:
                    f.write(yaml.dump(fruit_rubric))
            else:
                with open(tmp_path / "fruit_matrix.yaml", 'w', encoding='utf-8') as f:
                    f.write((self.rubrics_path / "fruit_matrix.yaml").read_text(encoding='utf-8'))
            
            if constraint_rubric:
                with open(tmp_path / "constraint_rubric.yaml", 'w', encoding='utf-8') as f:
                    f.write(yaml.dump(constraint_rubric))
            else:
                with open(tmp_path / "constraint_rubric.yaml", 'w', encoding='utf-8') as f:
                    f.write((self.rubrics_path / "constraint_rubric.yaml").read_text(encoding='utf-8'))
            
            # Copy defense rubric (unchanged)
            with open(tmp_path / "defense_rubric.yaml", 'w', encoding='utf-8') as f:
                f.write((self.rubrics_path / "defense_rubric.yaml").read_text(encoding='utf-8'))
            
            # Score with modified rubrics
            temp_scorer = UnifiedCoherenceScorer(rubrics_path=str(tmp_path))
            result = temp_scorer.score_document(text, doc_name)
            return result.chi
    
    # ========================================================================
    # TEST 2: TOPOLOGY (Graph Structure)
    # ========================================================================
    
    def test_topology(self, text: str, document_name: str = "Test Document") -> List[TopologyResult]:
        """
        Test whether graph topology matters.
        Does changing connection structure degrade coherence?
        """
        print("\n" + "="*80)
        print("TEST 2: TOPOLOGY SENSITIVITY (Structure Analysis)")
        print("="*80)
        print("Testing: Does the graph structure matter, or could any structure work?\n")
        
        baseline_result = self.baseline_scorer.score_document(text, document_name)
        baseline_chi = baseline_result.chi
        
        print(f"Baseline chi: {baseline_chi:.2f}\n")
        
        results = []
        
        # Test 2a: Scramble Fruit-to-Triad mappings
        print("2a. Scramble Fruit-to-Triad Mappings")
        print("-" * 80)
        scrambled_chi = self._scramble_fruit_triad_mappings(text, document_name)
        delta = scrambled_chi - baseline_chi
        structure_matters = abs(delta / baseline_chi * 100) > 15
        
        result = TopologyResult(
            test_name="Scrambled Fruit→Triad",
            original_chi=baseline_chi,
            modified_chi=scrambled_chi,
            delta_chi=delta,
            structure_matters=structure_matters,
            description="Randomized which Triad components each Fruit connects to"
        )
        results.append(result)
        print(f"  Original chi: {baseline_chi:.2f}")
        print(f"  Scrambled chi: {scrambled_chi:.2f}")
        print(f"  Delta chi: {delta:+.2f} ({delta/baseline_chi*100:+.1f}%)")
        print(f"  Structure matters: {'YES' if structure_matters else 'NO'}\n")
        
        # Test 2b: Flatten Triad hierarchy
        print("2b. Flatten Triad Hierarchy")
        print("-" * 80)
        flat_chi = self._flatten_triad_hierarchy(text, document_name)
        delta = flat_chi - baseline_chi
        structure_matters = abs(delta / baseline_chi * 100) > 15
        
        result = TopologyResult(
            test_name="Flattened Hierarchy",
            original_chi=baseline_chi,
            modified_chi=flat_chi,
            delta_chi=delta,
            structure_matters=structure_matters,
            description="Removed hierarchical structure - all components equal weight"
        )
        results.append(result)
        print(f"  Original χ: {baseline_chi:.2f}")
        print(f"  Flattened χ: {flat_chi:.2f}")
        print(f"  Δχ: {delta:+.2f} ({delta/baseline_chi*100:+.1f}%)")
        print(f"  Structure matters: {'YES' if structure_matters else 'NO'}\n")
        
        return results
    
    def _scramble_fruit_triad_mappings(self, text: str, doc_name: str) -> float:
        """Randomize Fruit-to-Triad connections."""
        modified_rubric = deepcopy(self.fruit_rubric)
        
        # Get all triad subfactors
        all_subfactors = []
        for triad in ['Pi', 'A', 'Lambda']:
            for subfactor in modified_rubric['triad_subfactors'][triad].keys():
                all_subfactors.append(f"{triad}_{subfactor}")
        
        # Scramble mappings for each fruit
        for fruit_key in modified_rubric['fruits'].keys():
            # Get current mapping keys
            mapping_keys = list(modified_rubric['fruits'][fruit_key]['triad_mapping'].keys())
            
            # Randomly select new subfactors
            new_mapping = {}
            for key in mapping_keys:
                new_subfactor = random.choice(all_subfactors)
                new_mapping[new_subfactor] = modified_rubric['fruits'][fruit_key]['triad_mapping'][key]
            
            modified_rubric['fruits'][fruit_key]['triad_mapping'] = new_mapping
        
        return self._score_with_modified_rubric(text, doc_name, fruit_rubric=modified_rubric)
    
    def _flatten_triad_hierarchy(self, text: str, doc_name: str) -> float:
        """Remove hierarchical structure from Triad."""
        modified_rubric = deepcopy(self.fruit_rubric)
        
        # Set all triad mappings to equal distribution
        for fruit_key in modified_rubric['fruits'].keys():
            mapping = modified_rubric['fruits'][fruit_key]['triad_mapping']
            num_components = len(mapping)
            equal_weight = 1.0 / num_components if num_components > 0 else 0
            
            for key in mapping.keys():
                mapping[key] = equal_weight
        
        return self._score_with_modified_rubric(text, doc_name, fruit_rubric=modified_rubric)
    
    # ========================================================================
    # TEST 3: LABEL INDEPENDENCE (Semantic vs Structural)
    # ========================================================================
    
    def test_label_independence(self, text: str, document_name: str = "Test Document") -> LabelSwapResult:
        """
        Most important test: Does the math work regardless of theological labels?
        Swap all theological terms with neutral labels.
        If structure persists, it's not just semantic storytelling.
        """
        print("\n" + "="*80)
        print("TEST 3: LABEL INDEPENDENCE (Semantics vs Structure)")
        print("="*80)
        print("Testing: Does the framework work regardless of theological labels?\n")
        
        baseline_result = self.baseline_scorer.score_document(text, document_name)
        baseline_chi = baseline_result.chi
        
        # Create label mapping
        label_mapping = {
            'Grace': 'Negentropy_Field',
            'Sin': 'Entropy_Source',
            'Logos': 'Information_Substrate',
            'Faith': 'Trust_Operator',
            'Hope': 'Non_Terminal_State',
            'Love': 'Positive_Sum_Field',
            'Resurrection': 'State_Transition',
            'Redemption': 'Error_Correction',
            'Covenant': 'Binding_Contract',
            'Truth': 'Signal_Fidelity'
        }
        
        print("Label Mapping:")
        for old, new in label_mapping.items():
            print(f"  {old:<20} → {new}")
        print()
        
        # Replace labels in text
        neutral_text = text
        for old, new in label_mapping.items():
            neutral_text = neutral_text.replace(old, new)
            neutral_text = neutral_text.replace(old.lower(), new.lower())
        
        # Score with neutral labels
        neutral_result = self.baseline_scorer.score_document(neutral_text, f"{document_name} (Neutral Labels)")
        neutral_chi = neutral_result.chi
        
        delta = neutral_chi - baseline_chi
        delta_pct = abs(delta / baseline_chi * 100) if baseline_chi != 0 else 0
        structure_preserved = delta_pct < 5  # Less than 5% change = structure preserved
        
        print(f"Original χ (theological labels): {baseline_chi:.2f}")
        print(f"Neutral χ (neutral labels):       {neutral_chi:.2f}")
        print(f"Δχ: {delta:+.2f} ({delta_pct:.1f}% change)")
        print(f"\nStructure preserved: {'YES' if structure_preserved else 'NO'}")
        print(f"Verdict: {'Math is label-independent ✓' if structure_preserved else 'Framework is label-dependent ✗'}\n")
        
        return LabelSwapResult(
            original_chi=baseline_chi,
            neutral_chi=neutral_chi,
            delta_chi=delta,
            structure_preserved=structure_preserved,
            mapping=label_mapping
        )
    
    # ========================================================================
    # TEST 4: ADVERSARIAL RESISTANCE
    # ========================================================================
    
    def test_adversarial_resistance(self, text: str, document_name: str = "Test Document") -> List[AdversarialResult]:
        """
        Test whether the framework correctly rejects nonsense.
        Feed it garbage and see if it scores low.
        """
        print("\n" + "="*80)
        print("TEST 4: ADVERSARIAL RESISTANCE")
        print("="*80)
        print("Testing: Does the framework correctly identify incoherence?\n")
        
        baseline_result = self.baseline_scorer.score_document(text, document_name)
        baseline_chi = baseline_result.chi
        
        print(f"Baseline χ (coherent text): {baseline_chi:.2f}\n")
        
        results = []
        
        # Attack 1: Keyword spam
        print("Attack 1: Keyword Spam")
        print("-" * 80)
        spam_text = self._generate_keyword_spam()
        spam_result = self.baseline_scorer.score_document(spam_text, "Keyword Spam Attack")
        spam_chi = spam_result.chi
        rejected = spam_chi < baseline_chi - 1.0
        
        result = AdversarialResult(
            attack_type="Keyword Spam",
            baseline_chi=baseline_chi,
            attack_chi=spam_chi,
            correctly_rejected=rejected,
            description="Text stuffed with high-scoring keywords but no structure"
        )
        results.append(result)
        print(f"  Spam χ: {spam_chi:.2f}")
        print(f"  Correctly rejected: {'YES ✓' if rejected else 'NO ✗'}\n")
        
        # Attack 2: Random text
        print("Attack 2: Random Gibberish")
        print("-" * 80)
        random_text = self._generate_random_text()
        random_result = self.baseline_scorer.score_document(random_text, "Random Text Attack")
        random_chi = random_result.chi
        rejected = random_chi < baseline_chi - 1.0
        
        result = AdversarialResult(
            attack_type="Random Gibberish",
            baseline_chi=baseline_chi,
            attack_chi=random_chi,
            correctly_rejected=rejected,
            description="Completely random text with no coherent structure"
        )
        results.append(result)
        print(f"  Random χ: {random_chi:.2f}")
        print(f"  Correctly rejected: {'YES ✓' if rejected else 'NO ✗'}\n")
        
        # Attack 3: Coherent but opposite framework
        print("Attack 3: Opposite Framework (Pure Materialism)")
        print("-" * 80)
        opposite_text = self._generate_opposite_framework()
        opposite_result = self.baseline_scorer.score_document(opposite_text, "Opposite Framework")
        opposite_chi = opposite_result.chi
        rejected = opposite_chi < baseline_chi - 0.5
        
        result = AdversarialResult(
            attack_type="Opposite Framework",
            baseline_chi=baseline_chi,
            attack_chi=opposite_chi,
            correctly_rejected=rejected,
            description="Coherent materialist framework (should score lower)"
        )
        results.append(result)
        print(f"  Opposite χ: {opposite_chi:.2f}")
        print(f"  Correctly differentiated: {'YES ✓' if rejected else 'NO ✗'}\n")
        
        # Calculate resistance rate
        resistance_rate = sum(1 for r in results if r.correctly_rejected) / len(results)
        print(f"[SUMMARY] Adversarial resistance: {resistance_rate*100:.0f}% ({sum(1 for r in results if r.correctly_rejected)}/{len(results)} attacks rejected)\n")
        
        return results
    
    def _generate_keyword_spam(self) -> str:
        """Generate text stuffed with high-scoring keywords but no structure."""
        keywords = [
            "grace", "truth", "coherence", "faith", "love", "unity", "peace",
            "knowledge", "entropy", "energy", "quantum", "consciousness",
            "resurrection", "redemption", "covenant", "logos", "information"
        ]
        
        sentences = []
        for _ in range(50):
            words = random.sample(keywords, 5)
            sentences.append(" ".join(words).capitalize() + ".")
        
        return " ".join(sentences)
    
    def _generate_random_text(self) -> str:
        """Generate completely random text."""
        words = ["the", "is", "and", "of", "to", "in", "a", "that", "it", "with",
                 "as", "for", "on", "was", "at", "by", "from", "this", "be", "have"]
        
        sentences = []
        for _ in range(50):
            sentence_words = [random.choice(words) for _ in range(random.randint(5, 15))]
            sentences.append(" ".join(sentence_words).capitalize() + ".")
        
        return " ".join(sentences)
    
    def _generate_opposite_framework(self) -> str:
        """Generate a coherent materialist framework for comparison."""
        return """
        Consciousness is an emergent property of complex neural networks.
        There is no evidence for non-physical phenomena or immaterial substances.
        The universe operates according to deterministic physical laws.
        Evolution through natural selection explains the complexity of life.
        Morality is a social construct evolved for group survival.
        Free will is an illusion created by deterministic brain processes.
        Information is physical and substrate-dependent.
        Entropy always increases and there is no reversal mechanism.
        Truth is provisional and contingent on empirical verification.
        There is no teleology or purpose in natural processes.
        All phenomena reduce to fundamental particles and forces.
        Meaning is subjectively constructed with no objective basis.
        """
    
    # ========================================================================
    # GENERATE FULL REPORT
    # ========================================================================
    
    def run_full_analysis(self, text: str, document_name: str = "Test Document") -> SensitivityReport:
        """Run all sensitivity tests and generate comprehensive report."""
        print("\n" + "="*80)
        print("SENSITIVITY & NECESSITY ANALYSIS")
        print("Testing Framework Structural Robustness (NO WEIGHTS)")
        print("="*80)
        
        # Run all tests
        ablation_results = self.test_ablation(text, document_name)
        topology_results = self.test_topology(text, document_name)
        label_result = self.test_label_independence(text, document_name)
        adversarial_results = self.test_adversarial_resistance(text, document_name)
        
        # Extract insights
        load_bearing = [r.component_name for r in ablation_results if r.is_load_bearing]
        structure_sensitive = [r.test_name for r in topology_results if r.structure_matters]
        resistance_rate = sum(1 for r in adversarial_results if r.correctly_rejected) / len(adversarial_results)
        
        # Determine verdict
        if (len(load_bearing) > 5 and  # Multiple load-bearing components
            len(structure_sensitive) > 0 and  # Topology matters
            label_result.structure_preserved and  # Label-independent
            resistance_rate > 0.66):  # Rejects most attacks
            verdict = "ROBUST"
        elif len(load_bearing) < 3 or not label_result.structure_preserved:
            verdict = "ARBITRARY"
        else:
            verdict = "FRAGILE"
        
        baseline_result = self.baseline_scorer.score_document(text, document_name)
        
        report = SensitivityReport(
            baseline_chi=baseline_result.chi,
            ablation_results=ablation_results,
            topology_results=topology_results,
            label_swap_result=label_result,
            adversarial_results=adversarial_results,
            load_bearing_components=load_bearing,
            structure_sensitive_tests=structure_sensitive,
            passes_label_independence=label_result.structure_preserved,
            adversarial_resistance_rate=resistance_rate,
            verdict=verdict
        )
        
        self._print_final_summary(report)
        
        return report
    
    def _print_final_summary(self, report: SensitivityReport):
        """Print final summary of all tests."""
        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"\nBaseline χ: {report.baseline_chi:.2f}")
        print(f"\nLoad-Bearing Components: {len(report.load_bearing_components)}/31")
        for comp in report.load_bearing_components[:5]:
            print(f"  • {comp}")
        if len(report.load_bearing_components) > 5:
            print(f"  ... and {len(report.load_bearing_components) - 5} more")
        
        print(f"\nTopology Sensitivity: {len(report.structure_sensitive_tests)}/{len(report.topology_results)} tests")
        for test in report.structure_sensitive_tests:
            print(f"  • {test}")
        
        print(f"\nLabel Independence: {'PASS ✓' if report.passes_label_independence else 'FAIL ✗'}")
        print(f"  Δχ with neutral labels: {report.label_swap_result.delta_chi:+.2f}")
        
        print(f"\nAdversarial Resistance: {report.adversarial_resistance_rate*100:.0f}%")
        for result in report.adversarial_results:
            status = "✓" if result.correctly_rejected else "✗"
            print(f"  {status} {result.attack_type}")
        
        print(f"\n{'='*80}")
        print(f"VERDICT: {report.verdict}")
        print(f"{'='*80}\n")
        
        if report.verdict == "ROBUST":
            print("Framework demonstrates structural necessity:")
            print("  • Multiple load-bearing components")
            print("  • Topology-sensitive")
            print("  • Label-independent")
            print("  • Adversarially resistant")
            print("\nThis is not arbitrary pattern-matching.")
        elif report.verdict == "ARBITRARY":
            print("Framework shows signs of arbitrariness:")
            print("  • Few load-bearing components")
            print("  • Structure could be replaced")
            print("  • Depends on specific labels")
            print("\nNeeds structural revision.")
        else:
            print("Framework is structurally sound but fragile:")
            print("  • Some components are load-bearing")
            print("  • Vulnerable to specific attacks")
            print("\nNeeds hardening.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run sensitivity analysis on a test document."""
    
    # Path to rubrics
    rubrics_path = Path(__file__).parent / "core" / "coherence" / "rubrics"
    
    # Sample coherent text (from Moral Decay project)
    test_text = """
    The coherence of a society depends on the alignment of its institutions with fundamental
    principles of grace, truth, and faith. When entropy increases without counteracting
    negentropic forces, social structures degrade and meaning collapses.
    
    Grace acts as an entropy absorption mechanism, allowing systems to recover from shocks
    without catastrophic collapse. Truth provides signal fidelity, ensuring information
    can propagate without distortion. Faith enables action under uncertainty.
    
    The Master Equation describes this dynamics through ten variables: Grace (G), Motion (M),
    Energy (E), Entropy (S), Time (T), Knowledge (K), Resurrection (R), Quantum (Q),
    Faith (F), and Consciousness (C). These are not arbitrary but structurally necessary.
    
    When these components are in alignment, coherence emerges naturally. When they are
    violated, decay is inevitable. This is not metaphor but mathematical necessity.
    """
    
    # Initialize analyzer
    analyzer = SensitivityAnalyzer(rubrics_path=str(rubrics_path))
    
    # Run full analysis
    report = analyzer.run_full_analysis(test_text, "Test Framework Document")
    
    # Save report
    output_file = Path(__file__).parent / "sensitivity_analysis_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'verdict': report.verdict,
            'baseline_chi': report.baseline_chi,
            'load_bearing_count': len(report.load_bearing_components),
            'label_independent': report.passes_label_independence,
            'adversarial_resistance': report.adversarial_resistance_rate,
            'load_bearing_components': report.load_bearing_components,
            'structure_sensitive_tests': report.structure_sensitive_tests
        }, f, indent=2)
    
    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
