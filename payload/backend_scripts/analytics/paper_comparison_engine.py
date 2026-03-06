"""
Theophysics Paper Comparison Engine
====================================
Multi-level analysis:
- Individual paper analysis
- Subset comparison (P1, P3, P5)
- Full corpus aggregation
- Trend analysis over time

Enables questions like:
- How does P03 compare to P07?
- What's the average wisdom score for papers 1-6?
- Are coherence scores trending up across the series?
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from collections import defaultdict
from dataclasses import dataclass
import statistics

from .paper_metrics_engine import PaperMetrics, PaperMetricsEngine


@dataclass
class ComparisonResult:
    """Results of comparing papers."""
    papers: List[str]
    metric_comparisons: Dict[str, Dict]
    trends: Dict[str, str]  # 'up', 'down', 'stable'
    insights: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'papers': self.papers,
            'metric_comparisons': self.metric_comparisons,
            'trends': self.trends,
            'insights': self.insights,
        }


@dataclass
class AggregateMetrics:
    """Aggregated metrics across multiple papers."""
    paper_count: int
    total_words: int
    total_axioms: int
    total_equations: int
    total_citations: int
    avg_chi_score: float
    avg_wisdom_score: float
    avg_knowledge_score: float
    avg_wisdom_knowledge_ratio: float
    avg_fruits_score: float
    avg_master_equation_score: float
    trend_chi: str = "stable"
    trend_wisdom: str = "stable"
    trend_coherence: str = "stable"


class PaperComparisonEngine:
    """Compare and aggregate paper metrics."""
    
    def __init__(self):
        self.metrics_engine = PaperMetricsEngine()
        self.paper_metrics_cache: Dict[str, PaperMetrics] = {}
    
    def analyze_paper_set(self, paper_paths: List[Path]) -> List[PaperMetrics]:
        """Analyze multiple papers."""
        results = []
        for path in paper_paths:
            print(f"  Analyzing: {path.name}")
            metrics = self.metrics_engine.analyze_paper(path)
            self.paper_metrics_cache[path.stem] = metrics
            results.append(metrics)
        return results
    
    def compare_papers(self, paper_ids: List[str]) -> ComparisonResult:
        """Compare specific papers."""
        # Get metrics for each paper
        metrics_list = [self.paper_metrics_cache[pid] for pid in paper_ids if pid in self.paper_metrics_cache]
        
        if not metrics_list:
            return ComparisonResult(
                papers=[],
                metric_comparisons={},
                trends={},
                insights=["No papers found for comparison"]
            )
        
        # Compare key metrics
        comparisons = {}
        
        # Structural comparison
        comparisons['word_count'] = {
            pid: m.word_count for pid, m in zip(paper_ids, metrics_list)
        }
        comparisons['axiom_count'] = {
            pid: m.axiom_count for pid, m in zip(paper_ids, metrics_list)
        }
        
        # Coherence comparison
        comparisons['chi_score'] = {
            pid: m.chi_score for pid, m in zip(paper_ids, metrics_list)
        }
        
        # Wisdom vs Knowledge
        comparisons['wisdom_score'] = {
            pid: m.wisdom_score for pid, m in zip(paper_ids, metrics_list)
        }
        comparisons['wisdom_knowledge_ratio'] = {
            pid: m.wisdom_knowledge_ratio for pid, m in zip(paper_ids, metrics_list)
        }
        
        # Fruits composite
        comparisons['fruits_composite'] = {
            pid: m.get_composite_scores()['fruits_composite'] 
            for pid, m in zip(paper_ids, metrics_list)
        }
        
        # Master equation composite
        comparisons['master_equation_composite'] = {
            pid: m.get_composite_scores()['master_equation_composite'] 
            for pid, m in zip(paper_ids, metrics_list)
        }
        
        # Detect trends
        trends = {}
        for metric_name, values in comparisons.items():
            value_list = list(values.values())
            if len(value_list) >= 2:
                if value_list[-1] > value_list[0] * 1.1:
                    trends[metric_name] = 'up ↑'
                elif value_list[-1] < value_list[0] * 0.9:
                    trends[metric_name] = 'down ↓'
                else:
                    trends[metric_name] = 'stable →'
        
        # Generate insights
        insights = self._generate_insights(metrics_list, paper_ids)
        
        return ComparisonResult(
            papers=paper_ids,
            metric_comparisons=comparisons,
            trends=trends,
            insights=insights
        )
    
    def aggregate_corpus(self, metrics_list: List[PaperMetrics]) -> AggregateMetrics:
        """Aggregate metrics across entire corpus."""
        if not metrics_list:
            return AggregateMetrics(
                paper_count=0, total_words=0, total_axioms=0,
                total_equations=0, total_citations=0, avg_chi_score=0,
                avg_wisdom_score=0, avg_knowledge_score=0,
                avg_wisdom_knowledge_ratio=0, avg_fruits_score=0,
                avg_master_equation_score=0
            )
        
        total_words = sum(m.word_count for m in metrics_list)
        total_axioms = sum(m.axiom_count for m in metrics_list)
        total_equations = sum(m.equation_count for m in metrics_list)
        total_citations = sum(m.citation_count for m in metrics_list)
        
        avg_chi = statistics.mean(m.chi_score for m in metrics_list)
        avg_wisdom = statistics.mean(m.wisdom_score for m in metrics_list)
        avg_knowledge = statistics.mean(m.knowledge_score for m in metrics_list)
        avg_wk_ratio = statistics.mean(m.wisdom_knowledge_ratio for m in metrics_list)
        
        # Composite scores
        fruits_scores = [m.get_composite_scores()['fruits_composite'] for m in metrics_list]
        master_eq_scores = [m.get_composite_scores()['master_equation_composite'] for m in metrics_list]
        
        avg_fruits = statistics.mean(fruits_scores)
        avg_master_eq = statistics.mean(master_eq_scores)
        
        # Detect trends (first half vs second half)
        mid = len(metrics_list) // 2
        first_half_chi = statistics.mean(m.chi_score for m in metrics_list[:mid]) if mid > 0 else 0
        second_half_chi = statistics.mean(m.chi_score for m in metrics_list[mid:]) if mid > 0 else 0
        
        trend_chi = "up ↑" if second_half_chi > first_half_chi * 1.1 else "down ↓" if second_half_chi < first_half_chi * 0.9 else "stable →"
        
        return AggregateMetrics(
            paper_count=len(metrics_list),
            total_words=total_words,
            total_axioms=total_axioms,
            total_equations=total_equations,
            total_citations=total_citations,
            avg_chi_score=avg_chi,
            avg_wisdom_score=avg_wisdom,
            avg_knowledge_score=avg_knowledge,
            avg_wisdom_knowledge_ratio=avg_wk_ratio,
            avg_fruits_score=avg_fruits,
            avg_master_equation_score=avg_master_eq,
            trend_chi=trend_chi,
        )
    
    def _generate_insights(self, metrics_list: List[PaperMetrics], paper_ids: List[str]) -> List[str]:
        """Generate insights from comparison."""
        insights = []
        
        # Find highest wisdom/knowledge ratio
        best_wk = max(metrics_list, key=lambda m: m.wisdom_knowledge_ratio)
        insights.append(f"📚 Highest Wisdom/Knowledge Ratio: {best_wk.paper_name} ({best_wk.wisdom_knowledge_ratio:.2f})")
        
        # Find highest coherence
        best_chi = max(metrics_list, key=lambda m: m.chi_score)
        insights.append(f"⚛️ Highest Coherence: {best_chi.paper_name} (CHI = {best_chi.chi_score:.2f})")
        
        # Find most comprehensive
        best_comprehensive = max(metrics_list, key=lambda m: m.axiom_count + m.theorem_count + m.citation_count)
        insights.append(f"📖 Most Comprehensive: {best_comprehensive.paper_name} ({best_comprehensive.axiom_count} axioms, {best_comprehensive.citation_count} citations)")
        
        # Check for wisdom dominance
        wisdom_dominant = [m for m in metrics_list if m.wisdom_score > m.knowledge_score * 1.5]
        if wisdom_dominant:
            insights.append(f"🕊️ {len(wisdom_dominant)} papers show strong wisdom dominance (W > 1.5*K)")
        
        # Fruits analysis
        fruits_scores = [(m.paper_name, m.get_composite_scores()['fruits_composite']) for m in metrics_list]
        best_fruits = max(fruits_scores, key=lambda x: x[1])
        insights.append(f"🌱 Highest Fruits Score: {best_fruits[0]} ({best_fruits[1]:.2f}/10)")
        
        return insights
    
    def generate_trend_report(self, metrics_list: List[PaperMetrics]) -> Dict:
        """Generate trend analysis report."""
        if len(metrics_list) < 2:
            return {'error': 'Need at least 2 papers for trend analysis'}
        
        # Sort by paper number if available
        sorted_metrics = sorted(metrics_list, key=lambda m: m.paper_id)
        
        trends = {
            'paper_sequence': [m.paper_id for m in sorted_metrics],
            'chi_scores': [m.chi_score for m in sorted_metrics],
            'wisdom_scores': [m.wisdom_score for m in sorted_metrics],
            'wisdom_knowledge_ratios': [m.wisdom_knowledge_ratio for m in sorted_metrics],
            'fruits_scores': [m.get_composite_scores()['fruits_composite'] for m in sorted_metrics],
            'master_equation_scores': [m.get_composite_scores()['master_equation_composite'] for m in sorted_metrics],
        }
        
        # Calculate trend directions
        trend_directions = {}
        for metric_name, values in trends.items():
            if metric_name != 'paper_sequence' and len(values) >= 2:
                # Linear regression slope
                n = len(values)
                x = list(range(n))
                slope = (n * sum(i*v for i, v in zip(x, values)) - sum(x) * sum(values)) / (n * sum(i**2 for i in x) - sum(x)**2)
                
                if slope > 0.1:
                    trend_directions[metric_name] = 'upward ↗'
                elif slope < -0.1:
                    trend_directions[metric_name] = 'downward ↘'
                else:
                    trend_directions[metric_name] = 'stable →'
        
        trends['trend_directions'] = trend_directions
        
        return trends


def main():
    """Test comparison engine."""
    import sys
    
    print("=" * 80)
    print("THEOPHYSICS PAPER COMPARISON ENGINE - TEST")
    print("=" * 80)
    print()
    
    engine = PaperComparisonEngine()
    
    # Find Logos papers
    base_path = Path(os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3'))
    paper_folders = [
        'V3_P01-Logos-Principle', 'V3_P02-Quantum-Bridge', 'V3_P03-Algorithm-Reality',
        'V3_P04-Hard-Problem', 'V3_P05-Soul-Observer'
    ]
    
    papers_to_analyze = []
    for folder in paper_folders:
        folder_path = base_path / folder
        if folder_path.exists():
            canonicals = list(folder_path.glob("*canonical*.md"))
            if canonicals:
                papers_to_analyze.append(canonicals[0])
    
    if papers_to_analyze:
        print(f"Found {len(papers_to_analyze)} papers to analyze\n")
        
        # Analyze all papers
        print("Analyzing papers...")
        metrics_list = engine.analyze_paper_set(papers_to_analyze)
        
        # Aggregate corpus
        print("\nAGGREGATE METRICS")
        print("-" * 40)
        aggregate = engine.aggregate_corpus(metrics_list)
        print(f"Papers: {aggregate.paper_count}")
        print(f"Total Words: {aggregate.total_words:,}")
        print(f"Total Axioms: {aggregate.total_axioms}")
        print(f"Avg CHI Score: {aggregate.avg_chi_score:.2f}")
        print(f"Avg Wisdom Score: {aggregate.avg_wisdom_score:.2f}")
        print(f"Avg W/K Ratio: {aggregate.avg_wisdom_knowledge_ratio:.2f}")
        print(f"Avg Fruits Score: {aggregate.avg_fruits_score:.2f}")
        print(f"CHI Trend: {aggregate.trend_chi}")
        
        # Compare subset
        print("\n\nCOMPARING PAPERS 1, 3, 5")
        print("-" * 40)
        paper_ids = [m.paper_id for m in metrics_list][:3]  # First 3 for demo
        comparison = engine.compare_papers(paper_ids)
        
        print("\nKey Metrics Comparison:")
        for metric, values in comparison.metric_comparisons.items():
            print(f"\n  {metric}:")
            for pid, val in values.items():
                print(f"    {pid}: {val:.2f}" if isinstance(val, float) else f"    {pid}: {val}")
        
        print("\n\nTrends:")
        for metric, trend in comparison.trends.items():
            print(f"  {metric}: {trend}")
        
        print("\n\nInsights:")
        for insight in comparison.insights:
            print(f"  • {insight}")
        
        # Trend analysis
        print("\n\nTREND ANALYSIS")
        print("-" * 40)
        trends = engine.generate_trend_report(metrics_list)
        for metric, direction in trends['trend_directions'].items():
            print(f"  {metric}: {direction}")
    
    else:
        print("No papers found for analysis")


if __name__ == "__main__":
    main()
