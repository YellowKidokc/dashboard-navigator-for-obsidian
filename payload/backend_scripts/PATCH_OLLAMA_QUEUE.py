"""
PATCH: Adds folder queue + throttle controls to Ollama YAML page
Run this to patch main_window_v2.py with enhanced Ollama features
"""

import re
from pathlib import Path

MAIN_WINDOW_PATH = Path(__file__).parent / "ui" / "main_window_v2.py"

# The new _build_ollama_page method to replace the existing one
NEW_OLLAMA_PAGE = '''
    # ==========================================
    # PAGE 9: OLLAMA YAML PROCESSOR (ENHANCED)
    # ==========================================
    def _build_ollama_page(self):
        """Build the enhanced Ollama YAML processing page with queue."""
        page, layout = self._create_page_container("🤖 Ollama YAML Processor")

        # Main splitter
        from PySide6.QtWidgets import QSplitter, QDoubleSpinBox, QListWidget
        from PySide6.QtCore import Qt as QtCore

        splitter = QSplitter(QtCore.Horizontal)

        # ==========================================
        # LEFT PANEL: Folder Queue
        # ==========================================
        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)

        queue_group = QGroupBox("📂 Folder Queue (Drag to Reorder)")
        queue_inner = QVBoxLayout(queue_group)

        self.ollama_folder_queue = QListWidget()
        self.ollama_folder_queue.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.ollama_folder_queue.setMinimumHeight(200)
        queue_inner.addWidget(self.ollama_folder_queue)

        # Queue buttons
        q_btn_row = QHBoxLayout()

        add_folder_btn = QPushButton("+ Add Folder")
        add_folder_btn.clicked.connect(self._add_ollama_folder)
        q_btn_row.addWidget(add_folder_btn)

        remove_folder_btn = QPushButton("- Remove")
        remove_folder_btn.clicked.connect(self._remove_ollama_folder)
        q_btn_row.addWidget(remove_folder_btn)

        clear_queue_btn = QPushButton("Clear")
        clear_queue_btn.clicked.connect(lambda: self.ollama_folder_queue.clear())
        q_btn_row.addWidget(clear_queue_btn)

        queue_inner.addLayout(q_btn_row)

        # Preset buttons
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Presets:"))

        draft_btn = QPushButton("02_DRAFTING")
        draft_btn.clicked.connect(lambda: self._add_preset_ollama("02_DRAFTING"))
        preset_row.addWidget(draft_btn)

        pub_btn = QPushButton("03_PUBLICATIONS")
        pub_btn.clicked.connect(lambda: self._add_preset_ollama("03_PUBLICATIONS"))
        preset_row.addWidget(pub_btn)

        queue_inner.addLayout(preset_row)
        queue_layout.addWidget(queue_group)

        splitter.addWidget(queue_widget)

        # ==========================================
        # RIGHT PANEL: Controls
        # ==========================================
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Model selection
        config_group = QGroupBox("⚙️ Ollama Configuration")
        config_layout = QVBoxLayout(config_group)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.addItems([
            "llama3.2", "llama3.2:3b", "llama3.1", "llama3.1:8b",
            "mistral", "mixtral", "phi3", "qwen2.5"
        ])
        self.ollama_model_combo.setEditable(True)
        model_row.addWidget(self.ollama_model_combo, 1)

        self.ollama_check_btn = QPushButton("🔍 Check")
        self.ollama_check_btn.clicked.connect(self._check_ollama_status)
        model_row.addWidget(self.ollama_check_btn)

        self.ollama_status_label = QLabel("❓")
        model_row.addWidget(self.ollama_status_label)

        config_layout.addLayout(model_row)
        right_layout.addWidget(config_group)

        # Throttle controls
        throttle_group = QGroupBox("🐢 Throttle Settings (Low CPU Mode)")
        throttle_layout = QVBoxLayout(throttle_group)

        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel("Delay between files (sec):"))
        self.ollama_file_delay = QDoubleSpinBox()
        self.ollama_file_delay.setRange(0.5, 60.0)
        self.ollama_file_delay.setValue(3.0)
        self.ollama_file_delay.setSingleStep(0.5)
        delay_row.addWidget(self.ollama_file_delay)
        throttle_layout.addLayout(delay_row)

        threads_row = QHBoxLayout()
        threads_row.addWidget(QLabel("CPU Threads (2=low):"))
        self.ollama_threads = QSpinBox()
        self.ollama_threads.setRange(1, 16)
        self.ollama_threads.setValue(2)
        threads_row.addWidget(self.ollama_threads)
        throttle_layout.addLayout(threads_row)

        right_layout.addWidget(throttle_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.ollama_skip_fm_check = QCheckBox("Skip files with existing frontmatter")
        self.ollama_skip_fm_check.setChecked(True)
        options_layout.addWidget(self.ollama_skip_fm_check)

        self.ollama_dry_run_check = QCheckBox("Dry run (preview only)")
        options_layout.addWidget(self.ollama_dry_run_check)

        self.ollama_recursive_check = QCheckBox("Recursive (include subfolders)")
        self.ollama_recursive_check.setChecked(True)
        options_layout.addWidget(self.ollama_recursive_check)

        right_layout.addWidget(options_group)

        # Run controls
        run_group = QGroupBox("🚀 Background Processing")
        run_layout = QVBoxLayout(run_group)

        btn_row = QHBoxLayout()

        self.ollama_run_btn = QPushButton("▶️ Start Processing")
        self.ollama_run_btn.setProperty("class", "primary")
        self.ollama_run_btn.clicked.connect(self._start_ollama_background)
        btn_row.addWidget(self.ollama_run_btn)

        self.ollama_pause_btn = QPushButton("⏸️ Pause")
        self.ollama_pause_btn.setEnabled(False)
        self.ollama_pause_btn.clicked.connect(self._toggle_ollama_pause)
        btn_row.addWidget(self.ollama_pause_btn)

        self.ollama_stop_btn = QPushButton("⏹️ Stop")
        self.ollama_stop_btn.setEnabled(False)
        self.ollama_stop_btn.clicked.connect(self._stop_ollama_processing)
        btn_row.addWidget(self.ollama_stop_btn)

        run_layout.addLayout(btn_row)

        self.ollama_progress = QProgressBar()
        run_layout.addWidget(self.ollama_progress)

        self.ollama_run_status = QLabel("⏹️ Ready - Add folders and click Start")
        self.ollama_run_status.setStyleSheet("font-weight: bold;")
        run_layout.addWidget(self.ollama_run_status)

        right_layout.addWidget(run_group)

        # Stats
        stats_group = QGroupBox("📊 Statistics")
        stats_layout = QGridLayout(stats_group)

        self.ollama_stats = {
            'processed': QLabel("0"),
            'updated': QLabel("0"),
            'skipped': QLabel("0"),
            'errors': QLabel("0"),
        }

        for i, (label, key) in enumerate([
            ("Processed", 'processed'), ("Updated", 'updated'),
            ("Skipped", 'skipped'), ("Errors", 'errors')
        ]):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("font-weight: bold;")
            stats_layout.addWidget(lbl, 0, i * 2)
            self.ollama_stats[key].setStyleSheet("font-size: 16px; color: #22c55e;")
            stats_layout.addWidget(self.ollama_stats[key], 0, i * 2 + 1)

        right_layout.addWidget(stats_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([350, 450])

        layout.addWidget(splitter)

        # Log
        log_group = QGroupBox("📋 Processing Log")
        log_layout = QVBoxLayout(log_group)

        self.ollama_log = QTextEdit()
        self.ollama_log.setReadOnly(True)
        self.ollama_log.setMaximumHeight(180)
        self.ollama_log.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            color: {COLORS['text_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 9pt;
        """)
        log_layout.addWidget(self.ollama_log)

        log_btn_row = QHBoxLayout()
        clear_log_btn = QPushButton("🗑️ Clear")
        clear_log_btn.clicked.connect(lambda: self.ollama_log.clear())
        log_btn_row.addWidget(clear_log_btn)
        log_btn_row.addStretch()
        log_layout.addLayout(log_btn_row)

        layout.addWidget(log_group)

        # Initialize worker reference
        self._ollama_worker = None
        self._ollama_paused = False

    def _add_ollama_folder(self):
        """Add folder to queue."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder",
            "O:/Theophysics_Master/TM SUBSTACK"
        )
        if folder:
            from PySide6.QtWidgets import QListWidgetItem
            self.ollama_folder_queue.addItem(QListWidgetItem(folder))
            self._log_ollama(f"Added: {folder}")

    def _remove_ollama_folder(self):
        """Remove selected folder from queue."""
        for item in self.ollama_folder_queue.selectedItems():
            self.ollama_folder_queue.takeItem(self.ollama_folder_queue.row(item))

    def _add_preset_ollama(self, name: str):
        """Add preset folder."""
        from PySide6.QtWidgets import QListWidgetItem
        base = Path("O:/Theophysics_Master/TM SUBSTACK")
        folder = base / name
        if folder.exists():
            self.ollama_folder_queue.addItem(QListWidgetItem(str(folder)))
            self._log_ollama(f"Added preset: {name}")

    def _log_ollama(self, message: str):
        """Add message to log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ollama_log.append(f"[{timestamp}] {message}")
        # Auto-scroll
        scrollbar = self.ollama_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _start_ollama_background(self):
        """Start background processing."""
        if self.ollama_folder_queue.count() == 0:
            self._log_ollama("⚠️ No folders in queue!")
            return

        from ui.tabs.ollama_processor_tab import OllamaWorker

        self._ollama_worker = OllamaWorker()
        self._ollama_worker.set_model(self.ollama_model_combo.currentText())
        self._ollama_worker.set_delays(
            self.ollama_file_delay.value(),
            0.5  # request delay
        )
        self._ollama_worker.skip_existing = self.ollama_skip_fm_check.isChecked()
        self._ollama_worker.dry_run = self.ollama_dry_run_check.isChecked()

        # Connect signals
        self._ollama_worker.progress.connect(self._log_ollama)
        self._ollama_worker.file_done.connect(self._on_ollama_file_done)
        self._ollama_worker.status_update.connect(self._on_ollama_status)
        self._ollama_worker.finished.connect(self._on_ollama_finished)

        # Add folders to queue
        for i in range(self.ollama_folder_queue.count()):
            folder = self.ollama_folder_queue.item(i).text()
            self._ollama_worker.add_folder(folder, priority=i+1)

        # Update UI
        self.ollama_run_btn.setEnabled(False)
        self.ollama_pause_btn.setEnabled(True)
        self.ollama_stop_btn.setEnabled(True)
        self.ollama_run_status.setText("🔄 Running...")
        self.ollama_run_status.setStyleSheet("color: #22c55e; font-weight: bold;")

        self._ollama_worker.start()

    def _toggle_ollama_pause(self):
        """Toggle pause state."""
        if self._ollama_worker:
            if self._ollama_paused:
                self._ollama_worker.resume()
                self.ollama_pause_btn.setText("⏸️ Pause")
                self.ollama_run_status.setText("🔄 Running...")
                self._ollama_paused = False
            else:
                self._ollama_worker.pause()
                self.ollama_pause_btn.setText("▶️ Resume")
                self.ollama_run_status.setText("⏸️ Paused")
                self._ollama_paused = True

    def _on_ollama_file_done(self, result: dict):
        """Handle file completion."""
        status = result.get('status', 'unknown')
        current = int(self.ollama_stats['processed'].text())
        self.ollama_stats['processed'].setText(str(current + 1))

        if status == 'updated':
            curr = int(self.ollama_stats['updated'].text())
            self.ollama_stats['updated'].setText(str(curr + 1))
        elif status == 'skipped_has_fm':
            curr = int(self.ollama_stats['skipped'].text())
            self.ollama_stats['skipped'].setText(str(curr + 1))
        elif status == 'error':
            curr = int(self.ollama_stats['errors'].text())
            self.ollama_stats['errors'].setText(str(curr + 1))

    def _on_ollama_status(self, status: dict):
        """Update progress."""
        processed = status.get('processed', 0)
        total = status.get('total', 1)
        self.ollama_progress.setMaximum(total)
        self.ollama_progress.setValue(processed)

    def _on_ollama_finished(self):
        """Handle worker finished."""
        self.ollama_run_btn.setEnabled(True)
        self.ollama_pause_btn.setEnabled(False)
        self.ollama_stop_btn.setEnabled(False)
        self.ollama_run_status.setText("⏹️ Finished")
        self.ollama_run_status.setStyleSheet("font-weight: bold;")
        self._ollama_worker = None
'''

def patch_file():
    """Apply the patch to main_window_v2.py"""
    if not MAIN_WINDOW_PATH.exists():
        print(f"ERROR: {MAIN_WINDOW_PATH} not found!")
        return False

    content = MAIN_WINDOW_PATH.read_text(encoding='utf-8')

    # Find the existing _build_ollama_page method
    pattern = r'(    # ={40,}\s*\n    # PAGE 9: OLLAMA YAML PROCESSOR\s*\n    # ={40,}\s*\n    def _build_ollama_page\(self\):.*?)(?=\n    # ={40,}\s*\n    # PAGE \d|$)'

    match = re.search(pattern, content, re.DOTALL)
    if not match:
        print("ERROR: Could not find _build_ollama_page method!")
        return False

    # Backup
    backup_path = MAIN_WINDOW_PATH.with_suffix('.py.ollama_backup')
    MAIN_WINDOW_PATH.rename(backup_path)
    print(f"Backup saved: {backup_path}")

    # Replace
    new_content = content[:match.start()] + NEW_OLLAMA_PAGE + content[match.end():]

    MAIN_WINDOW_PATH.write_text(new_content, encoding='utf-8')
    print(f"Patched: {MAIN_WINDOW_PATH}")
    print("\nEnhanced Ollama page with:")
    print("  - Folder queue (multiple folders)")
    print("  - Drag-drop reordering")
    print("  - Preset buttons (02_DRAFTING, 03_PUBLICATIONS)")
    print("  - Throttle controls (delay, CPU threads)")
    print("  - Background worker (runs day/night)")
    print("  - Pause/Resume support")

    return True


if __name__ == '__main__':
    print("=" * 50)
    print("  OLLAMA QUEUE PATCH")
    print("=" * 50)

    response = input("\nApply patch to main_window_v2.py? (y/n): ")
    if response.lower() == 'y':
        if patch_file():
            print("\n✅ Patch applied successfully!")
        else:
            print("\n❌ Patch failed!")
    else:
        print("Cancelled.")
