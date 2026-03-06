import os
import re
from pathlib import Path
from collections import defaultdict

BASE = os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3')

def count_words(text):
    return len(text.split())

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        axioms = len(re.findall(r'Axiom|%%tag::Axiom::', text, re.IGNORECASE))
        equations = len(re.findall(r'[χΨΦΛΩ∫∑∏∂∇]|=.*[+\-*/]', text))
        citations = len(re.findall(r'\([A-Z][a-z]+.*?\d{4}\)', text))
        return {
            'name': filepath.name,
            'folder': filepath.parent.name,
            'words': count_words(text),
            'lines': len(text.splitlines()),
            'axioms': axioms,
            'equations': equations,
            'citations': citations,
            'kb': filepath.stat().st_size / 1024
        }
    except:
        return None

results = []
base = Path(BASE)
# Scan all .md in vault (Logos, 02_THEOPHYSICS, etc.)
for md in base.rglob('*.md'):
    r = analyze_file(md)
    if r and r['words'] > 100:
        results.append(r)

results.sort(key=lambda x: x['words'], reverse=True)

total_words = sum(r['words'] for r in results)
total_axioms = sum(r['axioms'] for r in results)
total_equations = sum(r['equations'] for r in results)
total_citations = sum(r['citations'] for r in results)

print('=== THEOPHYSICS CORPUS STATISTICS ===')
print(f'Total files analyzed: {len(results)}')
print(f'Total words: {total_words:,}')
print(f'Total axiom refs: {total_axioms:,}')
print(f'Total equation patterns: {total_equations:,}')
print(f'Total citations: {total_citations:,}')
print()
print('=== TOP 25 FILES BY WORD COUNT ===')
for r in results[:25]:
    fname = r['name'][:45]
    print(f"{r['words']:>8,} words | {r['axioms']:>3} ax | {r['citations']:>3} cit | {r['folder']}/{fname}")

print()
print('=== BY PAPER FOLDER ===')
folder_stats = defaultdict(lambda: {'words': 0, 'files': 0, 'axioms': 0, 'citations': 0})
for r in results:
    folder = r['folder']
    folder_stats[folder]['words'] += r['words']
    folder_stats[folder]['files'] += 1
    folder_stats[folder]['axioms'] += r['axioms']
    folder_stats[folder]['citations'] += r['citations']

sorted_folders = sorted(folder_stats.items(), key=lambda x: x[1]['words'], reverse=True)
for folder, stats in sorted_folders[:30]:
    print(f"{stats['words']:>8,} words | {stats['files']:>3} files | {stats['axioms']:>4} ax | {stats['citations']:>4} cit | {folder}")

print()
print('=== PUBLICATION READINESS SCORE ===')
# Score = words + (citations * 100) + (axioms * 50) - penalty for being in _working folders
for r in results[:15]:
    score = r['words'] + (r['citations'] * 100) + (r['axioms'] * 50)
    if '_' in r['folder']:
        score = int(score * 0.7)  # Penalty for working folders
    print(f"{score:>10,} score | {r['name'][:50]}")
