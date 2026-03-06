"""
QUICK FIX - Fix indentation for coherence analysis methods
"""

from pathlib import Path
import shutil
from datetime import datetime

def fix_indentation():
    """Fix the indentation error in main_window_v2.py"""
    
    main_window_path = Path(__file__).parent / "ui" / "main_window_v2.py"
    
    print("=" * 70)
    print("FIXING INDENTATION ERROR")
    print("=" * 70)
    
    # Backup
    backup_path = main_window_path.parent / f"{main_window_path.stem}_backup_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}{main_window_path.suffix}"
    shutil.copy2(main_window_path, backup_path)
    print(f"[OK] Backup: {backup_path.name}")
    
    # Read file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"[READING] {len(lines)} lines")
    
    # Find the problematic line
    fixed = False
    for i, line in enumerate(lines):
        if line.strip().startswith('def _build_coherence_analysis_page(self):'):
            print(f"[FOUND] Problem at line {i+1}")
            
            # Find where to insert (after the last MainWindowV2.xxx = xxx line)
            insert_pos = i
            for j in range(i-1, max(0, i-50), -1):
                if 'MainWindowV2.' in lines[j] and '=' in lines[j]:
                    insert_pos = j + 1
                    break
            
            print(f"[FIXING] Will insert at line {insert_pos+1}")
            
            # Remove the incorrectly indented methods (from line i onwards)
            bad_code = lines[i:]
            lines = lines[:i]
            
            # De-indent the methods (remove 4 spaces from start of each line)
            fixed_code = []
            for line in bad_code:
                if line.startswith('    ') and not line.strip() == '':
                    fixed_code.append(line[4:])  # Remove 4 spaces
                elif line.strip() == '':
                    fixed_code.append(line)  # Keep empty lines
                else:
                    fixed_code.append(line)  # Keep lines already at module level
            
            # Add the fixed code
            lines.extend(fixed_code)
            
            # Now add the MainWindowV2 assignments at the end
            assignments = """
# Attach coherence analysis methods to class
MainWindowV2._build_coherence_analysis_page = _build_coherence_analysis_page
MainWindowV2._browse_cdcm_file = _browse_cdcm_file
MainWindowV2._load_cdcm_data = _load_cdcm_data
MainWindowV2._generate_cdcm_dashboard = _generate_cdcm_dashboard
MainWindowV2._export_cdcm_png = _export_cdcm_png
"""
            lines.append(assignments)
            
            fixed = True
            break
    
    if not fixed:
        print("[ERROR] Could not find the problematic method")
        return False
    
    # Write fixed file
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"[OK] File fixed!")
    print(f"[OK] New total: {len(lines)} lines")
    
    print("\n" + "=" * 70)
    print("[COMPLETE] Indentation fixed!")
    print("=" * 70)
    print("\nYou can now restart the app.")
    
    return True

if __name__ == "__main__":
    try:
        success = fix_indentation()
        if not success:
            print("\n[ERROR] Fix failed - restore from backup")
        input("\nPress Enter to close...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
