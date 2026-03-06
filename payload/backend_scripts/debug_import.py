
try:
    from ui.main_window_v2 import MainWindowV2
    print("Import successful")
    if hasattr(MainWindowV2, '_build_def_scanner_page'):
        print("Method found")
    else:
        print("Method NOT found on class")
except Exception as e:
    print(f"Import failed: {e}")
