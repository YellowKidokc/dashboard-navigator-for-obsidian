"""Check function body indentation"""
with open(r'O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Check lines 4376-4390 (function definition + body)
for i in range(4375, min(4390, len(lines))):
    line = lines[i]
    leading = len(line) - len(line.lstrip())
    print(f'Line {i+1:4d} [{leading:2d} spaces]: {line[:70].rstrip()}')
