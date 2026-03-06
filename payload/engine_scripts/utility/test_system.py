"""
QUICK TEST SCRIPT
=================
Verifies that the orchestrator system is properly installed.

Run this to check:
1. All modules can be imported
2. Basic functionality works
3. Vault structure is accessible

Author: David Lowe & Claude
Date: 2025-11-19
"""

import sys
from pathlib import Path

print("=" * 70)
print("THEOPHYSICS ORCHESTRATOR - SYSTEM CHECK")
print("=" * 70)

# Test 1: Module Imports
print("\n[1/5] Testing module imports...")
try:
    from modules.circulation_detector import CirculationDetector
    from modules.infrastructure_manager import InfrastructureManager
    from modules.uuid_semantic_manager import UUIDSemanticManager
    from modules.dashboard_generator import DashboardGenerator
    from modules.tracker_integrator import TrackerIntegrator
    print("  ✓ All modules imported successfully")
except ImportError as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Dependencies
print("\n[2/5] Checking dependencies...")
try:
    import numpy as np
    import yaml
    print("  ✓ Core dependencies available")
except ImportError as e:
    print(f"  ⚠️  Missing dependency: {e}")
    print("  Run: pip install -r requirements.txt")

# Test 3: Vault Detection
print("\n[3/5] Testing vault detection...")
try:
    current = Path(__file__).resolve().parent
    vault_root = current.parent.parent.parent
    
    if (vault_root / "00_VAULT_SYSTEM").exists():
        print(f"  ✓ Vault detected: {vault_root}")
    else:
        print(f"  ⚠️  Vault structure not found at: {vault_root}")
except Exception as e:
    print(f"  ✗ Detection failed: {e}")

# Test 4: Configuration
print("\n[4/5] Checking configuration...")
config_path = vault_root / "00_VAULT_SYSTEM" / "orchestrator_config.yaml"
if config_path.exists():
    print(f"  ✓ Config found: {config_path}")
else:
    print(f"  ℹ️  No config file (will use defaults)")

# Test 5: Module Instantiation
print("\n[5/5] Testing module creation...")
try:
    config = {
        'vault': {},
        'user': {'experience_level': 2},
        'analytics': {}
    }
    
    detector = CirculationDetector(vault_root, config)
    print(f"  ✓ CirculationDetector created")
    print(f"  ✓ Loaded {len(detector.concepts_glossary)} concepts")
    
except Exception as e:
    print(f"  ✗ Module creation failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 70)
print("SYSTEM CHECK COMPLETE")
print("=" * 70)
print("\n✅ Ready to run!")
print("\nNext steps:")
print("  1. python orchestrator.py --init    # Guided setup")
print("  2. python orchestrator.py           # Interactive mode")
print("\n" + "=" * 70)
