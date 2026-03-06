"""
GITHUB READINESS AUDIT
======================
Scans the Backend Python folder and identifies:
1. Files that SHOULD be committed
2. Files that should NOT be committed (secrets, db, venv)
3. Files that are unclear
4. Generates a cleanup report

Run this before pushing to GitHub!
"""

import os
from pathlib import Path
from collections import defaultdict
import json

BASE = r"O:\Theophysics_Backend\Backend Python"

# Files/folders that should NEVER go to GitHub
EXCLUDE_PATTERNS = {
    'directories': [
        'venv', 'env', '.venv', '__pycache__', '.git', 
        '_BACKUPS', '.claude', 'node_modules', '.idea', '.vscode'
    ],
    'extensions': [
        '.db', '.sqlite', '.sqlite3', '.log', '.pyc', '.pyo',
        '.key', '.pem', '.env', '.bak', '.tmp'
    ],
    'files': [
        'theophysics_config.json', 'secrets.json', 'credentials.json',
        'openai_key.txt', 'anthropic_key.txt', '.DS_Store', 'Thumbs.db',
        'desktop.ini', 'ollama_run.log'
    ]
}

# Files that SHOULD go to GitHub
INCLUDE_PATTERNS = {
    'extensions': ['.py', '.md', '.txt', '.bat', '.sh', '.json', '.yaml', '.yml'],
    'files': ['LICENSE', 'README.md', 'requirements.txt', '.gitignore', 'CONTRIBUTING.md']
}

def analyze_folder(base_path):
    """Categorize all files"""
    results = {
        'should_commit': [],
        'should_exclude': [],
        'unclear': [],
        'stats': defaultdict(int)
    }
    
    base = Path(base_path)
    
    for item in base.rglob('*'):
        if item.is_dir():
            continue
            
        rel_path = item.relative_to(base)
        parts = rel_path.parts
        
        # Check if in excluded directory
        in_excluded_dir = any(part in EXCLUDE_PATTERNS['directories'] for part in parts)
        
        # Check extension
        ext = item.suffix.lower()
        is_excluded_ext = ext in EXCLUDE_PATTERNS['extensions']
        is_included_ext = ext in INCLUDE_PATTERNS['extensions']
        
        # Check filename
        is_excluded_file = item.name in EXCLUDE_PATTERNS['files']
        is_included_file = item.name in INCLUDE_PATTERNS['files']
        
        # Categorize
        if in_excluded_dir or is_excluded_ext or is_excluded_file:
            results['should_exclude'].append({
                'path': str(rel_path),
                'reason': 'excluded_dir' if in_excluded_dir else 'excluded_ext' if is_excluded_ext else 'excluded_file',
                'size_kb': item.stat().st_size / 1024
            })
            results['stats']['excluded'] += 1
        elif is_included_ext or is_included_file:
            results['should_commit'].append({
                'path': str(rel_path),
                'size_kb': item.stat().st_size / 1024
            })
            results['stats']['commit'] += 1
        else:
            results['unclear'].append({
                'path': str(rel_path),
                'size_kb': item.stat().st_size / 1024
            })
            results['stats']['unclear'] += 1
    
    return results

def print_report(results):
    """Print formatted report"""
    print("=" * 80)
    print("GITHUB READINESS AUDIT")
    print("=" * 80)
    
    print(f"\n📊 SUMMARY:")
    print(f"   ✅ Files to COMMIT:  {results['stats']['commit']}")
    print(f"   ❌ Files to EXCLUDE: {results['stats']['excluded']}")
    print(f"   ❓ Unclear:          {results['stats']['unclear']}")
    
    total_commit_size = sum(f['size_kb'] for f in results['should_commit'])
    total_exclude_size = sum(f['size_kb'] for f in results['should_exclude'])
    
    print(f"\n💾 SIZE ANALYSIS:")
    print(f"   Commit size:  {total_commit_size/1024:.2f} MB")
    print(f"   Exclude size: {total_exclude_size/1024:.2f} MB")
    
    print("\n" + "=" * 80)
    print("✅ FILES TO COMMIT (showing first 50)")
    print("=" * 80)
    for f in sorted(results['should_commit'], key=lambda x: x['path'])[:50]:
        print(f"   {f['path']}")
    
    if results['unclear']:
        print("\n" + "=" * 80)
        print("❓ UNCLEAR FILES (review manually)")
        print("=" * 80)
        for f in results['unclear']:
            print(f"   {f['path']} ({f['size_kb']:.1f} KB)")
    
    print("\n" + "=" * 80)
    print("❌ LARGE EXCLUDED FILES (>100KB)")
    print("=" * 80)
    large_excluded = [f for f in results['should_exclude'] if f['size_kb'] > 100]
    for f in sorted(large_excluded, key=lambda x: -x['size_kb'])[:20]:
        print(f"   {f['size_kb']:.1f} KB | {f['path']}")
    
    # Check for secrets
    print("\n" + "=" * 80)
    print("🔐 SECURITY CHECK")
    print("=" * 80)
    
    security_keywords = ['key', 'secret', 'password', 'token', 'credential', 'api']
    security_concerns = []
    
    for f in results['should_commit']:
        name_lower = f['path'].lower()
        if any(kw in name_lower for kw in security_keywords):
            security_concerns.append(f['path'])
    
    if security_concerns:
        print("   ⚠️ WARNING: These files might contain secrets:")
        for path in security_concerns:
            print(f"      {path}")
    else:
        print("   ✅ No obvious security concerns in commit list")
    
    return results

def main():
    print(f"\nScanning: {BASE}\n")
    results = analyze_folder(BASE)
    print_report(results)
    
    # Save report
    report_path = Path(BASE) / "GITHUB_AUDIT_REPORT.json"
    with open(report_path, 'w') as f:
        json.dump({
            'should_commit': results['should_commit'],
            'should_exclude': [e for e in results['should_exclude'] if e['size_kb'] > 10],
            'unclear': results['unclear'],
            'stats': dict(results['stats'])
        }, f, indent=2)
    
    print(f"\n📄 Full report saved to: {report_path}")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("📋 RECOMMENDED ACTIONS")
    print("=" * 80)
    print("""
1. DELETE before push:
   - venv/ folder (users will create their own)
   - _BACKUPS/ (not needed in repo)
   - *.db files (database should be created fresh)
   - *.log files
   - theophysics_config.json (contains settings)
   
2. CREATE before push:
   - theophysics_config.example.json (template without secrets)
   - .env.example (template for environment variables)
   
3. VERIFY:
   - No API keys in any committed file
   - No personal paths hard-coded
   - requirements.txt is complete
   
4. GIT COMMANDS:
   git status
   git add -A
   git commit -m "Clean version for public release"
   git push origin main
""")

if __name__ == "__main__":
    main()
