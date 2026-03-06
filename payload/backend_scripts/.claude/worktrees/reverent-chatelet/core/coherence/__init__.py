"""
Coherence Analysis Module
CDCM (Cross-Domain Coherence Metric) analysis tools
"""

from .cdcm_analyzer import (
    CDCMAnalyzer,
    FrameworkMetrics,
    ConstraintScores,
    TheoryMapping,
    load_cdcm,
)

__all__ = [
    "CDCMAnalyzer",
    "FrameworkMetrics",
    "ConstraintScores",
    "TheoryMapping",
    "load_cdcm",
]
