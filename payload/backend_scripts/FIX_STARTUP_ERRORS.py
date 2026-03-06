#!/usr/bin/env python3
"""
Fix Startup Errors for Theophysics Research Manager V2
- Fixes missing translation table path
- Fixes stats cache database error
- Integrates coherence metrics (Fruits of the Spirit)
"""

import shutil
from pathlib import Path

print("="*80)
print("  Fixing Theophysics Research Manager V2 Startup Errors")
print("="*80)

# Fix 1: Math Translation Table Path
print("\n[1/3] Fixing math translation table path...")

math_engine_file = Path("O:/Theophysics_Backend/Python_Backend/Backend Python/engine/math_translation_engine.py")

if math_engine_file.exists():
    content = math_engine_file.read_text(encoding='utf-8')
    
    # Replace the hardcoded path with a more flexible one
    old_line = '        self.excel_path = Path("O:/Theophysics_Backend/TTS_Pipeline/MATH_TRANSLATION_TABLE_UPDATED (1).xlsx")'
    new_lines = '''        # Try multiple possible paths for translation table
        possible_paths = [
            Path("O:/Theophysics_Backend/TTS_Pipeline/MATH_TRANSLATION_TABLE_UPDATED (1).xlsx"),
            Path("O:/Theophysics_Backend/TTS_Pipeline/MATH_TRANSLATION_TABLE.xlsx"),
            Path("O:/Theophysics_Backend/Python_Backend/Backend Python/data/MATH_TRANSLATION_TABLE.xlsx"),
        ]
        self.excel_path = None
        for p in possible_paths:
            if p.exists():
                self.excel_path = p
                break
        if not self.excel_path:
            # Use first path as default, but don't fail if missing
            self.excel_path = possible_paths[0]
            print(f"[WARN] Translation table not found at {self.excel_path}")'''
    
    if old_line in content:
        content = content.replace(old_line, new_lines)
        math_engine_file.write_text(content, encoding='utf-8')
        print("  [OK] Math translation engine updated")
    else:
        print("  [SKIP] Already patched or different format")
else:
    print("  [ERROR] Math engine file not found")

# Fix 2: Stats Cache Database Error
print("\n[2/3] Fixing stats cache database error...")

# Create cache directory if it doesn't exist
cache_dir = Path("O:/Theophysics_Backend/Python_Backend/Backend Python/cache")
cache_dir.mkdir(exist_ok=True)
print(f"  [OK] Cache directory: {cache_dir}")

# Fix 3: Add Coherence Metrics Integration
print("\n[3/3] Integrating Fruits of the Spirit coherence metrics...")

# Copy coherence engine from crawl4ai to backend
src_coherence = Path("D:/GitHub/crawl4ai/theophysics_coherence_engine")
dst_coherence = Path("O:/Theophysics_Backend/Python_Backend/Backend Python/core/coherence")

if src_coherence.exists():
    if not dst_coherence.exists():
        shutil.copytree(src_coherence, dst_coherence)
        print(f"  [OK] Coherence engine copied from {src_coherence}")
    else:
        print("  [OK] Coherence engine already present")
        # Update specific files
        for file in ["unified_scorer.py", "fruits_scorer.py", "rubrics"]:
            src_file = src_coherence / file
            dst_file = dst_coherence / file
            if src_file.exists():
                if src_file.is_dir():
                    if dst_file.exists():
                        shutil.rmtree(dst_file)
                    shutil.copytree(src_file, dst_file)
                else:
                    shutil.copy2(src_file, dst_file)
        print("  [OK] Coherence engine updated")
else:
    print("  [ERROR] Source coherence engine not found")
    print(f"    Expected at: {src_coherence}")

print("\n" + "="*80)
print("FIXES COMPLETE!")
print("="*80)
print("\nNext steps:")
print("1. Restart the application: LAUNCH_V2.bat")
print("2. The math translation warning can be ignored if you're not using that feature")
print("3. Coherence metrics are now available in core/coherence/")
print("\nTo use coherence scoring:")
print("  from core.coherence.unified_scorer import UnifiedCoherenceScorer")
print("  scorer = UnifiedCoherenceScorer()")
print("  result = scorer.score(text)")
print("  print(f'Coherence (chi): {result.chi:.3f}')")
