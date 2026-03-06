"""
AUTO-PATCH SCRIPT - Add Coherence Analysis Tab
Automatically integrates CDCM dashboard into main_window_v2.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create timestamped backup."""
    backup_path = filepath.parent / f"{filepath.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    print(f"[OK] Backup created: {backup_path.name}")
    return backup_path

def apply_patch():
    """Apply coherence analysis tab patch to main_window_v2.py"""
    
    main_window_path = Path(__file__).parent / "ui" / "main_window_v2.py"
    
    if not main_window_path.exists():
        print(f"[ERROR] File not found: {main_window_path}")
        return False
    
    print("=" * 70)
    print("COHERENCE ANALYSIS TAB - AUTO-PATCH")
    print("=" * 70)
    
    # Backup original file
    backup_path = backup_file(main_window_path)
    
    # Read file
    print(f"[READING] {main_window_path.name}")
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = content.count('\n')
    print(f"          Lines: {original_lines}")
    
    # Check if already patched
    if '"Coherence Analysis"' in content or '_build_coherence_analysis_page' in content:
        print("\n[WARNING] File appears to already be patched!")
        print("          Found: Coherence Analysis references")
        response = input("\n          Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("[CANCELLED] Patch cancelled")
            return False
    
    print("\n[PATCHING] Applying changes...")
    
    # PATCH 1: Update NAV_ITEMS
    print("\n[1/3] Adding to NAV_ITEMS...")
    old_nav = '''    NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("📄", "Paper Scanner"),
        ("🔗", "Auto-Linker"),
        ("📚", "Definitions"),
        ("📊", "Data Aggregation"),
        ("🔗", "Research Links"),
        ("📝", "Footnotes & Templates"),
        ("🧠", "Semantic Dashboard"),
        ("🏷️", "Tag Manager"),
        ("🗄️", "Database"),
        ("⚙️", "Settings"),
    ]'''
    
    new_nav = '''    NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("📄", "Paper Scanner"),
        ("🔗", "Auto-Linker"),
        ("📚", "Definitions"),
        ("📊", "Data Aggregation"),
        ("🔗", "Research Links"),
        ("📝", "Footnotes & Templates"),
        ("🧠", "Semantic Dashboard"),
        ("📈", "Coherence Analysis"),
        ("🏷️", "Tag Manager"),
        ("🗄️", "Database"),
        ("⚙️", "Settings"),
    ]'''
    
    if old_nav in content:
        content = content.replace(old_nav, new_nav)
        print("      [OK] NAV_ITEMS updated")
    else:
        print("      [WARNING] Could not find exact NAV_ITEMS match")
    
    # PATCH 2: Update page build section
    print("\n[2/3] Adding to page build section...")
    old_build = '''        self._build_dashboard_page()      # 0 - Dashboard
        self._build_paper_scanner_page()  # 1 - Paper Scanner
        self._build_linker_page()         # 2 - Auto-Linker
        self._build_definitions_page()    # 3 - Definitions
        self._build_aggregation_page()    # 4 - Data Aggregation
        self._build_research_links_page() # 5 - Research Links
        self._build_footnotes_page()      # 6 - Footnotes & Templates
        self._build_semantic_dashboard()  # 7 - Semantic Dashboard
        self._build_tag_manager_page()    # 8 - Tag Manager
        self._build_database_page()       # 9 - Database
        self._build_settings_page()       # 10 - Settings'''
    
    new_build = '''        self._build_dashboard_page()          # 0 - Dashboard
        self._build_paper_scanner_page()      # 1 - Paper Scanner
        self._build_linker_page()             # 2 - Auto-Linker
        self._build_definitions_page()        # 3 - Definitions
        self._build_aggregation_page()        # 4 - Data Aggregation
        self._build_research_links_page()     # 5 - Research Links
        self._build_footnotes_page()          # 6 - Footnotes & Templates
        self._build_semantic_dashboard()      # 7 - Semantic Dashboard
        self._build_coherence_analysis_page() # 8 - Coherence Analysis
        self._build_tag_manager_page()        # 9 - Tag Manager
        self._build_database_page()           # 10 - Database
        self._build_settings_page()           # 11 - Settings'''
    
    if old_build in content:
        content = content.replace(old_build, new_build)
        print("      [OK] Page build section updated")
    else:
        print("      [WARNING] Could not find exact build section match")
    
    # PATCH 3: Add new methods at end
    print("\n[3/3] Adding new methods...")
    
    # Read the method implementations from patch file
    patch_methods = '''
    def _build_coherence_analysis_page(self):
        """Build the Coherence Analysis page with CDCM dashboard."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page header
        header = QLabel("📈 Coherence Analysis")
        header.setStyleSheet(f"""
            font-size: 24pt;
            font-weight: bold;
            color: {COLORS['text_primary']};
            padding-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Cross-Domain Coherence Metric (CDCM) analysis for evaluating theoretical frameworks "
            "against physical, mathematical, and theological constraints."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt; padding-bottom: 20px;")
        layout.addWidget(desc)
        
        # === CDCM Dashboard Section ===
        cdcm_group = QGroupBox("CDCM Dashboard Generator")
        cdcm_layout = QVBoxLayout(cdcm_group)
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("CDCM Excel File:"))
        
        self.cdcm_file_edit = QLineEdit()
        self.cdcm_file_edit.setPlaceholderText("Select CDCM.xlsx file...")
        self.cdcm_file_edit.setText("O:/Theophysics_Backend/CDCM.xlsx")
        file_layout.addWidget(self.cdcm_file_edit)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_cdcm_file)
        file_layout.addWidget(browse_btn)
        
        cdcm_layout.addLayout(file_layout)
        
        # Framework selection
        framework_layout = QHBoxLayout()
        framework_layout.addWidget(QLabel("Framework:"))
        
        self.framework_combo = QComboBox()
        self.framework_combo.addItems([
            "Primary",
            "String Theory",
            "Loop Quantum Gravity",
            "M-Theory",
            "Quantum Mechanics",
            "General Relativity"
        ])
        framework_layout.addWidget(self.framework_combo)
        framework_layout.addStretch()
        cdcm_layout.addLayout(framework_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        load_btn = QPushButton("📂 Load CDCM Data")
        load_btn.setProperty("class", "primary")
        load_btn.setMinimumHeight(40)
        load_btn.clicked.connect(self._load_cdcm_data)
        btn_layout.addWidget(load_btn)
        
        generate_btn = QPushButton("📊 Generate Dashboard")
        generate_btn.setProperty("class", "success")
        generate_btn.setMinimumHeight(40)
        generate_btn.clicked.connect(self._generate_cdcm_dashboard)
        btn_layout.addWidget(generate_btn)
        
        export_png_btn = QPushButton("📸 Export PNG")
        export_png_btn.setMinimumHeight(40)
        export_png_btn.clicked.connect(self._export_cdcm_png)
        btn_layout.addWidget(export_png_btn)
        
        cdcm_layout.addLayout(btn_layout)
        
        # Status log
        self.cdcm_log = QTextEdit()
        self.cdcm_log.setReadOnly(True)
        self.cdcm_log.setMaximumHeight(200)
        self.cdcm_log.setPlaceholderText("CDCM operations will be logged here...")
        cdcm_layout.addWidget(self.cdcm_log)
        
        layout.addWidget(cdcm_group)
        
        # === Statistics Section ===
        stats_group = QGroupBox("Current Analysis Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.cdcm_stats_labels = {}
        stats_items = [
            ("Frameworks Loaded:", "frameworks"),
            ("Metrics Calculated:", "metrics"),
            ("Coherence Score:", "coherence"),
            ("Violation Count:", "violations"),
        ]
        
        for row, (label, key) in enumerate(stats_items):
            stats_layout.addWidget(QLabel(label), row, 0)
            value_label = QLabel("--")
            value_label.setStyleSheet(f"color: {COLORS['accent_cyan']}; font-weight: bold;")
            stats_layout.addWidget(value_label, row, 1)
            self.cdcm_stats_labels[key] = value_label
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        scroll.setWidget(page)
        self.page_stack.addWidget(scroll)
        
        # Store references
        self.cdcm_analyzer = None
        self.cdcm_last_html = None

    def _browse_cdcm_file(self):
        """Browse for CDCM Excel file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select CDCM Excel File",
            "O:/Theophysics_Backend",
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        if filename:
            self.cdcm_file_edit.setText(filename)

    def _load_cdcm_data(self):
        """Load CDCM data from Excel file."""
        from pathlib import Path
        from core.coherence.cdcm_analyzer import CDCMAnalyzer
        
        filepath = Path(self.cdcm_file_edit.text())
        
        if not filepath.exists():
            self.cdcm_log.append(f"[ERROR] File not found: {filepath}")
            return
        
        try:
            self.cdcm_log.append(f"[LOADING] {filepath.name}")
            self.cdcm_analyzer = CDCMAnalyzer()
            self.cdcm_analyzer.load(filepath)
            
            # Update stats
            frameworks = len(self.cdcm_analyzer.frameworks)
            self.cdcm_stats_labels["frameworks"].setText(str(frameworks))
            self.cdcm_stats_labels["metrics"].setText("26")
            
            self.cdcm_log.append(f"[OK] Loaded {frameworks} frameworks")
            self.cdcm_log.append(f"[OK] Ready to generate dashboard")
            
        except Exception as e:
            self.cdcm_log.append(f"[ERROR] Loading failed: {e}")

    def _generate_cdcm_dashboard(self):
        """Generate HTML dashboard and open in browser."""
        from pathlib import Path
        from core.coherence.html_generator import CDCMDashboardGenerator
        import webbrowser
        
        if not self.cdcm_analyzer:
            self.cdcm_log.append("[ERROR] Please load CDCM data first")
            return
        
        try:
            framework = self.framework_combo.currentText()
            self.cdcm_log.append(f"[GENERATING] Dashboard for {framework}...")
            
            output_dir = Path("O:/Theophysics_Backend/dashboards")
            output_dir.mkdir(exist_ok=True)
            
            generator = CDCMDashboardGenerator()
            html_path = generator.generate_framework_dashboard(
                self.cdcm_analyzer,
                framework,
                output_dir
            )
            
            self.cdcm_last_html = html_path
            
            self.cdcm_log.append(f"[OK] Dashboard saved: {html_path.name}")
            self.cdcm_log.append(f"[OPENING] Browser...")
            
            webbrowser.open(html_path.as_uri())
            
            # Update stats (if metrics available)
            if hasattr(self.cdcm_analyzer, 'get_framework_metrics'):
                metrics = self.cdcm_analyzer.get_framework_metrics(framework)
                if metrics:
                    coherence = metrics.get('coherence_index', 0)
                    violations = metrics.get('total_violations', 0)
                    self.cdcm_stats_labels["coherence"].setText(f"{coherence:.2f}")
                    self.cdcm_stats_labels["violations"].setText(str(violations))
            
        except Exception as e:
            self.cdcm_log.append(f"[ERROR] Generation failed: {e}")

    def _export_cdcm_png(self):
        """Export last dashboard to PNG."""
        from core.coherence.screenshot_exporter import export_dashboard_png
        
        if not self.cdcm_last_html:
            self.cdcm_log.append("[ERROR] Please generate a dashboard first")
            return
        
        try:
            self.cdcm_log.append("[CAPTURING] PNG screenshot...")
            
            framework = self.framework_combo.currentText()
            output_dir = self.cdcm_last_html.parent / "images"
            
            png_path = export_dashboard_png(
                self.cdcm_last_html,
                output_dir,
                filename_prefix=framework.replace(" ", "_"),
                chart_type="dashboard"
            )
            
            if png_path:
                self.cdcm_log.append(f"[OK] PNG saved: {png_path.name}")
                self.cdcm_log.append(f"[OK] Media copy: O:/00_MEDIA/Dashboards/")
            else:
                self.cdcm_log.append("[ERROR] PNG export failed (check Playwright installation)")
                
        except Exception as e:
            self.cdcm_log.append(f"[ERROR] Export failed: {e}")
'''
    
    # Add methods before the last line
    content = content.rstrip() + patch_methods + '\n'
    print("      [OK] Methods added")
    
    # Write patched file
    print(f"\n[SAVING] Writing patched file...")
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_lines = content.count('\n')
    added_lines = new_lines - original_lines
    
    print(f"         Original: {original_lines} lines")
    print(f"         Patched:  {new_lines} lines")
    print(f"         Added:    +{added_lines} lines")
    
    print("\n" + "=" * 70)
    print("[COMPLETE] PATCH APPLIED SUCCESSFULLY!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart the Python application")
    print("2. Look for 'Coherence Analysis' in the sidebar")
    print("3. Click it to access CDCM dashboard")
    print("\nIf something went wrong:")
    print(f"   Restore from: {backup_path.name}")
    
    return True


if __name__ == "__main__":
    try:
        success = apply_patch()
        if success:
            input("\nPress Enter to close...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
