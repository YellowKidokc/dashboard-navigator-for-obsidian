"""
Coherence Analysis Tab - CDCM System Integration
Qt interface for loading Excel, analyzing frameworks, and comparing theories

Includes:
- Dashboard generation with signature metrics (UTDGS, Fruits of the Spirit)
- Theory comparison (Theophysics vs Copenhagen, Many-Worlds, GRW, Penrose, IIT)
- Chi time series computation (Pi, Lambda, A composites)
- Full report generation
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QProgressBar, QListWidget,
    QFileDialog, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QListWidgetItem, QSplitter, QTabWidget,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

from .base import BaseTab


class LoadCDCMThread(QThread):
    """Background thread for loading CDCM Excel files."""
    
    progress = Signal(str)  # status message
    finished = Signal(object)  # analyzer object
    error = Signal(str)
    
    def __init__(self, excel_path: Path):
        super().__init__()
        self.excel_path = excel_path
    
    def run(self):
        """Load the CDCM workbook."""
        try:
            from core.coherence.cdcm_analyzer import CDCMAnalyzer
            
            self.progress.emit("Loading Excel workbook...")
            analyzer = CDCMAnalyzer(self.excel_path)
            
            self.progress.emit("Parsing constraint matrix...")
            if not analyzer.load():
                self.error.emit("Failed to load workbook")
                return
            
            self.progress.emit(f"Loaded {len(analyzer.frameworks)} frameworks")
            self.finished.emit(analyzer)
            
        except Exception as e:
            self.error.emit(f"Error loading CDCM: {str(e)}")


class GenerateDashboardThread(QThread):
    """Background thread for generating HTML dashboards."""

    progress = Signal(str)
    finished = Signal(str)  # output path
    error = Signal(str)

    def __init__(self, analyzer, framework_name: str, output_dir: Path):
        super().__init__()
        self.analyzer = analyzer
        self.framework_name = framework_name
        self.output_dir = output_dir

    def run(self):
        """Generate dashboard."""
        try:
            from core.coherence.html_generator import generate_dashboard

            self.progress.emit(f"Generating dashboard for {self.framework_name}...")
            output_path = generate_dashboard(self.analyzer, self.framework_name, self.output_dir)

            self.finished.emit(str(output_path))

        except Exception as e:
            self.error.emit(f"Error generating dashboard: {str(e)}")


class GenerateFullReportThread(QThread):
    """Background thread for generating full Theophysics report with signature metrics."""

    progress = Signal(str)
    finished = Signal(dict)  # results dict with scores and paths
    error = Signal(str)

    def __init__(self, base_path: Path, axioms_path: Path, output_dir: Path):
        super().__init__()
        self.base_path = base_path
        self.axioms_path = axioms_path
        self.output_dir = output_dir

    def run(self):
        """Generate full report with signature metrics."""
        try:
            # Add parent directory to path for imports
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "Global_Analytics"))

            from dashboard_generator import DashboardGenerator

            self.progress.emit("Initializing dashboard generator...")
            generator = DashboardGenerator(self.base_path, self.axioms_path)

            self.progress.emit("Scanning for dashboards...")
            count = generator.scan_all()

            self.progress.emit(f"Found {count} dashboards. Calculating metrics...")

            # Generate all outputs
            self.progress.emit("Generating report files...")
            outputs = generator.output_all_formats(self.output_dir)

            # Package results
            results = {
                'dashboard_count': count,
                'utdgs_score': generator.utdgs_score.total_score if generator.utdgs_score else 0,
                'utdgs_grade': generator.utdgs_score.grade if generator.utdgs_score else 'N/A',
                'utdgs_components': {
                    'objection_anticipation': generator.utdgs_score.objection_anticipation if generator.utdgs_score else 0,
                    'response_strength': generator.utdgs_score.response_strength if generator.utdgs_score else 0,
                    'evidence_depth': generator.utdgs_score.evidence_depth if generator.utdgs_score else 0,
                    'chain_completeness': generator.utdgs_score.chain_completeness if generator.utdgs_score else 0,
                    'width_adequacy': generator.utdgs_score.width_adequacy if generator.utdgs_score else 0,
                },
                'fruits_score': generator.fruits_score.total_score if generator.fruits_score else 0,
                'fruits_individual': generator.fruits_score.to_dict() if generator.fruits_score else {},
                'theory_comparisons': [
                    {
                        'name': tc.name,
                        'score': tc.score,
                        'weaknesses': tc.key_weaknesses,
                        'advantage': tc.theophysics_advantage
                    }
                    for tc in generator.THEORY_COMPARISONS
                ],
                'output_paths': {k: str(v) for k, v in outputs.items()},
                'categories': {k: len(v) for k, v in generator.categories.items()},
            }

            self.progress.emit("Report generation complete!")
            self.finished.emit(results)

        except Exception as e:
            import traceback
            self.error.emit(f"Error generating report: {str(e)}\n{traceback.format_exc()}")


class CoherenceAnalysisTab(BaseTab):
    """Tab for CDCM (Cross-Domain Coherence Metric) analysis."""

    # Default paths
    DEFAULT_BASE_PATH = Path(r"O:\Theophysics_Backend\Python_Backend\Global_Analytics")
    DEFAULT_AXIOMS_PATH = Path(r"O:\_THEO\AXIOMS_MASTER\Axioms")

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.analyzer = None
        self.load_thread = None
        self.dashboard_thread = None
        self.report_thread = None
        self.last_results = None
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Coherence Analysis - CDCM System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Cross-Domain Coherence Metric: Evaluate frameworks, compute signature metrics (UTDGS, Fruits), "
            "run theory comparisons, and generate comprehensive reports."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Create tab widget for different sections
        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs, 1)

        # Tab 1: Full Report Generation
        self._build_report_tab()

        # Tab 2: CDCM Framework Analysis (existing)
        self._build_cdcm_tab()

        # Status bar at bottom
        self.status_label = QLabel("Ready. Generate a full report or load a CDCM Excel file to begin.")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)

    def _build_report_tab(self):
        """Build the Full Report tab with signature metrics."""
        report_widget = QWidget()
        report_layout = QVBoxLayout(report_widget)
        report_layout.setContentsMargins(5, 5, 5, 5)

        # Top: Generate button and status
        top_group = QGroupBox("Generate Full Theophysics Report")
        top_layout = QVBoxLayout()

        btn_row = QHBoxLayout()
        self.generate_report_btn = QPushButton("Generate Report with Signature Metrics")
        self.generate_report_btn.setMinimumHeight(40)
        self.generate_report_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.generate_report_btn.clicked.connect(self._generate_full_report)
        btn_row.addWidget(self.generate_report_btn)

        self.open_output_btn = QPushButton("Open Output Folder")
        self.open_output_btn.setEnabled(False)
        self.open_output_btn.clicked.connect(self._open_output_folder)
        btn_row.addWidget(self.open_output_btn)
        top_layout.addLayout(btn_row)

        self.report_progress = QLabel("")
        self.report_progress.setStyleSheet("color: #58a6ff; font-size: 11px;")
        top_layout.addWidget(self.report_progress)

        top_group.setLayout(top_layout)
        report_layout.addWidget(top_group)

        # Main content: splitter with metrics on left, details on right
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Signature Metrics
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # UTDGS Score Card
        utdgs_group = QGroupBox("UTDGS Score (Universal Theory Defense Grading System)")
        utdgs_layout = QVBoxLayout()

        self.utdgs_total = QLabel("--/100")
        self.utdgs_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #58a6ff;")
        utdgs_layout.addWidget(self.utdgs_total)

        self.utdgs_grade = QLabel("Grade: --")
        self.utdgs_grade.setStyleSheet("font-size: 14px;")
        utdgs_layout.addWidget(self.utdgs_grade)

        # UTDGS components table
        self.utdgs_table = QTableWidget(5, 2)
        self.utdgs_table.setHorizontalHeaderLabels(["Component", "Score"])
        self.utdgs_table.horizontalHeader().setStretchLastSection(True)
        self.utdgs_table.setMaximumHeight(160)
        utdgs_layout.addWidget(self.utdgs_table)

        utdgs_group.setLayout(utdgs_layout)
        left_layout.addWidget(utdgs_group)

        # Fruits Score Card
        fruits_group = QGroupBox("Structural Coherence Invariants (12 Fruits)")
        fruits_layout = QVBoxLayout()

        self.fruits_total = QLabel("--/12.00")
        self.fruits_total.setStyleSheet("font-size: 24px; font-weight: bold; color: #3fb950;")
        fruits_layout.addWidget(self.fruits_total)

        # Fruits table
        self.fruits_table = QTableWidget(12, 2)
        self.fruits_table.setHorizontalHeaderLabels(["Fruit", "Score"])
        self.fruits_table.horizontalHeader().setStretchLastSection(True)
        fruits_layout.addWidget(self.fruits_table)

        fruits_group.setLayout(fruits_layout)
        left_layout.addWidget(fruits_group)

        splitter.addWidget(left_widget)

        # Right side: Theory Comparison
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        theory_group = QGroupBox("Theory Comparison: Theophysics vs Alternatives")
        theory_layout = QVBoxLayout()

        # Theophysics score header
        theophysics_header = QLabel("Theophysics: 5/5 (All problems addressed)")
        theophysics_header.setStyleSheet("font-size: 14px; font-weight: bold; color: #3fb950; margin-bottom: 10px;")
        theory_layout.addWidget(theophysics_header)

        # Theory comparison table
        self.theory_table = QTableWidget(5, 3)
        self.theory_table.setHorizontalHeaderLabels(["Theory", "Score", "Theophysics Advantage"])
        self.theory_table.horizontalHeader().setStretchLastSection(True)
        self.theory_table.setAlternatingRowColors(True)
        theory_layout.addWidget(self.theory_table)

        theory_group.setLayout(theory_layout)
        right_layout.addWidget(theory_group)

        # Dashboard summary
        dashboard_group = QGroupBox("Dashboard Inventory")
        dashboard_layout = QVBoxLayout()

        self.dashboard_count_label = QLabel("Total Dashboards: --")
        self.dashboard_count_label.setStyleSheet("font-size: 14px;")
        dashboard_layout.addWidget(self.dashboard_count_label)

        self.dashboard_details = QTextEdit()
        self.dashboard_details.setReadOnly(True)
        self.dashboard_details.setMaximumHeight(150)
        self.dashboard_details.setStyleSheet("font-family: Consolas, monospace; font-size: 10px;")
        dashboard_layout.addWidget(self.dashboard_details)

        dashboard_group.setLayout(dashboard_layout)
        right_layout.addWidget(dashboard_group)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        report_layout.addWidget(splitter, 1)

        self.main_tabs.addTab(report_widget, "Full Report")

    def _build_cdcm_tab(self):
        """Build the CDCM Framework Analysis tab (existing functionality)."""
        cdcm_widget = QWidget()
        cdcm_layout = QVBoxLayout(cdcm_widget)
        cdcm_layout.setContentsMargins(5, 5, 5, 5)

        # Excel Loading Section
        excel_group = QGroupBox("1. Load CDCM Excel File")
        excel_layout = QVBoxLayout()

        excel_path_layout = QHBoxLayout()
        self.excel_path_label = QLabel("No file loaded")
        self.excel_path_label.setStyleSheet("color: #999;")
        excel_path_layout.addWidget(self.excel_path_label, 1)

        self.browse_excel_btn = QPushButton("Browse CDCM.xlsx")
        self.browse_excel_btn.clicked.connect(self._browse_excel)
        excel_path_layout.addWidget(self.browse_excel_btn)

        self.load_excel_btn = QPushButton("Load & Analyze")
        self.load_excel_btn.setEnabled(False)
        self.load_excel_btn.clicked.connect(self._load_excel)
        excel_path_layout.addWidget(self.load_excel_btn)

        excel_layout.addLayout(excel_path_layout)

        self.load_status = QLabel("")
        self.load_status.setStyleSheet("color: #58a6ff; font-size: 12px;")
        excel_layout.addWidget(self.load_status)

        excel_group.setLayout(excel_layout)
        cdcm_layout.addWidget(excel_group)

        # Main content splitter
        cdcm_splitter = QSplitter(Qt.Horizontal)

        # Left: Framework Selection
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        frameworks_group = QGroupBox("2. Select Frameworks")
        frameworks_layout = QVBoxLayout()

        self.frameworks_list = QListWidget()
        self.frameworks_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.frameworks_list.itemSelectionChanged.connect(self._on_framework_selection_changed)
        frameworks_layout.addWidget(self.frameworks_list)

        btn_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_frameworks)
        btn_layout.addWidget(self.select_all_btn)

        self.clear_selection_btn = QPushButton("Clear")
        self.clear_selection_btn.clicked.connect(self._clear_framework_selection)
        btn_layout.addWidget(self.clear_selection_btn)

        frameworks_layout.addLayout(btn_layout)
        frameworks_group.setLayout(frameworks_layout)
        left_layout.addWidget(frameworks_group)

        cdcm_splitter.addWidget(left_widget)

        # Right: Metrics Display
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        metrics_group = QGroupBox("3. Framework Metrics")
        metrics_layout = QVBoxLayout()

        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setAlternatingRowColors(True)
        metrics_layout.addWidget(self.metrics_table)

        metrics_group.setLayout(metrics_layout)
        right_layout.addWidget(metrics_group)

        cdcm_splitter.addWidget(right_widget)
        cdcm_splitter.setStretchFactor(0, 1)
        cdcm_splitter.setStretchFactor(1, 2)

        cdcm_layout.addWidget(cdcm_splitter, 1)

        # Actions Section
        actions_group = QGroupBox("4. Generate Outputs")
        actions_layout = QHBoxLayout()

        self.generate_dashboard_btn = QPushButton("Generate HTML Dashboard")
        self.generate_dashboard_btn.setEnabled(False)
        self.generate_dashboard_btn.clicked.connect(self._generate_dashboard)
        actions_layout.addWidget(self.generate_dashboard_btn)

        self.compare_frameworks_btn = QPushButton("Compare Selected")
        self.compare_frameworks_btn.setEnabled(False)
        self.compare_frameworks_btn.clicked.connect(self._compare_frameworks)
        actions_layout.addWidget(self.compare_frameworks_btn)

        self.export_json_btn = QPushButton("Export to JSON")
        self.export_json_btn.setEnabled(False)
        self.export_json_btn.clicked.connect(self._export_json)
        actions_layout.addWidget(self.export_json_btn)

        actions_group.setLayout(actions_layout)
        cdcm_layout.addWidget(actions_group)

        # Add the tab
        self.main_tabs.addTab(cdcm_widget, "CDCM Analysis")
    
    def _browse_excel(self):
        """Browse for CDCM Excel file."""
        # Try to start from Backend directory
        start_dir = Path("O:/Theophysics_Backend")
        if not start_dir.exists():
            start_dir = Path.home()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CDCM Excel File",
            str(start_dir),
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        
        if file_path:
            self.excel_path_label.setText(file_path)
            self.excel_path_label.setStyleSheet("color: #58a6ff;")
            self.load_excel_btn.setEnabled(True)
    
    def _load_excel(self):
        """Load Excel file in background thread."""
        excel_path = Path(self.excel_path_label.text())
        if not excel_path.exists():
            QMessageBox.warning(self, "Error", "Excel file not found")
            return
        
        self.load_excel_btn.setEnabled(False)
        self.browse_excel_btn.setEnabled(False)
        self.load_status.setText("Loading...")
        
        self.load_thread = LoadCDCMThread(excel_path)
        self.load_thread.progress.connect(self._on_load_progress)
        self.load_thread.finished.connect(self._on_load_finished)
        self.load_thread.error.connect(self._on_load_error)
        self.load_thread.start()
    
    def _on_load_progress(self, message: str):
        """Handle load progress updates."""
        self.load_status.setText(message)
    
    def _on_load_finished(self, analyzer):
        """Handle successful load."""
        self.analyzer = analyzer
        
        # Populate frameworks list
        self.frameworks_list.clear()
        for name in analyzer.get_all_framework_names():
            self.frameworks_list.addItem(name)
        
        self.load_status.setText(f"✓ Loaded {len(analyzer.frameworks)} frameworks")
        self.load_status.setStyleSheet("color: #3fb950; font-size: 12px;")
        
        self.load_excel_btn.setEnabled(True)
        self.browse_excel_btn.setEnabled(True)
        self.generate_dashboard_btn.setEnabled(True)
        self.export_json_btn.setEnabled(True)
        
        self.status_label.setText(f"Ready. {len(analyzer.frameworks)} frameworks loaded.")
        
        # Auto-select first framework
        if self.frameworks_list.count() > 0:
            self.frameworks_list.item(0).setSelected(True)
    
    def _on_load_error(self, error_msg: str):
        """Handle load error."""
        QMessageBox.critical(self, "Load Error", error_msg)
        self.load_status.setText("✗ Failed to load")
        self.load_status.setStyleSheet("color: #f85149; font-size: 12px;")
        self.load_excel_btn.setEnabled(True)
        self.browse_excel_btn.setEnabled(True)
    
    def _on_framework_selection_changed(self):
        """Handle framework selection change."""
        selected_items = self.frameworks_list.selectedItems()
        
        if not selected_items or not self.analyzer:
            self.metrics_table.setRowCount(0)
            self.compare_frameworks_btn.setEnabled(False)
            return
        
        # Enable compare if multiple selected
        self.compare_frameworks_btn.setEnabled(len(selected_items) > 1)
        
        # Show metrics for first selected framework
        framework_name = selected_items[0].text()
        framework = self.analyzer.get_framework(framework_name)
        
        if framework:
            self._display_framework_metrics(framework)
    
    def _display_framework_metrics(self, framework):
        """Display framework metrics in table."""
        metrics = framework.get_all_metrics()
        
        self.metrics_table.setRowCount(len(metrics))
        
        row = 0
        for key, value in metrics.items():
            # Format key
            label = key.replace('_', ' ').title()
            
            # Format value
            if isinstance(value, float):
                if 'ratio' in key or 'rate' in key:
                    formatted = f"{value:.1%}" if value <= 1 else f"{value:.1f}%"
                else:
                    formatted = f"{value:.2f}"
            else:
                formatted = str(value)
            
            self.metrics_table.setItem(row, 0, QTableWidgetItem(label))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(formatted))
            
            row += 1
        
        self.metrics_table.resizeColumnsToContents()
    
    def _select_all_frameworks(self):
        """Select all frameworks."""
        for i in range(self.frameworks_list.count()):
            self.frameworks_list.item(i).setSelected(True)
    
    def _clear_framework_selection(self):
        """Clear framework selection."""
        self.frameworks_list.clearSelection()
    
    def _generate_dashboard(self):
        """Generate HTML dashboard for selected framework."""
        if not self.analyzer:
            return
        
        selected_items = self.frameworks_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a framework first")
            return
        
        framework_name = selected_items[0].text()
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if not output_dir:
            return
        
        self.generate_dashboard_btn.setEnabled(False)
        self.status_label.setText(f"Generating dashboard for {framework_name}...")
        
        self.dashboard_thread = GenerateDashboardThread(
            self.analyzer,
            framework_name,
            Path(output_dir)
        )
        self.dashboard_thread.progress.connect(self._on_dashboard_progress)
        self.dashboard_thread.finished.connect(self._on_dashboard_finished)
        self.dashboard_thread.error.connect(self._on_dashboard_error)
        self.dashboard_thread.start()
    
    def _on_dashboard_progress(self, message: str):
        """Handle dashboard generation progress."""
        self.status_label.setText(message)
    
    def _on_dashboard_finished(self, output_path: str):
        """Handle dashboard generation completion."""
        self.generate_dashboard_btn.setEnabled(True)
        self.status_label.setText(f"✓ Dashboard generated: {output_path}")
        
        # Ask if user wants to open it
        reply = QMessageBox.question(
            self,
            "Dashboard Generated",
            f"Dashboard saved to:\n{output_path}\n\nOpen in browser?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(f"file:///{output_path}")
    
    def _on_dashboard_error(self, error_msg: str):
        """Handle dashboard generation error."""
        self.generate_dashboard_btn.setEnabled(True)
        QMessageBox.critical(self, "Generation Error", error_msg)
        self.status_label.setText("✗ Dashboard generation failed")
    
    def _compare_frameworks(self):
        """Generate comparison dashboard for selected frameworks."""
        if not self.analyzer:
            return
        
        selected_items = self.frameworks_list.selectedItems()
        if len(selected_items) < 2:
            QMessageBox.warning(self, "Insufficient Selection", "Select at least 2 frameworks to compare")
            return
        
        framework_names = [item.text() for item in selected_items]
        
        # Ask for output directory
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(Path.home())
        )
        
        if not output_dir:
            return
        
        try:
            from core.coherence.html_generator import CDCMDashboardGenerator
            
            comparison_data = self.analyzer.compare_frameworks(framework_names)
            
            generator = CDCMDashboardGenerator()
            output_path = Path(output_dir) / "framework_comparison.html"
            generator.generate_comparison_dashboard(comparison_data, output_path)
            
            self.status_label.setText(f"✓ Comparison generated: {output_path}")
            
            # Ask if user wants to open it
            reply = QMessageBox.question(
                self,
                "Comparison Generated",
                f"Comparison saved to:\n{output_path}\n\nOpen in browser?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                import webbrowser
                webbrowser.open(f"file:///{output_path}")
        
        except Exception as e:
            QMessageBox.critical(self, "Comparison Error", f"Error generating comparison: {str(e)}")
    
    def _export_json(self):
        """Export all frameworks to JSON."""
        if not self.analyzer:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to JSON",
            str(Path.home() / "cdcm_export.json"),
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                self.analyzer.export_to_json(Path(file_path))
                self.status_label.setText(f"Exported to {file_path}")
                QMessageBox.information(self, "Export Complete", f"Data exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting: {str(e)}")

    # =========================================================================
    # FULL REPORT METHODS
    # =========================================================================

    def _generate_full_report(self):
        """Generate the full Theophysics report with signature metrics."""
        self.generate_report_btn.setEnabled(False)
        self.report_progress.setText("Starting report generation...")
        self.report_progress.setStyleSheet("color: #58a6ff; font-size: 11px;")

        # Use default paths
        base_path = self.DEFAULT_BASE_PATH
        axioms_path = self.DEFAULT_AXIOMS_PATH
        output_dir = self.DEFAULT_BASE_PATH

        # Check if paths exist
        if not base_path.exists():
            QMessageBox.warning(
                self,
                "Path Not Found",
                f"Base path not found:\n{base_path}\n\nPlease verify the path exists."
            )
            self.generate_report_btn.setEnabled(True)
            self.report_progress.setText("")
            return

        self.report_thread = GenerateFullReportThread(base_path, axioms_path, output_dir)
        self.report_thread.progress.connect(self._on_report_progress)
        self.report_thread.finished.connect(self._on_report_finished)
        self.report_thread.error.connect(self._on_report_error)
        self.report_thread.start()

    def _on_report_progress(self, message: str):
        """Handle report generation progress updates."""
        self.report_progress.setText(message)
        self.status_label.setText(message)

    def _on_report_finished(self, results: dict):
        """Handle successful report generation."""
        self.last_results = results
        self.generate_report_btn.setEnabled(True)
        self.open_output_btn.setEnabled(True)

        # Update UTDGS display
        self._update_utdgs_display(results)

        # Update Fruits display
        self._update_fruits_display(results)

        # Update Theory Comparison table
        self._update_theory_table(results)

        # Update Dashboard summary
        self._update_dashboard_summary(results)

        # Update status
        self.report_progress.setText(
            f"Report complete! UTDGS: {results['utdgs_score']:.1f}/100 ({results['utdgs_grade']}), "
            f"Fruits: {results['fruits_score']:.2f}/12"
        )
        self.report_progress.setStyleSheet("color: #3fb950; font-size: 11px;")
        self.status_label.setText(
            f"Report generated: {results['dashboard_count']} dashboards scanned"
        )

    def _on_report_error(self, error_msg: str):
        """Handle report generation error."""
        self.generate_report_btn.setEnabled(True)
        self.report_progress.setText("Report generation failed")
        self.report_progress.setStyleSheet("color: #f85149; font-size: 11px;")
        QMessageBox.critical(self, "Report Error", error_msg)

    def _update_utdgs_display(self, results: dict):
        """Update the UTDGS score display."""
        score = results['utdgs_score']
        grade = results['utdgs_grade']

        # Update total score
        self.utdgs_total.setText(f"{score:.1f}/100")
        self.utdgs_grade.setText(f"Grade: {grade}")

        # Color based on grade
        if grade.startswith('A'):
            color = "#3fb950"  # Green
        elif grade.startswith('B'):
            color = "#58a6ff"  # Blue
        elif grade.startswith('C'):
            color = "#d29922"  # Yellow
        else:
            color = "#f85149"  # Red

        self.utdgs_total.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")

        # Update components table
        components = results['utdgs_components']
        component_names = [
            ("Objection Anticipation", "objection_anticipation"),
            ("Response Strength", "response_strength"),
            ("Evidence Depth", "evidence_depth"),
            ("Chain Completeness", "chain_completeness"),
            ("Width Adequacy", "width_adequacy"),
        ]

        for row, (name, key) in enumerate(component_names):
            value = components.get(key, 0)
            self.utdgs_table.setItem(row, 0, QTableWidgetItem(name))
            self.utdgs_table.setItem(row, 1, QTableWidgetItem(f"{value:.1%}"))

        self.utdgs_table.resizeColumnsToContents()

    def _update_fruits_display(self, results: dict):
        """Update the Fruits of the Spirit display."""
        total = results['fruits_score']
        self.fruits_total.setText(f"{total:.2f}/12.00")

        # Color based on score
        if total >= 9:
            color = "#3fb950"  # Green
        elif total >= 6:
            color = "#58a6ff"  # Blue
        elif total >= 3:
            color = "#d29922"  # Yellow
        else:
            color = "#f85149"  # Red

        self.fruits_total.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")

        # Update fruits table
        fruits = results['fruits_individual']
        for row, (name, value) in enumerate(fruits.items()):
            self.fruits_table.setItem(row, 0, QTableWidgetItem(name))
            self.fruits_table.setItem(row, 1, QTableWidgetItem(f"{value:.3f}"))

        self.fruits_table.resizeColumnsToContents()

    def _update_theory_table(self, results: dict):
        """Update the theory comparison table."""
        comparisons = results['theory_comparisons']

        for row, tc in enumerate(comparisons):
            self.theory_table.setItem(row, 0, QTableWidgetItem(tc['name']))
            self.theory_table.setItem(row, 1, QTableWidgetItem(tc['score']))
            self.theory_table.setItem(row, 2, QTableWidgetItem(tc['advantage']))

        self.theory_table.resizeColumnsToContents()

    def _update_dashboard_summary(self, results: dict):
        """Update the dashboard inventory summary."""
        count = results['dashboard_count']
        categories = results['categories']

        self.dashboard_count_label.setText(f"Total Dashboards: {count}")

        # Build category details
        lines = []
        for cat, num in sorted(categories.items(), key=lambda x: -x[1]):
            lines.append(f"  [{cat}] {num} dashboards")

        # Add output file paths
        lines.append("")
        lines.append("Generated Files:")
        for name, path in results['output_paths'].items():
            lines.append(f"  {name}: {path}")

        self.dashboard_details.setText("\n".join(lines))

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        import subprocess
        import os

        output_dir = self.DEFAULT_BASE_PATH
        if output_dir.exists():
            if sys.platform == 'win32':
                os.startfile(str(output_dir))
            elif sys.platform == 'darwin':
                subprocess.run(['open', str(output_dir)])
            else:
                subprocess.run(['xdg-open', str(output_dir)])
