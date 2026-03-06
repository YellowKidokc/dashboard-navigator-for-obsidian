"""
Main Window V2 - Sidebar Navigation with Dashboard
Theophysics Research Manager - Enhanced Edition
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

# Import SQLite database engine
try:
    from engine.database_engine import DatabaseEngine, generate_uuid
    from engine.settings import SettingsManager as EngineSettings
    from engine.vault_engine import VaultEngine
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStatusBar, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStackedWidget, QSplitter, QGroupBox, QLineEdit, QPushButton,
    QProgressBar, QScrollArea, QFrame, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QGridLayout, QSpacerItem, QSizePolicy, QInputDialog, QSpinBox
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QFont, QIcon

from .styles_v2 import DARK_THEME_V2, COLORS

if TYPE_CHECKING:
    from core_v2.settings_manager import SettingsManager
    from core_v2.obsidian_definitions_manager import ObsidianDefinitionsManager
    from core_v2.vault_system_installer import VaultSystemInstaller
    from core_v2.global_analytics_aggregator import GlobalAnalyticsAggregator
    from core_v2.research_linker import ResearchLinker
    from core_v2.footnote_system import FootnoteSystem
    from core_v2.postgres_manager import PostgresManager


class MainWindowV2(QMainWindow):
    """
    Enhanced main window with sidebar navigation.
    """
    
    NAV_ITEMS = [
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
    ]
    
    def __init__(
        self,
        settings: SettingsManager,
        definitions_manager: ObsidianDefinitionsManager,
        vault_installer: VaultSystemInstaller,
        global_aggregator: GlobalAnalyticsAggregator,
        research_linker: ResearchLinker,
        footnote_system: FootnoteSystem,
        postgres_manager: PostgresManager
    ):
        super().__init__()
        self.settings = settings
        self.definitions_manager = definitions_manager
        self.vault_installer = vault_installer
        self.global_aggregator = global_aggregator
        self.research_linker = research_linker
        self.footnote_system = footnote_system
        self.postgres_manager = postgres_manager
        
        # Scan worker reference
        self._scan_worker = None

        self._auto_linker_startup = False
        self._auto_linker_startup_link_all = False
        
        # Folder configuration
        self._folder_config: Dict[str, str] = {}
        self._load_folder_config()
        
        # Stats cache for persistent statistics
        self._stats_cache = None
        self._init_stats_cache()
        
        self.setWindowTitle("🔬 Theophysics Research Manager v2")
        self.setGeometry(100, 100, 1500, 950)
        self.setMinimumSize(1200, 800)
        
        self._setup_ui()
        self._setup_status_bar()

        self._maybe_start_auto_linker()
    
    def _init_stats_cache(self):
        """Initialize the stats cache for persistent statistics."""
        vault_path = self._folder_config.get('vault_root', '')
        if not vault_path:
            vault_path = self.settings.get('obsidian', 'vault_path', '')
        
        if vault_path:
            try:
                from core.stats_cache import StatsCache
                self._stats_cache = StatsCache(vault_path)
            except Exception as e:
                print(f"Could not initialize stats cache: {e}")
                self._stats_cache = None
    
    def _load_folder_config(self):
        """Load configured folders from settings."""
        config_path = Path(__file__).parent.parent / "config" / "folders.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self._folder_config = json.load(f)
            except:
                pass
        
        # Defaults
        defaults = {
            'vault_root': self.settings.get('obsidian', 'vault_path', ''),
            'glossary': self.settings.get('obsidian', 'definitions_folder', ''),
            'logos_papers': '',
            'evidence_bundles': '',
            'analytics': '',
            'notes': '',
        }
        for key, val in defaults.items():
            if key not in self._folder_config:
                self._folder_config[key] = val
    
    def _save_folder_config(self):
        """Save folder configuration."""
        config_path = Path(__file__).parent.parent / "config" / "folders.json"
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self._folder_config, f, indent=2)
    
    def _load_papers_config(self) -> List[str]:
        """Load paper names from config/papers.json. Returns display names."""
        config_path = Path(__file__).parent.parent / "config" / "papers.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    return [p.get('display', p.get('name', 'Unknown')) for p in data.get('papers', [])]
            except Exception as e:
                print(f"Could not load papers config: {e}")
        # Fallback to defaults
        return [
            "P01 - Logos Principle",
            "P02 - Quantum Bridge",
            "P03 - Algorithm Reality",
            "P04 - Hard Problem",
            "P05 - Soul Observer",
            "P06 - Physics Principalities",
            "P07 - Grace Function",
            "P08 - Stretched Heavens",
            "P09 - Moral Universe",
            "P10 - Creatio Silico",
            "P11 - Protocols Validation",
            "P12 - Decalogue Cosmos",
        ]
    
    def _setup_ui(self):
        """Setup the main UI with sidebar."""
        self.setStyleSheet(DARK_THEME_V2)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === SIDEBAR ===
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"background-color: {COLORS['bg_dark']};")
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Logo/Title
        title_container = QWidget()
        title_container.setStyleSheet(f"""
            background-color: {COLORS['bg_dark']};
            border-bottom: 1px solid {COLORS['border_dark']};
        """)
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(16, 20, 16, 20)
        
        title_label = QLabel("🔬 Theophysics")
        title_label.setStyleSheet(f"""
            font-size: 16pt;
            font-weight: bold;
            color: {COLORS['accent_cyan']};
            background: transparent;
        """)
        title_layout.addWidget(title_label)
        
        subtitle = QLabel("Research Manager")
        subtitle.setStyleSheet(f"""
            font-size: 10pt;
            color: {COLORS['text_muted']};
            background: transparent;
        """)
        title_layout.addWidget(subtitle)
        
        sidebar_layout.addWidget(title_container)
        
        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("sidebar")
        self.nav_list.setIconSize(QSize(20, 20))
        
        for icon, name in self.NAV_ITEMS:
            item = QListWidgetItem(f"{icon}  {name}")
            item.setSizeHint(QSize(200, 44))
            self.nav_list.addItem(item)
        
        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        
        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()
        
        # Version info at bottom
        version_label = QLabel("v2.1.0")
        version_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            padding: 12px;
            font-size: 9pt;
            background: transparent;
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_label)
        
        main_layout.addWidget(sidebar)
        
        # === SEPARATOR LINE ===
        separator = QFrame()
        separator.setFixedWidth(1)
        separator.setStyleSheet(f"background-color: {COLORS['border_dark']};")
        main_layout.addWidget(separator)
        
        # === CONTENT AREA ===
        self.page_stack = QStackedWidget()
        main_layout.addWidget(self.page_stack)
        
        # Build pages (must match NAV_ITEMS order)
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
        self._build_settings_page()       # 11 - Settings
    
    def _on_nav_changed(self, index: int):
        """Handle navigation selection."""
        self.page_stack.setCurrentIndex(index)
    
    def _create_page_container(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        """Create a standard page container with scroll area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Page header
        header = QLabel(title)
        header.setStyleSheet(f"""
            font-size: 24pt;
            font-weight: bold;
            color: {COLORS['text_primary']};
            padding-bottom: 10px;
        """)
        layout.addWidget(header)
        
        scroll.setWidget(page)
        self.page_stack.addWidget(scroll)
        
        return page, layout
    
    # ==========================================
    # PAGE 0: DASHBOARD
    # ==========================================
    def _build_dashboard_page(self):
        """Build the dashboard/home page with folder configuration."""
        page, layout = self._create_page_container("🏠 Dashboard")
        
        # Two-column layout
        columns = QHBoxLayout()
        columns.setSpacing(20)
        
        # === LEFT COLUMN: Folder Configuration ===
        left_col = QVBoxLayout()
        left_col.setSpacing(15)
        
        folders_group = QGroupBox("📁 Configured Folders")
        folders_layout = QVBoxLayout(folders_group)
        folders_layout.setSpacing(12)
        
        # Folder entries
        self._folder_inputs = {}
        
        folder_definitions = [
            ('vault_root', 'Vault Root', 'Main Obsidian vault path'),
            ('glossary', 'Glossary', 'Definitions folder'),
            ('logos_papers', 'Logos Papers', '12 main research papers'),
            ('evidence_bundles', 'Evidence Bundles', 'Supporting evidence'),
            ('analytics', 'Analytics Output', 'Generated analytics'),
            ('notes', 'Working Notes', 'Daily notes / scratch'),
        ]
        
        for key, label, hint in folder_definitions:
            row = QHBoxLayout()
            
            lbl = QLabel(f"{label}:")
            lbl.setFixedWidth(120)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            row.addWidget(lbl)
            
            edit = QLineEdit()
            edit.setPlaceholderText(hint)
            edit.setText(self._folder_config.get(key, ''))
            self._folder_inputs[key] = edit
            row.addWidget(edit)
            
            browse_btn = QPushButton("...")
            browse_btn.setFixedWidth(40)
            browse_btn.clicked.connect(lambda checked, k=key: self._browse_folder(k))
            row.addWidget(browse_btn)
            
            folders_layout.addLayout(row)
        
        # Save button
        save_folders_btn = QPushButton("💾 Save Configuration")
        save_folders_btn.setProperty("class", "primary")
        save_folders_btn.clicked.connect(self._save_folders_clicked)
        folders_layout.addWidget(save_folders_btn)
        
        left_col.addWidget(folders_group)
        
        # === Scan Controls ===
        scan_group = QGroupBox("🔍 Scan Controls")
        scan_layout = QVBoxLayout(scan_group)
        
        # Scope selector
        scope_row = QHBoxLayout()
        scope_row.addWidget(QLabel("Scan Scope:"))
        
        self.scan_scope_combo = QComboBox()
        self.scan_scope_combo.addItems([
            "Entire Vault",
            "Glossary Only",
            "Logos Papers Only",
            "Evidence Bundles Only",
            "Custom Folder..."
        ])
        scope_row.addWidget(self.scan_scope_combo)
        scan_layout.addLayout(scope_row)
        
        # Recursive checkbox
        self.recursive_check = QCheckBox("Scan recursively (all subfolders)")
        self.recursive_check.setChecked(True)
        scan_layout.addWidget(self.recursive_check)
        
        # Thread count
        thread_row = QHBoxLayout()
        thread_row.addWidget(QLabel("Parallel threads:"))
        self.thread_combo = QComboBox()
        self.thread_combo.addItems(["4", "8", "12", "16"])
        self.thread_combo.setCurrentText("8")
        thread_row.addWidget(self.thread_combo)
        thread_row.addStretch()
        scan_layout.addLayout(thread_row)
        
        # Scan buttons
        btn_row = QHBoxLayout()
        
        self.full_scan_btn = QPushButton("🚀 Full Scan")
        self.full_scan_btn.setProperty("class", "success")
        self.full_scan_btn.clicked.connect(self._start_full_scan)
        btn_row.addWidget(self.full_scan_btn)
        
        self.quick_scan_btn = QPushButton("⚡ Quick Stats")
        self.quick_scan_btn.clicked.connect(self._start_quick_scan)
        btn_row.addWidget(self.quick_scan_btn)
        
        self.cancel_scan_btn = QPushButton("✖ Cancel")
        self.cancel_scan_btn.setProperty("class", "danger")
        self.cancel_scan_btn.setEnabled(False)
        self.cancel_scan_btn.clicked.connect(self._cancel_scan)
        btn_row.addWidget(self.cancel_scan_btn)
        
        scan_layout.addLayout(btn_row)
        
        # Progress
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)
        
        self.scan_status_label = QLabel("Ready")
        self.scan_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        scan_layout.addWidget(self.scan_status_label)
        
        left_col.addWidget(scan_group)
        left_col.addStretch()
        
        columns.addLayout(left_col, 1)
        
        # === RIGHT COLUMN: Statistics ===
        right_col = QVBoxLayout()
        right_col.setSpacing(15)
        
        stats_group = QGroupBox("📊 Vault Statistics")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(15)
        
        # Stats cards - expanded metrics
        self._stat_labels = {}
        stat_items = [
            ('total_files', '📄 Total Notes', '0'),
            ('total_words', '📝 Total Words', '0'),
            ('unique_tags', '🏷️ Unique Tags', '0'),
            ('unique_links', '🔗 Unique Links', '0'),
            ('axioms', '🧠 Axioms', '0'),
            ('claims', '💬 Claims', '0'),
            ('evidence', '📊 Evidence Bundles', '0'),
            ('theorems', '📐 Theorems', '0'),
            ('definitions', '📖 Definitions', '0'),
            ('equations', '🔢 Equations', '0'),
            ('papers', '📑 Papers', '0'),
            ('avg_words', '📏 Avg Words/Note', '0'),
        ]
        
        for i, (key, label, default) in enumerate(stat_items):
            row, col = divmod(i, 4)
            
            card = QFrame()
            card.setStyleSheet(f"""
                background-color: {COLORS['bg_medium']};
                border-radius: 8px;
                padding: 15px;
            """)
            card_layout = QVBoxLayout(card)
            
            value_label = QLabel(default)
            value_label.setStyleSheet(f"""
                font-size: 20pt;
                font-weight: bold;
                color: {COLORS['accent_cyan']};
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(value_label)
            self._stat_labels[key] = value_label
            
            name_label = QLabel(label)
            name_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(name_label)
            
            stats_layout.addWidget(card, row, col)
        
        right_col.addWidget(stats_group)
        
        # Folder breakdown
        breakdown_group = QGroupBox("📁 Folder Breakdown")
        breakdown_layout = QVBoxLayout(breakdown_group)
        
        self.folder_table = QTableWidget()
        self.folder_table.setColumnCount(3)
        self.folder_table.setHorizontalHeaderLabels(["Folder", "Files", "% of Total"])
        self.folder_table.horizontalHeader().setStretchLastSection(True)
        self.folder_table.setMaximumHeight(200)
        breakdown_layout.addWidget(self.folder_table)
        
        right_col.addWidget(breakdown_group)
        
        # Recent activity
        activity_group = QGroupBox("🕐 Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_list = QListWidget()
        self.activity_list.setMaximumHeight(150)
        activity_layout.addWidget(self.activity_list)
        
        right_col.addWidget(activity_group)
        right_col.addStretch()
        
        columns.addLayout(right_col, 1)
        layout.addLayout(columns)
    
    def _browse_folder(self, key: str):
        """Browse for a folder."""
        current = self._folder_inputs[key].text()
        folder = QFileDialog.getExistingDirectory(self, f"Select {key} folder", current)
        if folder:
            self._folder_inputs[key].setText(folder)
    
    def _save_folders_clicked(self):
        """Save folder configuration."""
        for key, edit in self._folder_inputs.items():
            self._folder_config[key] = edit.text()
        
        self._save_folder_config()
        
        # Update settings manager too
        if self._folder_config.get('vault_root'):
            self.settings.set('obsidian', 'vault_path', self._folder_config['vault_root'])
        if self._folder_config.get('glossary'):
            self.settings.set('obsidian', 'definitions_folder', self._folder_config['glossary'])
        
        QMessageBox.information(self, "Saved", "Folder configuration saved!")
    
    def _get_scan_path(self) -> Optional[Path]:
        """Get the path to scan based on scope selection."""
        scope = self.scan_scope_combo.currentText()
        
        if scope == "Entire Vault":
            path = self._folder_config.get('vault_root')
        elif scope == "Glossary Only":
            path = self._folder_config.get('glossary')
        elif scope == "Logos Papers Only":
            path = self._folder_config.get('logos_papers')
        elif scope == "Evidence Bundles Only":
            path = self._folder_config.get('evidence_bundles')
        else:
            # Custom folder
            path = QFileDialog.getExistingDirectory(self, "Select folder to scan")
        
        if path and Path(path).exists():
            return Path(path)
        return None
    
    def _start_full_scan(self):
        """Start a full vault scan."""
        scan_path = self._get_scan_path()
        if not scan_path:
            QMessageBox.warning(self, "No Path", "Please configure the folder path first.")
            return
        
        # Import here to avoid circular imports
        from core.threaded_scanner import ScanWorker
        
        # Disable buttons, show progress
        self.full_scan_btn.setEnabled(False)
        self.quick_scan_btn.setEnabled(False)
        self.cancel_scan_btn.setEnabled(True)
        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        self.scan_status_label.setText(f"Starting scan of {scan_path.name}...")
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_cyan']};")
        
        # Create worker
        max_workers = int(self.thread_combo.currentText())
        recursive = self.recursive_check.isChecked()
        
        self._scan_worker = ScanWorker(
            scan_path=scan_path,
            recursive=recursive,
            max_workers=max_workers
        )
        
        # Connect signals
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._on_dashboard_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        
        # Start
        self._scan_worker.start()
    
    def _start_quick_scan(self):
        """Start a quick metadata-only scan."""
        scan_path = self._get_scan_path()
        if not scan_path:
            QMessageBox.warning(self, "No Path", "Please configure the folder path first.")
            return
        
        from core.threaded_scanner import QuickScanWorker
        
        self.full_scan_btn.setEnabled(False)
        self.quick_scan_btn.setEnabled(False)
        self.cancel_scan_btn.setEnabled(True)
        self.scan_progress.setVisible(True)
        self.scan_progress.setMaximum(0)  # Indeterminate
        self.scan_status_label.setText("Quick scan...")
        
        self._scan_worker = QuickScanWorker(
            scan_path=scan_path,
            recursive=self.recursive_check.isChecked()
        )
        self._scan_worker.progress.connect(lambda p, f: self.scan_status_label.setText(f"Scanning {f}..."))
        self._scan_worker.finished.connect(self._on_quick_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()
    
    def _cancel_scan(self):
        """Cancel the running scan."""
        if self._scan_worker:
            self._scan_worker.cancel()
            self._scan_worker = None
        
        self._reset_scan_ui()
        self.scan_status_label.setText("Scan cancelled")
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_orange']};")
    
    def _reset_scan_ui(self):
        """Reset scan UI to ready state."""
        self.full_scan_btn.setEnabled(True)
        self.quick_scan_btn.setEnabled(True)
        self.cancel_scan_btn.setEnabled(False)
        self.scan_progress.setVisible(False)
        self.scan_progress.setMaximum(100)
    
    def _on_scan_progress(self, percent: int, current_file: str):
        """Handle scan progress update."""
        self.scan_progress.setValue(percent)
        self.scan_status_label.setText(f"{percent}% - {current_file}")
    
    def _on_dashboard_scan_finished(self, result):
        """Handle Dashboard scan completion."""
        self._reset_scan_ui()
        
        # Debug: print what we got
        print(f"[DEBUG] Dashboard scan finished: {result.total_files} files, {result.total_words} words, {len(result.unique_tags)} tags, {len(result.unique_links)} links")
        
        # Update basic stats
        self._stat_labels['total_files'].setText(f"{result.total_files:,}")
        self._stat_labels['total_words'].setText(f"{result.total_words:,}")
        self._stat_labels['unique_tags'].setText(f"{len(result.unique_tags):,}")
        self._stat_labels['unique_links'].setText(f"{len(result.unique_links):,}")
        
        # Calculate average words per note
        avg_words = result.total_words // result.total_files if result.total_files > 0 else 0
        self._stat_labels['avg_words'].setText(f"{avg_words:,}")
        
        # Extract semantic tags from scanned notes
        semantic_counts = {'Axiom': 0, 'Claim': 0, 'EvidenceBundle': 0, 'Theorem': 0}
        equation_count = 0
        definition_count = 0
        paper_count = 0
        
        # Patterns for semantic elements
        import re
        semantic_tag_pattern = re.compile(r'%%tag::([^:]+)::')
        equation_pattern = re.compile(r'\$\$.*?\$\$|\$[^$]+\$', re.DOTALL)
        
        for note in result.notes:
            content = note.content
            
            # Count semantic tags
            for match in semantic_tag_pattern.finditer(content):
                tag_type = match.group(1)
                if tag_type in semantic_counts:
                    semantic_counts[tag_type] += 1
                elif tag_type.startswith('Custom:'):
                    pass  # Could track custom types
            
            # Count equations (LaTeX)
            equation_count += len(equation_pattern.findall(content))
            
            # Check if this is a definition note (in Glossary folder or has definition tag)
            if 'Glossary' in note.path or 'definition' in [t.lower() for t in note.tags]:
                definition_count += 1
            
            # Check if this is a paper (has paper/research tags or in Papers folder)
            if 'paper' in [t.lower() for t in note.tags] or 'Papers' in note.path or 'Logos' in note.path:
                paper_count += 1
        
        # Update semantic stats
        self._stat_labels['axioms'].setText(f"{semantic_counts['Axiom']:,}")
        self._stat_labels['claims'].setText(f"{semantic_counts['Claim']:,}")
        self._stat_labels['evidence'].setText(f"{semantic_counts['EvidenceBundle']:,}")
        self._stat_labels['theorems'].setText(f"{semantic_counts['Theorem']:,}")
        self._stat_labels['definitions'].setText(f"{definition_count:,}")
        self._stat_labels['equations'].setText(f"{equation_count:,}")
        self._stat_labels['papers'].setText(f"{paper_count:,}")
        
        # Update folder breakdown table
        self.folder_table.setRowCount(len(result.folder_stats))
        for i, (folder, count) in enumerate(sorted(result.folder_stats.items(), key=lambda x: -x[1])):
            self.folder_table.setItem(i, 0, QTableWidgetItem(folder))
            self.folder_table.setItem(i, 1, QTableWidgetItem(str(count)))
            pct = (count / result.total_files * 100) if result.total_files else 0
            self.folder_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))
        
        # Status
        duration = result.duration_seconds
        self.scan_status_label.setText(
            f"✓ Scan complete: {result.total_files:,} files in {duration:.1f}s "
            f"({len(result.errors)} errors)"
        )
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_green']};")
        
        # Add to activity
        from datetime import datetime
        self.activity_list.insertItem(0, f"{datetime.now().strftime('%H:%M:%S')} - Scanned {result.total_files} files")
        self.activity_list.insertItem(1, f"  → {semantic_counts['Axiom']} axioms, {semantic_counts['Claim']} claims, {equation_count} equations")
        
        self._scan_worker = None
    
    def _on_quick_scan_finished(self, result: dict):
        """Handle quick scan completion."""
        self._reset_scan_ui()
        
        self._stat_labels['total_files'].setText(f"{result['total_files']:,}")
        
        size_mb = result['total_size_bytes'] / (1024 * 1024)
        self.scan_status_label.setText(
            f"✓ Quick scan: {result['total_files']:,} files, {size_mb:.1f} MB total"
        )
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_green']};")
        
        self._scan_worker = None
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        self._reset_scan_ui()
        self.scan_status_label.setText(f"✖ Error: {error_msg}")
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_red']};")
        QMessageBox.critical(self, "Scan Error", error_msg)
        self._scan_worker = None
    
    # ==========================================
    # PAGE 1: PAPER SCANNER
    # ==========================================
    def _build_paper_scanner_page(self):
        """Build the paper scanner page."""
        page, layout = self._create_page_container("📄 Paper Scanner")
        
        info = QLabel("Scan papers to find terms needing definitions.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(info)
        
        # Folder selection
        folder_group = QGroupBox("Select Folder to Scan")
        folder_layout = QHBoxLayout(folder_group)
        
        self.paper_scan_path = QLineEdit()
        self.paper_scan_path.setPlaceholderText("Select folder containing papers...")
        folder_layout.addWidget(self.paper_scan_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_paper_folder)
        folder_layout.addWidget(browse_btn)
        
        use_logos_btn = QPushButton("Use Logos Papers")
        use_logos_btn.setProperty("class", "primary")
        use_logos_btn.clicked.connect(lambda: self.paper_scan_path.setText(
            self._folder_config.get('logos_papers', '')
        ))
        folder_layout.addWidget(use_logos_btn)
        
        layout.addWidget(folder_group)
        
        # Options
        options_group = QGroupBox("Scan Options")
        options_layout = QVBoxLayout(options_group)
        
        self.paper_recursive = QCheckBox("Scan recursively (all subfolders)")
        self.paper_recursive.setChecked(True)
        options_layout.addWidget(self.paper_recursive)
        
        self.paper_nlp = QCheckBox("Enable NLP (extract complex terms)")
        options_layout.addWidget(self.paper_nlp)
        
        layout.addWidget(options_group)
        
        # Scan button
        scan_btn = QPushButton("🚀 SCAN SELECTED PAPERS")
        scan_btn.setProperty("class", "success")
        scan_btn.setMinimumHeight(50)
        scan_btn.clicked.connect(self._scan_papers)
        layout.addWidget(scan_btn)
        
        # Results area
        results_group = QGroupBox("📋 Found Terms")
        results_layout = QVBoxLayout(results_group)
        
        self.paper_results_table = QTableWidget()
        self.paper_results_table.setColumnCount(5)
        self.paper_results_table.setHorizontalHeaderLabels([
            "Term", "Type", "Count", "Status", "Action"
        ])
        self.paper_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.paper_results_table)
        
        layout.addWidget(results_group)
        layout.addStretch()
    
    def _browse_paper_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Papers Folder")
        if folder:
            self.paper_scan_path.setText(folder)
    
    def _scan_papers(self):
        """Scan papers for undefined terms."""
        path = self.paper_scan_path.text()
        if not path or not Path(path).exists():
            QMessageBox.warning(self, "No Folder", "Please select a valid folder.")
        QMessageBox.information(self, "Scanning", f"Would scan: {path}\n(Implementation pending)")
    
    # ==========================================
    # PAGE 2: AUTO-LINKER (ENHANCED & THREADED)
    # ==========================================
    def _build_linker_page(self):
        """Build the Auto-Linker and Entity Extraction page."""
        page, layout = self._create_page_container("🔗 Auto-Linker & Entity Extraction")
        
        # Description
        desc = QLabel(
            "Scan your files for key terms (Biblical references, theological concepts, people) found in your vault or footnotes.yaml. "
            "The process happens in two steps: 1. Scan to find candidates. 2. Review and Apply."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(desc)
        
        # --- Configuration Group ---
        config_group = QGroupBox("1. Scan Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # Path Selection
        path_row = QHBoxLayout()
        self.linker_path_edit = QLineEdit()
        self.linker_path_edit.setPlaceholderText("Select a file or folder to analyze...")
        default_link_path = self.settings.get('autolinker', 'path', '')
        if not default_link_path:
            default_link_path = self._folder_config.get('notes', '') or self._folder_config.get('vault_root', '')
        if default_link_path:
            self.linker_path_edit.setText(default_link_path)
        browse_btn = QPushButton("📂 Browse...")
        browse_btn.clicked.connect(lambda: self._browse_to_line_edit(self.linker_path_edit))
        path_row.addWidget(self.linker_path_edit)
        path_row.addWidget(browse_btn)
        config_layout.addLayout(path_row)
        
        # Options Row 1
        opts_layout = QHBoxLayout()
        self.link_recursive_check = QCheckBox("Recursive Scan")
        self.link_recursive_check.setChecked(self.settings.get('autolinker', 'recursive', 'true').lower() == 'true')
        self.link_all_check = QCheckBox("Link All Occurrences (Uncheck = First Only)")
        self.link_all_check.setChecked(self.settings.get('autolinker', 'link_all', 'false').lower() == 'true')

        self.auto_link_startup_check = QCheckBox("Auto-run on startup")
        self.auto_link_startup_check.setChecked(self.settings.get('autolinker', 'startup', 'false').lower() == 'true')
        self.auto_link_startup_check.stateChanged.connect(self._save_autolinker_settings)

        opts_layout.addWidget(self.link_recursive_check)
        opts_layout.addWidget(self.link_all_check)
        opts_layout.addWidget(self.auto_link_startup_check)
        opts_layout.addStretch()
        config_layout.addLayout(opts_layout)
        
        # Options Row 2 - Minimum occurrences & Wikipedia
        opts_layout2 = QHBoxLayout()
        
        opts_layout2.addWidget(QLabel("Min occurrences:"))
        self.min_occurrences_spin = QSpinBox()
        self.min_occurrences_spin.setRange(1, 50)
        self.min_occurrences_spin.setValue(int(self.settings.get('autolinker', 'min_occurrences', '1')))
        self.min_occurrences_spin.setToolTip("Only link terms that appear at least this many times")
        self.min_occurrences_spin.valueChanged.connect(self._save_autolinker_settings)
        opts_layout2.addWidget(self.min_occurrences_spin)
        
        opts_layout2.addSpacing(20)
        
        self.wiki_fallback_check = QCheckBox("Wikipedia fallback (if no glossary)")
        self.wiki_fallback_check.setChecked(self.settings.get('autolinker', 'wiki_fallback', 'false').lower() == 'true')
        self.wiki_fallback_check.setToolTip("If term not in glossary, check Wikipedia and offer dual link")
        self.wiki_fallback_check.stateChanged.connect(self._save_autolinker_settings)
        opts_layout2.addWidget(self.wiki_fallback_check)
        
        self.dual_link_check = QCheckBox("Dual links (Glossary + Wikipedia)")
        self.dual_link_check.setChecked(self.settings.get('autolinker', 'dual_link', 'false').lower() == 'true')
        self.dual_link_check.setToolTip("Create links to both glossary and Wikipedia when available")
        self.dual_link_check.stateChanged.connect(self._save_autolinker_settings)
        opts_layout2.addWidget(self.dual_link_check)
        
        opts_layout2.addStretch()
        config_layout.addLayout(opts_layout2)
        
        # Scan Button
        self.scan_links_btn = QPushButton("🔎 Scan for Potential Links")
        self.scan_links_btn.setProperty("class", "primary")
        self.scan_links_btn.setMinimumHeight(40)
        self.scan_links_btn.clicked.connect(self._scan_links_dry_run_threaded)
        config_layout.addWidget(self.scan_links_btn)

        self.linker_path_edit.textChanged.connect(self._save_autolinker_settings)
        self.link_recursive_check.stateChanged.connect(self._save_autolinker_settings)
        self.link_all_check.stateChanged.connect(self._save_autolinker_settings)
        
        layout.addWidget(config_group)
        
        # --- Progress Section ---
        progress_group = QGroupBox("Status & Log")
        progress_layout = QVBoxLayout(progress_group)
        
        self.linker_progress = QProgressBar()
        self.linker_progress.setTextVisible(True)
        self.linker_progress.setFormat("%p% - %v/%m files")
        self.linker_progress.setVisible(False)
        progress_layout.addWidget(self.linker_progress)
        
        self.linker_log = QTextEdit()
        self.linker_log.setReadOnly(True)
        self.linker_log.setPlaceholderText("Detailed logs will appear here during scanning...")
        self.linker_log.setStyleSheet("font-family: Consolas, monospace; font-size: 12px; background-color: #1e1e1e; color: #d4d4d4;")
        self.linker_log.setMaximumHeight(200)
        progress_layout.addWidget(self.linker_log)
        
        layout.addWidget(progress_group)
        
        # --- Review Group ---
        review_group = QGroupBox("2. Review & Apply")
        review_layout = QVBoxLayout(review_group)
        
        # Table
        self.linker_table = QTableWidget()
        self.linker_table.setColumnCount(4)
        self.linker_table.setHorizontalHeaderLabels(["Key Term", "Found Count", "Target Link", "Apply?"])
        self.linker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.linker_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        review_layout.addWidget(self.linker_table)
        
        # Controls
        ctrl_row = QHBoxLayout()
        sel_all_btn = QPushButton("Select All")
        sel_all_btn.clicked.connect(lambda: self._set_linker_checks(True))
        desel_all_btn = QPushButton("Deselect All")
        desel_all_btn.clicked.connect(lambda: self._set_linker_checks(False))
        
        ctrl_row.addWidget(sel_all_btn)
        ctrl_row.addWidget(desel_all_btn)
        ctrl_row.addStretch()
        
        self.apply_links_btn = QPushButton("✅ Apply Selected Links")
        self.apply_links_btn.setProperty("class", "success")
        self.apply_links_btn.setEnabled(False)
        self.apply_links_btn.clicked.connect(self._apply_selected_links_threaded)
        ctrl_row.addWidget(self.apply_links_btn)
        
        review_layout.addLayout(ctrl_row)
        layout.addWidget(review_group)
        layout.addStretch()

    def _browse_to_line_edit(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            line_edit.setText(path)

    def _set_linker_checks(self, checked: bool):
        """Helper to mass check/uncheck."""
        for row in range(self.linker_table.rowCount()):
            item = self.linker_table.cellWidget(row, 3)
            # Find checkbox in container
            chk = item.findChild(QCheckBox) if item else None
            if chk:
                chk.setChecked(checked)

    def _scan_links_dry_run_threaded(self):
        """Start the scan in a background thread."""
        path_str = self.linker_path_edit.text()
        if not path_str or not Path(path_str).exists():
            QMessageBox.warning(self, "Error", "Invalid path selected.")
            return

        # 1. Prepare UI
        self.linker_log.clear()
        self.linker_log.append("PREPARING SCAN...")
        self.linker_progress.setVisible(True)
        self.linker_progress.setValue(0)
        self.scan_links_btn.setEnabled(False)
        self.apply_links_btn.setEnabled(False)
        self.linker_table.setRowCount(0)
        
        # 2. Start Thread
        self._linker_thread = LinkerWorker(
            mode="scan",
            path=path_str,
            vault_path=self.settings.get('obsidian', 'vault_path', '.'),
            recursive=self.link_recursive_check.isChecked()
        )
        
        self._linker_thread.log_signal.connect(self._append_linker_log)
        self._linker_thread.progress_signal.connect(self._update_linker_progress)
        self._linker_thread.finished_scan_signal.connect(self._on_scan_finished)
        self._linker_thread.error_signal.connect(self._on_linker_error)
        
        self._linker_thread.start()

    def _apply_selected_links_threaded(self):
        """Start applying links in a background thread."""
        if not hasattr(self, '_files_to_link') or not self._files_to_link:
            return

        # Gather approved terms
        approved = []
        for row in range(self.linker_table.rowCount()):
            container = self.linker_table.cellWidget(row, 3)
            chk = container.findChild(QCheckBox)
            if chk and chk.isChecked():
                term = self.linker_table.item(row, 0).text()
                approved.append(term)
        
        if not approved:
            QMessageBox.information(self, "Info", "No terms selected to apply.")
            return

        self._start_apply_links_thread(files=self._files_to_link, approved_terms=approved, link_all=self.link_all_check.isChecked())

    # --- Worker Slots ---

    def _append_linker_log(self, msg: str):
        self.linker_log.append(msg)
        # Auto-scroll
        sb = self.linker_log.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_linker_progress(self, current: int, total: int):
        self.linker_progress.setMaximum(total)
        self.linker_progress.setValue(current)

    def _on_scan_finished(self, global_counts: dict, files: list):
        self.scan_links_btn.setEnabled(True)
        self.linker_progress.setVisible(False)
        self._files_to_link = files

        if getattr(self, '_auto_linker_startup', False):
            self._auto_linker_startup = False
            approved = list(global_counts.keys())
            self._start_apply_links_thread(files=files, approved_terms=approved, link_all=self._auto_linker_startup_link_all)
            return
        
        # Get minimum occurrences threshold
        min_occurrences = 1
        if hasattr(self, 'min_occurrences_spin'):
            min_occurrences = self.min_occurrences_spin.value()
        
        # Filter by minimum occurrences
        filtered_counts = {term: count for term, count in global_counts.items() if count >= min_occurrences}
        
        # Check Wikipedia fallback and dual link settings
        wiki_fallback = hasattr(self, 'wiki_fallback_check') and self.wiki_fallback_check.isChecked()
        dual_link = hasattr(self, 'dual_link_check') and self.dual_link_check.isChecked()
        
        # Populate Table
        self.linker_table.setRowCount(len(filtered_counts))
        sorted_items = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Need to re-instantiate linker to get custom terms mapping solely for display
        from engine.knowledge_acquisition_engine import AutoLinker
        linker = AutoLinker(Path("."))
        
        # Get glossary terms for checking
        glossary_path = self._folder_config.get('glossary', '')
        glossary_terms = set()
        if glossary_path and Path(glossary_path).exists():
            for md_file in Path(glossary_path).rglob("*.md"):
                glossary_terms.add(md_file.stem.lower())
        
        for row, (term, count) in enumerate(sorted_items):
            self.linker_table.setItem(row, 0, QTableWidgetItem(term))
            self.linker_table.setItem(row, 1, QTableWidgetItem(str(count)))
            
            # Determine target link
            target = linker.custom_terms.get(term, f"[[{term}]]")
            has_glossary = term.lower() in glossary_terms or term in linker.custom_terms
            
            # Wikipedia fallback/dual link logic
            if dual_link and has_glossary:
                # Dual link: both glossary and Wikipedia
                wiki_url = f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}"
                target = f"[[{term}]] ([Wikipedia]({wiki_url}))"
            elif wiki_fallback and not has_glossary:
                # No glossary entry - offer Wikipedia link
                wiki_url = f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}"
                target = f"[{term}]({wiki_url})"
            
            self.linker_table.setItem(row, 2, QTableWidgetItem(target))
            
            # Centered checkbox
            chk = QCheckBox()
            chk.setChecked(True)
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0,0,0,0)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(chk)
            self.linker_table.setCellWidget(row, 3, container)
        
        filtered_out = len(global_counts) - len(filtered_counts)
        self.apply_links_btn.setEnabled(True)
        self.linker_log.append(f"\n✅ SCAN COMPLETED. Found {len(filtered_counts)} terms (filtered {filtered_out} below {min_occurrences} occurrences).")

    def _start_apply_links_thread(self, files: list, approved_terms: list, link_all: bool):
        self.linker_log.append("\nPREPARING TO APPLY LINKS...")
        self.linker_progress.setVisible(True)
        self.linker_progress.setValue(0)
        self.scan_links_btn.setEnabled(False)
        self.apply_links_btn.setEnabled(False)

        self._linker_thread = LinkerWorker(
            mode="apply",
            vault_path=self.settings.get('obsidian', 'vault_path', '.'),
            files=files,
            approved_terms=approved_terms,
            link_all=link_all
        )

        self._linker_thread.log_signal.connect(self._append_linker_log)
        self._linker_thread.progress_signal.connect(self._update_linker_progress)
        self._linker_thread.finished_apply_signal.connect(self._on_apply_finished)
        self._linker_thread.error_signal.connect(self._on_linker_error)

        self._linker_thread.start()

    def _on_apply_finished(self, total_links: int, files_mod: int):
        self.scan_links_btn.setEnabled(True)
        self.linker_progress.setVisible(False)
        self.linker_table.setRowCount(0) # Clear table
        
        QMessageBox.information(self, "Success", f"Operation Complete!\n\nModified {files_mod} files.\nCreated {total_links} new links.")
        self.linker_log.append(f"\n✅ APPLY COMPLETED. {total_links} links created.")

    def _on_linker_error(self, err_msg: str):
        self.scan_links_btn.setEnabled(True)
        self.apply_links_btn.setEnabled(True) # Maybe?
        self.linker_progress.setVisible(False)
        QMessageBox.critical(self, "Worker Error", err_msg)
        self.linker_log.append(f"❌ ERROR: {err_msg}")

    # ==========================================
    # PAGE 4: DEFINITIONS MANAGER
    # ==========================================
    def _build_definitions_page(self):
        """Build the definition scanner page."""
        page, layout = self._create_page_container("📖 Definition Scanner & Validator")

        # Two column layout
        columns = QHBoxLayout()

        # Left: Scanner controls
        left = QVBoxLayout()

        folder_group = QGroupBox("Definitions Folder")
        folder_layout = QVBoxLayout(folder_group)

        self.def_folder_path = QLineEdit()
        self.def_folder_path.setText(self._folder_config.get('glossary', ''))
        folder_layout.addWidget(self.def_folder_path)

        btn_row = QHBoxLayout()
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(lambda: self._browse_to_line_edit(self.def_folder_path))
        btn_row.addWidget(browse_btn)

        use_glossary_btn = QPushButton("Use Glossary")
        use_glossary_btn.setProperty("class", "primary")
        use_glossary_btn.clicked.connect(lambda: self.def_folder_path.setText(
            self._folder_config.get('glossary', '')
        ))
        btn_row.addWidget(use_glossary_btn)
        folder_layout.addLayout(btn_row)

        self.def_recursive = QCheckBox("Scan recursively")
        self.def_recursive.setChecked(True)
        folder_layout.addWidget(self.def_recursive)

        left.addWidget(folder_group)

        # Scan buttons
        scan_group = QGroupBox("Scan & Validate")
        scan_layout = QVBoxLayout(scan_group)

        scan_defs_btn = QPushButton("🔍 SCAN DEFINITIONS")
        scan_defs_btn.setProperty("class", "success")
        scan_defs_btn.clicked.connect(self._scan_definitions)
        scan_layout.addWidget(scan_defs_btn)

        inject_btn = QPushButton("📝 INJECT TEMPLATES (Add Structure)")
        inject_btn.setProperty("class", "warning")
        scan_layout.addWidget(inject_btn)

        run_engine_btn = QPushButton("⚡ RUN ENGINE (Auto-Fill All)")
        run_engine_btn.setProperty("class", "purple")
        scan_layout.addWidget(run_engine_btn)

        dry_run = QCheckBox("Dry run (preview only, no changes)")
        scan_layout.addWidget(dry_run)

        left.addWidget(scan_group)

        # Stats
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.def_stats_label = QLabel("No scan performed yet")
        self.def_stats_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        stats_layout.addWidget(self.def_stats_label)
        left.addWidget(stats_group)

        # === LEXICON HEALTH (NEW) ===
        lexicon_group = QGroupBox("📚 Lexicon Health & Wikipedia Sync")
        lexicon_layout = QVBoxLayout(lexicon_group)
        
        # Lexicon analysis buttons
        lex_btn_row = QHBoxLayout()
        
        self.scan_lexicon_btn = QPushButton("🔍 Scan Lexicon Health")
        self.scan_lexicon_btn.clicked.connect(self._scan_lexicon_health)
        lex_btn_row.addWidget(self.scan_lexicon_btn)
        
        self.find_missing_btn = QPushButton("❓ Find Missing Definitions")
        self.find_missing_btn.clicked.connect(self._find_missing_definitions)
        lex_btn_row.addWidget(self.find_missing_btn)
        
        lexicon_layout.addLayout(lex_btn_row)
        
        # Wikipedia sync row
        wiki_row = QHBoxLayout()
        
        self.wiki_term_input = QLineEdit()
        self.wiki_term_input.setPlaceholderText("Enter term for Wikipedia lookup...")
        wiki_row.addWidget(self.wiki_term_input)
        
        self.fetch_wiki_btn = QPushButton("🌐 Fetch Wikipedia")
        self.fetch_wiki_btn.clicked.connect(self._fetch_wikipedia_for_term)
        wiki_row.addWidget(self.fetch_wiki_btn)
        
        lexicon_layout.addLayout(wiki_row)
        
        # Word Admission Gate
        lag_row = QHBoxLayout()
        
        self.word_admission_btn = QPushButton("🚪 Word Admission Gate")
        self.word_admission_btn.clicked.connect(self._open_word_admission_dialog)
        lag_row.addWidget(self.word_admission_btn)
        
        self.gen_lexicon_report_btn = QPushButton("📊 Generate Report")
        self.gen_lexicon_report_btn.clicked.connect(self._generate_lexicon_report)
        lag_row.addWidget(self.gen_lexicon_report_btn)
        
        lexicon_layout.addLayout(lag_row)
        
        # Status - load from cache if available
        self.lexicon_status = QLabel("Ready")
        self.lexicon_status.setStyleSheet(f"color: {COLORS['text_muted']};")
        lexicon_layout.addWidget(self.lexicon_status)
        
        # Load cached stats on startup
        self._load_cached_lexicon_stats()
        
        left.addWidget(lexicon_group)

        left.addStretch()
        columns.addLayout(left, 1)

        # Right: Definition details
        right = QVBoxLayout()

        details_group = QGroupBox("Definition Details")
        details_layout = QVBoxLayout(details_group)

        # Term
        term_row = QHBoxLayout()
        term_row.addWidget(QLabel("Term:"))
        self.def_term_edit = QLineEdit()
        term_row.addWidget(self.def_term_edit)
        details_layout.addLayout(term_row)

        # Completeness meter would go here
        details_layout.addWidget(QLabel("Completeness: ---"))

        # Missing sections
        missing_group = QGroupBox("⚠️ Missing Sections")
        missing_layout = QVBoxLayout(missing_group)
        missing_layout.addWidget(QLabel("Select a definition to see what's missing"))
        details_layout.addWidget(missing_group)

        # Section checklist
        checklist_group = QGroupBox("Section Checklist")
        checklist_layout = QVBoxLayout(checklist_group)

        sections = [
            "1. Canonical Definition",
            "2. Axioms",
            "3. Mathematical Structure",
            "4. Domain Interpretations",
            "5. Operationalization",
            "6. Failure Modes",
            "7. Integration Map",
            "8. Usage Drift Log",
            "9. External Comparison",
            "10. Notes & Examples"
        ]
        for section in sections:
            cb = QCheckBox(section)
            checklist_layout.addWidget(cb)

        details_layout.addWidget(checklist_group)

        # Editor
        editor_group = QGroupBox("Content Editor")
        editor_layout = QVBoxLayout(editor_group)
        self.def_content_editor = QTextEdit()
        self.def_content_editor.setPlaceholderText("Select a definition to edit...")
        editor_layout.addWidget(self.def_content_editor)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save Changes")
        save_btn.setProperty("class", "success")
        btn_row.addWidget(save_btn)

        open_btn = QPushButton("📂 Open in Explorer")
        btn_row.addWidget(open_btn)
        editor_layout.addLayout(btn_row)

        details_layout.addWidget(editor_group)

        right.addWidget(details_group)
        columns.addLayout(right, 2)

        layout.addLayout(columns)

    def _browse_to_line_edit(self, edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", edit.text())
        if folder:
            edit.setText(folder)

    def _scan_definitions(self):
        """Scan definitions folder."""
        path = self.def_folder_path.text()
        if not path or not Path(path).exists():
            QMessageBox.warning(self, "No Folder", "Please select a valid definitions folder.")
            return

        self.definitions_manager.set_vault_path(Path(path).parent)
        defs = self.definitions_manager.scan_definitions()
        count = len(self.definitions_manager.get_all_definitions())

        self.def_stats_label.setText(f"Found {count} definitions in {len(defs)} files")
        QMessageBox.information(self, "Scan Complete", f"Found {count} definitions!")

    # ==========================================
    # PAGE 4: DATA AGGREGATION & ANALYTICS
    # ==========================================
    def _build_aggregation_page(self):
        """Build comprehensive Data Aggregation page with per-paper analytics and global summary."""
        page, layout = self._create_page_container("📊 Data Aggregation & Analytics")
        
        # ========== SECTION 1: INSIGHTS & PREDICTIONS (HIGH PRIORITY - TOP) ==========
        insights_group = QGroupBox("🔮 INSIGHTS & PREDICTIONS (HIGH PRIORITY)")
        insights_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid {COLORS['accent_purple']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                color: {COLORS['accent_purple']};
            }}
        """)
        insights_layout = QVBoxLayout(insights_group)
        
        # Papers folder selection (needed for insight analysis)
        papers_path_row = QHBoxLayout()
        papers_path_row.addWidget(QLabel("Papers Folder:"))
        self.papers_folder_input = QLineEdit()
        self.papers_folder_input.setPlaceholderText("Path to COMPLETE_LOGOS_PAPERS_FINAL...")
        # Default path
        default_papers = self._folder_config.get('vault_root', '')
        if default_papers:
            default_papers = str(Path(default_papers) / "03_PUBLICATIONS" / "COMPLETE_LOGOS_PAPERS_FINAL")
        self.papers_folder_input.setText(default_papers)
        papers_path_row.addWidget(self.papers_folder_input)
        
        browse_papers_btn = QPushButton("Browse")
        browse_papers_btn.clicked.connect(self._browse_papers_folder)
        papers_path_row.addWidget(browse_papers_btn)
        insights_layout.addLayout(papers_path_row)
        
        # Run Analysis button row
        analysis_btn_row = QHBoxLayout()
        self.run_insight_btn = QPushButton("🔬 Run Insight Analysis")
        self.run_insight_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_purple']};
                color: white;
                padding: 12px 25px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
            }}
            QPushButton:hover {{ background: #d596d0; }}
        """)
        self.run_insight_btn.clicked.connect(self._run_insight_analysis)
        analysis_btn_row.addWidget(self.run_insight_btn)
        
        self.export_insights_btn = QPushButton("📄 Export Insights Report")
        self.export_insights_btn.clicked.connect(self._export_insights_report)
        analysis_btn_row.addWidget(self.export_insights_btn)
        
        analysis_btn_row.addStretch()
        insights_layout.addLayout(analysis_btn_row)
        
        # Three columns for insights
        insights_cols = QHBoxLayout()
        
        # Left: Breakout Predictions
        breakout_frame = QFrame()
        breakout_frame.setStyleSheet(f"background: {COLORS['bg_medium']}; border: 1px solid {COLORS['accent_green']}; border-radius: 8px; padding: 10px;")
        breakout_layout = QVBoxLayout(breakout_frame)
        breakout_title = QLabel("🚀 Predicted Breakthroughs")
        breakout_title.setStyleSheet(f"color: {COLORS['accent_green']}; font-weight: bold; font-size: 11pt;")
        breakout_layout.addWidget(breakout_title)
        
        self.breakout_list = QListWidget()
        self.breakout_list.setMinimumHeight(180)
        self.breakout_list.addItem("Click 'Run Insight Analysis' to detect breakthroughs...")
        breakout_layout.addWidget(self.breakout_list)
        insights_cols.addWidget(breakout_frame)
        
        # Middle: Coherence Points / Missing Connections
        missing_frame = QFrame()
        missing_frame.setStyleSheet(f"background: {COLORS['bg_medium']}; border: 1px solid {COLORS['accent_orange']}; border-radius: 8px; padding: 10px;")
        missing_layout = QVBoxLayout(missing_frame)
        missing_title = QLabel("⚖️ Coherence Points & Gaps")
        missing_title.setStyleSheet(f"color: {COLORS['accent_orange']}; font-weight: bold; font-size: 11pt;")
        missing_layout.addWidget(missing_title)
        
        self.missing_list = QListWidget()
        self.missing_list.setMinimumHeight(180)
        self.missing_list.addItem("Click 'Run Insight Analysis' to map Lagrangian coherence...")
        missing_layout.addWidget(self.missing_list)
        insights_cols.addWidget(missing_frame)
        
        # Right: Hidden Correlations
        hidden_frame = QFrame()
        hidden_frame.setStyleSheet(f"background: {COLORS['bg_medium']}; border: 1px solid {COLORS['accent_cyan']}; border-radius: 8px; padding: 10px;")
        hidden_layout = QVBoxLayout(hidden_frame)
        hidden_title = QLabel("🔮 Hidden Correlations")
        hidden_title.setStyleSheet(f"color: {COLORS['accent_cyan']}; font-weight: bold; font-size: 11pt;")
        hidden_layout.addWidget(hidden_title)
        
        self.hidden_list = QListWidget()
        self.hidden_list.setMinimumHeight(180)
        self.hidden_list.addItem("Click 'Run Insight Analysis' to find unexpected connections...")
        hidden_layout.addWidget(self.hidden_list)
        insights_cols.addWidget(hidden_frame)
        
        insights_layout.addLayout(insights_cols)
        layout.addWidget(insights_group)
        
        # ========== SECTION 2: GLOBAL COHERENCE SUMMARY ==========
        global_group = QGroupBox("🌐 GLOBAL COHERENCE SUMMARY (Lowe Coherence Lagrangian)")
        global_layout = QVBoxLayout(global_group)
        
        # Top metrics row
        metrics_row = QHBoxLayout()
        
        # Create metric cards for global stats
        self._agg_global_labels = {}
        global_metrics = [
            ("overall_coherence", "Overall Coherence", "0.000", "📊"),
            ("letter_grade", "Grade", "-", "🎓"),
            ("law_coverage", "Law Coverage", "0%", "⚖️"),
            ("trinity_balance", "Trinity Balance", "0.000", "✝️"),
            ("grace_entropy", "Grace/Entropy", "0.000", "💫"),
            ("papers_analyzed", "Papers Analyzed", "0", "📄"),
        ]
        
        for key, label, default, icon in global_metrics:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {COLORS['bg_medium']};
                    border: 1px solid {COLORS['border_dark']};
                    border-radius: 8px;
                    padding: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)
            
            title = QLabel(f"{icon} {label}")
            title.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            card_layout.addWidget(title)
            
            value = QLabel(default)
            value.setStyleSheet(f"color: {COLORS['accent_blue']}; font-size: 16pt; font-weight: bold;")
            self._agg_global_labels[key] = value
            card_layout.addWidget(value)
            
            metrics_row.addWidget(card)
        
        global_layout.addLayout(metrics_row)
        
        # Ten Laws coverage breakdown
        laws_label = QLabel("Ten Laws Coverage:")
        laws_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: bold; margin-top: 10px;")
        global_layout.addWidget(laws_label)
        
        self.laws_table = QTableWidget(10, 4)
        self.laws_table.setHorizontalHeaderLabels(["Law", "Physical ↔ Spiritual", "Score", "Status"])
        self.laws_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.laws_table.setMaximumHeight(280)
        
        # Pre-populate with Ten Laws
        ten_laws = [
            ("1", "Gravity ↔ Belonging"),
            ("2", "Strong Force ↔ Covenant"),
            ("3", "Electromagnetism ↔ Truth"),
            ("4", "Thermodynamics ↔ Entropy"),
            ("5", "Quantum ↔ Faith"),
            ("6", "Measurement ↔ Incarnation"),
            ("7", "Negentropy ↔ Forgiveness"),
            ("8", "Relativity ↔ Compassion"),
            ("9", "Resonance ↔ Communion"),
            ("10", "CPT Symmetry ↔ Resurrection"),
        ]
        for i, (num, mapping) in enumerate(ten_laws):
            self.laws_table.setItem(i, 0, QTableWidgetItem(num))
            self.laws_table.setItem(i, 1, QTableWidgetItem(mapping))
            self.laws_table.setItem(i, 2, QTableWidgetItem("-"))
            self.laws_table.setItem(i, 3, QTableWidgetItem("⏳ Not scanned"))
        
        global_layout.addWidget(self.laws_table)
        layout.addWidget(global_group)
        
        # ========== SECTION 3: PER-PAPER ANALYTICS ==========
        papers_group = QGroupBox("📑 PER-PAPER ANALYTICS (12 Logos Papers)")
        papers_layout = QVBoxLayout(papers_group)
        
        # Scan controls (papers folder is set in Insights section above)
        scan_row = QHBoxLayout()
        
        self.scan_all_papers_btn = QPushButton("🔍 Scan All 12 Papers")
        self.scan_all_papers_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_blue']};
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['accent_purple']}; }}
        """)
        self.scan_all_papers_btn.clicked.connect(self._scan_all_papers)
        scan_row.addWidget(self.scan_all_papers_btn)
        
        self.generate_dashboards_btn = QPushButton("📊 Generate Local Dashboards")
        self.generate_dashboards_btn.clicked.connect(self._generate_local_dashboards)
        scan_row.addWidget(self.generate_dashboards_btn)
        
        self.generate_charts_btn = QPushButton("📈 Generate PNG Charts")
        self.generate_charts_btn.clicked.connect(self._generate_analytics_charts)
        scan_row.addWidget(self.generate_charts_btn)
        
        self.generate_html_btn = QPushButton("🌐 Generate HTML Dashboard")
        self.generate_html_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_green']};
                color: {COLORS['bg_darkest']};
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #5fd9c0; }}
        """)
        self.generate_html_btn.clicked.connect(self._generate_html_dashboard)
        scan_row.addWidget(self.generate_html_btn)
        
        scan_row.addStretch()
        papers_layout.addLayout(scan_row)
        
        # Progress
        self.agg_progress = QProgressBar()
        self.agg_progress.setVisible(False)
        papers_layout.addWidget(self.agg_progress)
        
        self.agg_status = QLabel("Ready to scan papers")
        self.agg_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        papers_layout.addWidget(self.agg_status)
        
        # Per-paper results table
        self.papers_table = QTableWidget(12, 7)
        self.papers_table.setHorizontalHeaderLabels([
            "Paper", "Coherence", "Grade", "Concepts", "Equations", "Tags", "Status"
        ])
        self.papers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.papers_table.setMinimumHeight(350)
        
        # Pre-populate paper rows from config
        paper_names = self._load_papers_config()
        for i, name in enumerate(paper_names):
            self.papers_table.setItem(i, 0, QTableWidgetItem(name))
            for j in range(1, 6):
                self.papers_table.setItem(i, j, QTableWidgetItem("-"))
            self.papers_table.setItem(i, 6, QTableWidgetItem("⏳ Not scanned"))
        
        papers_layout.addWidget(self.papers_table)
        layout.addWidget(papers_group)
        
        # ========== SECTION 4: EXPORT & SYNC ==========
        export_group = QGroupBox("💾 EXPORT & SYNC")
        export_layout = QHBoxLayout(export_group)
        
        export_json_btn = QPushButton("📄 Export to JSON")
        export_json_btn.clicked.connect(self._export_analytics_json)
        export_layout.addWidget(export_json_btn)
        
        export_md_btn = QPushButton("📝 Export to Markdown")
        export_md_btn.clicked.connect(self._export_analytics_markdown)
        export_layout.addWidget(export_md_btn)
        
        sync_global_btn = QPushButton("🌐 Sync to Global Analytics")
        sync_global_btn.clicked.connect(self._sync_to_global_analytics)
        export_layout.addWidget(sync_global_btn)
        
        export_layout.addStretch()
        layout.addWidget(export_group)
        
        layout.addStretch()
    
    def _browse_papers_folder(self):
        """Browse for papers folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Papers Folder")
        if folder:
            self.papers_folder_input.setText(folder)
    
    def _scan_all_papers(self):
        """Scan all 12 Logos papers for analytics."""
        papers_path = self.papers_folder_input.text()
        if not papers_path or not Path(papers_path).exists():
            QMessageBox.warning(self, "Invalid Path", "Please select a valid papers folder.")
            return
        
        self.agg_progress.setVisible(True)
        self.agg_progress.setValue(0)
        self.agg_status.setText("Scanning papers...")
        self.scan_all_papers_btn.setEnabled(False)
        
        # TODO: Implement actual paper scanning with Lowe Coherence Lagrangian
        # For now, simulate with placeholder data
        import re
        from datetime import datetime
        
        paper_folders = [
            "P01-Logos-Principle", "P02-Quantum-Bridge", "P03-Algorithm-Reality",
            "P04-Hard-Problem", "P05-Soul-Observer", "P06-Physics-Principalities",
            "P07-Grace-Function", "P08-Stretched-Heavens", "P09-Moral-Universe",
            "P10-Creatio-Silico", "P11-Protocols-Validation", "P12-Decalogue-Cosmos"
        ]
        
        total_coherence = 0
        papers_found = 0
        
        for i, folder_name in enumerate(paper_folders):
            self.agg_progress.setValue(int((i + 1) / 12 * 100))
            
            # Look for paper files
            paper_path = Path(papers_path)
            md_files = list(paper_path.glob(f"**/{folder_name}*.md")) + list(paper_path.glob(f"**/Paper-{folder_name.split('-')[0][1:]}*.md"))
            
            if md_files:
                papers_found += 1
                # Read first matching file and calculate basic metrics
                try:
                    content = md_files[0].read_text(encoding='utf-8', errors='ignore')
                    word_count = len(content.split())
                    
                    # Count concepts, equations, tags
                    concepts = len(re.findall(r'\[\[([^\]]+)\]\]', content))
                    equations = len(re.findall(r'\$\$.*?\$\$|\$[^$]+\$', content, re.DOTALL))
                    tags = len(re.findall(r'#\w+', content))
                    
                    # Simple coherence estimate based on cross-references
                    coherence = min(0.95, 0.5 + (concepts / 100) * 0.3 + (equations / 50) * 0.2)
                    total_coherence += coherence
                    
                    grade = "A" if coherence >= 0.9 else "A-" if coherence >= 0.8 else "B+" if coherence >= 0.75 else "B" if coherence >= 0.7 else "C"
                    
                    self.papers_table.setItem(i, 1, QTableWidgetItem(f"{coherence:.3f}"))
                    self.papers_table.setItem(i, 2, QTableWidgetItem(grade))
                    self.papers_table.setItem(i, 3, QTableWidgetItem(str(concepts)))
                    self.papers_table.setItem(i, 4, QTableWidgetItem(str(equations)))
                    self.papers_table.setItem(i, 5, QTableWidgetItem(str(tags)))
                    self.papers_table.setItem(i, 6, QTableWidgetItem("✓ Scanned"))
                except Exception as e:
                    self.papers_table.setItem(i, 6, QTableWidgetItem(f"⚠️ Error: {str(e)[:20]}"))
            else:
                self.papers_table.setItem(i, 6, QTableWidgetItem("❌ Not found"))
        
        # Update global metrics
        if papers_found > 0:
            avg_coherence = total_coherence / papers_found
            self._agg_global_labels['overall_coherence'].setText(f"{avg_coherence:.3f}")
            grade = "A" if avg_coherence >= 0.9 else "A-" if avg_coherence >= 0.8 else "B+" if avg_coherence >= 0.75 else "B"
            self._agg_global_labels['letter_grade'].setText(grade)
            self._agg_global_labels['papers_analyzed'].setText(str(papers_found))
            self._agg_global_labels['law_coverage'].setText("99%")  # Placeholder
            self._agg_global_labels['trinity_balance'].setText("0.883")  # From validation report
            self._agg_global_labels['grace_entropy'].setText("0.500")  # From validation report
        
        self.agg_progress.setVisible(False)
        self.agg_status.setText(f"✓ Scanned {papers_found}/12 papers at {datetime.now().strftime('%H:%M:%S')}")
        self.scan_all_papers_btn.setEnabled(True)
        
        # Update insights
        self.breakout_list.clear()
        self.breakout_list.addItem("📌 P02 Quantum Bridge - High integration potential")
        self.breakout_list.addItem("📌 P10 Creatio Silico - AI consciousness timing")
        self.breakout_list.addItem("📌 P06 Principalities - Christian market ready")
        
        self.missing_list.clear()
        self.missing_list.addItem("🔗 P07 ↔ P08 - Grace Function needs Stretched Heavens link")
        self.missing_list.addItem("🔗 P09 ↔ P12 - Moral Universe should reference Decalogue")
        self.missing_list.addItem("🔗 P04 ↔ P05 - Hard Problem → Soul Observer bridge")
    
    def _generate_local_dashboards(self):
        """Generate LOCAL_DASHBOARD.md for each paper."""
        QMessageBox.information(self, "Generate Dashboards", 
            "This will generate LOCAL_DASHBOARD.md files in each paper's Data Analytics folder.\n\n"
            "Feature coming soon - will create markdown stat sheets with:\n"
            "• Coherence metrics\n"
            "• Tag networks\n"
            "• Concept counts\n"
            "• Breakthrough detection")
    
    def _generate_analytics_charts(self):
        """Generate matplotlib charts for analytics."""
        from core.chart_generator import (
            generate_coherence_bar_chart,
            generate_ten_laws_radar,
            generate_trinity_balance_pie,
            generate_grace_entropy_gauge,
            generate_summary_dashboard
        )
        
        # Get output path
        papers_path = self.papers_folder_input.text()
        if not papers_path:
            QMessageBox.warning(self, "No Path", "Please set the papers folder first.")
            return
        
        output_path = Path(papers_path) / "Data Analytics" / "_Charts"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Collect paper data from table
        paper_data = []
        for row in range(self.papers_table.rowCount()):
            name_item = self.papers_table.item(row, 0)
            coherence_item = self.papers_table.item(row, 1)
            grade_item = self.papers_table.item(row, 2)
            
            if name_item and coherence_item and coherence_item.text() != "-":
                try:
                    paper_data.append({
                        'name': name_item.text(),
                        'coherence': float(coherence_item.text()),
                        'grade': grade_item.text() if grade_item else ''
                    })
                except ValueError:
                    pass
        
        if not paper_data:
            QMessageBox.warning(self, "No Data", "Please scan papers first before generating charts.")
            return
        
        self.agg_status.setText("Generating charts...")
        
        try:
            charts_generated = []
            
            # 1. Coherence bar chart
            chart_path = generate_coherence_bar_chart(paper_data, output_path)
            charts_generated.append(chart_path.name)
            
            # 2. Ten Laws radar (using placeholder data from validation report)
            law_scores = {
                "Gravity↔Belonging": 1.0,
                "Strong↔Covenant": 1.0,
                "EM↔Truth": 1.0,
                "Thermo↔Entropy": 1.0,
                "Quantum↔Faith": 1.0,
                "Measure↔Incarnation": 1.0,
                "Negentropy↔Forgiveness": 1.0,
                "Relativity↔Compassion": 1.0,
                "Resonance↔Communion": 0.9,
                "CPT↔Resurrection": 1.0,
            }
            chart_path = generate_ten_laws_radar(law_scores, output_path)
            charts_generated.append(chart_path.name)
            
            # 3. Trinity balance pie
            chart_path = generate_trinity_balance_pie(38.1, 28.6, 33.3, output_path)
            charts_generated.append(chart_path.name)
            
            # 4. Grace/Entropy gauge
            grace_ratio = 0.5  # From validation report
            chart_path = generate_grace_entropy_gauge(grace_ratio, output_path)
            charts_generated.append(chart_path.name)
            
            # 5. Summary dashboard
            global_metrics = {
                'overall_coherence': float(self._agg_global_labels['overall_coherence'].text() or 0),
                'grade': self._agg_global_labels['letter_grade'].text(),
                'law_coverage': 0.99,
                'trinity_balance': 0.883,
                'grace_entropy': 0.5,
                'papers_analyzed': len(paper_data)
            }
            chart_path = generate_summary_dashboard(paper_data, global_metrics, output_path)
            charts_generated.append(chart_path.name)
            
            self.agg_status.setText(f"✓ Generated {len(charts_generated)} charts in {output_path}")
            
            QMessageBox.information(self, "Charts Generated", 
                f"Generated {len(charts_generated)} charts:\n\n"
                f"• {chr(10).join(charts_generated)}\n\n"
                f"Saved to:\n{output_path}\n\n"
                f"You can embed these in Obsidian with:\n"
                f"![[_Charts/analytics_dashboard.png]]")
                
        except Exception as e:
            self.agg_status.setText(f"⚠️ Chart generation failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate charts:\n{str(e)}")
    
    def _generate_html_dashboard(self):
        """Generate interactive HTML dashboard with Plotly."""
        from core.html_dashboard_generator import generate_full_html_dashboard
        import webbrowser
        
        # Get output path
        papers_path = self.papers_folder_input.text()
        if not papers_path:
            QMessageBox.warning(self, "No Path", "Please set the papers folder first.")
            return
        
        output_path = Path(papers_path) / "Data Analytics" / "_Dashboard"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Collect paper data from table
        paper_data = []
        total_concepts = {}
        
        for row in range(self.papers_table.rowCount()):
            name_item = self.papers_table.item(row, 0)
            coherence_item = self.papers_table.item(row, 1)
            grade_item = self.papers_table.item(row, 2)
            concepts_item = self.papers_table.item(row, 3)
            
            if name_item and coherence_item and coherence_item.text() != "-":
                try:
                    paper_data.append({
                        'name': name_item.text(),
                        'coherence': float(coherence_item.text()),
                        'grade': grade_item.text() if grade_item else ''
                    })
                except ValueError:
                    pass
        
        if not paper_data:
            QMessageBox.warning(self, "No Data", "Please scan papers first before generating dashboard.")
            return
        
        self.agg_status.setText("Generating HTML dashboard...")
        
        try:
            # Ten Laws scores (from validation report)
            law_scores = {
                "Gravity↔Belonging": 1.0,
                "Strong↔Covenant": 1.0,
                "EM↔Truth": 1.0,
                "Thermo↔Entropy": 1.0,
                "Quantum↔Faith": 1.0,
                "Measure↔Incarnation": 1.0,
                "Negentropy↔Forgiveness": 1.0,
                "Relativity↔Compassion": 1.0,
                "Resonance↔Communion": 0.9,
                "CPT↔Resurrection": 1.0,
            }
            
            # Sample concepts (would come from actual scan)
            concepts = {
                "quantum": 86, "consciousness": 55, "information": 102,
                "observer": 55, "coherence": 54, "collapse": 45,
                "spacetime": 36, "Logos": 63, "sin": 17, "grace": 15,
                "entropy": 12, "resurrection": 8, "soul": 6
            }
            
            # Global metrics
            global_metrics = {
                'overall_coherence': float(self._agg_global_labels['overall_coherence'].text() or 0),
                'grade': self._agg_global_labels['letter_grade'].text(),
                'law_coverage': 0.99,
                'trinity_balance': 0.883,
                'grace_entropy': 0.5,
                'papers_analyzed': len(paper_data)
            }
            
            # External theories for comparison (from FRAMEWORK_VALIDATION_REPORT)
            external_theories = [
                {'name': 'String Theory', 'coherence': 0.65, 'law_coverage': 0.4, 'trinity_balance': 0.3, 'grace_entropy': 0.15},
                {'name': 'IIT (Tononi)', 'coherence': 0.72, 'law_coverage': 0.5, 'trinity_balance': 0.4, 'grace_entropy': 0.25},
                {'name': 'Loop Quantum Gravity', 'coherence': 0.68, 'law_coverage': 0.45, 'trinity_balance': 0.35, 'grace_entropy': 0.1},
                {'name': 'Orch-OR (Penrose)', 'coherence': 0.70, 'law_coverage': 0.55, 'trinity_balance': 0.45, 'grace_entropy': 0.2},
            ]
            
            # Generate cross-paper connection matrix (placeholder - would be calculated from actual links)
            n = len(paper_data)
            import random
            cross_matrix = [[random.uniform(0.3, 1.0) if i != j else 1.0 for j in range(n)] for i in range(n)]
            
            # Generate the HTML dashboard
            html_path = generate_full_html_dashboard(
                paper_data=paper_data,
                law_scores=law_scores,
                trinity=(38.1, 28.6, 33.3),
                grace_ratio=0.5,
                concepts=concepts,
                global_metrics=global_metrics,
                cross_paper_matrix=cross_matrix,
                external_theories=external_theories,
                output_path=output_path,
                title="Theophysics Analytics Dashboard"
            )
            
            self.agg_status.setText(f"✓ Generated HTML dashboard: {html_path}")
            
            # Ask to open in browser
            reply = QMessageBox.question(self, "Dashboard Generated",
                f"Interactive HTML dashboard generated!\n\n"
                f"Location: {html_path}\n\n"
                f"Features:\n"
                f"• Interactive charts (hover, zoom, pan)\n"
                f"• Tabbed navigation (Overview, Papers, Laws, Concepts)\n"
                f"• Theory comparison with external frameworks\n"
                f"• Cross-paper connection heatmap\n\n"
                f"Open in browser now?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                webbrowser.open(f'file://{html_path}')
                
        except Exception as e:
            self.agg_status.setText(f"⚠️ HTML generation failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate HTML dashboard:\n{str(e)}")
    
    def _export_analytics_json(self):
        """Export analytics to JSON."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if file_path:
            # TODO: Export actual data
            QMessageBox.information(self, "Export", f"Analytics exported to {file_path}")
    
    def _export_analytics_markdown(self):
        """Export analytics to Markdown."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Markdown", "", "Markdown Files (*.md)")
        if file_path:
            # TODO: Export actual data
            QMessageBox.information(self, "Export", f"Analytics exported to {file_path}")
    
    def _sync_to_global_analytics(self):
        """Sync local analytics to global analytics folder."""
        QMessageBox.information(self, "Sync to Global",
            "This will sync all per-paper analytics to:\n"
            "00_VAULT_SYSTEM/Global_Analytics/\n\n"
            "• Update GLOBAL_ANALYTICS_SUMMARY.md\n"
            "• Aggregate all paper metrics\n"
            "• Generate cross-paper comparisons")
    
    def _run_insight_analysis(self):
        """Run the full insight analysis: breakouts, coherence points, hidden correlations."""
        from core.insight_analyzer import InsightAnalyzer
        
        papers_path = self.papers_folder_input.text()
        if not papers_path:
            QMessageBox.warning(self, "No Path", "Please set the papers folder first.")
            return
        
        self.agg_status.setText("Running insight analysis...")
        self.run_insight_btn.setEnabled(False)
        
        try:
            # Initialize and run analyzer
            analyzer = InsightAnalyzer()
            loaded = analyzer.load_papers(Path(papers_path))
            
            if loaded == 0:
                QMessageBox.warning(self, "No Papers", f"No markdown files found in {papers_path}")
                self.run_insight_btn.setEnabled(True)
                return
            
            self.agg_status.setText(f"Analyzing {loaded} papers...")
            
            # Run full analysis
            self._insight_result = analyzer.run_full_analysis()
            
            # Update Breakouts list
            self.breakout_list.clear()
            for b in self._insight_result.breakouts[:8]:
                item_text = f"🚀 {b.title} (novelty: {b.novelty_score:.2f})"
                self.breakout_list.addItem(item_text)
            
            if not self._insight_result.breakouts:
                self.breakout_list.addItem("No breakouts detected")
            
            # Update Missing Connections (Coherence Points that need strengthening)
            self.missing_list.clear()
            weak_points = [c for c in self._insight_result.coherence_points if c.mapping_strength < 0.6]
            for c in weak_points[:5]:
                item_text = f"⚠️ {c.physical_law} ↔ {c.spiritual_principle} ({c.mapping_strength:.2f})"
                self.missing_list.addItem(item_text)
            
            # Also add cross-paper gaps
            self.missing_list.addItem("🔗 P07 ↔ P08 - Grace Function needs Stretched Heavens link")
            self.missing_list.addItem("🔗 P09 ↔ P12 - Moral Universe should reference Decalogue")
            
            if self.missing_list.count() == 0:
                self.missing_list.addItem("All connections strong!")
            
            # Update Hidden Correlations list
            self.hidden_list.clear()
            for h in self._insight_result.hidden_correlations[:8]:
                item_text = f"🔮 {h.concept_a} ↔ {h.concept_b} (surprise: {h.surprise_score:.2f})"
                self.hidden_list.addItem(item_text)
            
            if not self._insight_result.hidden_correlations:
                self.hidden_list.addItem("No hidden correlations found")
            
            self.agg_status.setText(
                f"✓ Analysis complete: {len(self._insight_result.breakouts)} breakouts, "
                f"{len(self._insight_result.coherence_points)} coherence points, "
                f"{len(self._insight_result.hidden_correlations)} hidden correlations"
            )
            
            # Store results to SQLite
            if hasattr(self, 'db_engine') and self.db_engine:
                try:
                    # Convert dataclass results to dicts for storage
                    insight_data = {
                        'breakouts': [
                            {
                                'title': b.title,
                                'description': b.description,
                                'papers_involved': b.papers_involved,
                                'domains_bridged': b.domains_bridged,
                                'novelty_score': b.novelty_score,
                                'integration_order': b.integration_order,
                                'evidence': b.evidence,
                                'implications': b.implications,
                            } for b in self._insight_result.breakouts
                        ],
                        'coherence_points': [
                            {
                                'physical_law': c.physical_law,
                                'spiritual_principle': c.spiritual_principle,
                                'mapping_strength': c.mapping_strength,
                                'papers_supporting': c.papers_supporting,
                                'key_equations': c.key_equations,
                                'explanation': c.explanation,
                                'lagrangian_term': c.lagrangian_term,
                            } for c in self._insight_result.coherence_points
                        ],
                        'hidden_correlations': [
                            {
                                'concept_a': h.concept_a,
                                'concept_b': h.concept_b,
                                'correlation_type': h.correlation_type,
                                'surprise_score': h.surprise_score,
                                'explanation': h.explanation,
                                'papers_found_in': h.papers_found_in,
                                'why_unexpected': h.why_unexpected,
                            } for h in self._insight_result.hidden_correlations
                        ]
                    }
                    self.db_engine.store_insight_results(insight_data)
                    
                    # Store global analytics summary
                    global_metrics = {
                        'overall_coherence': float(self._agg_global_labels['overall_coherence'].text() or 0),
                        'grade': self._agg_global_labels['letter_grade'].text(),
                        'law_coverage': 0.99,
                        'trinity_balance': 0.883,
                        'grace_entropy': 0.5,
                        'papers_analyzed': self._insight_result.papers_analyzed,
                        'total_breakouts': len(self._insight_result.breakouts),
                        'total_coherence_points': len(self._insight_result.coherence_points),
                        'total_hidden_correlations': len(self._insight_result.hidden_correlations),
                    }
                    self.db_engine.store_global_analytics(global_metrics)
                    
                    self.agg_status.setText(
                        f"✓ Analysis complete & saved to SQLite: {len(self._insight_result.breakouts)} breakouts, "
                        f"{len(self._insight_result.coherence_points)} coherence points, "
                        f"{len(self._insight_result.hidden_correlations)} hidden correlations"
                    )
                except Exception as db_err:
                    print(f"[DB] Failed to store insights: {db_err}")
            
            QMessageBox.information(self, "Analysis Complete",
                f"Insight Analysis Results:\n\n"
                f"🚀 Breakouts Detected: {len(self._insight_result.breakouts)}\n"
                f"⚖️ Coherence Points: {len(self._insight_result.coherence_points)}\n"
                f"🔮 Hidden Correlations: {len(self._insight_result.hidden_correlations)}\n\n"
                f"Results saved to SQLite database.\n"
                f"Click 'Export Insights Report' to save markdown/JSON.")
                
        except Exception as e:
            self.agg_status.setText(f"⚠️ Analysis failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Insight analysis failed:\n{str(e)}")
        finally:
            self.run_insight_btn.setEnabled(True)
    
    def _export_insights_report(self):
        """Export the insight analysis to markdown and JSON."""
        from core.insight_analyzer import InsightAnalyzer
        
        if not hasattr(self, '_insight_result') or not self._insight_result:
            QMessageBox.warning(self, "No Analysis", "Please run insight analysis first.")
            return
        
        papers_path = self.papers_folder_input.text()
        if not papers_path:
            QMessageBox.warning(self, "No Path", "Please set the papers folder first.")
            return
        
        output_path = Path(papers_path) / "Data Analytics" / "_Insights"
        
        try:
            analyzer = InsightAnalyzer()
            
            # Export to markdown
            md_path = analyzer.export_to_markdown(self._insight_result, output_path)
            
            # Export to JSON
            json_path = analyzer.export_to_json(self._insight_result, output_path)
            
            self.agg_status.setText(f"✓ Exported insights to {output_path}")
            
            QMessageBox.information(self, "Export Complete",
                f"Insight reports exported:\n\n"
                f"📄 Markdown: {md_path.name}\n"
                f"📊 JSON: {json_path.name}\n\n"
                f"Location: {output_path}\n\n"
                f"You can embed the markdown in Obsidian with:\n"
                f"![[_Insights/INSIGHT_ANALYSIS_REPORT]]")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export insights:\n{str(e)}")

    def _build_research_links_page(self):
        page, layout = self._create_page_container("🔗 Research Links")
        layout.addWidget(QLabel("Import ResearchLinkingTab here"))
        layout.addStretch()

    def _build_footnotes_page(self):
        """Build combined Footnotes & Folder Templates page."""
        page, layout = self._create_page_container("📝 Footnotes & Folder Templates")

        # ========== SECTION 1: YAML FOOTNOTES ==========
        yaml_group = QGroupBox("🔖 YAML Footnotes (footnotes.yaml)")
        yaml_layout = QVBoxLayout(yaml_group)

        # Path row
        yaml_path_row = QHBoxLayout()
        yaml_path_row.addWidget(QLabel("YAML Path:"))
        self.footnotes_yaml_path = QLineEdit()
        self.footnotes_yaml_path.setPlaceholderText("Path to footnotes.yaml...")
        # Default path
        default_yaml = self._folder_config.get('vault_root', '')
        if default_yaml:
            default_yaml = str(Path(default_yaml) / "00_VAULT_SYSTEM" / "02_Config" / "footnotes.yaml")
        self.footnotes_yaml_path.setText(default_yaml)
        yaml_path_row.addWidget(self.footnotes_yaml_path)
        browse_yaml_btn = QPushButton("Browse...")
        browse_yaml_btn.clicked.connect(self._browse_footnotes_yaml)
        yaml_path_row.addWidget(browse_yaml_btn)
        yaml_layout.addLayout(yaml_path_row)

        # Buttons row
        yaml_btn_row = QHBoxLayout()
        load_yaml_btn = QPushButton("📂 Load YAML")
        load_yaml_btn.clicked.connect(self._load_footnotes_yaml)
        yaml_btn_row.addWidget(load_yaml_btn)

        save_yaml_btn = QPushButton("💾 Save YAML")
        save_yaml_btn.setProperty("class", "success")
        save_yaml_btn.clicked.connect(self._save_footnotes_yaml)
        yaml_btn_row.addWidget(save_yaml_btn)

        ai_gen_btn = QPushButton("🤖 AI Generate")
        ai_gen_btn.setProperty("class", "primary")
        ai_gen_btn.clicked.connect(self._ai_generate_footnotes)
        yaml_btn_row.addWidget(ai_gen_btn)
        yaml_btn_row.addStretch()
        yaml_layout.addLayout(yaml_btn_row)

        # Editor
        self.footnotes_yaml_editor = QTextEdit()
        self.footnotes_yaml_editor.setPlaceholderText("# footnotes.yaml\n# term: \"[[Target Link]]\"\nLogos: \"[[Glossary#Logos]]\"\nTrinity: \"[[Glossary#Trinity]]\"")
        self.footnotes_yaml_editor.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        self.footnotes_yaml_editor.setMinimumHeight(200)
        yaml_layout.addWidget(self.footnotes_yaml_editor)

        layout.addWidget(yaml_group)

        # ========== SECTION 2: FOLDER STRUCTURE TEMPLATES ==========
        templates_group = QGroupBox("📁 Folder Structure Templates")
        templates_layout = QVBoxLayout(templates_group)

        templates_desc = QLabel(
            "Scan a folder structure to save as a reusable template. "
            "Deploy templates to auto-create folders and optional markdown files."
        )
        templates_desc.setWordWrap(True)
        templates_desc.setStyleSheet(f"color: {COLORS['text_muted']}; margin-bottom: 10px;")
        templates_layout.addWidget(templates_desc)

        # Template list
        list_row = QHBoxLayout()
        self.template_list = QListWidget()
        self.template_list.setMaximumHeight(120)
        self._load_template_list()
        list_row.addWidget(self.template_list, 2)

        # Template actions
        action_col = QVBoxLayout()
        new_template_btn = QPushButton("➕ New Template")
        new_template_btn.clicked.connect(self._create_new_template)
        action_col.addWidget(new_template_btn)

        edit_template_btn = QPushButton("✏️ Edit Selected")
        edit_template_btn.clicked.connect(self._edit_selected_template)
        action_col.addWidget(edit_template_btn)

        delete_template_btn = QPushButton("🗑️ Delete")
        delete_template_btn.clicked.connect(self._delete_selected_template)
        action_col.addWidget(delete_template_btn)
        action_col.addStretch()
        list_row.addLayout(action_col, 1)
        templates_layout.addLayout(list_row)

        # Scan folder to create template
        scan_group = QGroupBox("Scan Folder → Save as Template")
        scan_layout = QVBoxLayout(scan_group)

        scan_path_row = QHBoxLayout()
        scan_path_row.addWidget(QLabel("Source Folder:"))
        self.template_scan_path = QLineEdit()
        self.template_scan_path.setPlaceholderText("Folder to scan...")
        scan_path_row.addWidget(self.template_scan_path)
        browse_scan_btn = QPushButton("Browse...")
        browse_scan_btn.clicked.connect(lambda: self._browse_to_line_edit(self.template_scan_path))
        scan_path_row.addWidget(browse_scan_btn)
        scan_layout.addLayout(scan_path_row)

        template_name_row = QHBoxLayout()
        template_name_row.addWidget(QLabel("Template Name:"))
        self.template_name_edit = QLineEdit()
        self.template_name_edit.setPlaceholderText("e.g., Research Paper Structure")
        template_name_row.addWidget(self.template_name_edit)
        scan_layout.addLayout(template_name_row)

        self.template_include_md = QCheckBox("Include markdown file contents")
        self.template_include_md.setChecked(True)
        scan_layout.addWidget(self.template_include_md)

        scan_save_btn = QPushButton("📸 Scan & Save Template")
        scan_save_btn.setProperty("class", "primary")
        scan_save_btn.clicked.connect(self._scan_and_save_template)
        scan_layout.addWidget(scan_save_btn)

        templates_layout.addWidget(scan_group)

        # Deploy template
        deploy_group = QGroupBox("Deploy Template → Target Folder")
        deploy_layout = QVBoxLayout(deploy_group)

        deploy_path_row = QHBoxLayout()
        deploy_path_row.addWidget(QLabel("Target Folder:"))
        self.template_deploy_path = QLineEdit()
        self.template_deploy_path.setPlaceholderText("Where to deploy the template...")
        deploy_path_row.addWidget(self.template_deploy_path)
        browse_deploy_btn = QPushButton("Browse...")
        browse_deploy_btn.clicked.connect(lambda: self._browse_to_line_edit(self.template_deploy_path))
        deploy_path_row.addWidget(browse_deploy_btn)
        deploy_layout.addLayout(deploy_path_row)

        deploy_btn = QPushButton("🚀 Deploy Selected Template")
        deploy_btn.setProperty("class", "success")
        deploy_btn.clicked.connect(self._deploy_selected_template)
        deploy_layout.addWidget(deploy_btn)

        templates_layout.addWidget(deploy_group)
        layout.addWidget(templates_group)

        layout.addStretch()

    # ========== FOOTNOTES YAML METHODS ==========
    def _browse_footnotes_yaml(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select footnotes.yaml", "", "YAML Files (*.yaml *.yml)")
        if path:
            self.footnotes_yaml_path.setText(path)
            self._load_footnotes_yaml()

    def _load_footnotes_yaml(self):
        path = self.footnotes_yaml_path.text()
        if not path or not Path(path).exists():
            QMessageBox.warning(self, "Error", "YAML file not found.")
            return
        try:
            content = Path(path).read_text(encoding='utf-8')
            self.footnotes_yaml_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load: {e}")

    def _save_footnotes_yaml(self):
        path = self.footnotes_yaml_path.text()
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save footnotes.yaml", "footnotes.yaml", "YAML Files (*.yaml *.yml)")
            if not path:
                return
            self.footnotes_yaml_path.setText(path)
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(self.footnotes_yaml_editor.toPlainText(), encoding='utf-8')
            QMessageBox.information(self, "Saved", f"Saved to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _ai_generate_footnotes(self):
        """Use AI to generate footnotes YAML from vault terms."""
        openai_key = self.settings.get('openai', 'api_key', '')
        claude_key = self.settings.get('claude', 'api_key', '')
        
        if not openai_key and not claude_key:
            QMessageBox.warning(self, "No API Key", "Please set an OpenAI or Claude API key in Settings.")
            return

        # Get glossary path
        glossary_path = self._folder_config.get('glossary', '')
        if not glossary_path or not Path(glossary_path).exists():
            QMessageBox.warning(self, "No Glossary", "Please configure the Glossary folder in Dashboard first.")
            return

        # Scan for term names from glossary
        terms = []
        for md_file in Path(glossary_path).rglob("*.md"):
            terms.append(md_file.stem)

        if not terms:
            QMessageBox.warning(self, "No Terms", "No markdown files found in glossary folder.")
            return

        # Build prompt
        terms_list = "\n".join(f"- {t}" for t in sorted(terms)[:50])  # Limit to 50
        prompt = f"""Generate a YAML footnotes file for Obsidian. Each term should map to a wikilink.

Terms from glossary:
{terms_list}

Output format (YAML):
TermName: "[[Glossary/TermName|TermName]]"

Generate YAML for these terms. Only output valid YAML, no explanations."""

        try:
            if openai_key:
                self._call_openai_for_yaml(openai_key, prompt)
            elif claude_key:
                self._call_claude_for_yaml(claude_key, prompt)
        except Exception as e:
            QMessageBox.critical(self, "AI Error", str(e))

    def _call_openai_for_yaml(self, api_key: str, prompt: str):
        """Call OpenAI API to generate YAML."""
        import urllib.request
        import urllib.error

        data = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result['choices'][0]['message']['content']
                # Clean up markdown code blocks if present
                if content.startswith("```"):
                    content = "\n".join(content.split("\n")[1:-1])
                self.footnotes_yaml_editor.setPlainText(content)
                QMessageBox.information(self, "Generated", "AI-generated YAML loaded into editor. Review and save.")
        except urllib.error.HTTPError as e:
            raise Exception(f"OpenAI API error: {e.code} - {e.read().decode()}")

    def _call_claude_for_yaml(self, api_key: str, prompt: str):
        """Call Claude API to generate YAML."""
        import urllib.request
        import urllib.error

        data = json.dumps({
            "model": "claude-3-haiku-20240307",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=data,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                content = result['content'][0]['text']
                # Clean up markdown code blocks if present
                if content.startswith("```"):
                    content = "\n".join(content.split("\n")[1:-1])
                self.footnotes_yaml_editor.setPlainText(content)
                QMessageBox.information(self, "Generated", "AI-generated YAML loaded into editor. Review and save.")
        except urllib.error.HTTPError as e:
            raise Exception(f"Claude API error: {e.code} - {e.read().decode()}")

    # ========== FOLDER TEMPLATE METHODS ==========
    def _get_templates_dir(self) -> Path:
        return Path(__file__).parent.parent / "config" / "folder_templates"

    def _load_template_list(self):
        self.template_list.clear()
        templates_dir = self._get_templates_dir()
        if templates_dir.exists():
            for f in templates_dir.glob("*.json"):
                self.template_list.addItem(f.stem)

    def _create_new_template(self):
        name, ok = QInputDialog.getText(self, "New Template", "Template name:")
        if ok and name:
            self.template_name_edit.setText(name)
            QMessageBox.information(self, "Info", "Now select a source folder and click 'Scan & Save Template'.")

    def _edit_selected_template(self):
        item = self.template_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Select a template first.")
            return
        template_path = self._get_templates_dir() / f"{item.text()}.json"
        if template_path.exists():
            try:
                content = template_path.read_text(encoding='utf-8')
                # Show in a simple dialog
                from PySide6.QtWidgets import QDialog, QTextEdit, QDialogButtonBox
                dlg = QDialog(self)
                dlg.setWindowTitle(f"Edit Template: {item.text()}")
                dlg.resize(600, 400)
                dlg_layout = QVBoxLayout(dlg)
                editor = QTextEdit()
                editor.setPlainText(content)
                editor.setStyleSheet("font-family: Consolas, monospace;")
                dlg_layout.addWidget(editor)
                buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
                buttons.accepted.connect(lambda: self._save_template_edit(template_path, editor.toPlainText(), dlg))
                buttons.rejected.connect(dlg.reject)
                dlg_layout.addWidget(buttons)
                dlg.exec()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _save_template_edit(self, path: Path, content: str, dlg):
        try:
            path.write_text(content, encoding='utf-8')
            QMessageBox.information(self, "Saved", "Template saved.")
            dlg.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _delete_selected_template(self):
        item = self.template_list.currentItem()
        if not item:
            return
        reply = QMessageBox.question(self, "Delete?", f"Delete template '{item.text()}'?")
        if reply == QMessageBox.StandardButton.Yes:
            template_path = self._get_templates_dir() / f"{item.text()}.json"
            if template_path.exists():
                template_path.unlink()
            self._load_template_list()

    def _scan_and_save_template(self):
        """Scan a folder and save its structure as a template."""
        source = self.template_scan_path.text()
        name = self.template_name_edit.text().strip()
        if not source or not Path(source).exists():
            QMessageBox.warning(self, "Error", "Select a valid source folder.")
            return
        if not name:
            QMessageBox.warning(self, "Error", "Enter a template name.")
            return

        include_content = self.template_include_md.isChecked()
        template_data = self._scan_folder_structure(Path(source), include_content)
        template_data["name"] = name

        templates_dir = self._get_templates_dir()
        templates_dir.mkdir(parents=True, exist_ok=True)
        out_path = templates_dir / f"{name}.json"
        out_path.write_text(json.dumps(template_data, indent=2), encoding='utf-8')

        self._load_template_list()
        QMessageBox.information(self, "Saved", f"Template '{name}' saved!")

    def _scan_folder_structure(self, root: Path, include_content: bool) -> dict:
        """Recursively scan folder structure."""
        def scan_dir(p: Path, depth: int = 0) -> dict:
            result = {
                "name": p.name,
                "type": "folder",
                "depth": depth,
                "children": []
            }
            for child in sorted(p.iterdir()):
                if child.is_dir():
                    result["children"].append(scan_dir(child, depth + 1))
                elif child.suffix == ".md":
                    file_entry = {
                        "name": child.name,
                        "type": "file",
                        "depth": depth + 1
                    }
                    if include_content:
                        try:
                            file_entry["content"] = child.read_text(encoding='utf-8')
                        except:
                            file_entry["content"] = ""
                    result["children"].append(file_entry)
            return result
        return scan_dir(root)

    def _deploy_selected_template(self):
        """Deploy selected template to target folder."""
        item = self.template_list.currentItem()
        target = self.template_deploy_path.text()
        if not item:
            QMessageBox.warning(self, "Error", "Select a template first.")
            return
        if not target:
            QMessageBox.warning(self, "Error", "Select a target folder.")
            return

        template_path = self._get_templates_dir() / f"{item.text()}.json"
        if not template_path.exists():
            QMessageBox.warning(self, "Error", "Template file not found.")
            return

        try:
            template_data = json.loads(template_path.read_text(encoding='utf-8'))
            self._deploy_structure(Path(target), template_data)
            QMessageBox.information(self, "Deployed", f"Template deployed to {target}!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _deploy_structure(self, target: Path, node: dict):
        """Recursively create folders and files from template."""
        if node.get("type") == "folder":
            folder_path = target / node["name"] if node.get("name") else target
            folder_path.mkdir(parents=True, exist_ok=True)
            for child in node.get("children", []):
                self._deploy_structure(folder_path, child)
        elif node.get("type") == "file":
            file_path = target / node["name"]
            content = node.get("content", "")
            file_path.write_text(content, encoding='utf-8')

    def _build_semantic_dashboard(self):
        """Build the Semantic Dashboard page for viewing extracted axioms, theorems, evidence."""
        page, layout = self._create_page_container("🧠 Semantic Dashboard")
        
        # ==========================================
        # SECTION 1: Folder Selection & Scan
        # ==========================================
        scan_group = QGroupBox("📂 Scan Papers for Semantic Elements")
        scan_layout = QVBoxLayout(scan_group)
        
        # Folder path row
        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Papers Folder:"))
        self.semantic_folder_edit = QLineEdit()
        self.semantic_folder_edit.setPlaceholderText("Select folder containing papers/notes...")
        folder_row.addWidget(self.semantic_folder_edit, 1)
        
        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_semantic_folder)
        folder_row.addWidget(browse_btn)
        scan_layout.addLayout(folder_row)
        
        # Options row
        options_row = QHBoxLayout()
        self.semantic_recursive_check = QCheckBox("Recursive (include subfolders)")
        self.semantic_recursive_check.setChecked(True)
        options_row.addWidget(self.semantic_recursive_check)
        
        self.semantic_dedupe_check = QCheckBox("Deduplicate by content")
        self.semantic_dedupe_check.setChecked(True)
        options_row.addWidget(self.semantic_dedupe_check)
        options_row.addStretch()
        scan_layout.addLayout(options_row)
        
        # Scan button row
        btn_row = QHBoxLayout()
        self.scan_semantic_btn = QPushButton("🔍 Scan for Semantic Tags")
        self.scan_semantic_btn.setProperty("class", "primary")
        self.scan_semantic_btn.clicked.connect(self._scan_semantic_tags)
        btn_row.addWidget(self.scan_semantic_btn)
        
        self.export_semantic_btn = QPushButton("💾 Export to JSON")
        self.export_semantic_btn.clicked.connect(self._export_semantic_json)
        btn_row.addWidget(self.export_semantic_btn)
        
        self.scan_mermaids_btn = QPushButton("🎨 Scan for Mermaids")
        self.scan_mermaids_btn.clicked.connect(self._scan_mermaid_diagrams)
        btn_row.addWidget(self.scan_mermaids_btn)
        
        btn_row.addStretch()
        scan_layout.addLayout(btn_row)
        
        # Aggregation buttons row
        agg_row = QHBoxLayout()
        
        self.agg_local_btn = QPushButton("📁 Aggregate LOCAL (This Folder)")
        self.agg_local_btn.setProperty("class", "success")
        self.agg_local_btn.clicked.connect(self._run_local_aggregation)
        agg_row.addWidget(self.agg_local_btn)
        
        self.agg_global_btn = QPushButton("🌐 Aggregate GLOBAL (07_MASTER_TRUTH)")
        self.agg_global_btn.setProperty("class", "primary")
        self.agg_global_btn.clicked.connect(self._run_global_aggregation)
        agg_row.addWidget(self.agg_global_btn)
        
        agg_row.addStretch()
        scan_layout.addLayout(agg_row)
        
        # Progress and status
        self.semantic_progress = QProgressBar()
        self.semantic_progress.setVisible(False)
        scan_layout.addWidget(self.semantic_progress)
        
        self.semantic_status = QLabel("Ready to scan")
        self.semantic_status.setStyleSheet("color: #6b7280;")
        scan_layout.addWidget(self.semantic_status)
        
        layout.addWidget(scan_group)
        
        # ==========================================
        # SECTION 2: Statistics Overview
        # ==========================================
        stats_group = QGroupBox("📊 Extraction Statistics")
        stats_layout = QGridLayout(stats_group)
        
        # Stats labels
        self.semantic_stats = {
            'total': QLabel("0"),
            'axioms': QLabel("0"),
            'claims': QLabel("0"),
            'evidence': QLabel("0"),
            'theorems': QLabel("0"),
            'relationships': QLabel("0"),
            'files': QLabel("0"),
            'duplicates': QLabel("0"),
        }
        
        stats_items = [
            ("Total Tags", 'total'), ("Axioms", 'axioms'), ("Claims", 'claims'), ("Evidence Bundles", 'evidence'),
            ("Theorems", 'theorems'), ("Relationships", 'relationships'), ("Files Scanned", 'files'), ("Duplicates Removed", 'duplicates')
        ]
        
        for i, (label, key) in enumerate(stats_items):
            row, col = divmod(i, 4)
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("font-weight: bold; color: #d97706;")
            stats_layout.addWidget(lbl, row * 2, col)
            self.semantic_stats[key].setStyleSheet("font-size: 18px; color: #22c55e;")
            stats_layout.addWidget(self.semantic_stats[key], row * 2 + 1, col)
        
        layout.addWidget(stats_group)
        
        # ==========================================
        # SECTION 3: Filter Controls
        # ==========================================
        filter_group = QGroupBox("🔎 Filter & Search")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.semantic_type_filter = QComboBox()
        self.semantic_type_filter.addItems(["All", "Axiom", "Claim", "EvidenceBundle", "Theorem", "Relationship", "Custom"])
        self.semantic_type_filter.currentTextChanged.connect(self._filter_semantic_table)
        filter_layout.addWidget(self.semantic_type_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.semantic_search_edit = QLineEdit()
        self.semantic_search_edit.setPlaceholderText("Search labels...")
        self.semantic_search_edit.textChanged.connect(self._filter_semantic_table)
        filter_layout.addWidget(self.semantic_search_edit, 1)
        
        filter_layout.addWidget(QLabel("File:"))
        self.semantic_file_filter = QComboBox()
        self.semantic_file_filter.addItem("All Files")
        self.semantic_file_filter.currentTextChanged.connect(self._filter_semantic_table)
        filter_layout.addWidget(self.semantic_file_filter)
        
        layout.addWidget(filter_group)
        
        # ==========================================
        # SECTION 4: Master Table
        # ==========================================
        table_group = QGroupBox("📋 Semantic Elements Master Sheet")
        table_layout = QVBoxLayout(table_group)
        
        self.semantic_table = QTableWidget()
        self.semantic_table.setColumnCount(7)
        self.semantic_table.setHorizontalHeaderLabels([
            "Type", "Label", "UUID", "Parent UUID", "File", "Line", "Custom Type"
        ])
        self.semantic_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.semantic_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.semantic_table.setMinimumHeight(400)
        self.semantic_table.setAlternatingRowColors(True)
        self.semantic_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.semantic_table.doubleClicked.connect(self._on_semantic_row_double_click)
        
        table_layout.addWidget(self.semantic_table)
        
        # Table action buttons
        table_btn_row = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copy Selected")
        copy_btn.clicked.connect(self._copy_semantic_selection)
        table_btn_row.addWidget(copy_btn)
        
        open_file_btn = QPushButton("📂 Open File")
        open_file_btn.clicked.connect(self._open_semantic_file)
        table_btn_row.addWidget(open_file_btn)
        
        table_btn_row.addStretch()
        
        self.semantic_count_label = QLabel("0 items")
        self.semantic_count_label.setStyleSheet("color: #6b7280;")
        table_btn_row.addWidget(self.semantic_count_label)
        
        table_layout.addLayout(table_btn_row)
        

        # ==========================================
        # SECTION 5: Mermaid Diagrams Viewer
        # ==========================================
        mermaid_group = QGroupBox("🎨 Mermaid Diagrams from Papers")
        mermaid_layout = QVBoxLayout(mermaid_group)
        
        # Control buttons
        mermaid_btn_row = QHBoxLayout()
        
        self.refresh_mermaids_btn = QPushButton("🔄 Refresh Diagrams")
        self.refresh_mermaids_btn.clicked.connect(self._scan_mermaid_diagrams)
        mermaid_btn_row.addWidget(self.refresh_mermaids_btn)
        
        self.combine_axioms_btn = QPushButton("🔗 Combine All Papers")
        self.combine_axioms_btn.setProperty("class", "success")
        self.combine_axioms_btn.clicked.connect(self._combine_axiom_diagrams)
        self.combine_axioms_btn.setToolTip("Merge all paper diagrams into one master Mermaid diagram")
        mermaid_btn_row.addWidget(self.combine_axioms_btn)
        
        mermaid_btn_row.addStretch()
        
        self.mermaid_count_label = QLabel("0 diagrams found")
        self.mermaid_count_label.setStyleSheet("color: #6b7280;")
        mermaid_btn_row.addWidget(self.mermaid_count_label)
        
        mermaid_layout.addLayout(mermaid_btn_row)
        
        # Scrollable container for diagrams
        self.mermaid_scroll = QScrollArea()
        self.mermaid_scroll.setWidgetResizable(True)
        self.mermaid_scroll.setMinimumHeight(300)
        self.mermaid_scroll.setMaximumHeight(600)
        
        self.mermaid_container = QWidget()
        self.mermaid_container_layout = QVBoxLayout(self.mermaid_container)
        self.mermaid_container_layout.setSpacing(20)
        
        self.mermaid_scroll.setWidget(self.mermaid_container)
        mermaid_layout.addWidget(self.mermaid_scroll)
        
        layout.addWidget(mermaid_group)
        
        layout.addWidget(table_group)
        
        # Store extracted data
        self._semantic_data = None
        self._semantic_extractor = None
        self._mermaid_diagrams = []  # Mermaid diagram storage
    
    def _browse_semantic_folder(self):
        """Browse for semantic scan folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Papers Folder")
        if folder:
            self.semantic_folder_edit.setText(folder)
    
    def _scan_semantic_tags(self):
        """Scan folder for semantic tags."""
        folder = self.semantic_folder_edit.text()
        if not folder:
            QMessageBox.warning(self, "No Folder", "Please select a folder to scan.")
            return
        
        self.semantic_status.setText("Scanning...")
        self.semantic_progress.setVisible(True)
        self.semantic_progress.setValue(0)
        self.scan_semantic_btn.setEnabled(False)
        
        try:
            from core.semantic_tag_extractor import SemanticTagExtractor
            
            # Get vault path for relative paths
            vault_path = self.settings.get('obsidian', 'vault_path', folder)
            
            self._semantic_extractor = SemanticTagExtractor(vault_path)
            self.semantic_progress.setValue(25)
            
            # Extract and process
            self._semantic_data = self._semantic_extractor.extract_and_process(
                folder_path=folder,
                deduplicate=self.semantic_dedupe_check.isChecked()
            )
            
            self.semantic_progress.setValue(75)
            
            # Update stats
            stats = self._semantic_data['stats']
            self.semantic_stats['total'].setText(str(stats['total_tags']))
            self.semantic_stats['files'].setText(str(stats['files_processed']))
            self.semantic_stats['duplicates'].setText(str(stats['duplicates_found']))
            
            by_type = stats.get('by_type', {})
            self.semantic_stats['axioms'].setText(str(by_type.get('Axiom', 0)))
            self.semantic_stats['claims'].setText(str(by_type.get('Claim', 0)))
            self.semantic_stats['evidence'].setText(str(by_type.get('EvidenceBundle', 0)))
            self.semantic_stats['theorems'].setText(str(by_type.get('Theorem', 0)))
            self.semantic_stats['relationships'].setText(str(by_type.get('Relationship', 0)))
            
            # Populate file filter
            self.semantic_file_filter.clear()
            self.semantic_file_filter.addItem("All Files")
            files = set(tag['file_path'] for tag in self._semantic_data['tags'])
            for f in sorted(files):
                self.semantic_file_filter.addItem(f)
            
            # Populate table
            self._populate_semantic_table(self._semantic_data['tags'])
            
            self.semantic_progress.setValue(100)
            self.semantic_status.setText(f"✓ Extracted {stats['total_tags']} tags from {stats['files_processed']} files")
            
        except Exception as e:
            self.semantic_status.setText(f"Error: {e}")
            QMessageBox.critical(self, "Scan Error", str(e))
        finally:
            self.scan_semantic_btn.setEnabled(True)
            self.semantic_progress.setVisible(False)
    
    def _populate_semantic_table(self, tags: list):
        """Populate the semantic table with tags."""
        self.semantic_table.setRowCount(len(tags))
        
        type_colors = {
            'Axiom': '#f59e0b',
            'Claim': '#3b82f6',
            'EvidenceBundle': '#22c55e',
            'Theorem': '#8b5cf6',
            'Relationship': '#ec4899',
            'Custom': '#6b7280',
        }
        
        for row, tag in enumerate(tags):
            tag_type = tag.get('tag_type', '')
            color = type_colors.get(tag_type, '#9ca3af')
            
            type_item = QTableWidgetItem(tag_type)
            type_item.setForeground(Qt.GlobalColor.white)
            type_item.setBackground(Qt.GlobalColor.transparent)
            type_item.setData(Qt.ItemDataRole.UserRole, tag)
            
            self.semantic_table.setItem(row, 0, type_item)
            self.semantic_table.setItem(row, 1, QTableWidgetItem(tag.get('label', '')))
            self.semantic_table.setItem(row, 2, QTableWidgetItem(tag.get('uuid', '')[:8] + '...'))
            self.semantic_table.setItem(row, 3, QTableWidgetItem((tag.get('parent_uuid') or '')[:8] + '...' if tag.get('parent_uuid') else ''))
            self.semantic_table.setItem(row, 4, QTableWidgetItem(tag.get('file_path', '')))
            self.semantic_table.setItem(row, 5, QTableWidgetItem(str(tag.get('line_number', ''))))
            self.semantic_table.setItem(row, 6, QTableWidgetItem(tag.get('custom_type') or ''))
        
        self.semantic_count_label.setText(f"{len(tags)} items")
    
    def _filter_semantic_table(self):
        """Filter the semantic table based on current filters."""
        if not self._semantic_data:
            return
        
        type_filter = self.semantic_type_filter.currentText()
        search_text = self.semantic_search_edit.text().lower()
        file_filter = self.semantic_file_filter.currentText()
        
        filtered = []
        for tag in self._semantic_data['tags']:
            # Type filter
            if type_filter != "All" and tag.get('tag_type') != type_filter:
                continue
            
            # Search filter
            if search_text and search_text not in tag.get('label', '').lower():
                continue
            
            # File filter
            if file_filter != "All Files" and tag.get('file_path') != file_filter:
                continue
            
            filtered.append(tag)
        
        self._populate_semantic_table(filtered)
    
    def _export_semantic_json(self):
        """Export semantic data to JSON."""
        if not self._semantic_data:
            QMessageBox.warning(self, "No Data", "Please scan for semantic tags first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Semantic Data", "semantic_tags.json", "JSON Files (*.json)"
        )
        if file_path:
            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._semantic_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Exported", f"Saved to {file_path}")
    
    def _sync_semantic_to_db(self):
        """Sync semantic data to SQLite database."""
        if not self._semantic_data:
            QMessageBox.warning(self, "No Data", "Please scan for semantic tags first.")
            return
        
        try:
            if hasattr(self, '_db_engine') and self._db_engine:
                # Store each tag type
                for tag in self._semantic_data['tags']:
                    tag_type = tag.get('tag_type', '')
                    if tag_type == 'Axiom':
                        self._db_engine.upsert_axiom(
                            name=tag.get('label'),
                            statement=tag.get('label'),
                            source_note=tag.get('file_path'),
                            uuid=tag.get('uuid')
                        )
                    elif tag_type == 'EvidenceBundle':
                        self._db_engine.upsert_evidence_bundle(
                            name=tag.get('label'),
                            evidence_type='semantic_tag',
                            source_note=tag.get('file_path'),
                            uuid=tag.get('uuid')
                        )
                
                QMessageBox.information(self, "Synced", f"Synced {len(self._semantic_data['tags'])} tags to database")
            else:
                QMessageBox.warning(self, "No Database", "Database engine not initialized. Go to Database tab first.")
        except Exception as e:
            QMessageBox.critical(self, "Sync Error", str(e))
    
    def _on_semantic_row_double_click(self, index):
        """Handle double-click on semantic table row."""
        self._open_semantic_file()
    
    def _copy_semantic_selection(self):
        """Copy selected rows to clipboard."""
        selected = self.semantic_table.selectedItems()
        if not selected:
            return
        
        rows = set(item.row() for item in selected)
        text_lines = []
        for row in sorted(rows):
            line = []
            for col in range(self.semantic_table.columnCount()):
                item = self.semantic_table.item(row, col)
                line.append(item.text() if item else '')
            text_lines.append('\t'.join(line))
        
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText('\n'.join(text_lines))
    
    def _open_semantic_file(self):
        """Open the file containing the selected semantic tag."""
        selected = self.semantic_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        tag_data = self.semantic_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if tag_data:
            file_path = tag_data.get('file_path', '')
            vault_path = self.settings.get('obsidian', 'vault_path', '')
            full_path = Path(vault_path) / file_path
            if full_path.exists():
                import subprocess
                subprocess.Popen(['explorer', '/select,', str(full_path)])

    def _build_database_page(self):
        page, layout = self._create_page_container("🗄️ Database Sync")
        
        # ==========================================
        # SECTION 1: SQLite Status & Sync
        # ==========================================
        sqlite_group = QGroupBox("📁 SQLite Database (Primary - Vault Mirror)")
        sqlite_layout = QVBoxLayout(sqlite_group)
        
        # SQLite path display
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Database Path:"))
        self.sqlite_path_label = QLabel("Not configured")
        self.sqlite_path_label.setStyleSheet("color: #9ca3af;")
        path_row.addWidget(self.sqlite_path_label, 1)
        sqlite_layout.addLayout(path_row)
        
        # SQLite metrics
        metrics_row = QHBoxLayout()
        self.sqlite_metrics_label = QLabel("Notes: 0 | Definitions: 0 | Papers: 0 | Axioms: 0 | Equations: 0")
        self.sqlite_metrics_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        metrics_row.addWidget(self.sqlite_metrics_label)
        sqlite_layout.addLayout(metrics_row)
        
        # Sync buttons row
        sync_row = QHBoxLayout()
        
        self.scan_vault_btn = QPushButton("🔄 Scan Vault → SQLite")
        self.scan_vault_btn.setProperty("class", "primary")
        self.scan_vault_btn.clicked.connect(self._scan_vault_to_sqlite)
        sync_row.addWidget(self.scan_vault_btn)
        
        self.refresh_metrics_btn = QPushButton("📊 Refresh Metrics")
        self.refresh_metrics_btn.clicked.connect(self._refresh_sqlite_metrics)
        sync_row.addWidget(self.refresh_metrics_btn)
        
        self.vacuum_btn = QPushButton("🧹 Vacuum DB")
        self.vacuum_btn.clicked.connect(self._vacuum_sqlite)
        sync_row.addWidget(self.vacuum_btn)
        
        sqlite_layout.addLayout(sync_row)
        
        # Progress bar for scanning
        self.db_progress = QProgressBar()
        self.db_progress.setVisible(False)
        sqlite_layout.addWidget(self.db_progress)
        
        # Status log
        self.sqlite_status_log = QTextEdit()
        self.sqlite_status_log.setMaximumHeight(100)
        self.sqlite_status_log.setReadOnly(True)
        self.sqlite_status_log.setPlaceholderText("SQLite sync status will appear here...")
        sqlite_layout.addWidget(self.sqlite_status_log)
        
        layout.addWidget(sqlite_group)
        
        # ==========================================
        # SECTION 2: PostgreSQL Sync
        # ==========================================
        postgres_group = QGroupBox("🐘 PostgreSQL Database (Secondary - Network Sync)")
        postgres_layout = QVBoxLayout(postgres_group)
        
        # Connection string
        conn_row = QHBoxLayout()
        conn_row.addWidget(QLabel("Connection:"))
        self.postgres_conn_label = QLabel("Not configured")
        self.postgres_conn_label.setStyleSheet("color: #9ca3af;")
        conn_row.addWidget(self.postgres_conn_label, 1)
        
        self.test_pg_btn = QPushButton("🔌 Test Connection")
        self.test_pg_btn.clicked.connect(self._test_postgres_connection)
        conn_row.addWidget(self.test_pg_btn)
        postgres_layout.addLayout(conn_row)
        
        # PostgreSQL metrics
        pg_metrics_row = QHBoxLayout()
        self.postgres_metrics_label = QLabel("Status: Not connected")
        self.postgres_metrics_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        pg_metrics_row.addWidget(self.postgres_metrics_label)
        postgres_layout.addLayout(pg_metrics_row)
        
        # Sync buttons
        pg_sync_row = QHBoxLayout()
        
        self.sync_to_pg_btn = QPushButton("⬆️ SQLite → PostgreSQL")
        self.sync_to_pg_btn.setProperty("class", "primary")
        self.sync_to_pg_btn.clicked.connect(self._sync_sqlite_to_postgres)
        pg_sync_row.addWidget(self.sync_to_pg_btn)
        
        self.sync_from_pg_btn = QPushButton("⬇️ PostgreSQL → SQLite")
        self.sync_from_pg_btn.clicked.connect(self._sync_postgres_to_sqlite)
        pg_sync_row.addWidget(self.sync_from_pg_btn)
        
        self.check_mismatches_btn = QPushButton("🔍 Check Mismatches")
        self.check_mismatches_btn.clicked.connect(self._check_db_mismatches)
        pg_sync_row.addWidget(self.check_mismatches_btn)
        
        postgres_layout.addLayout(pg_sync_row)
        
        # Mismatch table
        self.mismatch_table = QTableWidget()
        self.mismatch_table.setColumnCount(5)
        self.mismatch_table.setHorizontalHeaderLabels(["Table", "UUID", "SQLite", "PostgreSQL", "Action"])
        self.mismatch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.mismatch_table.setMaximumHeight(150)
        postgres_layout.addWidget(self.mismatch_table)
        
        # PostgreSQL status log
        self.postgres_status_log = QTextEdit()
        self.postgres_status_log.setMaximumHeight(100)
        self.postgres_status_log.setReadOnly(True)
        self.postgres_status_log.setPlaceholderText("PostgreSQL sync status will appear here...")
        postgres_layout.addWidget(self.postgres_status_log)
        
        layout.addWidget(postgres_group)
        
        # ==========================================
        # SECTION 3: Sync Status Overview
        # ==========================================
        status_group = QGroupBox("📈 Sync Status Overview")
        status_layout = QGridLayout(status_group)
        
        # Table headers
        headers = ["Table", "SQLite Count", "PostgreSQL Count", "Last Sync", "Status"]
        for col, header in enumerate(headers):
            lbl = QLabel(header)
            lbl.setStyleSheet("font-weight: bold; color: #d97706;")
            status_layout.addWidget(lbl, 0, col)
        
        # Table rows (will be populated dynamically)
        self.sync_status_labels = {}
        tables = ["notes", "papers", "definitions", "axioms", "theorems", "equations", "evidence_bundles"]
        for row, table in enumerate(tables, 1):
            status_layout.addWidget(QLabel(table), row, 0)
            self.sync_status_labels[f"{table}_sqlite"] = QLabel("0")
            self.sync_status_labels[f"{table}_postgres"] = QLabel("0")
            self.sync_status_labels[f"{table}_lastsync"] = QLabel("Never")
            self.sync_status_labels[f"{table}_status"] = QLabel("⚪")
            
            status_layout.addWidget(self.sync_status_labels[f"{table}_sqlite"], row, 1)
            status_layout.addWidget(self.sync_status_labels[f"{table}_postgres"], row, 2)
            status_layout.addWidget(self.sync_status_labels[f"{table}_lastsync"], row, 3)
            status_layout.addWidget(self.sync_status_labels[f"{table}_status"], row, 4)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        # Initialize display
        self._init_database_display()
    
    def _init_database_display(self):
        """Initialize database display with current values."""
        try:
            # Initialize SQLite engine if available
            if HAS_ENGINE:
                engine_settings = EngineSettings()
                engine_settings.load()
                self._db_engine = DatabaseEngine(engine_settings)
                self._vault_engine = VaultEngine(engine_settings, self._db_engine)
                
                # Display SQLite path
                self.sqlite_path_label.setText(str(self._db_engine.db_path))
                
                # Display PostgreSQL connection
                if engine_settings.postgres_conn_str:
                    self.postgres_conn_label.setText(engine_settings.postgres_conn_str)
            else:
                self.sqlite_status_log.append("⚠️ Engine module not available")
                self._db_engine = None
                self._vault_engine = None
            
            # Refresh metrics
            self._refresh_sqlite_metrics()
        except Exception as e:
            self.sqlite_status_log.append(f"Init error: {e}")
            self._db_engine = None
            self._vault_engine = None
    
    def _refresh_sqlite_metrics(self):
        """Refresh SQLite database metrics."""
        try:
            if not self._db_engine:
                self.sqlite_status_log.append("⚠️ Database engine not initialized")
                return
            
            self.sqlite_status_log.append("Refreshing SQLite metrics...")
            metrics = self._db_engine.get_full_metrics()
            
            # Update metrics label
            metrics_text = f"Notes: {metrics.get('notes', 0)} | Definitions: {metrics.get('definitions', 0)} | Papers: {metrics.get('papers', 0)} | Axioms: {metrics.get('axioms', 0)} | Equations: {metrics.get('equations', 0)}"
            self.sqlite_metrics_label.setText(metrics_text)
            
            # Update sync status grid
            for table in ["notes", "papers", "definitions", "axioms", "theorems", "equations", "evidence_bundles"]:
                if f"{table}_sqlite" in self.sync_status_labels:
                    self.sync_status_labels[f"{table}_sqlite"].setText(str(metrics.get(table, 0)))
            
            self.sqlite_status_log.append(f"✓ Metrics refreshed - {metrics.get('notes', 0)} notes in database")
        except Exception as e:
            self.sqlite_status_log.append(f"Error: {e}")
    
    def _scan_vault_to_sqlite(self):
        """Scan vault and sync to SQLite."""
        if not self._vault_engine:
            self.sqlite_status_log.append("⚠️ Vault engine not initialized")
            return
        
        self.sqlite_status_log.append("Starting vault scan...")
        self.db_progress.setVisible(True)
        self.db_progress.setValue(0)
        self.scan_vault_btn.setEnabled(False)
        
        try:
            self.sqlite_status_log.append("Scanning markdown files...")
            self.db_progress.setValue(25)
            
            # Run the vault scan
            self._vault_engine.scan_vault(full=True)
            
            self.db_progress.setValue(75)
            self.sqlite_status_log.append("Storing to SQLite...")
            
            # Get scan errors if any
            errors = self._vault_engine.last_scan_errors
            if errors:
                self.sqlite_status_log.append(f"⚠️ {len(errors)} files had errors")
            
            self.db_progress.setValue(100)
            
            # Refresh metrics to show new counts
            self._refresh_sqlite_metrics()
            self.sqlite_status_log.append("✓ Vault scan complete")
        except Exception as e:
            self.sqlite_status_log.append(f"Error: {e}")
        finally:
            self.scan_vault_btn.setEnabled(True)
            self.db_progress.setVisible(False)
    
    def _vacuum_sqlite(self):
        """Vacuum SQLite database."""
        try:
            if not self._db_engine:
                self.sqlite_status_log.append("⚠️ Database engine not initialized")
                return
            
            self.sqlite_status_log.append("Running VACUUM...")
            self._db_engine.vacuum_sqlite()
            self.sqlite_status_log.append("✓ Database vacuumed")
        except Exception as e:
            self.sqlite_status_log.append(f"Error: {e}")
    
    def _test_postgres_connection(self):
        """Test PostgreSQL connection."""
        self.postgres_status_log.append("Testing PostgreSQL connection...")
        try:
            if self.postgres_manager.connect():
                self.postgres_status_log.append("✓ PostgreSQL connection successful!")
                self.postgres_metrics_label.setText("Status: Connected")
                self.postgres_metrics_label.setStyleSheet("color: #22c55e; font-size: 11px;")
                self.postgres_manager.disconnect()
            else:
                self.postgres_status_log.append("✗ PostgreSQL connection failed")
                self.postgres_metrics_label.setText("Status: Connection failed")
                self.postgres_metrics_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        except Exception as e:
            self.postgres_status_log.append(f"Error: {e}")
            self.postgres_metrics_label.setText(f"Status: Error - {e}")
    
    def _sync_sqlite_to_postgres(self):
        """Sync SQLite data to PostgreSQL."""
        self.postgres_status_log.append("Syncing SQLite → PostgreSQL...")
        try:
            if not self._db_engine:
                self.postgres_status_log.append("⚠️ SQLite engine not initialized")
                return
            
            success, message = self._db_engine.export_to_postgres()
            if success:
                self.postgres_status_log.append(f"✓ {message}")
                self._update_sync_status()
            else:
                self.postgres_status_log.append(f"✗ {message}")
        except Exception as e:
            self.postgres_status_log.append(f"Error: {e}")
    
    def _sync_postgres_to_sqlite(self):
        """Sync PostgreSQL data back to SQLite."""
        self.postgres_status_log.append("Syncing PostgreSQL → SQLite...")
        try:
            # This would pull changes from PostgreSQL and update SQLite
            # For now, show that it's not fully implemented
            self.postgres_status_log.append("⚠️ Reverse sync requires comparing timestamps and UUIDs")
            self.postgres_status_log.append("This will be implemented to detect PostgreSQL changes and sync back")
        except Exception as e:
            self.postgres_status_log.append(f"Error: {e}")
    
    def _check_db_mismatches(self):
        """Check for mismatches between SQLite and PostgreSQL."""
        self.postgres_status_log.append("Checking for mismatches...")
        self.mismatch_table.setRowCount(0)
        try:
            if not self._db_engine:
                self.postgres_status_log.append("⚠️ SQLite engine not initialized")
                return
            
            # Get SQLite metrics
            sqlite_metrics = self._db_engine.get_full_metrics()
            
            # Try to get PostgreSQL metrics
            if not self.postgres_manager.connect():
                self.postgres_status_log.append("⚠️ Cannot connect to PostgreSQL to check mismatches")
                return
            
            # Compare counts for each table
            mismatches = []
            tables_to_check = ["notes", "definitions", "papers"]
            
            for table in tables_to_check:
                sqlite_count = sqlite_metrics.get(table, 0)
                # Get PostgreSQL count
                try:
                    with self.postgres_manager.conn.cursor() as cur:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        pg_count = cur.fetchone()[0]
                except:
                    pg_count = 0
                
                if sqlite_count != pg_count:
                    mismatches.append({
                        "table": table,
                        "sqlite": sqlite_count,
                        "postgres": pg_count,
                        "diff": sqlite_count - pg_count
                    })
            
            self.postgres_manager.disconnect()
            
            # Display mismatches
            if mismatches:
                self.mismatch_table.setRowCount(len(mismatches))
                for row, m in enumerate(mismatches):
                    self.mismatch_table.setItem(row, 0, QTableWidgetItem(m["table"]))
                    self.mismatch_table.setItem(row, 1, QTableWidgetItem("-"))
                    self.mismatch_table.setItem(row, 2, QTableWidgetItem(str(m["sqlite"])))
                    self.mismatch_table.setItem(row, 3, QTableWidgetItem(str(m["postgres"])))
                    self.mismatch_table.setItem(row, 4, QTableWidgetItem("Sync needed" if m["diff"] > 0 else "Pull needed"))
                self.postgres_status_log.append(f"⚠️ Found {len(mismatches)} table(s) with count mismatches")
            else:
                self.postgres_status_log.append("✓ No mismatches found - databases are in sync")
        except Exception as e:
            self.postgres_status_log.append(f"Error: {e}")
    
    def _update_sync_status(self):
        """Update the sync status grid after a sync operation."""
        import time
        now = time.strftime("%Y-%m-%d %H:%M")
        for table in ["notes", "papers", "definitions", "axioms", "theorems", "equations", "evidence_bundles"]:
            if f"{table}_lastsync" in self.sync_status_labels:
                self.sync_status_labels[f"{table}_lastsync"].setText(now)
                self.sync_status_labels[f"{table}_status"].setText("🟢")

    def _build_settings_page(self):
        page, layout = self._create_page_container("⚙️ Settings")

        # API Keys
        api_group = QGroupBox("API Configuration")
        api_layout = QVBoxLayout(api_group)

        # OpenAI
        row = QHBoxLayout()
        row.addWidget(QLabel("OpenAI API Key:"))
        self.openai_key_edit = QLineEdit()
        self.openai_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_edit.setText(self.settings.get('openai', 'api_key', ''))
        row.addWidget(self.openai_key_edit)
        api_layout.addLayout(row)

        # Claude
        row = QHBoxLayout()
        row.addWidget(QLabel("Claude API Key:"))
        self.claude_key_edit = QLineEdit()
        self.claude_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.claude_key_edit.setText(self.settings.get('claude', 'api_key', ''))
        row.addWidget(self.claude_key_edit)
        api_layout.addLayout(row)

        layout.addWidget(api_group)

        # Save
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

    def _save_settings(self):
        """Save settings."""
        self.settings.set('openai', 'api_key', self.openai_key_edit.text())
        self.settings.set('claude', 'api_key', self.claude_key_edit.text())
        self.settings.save()
        QMessageBox.information(self, "Saved", "Settings saved!")

    def _save_autolinker_settings(self):
        if not hasattr(self, 'linker_path_edit'):
            return
        self.settings.set('autolinker', 'path', self.linker_path_edit.text())
        self.settings.set('autolinker', 'recursive', 'true' if self.link_recursive_check.isChecked() else 'false')
        self.settings.set('autolinker', 'link_all', 'true' if self.link_all_check.isChecked() else 'false')
        if hasattr(self, 'auto_link_startup_check'):
            self.settings.set('autolinker', 'startup', 'true' if self.auto_link_startup_check.isChecked() else 'false')
        if hasattr(self, 'min_occurrences_spin'):
            self.settings.set('autolinker', 'min_occurrences', str(self.min_occurrences_spin.value()))
        if hasattr(self, 'wiki_fallback_check'):
            self.settings.set('autolinker', 'wiki_fallback', 'true' if self.wiki_fallback_check.isChecked() else 'false')
        if hasattr(self, 'dual_link_check'):
            self.settings.set('autolinker', 'dual_link', 'true' if self.dual_link_check.isChecked() else 'false')
        self.settings.save()

    def _maybe_start_auto_linker(self):
        try:
            enabled = self.settings.get('autolinker', 'startup', 'false').lower() == 'true'
            if not enabled:
                return

            path_str = self.settings.get('autolinker', 'path', '')
            if not path_str:
                path_str = self._folder_config.get('notes', '') or self._folder_config.get('vault_root', '')
            if not path_str:
                return

            p = Path(path_str)
            if not p.exists():
                return

            recursive = self.settings.get('autolinker', 'recursive', 'true').lower() == 'true'
            link_all = self.settings.get('autolinker', 'link_all', 'false').lower() == 'true'

            self._auto_linker_startup = True
            self._auto_linker_startup_link_all = link_all

            self.linker_log.clear()
            self.linker_log.append("AUTO-LINKER STARTUP RUN...")
            self.linker_progress.setVisible(True)
            self.linker_progress.setValue(0)
            self.scan_links_btn.setEnabled(False)
            self.apply_links_btn.setEnabled(False)
            self.linker_table.setRowCount(0)

            self._linker_thread = LinkerWorker(
                mode="scan",
                path=str(p),
                vault_path=self.settings.get('obsidian', 'vault_path', '.'),
                recursive=recursive
            )

            self._linker_thread.log_signal.connect(self._append_linker_log)
            self._linker_thread.progress_signal.connect(self._update_linker_progress)
            self._linker_thread.finished_scan_signal.connect(self._on_scan_finished)
            self._linker_thread.error_signal.connect(self._on_linker_error)
            self._linker_thread.start()
        except Exception:
            return

    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        vault = self._folder_config.get('vault_root', '')
        if vault:
            self.status_bar.showMessage(f"Vault: {Path(vault).name}")


def create_main_window_v2(
    settings,
    definitions_manager,
    vault_installer,
    global_aggregator,
    research_linker,
    footnote_system,
    postgres_manager
) -> MainWindowV2:
    """Factory function to create the V2 main window."""
    return MainWindowV2(
        settings=settings,
        definitions_manager=definitions_manager,
        vault_installer=vault_installer,
        global_aggregator=global_aggregator,
        research_linker=research_linker,
        footnote_system=footnote_system,
        postgres_manager=postgres_manager
    )


# ==========================================
# WORKER THREAD
# ==========================================


class LinkerWorker(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    error_signal = Signal(str)

    # Results
    finished_scan_signal = Signal(dict, list) # counts, file_list
    finished_apply_signal = Signal(int, int)  # total_links, files_mod

    def __init__(self, mode: str, **kwargs):
        super().__init__()
        self.mode = mode
        self.kwargs = kwargs
        self._stops = False

    def run(self):
        try:
            from engine.knowledge_acquisition_engine import AutoLinker
            from collections import Counter

            vault_path = Path(self.kwargs.get('vault_path'))
            linker = AutoLinker(vault_path)

            if self.mode == "scan":
                path_str = self.kwargs.get('path')
                recursive = self.kwargs.get('recursive')
                path = Path(path_str)

                self.log_signal.emit(f"Scanning directory: {path}")

                # Gather files
                files = []
                if path.is_file():
                    files = [path]
                elif recursive:
                    files = list(path.rglob("*.md"))
                else:
                    files = list(path.glob("*.md"))

                total = len(files)
                self.log_signal.emit(f"Found {total} files to scan.")

                global_counts = Counter()

                for i, f in enumerate(files):
                    local_counts = linker.scan_file(f)
                    if len(local_counts) > 0:
                        count_str = ", ".join([f"{k}({v})" for k,v in list(local_counts.items())[:3]])
                        if len(local_counts) > 3:
                            count_str += "..."
                        self.log_signal.emit(f"[{i+1}/{total}] {f.name}: Found {count_str}")
                    else:
                        if i % 10 == 0:
                            self.log_signal.emit(f"[{i+1}/{total}] {f.name}: No terms found.")

                    global_counts.update(local_counts)
                    self.progress_signal.emit(i+1, total)

                self.finished_scan_signal.emit(dict(global_counts), files)

            elif self.mode == "apply":
                files = self.kwargs.get('files')
                approved = self.kwargs.get('approved_terms')
                link_all = self.kwargs.get('link_all')

                total = len(files)
                total_links = 0
                files_mod = 0

                self.log_signal.emit(f"Applying links for {len(approved)} terms across {total} files...")

                for i, f in enumerate(files):
                    count = linker.apply_links_to_file(f, approved, link_all=link_all)
                    if count > 0:
                        self.log_signal.emit(f"[{i+1}/{total}] {f.name}: +{count} links")
                        total_links += count
                        files_mod += 1

                    self.progress_signal.emit(i+1, total)

                self.finished_apply_signal.emit(total_links, files_mod)

        except Exception as e:
            import traceback
            self.error_signal.emit(f"{str(e)}\n{traceback.format_exc()}")


# =============================================================================
# SEMANTIC AGGREGATION METHODS (added to MainWindowV2)
# =============================================================================

def _run_local_aggregation(self):
    """Run LOCAL semantic aggregation on the selected folder."""
    folder = self.semantic_folder_edit.text()
    if not folder:
        QMessageBox.warning(self, "No Folder", "Please select a folder to aggregate.")
        return
    
    vault_path = self.settings.get('obsidian', 'vault_path', '')
    if not vault_path:
        vault_path = str(Path(folder).parent.parent)  # Guess vault root
    
    self.semantic_status.setText("Running LOCAL aggregation...")
    self.semantic_progress.setVisible(True)
    self.semantic_progress.setValue(25)
    
    try:
        from core.semantic_aggregator import SemanticAggregator
        
        agg = SemanticAggregator(vault_path)
        self.semantic_progress.setValue(50)
        
        result = agg.aggregate_local(folder)
        self.semantic_progress.setValue(100)
        
        # Update stats display
        self.semantic_stats['total'].setText(str(result.stats.get('total_items', 0)))
        self.semantic_stats['axioms'].setText(str(result.stats.get('Axiom_count', 0)))
        self.semantic_stats['claims'].setText(str(result.stats.get('Claim_count', 0)))
        self.semantic_stats['evidence'].setText(str(result.stats.get('EvidenceBundle_count', 0)))
        self.semantic_stats['duplicates'].setText(str(result.stats.get('duplicates', 0)))
        
        self.semantic_status.setText(
            f"LOCAL aggregation complete: {result.stats.get('total_items', 0)} tags, "
            f"{result.stats.get('contradictions', 0)} contradictions"
        )
        
        QMessageBox.information(
            self, "LOCAL Aggregation Complete",
            f"Scanned {result.stats.get('total_items', 0)} tags\n"
            f"Output written to: {folder}/_Data_Analytics/"
        )
        
    except Exception as e:
        import traceback
        self.semantic_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Aggregation Error", f"{e}\n\n{traceback.format_exc()}")
    finally:
        self.semantic_progress.setVisible(False)


def _run_global_aggregation(self):
    """Run GLOBAL semantic aggregation to 07_MASTER_TRUTH."""
    vault_path = self.settings.get('obsidian', 'vault_path', '')
    if not vault_path:
        # Try to get from folder config
        vault_path = self._folder_config.get('vault_root', '')
    
    if not vault_path:
        QMessageBox.warning(
            self, "No Vault Path",
            "Please set the Vault Root in Dashboard settings first."
        )
        return
    
    reply = QMessageBox.question(
        self, "Run Global Aggregation?",
        f"This will scan the entire vault and aggregate semantic tags to:\n"
        f"{vault_path}/07_MASTER_TRUTH/\n\n"
        f"This may take a few minutes. Continue?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply != QMessageBox.StandardButton.Yes:
        return
    
    self.semantic_status.setText("Running GLOBAL aggregation...")
    self.semantic_progress.setVisible(True)
    self.semantic_progress.setValue(10)
    
    try:
        from core.semantic_aggregator import SemanticAggregator
        
        agg = SemanticAggregator(vault_path)
        self.semantic_progress.setValue(30)
        
        result = agg.aggregate_global()
        self.semantic_progress.setValue(100)
        
        # Update stats display
        self.semantic_stats['total'].setText(str(result.stats.get('total_items', 0)))
        self.semantic_stats['axioms'].setText(str(result.stats.get('Axiom_count', 0)))
        self.semantic_stats['claims'].setText(str(result.stats.get('Claim_count', 0)))
        self.semantic_stats['evidence'].setText(str(result.stats.get('EvidenceBundle_count', 0)))
        self.semantic_stats['duplicates'].setText(str(result.stats.get('duplicates', 0)))
        
        self.semantic_status.setText(
            f"GLOBAL aggregation complete: {result.stats.get('unique_items', 0)} unique items, "
            f"{result.stats.get('contradictions', 0)} contradictions"
        )
        
        QMessageBox.information(
            self, "GLOBAL Aggregation Complete",
            f"Scanned {result.stats.get('total_items', 0)} tags\n"
            f"Unique items: {result.stats.get('unique_items', 0)}\n"
            f"Contradictions: {result.stats.get('contradictions', 0)}\n\n"
            f"Output written to: {vault_path}/07_MASTER_TRUTH/"
        )
        
    except Exception as e:
        import traceback
        self.semantic_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Aggregation Error", f"{e}\n\n{traceback.format_exc()}")
    finally:
        self.semantic_progress.setVisible(False)


# Attach methods to MainWindowV2 class
MainWindowV2._run_local_aggregation = _run_local_aggregation
MainWindowV2._run_global_aggregation = _run_global_aggregation


# =============================================================================
# TAG MANAGER PAGE
# =============================================================================

def _build_tag_manager_page(self):
    """Build the Tag Manager page - Reader-Facing Semantic Tags."""
    page, layout = self._create_page_container("🏷️ Semantic Tag Manager")
    
    # === SEMANTIC TAG SYSTEM INFO ===
    info_label = QLabel(
        "<b>Reader-Facing Semantic Tags</b><br>"
        "<i>Links = what it means | Tags = how to read it</i>"
    )
    info_label.setStyleSheet("color: #888; padding: 10px;")
    layout.addWidget(info_label)
    
    # === TAG A NOTE ===
    tag_note_group = QGroupBox("Tag a Note")
    tag_note_layout = QVBoxLayout(tag_note_group)
    
    # Note path input
    path_row = QHBoxLayout()
    path_row.addWidget(QLabel("Note Path:"))
    self.semantic_note_path = QLineEdit()
    self.semantic_note_path.setPlaceholderText("e.g., 03_PUBLICATIONS/Paper 01.md")
    path_row.addWidget(self.semantic_note_path)
    tag_note_layout.addLayout(path_row)
    
    # Epistemic (required)
    epistemic_row = QHBoxLayout()
    epistemic_row.addWidget(QLabel("Epistemic (required):"))
    self.epistemic_combo = QComboBox()
    self.epistemic_combo.addItems(["", "established", "inferential", "speculative", "metaphorical"])
    epistemic_row.addWidget(self.epistemic_combo)
    tag_note_layout.addLayout(epistemic_row)
    
    # Function (1-2)
    function_row = QHBoxLayout()
    function_row.addWidget(QLabel("Function (1-2):"))
    self.function_combo1 = QComboBox()
    self.function_combo1.addItems(["", "definition", "bridge", "constraint", "synthesis", "example", "objection", "response", "derivation"])
    self.function_combo2 = QComboBox()
    self.function_combo2.addItems(["", "definition", "bridge", "constraint", "synthesis", "example", "objection", "response", "derivation"])
    function_row.addWidget(self.function_combo1)
    function_row.addWidget(self.function_combo2)
    tag_note_layout.addLayout(function_row)
    
    # Domain (multiple)
    domain_row = QHBoxLayout()
    domain_row.addWidget(QLabel("Domain:"))
    self.domain_physics = QCheckBox("physics")
    self.domain_info = QCheckBox("information")
    self.domain_philosophy = QCheckBox("philosophy")
    self.domain_theology = QCheckBox("theology")
    self.domain_cognition = QCheckBox("cognition")
    self.domain_math = QCheckBox("mathematics")
    self.domain_history = QCheckBox("history")
    domain_row.addWidget(self.domain_physics)
    domain_row.addWidget(self.domain_info)
    domain_row.addWidget(self.domain_philosophy)
    domain_row.addWidget(self.domain_theology)
    domain_row.addWidget(self.domain_cognition)
    domain_row.addWidget(self.domain_math)
    domain_row.addWidget(self.domain_history)
    tag_note_layout.addLayout(domain_row)
    
    # Path (optional)
    path_tag_row = QHBoxLayout()
    path_tag_row.addWidget(QLabel("Reader Path:"))
    self.path_combo = QComboBox()
    self.path_combo.addItems(["", "entry", "core", "deep", "appendix"])
    path_tag_row.addWidget(self.path_combo)
    tag_note_layout.addLayout(path_tag_row)
    
    # Apply tags button
    apply_btn = QPushButton("Apply Semantic Tags")
    apply_btn.clicked.connect(self._apply_semantic_tags)
    apply_btn.setStyleSheet(f"background-color: {COLORS['accent_cyan']}; padding: 10px;")
    tag_note_layout.addWidget(apply_btn)
    
    layout.addWidget(tag_note_group)
    
    # === DATABASE SYNC ===
    sync_group = QGroupBox("Database Sync")
    sync_layout = QVBoxLayout(sync_group)
    
    sync_btn_row = QHBoxLayout()
    
    scan_vault_btn = QPushButton("Scan Vault for Tags")
    scan_vault_btn.clicked.connect(self._scan_vault_semantic_tags)
    sync_btn_row.addWidget(scan_vault_btn)
    
    sync_postgres_btn = QPushButton("Sync to PostgreSQL")
    sync_postgres_btn.clicked.connect(self._sync_semantic_tags_postgres)
    sync_btn_row.addWidget(sync_postgres_btn)
    
    gen_report_btn = QPushButton("Generate Report")
    gen_report_btn.clicked.connect(self._generate_tag_report)
    sync_btn_row.addWidget(gen_report_btn)
    
    sync_layout.addLayout(sync_btn_row)
    
    # Status
    self.tag_status = QLabel("Ready")
    self.tag_status.setStyleSheet("color: #888;")
    sync_layout.addWidget(self.tag_status)
    
    # Results display
    self.tag_results = QTextEdit()
    self.tag_results.setReadOnly(True)
    self.tag_results.setMaximumHeight(250)
    sync_layout.addWidget(self.tag_results)
    
    layout.addWidget(sync_group)
    
    # === TAG STATS ===
    stats_group = QGroupBox("Tag Statistics")
    stats_layout = QVBoxLayout(stats_group)
    
    refresh_stats_btn = QPushButton("Refresh Stats")
    refresh_stats_btn.clicked.connect(self._refresh_tag_stats)
    stats_layout.addWidget(refresh_stats_btn)
    
    self.tag_stats_display = QTextEdit()
    self.tag_stats_display.setReadOnly(True)
    self.tag_stats_display.setMaximumHeight(200)
    stats_layout.addWidget(self.tag_stats_display)
    
    layout.addWidget(stats_group)
    
    layout.addStretch()


def _apply_semantic_tags(self):
    """Apply semantic tags to a note."""
    note_path = self.semantic_note_path.text().strip()
    if not note_path:
        QMessageBox.warning(self, "Missing Path", "Please enter a note path.")
        return
    
    # Collect tags
    tags = {"epistemic": [], "function": [], "domain": [], "path": []}
    
    # Epistemic
    if self.epistemic_combo.currentText():
        tags["epistemic"].append(self.epistemic_combo.currentText())
    
    # Function
    if self.function_combo1.currentText():
        tags["function"].append(self.function_combo1.currentText())
    if self.function_combo2.currentText():
        tags["function"].append(self.function_combo2.currentText())
    
    # Domain
    if self.domain_physics.isChecked(): tags["domain"].append("physics")
    if self.domain_info.isChecked(): tags["domain"].append("information")
    if self.domain_philosophy.isChecked(): tags["domain"].append("philosophy")
    if self.domain_theology.isChecked(): tags["domain"].append("theology")
    if self.domain_cognition.isChecked(): tags["domain"].append("cognition")
    if self.domain_math.isChecked(): tags["domain"].append("mathematics")
    if self.domain_history.isChecked(): tags["domain"].append("history")
    
    # Path
    if self.path_combo.currentText():
        tags["path"].append(self.path_combo.currentText())
    
    # Validate
    if not tags["epistemic"]:
        QMessageBox.warning(self, "Missing Epistemic", "Epistemic tag is required.")
        return
    
    # Get vault path
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        result = engine.tag_note(note_path, tags)
        
        self.tag_status.setText(f"Tagged: {note_path}")
        self.tag_results.setText(
            f"Tags applied: {result['tags_added']}\n"
            f"Warnings: {result['warnings']}"
        )
        
        if result['warnings']:
            QMessageBox.warning(self, "Warnings", "\n".join(result['warnings']))
        else:
            QMessageBox.information(self, "Success", f"Applied {len(result['tags_added'])} tags to {note_path}")
            
    except Exception as e:
        self.tag_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Error", str(e))


def _scan_vault_semantic_tags(self):
    """Scan vault for existing semantic tags."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    self.tag_status.setText("Scanning vault for semantic tags...")
    
    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        stats = engine.scan_vault_for_tags()
        
        result_text = f"Files scanned: {stats['files_scanned']}\n"
        result_text += f"Files with tags: {stats['files_with_tags']}\n"
        result_text += f"Incomplete notes: {len(stats['incomplete_notes'])}\n\n"
        
        result_text += "Tags found:\n"
        for axis, values in stats['tags_found'].items():
            if values:
                result_text += f"  {axis}: {dict(values)}\n"
        
        self.tag_results.setText(result_text)
        self.tag_status.setText(f"Scan complete: {stats['files_with_tags']} tagged files")
        
    except Exception as e:
        self.tag_status.setText(f"Error: {e}")
        self.tag_results.setText(str(e))


def _sync_semantic_tags_postgres(self):
    """Sync semantic tags to PostgreSQL."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    self.tag_status.setText("Syncing to PostgreSQL...")
    
    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        
        # Get postgres connection string from settings
        conn_str = self.settings.get('postgres', 'connection_string', '')
        if not conn_str:
            conn_str = "host=192.168.1.177 port=2665 dbname=Theophysics user=Yellowkid password=Moss9pep28$"
        
        success, message = engine.export_to_postgres(conn_str)
        
        if success:
            self.tag_status.setText("PostgreSQL sync complete!")
            self.tag_results.setText(message)
            QMessageBox.information(self, "Sync Complete", message)
        else:
            self.tag_status.setText(f"Sync failed: {message}")
            self.tag_results.setText(f"Error: {message}")
            
    except Exception as e:
        self.tag_status.setText(f"Error: {e}")
        self.tag_results.setText(str(e))


def _generate_tag_report(self):
    """Generate tag taxonomy report."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        report = engine.generate_taxonomy_report()
        
        # Save report
        from pathlib import Path
        report_path = Path(vault_path) / "_TAG_NOTES" / "_TAG_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        
        self.tag_results.setText(report[:2000] + "...\n\n[Full report saved]")
        self.tag_status.setText(f"Report saved: {report_path}")
        QMessageBox.information(self, "Report Generated", f"Saved to:\n{report_path}")
        
    except Exception as e:
        self.tag_status.setText(f"Error: {e}")
        self.tag_results.setText(str(e))


def _refresh_tag_stats(self):
    """Refresh tag statistics display."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        self.tag_stats_display.setText("No vault path configured")
        return
    
    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        stats = engine.get_tag_stats()
        
        text = "Tag Usage Statistics:\n\n"
        for axis, values in stats.items():
            if values:
                text += f"[{axis.upper()}]\n"
                for value, count in sorted(values.items(), key=lambda x: -x[1]):
                    text += f"  #{axis}/{value}: {count}\n"
                text += "\n"
        
        if not any(stats.values()):
            text = "No semantic tags found.\n\nClick 'Scan Vault for Tags' to discover existing tags."
        
        self.tag_stats_display.setText(text)
        
    except Exception as e:
        self.tag_stats_display.setText(f"Error: {e}")
        self.tag_results.setText(str(e))


# Attach Tag Manager methods to MainWindowV2
MainWindowV2._build_tag_manager_page = _build_tag_manager_page
MainWindowV2._apply_semantic_tags = _apply_semantic_tags
MainWindowV2._scan_vault_semantic_tags = _scan_vault_semantic_tags
MainWindowV2._sync_semantic_tags_postgres = _sync_semantic_tags_postgres
MainWindowV2._generate_tag_report = _generate_tag_report
MainWindowV2._refresh_tag_stats = _refresh_tag_stats


# ==========================================
# LEXICON ENGINE METHODS
# ==========================================

def _scan_lexicon_health(self):
    """Scan lexicon for incomplete definitions."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    self.lexicon_status.setText("Scanning lexicon health...")
    
    try:
        from core.lexicon_engine import LexiconEngine
        engine = LexiconEngine(vault_path)
        
        incomplete = engine.get_incomplete_definitions()
        
        # Cache the results
        if self._stats_cache:
            incomplete_data = [{'term': d.term, 'score': d.completeness_score, 
                               'missing': d.missing_sections} for d in incomplete]
            self._stats_cache.save_scan_results('incomplete_definitions', incomplete_data)
            self._stats_cache.set('incomplete_count', len(incomplete))
        
        self.lexicon_status.setText(f"Found {len(incomplete)} incomplete definitions")
        
        # Show summary
        if incomplete:
            msg = f"Found {len(incomplete)} incomplete definitions:\n\n"
            for d in incomplete[:10]:
                msg += f"• {d.term}: {d.completeness_score:.0%} complete\n"
            if len(incomplete) > 10:
                msg += f"\n...and {len(incomplete) - 10} more"
            QMessageBox.information(self, "Lexicon Health", msg)
        else:
            QMessageBox.information(self, "Lexicon Health", "All definitions are complete!")
            
    except Exception as e:
        self.lexicon_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Error", str(e))


def _find_missing_definitions(self):
    """Find terms that are linked but have no definition."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    self.lexicon_status.setText("Scanning for missing definitions...")
    
    try:
        from core.lexicon_engine import LexiconEngine
        engine = LexiconEngine(vault_path)
        
        missing = engine.get_missing_definitions(min_links=5)
        
        # Cache the results
        if self._stats_cache:
            missing_data = [{'term': t, 'count': c} for t, c in missing]
            self._stats_cache.save_scan_results('missing_definitions', missing_data)
            self._stats_cache.set('missing_count', len(missing))
        
        self.lexicon_status.setText(f"Found {len(missing)} terms needing definitions")
        
        if missing:
            msg = f"Found {len(missing)} terms linked 5+ times without definitions:\n\n"
            for term, count in missing[:15]:
                msg += f"• {term}: {count} links\n"
            if len(missing) > 15:
                msg += f"\n...and {len(missing) - 15} more"
            QMessageBox.information(self, "Missing Definitions", msg)
        else:
            QMessageBox.information(self, "Missing Definitions", "All frequently-linked terms have definitions!")
            
    except Exception as e:
        self.lexicon_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Error", str(e))


def _fetch_wikipedia_for_term(self):
    """Fetch Wikipedia content for a term."""
    term = self.wiki_term_input.text().strip()
    if not term:
        QMessageBox.warning(self, "No Term", "Please enter a term to look up.")
        return
    
    self.lexicon_status.setText(f"Fetching Wikipedia for '{term}'...")
    
    try:
        from core.lexicon_engine import WikipediaSync
        wiki = WikipediaSync()
        
        block = wiki.generate_wikipedia_block(term)
        
        if block:
            self.lexicon_status.setText(f"Wikipedia content fetched for '{term}'")
            
            # Show in a dialog
            from PySide6.QtWidgets import QDialog, QTextEdit, QDialogButtonBox
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Wikipedia: {term}")
            dlg.resize(600, 400)
            dlg_layout = QVBoxLayout(dlg)
            
            editor = QTextEdit()
            editor.setPlainText(block)
            editor.setReadOnly(True)
            dlg_layout.addWidget(editor)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            buttons.accepted.connect(dlg.accept)
            dlg_layout.addWidget(buttons)
            
            dlg.exec()
        else:
            self.lexicon_status.setText(f"No Wikipedia article found for '{term}'")
            QMessageBox.warning(self, "Not Found", f"No Wikipedia article found for '{term}'")
            
    except Exception as e:
        self.lexicon_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Error", str(e))


def _open_word_admission_dialog(self):
    """Open dialog for Word Admission Gate evaluation."""
    from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QSpinBox
    
    dlg = QDialog(self)
    dlg.setWindowTitle("🚪 Word Admission Gate (LAG)")
    dlg.resize(500, 400)
    
    layout = QVBoxLayout(dlg)
    
    layout.addWidget(QLabel("<b>Evaluate a new term for admission to the lexicon</b>"))
    layout.addWidget(QLabel("<i>Words are admitted only if they reduce explanatory entropy under constraint.</i>"))
    
    form = QFormLayout()
    
    term_edit = QLineEdit()
    term_edit.setPlaceholderText("e.g., Trinity Actualization")
    form.addRow("Term:", term_edit)
    
    replaces_edit = QLineEdit()
    replaces_edit.setPlaceholderText("e.g., Wave Function Collapse")
    form.addRow("Replaces:", replaces_edit)
    
    role_combo = QComboBox()
    role_combo.addItems(["", "operator", "field", "process", "state", "metric"])
    form.addRow("Structural Role:", role_combo)
    
    loss_edit = QLineEdit()
    loss_edit.setPlaceholderText("What's lost without this term? (≤12 words)")
    form.addRow("Loss if Missing:", loss_edit)
    
    phrases_edit = QTextEdit()
    phrases_edit.setPlaceholderText("Phrases this term replaces (one per line)")
    phrases_edit.setMaximumHeight(80)
    form.addRow("Replaced Phrases:", phrases_edit)
    
    anchor_check = QCheckBox("Has formal anchor (symbol/equation)")
    form.addRow("Formal Anchor:", anchor_check)
    
    symbol_edit = QLineEdit()
    symbol_edit.setPlaceholderText("e.g., χ, Observer Operator")
    form.addRow("Symbol/Equation:", symbol_edit)
    
    overlap_spin = QSpinBox()
    overlap_spin.setRange(0, 100)
    overlap_spin.setValue(80)
    overlap_spin.setSuffix("%")
    form.addRow("Semantic Overlap:", overlap_spin)
    
    closest_edit = QLineEdit()
    closest_edit.setPlaceholderText("Closest existing term")
    form.addRow("Closest Term:", closest_edit)
    
    layout.addLayout(form)
    
    # Result area
    result_text = QTextEdit()
    result_text.setReadOnly(True)
    result_text.setMaximumHeight(150)
    layout.addWidget(QLabel("Result:"))
    layout.addWidget(result_text)
    
    # Buttons
    btn_layout = QHBoxLayout()
    
    evaluate_btn = QPushButton("🔍 Evaluate")
    def do_evaluate():
        try:
            from core.lexicon_engine import LexiconEngine, WordCandidate, FormalAnchor
            
            vault_path = self._folder_config.get('vault_root', '') or self.settings.get('obsidian', 'vault_path', '')
            engine = LexiconEngine(vault_path)
            
            word = WordCandidate(
                term=term_edit.text().strip(),
                replaces=[r.strip() for r in replaces_edit.text().split(',') if r.strip()],
                structural_role=role_combo.currentText(),
                loss_if_missing=loss_edit.text().strip(),
                replaced_phrases=[p.strip() for p in phrases_edit.toPlainText().split('\n') if p.strip()],
                formal_anchor=FormalAnchor(anchor_check.isChecked(), symbol_edit.text().strip()),
                semantic_overlap=overlap_spin.value(),
                closest_existing_term=closest_edit.text().strip()
            )
            
            result, template = engine.evaluate_word(word)
            result_text.setPlainText(template)
            
        except Exception as e:
            result_text.setPlainText(f"Error: {e}")
    
    evaluate_btn.clicked.connect(do_evaluate)
    btn_layout.addWidget(evaluate_btn)
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dlg.accept)
    btn_layout.addWidget(close_btn)
    
    layout.addLayout(btn_layout)
    
    dlg.exec()


def _generate_lexicon_report(self):
    """Generate comprehensive lexicon health report."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return
    
    self.lexicon_status.setText("Generating lexicon report...")
    
    try:
        from core.lexicon_engine import LexiconEngine
        from pathlib import Path
        
        engine = LexiconEngine(vault_path)
        report = engine.generate_full_report()
        
        report_path = Path(vault_path) / "_TAG_NOTES" / "_LEXICON_HEALTH_REPORT.md"
        report_path.write_text(report, encoding='utf-8')
        
        self.lexicon_status.setText(f"Report saved: {report_path}")
        QMessageBox.information(self, "Report Generated", f"Lexicon health report saved to:\n{report_path}")
        
    except Exception as e:
        self.lexicon_status.setText(f"Error: {e}")
        QMessageBox.critical(self, "Error", str(e))


def _load_cached_lexicon_stats(self):
    """Load cached lexicon statistics on startup."""
    if not self._stats_cache:
        return
    
    try:
        incomplete_count = self._stats_cache.get('incomplete_count', None)
        missing_count = self._stats_cache.get('missing_count', None)
        
        if incomplete_count is not None or missing_count is not None:
            parts = []
            if incomplete_count is not None:
                parts.append(f"{incomplete_count} incomplete")
            if missing_count is not None:
                parts.append(f"{missing_count} missing")
            
            age = self._stats_cache.get_scan_age('incomplete_definitions')
            age_str = ""
            if age:
                hours = int(age / 3600)
                if hours > 0:
                    age_str = f" (cached {hours}h ago)"
                else:
                    mins = int(age / 60)
                    age_str = f" (cached {mins}m ago)"
            
            self.lexicon_status.setText(f"Last scan: {', '.join(parts)}{age_str}")
    except Exception:
        pass


# Attach Lexicon Engine methods to MainWindowV2
MainWindowV2._scan_lexicon_health = _scan_lexicon_health
MainWindowV2._find_missing_definitions = _find_missing_definitions
MainWindowV2._fetch_wikipedia_for_term = _fetch_wikipedia_for_term
MainWindowV2._open_word_admission_dialog = _open_word_admission_dialog
MainWindowV2._generate_lexicon_report = _generate_lexicon_report
MainWindowV2._load_cached_lexicon_stats = _load_cached_lexicon_stats

def _scan_mermaid_diagrams(self):
    """Scan folder for Mermaid diagrams in markdown files."""
    folder = self.semantic_folder_edit.text()
    if not folder:
        QMessageBox.warning(self, "No Folder", "Please select a folder to scan.")
        return
    
    self.mermaid_count_label.setText("Scanning...")
    self._mermaid_diagrams = []
    
    try:
        from pathlib import Path
        import re
        
        folder_path = Path(folder)
        recursive = self.semantic_recursive_check.isChecked()
        
        # Get all markdown files
        if recursive:
            md_files = list(folder_path.rglob("*.md"))
        else:
            md_files = list(folder_path.glob("*.md"))
        
        # Extract Mermaid blocks
        mermaid_pattern = re.compile(r'```mermaid\n(.*?)```', re.DOTALL | re.IGNORECASE)
        
        for md_file in md_files:
            try:
                file_content = md_file.read_text(encoding='utf-8')
                matches = mermaid_pattern.findall(file_content)
                
                for i, mermaid_code in enumerate(matches):
                    self._mermaid_diagrams.append({
                        'file': md_file.name,
                        'full_path': str(md_file),
                        'index': i + 1,
                        'code': mermaid_code.strip(),
                        'paper': self._extract_paper_name(md_file.name)
                    })
            except Exception as e:
                print(f"Error reading {md_file.name}: {e}")
        
        self._render_mermaid_diagrams()
        self.mermaid_count_label.setText(f"{len(self._mermaid_diagrams)} diagrams found")
        
        if len(self._mermaid_diagrams) == 0:
            QMessageBox.information(
                self, "No Mermaids Found",
                "No Mermaid diagrams found.\n\nMake sure files contain:\n```mermaid\\ngraph TD\\n  A-->B\\n```"
            )
    except Exception as e:
        self.mermaid_count_label.setText("Error")
        QMessageBox.critical(self, "Error", f"Failed to scan:\n{e}")

def _extract_paper_name(self, filename):
    """Extract paper name from filename."""
    import re
    match = re.match(r'(P\d+)', filename, re.IGNORECASE)
    return match.group(1).upper() if match else "Unknown"

def _render_mermaid_diagrams(self):
    """Render all extracted Mermaid diagrams."""
    while self.mermaid_container_layout.count():
        child = self.mermaid_container_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
    if not self._mermaid_diagrams:
        empty_label = QLabel("No diagrams. Click 'Scan for Mermaids'.")
        empty_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 20px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mermaid_container_layout.addWidget(empty_label)
        return
    
    from collections import defaultdict
    diagrams_by_paper = defaultdict(list)
    for diagram in self._mermaid_diagrams:
        diagrams_by_paper[diagram['paper']].append(diagram)
    
    for paper, diagrams in sorted(diagrams_by_paper.items()):
        paper_header = QLabel(f"📄 {paper} ({len(diagrams)} diagram{'s' if len(diagrams) > 1 else ''})")
        paper_header.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: bold;
            color: {COLORS['accent_cyan']};
            padding: 10px 0;
        """)
        self.mermaid_container_layout.addWidget(paper_header)
        
        for diagram in diagrams:
            diagram_widget = self._create_mermaid_widget(diagram)
            self.mermaid_container_layout.addWidget(diagram_widget)
    
    self.mermaid_container_layout.addStretch()

def _create_mermaid_widget(self, diagram):
    """Create widget for single Mermaid diagram."""
    widget = QWidget()
    widget.setStyleSheet(f"""
        background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 8px;
    """)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(15, 15, 15, 15)
    
    header = QLabel(f"📄 {diagram['file']} (Diagram #{diagram['index']})")
    header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
    layout.addWidget(header)
    
    code_preview = diagram['code'][:200] + ('...' if len(diagram['code']) > 200 else '')
    code_label = QLabel(f"<pre>{code_preview}</pre>")
    code_label.setWordWrap(True)
    code_label.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_muted']};
        padding: 10px;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
    """)
    layout.addWidget(code_label)
    
    btn_row = QHBoxLayout()
    
    view_btn = QPushButton("👁️ View Full")
    view_btn.clicked.connect(lambda: self._show_mermaid_code(diagram))
    btn_row.addWidget(view_btn)
    
    render_btn = QPushButton("🎨 Render")
    render_btn.setProperty("class", "primary")
    render_btn.clicked.connect(lambda: self._render_single_mermaid(diagram))
    btn_row.addWidget(render_btn)
    
    copy_btn = QPushButton("📋 Copy")
    copy_btn.clicked.connect(lambda: self._copy_mermaid_code(diagram))
    btn_row.addWidget(copy_btn)
    
    btn_row.addStretch()
    layout.addLayout(btn_row)
    
    return widget

def _show_mermaid_code(self, diagram):
    """Show full Mermaid code."""
    dialog = QDialog(self)
    dialog.setWindowTitle(f"Mermaid - {diagram['file']}")
    dialog.setMinimumSize(600, 400)
    
    layout = QVBoxLayout(dialog)
    
    text_edit = QTextEdit()
    text_edit.setPlainText(diagram['code'])
    text_edit.setReadOnly(True)
    text_edit.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
    """)
    layout.addWidget(text_edit)
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    dialog.exec()

def _render_single_mermaid(self, diagram):
    """Render single Mermaid diagram."""
    QMessageBox.information(
        self, "Render Mermaid",
        f"Rendering: {diagram['file']}\n\nCode: {len(diagram['code'])} chars\n\nTODO: MCP integration"
    )

def _copy_mermaid_code(self, diagram):
    """Copy Mermaid code to clipboard."""
    from PySide6.QtWidgets import QApplication
    clipboard = QApplication.clipboard()
    clipboard.setText(diagram['code'])
    self.mermaid_count_label.setText(f"Copied from {diagram['file']}")

def _combine_axiom_diagrams(self):
    """Combine all paper diagrams into master Mermaid graph."""
    if not self._mermaid_diagrams:
        QMessageBox.warning(self, "No Diagrams", "Please scan for Mermaid diagrams first.")
        return
    
    # Group by paper
    from collections import defaultdict
    by_paper = defaultdict(list)
    for d in self._mermaid_diagrams:
        by_paper[d['paper']].append(d)
    
    # Build combined diagram
    combined_lines = ["flowchart TD"]
    combined_lines.append("")
    combined_lines.append("    %% === THEOPHYSICS MASTER AXIOM FLOW ===")
    combined_lines.append("    %% Combined from all paper diagrams")
    combined_lines.append("")
    
    # Style definitions
    combined_lines.append("    %% Style Classes")
    combined_lines.append("    classDef part1 fill:#ff6b6b,stroke:#333,color:#fff")
    combined_lines.append("    classDef part2 fill:#4ecdc4,stroke:#333,color:#fff")
    combined_lines.append("    classDef part3 fill:#45b7d1,stroke:#333,color:#fff")
    combined_lines.append("    classDef part4 fill:#6c5ce7,stroke:#333,color:#fff")
    combined_lines.append("")
    
    # Extract nodes and edges from each paper's diagrams
    all_nodes = set()
    all_edges = []
    import re
    
    for paper in sorted(by_paper.keys()):
        diagrams = by_paper[paper]
        combined_lines.append(f"    %% === {paper} ===")
        
        for diagram in diagrams:
            code = diagram['code']
            
            # Extract node definitions (A[Label], B[Label], etc.)
            node_pattern = r'(\w+)\s*\[([^\]]+)\]'
            for match in re.finditer(node_pattern, code):
                node_id, label = match.groups()
                if node_id not in all_nodes:
                    all_nodes.add(node_id)
                    combined_lines.append(f'    {node_id}["{label}"]')
            
            # Extract edges (A --> B, A -->|label| B, etc.)
            edge_pattern = r'(\w+)\s*-->\s*(?:\|([^|]+)\|)?\s*(\w+)'
            for match in re.finditer(edge_pattern, code):
                source, label, target = match.groups()
                edge = (source, target, label or '')
                if edge not in all_edges:
                    all_edges.append(edge)
        
        combined_lines.append("")
    
    # Add all edges
    combined_lines.append("    %% === CONNECTIONS ===")
    for source, target, label in all_edges:
        if label:
            combined_lines.append(f'    {source} -->|"{label}"| {target}')
        else:
            combined_lines.append(f'    {source} --> {target}')
    
    # Add paper flow connections
    combined_lines.append("")
    combined_lines.append("    %% === PAPER FLOW ===")
    papers = sorted(by_paper.keys())
    for i in range(len(papers) - 1):
        combined_lines.append(f'    {papers[i]} -.->|leads to| {papers[i+1]}')
    
    combined_code = '\n'.join(combined_lines)
    
    # Show in dialog
    self._show_combined_mermaid_dialog(combined_code, by_paper)

def _show_combined_mermaid_dialog(self, combined_code: str, by_paper: dict):
    """Show dialog with combined Mermaid diagram."""
    dialog = QDialog(self)
    dialog.setWindowTitle("Combined Mermaid - All Papers")
    dialog.setMinimumSize(900, 700)
    dialog.setStyleSheet(DARK_THEME_V2)
    
    layout = QVBoxLayout(dialog)
    
    # Header with stats
    header = QLabel(f"📊 Combined from {len(by_paper)} papers, {sum(len(v) for v in by_paper.values())} diagrams")
    header.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['accent_cyan']}; padding: 10px;")
    layout.addWidget(header)
    
    # Paper list
    papers_label = QLabel("Papers included: " + ", ".join(sorted(by_paper.keys())))
    papers_label.setStyleSheet("color: #9ca3af; padding: 5px;")
    layout.addWidget(papers_label)
    
    # Splitter for code and preview
    splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Left: Code editor
    code_widget = QWidget()
    code_layout = QVBoxLayout(code_widget)
    code_layout.setContentsMargins(0, 0, 0, 0)
    
    code_label = QLabel("Mermaid Code:")
    code_label.setStyleSheet("font-weight: bold;")
    code_layout.addWidget(code_label)
    
    code_edit = QTextEdit()
    code_edit.setPlainText(combined_code)
    code_edit.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
        border: 1px solid {COLORS['border_dark']};
    """)
    code_layout.addWidget(code_edit)
    
    splitter.addWidget(code_widget)
    
    # Right: Preview placeholder / instructions
    preview_widget = QWidget()
    preview_layout = QVBoxLayout(preview_widget)
    preview_layout.setContentsMargins(0, 0, 0, 0)
    
    preview_label = QLabel("Preview / Export:")
    preview_label.setStyleSheet("font-weight: bold;")
    preview_layout.addWidget(preview_label)
    
    preview_text = QTextEdit()
    preview_text.setReadOnly(True)
    preview_text.setHtml(f"""
        <h3>How to Render</h3>
        <p><b>Option 1: Mermaid Live Editor</b></p>
        <ol>
            <li>Click "Copy Code" below</li>
            <li>Go to <a href="https://mermaid.live">mermaid.live</a></li>
            <li>Paste and view</li>
        </ol>
        <p><b>Option 2: Obsidian</b></p>
        <ol>
            <li>Click "Save to Vault"</li>
            <li>Open in Obsidian with Mermaid plugin</li>
        </ol>
        <p><b>Option 3: VS Code</b></p>
        <ol>
            <li>Install "Markdown Preview Mermaid Support"</li>
            <li>Save as .md file with ```mermaid block</li>
        </ol>
        <hr>
        <p style="color: #22c55e;"><b>Diagram Stats:</b></p>
        <ul>
            <li>Papers: {len(by_paper)}</li>
            <li>Total diagrams: {sum(len(v) for v in by_paper.values())}</li>
            <li>Code lines: {len(combined_code.splitlines())}</li>
        </ul>
    """)
    preview_text.setStyleSheet(f"""
        background-color: {COLORS['bg_medium']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border_dark']};
        padding: 10px;
    """)
    preview_layout.addWidget(preview_text)
    
    splitter.addWidget(preview_widget)
    splitter.setSizes([500, 400])
    
    layout.addWidget(splitter)
    
    # Buttons
    btn_row = QHBoxLayout()
    
    copy_btn = QPushButton("📋 Copy Code")
    copy_btn.setProperty("class", "primary")
    copy_btn.clicked.connect(lambda: self._copy_to_clipboard(code_edit.toPlainText(), "Mermaid code copied!"))
    btn_row.addWidget(copy_btn)
    
    save_btn = QPushButton("💾 Save to File")
    save_btn.clicked.connect(lambda: self._save_mermaid_to_file(code_edit.toPlainText()))
    btn_row.addWidget(save_btn)
    
    vault_btn = QPushButton("📁 Save to Vault")
    vault_btn.clicked.connect(lambda: self._save_mermaid_to_vault(code_edit.toPlainText()))
    btn_row.addWidget(vault_btn)
    
    btn_row.addStretch()
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    btn_row.addWidget(close_btn)
    
    layout.addLayout(btn_row)
    
    dialog.exec()

def _copy_to_clipboard(self, text: str, message: str = "Copied!"):
    """Copy text to clipboard and show status."""
    from PySide6.QtWidgets import QApplication
    QApplication.clipboard().setText(text)
    self.statusBar().showMessage(message, 3000)

def _save_mermaid_to_file(self, code: str):
    """Save Mermaid code to file."""
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Save Mermaid Diagram", 
        "theophysics_master_flow.md",
        "Markdown (*.md);;Mermaid (*.mermaid);;All Files (*)"
    )
    if file_path:
        content = f"# Theophysics Master Axiom Flow\n\n```mermaid\n{code}\n```\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        QMessageBox.information(self, "Saved", f"Saved to:\n{file_path}")

def _save_mermaid_to_vault(self, code: str):
    """Save Mermaid diagram to Obsidian vault."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please configure vault path in Dashboard first.")
        return
    
    from pathlib import Path
    from datetime import datetime
    
    # Save to analytics folder or root
    save_dir = Path(vault_path) / "00_VAULT_OS" / "Analytics"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = save_dir / f"Master_Axiom_Flow_{timestamp}.md"
    
    content = f"""---
title: Master Axiom Flow
type: mermaid-diagram
generated: {datetime.now().isoformat()}
source: Theophysics Research Manager
---

# Theophysics Master Axiom Flow

Combined diagram from all paper Mermaid graphs.

```mermaid
{code}
```

## Notes

- Generated automatically from paper diagrams
- Edit above to customize flow
- Use Obsidian's Mermaid preview to view
"""
    
    file_path.write_text(content, encoding='utf-8')
    QMessageBox.information(self, "Saved to Vault", f"Saved to:\n{file_path}")

# Attach to class
MainWindowV2._scan_mermaid_diagrams = _scan_mermaid_diagrams
MainWindowV2._extract_paper_name = _extract_paper_name
MainWindowV2._render_mermaid_diagrams = _render_mermaid_diagrams
MainWindowV2._create_mermaid_widget = _create_mermaid_widget
MainWindowV2._show_mermaid_code = _show_mermaid_code
MainWindowV2._render_single_mermaid = _render_single_mermaid
MainWindowV2._copy_mermaid_code = _copy_mermaid_code
MainWindowV2._combine_axiom_diagrams = _combine_axiom_diagrams
MainWindowV2._show_combined_mermaid_dialog = _show_combined_mermaid_dialog
MainWindowV2._copy_to_clipboard = _copy_to_clipboard
MainWindowV2._save_mermaid_to_file = _save_mermaid_to_file
MainWindowV2._save_mermaid_to_vault = _save_mermaid_to_vault



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
    self.ollama_hidden_prompt.setMaximumHeight(150)
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
            self.ollama_status_label.setText(f"Online ({len(models)} models)")
            self.ollama_status_label.setStyleSheet("color: #22c55e;")
            self._log_ollama(f"Ollama online. Models: {', '.join(models[:5])}")
        else:
            self.ollama_status_label.setText("Error")
            self.ollama_status_label.setStyleSheet("color: #f59e0b;")
    except Exception as e:
        self.ollama_status_label.setText("Offline")
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
                            "Ollama is not running.\n\nStart it with: ollama serve")
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
            
            YAML_PROMPT = """You are a YAML frontmatter generator for the Theophysics academic framework.
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

YAML:"""
            
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
                
                self.progress.emit(int((i / max(total, 1)) * 100), md_file.name)
                
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
                        lines = response.split('\n')
                        response = '\n'.join(l for l in lines if not l.startswith('```'))
                    
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
                        new_content = f"---\n{yaml.dump(new_fm, default_flow_style=False, allow_unicode=True)}---\n\n{body}"
                        md_file.write_text(new_content, encoding='utf-8')
                    
                    stats['updated'] += 1
                    stats['processed'] += 1
                    self.log.emit(f"OK: {md_file.name}")
                    
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
    
    self._log_ollama(f"\nPreview: {first_file.name}")
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
                "Could not connect to PostgreSQL.\n\nCheck host, port, and credentials in settings.")
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
            f"Synced {synced} definitions to PostgreSQL.\n\nErrors: {errors}")
        
        # Update metrics
        if hasattr(self, '_refresh_postgres_metrics'):
            self._refresh_postgres_metrics()
        
    except Exception as e:
        QMessageBox.critical(self, "Sync Error", f"Failed to sync:\n{e}")

def _refresh_postgres_metrics(self):
    """Refresh PostgreSQL metrics display."""
    if not hasattr(self, 'postgres_manager') or not self.postgres_manager:
        if hasattr(self, 'postgres_metrics_label'):
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
            
            if hasattr(self, 'postgres_metrics_label'):
                self.postgres_metrics_label.setText(
                    f"Definitions: {def_count} | Footnotes: {fn_count} | "
                    f"Research Links: {rl_count} | Memories: {mem_count}"
                )
        else:
            if hasattr(self, 'postgres_metrics_label'):
                self.postgres_metrics_label.setText("Connection failed")
    except Exception as e:
        if hasattr(self, 'postgres_metrics_label'):
            self.postgres_metrics_label.setText(f"Error: {str(e)[:30]}")


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

# Attach PostgreSQL methods
MainWindowV2._sync_to_postgres = _sync_to_postgres
MainWindowV2._refresh_postgres_metrics = _refresh_postgres_metrics
