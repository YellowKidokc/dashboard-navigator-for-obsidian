"""
Coherence Analysis Tab - CDCM System Integration
Qt interface for loading Excel, analyzing frameworks, and comparing theories
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QProgressBar, QListWidget,
    QFileDialog, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QListWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

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


class CoherenceAnalysisTab(BaseTab):
    """Tab for CDCM (Cross-Domain Coherence Metric) analysis."""
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.analyzer = None
        self.load_thread = None
        self.dashboard_thread = None
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🔬 Coherence Analysis - CDCM System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Cross-Domain Coherence Metric: Evaluate frameworks across 9 universal constraints, "
            "compute 26+ advanced metrics, and run comparative analysis."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)
        
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
        layout.addWidget(excel_group)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
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
        
        splitter.addWidget(left_widget)
        
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
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter, 1)
        
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
        layout.addWidget(actions_group)
        
        # Status bar
        self.status_label = QLabel("Ready. Load a CDCM Excel file to begin.")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        layout.addWidget(self.status_label)
    
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
                self.status_label.setText(f"✓ Exported to {file_path}")
                QMessageBox.information(self, "Export Complete", f"Data exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Error exporting: {str(e)}")
