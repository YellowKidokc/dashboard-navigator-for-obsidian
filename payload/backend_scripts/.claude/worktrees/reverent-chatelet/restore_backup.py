"""Restore from backup"""
import shutil
from pathlib import Path

backup = Path(r"O:\Theophysics_Backend\Backend Python\ui\main_window_v2_backup_20251226_035432.py")
target = Path(r"O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py")

if backup.exists():
    shutil.copy2(backup, target)
    print(f"[OK] Restored from {backup.name}")
    print(f"[OK] File size: {target.stat().st_size} bytes")
else:
    print(f"[ERROR] Backup not found: {backup}")
