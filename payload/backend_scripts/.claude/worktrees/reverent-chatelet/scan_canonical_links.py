"""
CANONICAL VAULT LINK SCANNER
Scans O:\00_CANONICAL for all wikilinks and generates a link report
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Wikilink pattern - [[link]] or [[link|alias]]
LINK_PATTERN = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")

# Boundary condition pattern
BC_PATTERN = re.compile(r"\[(?:Violates|Enforces)\s+(BC-\d+[^\]]*)\]")

def extract_links(text):
    """Extract wikilinks from text."""
    if not text:
        return []
    # Remove code blocks
    text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text_no_code = re.sub(r"`[^`]+`", "", text_no_code)
    
    links = LINK_PATTERN.findall(text_no_code)
    cleaned = []
    for link in links:
        note_name = link.split('#')[0].strip()
        if note_name:
            cleaned.append(note_name)
    return list(set(cleaned))

def extract_bc_references(text):
    """Extract Boundary Condition references like [Violates BC-01 ...]"""
    if not text:
        return []
    return BC_PATTERN.findall(text)

def scan_vault(vault_path):
    """Scan vault and return link data."""
    vault = Path(vault_path)
    results = {
        'notes': [],
        'all_links': defaultdict(list),  # link_target -> [source_notes]
        'bc_references': defaultdict(list),  # BC-XX -> [source_notes]
        'orphan_links': [],  # links that point to non-existent notes
        'stats': {}
    }
    
    note_names = set()
    
    # First pass: collect all note names
    for path in vault.rglob('*.md'):
        note_names.add(path.stem)
    
    # Second pass: extract links
    for path in vault.rglob('*.md'):
        try:
            content = path.read_text(encoding='utf-8', errors='ignore')
        except:
            continue
        
        rel_path = str(path.relative_to(vault))
        note_name = path.stem
        
        links = extract_links(content)
        bc_refs = extract_bc_references(content)
        
        results['notes'].append({
            'path': rel_path,
            'name': note_name,
            'links': links,
            'bc_refs': bc_refs,
            'link_count': len(links),
            'bc_count': len(bc_refs)
        })
        
        # Track where each link target is referenced from
        for link in links:
            results['all_links'][link].append(note_name)
            if link not in note_names and not link.startswith('http'):
                results['orphan_links'].append({
                    'target': link,
                    'source': note_name,
                    'path': rel_path
                })
        
        for bc in bc_refs:
            results['bc_references'][bc].append(note_name)
    
    # Stats
    results['stats'] = {
        'total_notes': len(results['notes']),
        'total_links': sum(n['link_count'] for n in results['notes']),
        'unique_link_targets': len(results['all_links']),
        'total_bc_references': sum(n['bc_count'] for n in results['notes']),
        'unique_bc_references': len(results['bc_references']),
        'orphan_links': len(results['orphan_links'])
    }
    
    return results

def generate_report(results, output_path):
    """Generate HTML report."""
    stats = results['stats']
    
    # Sort by most linked
    most_linked = sorted(results['all_links'].items(), key=lambda x: len(x[1]), reverse=True)[:30]
    
    # Sort notes by link count
    most_connected = sorted(results['notes'], key=lambda x: x['link_count'], reverse=True)[:30]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Canonical Vault Link Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #1a1a1a;
            color: #e0e0e0;
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            padding: 20px;
        }}
        h1 {{ color: #7b68ee; margin-bottom: 5px; }}
        h2 {{ color: #4ecdc4; margin: 20px 0 10px 0; border-bottom: 1px solid #333; padding-bottom: 5px; }}
        h3 {{ color: #ff6b6b; margin: 15px 0 8px 0; }}
        .meta {{ color: #888; font-size: 10px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }}
        .stat {{ background: #252525; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-value {{ font-size: 24px; color: #7b68ee; font-weight: bold; }}
        .stat-label {{ font-size: 10px; color: #888; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th {{ text-align: left; padding: 8px; background: #252525; color: #888; }}
        td {{ padding: 8px; border-bottom: 1px solid #333; }}
        .link {{ color: #7b68ee; }}
        .bc {{ color: #ff6b6b; font-weight: bold; }}
        .orphan {{ color: #ff9800; }}
        .card {{ background: #252525; border-radius: 6px; padding: 15px; margin: 10px 0; }}
    </style>
</head>
<body>
    <h1>CANONICAL VAULT LINK REPORT</h1>
    <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Vault: O:\\00_CANONICAL</div>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{stats['total_notes']}</div>
            <div class="stat-label">Total Notes</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['total_links']}</div>
            <div class="stat-label">Total Links</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['unique_link_targets']}</div>
            <div class="stat-label">Unique Targets</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['total_bc_references']}</div>
            <div class="stat-label">BC References</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['unique_bc_references']}</div>
            <div class="stat-label">Unique BCs</div>
        </div>
        <div class="stat">
            <div class="stat-value">{stats['orphan_links']}</div>
            <div class="stat-label">Orphan Links</div>
        </div>
    </div>
    
    <h2>BOUNDARY CONDITION REFERENCES</h2>
    <div class="card">
        <table>
            <tr><th>Boundary Condition</th><th>Referenced In</th><th>Count</th></tr>
"""
    
    for bc, sources in sorted(results['bc_references'].items()):
        html += f"""            <tr>
                <td class="bc">{bc}</td>
                <td>{', '.join(sources[:5])}{'...' if len(sources) > 5 else ''}</td>
                <td>{len(sources)}</td>
            </tr>
"""
    
    html += """        </table>
    </div>
    
    <h2>MOST LINKED TARGETS (Top 30)</h2>
    <div class="card">
        <table>
            <tr><th>Target</th><th>Linked From</th><th>Count</th></tr>
"""
    
    for target, sources in most_linked:
        html += f"""            <tr>
                <td class="link">{target}</td>
                <td>{', '.join(sources[:3])}{'...' if len(sources) > 3 else ''}</td>
                <td>{len(sources)}</td>
            </tr>
"""
    
    html += """        </table>
    </div>
    
    <h2>MOST CONNECTED NOTES (Top 30)</h2>
    <div class="card">
        <table>
            <tr><th>Note</th><th>Outgoing Links</th><th>BC Refs</th></tr>
"""
    
    for note in most_connected:
        html += f"""            <tr>
                <td>{note['name']}</td>
                <td>{note['link_count']}</td>
                <td class="bc">{note['bc_count']}</td>
            </tr>
"""
    
    html += """        </table>
    </div>
"""
    
    if results['orphan_links']:
        html += """
    <h2>ORPHAN LINKS (Broken)</h2>
    <div class="card">
        <table>
            <tr><th>Target (Missing)</th><th>Source</th></tr>
"""
        for orphan in results['orphan_links'][:50]:
            html += f"""            <tr>
                <td class="orphan">{orphan['target']}</td>
                <td>{orphan['source']}</td>
            </tr>
"""
        html += """        </table>
    </div>
"""
    
    html += """
</body>
</html>"""
    
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"Report saved: {output_path}")

def main():
    vault_path = r"O:\00_CANONICAL"
    output_path = r"O:\Theophysics_Backend\Backend Python\data\canonical_link_report.html"
    json_output = r"O:\Theophysics_Backend\Backend Python\data\canonical_links.json"
    
    print("=" * 60)
    print("  CANONICAL VAULT LINK SCANNER")
    print("=" * 60)
    print(f"Scanning: {vault_path}")
    
    results = scan_vault(vault_path)
    
    print(f"\nSTATS:")
    for k, v in results['stats'].items():
        print(f"  {k}: {v}")
    
    # Save JSON
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump({
            'stats': results['stats'],
            'bc_references': dict(results['bc_references']),
            'all_links': {k: v for k, v in sorted(results['all_links'].items(), key=lambda x: len(x[1]), reverse=True)[:100]},
            'orphan_links': results['orphan_links']
        }, f, indent=2)
    print(f"\nJSON saved: {json_output}")
    
    # Generate HTML
    generate_report(results, output_path)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
