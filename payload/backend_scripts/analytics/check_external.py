import json

with open(r'O:\Theophysics_Backend\In_House_Programs\Theophysics theory downloader\Data_Analytics\Output\fruits_data.json') as f:
    data = json.load(f)

external = data.get('external', [])

with open(r'O:\Theophysics_Backend\Python_Backend\Backend Python\analytics\external_theories_list.txt', 'w', encoding='utf-8') as out:
    out.write(f'External theories count: {len(external)}\n\n')
    for t in external:
        name = t.get('name', 'NO NAME')
        out.write(f'{name}\n')
    
    spinoza = [t for t in external if 'spinoza' in t.get('name','').lower()]
    out.write(f'\nSpinoza found: {len(spinoza)}\n')

print('Done - check Backend Python/analytics/external_theories_list.txt')
