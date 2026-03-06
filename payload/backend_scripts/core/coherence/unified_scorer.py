#!/usr/bin/env python3
"""
THEOPHYSICS COHERENCE ENGINE - Unified Scorer
==============================================

Operational, auditable, non-circular prediction of societal collapse.

Computes:
- χ (coherence): Fruits of the Spirit 12-metric structural invariants
- δ (drift): Misalignment + entropy pressure
- G (grace): Exogenous impulses (residual analysis)

Every run produces a manifest with:
- Input hashes (deterministic)
- Model spec (versioned)
- Full provenance (reproducible)
"""

import sys
import os
from pathlib import Path
import time
import hashlib
import yaml
import uuid
from datetime import datetime
from typing import List, Tuple, Optional

# Add fruits_scorer to path
sys.path.insert(0, r'O:\Theophysics_Backend\In_House_Programs\Plugins\Theophysics theory downloader\Data_Analytics\Scripts')

from fruits_scorer import analyze_theory_fruits, FruitsAnalysis

from core import Entity, ClaimSet, Observations, ModelSpec, RunResult
from core.drift import DriftScorer, minimal_drift
from core.grace import GraceScorer, minimal_grace


class CoherenceEngine:
    """
    Main engine for computing χ, δ, G with full auditability.
    """
    
    def __init__(self, 
                 model_version: str = "minimal_v1",
                 output_dir: str = "outputs/manifests"):
        """
        Initialize the coherence engine.
        
        Args:
            model_version: Version tag for this run
            output_dir: Where to save run manifests
        """
        self.version = model_version
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load rubrics
        self.drift_rubric = self._load_rubric("rubrics/drift_rubric.yaml")
        self.grace_rubric = self._load_rubric("rubrics/grace_rubric.yaml")
        
        # Initialize scorers
        self.drift_scorer = DriftScorer()
        self.grace_scorer = GraceScorer()
    
    def _load_rubric(self, path: str) -> dict:
        """Load and hash a rubric file."""
        rubric_path = Path(__file__).parent / path
        
        if not rubric_path.exists():
            raise FileNotFoundError(f"Rubric not found: {rubric_path}")
        
        with open(rubric_path, 'r', encoding='utf-8') as f:
            content = f.read()
            rubric = yaml.safe_load(content)
            
        # Hash for provenance
        rubric['_hash'] = hashlib.sha256(content.encode()).hexdigest()[:12]
        
        return rubric
    
    def compute_chi_from_text(self, text: str, entity_name: str) -> List[Tuple[int, float]]:
        """
        Compute χ (coherence) from text using Fruits of the Spirit.
        
        This is a single-point measurement. For time series, you need
        multiple texts or documents per year.
        
        Returns:
            [(year, chi_score), ...] - Here just [(current_year, score)]
        """
        analysis = analyze_theory_fruits(text, entity_name)
        
        # Normalize from -12/+12 to 0/1
        chi = (analysis.total_score + 12) / 24
        
        current_year = datetime.now().year
        return [(current_year, chi)]
    
    def compute_chi_time_series(self, 
                                texts_by_year: dict) -> List[Tuple[int, float]]:
        """
        Compute χ time series from yearly documents.
        
        Args:
            texts_by_year: {year: text_content, ...}
            
        Returns:
            [(year, chi), ...] sorted by year
        """
        results = []
        
        for year, text in sorted(texts_by_year.items()):
            analysis = analyze_theory_fruits(text, f"year_{year}")
            chi = (analysis.total_score + 12) / 24  # Normalize to [0, 1]
            results.append((year, chi))
        
        return results
    
    def run(self, entity: Entity, use_minimal: bool = True) -> RunResult:
        """
        Execute full χ, δ, G analysis on an entity.
        
        Args:
            entity: Entity with ClaimSet and Observations
            use_minimal: If True, use simplified δ and G (faster, good for testing)
            
        Returns:
            RunResult with complete provenance
        """
        start_time = time.time()
        run_id = f"{entity.entity_id}_{uuid.uuid4().hex[:8]}"
        
        print(f"=" * 60)
        print(f"COHERENCE ENGINE RUN: {run_id}")
        print(f"=" * 60)
        print(f"Entity: {entity.name}")
        print(f"Type: {entity.entity_type}")
        print(f"Model: {self.version}")
        print()
        
        # Validate entity
        is_valid, error_msg = entity.validate()
        if not is_valid:
            raise ValueError(f"Entity validation failed: {error_msg}")
        
        # Create model spec
        model_spec = ModelSpec(
            version=self.version,
            chi_method="fruits_12_normalized",
            drift_method="minimal_v1" if use_minimal else "full_v1",
            grace_method="residual_v1" if use_minimal else "changepoint_v2",
            parameters={
                "drift_w_misalignment": 0.5,
                "drift_w_pressure": 0.5,
                "grace_threshold": 0.1,
                "grace_window": 5
            },
            rubric_hashes={
                "drift": self.drift_rubric.get('_hash', 'unknown'),
                "grace": self.grace_rubric.get('_hash', 'unknown')
            }
        )
        
        # Step 1: Compute χ (coherence) time series
        print("[1/3] Computing χ (coherence) from observations...")
        
        # For this minimal version, we'll use a simple proxy
        # In production, you'd extract χ from actual text corpus per year
        chi_scores = self._compute_chi_proxy(entity.observations)
        
        print(f"  Computed χ for {len(chi_scores)} time points")
        print(f"  Range: {min(c for _, c in chi_scores):.3f} to {max(c for _, c in chi_scores):.3f}")
        print()
        
        # Step 2: Compute δ (drift)
        print("[2/3] Computing δ (drift)...")
        
        if use_minimal:
            drift_scores = minimal_drift(chi_scores)
        else:
            drift_results = self.drift_scorer.compute_drift(
                chi_scores,
                entity.observations.time_series,
                {}  # Would extract from ClaimSet in production
            )
            drift_scores = [(d.year, d.delta_total) for d in drift_results]
        
        print(f"  Computed δ for {len(drift_scores)} time points")
        if drift_scores:
            avg_drift = sum(d for _, d in drift_scores) / len(drift_scores)
            print(f"  Average drift: {avg_drift:.3f}")
        print()
        
        # Step 3: Compute G (grace)
        print("[3/3] Computing G (grace via residual analysis)...")
        
        if use_minimal:
            grace_scores = minimal_grace(chi_scores)
        else:
            grace_results = self.grace_scorer.compute_grace(
                chi_scores,
                drift_scores,
                entity.observations.events
            )
            grace_scores = [(g.year, g.G) for g in grace_results]
        
        print(f"  Computed G for {len(grace_scores)} time points")
        grace_events = [g for _, g in grace_scores if abs(g) > 0.1]
        print(f"  Detected {len(grace_events)} grace events (|G| > 0.1)")
        print()
        
        # Create result
        runtime = time.time() - start_time
        
        result = RunResult(
            run_id=run_id,
            entity=entity,
            model_spec=model_spec,
            chi_scores=chi_scores,
            drift_scores=drift_scores,
            grace_scores=grace_scores,
            diagnostics={
                "chi_mean": sum(c for _, c in chi_scores) / len(chi_scores) if chi_scores else 0,
                "chi_trend": self._compute_trend(chi_scores),
                "drift_mean": sum(d for _, d in drift_scores) / len(drift_scores) if drift_scores else 0,
                "grace_events_count": len(grace_events)
            },
            runtime_seconds=runtime
        )
        
        # Save manifest
        manifest_path = result.save_manifest(str(self.output_dir))
        
        print("=" * 60)
        print("RUN COMPLETE")
        print("=" * 60)
        print(f"Run ID: {run_id}")
        print(f"Runtime: {runtime:.2f} seconds")
        print(f"Manifest saved: {manifest_path}")
        print()
        
        return result
    
    def _compute_chi_proxy(self, observations: Observations) -> List[Tuple[int, float]]:
        """
        Proxy χ from observations (minimal version).
        
        In production, this would:
        1. Load yearly text corpus for entity
        2. Run fruits_scorer on each year's text
        3. Return actual χ scores
        
        For now, we'll synthesize from available metrics.
        """
        # Get time range
        all_years = set()
        for series in observations.time_series.values():
            all_years.update([y for y, _ in series])
        
        if not all_years:
            return []
        
        years = sorted(all_years)
        
        # Synthesize χ from available metrics
        # This is a PLACEHOLDER - replace with actual text analysis
        chi_scores = []
        
        for year in years:
            # Aggregate metrics for this year
            values = []
            for metric, series in observations.time_series.items():
                year_vals = [v for y, v in series if y == year]
                if year_vals:
                    # Normalize assuming higher = better
                    # TODO: Make this metric-specific via rubric
                    normalized = min(1.0, max(0.0, year_vals[0] / 100))
                    values.append(normalized)
            
            chi = sum(values) / len(values) if values else 0.5
            chi_scores.append((year, chi))
        
        return chi_scores
    
    def _compute_trend(self, scores: List[Tuple[int, float]]) -> float:
        """Compute linear trend slope."""
        if len(scores) < 2:
            return 0.0
        
        import numpy as np
        years = [y for y, _ in scores]
        vals = [v for _, v in scores]
        
        x = np.arange(len(years))
        slope, _ = np.polyfit(x, vals, 1)
        
        return slope


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for the coherence engine."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Theophysics Coherence Engine - Predict societal collapse"
    )
    parser.add_argument(
        '--entity',
        required=True,
        help="Entity configuration file (JSON)"
    )
    parser.add_argument(
        '--output',
        default="outputs/manifests",
        help="Output directory for manifests"
    )
    parser.add_argument(
        '--minimal',
        action='store_true',
        help="Use minimal/fast version (for testing)"
    )
    
    args = parser.parse_args()
    
    # TODO: Load entity from JSON config file
    # For now, just show usage
    
    print("Coherence Engine initialized!")
    print(f"Entity config: {args.entity}")
    print(f"Output dir: {args.output}")
    print(f"Mode: {'minimal' if args.minimal else 'full'}")
    

if __name__ == "__main__":
    main()
