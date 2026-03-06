# API Query System - Integration Guide
# =====================================
# 
# This module adds API query capabilities to the Theophysics Backend.
# 
# INSTALLATION STEPS:
# 
# 1. Files created:
#    - core/api_manager.py          - API calling, caching, tracking
#    - engine/api_query_engine.py   - Query templates, job management
#    - ui/tabs/api_query_tab.py     - GUI tab
#    - config/api_endpoints.json    - Saved endpoints
#    - config/api_jobs.json         - Saved jobs
#    - data/api_cache/              - Downloaded data folder
#
# 2. To add the tab to MainWindowV2, add to NAV_ITEMS:
#
#    NAV_ITEMS = [
#        ("🏠", "Dashboard"),
#        ("📄", "Paper Scanner"),
#        ...
#        ("🔌", "API Query"),  # <-- ADD THIS LINE
#        ("⚙️", "Settings"),
#    ]
#
# 3. In the _setup_ui method, add the page creation:
#
#    # After other page creations, add:
#    from core.api_manager import APIManager
#    from engine.api_query_engine import APIQueryEngine
#    from ui.tabs.api_query_tab import APIQueryTab
#    
#    self.api_manager = APIManager()
#    self.query_engine = APIQueryEngine(self.api_manager)
#    self.api_query_tab = APIQueryTab(self.api_manager, self.query_engine)
#    self.stacked.addWidget(self.api_query_tab)
#
# USAGE EXAMPLE:
# ==============

from pathlib import Path

def demo_api_query():
    """Demo the API query system"""
    from core.api_manager import APIManager, BUILTIN_APIS
    from engine.api_query_engine import APIQueryEngine, PRESET_TEMPLATES
    
    # Initialize
    api = APIManager()
    engine = APIQueryEngine(api)
    
    # Add a custom endpoint
    ep_id = api.add_endpoint(
        name="Semantic Scholar",
        url="https://api.semanticscholar.org/graph/v1/paper/search",
        method="GET",
        params={"fields": "title,abstract,authors,year", "limit": 10}
    )
    
    # Create a job with variable parameters
    job_id = api.create_job(
        name="HeartMath Research",
        endpoint_id=ep_id,
        params={"query": "HeartMath HRV coherence"},
        param_variants={
            "limit": [10, 25, 50],
            "year": [2020, 2021, 2022, 2023, 2024]
        },
        description="Search for HeartMath-related papers"
    )
    
    # Run the job (single run)
    results = api.run_job(job_id)
    print(f"Results: {len(results)}")
    
    # Run with specific variants
    results = api.run_job(job_id, {"limit": 25, "year": 2023})
    
    # Run ALL variant combinations (10 * 5 = 50 calls!)
    # results = api.run_job_all_variants(job_id)
    
    # Use a template
    template = PRESET_TEMPLATES["heartmath_hrv"]
    params = template.build_params({"topic": "HRV moral behavior", "limit": 25})
    result = api.call_api(ep_id, params)
    
    # Check history
    history = api.get_call_history(10)
    for call in history:
        print(f"{call['timestamp']}: {call['success']}")
    
    return results


# QUICK LAUNCHER
# ==============
# Run this standalone to test the API Query tab

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    
    from core.api_manager import APIManager
    from engine.api_query_engine import APIQueryEngine
    from ui.tabs.api_query_tab import APIQueryTab
    from ui.styles_v2 import DARK_THEME_V2
    
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_V2)
    
    # Create components
    api_manager = APIManager()
    query_engine = APIQueryEngine(api_manager)
    
    # Create window
    window = QMainWindow()
    window.setWindowTitle("🔌 API Query Builder")
    window.setGeometry(100, 100, 1400, 900)
    
    # Add tab as central widget
    tab = APIQueryTab(api_manager, query_engine)
    window.setCentralWidget(tab)
    
    window.show()
    sys.exit(app.exec())
