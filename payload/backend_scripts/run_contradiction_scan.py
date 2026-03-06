#!/usr/bin/env python3
"""
Run the Contradiction Detector
===============================

Usage:
    # Full scan on axioms folder (with AI if available)
    python run_contradiction_scan.py

    # Scan specific folder
    python run_contradiction_scan.py --folder "O:\_Theophysics_v3\02_THEOPHYSICS"

    # Rules only (no AI)
    python run_contradiction_scan.py --no-ai

    # Pass 1 only (internal consistency)
    python run_contradiction_scan.py --pass 1

    # Pass 2 only (cross-reference)
    python run_contradiction_scan.py --pass 2

    # Pass 2 with specific strategy
    python run_contradiction_scan.py --pass 2 --strategy adjacent

    # Check DB connection and show conflict summary
    python run_contradiction_scan.py --status
"""

import sys
import argparse
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from core.contradiction import ContradictionDetector, ConflictLedger
from core.contradiction.detector import DetectorConfig


def main():
    parser = argparse.ArgumentParser(description="Theophysics Contradiction Detector")
    parser.add_argument('--folder', type=str, default=None,
                        help='Folder to scan (default: axioms folder)')
    parser.add_argument('--no-ai', action='store_true',
                        help='Run rule-based checks only, skip Ollama')
    parser.add_argument('--pass', type=int, dest='pass_num', default=0,
                        help='Run specific pass only (1, 2, or 0 for both)')
    parser.add_argument('--strategy', type=str, default='dependency',
                        choices=['dependency', 'adjacent', 'shared_tags', 'all_pairs'],
                        help='Pairing strategy for Pass 2')
    parser.add_argument('--status', action='store_true',
                        help='Show conflict ledger summary and exit')
    parser.add_argument('--model', type=str, default='llama3.2',
                        help='Ollama model to use')
    parser.add_argument('--max-files', type=int, default=500,
                        help='Maximum files to scan')
    
    args = parser.parse_args()
    
    # Status check
    if args.status:
        ledger = ConflictLedger()
        if not ledger.test_connection():
            print("❌ Cannot connect to PostgreSQL")
            sys.exit(1)
        
        print("✅ PostgreSQL connected")
        summary = ledger.get_conflict_summary()
        if summary:
            print(f"\n{'='*60}")
            print(f"CONFLICT LEDGER SUMMARY")
            print(f"{'='*60}")
            print(f"  Total conflicts:    {summary.get('total', 0)}")
            print(f"  Unresolved:         {summary.get('unresolved', 0)}")
            print(f"  Resolved:           {summary.get('resolved', 0)}")
            print(f"  Accepted tensions:  {summary.get('accepted', 0)}")
            print(f"  False positives:    {summary.get('false_positives', 0)}")
            print(f"")
            print(f"  Critical:           {summary.get('critical', 0)}")
            print(f"  Warnings:           {summary.get('warnings', 0)}")
            print(f"  Notes:              {summary.get('notes', 0)}")
            print(f"")
            print(f"  Pass 1 (internal):  {summary.get('pass_1', 0)}")
            print(f"  Pass 2 (cross-ref): {summary.get('pass_2', 0)}")
            print(f"  Pass 3 (external):  {summary.get('pass_3', 0)}")
            print(f"{'='*60}")
        else:
            print("  (No conflicts recorded yet)")
        
        # Show recent conflicts
        recent = ledger.get_conflicts(status='unresolved', limit=10)
        if recent:
            print(f"\nMOST RECENT UNRESOLVED ({len(recent)}):")
            for c in recent:
                sev = c.get('severity', '?')
                ctype = c.get('conflict_type', '?')
                src = Path(c.get('source_file', '')).name
                tgt = Path(c.get('target_file', '')).name if c.get('target_file') else src
                print(f"  [{sev.upper():8}] {ctype:25} {src} ↔ {tgt}")
                if c.get('reasoning'):
                    print(f"             {c['reasoning'][:80]}")
        
        sys.exit(0)
    
    # Build config
    config = DetectorConfig(
        use_ai=not args.no_ai,
        ollama_model=args.model,
        max_files_per_scan=args.max_files
    )
    
    folder = args.folder or config.axioms_folder
    
    if not Path(folder).exists():
        print(f"❌ Folder not found: {folder}")
        sys.exit(1)
    
    print(f"{'='*60}")
    print(f"THEOPHYSICS CONTRADICTION DETECTOR")
    print(f"{'='*60}")
    print(f"  Target:    {folder}")
    print(f"  AI Mode:   {'Ollama ({})'.format(args.model) if not args.no_ai else 'Rules Only'}")
    print(f"  Pass:      {'All' if args.pass_num == 0 else args.pass_num}")
    if args.pass_num in (0, 2):
        print(f"  Strategy:  {args.strategy}")
    print(f"{'='*60}\n")
    
    # Create detector
    detector = ContradictionDetector(config)
    
    # Run requested passes
    if args.pass_num == 0:
        results = detector.full_scan(folder, pair_strategy=args.strategy)
    elif args.pass_num == 1:
        conflicts = detector.pass_1_internal(folder)
        results = {'pass_1': conflicts}
    elif args.pass_num == 2:
        conflicts = detector.pass_2_crossref(folder, pair_strategy=args.strategy)
        results = {'pass_2': conflicts}
    else:
        print(f"Invalid pass number: {args.pass_num}")
        sys.exit(1)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    if 'pass_1' in results:
        print(f"  Pass 1 conflicts: {len(results['pass_1'])}")
    if 'pass_2' in results:
        print(f"  Pass 2 conflicts: {len(results['pass_2'])}")
    if 'summary' in results:
        s = results['summary']
        print(f"  Total in DB:      {s.get('total', 0)}")
        print(f"  Unresolved:       {s.get('unresolved', 0)}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
