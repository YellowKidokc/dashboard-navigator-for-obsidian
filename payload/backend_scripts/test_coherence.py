"""
CDCM System Test Script
Run this standalone to verify the coherence analysis system
"""

from pathlib import Path
import sys

print("=" * 70)
print("CDCM SYSTEM TEST")
print("=" * 70)

# Test 1: Import modules
print("\n[1/5] Testing imports...")
try:
    from core.coherence import load_cdcm, CDCMAnalyzer
    from core.coherence.html_generator import generate_dashboard, CDCMDashboardGenerator
    print("✓ All modules imported successfully")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Find CDCM Excel file
print("\n[2/5] Locating CDCM.xlsx...")
possible_paths = [
    Path("O:/Theophysics_Backend/CDCM.xlsx"),
    Path("O:/Theophysics_Backend/Backend Python/CDCM.xlsx"),
    Path("./CDCM.xlsx"),
]

cdcm_path = None
for path in possible_paths:
    if path.exists():
        cdcm_path = path
        break

if not cdcm_path:
    print("✗ CDCM.xlsx not found in expected locations:")
    for p in possible_paths:
        print(f"  - {p}")
    print("\nPlease specify path:")
    user_path = input("Path to CDCM.xlsx: ").strip()
    cdcm_path = Path(user_path)
    if not cdcm_path.exists():
        print("✗ File not found. Exiting.")
        sys.exit(1)

print(f"✓ Found CDCM.xlsx at: {cdcm_path}")

# Test 3: Load and parse Excel
print("\n[3/5] Loading Excel workbook...")
try:
    analyzer = load_cdcm(cdcm_path)
    if not analyzer:
        print("✗ Failed to load workbook")
        sys.exit(1)
    
    framework_count = len(analyzer.frameworks)
    print(f"✓ Loaded {framework_count} framework(s)")
    
    for name in analyzer.get_all_framework_names():
        framework = analyzer.get_framework(name)
        axiom_count = len(framework.axioms)
        print(f"  • {name}: {axiom_count} axioms")
    
except Exception as e:
    print(f"✗ Loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Compute metrics
print("\n[4/5] Computing metrics...")
try:
    primary = analyzer.get_framework("Primary")
    if not primary:
        print("✗ Primary framework not found")
        sys.exit(1)
    
    metrics = primary.get_all_metrics()
    
    print(f"✓ Computed {len(metrics)} metrics")
    print("\nKey Metrics:")
    print(f"  • Mean Net Score: {metrics['mean_net_score']}")
    print(f"  • Fracture Rate: {metrics['fracture_rate']}%")
    print(f"  • Constraint Coverage: {metrics['constraint_coverage_ratio']:.1%}")
    print(f"  • Constraint Efficiency: {metrics['constraint_efficiency']:.2f}")
    print(f"  • Positive Directionality: {metrics['positive_directionality_ratio']:.1%}")
    print(f"  • Phase Transition Proximity: {metrics['phase_transition_proximity']:.2f}")
    
    # Status indicators
    status = []
    if metrics['mean_net_score'] >= 5.0:
        status.append("✓ Mean Net Score: GOOD")
    elif metrics['mean_net_score'] >= 3.0:
        status.append("⚠ Mean Net Score: MODERATE")
    else:
        status.append("✗ Mean Net Score: POOR")
    
    if metrics['fracture_rate'] < 20:
        status.append("✓ Fracture Rate: GOOD")
    elif metrics['fracture_rate'] < 40:
        status.append("⚠ Fracture Rate: MODERATE")
    else:
        status.append("✗ Fracture Rate: POOR")
    
    print("\nStatus:")
    for s in status:
        print(f"  {s}")

except Exception as e:
    print(f"✗ Metrics computation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Generate HTML dashboard
print("\n[5/5] Generating HTML dashboard...")
try:
    output_dir = Path("O:/Theophysics_Backend/test_output")
    output_dir.mkdir(exist_ok=True)
    
    dashboard_path = generate_dashboard(analyzer, "Primary", output_dir)
    
    print(f"✓ Dashboard generated: {dashboard_path}")
    print(f"\nYou can open this file in your browser:")
    print(f"  file:///{dashboard_path}")
    
    # Check file size
    file_size = dashboard_path.stat().st_size
    print(f"\nDashboard size: {file_size:,} bytes")
    
except Exception as e:
    print(f"✗ Dashboard generation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("TEST COMPLETE - ALL SYSTEMS OPERATIONAL")
print("=" * 70)
print("\nNext Steps:")
print("1. Open the generated dashboard in your browser")
print("2. Wire the tab into main_window_v2.py (see README.md)")
print("3. Launch the full GUI application")
print("4. Test with the Coherence Analysis tab")
print("\nQuick GUI Test:")
print("  python main.py  # or LAUNCH_V2.bat")
print("=" * 70)
