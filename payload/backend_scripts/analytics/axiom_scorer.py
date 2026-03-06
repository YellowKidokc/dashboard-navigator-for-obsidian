#!/usr/bin/env python3
"""
Batch runner for coherence scorer on Theophysics axioms
"""

import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Import coherence scoring from same package
from .coherence_scorer import score_document as score_doc_basic

# Extended coherence terms for axiom-specific scoring
COHERENCE_TERMS_EXTENDED = {
    'order': 8, 'coherence': 10, 'unity': 8, 'harmony': 7, 'balance': 6,
    'structure': 7, 'pattern': 6, 'law': 8, 'principle': 7, 'truth': 9,
    'logos': 10, 'reason': 7, 'purpose': 8, 'meaning': 8, 'integration': 7,
    'grace': 9, 'redemption': 8, 'salvation': 8, 'restoration': 7,
    'consciousness': 9, 'awareness': 7, 'intention': 7, 'will': 7,
    'divine': 9, 'sacred': 7, 'holy': 7, 'blessed': 6,
}

ENTROPY_TERMS = {
    'chaos': -8, 'disorder': -7, 'confusion': -6, 'entropy': -5,
    'random': -5, 'arbitrary': -5, 'meaningless': -8, 'purposeless': -7,
    'incoherent': -8, 'inconsistent': -7, 'contradictory': -7,
}

def score_document(text: str) -> dict:
    """Score a document for coherence vs entropy."""
    words = text.lower().split()
    word_count = len(words)
    
    if word_count < 10:
        return {
            'word_count': word_count,
            'coherence_score': 0,
            'entropy_score': 0,
            'structural_score': 0,
            'raw_score': 0,
            'chi_score': 5.0,
            'status': 'TOO SHORT'
        }
    
    # Count coherence terms
    coherence_score = 0
    coherence_found = {}
    for term, weight in COHERENCE_TERMS_EXTENDED.items():
        count = text.lower().count(term.lower())
        if count > 0:
            coherence_score += count * weight
            coherence_found[term] = count
    
    # Count entropy terms
    entropy_score = 0
    entropy_found = {}
    for term, weight in ENTROPY_TERMS.items():
        count = text.lower().count(term.lower())
        if count > 0:
            entropy_score += count * weight
            entropy_found[term] = count
    
    # Structural analysis
    structural_score = 0
    if re.search(r'if.*then', text, re.IGNORECASE):
        structural_score += 5
    if re.search(r'therefore|thus|hence|consequently', text, re.IGNORECASE):
        structural_score += 5
    if re.search(r'because|since|given that', text, re.IGNORECASE):
        structural_score += 3
    if re.search(r'∀|∃|→|↔|∧|∨|¬|⊃|≡', text):
        structural_score += 10
    if re.search(r'\b[A-Z]\s*[=:→]\s*', text):
        structural_score += 3
    
    # Normalize per 1000 words
    norm_factor = 1000 / word_count if word_count > 0 else 0
    coherence_norm = coherence_score * norm_factor
    entropy_norm = entropy_score * norm_factor
    structural_norm = structural_score * norm_factor
    
    raw_score = coherence_norm + entropy_norm + structural_norm
    
    # Map to 0-10 scale
    if raw_score >= 200:
        chi = 10.0
    elif raw_score <= -100:
        chi = 0.0
    else:
        chi = round(((raw_score + 100) / 300) * 10, 1)
        chi = max(0, min(10, chi))
    
    if chi >= 7:
        status = 'HIGH COHERENCE'
    elif chi >= 4:
        status = 'MODERATE'
    else:
        status = 'HIGH ENTROPY / INCOHERENT'
    
    return {
        'word_count': word_count,
        'coherence_score': round(coherence_norm, 2),
        'entropy_score': round(entropy_norm, 2),
        'structural_score': round(structural_norm, 2),
        'raw_score': round(raw_score, 2),
        'chi_score': chi,
        'status': status,
        'coherence_terms': dict(sorted(coherence_found.items(), key=lambda x: -x[1])[:10]),
        'entropy_terms': entropy_found
    }


def scan_axioms(base_path: str) -> list:
    """Scan all axiom files and score them."""
    results = []
    base = Path(base_path)
    
    # Find all .md files
    for md_file in sorted(base.rglob('*.md')):
        if md_file.name == '00_INDEX.md':
            continue
            
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            score = score_document(content)
            score['file'] = str(md_file.relative_to(base))
            score['name'] = md_file.stem
            results.append(score)
            
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    return results


def main():
    import os
    import sys
    
    base_path = os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3')
    output_path = Path(__file__).parent / "axiom_coherence_results.json"
    
    print("=" * 70)
    print("THEOPHYSICS AXIOM COHERENCE ANALYSIS")
    print("=" * 70)
    print(f"\nScanning: {base_path}")
    
    results = scan_axioms(base_path)
    
    # Sort by CHI score
    results_sorted = sorted(results, key=lambda x: -x['chi_score'])
    
    # Calculate statistics
    chi_scores = [r['chi_score'] for r in results]
    avg_chi = sum(chi_scores) / len(chi_scores) if chi_scores else 0
    
    high_coherence = len([r for r in results if r['chi_score'] >= 7])
    moderate = len([r for r in results if 4 <= r['chi_score'] < 7])
    low_coherence = len([r for r in results if r['chi_score'] < 4])
    
    print(f"\nTotal Axioms Scored: {len(results)}")
    print(f"Average CHI Score: {avg_chi:.2f} / 10")
    print(f"\nDistribution:")
    print(f"  HIGH COHERENCE (>=7): {high_coherence} ({100*high_coherence/len(results):.1f}%)")
    print(f"  MODERATE (4-7):      {moderate} ({100*moderate/len(results):.1f}%)")
    print(f"  LOW (<4):            {low_coherence} ({100*low_coherence/len(results):.1f}%)")
    
    print("\n" + "=" * 70)
    print("TOP 20 HIGHEST COHERENCE AXIOMS")
    print("=" * 70)
    for r in results_sorted[:20]:
        print(f"  CHI {r['chi_score']:4.1f} | {r['name'][:50]}")
    
    print("\n" + "=" * 70)
    print("BOTTOM 10 (NEEDS ATTENTION)")
    print("=" * 70)
    for r in results_sorted[-10:]:
        print(f"  CHI {r['chi_score']:4.1f} | {r['name'][:50]}")
    
    # Group by folder
    folder_scores = defaultdict(list)
    for r in results:
        folder = r['file'].split('\\')[0] if '\\' in r['file'] else 'ROOT'
        folder_scores[folder].append(r['chi_score'])
    
    print("\n" + "=" * 70)
    print("SCORES BY CATEGORY")
    print("=" * 70)
    for folder, scores in sorted(folder_scores.items()):
        avg = sum(scores) / len(scores)
        print(f"  {folder:20} | Avg CHI: {avg:.2f} | Count: {len(scores)}")
    
    # Save full results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_axioms': len(results),
                'avg_chi': round(avg_chi, 2),
                'high_coherence_count': high_coherence,
                'moderate_count': moderate,
                'low_count': low_coherence
            },
            'by_category': {
                folder: {
                    'avg_chi': round(sum(scores)/len(scores), 2),
                    'count': len(scores)
                }
                for folder, scores in folder_scores.items()
            },
            'axioms': results_sorted
        }, f, indent=2)
    
    print(f"\nFull results saved to: {output_path}")


if __name__ == '__main__':
    main()
