"""
Ollama Processor Tab - Background YAML processing with folder queue management
Designed for low-CPU continuous operation (day/night processing)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import threading
import queue
import time
import requests
import yaml
import uuid
import re

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QComboBox, QSpinBox,
        QTextEdit, QGroupBox, QProgressBar, QCheckBox,
        QFileDialog, QSplitter, QFrame, QSlider, QDoubleSpinBox
    )
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
    from PySide6.QtGui import QColor
    pyqtSignal = Signal  # Alias for compatibility
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QListWidget, QListWidgetItem, QComboBox, QSpinBox,
        QTextEdit, QGroupBox, QProgressBar, QCheckBox,
        QFileDialog, QSplitter, QFrame, QSlider, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QColor


class OllamaWorker(QThread):
    """Background worker for continuous Ollama processing."""

    progress = pyqtSignal(str)  # Log message
    file_done = pyqtSignal(dict)  # File result
    folder_done = pyqtSignal(str)  # Folder path
    status_update = pyqtSignal(dict)  # Status dict

    def __init__(self):
        super().__init__()
        self.running = False
        self.paused = False
        self.folder_queue = queue.Queue()
        self.model = "llama3.2"
        self.delay_between_files = 2.0  # seconds
        self.delay_between_requests = 0.5  # seconds within file
        self.skip_existing = True
        self.dry_run = False
        self.current_folder = None
        self.files_processed = 0
        self.files_total = 0

        # YAML prompt template
        self.yaml_prompt = """You are a YAML frontmatter generator for the Theophysics academic framework.
Analyze this note and generate YAML frontmatter.

REQUIRED FIELDS:
- title: Extract from first heading or generate
- uuid: Generate UUID format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- type: One of [axiom, theorem, definition, stage, paper, evidence, claim, note]
- status: draft
- tier: One of [primordial, ontological, physical, consciousness, agency, relational, eschatological]

OPTIONAL:
- axiom_refs: List referenced axioms [A1.1, T1, etc]
- domains: [physics, theology, information-theory, consciousness, mathematics, ethics]
- tags: Relevant tags
- aliases: Domain variants [AT#.#, AS#.#, AE#.#, AQ#.#, AP#.#, AC#.#, AI#.#]
- summary: One sentence

Return ONLY valid YAML, no code blocks.

Note content:
{content}

YAML:"""

        self.axiom_pattern = re.compile(
            r'\[\[([ATLMPC]\d+(?:\.\d+)*)\]\]|'
            r'(?<!\w)([ATLM]\d+\.\d+)(?!\w)',
            re.IGNORECASE
        )

    def add_folder(self, folder_path: str, priority: int = 5):
        """Add folder to queue with priority (1=highest, 10=lowest)."""
        self.folder_queue.put((priority, folder_path))
        self.progress.emit(f"Added to queue: {folder_path} (priority {priority})")

    def set_model(self, model: str):
        self.model = model

    def set_delays(self, file_delay: float, request_delay: float):
        self.delay_between_files = file_delay
        self.delay_between_requests = request_delay

    def pause(self):
        self.paused = True
        self.progress.emit("⏸️ Paused")

    def resume(self):
        self.paused = False
        self.progress.emit("▶️ Resumed")

    def stop(self):
        self.running = False
        self.progress.emit("⏹️ Stopping...")

    def check_ollama(self) -> bool:
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False

    def generate(self, prompt: str, timeout: int = 180) -> Optional[str]:
        """Call Ollama with longer timeout for slow/idle mode."""
        try:
            r = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,  # Reduced context for lower memory
                        "num_thread": 2,  # Limit CPU threads
                    }
                },
                timeout=timeout
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception as e:
            self.progress.emit(f"⚠️ Ollama error: {e}")
        return None

    def extract_frontmatter(self, content: str) -> tuple:
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[1].strip(), parts[2].strip()
        return None, content

    def extract_axiom_refs(self, content: str) -> List[str]:
        refs = set()
        for match in self.axiom_pattern.finditer(content):
            ref = match.group(1) or match.group(2)
            if ref:
                refs.add(ref.upper())
        return sorted(refs)

    def parse_yaml(self, yaml_str: str) -> Optional[Dict]:
        try:
            yaml_str = yaml_str.strip()
            if yaml_str.startswith('```'):
                lines = yaml_str.split('\n')
                yaml_str = '\n'.join(l for l in lines if not l.startswith('```'))
            return yaml.safe_load(yaml_str)
        except:
            return None

    def process_file(self, filepath: Path) -> Dict:
        result = {
            'path': str(filepath),
            'status': 'skipped',
            'time': datetime.now().isoformat()
        }

        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            return result

        existing_fm, body = self.extract_frontmatter(content)

        if existing_fm and self.skip_existing:
            result['status'] = 'skipped_has_fm'
            return result

        # Extract axiom refs
        axioms = self.extract_axiom_refs(content)

        # Generate YAML
        prompt = self.yaml_prompt.format(content=content[:1500])

        time.sleep(self.delay_between_requests)  # Throttle

        response = self.generate(prompt)
        if not response:
            result['status'] = 'error'
            result['error'] = 'No Ollama response'
            return result

        new_fm = self.parse_yaml(response)
        if not new_fm:
            result['status'] = 'error'
            result['error'] = 'Invalid YAML'
            return result

        # Add axiom refs
        if axioms:
            new_fm['axiom_refs'] = axioms

        # Ensure UUID
        if 'uuid' not in new_fm:
            new_fm['uuid'] = str(uuid.uuid4())

        # Generate aliases if it's an axiom
        if new_fm.get('type') == 'axiom' and 'axiom_refs' in new_fm:
            for ref in new_fm['axiom_refs']:
                if ref.startswith('A') and '.' in ref:
                    num = ref[1:]  # e.g., "1.1"
                    new_fm['aliases'] = [
                        f"AT{num}", f"AS{num}", f"AE{num}",
                        f"AQ{num}", f"AP{num}", f"AC{num}", f"AI{num}"
                    ]
                    break

        result['generated'] = new_fm
        result['status'] = 'generated'

        if not self.dry_run:
            try:
                new_content = f"---\n{yaml.dump(new_fm, default_flow_style=False, allow_unicode=True)}---\n\n{body}"
                filepath.write_text(new_content, encoding='utf-8')
                result['status'] = 'updated'
            except Exception as e:
                result['status'] = 'error'
                result['error'] = f"Write failed: {e}"

        return result

    def process_folder(self, folder_path: str):
        folder = Path(folder_path)
        if not folder.exists():
            self.progress.emit(f"❌ Folder not found: {folder_path}")
            return

        self.current_folder = folder_path
        md_files = list(folder.rglob("*.md"))

        # Skip canonical/system files
        skip_patterns = ['04_The_Axioms', '00_CANONICAL', '01_CANONICAL', '_TEMPLATE', '.obsidian']
        md_files = [f for f in md_files if not any(p in str(f) for p in skip_patterns)]

        self.files_total = len(md_files)
        self.files_processed = 0

        self.progress.emit(f"📂 Processing: {folder_path}")
        self.progress.emit(f"   Found {self.files_total} files")

        for filepath in md_files:
            if not self.running:
                break

            while self.paused:
                time.sleep(0.5)
                if not self.running:
                    break

            self.progress.emit(f"  → {filepath.name[:50]}")
            result = self.process_file(filepath)
            self.files_processed += 1

            self.file_done.emit(result)
            self.status_update.emit({
                'folder': folder_path,
                'processed': self.files_processed,
                'total': self.files_total,
                'status': result['status']
            })

            time.sleep(self.delay_between_files)  # Throttle between files

        self.folder_done.emit(folder_path)
        self.progress.emit(f"✅ Completed: {folder_path}")

    def run(self):
        self.running = True
        self.progress.emit("🚀 Worker started")

        if not self.check_ollama():
            self.progress.emit("❌ Ollama not running! Start with: ollama serve")
            self.running = False
            return

        self.progress.emit(f"✅ Ollama ready (model: {self.model})")

        while self.running:
            try:
                # Get next folder (with timeout so we can check running flag)
                priority, folder_path = self.folder_queue.get(timeout=1.0)
                self.process_folder(folder_path)
                self.folder_queue.task_done()
            except queue.Empty:
                # No folders in queue, just wait
                pass
            except Exception as e:
                self.progress.emit(f"❌ Error: {e}")

        self.progress.emit("⏹️ Worker stopped")


class OllamaProcessorTab(QWidget):
    """GUI tab for Ollama background processing."""

    def __init__(self, parent=None, settings=None, db_engine=None):
        super().__init__(parent)
        self.settings = settings
        self.db = db_engine
        self.worker = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Top controls
        top_layout = QHBoxLayout()

        # Status indicator
        self.status_label = QLabel("⏹️ Stopped")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        top_layout.addWidget(self.status_label)

        top_layout.addStretch()

        # Model selection
        top_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["llama3.2", "llama3.1", "mistral", "phi3", "gemma2"])
        self.model_combo.setCurrentText("llama3.2")
        top_layout.addWidget(self.model_combo)

        # Refresh models button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(30)
        refresh_btn.clicked.connect(self.refresh_models)
        top_layout.addWidget(refresh_btn)

        layout.addLayout(top_layout)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Folder queue
        queue_group = QGroupBox("Folder Queue")
        queue_layout = QVBoxLayout(queue_group)

        self.folder_list = QListWidget()
        self.folder_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        queue_layout.addWidget(self.folder_list)

        # Queue buttons
        queue_btn_layout = QHBoxLayout()

        add_folder_btn = QPushButton("+ Add Folder")
        add_folder_btn.clicked.connect(self.add_folder)
        queue_btn_layout.addWidget(add_folder_btn)

        remove_btn = QPushButton("- Remove")
        remove_btn.clicked.connect(self.remove_selected)
        queue_btn_layout.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_queue)
        queue_btn_layout.addWidget(clear_btn)

        queue_layout.addLayout(queue_btn_layout)

        # Priority preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))

        drafting_btn = QPushButton("02_DRAFTING")
        drafting_btn.clicked.connect(lambda: self.add_preset_folder("02_DRAFTING"))
        preset_layout.addWidget(drafting_btn)

        publications_btn = QPushButton("03_PUBLICATIONS")
        publications_btn.clicked.connect(lambda: self.add_preset_folder("03_PUBLICATIONS"))
        preset_layout.addWidget(publications_btn)

        queue_layout.addLayout(preset_layout)

        splitter.addWidget(queue_group)

        # Right: Controls & Log
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Throttle controls
        throttle_group = QGroupBox("Throttle Settings (Low CPU Mode)")
        throttle_layout = QVBoxLayout(throttle_group)

        # Delay between files
        file_delay_layout = QHBoxLayout()
        file_delay_layout.addWidget(QLabel("Delay between files (sec):"))
        self.file_delay_spin = QDoubleSpinBox()
        self.file_delay_spin.setRange(0.5, 60.0)
        self.file_delay_spin.setValue(3.0)
        self.file_delay_spin.setSingleStep(0.5)
        file_delay_layout.addWidget(self.file_delay_spin)
        throttle_layout.addLayout(file_delay_layout)

        # Request delay
        req_delay_layout = QHBoxLayout()
        req_delay_layout.addWidget(QLabel("Delay between requests (sec):"))
        self.req_delay_spin = QDoubleSpinBox()
        self.req_delay_spin.setRange(0.1, 10.0)
        self.req_delay_spin.setValue(1.0)
        self.req_delay_spin.setSingleStep(0.1)
        req_delay_layout.addWidget(self.req_delay_spin)
        throttle_layout.addLayout(req_delay_layout)

        # Options
        self.skip_existing_cb = QCheckBox("Skip files with existing YAML")
        self.skip_existing_cb.setChecked(True)
        throttle_layout.addWidget(self.skip_existing_cb)

        self.dry_run_cb = QCheckBox("Dry run (don't write files)")
        throttle_layout.addWidget(self.dry_run_cb)

        right_layout.addWidget(throttle_group)

        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("Ready")
        progress_layout.addWidget(self.progress_label)

        right_layout.addWidget(progress_group)

        # Control buttons
        control_layout = QHBoxLayout()

        self.start_btn = QPushButton("▶️ Start")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self.start_processing)
        control_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_processing)
        control_layout.addWidget(self.stop_btn)

        right_layout.addLayout(control_layout)

        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        log_layout.addWidget(clear_log_btn)

        right_layout.addWidget(log_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([300, 400])

        layout.addWidget(splitter)

        # Auto-refresh models on init
        QTimer.singleShot(1000, self.refresh_models)

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def refresh_models(self):
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m['name'] for m in r.json().get('models', [])]
                current = self.model_combo.currentText()
                self.model_combo.clear()
                self.model_combo.addItems(models)
                if current in models:
                    self.model_combo.setCurrentText(current)
                self.log(f"Found {len(models)} Ollama models")
        except Exception as e:
            self.log(f"⚠️ Can't connect to Ollama: {e}")

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Process",
            "O:/Theophysics_Master/TM SUBSTACK"
        )
        if folder:
            item = QListWidgetItem(folder)
            self.folder_list.addItem(item)
            self.log(f"Added: {folder}")

    def add_preset_folder(self, name: str):
        base = Path("O:/Theophysics_Master/TM SUBSTACK")
        folder = base / name
        if folder.exists():
            item = QListWidgetItem(str(folder))
            self.folder_list.addItem(item)
            self.log(f"Added preset: {name}")
        else:
            self.log(f"⚠️ Folder not found: {folder}")

    def remove_selected(self):
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))

    def clear_queue(self):
        self.folder_list.clear()
        self.log("Queue cleared")

    def start_processing(self):
        if self.folder_list.count() == 0:
            self.log("⚠️ No folders in queue!")
            return

        # Create worker
        self.worker = OllamaWorker()
        self.worker.set_model(self.model_combo.currentText())
        self.worker.set_delays(
            self.file_delay_spin.value(),
            self.req_delay_spin.value()
        )
        self.worker.skip_existing = self.skip_existing_cb.isChecked()
        self.worker.dry_run = self.dry_run_cb.isChecked()

        # Connect signals
        self.worker.progress.connect(self.log)
        self.worker.file_done.connect(self.on_file_done)
        self.worker.folder_done.connect(self.on_folder_done)
        self.worker.status_update.connect(self.on_status_update)
        self.worker.finished.connect(self.on_worker_finished)

        # Add folders to worker queue (in order shown)
        for i in range(self.folder_list.count()):
            folder = self.folder_list.item(i).text()
            self.worker.add_folder(folder, priority=i+1)

        # Update UI
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("🔄 Running")
        self.status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")

        # Start
        self.worker.start()

    def toggle_pause(self):
        if self.worker:
            if self.worker.paused:
                self.worker.resume()
                self.pause_btn.setText("⏸️ Pause")
                self.status_label.setText("🔄 Running")
            else:
                self.worker.pause()
                self.pause_btn.setText("▶️ Resume")
                self.status_label.setText("⏸️ Paused")

    def stop_processing(self):
        if self.worker:
            self.worker.stop()

    def on_file_done(self, result: dict):
        status = result.get('status', 'unknown')
        if status == 'updated':
            self.log(f"  ✅ Updated")
        elif status == 'skipped_has_fm':
            pass  # Don't log skips
        elif status == 'error':
            self.log(f"  ❌ Error: {result.get('error', 'unknown')}")

    def on_folder_done(self, folder: str):
        # Remove from list
        for i in range(self.folder_list.count()):
            if self.folder_list.item(i).text() == folder:
                self.folder_list.takeItem(i)
                break

    def on_status_update(self, status: dict):
        processed = status.get('processed', 0)
        total = status.get('total', 1)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(processed)
        self.progress_label.setText(f"{processed}/{total} files")

    def on_worker_finished(self):
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏹️ Stopped")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.log("Worker finished")
        self.worker = None
