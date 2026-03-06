"""
Data Aggregation Tab
UI for aggregating data from all Obsidian plugins and exporting to PostgreSQL.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QTableWidget, QTableWidgetItem, QGroupBox,
    QCheckBox, QProgressBar, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
import json

from core.plugin_data_aggregator import PluginDataAggregator


class AggregationWorker(QThread):
    """Worker thread for aggregation operations."""
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, aggregator: PluginDataAggregator):
        super().__init__()
        self.aggregator = aggregator
    
    def run(self):
        try:
            self.progress.emit("Scanning plugins...")
            results = self.aggregator.scan_all_plugins()
            
            self.progress.emit("Aggregating data...")
            postgres_data = self.aggregator.aggregate_to_postgres_format(
                results["aggregated"]
            )
            
            self.progress.emit("Saving aggregated data...")
            output_file = self.aggregator.save_aggregated_data(results)
            
            results["output_file"] = str(output_file)
            results["postgres_data"] = postgres_data
            
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class DataAggregationTab(QWidget):
    """Tab for data aggregation and PostgreSQL export."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aggregator = None
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Data Aggregation & PostgreSQL Export")
        header.setStyleSheet("font-size: 18pt; font-weight: bold; margin: 10px;")
        layout.addWidget(header)
        
        # Plugin Selection
        plugin_group = QGroupBox("Plugin Sources")
        plugin_layout = QVBoxLayout()
        
        self.plugin_checkboxes = {}
        plugins = [
            ("Word Ontology", "word_ontology", r"D:\Word-ontology"),
            ("Module Notes", "module_notes", r"D:\Obsidian-Plugin-Module-Notes"),
            ("Link Tag Plugin", "link_tag", r"D:\Obsidian-link-tag-plugin"),
            ("Tags Analytics", "tags_analytics", r"D:\Obsidian-Tags-Data-Analytics")
        ]
        
        for name, plugin_id, path in plugins:
            checkbox = QCheckBox(f"{name} ({path})")
            checkbox.setChecked(True)
            checkbox.setEnabled(Path(path).exists())
            self.plugin_checkboxes[plugin_id] = checkbox
            plugin_layout.addWidget(checkbox)
        
        plugin_group.setLayout(plugin_layout)
        layout.addWidget(plugin_group)
        
        # Aggregation Target
        target_group = QGroupBox("Aggregation Target")
        target_layout = QVBoxLayout()
        
        target_label = QLabel("Target Folder:")
        target_layout.addWidget(target_label)
        
        target_input = QLineEdit(r"D:\Obsidian-Theophysics-research")
        target_input.setPlaceholderText("Path to aggregation target folder")
        target_layout.addWidget(target_input)
        self.target_input = target_input
        
        target_layout.addWidget(QLabel("This folder will contain all aggregated data"))
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)
        
        # PostgreSQL Connection
        postgres_group = QGroupBox("PostgreSQL Connection")
        postgres_layout = QVBoxLayout()
        
        postgres_label = QLabel("Connection String:")
        postgres_layout.addWidget(postgres_label)
        
        postgres_input = QLineEdit("postgresql://postgres:Moss9pep28$@192.168.1.93:5432/theophysics")
        postgres_input.setEchoMode(QLineEdit.Password)
        postgres_layout.addWidget(postgres_input)
        self.postgres_input = postgres_input
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_postgres_connection)
        postgres_layout.addWidget(test_btn)
        
        postgres_group.setLayout(postgres_layout)
        layout.addWidget(postgres_group)
        
        # Actions
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        
        scan_btn = QPushButton("Scan All Plugins")
        scan_btn.clicked.connect(self.scan_plugins)
        action_layout.addWidget(scan_btn)
        
        aggregate_btn = QPushButton("Aggregate Data")
        aggregate_btn.clicked.connect(self.aggregate_data)
        action_layout.addWidget(aggregate_btn)
        
        export_btn = QPushButton("Export to PostgreSQL")
        export_btn.clicked.connect(self.export_to_postgres)
        action_layout.addWidget(export_btn)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Plugin", "Status", "Data Count"])
        results_layout.addWidget(self.results_table)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
    
    def test_postgres_connection(self):
        """Test PostgreSQL connection."""
        connection_string = self.postgres_input.text()
        try:
            import psycopg2
            conn_str = connection_string.replace("postgresql://", "")
            user_pass, host_db = conn_str.split("@")
            user, password = user_pass.split(":")
            host, port_db = host_db.split(":")
            port, database = port_db.split("/")
            
            conn = psycopg2.connect(
                host=host,
                port=int(port),
                database=database,
                user=user,
                password=password
            )
            conn.close()
            
            QMessageBox.information(self, "Success", "PostgreSQL connection successful!")
        except ImportError:
            QMessageBox.warning(self, "Error", "psycopg2 not installed.\nInstall with: pip install psycopg2-binary")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed:\n{str(e)}")
    
    def scan_plugins(self):
        """Scan all enabled plugins."""
        target_path = Path(self.target_input.text())
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
        
        self.aggregator = PluginDataAggregator(target_path)
        
        # Update enabled plugins
        for plugin_id, checkbox in self.plugin_checkboxes.items():
            self.aggregator.plugins[plugin_id].enabled = checkbox.isChecked()
        
        self.worker = AggregationWorker(self.aggregator)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_aggregation_finished)
        self.worker.error.connect(self.on_aggregation_error)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.worker.start()
    
    def aggregate_data(self):
        """Aggregate data from all plugins."""
        if not self.aggregator:
            self.scan_plugins()
        else:
            self.scan_plugins()  # Re-scan and aggregate
    
    def export_to_postgres(self):
        """Export aggregated data to PostgreSQL."""
        if not self.aggregator:
            QMessageBox.warning(self, "Warning", "Please scan plugins first.")
            return
        
        connection_string = self.postgres_input.text()
        if not connection_string:
            QMessageBox.warning(self, "Warning", "Please enter PostgreSQL connection string.")
            return
        
        # Get last aggregated data
        # In real implementation, would load from saved file
        QMessageBox.information(
            self,
            "Export",
            "PostgreSQL export functionality will be implemented.\n"
            "This will write all aggregated data to the theophysics database."
        )
    
    def update_progress(self, message: str):
        """Update progress message."""
        self.results_text.append(message)
    
    def on_aggregation_finished(self, results: dict):
        """Handle aggregation completion."""
        self.progress_bar.setVisible(False)
        
        # Update results table
        self.results_table.setRowCount(len(results.get("plugins", {})))
        row = 0
        for plugin_id, plugin_info in results.get("plugins", {}).items():
            self.results_table.setItem(row, 0, QTableWidgetItem(plugin_id))
            self.results_table.setItem(row, 1, QTableWidgetItem(plugin_info.get("status", "unknown")))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(plugin_info.get("data_count", 0))))
            row += 1
        
        # Show summary
        summary = f"""
Aggregation Complete!

Plugins Scanned: {len(results.get("plugins", {}))}
Output File: {results.get("output_file", "N/A")}

Data Summary:
- Axioms: {len(results.get("aggregated", {}).get("axioms", []))}
- Claims: {len(results.get("aggregated", {}).get("claims", []))}
- Evidence: {len(results.get("aggregated", {}).get("evidence", []))}
- Definitions: {len(results.get("aggregated", {}).get("definitions", []))}
- Tags: {len(results.get("aggregated", {}).get("tags", []))}
        """
        self.results_text.append(summary)
    
    def on_aggregation_error(self, error: str):
        """Handle aggregation error."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Aggregation failed:\n{error}")

