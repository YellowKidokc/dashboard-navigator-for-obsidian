"""
Definitions V2 Tab - Mass processing with external sources and provenance
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QProgressBar, QSpinBox,
    QCheckBox, QComboBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal

from .base import BaseTab
from pathlib import Path
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.obsidian_definitions_manager import ObsidianDefinitionsManager


class ProcessingThread(QThread):
    """Background thread for processing definitions."""
    
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(dict)  # stats
    error = Signal(str)
    
    def __init__(self, vault_path: Path, max_workers: int, force_reprocess: bool):
        super().__init__()
        self.vault_path = vault_path
        self.max_workers = max_workers
        self.force_reprocess = force_reprocess
    
    def run(self):
        """Run the processing."""
        try:
            from engine.definition_processor_v2 import DefinitionProcessorV2
            
            processor = DefinitionProcessorV2(
                vault_path=self.vault_path,
                max_workers=self.max_workers
            )
            
            # Hook into progress updates
            # (In real implementation, you'd add callbacks to the processor)
            
            stats = processor.process_all_definitions(
                force_reprocess=self.force_reprocess
            )
            
            self.finished.emit(stats)
            
        except Exception as e:
            self.error.emit(str(e))


class DefinitionsV2Tab(BaseTab):
    """Tab for Definition 2.0 mass processing."""

    def __init__(self, definitions_manager: ObsidianDefinitionsManager, settings):
        super().__init__()
        self.definitions_manager = definitions_manager
        self.settings = settings
        self.processing_thread = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Definition 2.0 - Mass Processor")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Process 700+ definitions with external source acquisition, "
            "provenance tracking, and drift detection."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Configuration Group
        config_group = QGroupBox("Configuration")
        config_layout = QVBoxLayout()

        # Workers
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("CPU Cores to Use:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(32)
        self.workers_spin.setValue(8)
        self.workers_spin.setToolTip("Number of parallel workers for processing")
        workers_layout.addWidget(self.workers_spin)
        workers_layout.addStretch()
        config_layout.addLayout(workers_layout)

        # Options
        self.force_reprocess_check = QCheckBox("Force reprocess all definitions")
        self.force_reprocess_check.setToolTip("Reprocess even if already processed")
        config_layout.addWidget(self.force_reprocess_check)

        self.download_external_check = QCheckBox("Download external sources")
        self.download_external_check.setChecked(True)
        self.download_external_check.setToolTip("Download content from SEP, arXiv, Wikipedia")
        config_layout.addWidget(self.download_external_check)

        self.detect_drift_check = QCheckBox("Detect usage drift")
        self.detect_drift_check.setChecked(True)
        self.detect_drift_check.setToolTip("Check for inconsistent usage across vault")
        config_layout.addWidget(self.detect_drift_check)

        self.generate_notes_check = QCheckBox("Generate definition notes")
        self.generate_notes_check.setChecked(False)
        self.generate_notes_check.setToolTip("Create markdown files for each definition")
        config_layout.addWidget(self.generate_notes_check)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Action Buttons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Start Processing")
        self.start_btn.setStyleSheet(
            "padding: 12px; font-weight: bold; font-size: 12pt; "
            "background-color: #4CAF50; color: white;"
        )
        self.start_btn.clicked.connect(self._start_processing)
        buttons_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_processing)
        buttons_layout.addWidget(self.stop_btn)

        buttons_layout.addStretch()

        view_report_btn = QPushButton("📊 View Report")
        view_report_btn.clicked.connect(self._view_report)
        buttons_layout.addWidget(view_report_btn)

        layout.addLayout(buttons_layout)

        # Progress Group
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to process")
        self.status_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.status_label)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        # Statistics Group
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()

        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_table)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Log Output
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(200)
        self.log_output.setStyleSheet("font-family: monospace; font-size: 9pt;")
        log_layout.addWidget(self.log_output)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_output.clear)
        log_layout.addWidget(clear_log_btn)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()

    def _start_processing(self):
        """Start the processing."""
        vault_path = Path(self.settings.get("vault_path", "."))
        
        if not vault_path.exists():
            QMessageBox.warning(
                self, "Invalid Path",
                f"Vault path does not exist: {vault_path}"
            )
            return

        # Confirm
        reply = QMessageBox.question(
            self, "Confirm Processing",
            f"This will process all definitions in:\n{vault_path}\n\n"
            f"Workers: {self.workers_spin.value()}\n"
            f"Force reprocess: {self.force_reprocess_check.isChecked()}\n\n"
            "This may take several minutes. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Disable controls
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Initializing...")
        self.log_output.clear()
        self._log("Starting Definition 2.0 processing...")

        # Start processing thread
        self.processing_thread = ProcessingThread(
            vault_path=vault_path,
            max_workers=self.workers_spin.value(),
            force_reprocess=self.force_reprocess_check.isChecked()
        )
        
        self.processing_thread.progress.connect(self._on_progress)
        self.processing_thread.finished.connect(self._on_finished)
        self.processing_thread.error.connect(self._on_error)
        
        self.processing_thread.start()

    def _stop_processing(self):
        """Stop the processing."""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.terminate()
            self.processing_thread.wait()
            self._log("Processing stopped by user")
            self.status_label.setText("Stopped")
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _on_progress(self, current: int, total: int, message: str):
        """Handle progress update."""
        if total > 0:
            progress = int((current / total) * 100)
            self.progress_bar.setValue(progress)
        
        self.status_label.setText(f"{current}/{total} - {message}")
        self._log(message)

    def _on_finished(self, stats: dict):
        """Handle completion."""
        self.progress_bar.setValue(100)
        self.status_label.setText("Complete!")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        # Update statistics table
        self.stats_table.setRowCount(0)
        for key, value in stats.items():
            row = self.stats_table.rowCount()
            self.stats_table.insertRow(row)
            self.stats_table.setItem(row, 0, QTableWidgetItem(key.replace('_', ' ').title()))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(value)))

        self._log(f"\n{'='*50}")
        self._log("Processing complete!")
        self._log(f"Total: {stats.get('total', 0)}")
        self._log(f"Success: {stats.get('success', 0)}")
        self._log(f"Partial: {stats.get('partial', 0)}")
        self._log(f"Failed: {stats.get('failed', 0)}")
        self._log(f"{'='*50}\n")

        QMessageBox.information(
            self, "Complete",
            f"Processing complete!\n\n"
            f"Total: {stats.get('total', 0)}\n"
            f"Success: {stats.get('success', 0)}\n"
            f"Partial: {stats.get('partial', 0)}\n"
            f"Failed: {stats.get('failed', 0)}"
        )

    def _on_error(self, error_msg: str):
        """Handle error."""
        self.status_label.setText("Error!")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._log(f"ERROR: {error_msg}")
        
        QMessageBox.critical(
            self, "Processing Error",
            f"An error occurred during processing:\n\n{error_msg}"
        )

    def _view_report(self):
        """Open the processing report."""
        vault_path = Path(self.settings.get("vault_path", "."))
        report_path = vault_path / "Definitions_v2" / "processing_summary.md"
        
        if not report_path.exists():
            QMessageBox.information(
                self, "No Report",
                "No processing report found. Run processing first."
            )
            return

        # Open in default application
        import os
        import platform
        
        try:
            if platform.system() == 'Windows':
                os.startfile(report_path)
            elif platform.system() == 'Darwin':  # macOS
                os.system(f'open "{report_path}"')
            else:  # Linux
                os.system(f'xdg-open "{report_path}"')
        except Exception as e:
            QMessageBox.warning(
                self, "Error",
                f"Could not open report:\n{e}\n\nPath: {report_path}"
            )

    def _log(self, message: str):
        """Add message to log."""
        self.log_output.append(message)
        # Auto-scroll to bottom
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
