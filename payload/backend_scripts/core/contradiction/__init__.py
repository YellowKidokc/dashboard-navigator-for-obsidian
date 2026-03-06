"""
Contradiction Detection System
================================
Universal coherence integrity layer for the Theophysics framework.

Three passes:
  Pass 1: Internal consistency (single document)
  Pass 2: Cross-reference consistency (pairwise documents)
  Pass 3: External consistency (vs. established knowledge)

All results → conflict_ledger table in PostgreSQL.

Author: David Lowe / Theophysics Project
"""

from .conflict_ledger import ConflictLedger, Conflict
from .claim_extractor import ClaimExtractor
from .detector import ContradictionDetector

__all__ = [
    'ConflictLedger',
    'Conflict', 
    'ClaimExtractor',
    'ContradictionDetector',
]
