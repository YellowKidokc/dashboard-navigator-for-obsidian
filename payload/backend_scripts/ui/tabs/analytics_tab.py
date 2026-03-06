# ui/tabs/analytics_tab.py
"""
Data Analytics Tab - Comprehensive analytics dashboard
Integrates Global Analytics Engine + Fruits of Spirit Analysis
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFileDialog, QComboBox,
    QProgressBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
import json
import sqlite3
from datetime import datetime


class AnalyticsWorker(QThread):
    """Background worker for analytics processing."""
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, folder_path, options, settings_mgr):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.options = options
        self.settings = settings_mgr
        
    def run(self):
        try:
            from engine.global_analytics_engine import GlobalAnalyticsEngine
            from engine.analytics_dashboard_generator import AnalyticsDashboardGenerator
            
            # Create output folder
            output_root = self.folder_path.parent / f"{self.folder_path.name}_ANALYTICS"
            output_root.mkdir(exist_ok=True)
            
            self.progress.emit(f"📊 Analyzing: {self.folder_path.name}")
            
            # Run global analytics
            analytics = GlobalAnalyticsEngine(
                backend_root=self.folder_path,
                output_path=output_root / "data"
            )
            
            self.progress.emit("🔍 Scanning files...")
            analytics.scan_vault(str(self.folder_path))
            
            self.progress.emit("📈 Generating dashboards...")
            dashboard_gen = AnalyticsDashboardGenerator(
                db_path=analytics.db_path,
                output_root=output_root
            )
            
            run_folder = dashboard_gen.generate_all_outputs()
            
            # Get summary stats
            conn = sqlite3.connect(analytics.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM papers")
            paper_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tags")
            tag_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM links")
            link_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM definitions")
            def_count = cursor.fetchone()[0]
            
            conn.close()
            
            # If Fruits analysis requested
            if self.options.get('fruits_analysis'):
                self.progress.emit("🍇 Running Fruits of Spirit analysis...")
                fruits_results = self._analyze_fruits()
            else:
                fruits_results = None
            
            results = {
                'output_folder': str(run_folder),
                'papers': paper_count,
                'tags': tag_count,
                'links': link_count,
                'definitions': def_count,
                'fruits': fruits_results
            }
            
            self.progress.emit("✅ Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Analytics error: {str(e)}")
    
    def _analyze_fruits(self):
        """Analyze Fruits of Spirit manifestations in axioms."""
        fruits = {
            'Love': 0, 'Joy': 0, 'Peace': 0, 'Patience': 0,
            'Kindness': 0, 'Goodness': 0, 'Faithfulness': 0,
            'Gentleness': 0, 'Self-Control': 0
        }
        
        # Scan for fruit keywords in axiom files
        for md_file in self.folder_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8').lower()
                for fruit in fruits.keys():
                    if fruit.lower() in content:
                        fruits[fruit] += 1
            except:
                continue
        
        return fruits


class AnalyticsTab(QWidget):
    """Comprehensive Data Analytics Dashboard Tab."""
    
    def __init__(self, settings_mgr, db_engine):
        super().__init__()
        self.settings = settings_mgr
        self.db = db_engine
        self.worker = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("📊 Data Analytics Dashboard")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)
        
        subtitle = QLabel("Comprehensive analytics for axioms, papers, and concepts")
        subtitle.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(subtitle)
        
        # Folder Selection
        folder_box = QGroupBox("Source Folder")
        folder_layout = QVBoxLayout(folder_box)
        
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select folder to analyze...")
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_folder)
        
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse_btn)
        folder_layout.addLayout(folder_row)
        
        # Quick presets
        preset_row = QHBoxLayout()
        preset_label = QLabel("Quick Select:")
        preset_label.setStyleSheet("color: #888;")
        
        axioms_btn = QPushButton("📚 Axioms (001-188)")
        axioms_btn.clicked.connect(lambda: self._set_preset("D:\\Canon\\01_Axioms\\_001-188"))
        
        papers_btn = QPushButton("📄 Papers")
        papers_btn.clicked.connect(lambda: self._set_preset("D:\\Canon\\01_Axioms\\_PAPERS"))
        
        topics_btn = QPushButton("🏷️ Topics")
        topics_btn.clicked.connect(lambda: self._set_preset("D:\\Canon\\01_Axioms\\_TOPICS"))
        
        preset_row.addWidget(preset_label)
        preset_row.addWidget(axioms_btn)
        preset_row.addWidget(papers_btn)
        preset_row.addWidget(topics_btn)
        preset_row.addStretch()
        
        folder_layout.addLayout(preset_row)
        layout.addWidget(folder_box)
        
        # Analysis Options
        options_box = QGroupBox("Analysis Options")
        options_layout = QVBoxLayout(options_box)
        
        self.fruits_check = QCheckBox("🍇 Include Fruits of Spirit Analysis")
        self.fruits_check.setChecked(True)
        
        self.charts_check = QCheckBox("📈 Generate Visual Charts")
        self.charts_check.setChecked(True)
        
        self.export_check = QCheckBox("💾 Export Data Files (JSON/CSV)")
        self.export_check.setChecked(True)
        
        options_layout.addWidget(self.fruits_check)
        options_layout.addWidget(self.charts_check)
        options_layout.addWidget(self.export_check)
        
        layout.addWidget(options_box)
        
        # Run Button
        run_btn = QPushButton("🚀 Run Analytics")
        run_btn.setObjectName("primaryBtn")
        run_btn.setMinimumHeight(50)
        run_btn.clicked.connect(self._run_analytics)
        layout.addWidget(run_btn)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to analyze")
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)
        
        # Results Display
        results_box = QGroupBox("Analytics Results")
        results_layout = QVBoxLayout(results_box)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMinimumHeight(200)
        self.results_text.setPlaceholderText("Results will appear here after analysis...")
        results_layout.addWidget(self.results_text)
        
        # Open output button
        self.open_output_btn = QPushButton("📂 Open Output Folder")
        self.open_output_btn.setVisible(False)
        self.open_output_btn.clicked.connect(self._open_output)
        results_layout.addWidget(self.open_output_btn)
        
        layout.addWidget(results_box)
        
        layout.addStretch()
    
    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Analyze")
        if folder:
            self.folder_edit.setText(folder)
    
    def _set_preset(self, path):
        self.folder_edit.setText(path)
    
    def _run_analytics(self):
        folder_path = self.folder_edit.text().strip()
        
        if not folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder to analyze.")
            return
        
        if not Path(folder_path).exists():
            QMessageBox.warning(self, "Invalid Path", f"Folder does not exist:\n{folder_path}")
            return
        
        # Prepare options
        options = {
            'fruits_analysis': self.fruits_check.isChecked(),
            'generate_charts': self.charts_check.isChecked(),
            'export_data': self.export_check.isChecked()
        }
        
        # Start worker
        self.worker = AnalyticsWorker(folder_path, options, self.settings)
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._show_results)
        self.worker.error.connect(self._show_error)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Starting analysis...")
        self.results_text.clear()
        self.open_output_btn.setVisible(False)
        
        self.worker.start()
    
    def _update_progress(self, message):
        self.status_label.setText(message)
        self.results_text.append(message)
    
    def _show_results(self, results):
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ Analysis complete!")
        self.status_label.setStyleSheet("color: #00d9ff;")
        
        # Display results
        output = "\n" + "="*60 + "\n"
        output += "📊 ANALYTICS SUMMARY\n"
        output += "="*60 + "\n\n"
        
        output += f"📄 Papers Analyzed: {results['papers']:,}\n"
        output += f"🏷️  Tags Found: {results['tags']:,}\n"
        output += f"🔗 Links Extracted: {results['links']:,}\n"
        output += f"📖 Definitions: {results['definitions']:,}\n\n"
        
        if results.get('fruits'):
            output += "="*60 + "\n"
            output += "🍇 FRUITS OF SPIRIT ANALYSIS\n"
            output += "="*60 + "\n\n"
            
            for fruit, count in sorted(results['fruits'].items(), key=lambda x: x[1], reverse=True):
                output += f"  {fruit:15} : {count:4} mentions\n"
            output += "\n"
        
        output += "="*60 + "\n"
        output += f"📂 Output Location:\n{results['output_folder']}\n"
        output += "="*60 + "\n"
        
        self.results_text.append(output)
        
        self.output_folder = results['output_folder']
        self.open_output_btn.setVisible(True)
    
    def _show_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Analysis failed")
        self.status_label.setStyleSheet("color: #e94560;")
        
        self.results_text.append(f"\n❌ ERROR: {error_msg}\n")
        
        QMessageBox.critical(self, "Analytics Error", f"Analysis failed:\n\n{error_msg}")
    
    def _open_output(self):
        import subprocess
        import platform
        
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', self.output_folder])
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', self.output_folder])
        else:  # Linux
            subprocess.Popen(['xdg-open', self.output_folder])
