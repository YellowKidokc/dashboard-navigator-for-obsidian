"""Add missing blank line"""
with open(r'O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Insert blank line after line 4375 (before def _build_coherence_analysis_page)
lines.insert(4375, '\n')

with open(r'O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('[OK] Added blank line before function definition')
print(f'[OK] Total lines now: {len(lines)}')
