import os
import re
from pathlib import Path
from collections import defaultdict

BASE = os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3')

# Correct folder names based on actual structure (02_THEOPHYSICS, JS-SERIES, etc.)
paper_folders = [
    'V3_P00-Introduction', 'V3_P00-The-Missing-Step', 'V3_P00_2+2=5',
    'V3_P01-Logos-Principle', 'V3_P02-Quantum-Bridge', 'V3_P03-Algorithm-Reality',
    'V3_P04-Hard-Problem', 'V3_P05-Soul-Observer', 'V3_P06-Physics-Principalities',
    'V3_P07-Grace-Function', 'V3_P08-Stretched-Heavens', 'V3_P09-Moral-Universe',
    'V3_P10-Creatio-Silico', 'V3_P11-Protocols-Validation', 'V3_P12-Decalogue-Cosmos',
    'V3_P13_Test_Predictions', 'V3_P14_Aggregated_Data',
    'V1_Logo_Full', 'V2_Logos_Axioms', 'Logos Story', 'Trinity', 'TOE',
    'THE COHERENCE COLLAPSE', 'The_One', '01_Master_Drafts'
]

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        return {
            'name': filepath.name,
            'parent': filepath.parent.name,
            'words': len(text.split()),
            'lines': len(text.splitlines()),
            'axioms': len(re.findall(r'Axiom|%%tag::Axiom::', text, re.IGNORECASE)),
            'equations': len(re.findall(r'[χΨΦΛΩ∫∑∏∂∇=]', text)),
            'citations': len(re.findall(r'\([A-Z][a-z]+.*?\d{4}\)', text)),
            'semantic_tags': len(re.findall(r'%%tag::', text)),
            'kb': filepath.stat().st_size / 1024
        }
    except:
        return None

results = []
base = Path(BASE)

for folder_name in paper_folders:
    folder_path = base / folder_name
    if folder_path.exists():
        for md in folder_path.rglob('*.md'):
            r = analyze_file(md)
            if r and r['words'] > 50:
                r['paper_folder'] = folder_name
                results.append(r)

# Group by paper folder
paper_stats = defaultdict(lambda: {
    'total_words': 0, 'files': 0, 'axioms': 0, 'citations': 0, 
    'equations': 0, 'semantic_tags': 0, 'versions': set()
})

for r in results:
    p = r['paper_folder']
    paper_stats[p]['total_words'] += r['words']
    paper_stats[p]['files'] += 1
    paper_stats[p]['axioms'] += r['axioms']
    paper_stats[p]['citations'] += r['citations']
    paper_stats[p]['equations'] += r['equations']
    paper_stats[p]['semantic_tags'] += r['semantic_tags']
    
    name = r['name'].lower()
    if 'academic' in name or '-a-' in name:
        paper_stats[p]['versions'].add('Academic')
    if 'beginner' in name or '-b-' in name:
        paper_stats[p]['versions'].add('Beginner')
    if 'middle' in name or '-m-' in name:
        paper_stats[p]['versions'].add('Middle')
    if 'canonical' in name:
        paper_stats[p]['versions'].add('Canonical')
    if 'theology' in name or 't-p' in name:
        paper_stats[p]['versions'].add('Theology')
    if 'full' in name:
        paper_stats[p]['versions'].add('Full')

print('=' * 90)
print('LOGOS PAPERS V3 - PUBLICATION READINESS ANALYSIS')
print('=' * 90)
print()
print(f"{'Paper':<30} {'Words':>10} {'Files':>6} {'Ax':>5} {'Cit':>5} {'Eq':>6} {'Tags':>6} Versions")
print('-' * 90)

sorted_papers = sorted(paper_stats.items(), key=lambda x: x[1]['total_words'], reverse=True)
for paper, stats in sorted_papers:
    versions = ','.join(sorted(stats['versions']))[:20] if stats['versions'] else '-'
    print(f"{paper:<30} {stats['total_words']:>10,} {stats['files']:>6} {stats['axioms']:>5} {stats['citations']:>5} {stats['equations']:>6} {stats['semantic_tags']:>6} {versions}")

# Find canonical/full versions
print()
print('=' * 90)
print('CANONICAL/FULL VERSIONS (Publication-Ready Files)')
print('=' * 90)

canonical = [r for r in results if 'canonical' in r['name'].lower() or 'full' in r['name'].lower() or 'final all' in r['name'].lower()]
canonical.sort(key=lambda x: x['words'], reverse=True)

for r in canonical[:25]:
    print(f"{r['words']:>8,} w | {r['citations']:>3} cit | {r['axioms']:>3} ax | {r['paper_folder'][:20]:<20} | {r['name'][:40]}")

# Calculate publication readiness score
print()
print('=' * 90)
print('PUBLICATION ORDER BY COMPLETENESS SCORE')
print('=' * 90)

paper_scores = []
for paper, stats in paper_stats.items():
    # Skip meta folders
    if paper in ['01_Master_Drafts', 'THE COHERENCE COLLAPSE', 'The_One']:
        continue
    
    score = stats['total_words'] + (stats['citations'] * 200) + (stats['axioms'] * 50) + (stats['semantic_tags'] * 10)
    completeness = len(stats['versions']) / 6 * 100
    
    if stats['words'] > 0 if 'words' in stats else stats['total_words'] > 0:
        citation_density = stats['citations'] / (stats['total_words'] / 1000) if stats['total_words'] > 0 else 0
    else:
        citation_density = 0
    
    paper_scores.append({
        'paper': paper,
        'score': score,
        'completeness': completeness,
        'words': stats['total_words'],
        'citations': stats['citations'],
        'axioms': stats['axioms'],
        'versions': len(stats['versions']),
        'citation_density': citation_density
    })

paper_scores.sort(key=lambda x: x['score'], reverse=True)

print(f"{'Rank':<4} {'Paper':<30} {'Score':>12} {'Complete':>8} {'Words':>10} {'Cit':>5} {'Ax':>5}")
print('-' * 90)
for i, ps in enumerate(paper_scores, 1):
    print(f"{i:<4} {ps['paper']:<30} {ps['score']:>12,} {ps['completeness']:>7.0f}% {ps['words']:>10,} {ps['citations']:>5} {ps['axioms']:>5}")

# Best for first publication
print()
print('=' * 90)
print('RECOMMENDED FIRST PUBLICATION (Highest citation density + completeness)')
print('=' * 90)

# Filter to only V3 papers
v3_papers = [p for p in paper_scores if p['paper'].startswith('V3_')]
v3_papers.sort(key=lambda x: (x['versions'], x['citation_density']), reverse=True)

for i, ps in enumerate(v3_papers, 1):
    print(f"{i:>2}. {ps['paper']:<30} | {ps['versions']}/6 versions | {ps['citation_density']:>5.1f} cit/1Kw | {ps['citations']} total cit")
