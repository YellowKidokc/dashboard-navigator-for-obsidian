"""Check exact line content"""
with open(r'O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')
print(f'Line 4375: {repr(lines[4374][:60])}')
print(f'Line 4376: {repr(lines[4375][:60])}')  
print(f'Line 4377: {repr(lines[4376][:60])}')

# Check for leading spaces
line_4376 = lines[4375]
leading_spaces = len(line_4376) - len(line_4376.lstrip())
print(f'\nLeading spaces on line 4376: {leading_spaces}')
print(f'First 10 chars: {repr(line_4376[:10])}')
