"""
VAULT ANALYTICS DASHBOARD RUNNER
==================================
Run comprehensive vault analytics with custom folder selection.

Usage: python run_vault_dashboard.py <input_folder> <output_folder>

Author: Claude + David Lowe
Date: January 2026
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add Python folder to path for imports
PYTHON_FOLDER = Path(__file__).parent.parent.parent / "Python"
sys.path.insert(0, str(PYTHON_FOLDER))

def generate_vault_analytics(input_folder: str, output_folder: str):
    """Generate comprehensive vault analytics"""
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    
    print(f"📊 VAULT ANALYTICS DASHBOARD")
    print(f"=" * 70)
    print(f"📁 Input:  {input_path}")
    print(f"📤 Output: {output_path}")
    print(f"=" * 70)
    print()
    
    # Ensure output folder exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Statistics dictionary
    stats = {
        'generated_at': datetime.now().isoformat(),
        'input_folder': str(input_path),
        'output_folder': str(output_path),
        'total_files': 0,
        'total_md_files': 0,
        'total_words': 0,
        'total_size_mb': 0,
        'file_types': {}
    }
    
    print("🔍 Scanning folder structure...")
    
    # Scan all files
    all_files = list(input_path.rglob('*'))
    stats['total_files'] = len([f for f in all_files if f.is_file()])
    
    print(f"   Found {stats['total_files']} files")
    
    # Count file types
    for file in all_files:
        if file.is_file():
            ext = file.suffix.lower()
            stats['file_types'][ext] = stats['file_types'].get(ext, 0) + 1
            
            # Calculate size
            try:
                stats['total_size_mb'] += file.stat().st_size / (1024 * 1024)
            except:
                pass
    
    # Analyze markdown files
    print("📝 Analyzing markdown files...")
    md_files = list(input_path.rglob('*.md'))
    stats['total_md_files'] = len(md_files)
    
    word_counts = {}
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            word_count = len(content.split())
            stats['total_words'] += word_count
            word_counts[str(md_file.relative_to(input_path))] = word_count
        except Exception as e:
            print(f"   ⚠️ Error reading {md_file.name}: {e}")
    
    print(f"   Analyzed {stats['total_md_files']} markdown files")
    print(f"   Total words: {stats['total_words']:,}")
    
    # Find top 20 largest files
    top_files = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    stats['top_20_files'] = [{'file': f, 'words': w} for f, w in top_files]
    
    # Save statistics
    print()
    print("💾 Saving results...")
    
    stats_file = output_path / "vault_analytics.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✓ Statistics: {stats_file}")
    
    # Generate markdown report
    report_file = output_path / "vault_analytics_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# Vault Analytics Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Input Folder:** `{input_path}`\n\n")
        f.write(f"**Output Folder:** `{output_path}`\n\n")
        f.write(f"---\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Total Files:** {stats['total_files']:,}\n")
        f.write(f"- **Markdown Files:** {stats['total_md_files']:,}\n")
        f.write(f"- **Total Words:** {stats['total_words']:,}\n")
        f.write(f"- **Total Size:** {stats['total_size_mb']:.2f} MB\n\n")
        f.write(f"## File Types\n\n")
        for ext, count in sorted(stats['file_types'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"- `{ext or 'no extension'}`: {count:,} files\n")
        f.write(f"\n## Top 20 Largest Files (by word count)\n\n")
        for i, item in enumerate(stats['top_20_files'], 1):
            f.write(f"{i}. **{item['file']}** - {item['words']:,} words\n")
    
    print(f"   ✓ Report: {report_file}")
    
    print()
    print("=" * 70)
    print("✅ COMPLETE!")
    print(f"📊 View results in: {output_path}")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("ERROR: Missing arguments")
        print("Usage: python run_vault_dashboard.py <input_folder> <output_folder>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    if not os.path.exists(input_folder):
        print(f"ERROR: Input folder does not exist: {input_folder}")
        sys.exit(1)
    
    generate_vault_analytics(input_folder, output_folder)
