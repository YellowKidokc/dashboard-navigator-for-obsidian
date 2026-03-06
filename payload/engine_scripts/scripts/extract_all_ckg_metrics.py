#!/usr/bin/env python3
"""
Extract ALL CKG Metrics to Excel-Ready CSV
Extracts 20+ detailed metrics per paper, not just final scores
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

def extract_all_metrics(json_file):
    """Extract all metrics from a CKG JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metrics = {}
    
    # Basic info
    metrics['document_title'] = data.get('document_title', '')
    metrics['file_path'] = str(json_file.parent.parent.parent)
    
    # Get aggregate/document_aggregate
    agg = data.get('aggregate_summary', data.get('document_aggregate', {}))
    
    # Tier 1: Foundations (4 metrics)
    if isinstance(agg.get('tier1_foundations'), dict):
        t1 = agg['tier1_foundations']
        metrics['t1_axioms_stated'] = t1.get('axioms_stated', 0)
        metrics['t1_definitions_unambiguous'] = t1.get('definitions_unambiguous', 0)
        metrics['t1_internal_consistency'] = t1.get('internal_consistency', 0)
        metrics['t1_ontological_clarity'] = t1.get('ontological_clarity', 0)
        metrics['t1_total'] = t1.get('total', 0)
    else:
        metrics['t1_total'] = agg.get('tier1_foundations', 0)
    
    # Tier 2: Propositions (4 metrics)
    if isinstance(agg.get('tier2_propositions'), dict):
        t2 = agg['tier2_propositions']
        metrics['t2_claims_derived'] = t2.get('claims_derived', 0)
        metrics['t2_hypotheses_distinguished'] = t2.get('hypotheses_distinguished', 0)
        metrics['t2_theorems_supported'] = t2.get('theorems_supported', 0)
        metrics['t2_scope_declared'] = t2.get('scope_declared', 0)
        metrics['t2_total'] = t2.get('total', 0)
    else:
        metrics['t2_total'] = agg.get('tier2_propositions', 0)
    
    # Tier 3: Constraints (4 metrics)
    if isinstance(agg.get('tier3_constraints'), dict):
        t3 = agg['tier3_constraints']
        metrics['t3_constraints_declared'] = t3.get('constraints_declared', 0)
        metrics['t3_constraint_survival'] = t3.get('constraint_survival', 0)
        metrics['t3_cross_domain_tension'] = t3.get('cross_domain_tension', 0)
        metrics['t3_limiting_cases'] = t3.get('limiting_cases', 0)
        metrics['t3_total'] = t3.get('total', 0)
    else:
        metrics['t3_total'] = agg.get('tier3_constraints', 0)
    
    # Tier 4: Evidence (4 metrics)
    if isinstance(agg.get('tier4_evidence'), dict):
        t4 = agg['tier4_evidence']
        metrics['t4_testable_predictions'] = t4.get('testable_predictions', 0)
        metrics['t4_falsification_criteria'] = t4.get('falsification_criteria', 0)
        metrics['t4_empirical_support'] = t4.get('empirical_support', 0)
        metrics['t4_data_traceability'] = t4.get('data_traceability', 0)
        metrics['t4_total'] = t4.get('total', 0)
    else:
        metrics['t4_total'] = agg.get('tier4_evidence', 0)
    
    # Tier 5: Integration (4 metrics)
    if isinstance(agg.get('tier5_integration'), dict):
        t5 = agg['tier5_integration']
        metrics['t5_framework_bridges'] = t5.get('framework_bridges', 0)
        metrics['t5_master_equation_map'] = t5.get('master_equation_map', 0)
        metrics['t5_system_coherence'] = t5.get('system_coherence', 0)
        metrics['t5_downstream_implications'] = t5.get('downstream_implications', 0)
        metrics['t5_total'] = t5.get('total', 0)
    else:
        metrics['t5_total'] = agg.get('tier5_integration', 0)
    
    # Scores
    metrics['raw_score'] = agg.get('raw_score', 0)
    metrics['final_score'] = agg.get('final_score', 0)
    
    # Caps and flags
    caps = agg.get('applied_caps', [])
    metrics['applied_caps'] = '; '.join(caps) if caps else ''
    
    flags = agg.get('diagnostic_flags', [])
    metrics['diagnostic_flags'] = '; '.join(flags) if flags else ''
    
    missing = agg.get('missing_components', [])
    metrics['missing_components'] = '; '.join(missing) if missing else ''
    
    metrics['confidence'] = agg.get('confidence_of_evaluation', 0)
    
    return metrics

def main():
    vault_root = Path("O:/_Theophysics_v3")
    output_file = Path("C:/Users/lowes/Desktop/CKG_DETAILED_METRICS.csv")
    
    print("="*60)
    print("EXTRACT ALL CKG METRICS TO CSV")
    print("="*60)
    print()
    
    # Find all CKG JSON files
    print("[*] Scanning for CKG JSON files...")
    json_files = list(vault_root.glob("**/*_CKG_*.json"))
    print(f"[+] Found {len(json_files)} CKG result files\n")
    
    # Extract metrics from each file
    all_metrics = []
    for json_file in json_files:
        try:
            metrics = extract_all_metrics(json_file)
            all_metrics.append(metrics)
            print(f"[+] {metrics['document_title'][:50]}")
        except Exception as e:
            print(f"[-] Error processing {json_file.name}: {e}")
    
    # Write to CSV
    if all_metrics:
        # Get all unique field names
        fieldnames = set()
        for m in all_metrics:
            fieldnames.update(m.keys())
        fieldnames = sorted(fieldnames)
        
        # Move key fields to front
        priority = ['document_title', 'file_path', 'final_score', 'raw_score',
                   't1_total', 't2_total', 't3_total', 't4_total', 't5_total']
        fieldnames = [f for f in priority if f in fieldnames] + \
                    [f for f in fieldnames if f not in priority]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_metrics)
        
        print(f"\n[+] Created: {output_file}")
        print(f"[+] Papers: {len(all_metrics)}")
        print(f"[+] Metrics per paper: {len(fieldnames)}")
        print(f"\n[*] Open in Excel to analyze all detailed metrics!")
    else:
        print("[-] No metrics extracted")

if __name__ == '__main__':
    main()
