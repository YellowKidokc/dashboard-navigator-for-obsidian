"""
THEOPHYSICS Vault Orchestrator - Modules Package
=================================================

This package contains the modular subsystems that power the
THEOPHYSICS Vault Intelligence System.

Modules:
- circulation_detector: Breakthrough prediction through pattern detection
- infrastructure_manager: Structural maintenance and organization
- uuid_semantic_manager: Cross-platform identity and tagging
- dashboard_generator: Analytics and statistics generation
- tracker_integrator: Obsidian Tracker dashboards

Author: David Lowe & Claude
Date: 2025-11-19
"""

__version__ = "1.0.0"
__author__ = "David Lowe & Claude"

# Module imports for convenience
from .circulation_detector import CirculationDetector, ConceptApproach, CirculationPattern
from .infrastructure_manager import InfrastructureManager
from .uuid_semantic_manager import UUIDSemanticManager
from .dashboard_generator import DashboardGenerator
from .tracker_integrator import TrackerIntegrator

__all__ = [
    'CirculationDetector',
    'ConceptApproach',
    'CirculationPattern',
    'InfrastructureManager',
    'UUIDSemanticManager',
    'DashboardGenerator',
    'TrackerIntegrator'
]
