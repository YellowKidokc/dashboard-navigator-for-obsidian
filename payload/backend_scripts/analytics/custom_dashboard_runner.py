"""
CUSTOM METRICS DASHBOARD RUNNER
=================================
Run custom dashboard generation with folder selection.
Integrates metrics from the Python folder scripts.

Usage: python custom_dashboard_runner.py <input_folder> <output_folder>

Author: Claude + David Lowe
Date: January 2026
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json
import re
from collections import Counter

def count_pattern(content: str, pattern: str, flags=re.IGNORECASE) -> int:
    """Count regex pattern occurrences"""
    return len(re.findall(pattern, content, flags))

def generate_custom_dashboard(input_folder: str, output_folder: str):
    """Generate custom metrics dashboard"""
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    print(f"🌟 CUSTOM METRICS DASHBOARD")
    print(f"=" * 70)
    print(f"📁 Input:  {input_path}")
    print(f"📤 Output: {output_path}")
    print(f"=" * 70)
    print()
    
    # Ensure output folder exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize metrics
    metrics = {
        'generated_at': datetime.now().isoformat(),
        'input_folder': str(input_path),
        'output_folder': str(output_path),
        'corpus_metrics': {},
        'paper_metrics': {},
        'experimental_metrics': {},
        'coherence_metrics': {}
    }
    
    print("📊 [1/4] Calculating corpus metrics...")
    md_files = list(input_path.rglob('*.md'))
    
    total_words = 0
    total_axioms = 0
    total_equations = 0
    total_citations = 0
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            total_words += len(content.split())
            total_axioms += count_pattern(content, r'\bAxiom[:\s]')
            total_equations += count_pattern(content, r'\$\$.*?\$\$', re.DOTALL)
            total_citations += count_pattern(content, r'\[\d+\]')
        except:
            pass
    
    metrics['corpus_metrics'] = {
        'total_files': len(md_files),
        'total_words': total_words,
        'total_axioms': total_axioms,
        'total_equations': total_equations,
        'total_citations': total_citations,
        'avg_words_per_file': total_words // len(md_files) if md_files else 0
    }
    
    print(f"   ✓ Files: {len(md_files)}, Words: {total_words:,}, Axioms: {total_axioms}")
    
    print("📝 [2/4] Analyzing paper structure...")
    # Look for paper folders
    paper_folders = [d for d in input_path.glob('*') if d.is_dir() and d.name.startswith('P')]
    
    for paper_folder in paper_folders:
        paper_files = list(paper_folder.rglob('*.md'))
        paper_words = sum(len(f.read_text(encoding='utf-8', errors='ignore').split()) 
                         for f in paper_files)
        
        metrics['paper_metrics'][paper_folder.name] = {
            'files': len(paper_files),
            'words': paper_words
        }
    
    print(f"   ✓ Found {len(paper_folders)} paper folders")
    
    print("🔬 [3/4] Scanning experimental statistics...")
    experimental_patterns = {
        'sigma_values': r'(\d+\.?\d*)\s*sigma',
        'p_values': r'p\s*[<>=]\s*0\.\d+',
        'sample_sizes': r'n\s*=\s*(\d+)',
        'correlations': r'r\s*=\s*0\.\d+'
    }
    
    exp_counts = Counter()
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            for key, pattern in experimental_patterns.items():
                exp_counts[key] += count_pattern(content, pattern)
        except:
            pass
    
    metrics['experimental_metrics'] = dict(exp_counts)
    print(f"   ✓ Sigma values: {exp_counts['sigma_values']}, P-values: {exp_counts['p_values']}")
    
    print("🎯 [4/4] Calculating coherence indicators...")
    coherence_terms = ['coherent', 'consistent', 'integrated', 'unified', 'convergent']
    coherence_counts = Counter()
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore').lower()
            for term in coherence_terms:
                coherence_counts[term] += content.count(term)
        except:
            pass
    
    metrics['coherence_metrics'] = {
        'term_counts': dict(coherence_counts),
        'total_coherence_terms': sum(coherence_counts.values())
    }
    
    print(f"   ✓ Total coherence terms: {sum(coherence_counts.values())}")
    
    # Save metrics
    print()
    print("💾 Saving dashboard...")
    
    metrics_file = output_path / "custom_metrics.json"
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    print(f"   ✓ Metrics: {metrics_file}")
    
    # Generate HTML dashboard
    html_file = output_path / "custom_dashboard.html"
    html_content = generate_html_dashboard(metrics)
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✓ Dashboard: {html_file}")
    
    # Generate markdown summary
    summary_file = output_path / "dashboard_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"# Custom Metrics Dashboard\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Corpus Metrics\n\n")
        for key, value in metrics['corpus_metrics'].items():
            f.write(f"- **{key.replace('_', ' ').title()}:** {value:,}\n")
        f.write(f"\n## Paper Metrics\n\n")
        for paper, data in metrics['paper_metrics'].items():
            f.write(f"### {paper}\n")
            f.write(f"- Files: {data['files']}\n")
            f.write(f"- Words: {data['words']:,}\n\n")
        f.write(f"## Experimental Metrics\n\n")
        for key, value in metrics['experimental_metrics'].items():
            f.write(f"- **{key.replace('_', ' ').title()}:** {value}\n")
        f.write(f"\n## Coherence Metrics\n\n")
        f.write(f"- **Total Coherence Terms:** {metrics['coherence_metrics']['total_coherence_terms']:,}\n\n")
        for term, count in metrics['coherence_metrics']['term_counts'].items():
            f.write(f"  - {term}: {count}\n")
    
    print(f"   ✓ Summary: {summary_file}")
    
    print()
    print("=" * 70)
    print("✅ DASHBOARD COMPLETE!")
    print(f"📊 Open in browser: {html_file}")
    print("=" * 70)

def generate_html_dashboard(metrics: dict) -> str:
    """Generate HTML dashboard"""
    cm = metrics['corpus_metrics']
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Custom Metrics Dashboard</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(22, 33, 62, 0.9);
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #00d9ff;
            text-align: center;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 40px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            padding: 25px;
            border-radius: 8px;
            border-left: 4px solid #00d9ff;
        }}
        .metric-label {{
            font-size: 0.9em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            font-size: 2.5em;
            color: #00d9ff;
            font-weight: bold;
            margin: 10px 0;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>⚛️ Custom Metrics Dashboard</h1>
        <div class="subtitle">Theophysics Backend Analytics System</div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Files</div>
                <div class="metric-value">{cm['total_files']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Words</div>
                <div class="metric-value">{cm['total_words']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Axioms</div>
                <div class="metric-value">{cm['total_axioms']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Equations</div>
                <div class="metric-value">{cm['total_equations']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Citations</div>
                <div class="metric-value">{cm['total_citations']:,}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Avg Words/File</div>
                <div class="metric-value">{cm['avg_words_per_file']:,}</div>
            </div>
        </div>
        
        <div class="timestamp">
            Generated: {metrics['generated_at']}<br>
            Input: {metrics['input_folder']}<br>
            Output: {metrics['output_folder']}
        </div>
    </div>
</body>
</html>"""
    return html

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("ERROR: Missing arguments")
        print("Usage: python custom_dashboard_runner.py <input_folder> <output_folder>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    if not os.path.exists(input_folder):
        print(f"ERROR: Input folder does not exist: {input_folder}")
        sys.exit(1)
    
    generate_custom_dashboard(input_folder, output_folder)
