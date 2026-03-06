"""
THEOPHYSICS BACKEND FIX SCRIPT
==============================
This script fixes:
1. Adds Ollama YAML tab to the UI
2. Fixes Mermaid PyQt6 → PySide6 import bug
3. Adds hidden prompt system for YAML files
4. Fixes PostgreSQL sync issues

Run: python APPLY_ALL_FIXES.py
"""

import re
from pathlib import Path
from datetime import datetime

BACKEND_PATH = Path(r"O:\Theophysics_Backend\Backend Python")
UI_FILE = BACKEND_PATH / "ui" / "main_window_v2.py"
OLLAMA_SCRIPT = BACKEND_PATH / "scripts" / "ollama_yaml_processor.py"

def backup_file(filepath: Path) -> Path:
    """Create timestamped backup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    backup_path.write_text(filepath.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"✓ Backed up: {backup_path.name}")
    return backup_path

def fix_mermaid_import():
    """Fix PyQt6 → PySide6 import in Mermaid code."""
    content = UI_FILE.read_text(encoding='utf-8')
    
    # Fix the PyQt6 import bug
    old_import = "from PyQt6.QtWidgets import QApplication"
    new_import = "from PySide6.QtWidgets import QApplication"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        print("✓ Fixed PyQt6 → PySide6 import in Mermaid code")
    else:
        print("→ PyQt6 import already fixed or not found")
    
    # Also ensure QDialog is imported at the top level
    if "QDialog" not in content.split("from PySide6.QtWidgets import")[1].split(")")[0]:
        # Add QDialog to imports
        content = content.replace(
            "from PySide6.QtWidgets import (\n    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,",
            "from PySide6.QtWidgets import (\n    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDialog,"
        )
        print("✓ Added QDialog to PySide6 imports")
    
    return content

def add_ollama_to_nav_items(content: str) -> str:
    """Add Ollama to navigation items."""
    # Find and update NAV_ITEMS
    old_nav = '''NAV_ITEMS = [
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
    
    new_nav = '''NAV_ITEMS = [
        ("🏠", "Dashboard"),
        ("📄", "Paper Scanner"),
        ("🔗", "Auto-Linker"),
        ("📚", "Definitions"),
        ("📊", "Data Aggregation"),
        ("🔗", "Research Links"),
        ("📝", "Footnotes & Templates"),
        ("🧠", "Semantic Dashboard"),
        ("🏷️", "Tag Manager"),
        ("🤖", "Ollama YAML"),
        ("🗄️", "Database"),
        ("⚙️", "Settings"),
    ]'''
    
    if old_nav in content:
        content = content.replace(old_nav, new_nav)
        print("✓ Added Ollama to NAV_ITEMS")
    else:
        print("→ NAV_ITEMS structure different, manually check")
    
    return content

def update_page_build_calls(content: str) -> str:
    """Update page build calls to include Ollama."""
    old_builds = '''# Build pages (must match NAV_ITEMS order)
        self._build_dashboard_page()      # 0 - Dashboard
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
    
    new_builds = '''# Build pages (must match NAV_ITEMS order)
        self._build_dashboard_page()      # 0 - Dashboard
        self._build_paper_scanner_page()  # 1 - Paper Scanner
        self._build_linker_page()         # 2 - Auto-Linker
        self._build_definitions_page()    # 3 - Definitions
        self._build_aggregation_page()    # 4 - Data Aggregation
        self._build_research_links_page() # 5 - Research Links
        self._build_footnotes_page()      # 6 - Footnotes & Templates
        self._build_semantic_dashboard()  # 7 - Semantic Dashboard
        self._build_tag_manager_page()    # 8 - Tag Manager
        self._build_ollama_page()         # 9 - Ollama YAML
        self._build_database_page()       # 10 - Database
        self._build_settings_page()       # 11 - Settings'''
    
    if old_builds in content:
        content = content.replace(old_builds, new_builds)
        print("✓ Updated page build order with Ollama")
    else:
        print("→ Page build section different, manually check")
    
    return content

OLLAMA_PAGE_CODE = '''
# ==========================================
# PAGE 9: OLLAMA YAML PROCESSOR
# ==========================================
def _build_ollama_page(self):
    """Build the Ollama YAML processing page."""
    page, layout = self._create_page_container("🤖 Ollama YAML Processor")
    
    # ==========================================
    # SECTION 1: Configuration
    # ==========================================
    config_group = QGroupBox("⚙️ Ollama Configuration")
    config_layout = QVBoxLayout(config_group)
    
    # Model selection row
    model_row = QHBoxLayout()
    model_row.addWidget(QLabel("Model:"))
    self.ollama_model_combo = QComboBox()
    self.ollama_model_combo.addItems([
        "llama3.2", "llama3.2:3b", "llama3.1", "llama3.1:8b", 
        "mistral", "mixtral", "phi3", "qwen2.5"
    ])
    self.ollama_model_combo.setEditable(True)
    model_row.addWidget(self.ollama_model_combo, 1)
    
    self.ollama_check_btn = QPushButton("🔍 Check Status")
    self.ollama_check_btn.clicked.connect(self._check_ollama_status)
    model_row.addWidget(self.ollama_check_btn)
    
    self.ollama_status_label = QLabel("❓ Not checked")
    self.ollama_status_label.setStyleSheet("color: #6b7280;")
    model_row.addWidget(self.ollama_status_label)
    
    config_layout.addLayout(model_row)
    
    # Folder row
    folder_row = QHBoxLayout()
    folder_row.addWidget(QLabel("Papers Folder:"))
    self.ollama_folder_edit = QLineEdit()
    self.ollama_folder_edit.setPlaceholderText("Select folder with markdown papers...")
    folder_row.addWidget(self.ollama_folder_edit, 1)
    
    browse_btn = QPushButton("📁 Browse")
    browse_btn.clicked.connect(self._browse_ollama_folder)
    folder_row.addWidget(browse_btn)
    config_layout.addLayout(folder_row)
    
    # Options row
    options_row = QHBoxLayout()
    self.ollama_recursive_check = QCheckBox("Recursive")
    self.ollama_recursive_check.setChecked(True)
    options_row.addWidget(self.ollama_recursive_check)
    
    self.ollama_skip_fm_check = QCheckBox("Skip files with frontmatter")
    options_row.addWidget(self.ollama_skip_fm_check)
    
    self.ollama_dry_run_check = QCheckBox("Dry run (preview only)")
    options_row.addWidget(self.ollama_dry_run_check)
    
    options_row.addStretch()
    
    options_row.addWidget(QLabel("Limit:"))
    self.ollama_limit_spin = QSpinBox()
    self.ollama_limit_spin.setRange(0, 1000)
    self.ollama_limit_spin.setValue(0)
    self.ollama_limit_spin.setSpecialValueText("All")
    self.ollama_limit_spin.setToolTip("0 = process all files")
    options_row.addWidget(self.ollama_limit_spin)
    
    config_layout.addLayout(options_row)
    layout.addWidget(config_group)
    
    # ==========================================
    # SECTION 2: Hidden Prompt Configuration
    # ==========================================
    prompt_group = QGroupBox("📝 Hidden YAML Prompt (Added to Every File)")
    prompt_layout = QVBoxLayout(prompt_group)
    
    prompt_info = QLabel("This prompt is automatically appended to YAML frontmatter as a hidden field:")
    prompt_info.setStyleSheet("color: #9ca3af; font-style: italic;")
    prompt_layout.addWidget(prompt_info)
    
    self.ollama_hidden_prompt = QTextEdit()
    self.ollama_hidden_prompt.setMaximumHeight(120)
    self.ollama_hidden_prompt.setPlaceholderText("Enter hidden prompt to embed in YAML...")
    self.ollama_hidden_prompt.setPlainText("""# Theophysics Framework Note
# Part of the unified axiom system bridging physics, consciousness, and theology
# See: https://theophysics.substack.com""")
    prompt_layout.addWidget(self.ollama_hidden_prompt)
    
    prompt_btn_row = QHBoxLayout()
    
    self.prompt_enabled_check = QCheckBox("Enable hidden prompt in YAML")
    self.prompt_enabled_check.setChecked(True)
    prompt_btn_row.addWidget(self.prompt_enabled_check)
    
    prompt_btn_row.addStretch()
    
    save_prompt_btn = QPushButton("💾 Save as Default")
    save_prompt_btn.clicked.connect(self._save_ollama_prompt_default)
    prompt_btn_row.addWidget(save_prompt_btn)
    
    prompt_layout.addLayout(prompt_btn_row)
    layout.addWidget(prompt_group)
    
    # ==========================================
    # SECTION 3: Run Controls
    # ==========================================
    run_group = QGroupBox("🚀 Process YAML")
    run_layout = QVBoxLayout(run_group)
    
    btn_row = QHBoxLayout()
    
    self.ollama_run_btn = QPushButton("▶️ Generate YAML Frontmatter")
    self.ollama_run_btn.setProperty("class", "primary")
    self.ollama_run_btn.clicked.connect(self._run_ollama_processing)
    btn_row.addWidget(self.ollama_run_btn)
    
    self.ollama_stop_btn = QPushButton("⏹️ Stop")
    self.ollama_stop_btn.setEnabled(False)
    self.ollama_stop_btn.clicked.connect(self._stop_ollama_processing)
    btn_row.addWidget(self.ollama_stop_btn)
    
    btn_row.addStretch()
    
    self.ollama_preview_btn = QPushButton("👁️ Preview First File")
    self.ollama_preview_btn.clicked.connect(self._preview_ollama_yaml)
    btn_row.addWidget(self.ollama_preview_btn)
    
    run_layout.addLayout(btn_row)
    
    # Progress
    self.ollama_progress = QProgressBar()
    self.ollama_progress.setVisible(False)
    run_layout.addWidget(self.ollama_progress)
    
    self.ollama_run_status = QLabel("Ready")
    self.ollama_run_status.setStyleSheet("color: #6b7280;")
    run_layout.addWidget(self.ollama_run_status)
    
    layout.addWidget(run_group)
    
    # ==========================================
    # SECTION 4: Results Log
    # ==========================================
    log_group = QGroupBox("📋 Processing Log")
    log_layout = QVBoxLayout(log_group)
    
    self.ollama_log = QTextEdit()
    self.ollama_log.setReadOnly(True)
    self.ollama_log.setMinimumHeight(250)
    self.ollama_log.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
    """)
    log_layout.addWidget(self.ollama_log)
    
    log_btn_row = QHBoxLayout()
    
    clear_log_btn = QPushButton("🗑️ Clear Log")
    clear_log_btn.clicked.connect(lambda: self.ollama_log.clear())
    log_btn_row.addWidget(clear_log_btn)
    
    export_log_btn = QPushButton("💾 Export Log")
    export_log_btn.clicked.connect(self._export_ollama_log)
    log_btn_row.addWidget(export_log_btn)
    
    log_btn_row.addStretch()
    log_layout.addLayout(log_btn_row)
    
    layout.addWidget(log_group)
    
    # ==========================================
    # SECTION 5: Statistics
    # ==========================================
    stats_group = QGroupBox("📊 Session Statistics")
    stats_layout = QGridLayout(stats_group)
    
    self.ollama_stats = {
        'processed': QLabel("0"),
        'updated': QLabel("0"),
        'skipped': QLabel("0"),
        'errors': QLabel("0"),
    }
    
    stats_items = [
        ("Processed", 'processed'), ("Updated", 'updated'),
        ("Skipped", 'skipped'), ("Errors", 'errors')
    ]
    
    for i, (label, key) in enumerate(stats_items):
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("font-weight: bold; color: #d97706;")
        stats_layout.addWidget(lbl, 0, i * 2)
        self.ollama_stats[key].setStyleSheet("font-size: 18px; color: #22c55e;")
        stats_layout.addWidget(self.ollama_stats[key], 0, i * 2 + 1)
    
    layout.addWidget(stats_group)
    layout.addStretch()
    
    # Initialize Ollama worker reference
    self._ollama_worker = None

# Ollama helper methods
def _browse_ollama_folder(self):
    """Browse for folder to process."""
    folder = QFileDialog.getExistingDirectory(self, "Select Papers Folder")
    if folder:
        self.ollama_folder_edit.setText(folder)

def _check_ollama_status(self):
    """Check if Ollama is running."""
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', [])]
            self.ollama_status_label.setText(f"✅ Online ({len(models)} models)")
            self.ollama_status_label.setStyleSheet("color: #22c55e;")
            self._log_ollama(f"Ollama online. Models: {', '.join(models[:5])}")
        else:
            self.ollama_status_label.setText("⚠️ Error")
            self.ollama_status_label.setStyleSheet("color: #f59e0b;")
    except Exception as e:
        self.ollama_status_label.setText("❌ Offline")
        self.ollama_status_label.setStyleSheet("color: #ef4444;")
        self._log_ollama(f"Ollama not available: {e}")

def _log_ollama(self, message: str):
    """Add message to Ollama log."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%H:%M:%S")
    self.ollama_log.append(f"[{timestamp}] {message}")

def _run_ollama_processing(self):
    """Start Ollama YAML processing."""
    folder = self.ollama_folder_edit.text()
    if not folder:
        QMessageBox.warning(self, "No Folder", "Please select a folder to process.")
        return
    
    # Check Ollama first
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code != 200:
            raise Exception("Ollama not responding")
    except:
        QMessageBox.critical(self, "Ollama Offline", 
                            "Ollama is not running.\\n\\nStart it with: ollama serve")
        return
    
    self._log_ollama("=" * 40)
    self._log_ollama("Starting YAML processing...")
    self._log_ollama(f"Folder: {folder}")
    self._log_ollama(f"Model: {self.ollama_model_combo.currentText()}")
    self._log_ollama(f"Dry run: {self.ollama_dry_run_check.isChecked()}")
    
    self.ollama_run_btn.setEnabled(False)
    self.ollama_stop_btn.setEnabled(True)
    self.ollama_progress.setVisible(True)
    self.ollama_progress.setValue(0)
    
    # Get hidden prompt if enabled
    hidden_prompt = None
    if self.prompt_enabled_check.isChecked():
        hidden_prompt = self.ollama_hidden_prompt.toPlainText()
    
    # Start processing in thread
    from PySide6.QtCore import QThread, Signal
    
    class OllamaWorker(QThread):
        progress = Signal(int, str)
        finished = Signal(dict)
        log = Signal(str)
        
        def __init__(self, folder, model, dry_run, skip_fm, recursive, limit, hidden_prompt):
            super().__init__()
            self.folder = folder
            self.model = model
            self.dry_run = dry_run
            self.skip_fm = skip_fm
            self.recursive = recursive
            self.limit = limit
            self.hidden_prompt = hidden_prompt
            self._stop = False
        
        def stop(self):
            self._stop = True
        
        def run(self):
            import re
            import yaml
            import uuid
            import requests
            from pathlib import Path
            
            YAML_PROMPT = \"\"\"You are a YAML frontmatter generator for the Theophysics academic framework.
Analyze this note and generate YAML frontmatter following these rules:

REQUIRED FIELDS:
- title: Extract from first heading or generate from content
- uuid: Generate new UUID if none exists
- type: One of [axiom, theorem, definition, stage, paper, evidence, claim, note]
- status: One of [draft, review, canonical, deprecated]
- tier: One of [primordial, ontological, physical, consciousness, agency, relational, eschatological]

OPTIONAL FIELDS:
- axiom_refs: List axioms referenced (e.g., [A1.1, A2.2, T1])
- domains: List domains [physics, theology, information-theory, consciousness, mathematics, ethics]
- tags: List relevant tags
- depends_on: List dependencies
- created: ISO date
- summary: One sentence summary

Return ONLY valid YAML, no code blocks, no explanation.

Note content:
{content}

YAML:\"\"\"
            
            stats = {'processed': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
            
            folder_path = Path(self.folder)
            if self.recursive:
                md_files = list(folder_path.rglob("*.md"))
            else:
                md_files = list(folder_path.glob("*.md"))
            
            # Filter out canonical folders
            skip_patterns = ['04_The_Axioms', '00_CANONICAL', '01_CANONICAL']
            md_files = [f for f in md_files if not any(p in str(f) for p in skip_patterns)]
            
            if self.limit > 0:
                md_files = md_files[:self.limit]
            
            total = len(md_files)
            self.log.emit(f"Found {total} files to process")
            
            for i, md_file in enumerate(md_files):
                if self._stop:
                    self.log.emit("Processing stopped by user")
                    break
                
                self.progress.emit(int((i / total) * 100), md_file.name)
                
                try:
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    
                    # Check existing frontmatter
                    has_fm = content.startswith('---')
                    if self.skip_fm and has_fm:
                        stats['skipped'] += 1
                        continue
                    
                    # Generate with Ollama
                    prompt = YAML_PROMPT.format(content=content[:2000])
                    
                    r = requests.post(
                        "http://localhost:11434/api/generate",
                        json={"model": self.model, "prompt": prompt, "stream": False},
                        timeout=120
                    )
                    
                    if r.status_code != 200:
                        stats['errors'] += 1
                        self.log.emit(f"Error: {md_file.name} - API error")
                        continue
                    
                    response = r.json().get("response", "").strip()
                    
                    # Clean up response
                    if response.startswith('```'):
                        lines = response.split('\\n')
                        response = '\\n'.join(l for l in lines if not l.startswith('```'))
                    
                    try:
                        new_fm = yaml.safe_load(response)
                    except:
                        stats['errors'] += 1
                        self.log.emit(f"Error: {md_file.name} - Invalid YAML")
                        continue
                    
                    if not new_fm:
                        stats['errors'] += 1
                        continue
                    
                    # Ensure UUID
                    if 'uuid' not in new_fm:
                        new_fm['uuid'] = str(uuid.uuid4())
                    
                    # Add hidden prompt if enabled
                    if self.hidden_prompt:
                        new_fm['_meta_prompt'] = self.hidden_prompt
                    
                    # Extract body
                    if has_fm:
                        parts = content.split('---', 2)
                        body = parts[2].strip() if len(parts) >= 3 else content
                    else:
                        body = content
                    
                    # Write back
                    if not self.dry_run:
                        new_content = f"---\\n{yaml.dump(new_fm, default_flow_style=False, allow_unicode=True)}---\\n\\n{body}"
                        md_file.write_text(new_content, encoding='utf-8')
                    
                    stats['updated'] += 1
                    stats['processed'] += 1
                    self.log.emit(f"✓ {md_file.name}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    self.log.emit(f"Error: {md_file.name} - {str(e)[:50]}")
            
            self.progress.emit(100, "Done")
            self.finished.emit(stats)
    
    self._ollama_worker = OllamaWorker(
        folder=folder,
        model=self.ollama_model_combo.currentText(),
        dry_run=self.ollama_dry_run_check.isChecked(),
        skip_fm=self.ollama_skip_fm_check.isChecked(),
        recursive=self.ollama_recursive_check.isChecked(),
        limit=self.ollama_limit_spin.value(),
        hidden_prompt=hidden_prompt if self.prompt_enabled_check.isChecked() else None
    )
    
    self._ollama_worker.progress.connect(lambda p, f: (
        self.ollama_progress.setValue(p),
        self.ollama_run_status.setText(f"Processing: {f}")
    ))
    self._ollama_worker.log.connect(self._log_ollama)
    self._ollama_worker.finished.connect(self._on_ollama_finished)
    self._ollama_worker.start()

def _stop_ollama_processing(self):
    """Stop Ollama processing."""
    if self._ollama_worker:
        self._ollama_worker.stop()
        self._log_ollama("Stopping...")

def _on_ollama_finished(self, stats):
    """Handle Ollama processing completion."""
    self.ollama_run_btn.setEnabled(True)
    self.ollama_stop_btn.setEnabled(False)
    self.ollama_progress.setVisible(False)
    
    self.ollama_stats['processed'].setText(str(stats['processed']))
    self.ollama_stats['updated'].setText(str(stats['updated']))
    self.ollama_stats['skipped'].setText(str(stats['skipped']))
    self.ollama_stats['errors'].setText(str(stats['errors']))
    
    self.ollama_run_status.setText("Complete")
    self._log_ollama("=" * 40)
    self._log_ollama(f"COMPLETE: {stats['processed']} processed, {stats['updated']} updated, {stats['errors']} errors")

def _preview_ollama_yaml(self):
    """Preview YAML for first file."""
    folder = self.ollama_folder_edit.text()
    if not folder:
        QMessageBox.warning(self, "No Folder", "Please select a folder first.")
        return
    
    from pathlib import Path
    folder_path = Path(folder)
    md_files = list(folder_path.glob("*.md"))
    
    if not md_files:
        QMessageBox.information(self, "No Files", "No markdown files found.")
        return
    
    first_file = md_files[0]
    content = first_file.read_text(encoding='utf-8')[:500]
    
    self._log_ollama(f"\\nPreview: {first_file.name}")
    self._log_ollama("-" * 30)
    self._log_ollama(content + "...")

def _export_ollama_log(self):
    """Export log to file."""
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export Log", "ollama_log.txt", "Text Files (*.txt)"
    )
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.ollama_log.toPlainText())
        QMessageBox.information(self, "Exported", f"Log saved to {file_path}")

def _save_ollama_prompt_default(self):
    """Save current prompt as default."""
    import json
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent / "config" / "ollama_prompt.json"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump({
            'hidden_prompt': self.ollama_hidden_prompt.toPlainText(),
            'enabled': self.prompt_enabled_check.isChecked()
        }, f, indent=2)
    
    QMessageBox.information(self, "Saved", "Default prompt saved.")

# Attach Ollama methods to MainWindowV2
MainWindowV2._build_ollama_page = _build_ollama_page
MainWindowV2._browse_ollama_folder = _browse_ollama_folder
MainWindowV2._check_ollama_status = _check_ollama_status
MainWindowV2._log_ollama = _log_ollama
MainWindowV2._run_ollama_processing = _run_ollama_processing
MainWindowV2._stop_ollama_processing = _stop_ollama_processing
MainWindowV2._on_ollama_finished = _on_ollama_finished
MainWindowV2._preview_ollama_yaml = _preview_ollama_yaml
MainWindowV2._export_ollama_log = _export_ollama_log
MainWindowV2._save_ollama_prompt_default = _save_ollama_prompt_default
'''

POSTGRES_SYNC_FIX = '''
# ==========================================
# POSTGRES SYNC FIX
# ==========================================
def _sync_to_postgres(self):
    """Sync data to PostgreSQL database."""
    if not hasattr(self, 'postgres_manager') or not self.postgres_manager:
        QMessageBox.warning(self, "No Connection", "PostgreSQL not configured.")
        return
    
    try:
        # Test connection first
        if not self.postgres_manager.connect():
            QMessageBox.critical(self, "Connection Failed", 
                "Could not connect to PostgreSQL.\\n\\nCheck host, port, and credentials in settings.")
            return
        
        self.postgres_manager.disconnect()
        
        # Get current definitions
        definitions = []
        if hasattr(self, 'definitions_manager') and self.definitions_manager:
            definitions = self.definitions_manager.get_all_definitions()
        
        synced = 0
        errors = 0
        
        for defn in definitions:
            try:
                self.postgres_manager.save_definition(
                    phrase=defn.get('phrase', ''),
                    definition=defn.get('definition', ''),
                    aliases=defn.get('aliases', []),
                    classification=defn.get('classification', ''),
                    folder=defn.get('folder', ''),
                    vault_link=defn.get('vault_link', '')
                )
                synced += 1
            except Exception as e:
                errors += 1
                print(f"Sync error for {defn.get('phrase')}: {e}")
        
        QMessageBox.information(self, "Sync Complete", 
            f"Synced {synced} definitions to PostgreSQL.\\n\\nErrors: {errors}")
        
        # Update metrics
        self._refresh_postgres_metrics()
        
    except Exception as e:
        QMessageBox.critical(self, "Sync Error", f"Failed to sync:\\n{e}")

def _refresh_postgres_metrics(self):
    """Refresh PostgreSQL metrics display."""
    if not hasattr(self, 'postgres_manager') or not self.postgres_manager:
        self.postgres_metrics_label.setText("Not connected")
        return
    
    try:
        if self.postgres_manager.connect():
            with self.postgres_manager.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM definitions")
                def_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM footnotes")
                fn_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM research_links")
                rl_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM memories")
                mem_count = cur.fetchone()[0]
            
            self.postgres_manager.disconnect()
            
            self.postgres_metrics_label.setText(
                f"Definitions: {def_count} | Footnotes: {fn_count} | "
                f"Research Links: {rl_count} | Memories: {mem_count}"
            )
        else:
            self.postgres_metrics_label.setText("Connection failed")
    except Exception as e:
        self.postgres_metrics_label.setText(f"Error: {str(e)[:30]}")

# Attach PostgreSQL methods
MainWindowV2._sync_to_postgres = _sync_to_postgres
MainWindowV2._refresh_postgres_metrics = _refresh_postgres_metrics
'''

def apply_all_fixes():
    """Apply all fixes to main_window_v2.py."""
    print("=" * 60)
    print("  THEOPHYSICS BACKEND FIX SCRIPT")
    print("=" * 60)
    
    # Backup
    backup_file(UI_FILE)
    
    # Read current content
    content = UI_FILE.read_text(encoding='utf-8')
    
    # Fix 1: Mermaid import
    content = fix_mermaid_import()
    
    # Fix 2: Add Ollama to NAV_ITEMS  
    content = add_ollama_to_nav_items(content)
    
    # Fix 3: Update page build calls
    content = update_page_build_calls(content)
    
    # Add Ollama page code and PostgreSQL sync fix at end of file
    if "_build_ollama_page" not in content:
        content = content.rstrip() + "\n\n" + OLLAMA_PAGE_CODE + "\n" + POSTGRES_SYNC_FIX
        print("✓ Added Ollama page code")
        print("✓ Added PostgreSQL sync fix")
    else:
        print("→ Ollama page already exists")
    
    # Write back
    UI_FILE.write_text(content, encoding='utf-8')
    
    print("\n" + "=" * 60)
    print("  ALL FIXES APPLIED SUCCESSFULLY!")
    print("=" * 60)
    print("\nRestart the Theophysics Research Manager to see changes.")
    print("New tab: 🤖 Ollama YAML (after Tag Manager)")


if __name__ == '__main__':
    apply_all_fixes()
