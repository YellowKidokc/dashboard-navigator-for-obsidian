"""
Launcher for Definition & Research Links GUI
Easy-to-run interface for managing definitions and research links
"""

import sys
from pathlib import Path

# Add UI directory to path
sys.path.append(str(Path(__file__).parent / "ui"))

from ui.definition_research_gui import main

if __name__ == "__main__":
    print("="*70)
    print("Starting Theophysics Definition & Research Manager GUI...")
    print("="*70)
    main()
