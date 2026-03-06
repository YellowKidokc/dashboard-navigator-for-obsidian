#!/usr/bin/env python3
"""
Extract COMPREHENSIVE CKG Metrics - Document + Section Level
Every metric from every section of every paper
"""

import json
import csv
from pathlib import Path

def extract_section_metrics(section):
    """Extract all metrics from a section"""
    metrics = {'section_title': section.get('section_title', '')}
    
    # Tier 1
    if isinstance(section.get('tier1_foundations'), dict):
        t1 = section['tier1_foundations']
        metrics.update({
            't1_axioms': t1.get('axioms_stated', 0),
            't1_definitions': t1.get('definitions_unambiguous', 0),
            't1_consistency': t1.get('internal_consistency', 0),
            't1_clarity': t1.get('ontological_clarity', 0),
            't1_total': t1.get('total', 0)
        })
    
    # Tier 2
    if isinstance(section.get('tier2_propositions'), dict):
        t2 = section['tier2_propositions']
        metrics.update({
            't2_claims': t2.get('claims_derived', 0),
            't2_hypotheses': t2.get('hypotheses_distinguished', 0),
            't2_theorems': t2.get('theorems_supported', 0),
            't2_scope': t2.get('scope_declared', 0),
            't2_total': t2.get('total', 0)
        })
    
    # Tier 3
    if isinstance(section.get('tier3_constraints'), dict):
        t3 = section['tier3_constraints']
        metrics.update({
            't3_declared': t3.get('constraints_declared', 0),
            't3_survival': t3.get('constraint_survival', 0),
            't3_tension': t3.get('cross_domain_tension', 0),
            't3_limiting': t3.get('limiting_cases', 0),
            't3_total': t3.get('total', 0)
        })
    
    # Tier 4
    if isinstance(section.get('tier4_evidence'), dict):
        t4 = section['tier4_evidence']
        metrics.update({
            't4_predictions': t4.get('testable_predictions', 0),
            't4_falsification': t4.get('falsification_criteria', 0),
            't4_empirical': t4.get('empirical_support', 0),
            't4_traceability': t4.get('data_traceability', 0),
            't4_total': t4.get('total', 0)
        })
    
    # Tier 5
    if isinstance(section.get('tier5_integration'), dict):
        t5 = section['tier5_integration']
        metrics.update({
            't5_bridges': t5.get('framework_bridges', 0),
            't5_equation': t5.get('master_equation_map', 0),
            't5_coherence': t5.get('system_coherence', 0),
            't5_implications': t5.get('downstream_implications', 0),
            't5_total': t5.get('total', 0)
        })
    
    metrics['section_raw_score'] = section.get('section_raw_score', 0)
    
    return metrics

def main():
    vault_root = Path("O:/_Theophysics_v3")
    output_file = Path("C:/Users/lowes/Desktop/CKG_COMPREHENSIVE_ALL_SECTIONS.csv")
    
    print("="*70)
    print("EXTRACT COMPREHENSIVE CKG METRICS - ALL SECTIONS")
    print("="*70)
    print()
    
    json_files = list(vault_root.glob("**/*_CKG_*.json"))
    print(f"[+] Found {len(json_files)} CKG files\n")
    
    all_rows = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            doc_title = data.get('document_title', '')
            folder = str(json_file.parent.parent.parent)
            
            # Get document aggregate
            agg = data.get('aggregate_summary', data.get('document_aggregate', {}))
            doc_final_score = agg.get('final_score', 0)
            doc_raw_score = agg.get('raw_score', 0)
            
            # Extract each section
            sections = data.get('section_scores', [])
            for idx, section in enumerate(sections, 1):
                row = {
                    'document': doc_title,
                    'folder': folder,
                    'doc_final_score': doc_final_score,
                    'doc_raw_score': doc_raw_score,
                    'section_num': idx
                }
                row.update(extract_section_metrics(section))
                all_rows.append(row)
            
            print(f"[+] {doc_title[:60]} ({len(sections)} sections)")
            
        except Exception as e:
            continue
    
    # Write CSV
    if all_rows:
        fieldnames = list(all_rows[0].keys())
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"\n{'='*70}")
        print(f"[+] Created: {output_file}")
        print(f"[+] Total rows: {len(all_rows)} (sections from all papers)")
        print(f"[+] Metrics per section: {len(fieldnames)}")
        print(f"\n[*] Open in Excel - each row is one section with full metrics!")
        print(f"{'='*70}")

if __name__ == '__main__':
    main()
