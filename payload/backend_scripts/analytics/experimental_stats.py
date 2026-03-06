import os
import re
from pathlib import Path
from collections import defaultdict
import json

BASE = os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3')

# Search patterns for experimental/statistical content
STAT_PATTERNS = {
    'sigma': r'(\d+\.?\d*)\s*[σ]|(\d+\.?\d*)\s*sigma',
    'p_value': r'[Pp]\s*[<>=]\s*[\d\.e\-]+|p-value|P\s*=\s*[\d\.e\-]+',
    'correlation': r'[Rr]\s*=\s*[\d\.]+|correlation|r²\s*=',
    'trials': r'(\d[\d,]*)\s*trials?|N\s*=\s*(\d[\d,]*)',
    'confidence': r'\d+%\s*confidence|CI\s*[\[\(]',
    'effect_size': r"Cohen'?s?\s*d|effect\s*size|η²",
    'regression': r'regression|β\s*=|slope\s*=',
    'chi_square': r'χ²|chi-?square',
    'anova': r'ANOVA|F\s*\(\d+',
    'bayes': r'Bayes|posterior|prior|BF\s*=',
}

# Specific experimental references
EXP_PATTERNS = {
    'PEAR': r'PEAR|Princeton Engineering|Jahn|Dunne',
    'GCP': r'GCP|Global Consciousness|Roger Nelson',
    'REG': r'REG|random event generator|random number generator',
    'double_slit': r'double.?slit|which.?path|quantum eraser',
    'delayed_choice': r'delayed.?choice|Wheeler',
    'CERN': r'CERN|LHC|particle collider',
    'LIGO': r'LIGO|gravitational wave',
    'Planck': r'Planck satellite|CMB|cosmic microwave',
    'JWST': r'JWST|James Webb|Hubble tension',
}

def search_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        results = {
            'path': str(filepath),
            'name': filepath.name,
            'folder': filepath.parent.name,
            'words': len(text.split()),
            'stats': {},
            'experiments': {},
            'numbers': []
        }
        
        # Find statistical patterns
        for name, pattern in STAT_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results['stats'][name] = len(matches)
        
        # Find experimental references
        for name, pattern in EXP_PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                results['experiments'][name] = len(matches)
        
        # Extract specific sigma values
        sigma_matches = re.findall(r'(\d+\.?\d*)\s*[σ]', text)
        if sigma_matches:
            results['sigma_values'] = [float(s) for s in sigma_matches if float(s) < 100]
        
        # Extract p-values
        p_matches = re.findall(r'[Pp]\s*[<>=]\s*([\d\.e\-]+)', text)
        if p_matches:
            results['p_values'] = p_matches[:10]  # Limit
        
        # Extract trial counts
        trial_matches = re.findall(r'(\d[\d,]*)\s*trials?', text, re.IGNORECASE)
        if trial_matches:
            results['trial_counts'] = [int(t.replace(',', '')) for t in trial_matches if t.replace(',', '').isdigit()]
        
        return results if (results['stats'] or results['experiments']) else None
    except:
        return None

# Scan entire Theophysics_Master
results = []
base = Path(BASE)

print("Scanning for statistical and experimental content...")
for md in base.rglob('*.md'):
    r = search_file(md)
    if r:
        results.append(r)

print(f"\nFound {len(results)} files with statistical/experimental content")

# Aggregate statistics
all_stats = defaultdict(int)
all_experiments = defaultdict(int)
all_sigmas = []
all_trials = []

for r in results:
    for stat, count in r['stats'].items():
        all_stats[stat] += count
    for exp, count in r['experiments'].items():
        all_experiments[exp] += count
    if 'sigma_values' in r:
        all_sigmas.extend(r['sigma_values'])
    if 'trial_counts' in r:
        all_trials.extend(r['trial_counts'])

print()
print('=' * 80)
print('STATISTICAL METHODS REFERENCED')
print('=' * 80)
for stat, count in sorted(all_stats.items(), key=lambda x: x[1], reverse=True):
    print(f"{count:>6} references | {stat}")

print()
print('=' * 80)
print('EXPERIMENTAL STUDIES REFERENCED')
print('=' * 80)
for exp, count in sorted(all_experiments.items(), key=lambda x: x[1], reverse=True):
    print(f"{count:>6} references | {exp}")

print()
print('=' * 80)
print('SIGMA VALUES FOUND')
print('=' * 80)
if all_sigmas:
    print(f"Total sigma claims: {len(all_sigmas)}")
    print(f"Unique values: {sorted(set(all_sigmas), reverse=True)[:20]}")
    print(f"Max sigma: {max(all_sigmas)}")
    print(f"Claims >= 5σ: {len([s for s in all_sigmas if s >= 5])}")
    print(f"Claims >= 6σ: {len([s for s in all_sigmas if s >= 6])}")

print()
print('=' * 80)
print('TRIAL COUNTS FOUND')
print('=' * 80)
if all_trials:
    print(f"Total trial references: {len(all_trials)}")
    large_trials = [t for t in all_trials if t >= 10000]
    print(f"Large-scale trials (>10K): {len(large_trials)}")
    if large_trials:
        print(f"Largest: {max(large_trials):,}")
        print(f"Top 10: {sorted(large_trials, reverse=True)[:10]}")

print()
print('=' * 80)
print('FILES WITH HIGHEST STATISTICAL DENSITY')
print('=' * 80)

# Score files by statistical content
for r in results:
    r['stat_score'] = sum(r['stats'].values()) + sum(r['experiments'].values()) * 2
    if 'sigma_values' in r:
        r['stat_score'] += len([s for s in r['sigma_values'] if s >= 5]) * 10

results.sort(key=lambda x: x['stat_score'], reverse=True)

for r in results[:25]:
    stats_str = ', '.join([f"{k}:{v}" for k, v in r['stats'].items()][:3])
    exps_str = ', '.join([f"{k}:{v}" for k, v in r['experiments'].items()][:3])
    print(f"{r['stat_score']:>6} score | {r['folder'][:15]:<15} | {r['name'][:40]}")
    if stats_str:
        print(f"         Stats: {stats_str}")
    if exps_str:
        print(f"         Exps: {exps_str}")
