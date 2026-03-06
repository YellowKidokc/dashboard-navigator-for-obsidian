import json

with open(r'O:\Theophysics_Backend\Python_Backend\Backend Python\analytics\axiom_coherence_results.json') as f:
    data = json.load(f)

raw_scores = [a['raw_score'] for a in data['axioms']]
sorted_by_raw = sorted(data['axioms'], key=lambda x: -x['raw_score'])

print('RAW SCORE DISTRIBUTION (actual variance before cap):')
print(f'Max: {max(raw_scores):.0f}')
print(f'Min: {min(raw_scores):.0f}')  
print(f'Avg: {sum(raw_scores)/len(raw_scores):.0f}')
print()
print('TOP 10 by raw score:')
for a in sorted_by_raw[:10]:
    print(f"  {a['raw_score']:7.0f} | {a['name'][:45]}")
print()
print('BOTTOM 10 by raw score:')
for a in sorted_by_raw[-10:]:
    print(f"  {a['raw_score']:7.0f} | {a['name'][:45]}")
