"""
Theophysics Analytics Package
==============================
Comprehensive analytics suite for measuring coherence, completeness, and statistical properties.

NEW in v2.0:
- 50 baseline metrics per paper
- Wisdom vs Knowledge scoring
- Fruits of the Spirit quantification
- Master Equation variable implementation
- Multi-level comparison (individual, subset, aggregate)
- Trend analysis with visualization
- Interactive HTML dashboards
"""

from .coherence_scorer import score_document, print_report
from .axiom_scorer import scan_axioms, score_document as score_axiom
from .paper_metrics_engine import PaperMetrics, PaperMetricsEngine
from .paper_comparison_engine import PaperComparisonEngine, ComparisonResult, AggregateMetrics
from .comprehensive_dashboard_generator import ComprehensiveDashboardGenerator

__all__ = [
    # Legacy coherence scoring
    'score_document',
    'print_report',
    'scan_axioms',
    'score_axiom',
    
    # New comprehensive metrics (v2.0)
    'PaperMetrics',
    'PaperMetricsEngine',
    'PaperComparisonEngine',
    'ComparisonResult',
    'AggregateMetrics',
    'ComprehensiveDashboardGenerator',
]

__version__ = '2.0.0'
