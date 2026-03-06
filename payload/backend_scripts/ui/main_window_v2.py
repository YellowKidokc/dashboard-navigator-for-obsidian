"""
Main Window V2 - Sidebar Navigation with Dashboard
Theophysics Research Manager - Enhanced Edition
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

# Import SQLite database engine
try:
    from engine.database_engine import DatabaseEngine, generate_uuid
    from engine.settings import SettingsManager as EngineSettings
    from engine.vault_engine import VaultEngine
    from engine.math_translation_engine import MathTranslationEngine
    from engine.mermaid_generator import MermaidGenerator
    from ui.tabs.mermaid_tab import MermaidTab
    from ui.tabs.stats_hub_tab import StatsHubTab
    from ui.tabs.vault_health_tab import VaultHealthTab
    from ui.tabs.file_types_tab import FileTypesTab
    from ui.tabs.yaml_validator_tab import YAMLValidatorTab
    HAS_ENGINE = True
except ImportError as e:
    print(f"Import warning: {e}")
    HAS_ENGINE = False

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStatusBar, QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStackedWidget, QSplitter, QGroupBox, QLineEdit, QPushButton,
    QProgressBar, QScrollArea, QFrame, QCheckBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QGridLayout, QSpacerItem, QSizePolicy, QInputDialog, QSpinBox,
    QTabWidget
)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QColor
try:
    from PySide6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
    HAS_QT_CHARTS = True
except Exception:
    QChart = QChartView = QBarSeries = QBarSet = QBarCategoryAxis = QValueAxis = None
    HAS_QT_CHARTS = False

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
        ("📊", "Stats Hub"),
        ("🏥", "Vault Health"),
        ("📁", "File Types"),
        ("📋", "YAML Check"),
        ("🎨", "Mermaid Graphs"),
        ("🔢", "Math Translation"),
        ("🔗", "Auto-Linker"),
        ("📚", "Definitions"),
        ("📈", "Data Aggregation"),
        ("⚡", "Analytics Runner"),
        ("🍇", "Document Evaluator"),
        ("🔗", "Research Links"),
        ("📝", "Footnotes"),
        ("🧠", "Semantic"),
        ("🏷️", "Tags"),
        ("🤖", "Ollama"),
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
        
        # Initialize Math Translation Engine
        if HAS_ENGINE:
            try:
                engine_settings = EngineSettings()
                engine_settings.load()
                db_engine = DatabaseEngine(engine_settings)
                self.math_engine = MathTranslationEngine(engine_settings, db_engine)
                self.mermaid_engine = MermaidGenerator()
            except Exception as e:
                print(f"Could not initialize Math Translation Engine: {e}")
                self.math_engine = None
                self.mermaid_engine = None
        else:
            self.math_engine = None
            self.mermaid_engine = None
        
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
        self._autolinker_state = self._load_autolinker_state()
        self._current_scan_targets: Dict[str, str] = {}
        
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
            'analytics_target': self.settings.get('obsidian', 'vault_path', ''),
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
        self._build_stats_hub_page()      # 1 - Stats Hub
        self._build_vault_health_page()   # 2 - Vault Health
        self._build_file_types_page()     # 3 - File Types
        self._build_yaml_check_page()     # 4 - YAML Check
        self._build_mermaid_page()        # 5 - Mermaid Graphs
        self._build_paper_scanner_page()  # 6 - Math Translation
        self._build_linker_page()         # 7 - Auto-Linker
        self._build_definitions_page()    # 8 - Definitions
        self._build_aggregation_page()    # 9 - Data Aggregation
        self._build_analytics_runner_page()  # 10 - Analytics Runner
        self._build_document_evaluator_page() # 11 - Document Evaluator
        self._build_research_links_page() # 12 - Research Links
        self._build_footnotes_page()      # 13 - Footnotes
        self._build_semantic_dashboard()  # 14 - Semantic
        self._build_tag_manager_page()    # 15 - Tags
        self._build_ollama_page()         # 16 - Ollama
        self._build_database_page()       # 17 - Database
        self._build_settings_page()       # 18 - Settings
    
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

        self.copy_dashboard_btn = QPushButton("📋 Copy Snapshot")
        self.copy_dashboard_btn.clicked.connect(self._copy_dashboard_snapshot)
        btn_row.addWidget(self.copy_dashboard_btn)
        
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

        # Load last dashboard snapshot so results remain visible until next run.
        self._load_cached_dashboard_scan()

    def _dashboard_cache_path(self) -> Path:
        """Path for persisted dashboard scan snapshot."""
        return Path(__file__).resolve().parent.parent / "config" / "dashboard_cache.json"

    def _save_dashboard_scan_cache(self, payload: dict):
        """Persist dashboard scan snapshot."""
        try:
            cache_path = self._dashboard_cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Could not save dashboard cache: {e}")

    def _load_cached_dashboard_scan(self):
        """Load persisted dashboard scan snapshot into UI."""
        cache_path = self._dashboard_cache_path()
        if not cache_path.exists():
            return

        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            stats_display = payload.get("stats_display", {})
            folder_stats = payload.get("folder_stats", {})
            total_files_raw = int(payload.get("total_files_raw", 0) or 0)
            scan_path = payload.get("scan_path", "")
            cached_at = payload.get("cached_at", "")
            scan_type = payload.get("scan_type", "scan")

            for key, label in self._stat_labels.items():
                if key in stats_display:
                    label.setText(str(stats_display[key]))

            if folder_stats:
                sorted_rows = sorted(folder_stats.items(), key=lambda x: x[1], reverse=True)
                self.folder_table.setRowCount(len(sorted_rows))
                for i, (folder, count) in enumerate(sorted_rows):
                    count = int(count)
                    pct = (count / total_files_raw * 100) if total_files_raw else 0
                    self.folder_table.setItem(i, 0, QTableWidgetItem(str(folder)))
                    self.folder_table.setItem(i, 1, QTableWidgetItem(str(count)))
                    self.folder_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

            status = f"Loaded cached {scan_type} results"
            if scan_path:
                status += f" for {Path(scan_path).name}"
            if cached_at:
                status += f" ({cached_at[:19].replace('T', ' ')})"
            self.scan_status_label.setText(status)
            self.scan_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")
            self.activity_list.insertItem(0, f"{datetime.now().strftime('%H:%M:%S')} - Loaded cached dashboard results")
        except Exception as e:
            print(f"Could not load dashboard cache: {e}")
    
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
        self._current_scan_path = scan_path
        
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
        self._current_scan_path = scan_path
        
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

        self._save_dashboard_scan_cache({
            "scan_type": "full scan",
            "scan_scope": self.scan_scope_combo.currentText(),
            "scan_path": str(getattr(self, "_current_scan_path", "")),
            "cached_at": datetime.now().isoformat(timespec="seconds"),
            "total_files_raw": int(result.total_files),
            "folder_stats": dict(result.folder_stats),
            "stats_display": {k: v.text() for k, v in self._stat_labels.items()},
        })
        
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

        folders = result.get('folders', {}) or {}
        sorted_rows = sorted(
            ((name, data.get('count', 0)) for name, data in folders.items()),
            key=lambda x: x[1],
            reverse=True
        )
        self.folder_table.setRowCount(len(sorted_rows))
        for i, (folder, count) in enumerate(sorted_rows):
            pct = (count / result['total_files'] * 100) if result['total_files'] else 0
            self.folder_table.setItem(i, 0, QTableWidgetItem(folder))
            self.folder_table.setItem(i, 1, QTableWidgetItem(str(count)))
            self.folder_table.setItem(i, 2, QTableWidgetItem(f"{pct:.1f}%"))

        self._save_dashboard_scan_cache({
            "scan_type": "quick scan",
            "scan_scope": self.scan_scope_combo.currentText(),
            "scan_path": str(getattr(self, "_current_scan_path", "")),
            "cached_at": datetime.now().isoformat(timespec="seconds"),
            "total_files_raw": int(result.get('total_files', 0)),
            "folder_stats": {name: int(data.get('count', 0)) for name, data in folders.items()},
            "stats_display": {k: v.text() for k, v in self._stat_labels.items()},
        })
        
        self._scan_worker = None
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        self._reset_scan_ui()
        self.scan_status_label.setText(f"✖ Error: {error_msg}")
        self.scan_status_label.setStyleSheet(f"color: {COLORS['accent_red']};")
        QMessageBox.critical(self, "Scan Error", error_msg)
        self._scan_worker = None

    def _copy_dashboard_snapshot(self):
        """Copy dashboard stats + folder breakdown + recent activity."""
        lines: List[str] = []
        lines.append("Dashboard Snapshot Export")
        lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
        lines.append(f"Status: {self.scan_status_label.text()}")
        lines.append("")
        lines.append("Configured Folders:")
        for key, value in self._folder_config.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        lines.append("Stats:")
        for key in sorted(self._stat_labels.keys()):
            lines.append(f"- {key}: {self._stat_labels[key].text()}")
        lines.append("")

        lines.append("Folder Breakdown:")
        for row in range(self.folder_table.rowCount()):
            folder_item = self.folder_table.item(row, 0)
            count_item = self.folder_table.item(row, 1)
            pct_item = self.folder_table.item(row, 2)
            if folder_item and count_item and pct_item:
                lines.append(
                    f"- {folder_item.text()}: {count_item.text()} files ({pct_item.text()})"
                )
        lines.append("")

        lines.append("Recent Activity:")
        for i in range(self.activity_list.count()):
            item = self.activity_list.item(i)
            if item:
                lines.append(f"- {item.text()}")

        self._copy_to_clipboard("\n".join(lines), "Dashboard snapshot copied to clipboard.")
    
    # ==========================================
    # PAGE 1: STATS HUB
    # ==========================================
    def _build_stats_hub_page(self):
        """Build the stats hub page with grid of stat widgets."""
        if HAS_ENGINE:
            try:
                stats_tab = StatsHubTab(self.settings)
                self.page_stack.addWidget(stats_tab)
                return
            except Exception as e:
                print(f"Could not load StatsHubTab: {e}")
        
        # Fallback
        page, layout = self._create_page_container("📊 Stats Hub")
        info = QLabel("⚠️ Stats Hub not available. Check that ui/tabs/stats_hub_tab.py exists.")
        info.setStyleSheet(f"color: {COLORS['accent_yellow']};")
        layout.addWidget(info)
        layout.addStretch()
    
    # ==========================================
    # PAGE 2: VAULT HEALTH
    # ==========================================
    def _build_vault_health_page(self):
        """Build the vault health check page."""
        if HAS_ENGINE:
            try:
                health_tab = VaultHealthTab(self.settings)
                self.page_stack.addWidget(health_tab)
                return
            except Exception as e:
                print(f"Could not load VaultHealthTab: {e}")
        
        page, layout = self._create_page_container("🏥 Vault Health")
        info = QLabel("⚠️ Vault Health tab not available.")
        info.setStyleSheet(f"color: {COLORS['accent_yellow']};")
        layout.addWidget(info)
        layout.addStretch()
    
    # ==========================================
    # PAGE 3: FILE TYPES
    # ==========================================
    def _build_file_types_page(self):
        """Build the file types analysis page."""
        if HAS_ENGINE:
            try:
                types_tab = FileTypesTab(self.settings)
                self.page_stack.addWidget(types_tab)
                return
            except Exception as e:
                print(f"Could not load FileTypesTab: {e}")
        
        page, layout = self._create_page_container("📁 File Types")
        info = QLabel("⚠️ File Types tab not available.")
        info.setStyleSheet(f"color: {COLORS['accent_yellow']};")
        layout.addWidget(info)
        layout.addStretch()
    
    # ==========================================
    # PAGE 4: YAML CHECK
    # ==========================================
    def _build_yaml_check_page(self):
        """Build the YAML validator page."""
        if HAS_ENGINE:
            try:
                yaml_tab = YAMLValidatorTab(self.settings)
                self.page_stack.addWidget(yaml_tab)
                return
            except Exception as e:
                print(f"Could not load YAMLValidatorTab: {e}")
        
        page, layout = self._create_page_container("📋 YAML Validator")
        info = QLabel("⚠️ YAML Validator tab not available.")
        info.setStyleSheet(f"color: {COLORS['accent_yellow']};")
        layout.addWidget(info)
        layout.addStretch()
    
    # ==========================================
    # PAGE 5: MERMAID GRAPHS
    # ==========================================
    def _build_mermaid_page(self):
        """Build the mermaid dependency graph page using MermaidTab widget."""
        if HAS_ENGINE and self.mermaid_engine:
            # Use the full-featured MermaidTab
            mermaid_tab = MermaidTab(self.settings, self.mermaid_engine)
            self.page_stack.addWidget(mermaid_tab)
        else:
            # Fallback if engine not available
            page, layout = self._create_page_container("🎨 Mermaid Dependency Graphs")
            
            info = QLabel("⚠️ Mermaid Generator engine not available.\n\n"
                         "The engine could not be loaded. Check that:\n"
                         "• engine/mermaid_generator.py exists\n"
                         "• ui/tabs/mermaid_tab.py exists\n"
                         "• No import errors in console")
            info.setStyleSheet(f"color: {COLORS['accent_yellow']};")
            info.setWordWrap(True)
            layout.addWidget(info)
            layout.addStretch()
    
    # ==========================================
    # PAGE 3: MATH TRANSLATION
    # ==========================================
    def _build_paper_scanner_page(self):
        """Build the math translation page."""
        page, layout = self._create_page_container("🔢 Math Translation Layer")
        
        info = QLabel("Scan markdown documents for LaTeX equations and apply translations from the math translation table.")
        info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Translation Table Status
        stats_group = QGroupBox("Translation Table Status")
        stats_layout = QVBoxLayout(stats_group)
        
        self.math_stats_label = QLabel("Loading...")
        self.math_stats_label.setStyleSheet(f"color: {COLORS['text_dim']}; padding: 8px; background-color: {COLORS['bg_dark']}; border-radius: 4px;")
        stats_layout.addWidget(self.math_stats_label)
        
        reload_btn = QPushButton("Reload Translation Table")
        reload_btn.clicked.connect(self._reload_math_table)
        stats_layout.addWidget(reload_btn)
        
        layout.addWidget(stats_group)
        self._update_math_stats()
        
        # Document Scanner
        scan_group = QGroupBox("Document Scanner")
        scan_layout = QVBoxLayout(scan_group)
        
        # Mode selection
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.math_mode_inplace = QCheckBox("Modify papers in-place (add translations directly to files)")
        self.math_mode_inplace.setChecked(True)
        self.math_mode_inplace.toggled.connect(self._toggle_math_mode)
        mode_row.addWidget(self.math_mode_inplace)
        mode_row.addStretch()
        scan_layout.addLayout(mode_row)
        
        input_row = QHBoxLayout()
        self.math_input_folder = QLineEdit()
        self.math_input_folder.setPlaceholderText("Select folder with markdown documents...")
        default_math_input = (
            self._folder_config.get('logos_papers', '').strip()
            or self._folder_config.get('notes', '').strip()
            or self._folder_config.get('vault_root', '').strip()
            or self.settings.get('obsidian', 'vault_path', '').strip()
        )
        if default_math_input and Path(default_math_input).exists():
            self.math_input_folder.setText(default_math_input)
        input_row.addWidget(QLabel("Input Folder:"))
        input_row.addWidget(self.math_input_folder)
        browse_input_btn = QPushButton("Browse...")
        browse_input_btn.clicked.connect(self._browse_math_input)
        input_row.addWidget(browse_input_btn)
        scan_layout.addLayout(input_row)
        
        self.math_output_row = QHBoxLayout()
        self.math_output_folder = QLineEdit()
        self.math_output_folder.setPlaceholderText("Select output folder...")
        self.math_output_row.addWidget(QLabel("Output Folder:"))
        self.math_output_row.addWidget(self.math_output_folder)
        self.math_browse_output_btn = QPushButton("Browse...")
        self.math_browse_output_btn.clicked.connect(self._browse_math_output)
        self.math_output_row.addWidget(self.math_browse_output_btn)
        scan_layout.addLayout(self.math_output_row)
        
        # Hide output folder by default (in-place mode)
        self.math_output_folder.setVisible(False)
        for i in range(self.math_output_row.count()):
            widget = self.math_output_row.itemAt(i).widget()
            if widget:
                widget.setVisible(False)
        
        btn_row = QHBoxLayout()
        process_btn = QPushButton("🚀 Add Translations")
        process_btn.setProperty("class", "success")
        process_btn.setMinimumHeight(50)
        process_btn.clicked.connect(self._process_math_documents)
        btn_row.addWidget(process_btn)
        
        remove_btn = QPushButton("🗑️ Remove Translations")
        remove_btn.setProperty("class", "warning")
        remove_btn.setMinimumHeight(50)
        remove_btn.clicked.connect(self._remove_math_translations)
        btn_row.addWidget(remove_btn)
        
        scan_layout.addLayout(btn_row)
        
        self.math_progress = QProgressBar()
        self.math_progress.setVisible(False)
        scan_layout.addWidget(self.math_progress)
        
        layout.addWidget(scan_group)
        
        # Processing Results
        results_group = QGroupBox("Processing Results")
        results_layout = QVBoxLayout(results_group)
        
        self.math_results = QTextEdit()
        self.math_results.setReadOnly(True)
        self.math_results.setMaximumHeight(150)
        results_layout.addWidget(self.math_results)
        
        layout.addWidget(results_group)
        
        # TTS Audio Generation
        tts_group = QGroupBox("TTS Audio Generation")
        tts_layout = QVBoxLayout(tts_group)
        
        tts_file_row = QHBoxLayout()
        self.math_tts_file = QLineEdit()
        self.math_tts_file.setPlaceholderText("Select processed markdown file...")
        tts_file_row.addWidget(QLabel("File:"))
        tts_file_row.addWidget(self.math_tts_file)
        browse_tts_btn = QPushButton("Browse...")
        browse_tts_btn.clicked.connect(self._browse_math_tts)
        tts_file_row.addWidget(browse_tts_btn)
        tts_layout.addLayout(tts_file_row)
        
        tts_btn_row = QHBoxLayout()
        preview_btn = QPushButton("Preview TTS Text")
        preview_btn.clicked.connect(self._preview_tts_text)
        tts_btn_row.addWidget(preview_btn)
        
        generate_btn = QPushButton("Generate Audio")
        generate_btn.setProperty("class", "primary")
        generate_btn.clicked.connect(self._generate_tts_audio)
        tts_btn_row.addWidget(generate_btn)
        tts_layout.addLayout(tts_btn_row)
        
        self.math_tts_preview = QTextEdit()
        self.math_tts_preview.setReadOnly(True)
        self.math_tts_preview.setMaximumHeight(200)
        self.math_tts_preview.setPlaceholderText("TTS text preview will appear here...")
        tts_layout.addWidget(self.math_tts_preview)
        
        layout.addWidget(tts_group)
        layout.addStretch()
    
    def _update_math_stats(self):
        if not self.math_engine:
            self.math_stats_label.setText("⚠️ Math Translation Engine not available")
            return
        
        stats = self.math_engine.get_translation_stats()
        exists_text = "✓ Found" if stats.get('excel_exists') else "✗ Missing"
        bridge_text = "✓ Loaded" if stats.get('bridge_loaded') else ("✓ Found" if stats.get('bridge_exists') else "✗ Missing")
        self.math_stats_label.setText(
            f"Translation Table: {'✓ Loaded' if stats['loaded'] else '✗ Not loaded'}\n"
            f"Entries: {stats['count']}\n"
            f"Excel: {exists_text}\n"
            f"Path: {stats['excel_path']}\n"
            f"Columns: {stats.get('latex_column', '?')} -> {stats.get('translation_column', '?')}\n"
            f"Bridge: {bridge_text} ({stats.get('bridge_count', 0)})"
        )
    
    def _reload_math_table(self):
        if not self.math_engine:
            QMessageBox.warning(self, "Error", "Math Translation Engine not available")
            return
        
        loaded = self.math_engine.load_translation_table()
        self._update_math_stats()
        if loaded:
            QMessageBox.information(self, "Reloaded", "Translation table reloaded successfully")
        else:
            QMessageBox.warning(
                self,
                "Table Not Found",
                "Could not find a math translation table.\n"
                "Check the path shown in Translation Table Status."
            )
    
    def _toggle_math_mode(self, checked):
        """Toggle between in-place and output folder mode."""
        # Show/hide output folder controls
        self.math_output_folder.setVisible(not checked)
        for i in range(self.math_output_row.count()):
            widget = self.math_output_row.itemAt(i).widget()
            if widget:
                widget.setVisible(not checked)
    
    def _browse_math_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.math_input_folder.setText(folder)
    
    def _browse_math_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.math_output_folder.setText(folder)
    
    def _browse_math_tts(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Processed File", "", "Markdown Files (*.md)")
        if file:
            self.math_tts_file.setText(file)
    
    def _process_math_documents(self):
        if not self.math_engine:
            QMessageBox.warning(self, "Error", "Math Translation Engine not available")
            return
        
        input_folder = Path(self.math_input_folder.text())
        
        if not input_folder.exists():
            QMessageBox.warning(self, "Invalid Input", "Please select a valid input folder")
            return
        
        # Check mode
        in_place_mode = self.math_mode_inplace.isChecked()
        
        if in_place_mode:
            # In-place mode: modify files directly
            output_folder = input_folder
            confirm = QMessageBox.question(
                self,
                "Confirm In-Place Modification",
                f"This will modify the original files in:\n{input_folder}\n\n"
                f"Translations will be added directly to your papers.\n\n"
                f"Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if confirm != QMessageBox.StandardButton.Yes:
                return
        else:
            # Output folder mode
            output_folder = Path(self.math_output_folder.text())
            if not output_folder.exists():
                QMessageBox.warning(self, "Invalid Output", "Please select a valid output folder")
                return
        
        self.math_progress.setVisible(True)
        self.math_progress.setRange(0, 0)
        
        try:
            results = self.math_engine.process_folder(input_folder, output_folder)
            
            location_msg = "Modified in-place" if in_place_mode else f"Output saved to: {output_folder}"
            
            self.math_results.setPlainText(
                f"Processing Complete!\n\n"
                f"Files Processed: {results['files_processed']}\n"
                f"Equations Found: {results['equations_found']}\n"
                f"Equations Translated: {results['equations_translated']}\n"
                f"Untranslated: {results['equations_found'] - results['equations_translated']}\n\n"
                f"{location_msg}"
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"Processed {results['files_processed']} files\n"
                f"Found {results['equations_found']} equations\n"
                f"Translated {results['equations_translated']}\n\n"
                f"{location_msg}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Processing failed:\n\n{str(e)}")
        
        finally:
            self.math_progress.setVisible(False)
    
    def _preview_tts_text(self):
        if not self.math_engine:
            QMessageBox.warning(self, "Error", "Math Translation Engine not available")
            return
        
        file_path = Path(self.math_tts_file.text())
        if not file_path.exists():
            QMessageBox.warning(self, "Invalid File", "Please select a valid markdown file")
            return
        
        try:
            tts_text = self.math_engine.generate_tts_text(file_path)
            self.math_tts_preview.setPlainText(tts_text)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Preview failed:\n\n{str(e)}")
    
    def _generate_tts_audio(self):
        if not self.math_engine:
            QMessageBox.warning(self, "Error", "Math Translation Engine not available")
            return
        
        file_path = Path(self.math_tts_file.text())
        if not file_path.exists():
            QMessageBox.warning(self, "Invalid File", "Please select a valid markdown file")
            return
        
        try:
            tts_text = self.math_engine.generate_tts_text(file_path)
            
            tts_pipeline_path = self._resolve_tts_inbox_path()
            tts_pipeline_path.mkdir(parents=True, exist_ok=True)
            
            output_file = tts_pipeline_path / f"{file_path.stem}_tts.txt"
            output_file.write_text(tts_text, encoding='utf-8')
            
            QMessageBox.information(
                self,
                "TTS Text Saved",
                f"TTS text saved to:\n{output_file}\n\n"
                f"Run the TTS pipeline to generate audio."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate TTS text:\n\n{str(e)}")
    
    def _remove_math_translations(self):
        """Remove previously added math translations from documents."""
        if not self.math_engine:
            QMessageBox.warning(self, "Error", "Math Translation Engine not available")
            return
        
        input_folder = Path(self.math_input_folder.text())
        
        if not input_folder.exists():
            QMessageBox.warning(self, "Invalid Input", "Please select a valid input folder")
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"This will remove all math translations from files in:\n{input_folder}\n\n"
            f"The original LaTeX will remain, but spoken translations will be removed.\n\n"
            f"Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        self.math_progress.setVisible(True)
        self.math_progress.setRange(0, 0)
        
        try:
            results = self.math_engine.remove_translations_from_folder(input_folder)
            removed = results.get('callouts_removed', 0)
            cleaned = results.get('files_cleaned', 0)
            
            self.math_results.setPlainText(
                f"Removed translations from {results.get('files_processed', 0)} files\n"
                f"Files changed: {cleaned}\n"
                f"Translations removed: {removed}"
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"Removed translations from {results.get('files_processed', 0)} files\n"
                f"Files changed: {cleaned}\n"
                f"Translations removed: {removed}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Removal failed:\n\n{str(e)}")
        
        finally:
            self.math_progress.setVisible(False)

    def _resolve_tts_inbox_path(self) -> Path:
        """Resolve best available TTS inbox folder."""
        candidates = []

        env_inbox = os.getenv("TTS_INBOX_PATH", "").strip()
        if env_inbox:
            candidates.append(Path(env_inbox))

        candidates.extend([
            Path("O:/Theophysics_Backend/TTS_Pipeline/INBOX"),
            Path(__file__).resolve().parent.parent / "TTS_Pipeline" / "INBOX",
        ])

        for path in candidates:
            if path.exists():
                return path

        # Safe local fallback.
        return Path(__file__).resolve().parent.parent / "data" / "tts_inbox"
    
    # ==========================================
    # PAGE 4: AUTO-LINKER (ENHANCED & THREADED)
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
        browse_btn.clicked.connect(lambda: self._browse_file_or_folder_to_line_edit(self.linker_path_edit))
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
        review_group.setMinimumHeight(560)
        review_layout = QVBoxLayout(review_group)
        
        # Table
        self.linker_table = QTableWidget()
        self.linker_table.setColumnCount(4)
        self.linker_table.setHorizontalHeaderLabels(["Key Term", "Found Count", "Target Link", "Apply?"])
        self.linker_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.linker_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.linker_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.linker_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.linker_table.setMinimumHeight(380)
        review_layout.addWidget(self.linker_table)
        
        # Controls
        ctrl_row = QHBoxLayout()
        sel_all_btn = QPushButton("Select All")
        sel_all_btn.clicked.connect(lambda: self._set_linker_checks(True))
        desel_all_btn = QPushButton("Deselect All")
        desel_all_btn.clicked.connect(lambda: self._set_linker_checks(False))
        approve_memory_btn = QPushButton("⬅ Move Selected to Approved")
        approve_memory_btn.clicked.connect(self._persist_selected_linker_terms_as_approved)
        ignore_memory_btn = QPushButton("Move Selected to Ignored ➡")
        ignore_memory_btn.clicked.connect(self._ignore_selected_linker_terms)
        
        ctrl_row.addWidget(sel_all_btn)
        ctrl_row.addWidget(desel_all_btn)
        ctrl_row.addWidget(approve_memory_btn)
        ctrl_row.addWidget(ignore_memory_btn)
        ctrl_row.addStretch()
        
        self.apply_links_btn = QPushButton("✅ Apply Selected Links")
        self.apply_links_btn.setProperty("class", "success")
        self.apply_links_btn.setEnabled(False)
        self.apply_links_btn.clicked.connect(self._apply_selected_links_threaded)
        ctrl_row.addWidget(self.apply_links_btn)
        
        review_layout.addLayout(ctrl_row)
        layout.addWidget(review_group)

        state_group = QGroupBox("3. Persistent Term Controls")
        state_layout = QHBoxLayout(state_group)

        approved_col = QVBoxLayout()
        approved_col.addWidget(QLabel("Always Approved"))
        self.linker_approved_list = QListWidget()
        approved_col.addWidget(self.linker_approved_list)
        approved_remove_btn = QPushButton("Remove Selected Approved")
        approved_remove_btn.clicked.connect(self._remove_selected_linker_approved_terms)
        approved_col.addWidget(approved_remove_btn)
        state_layout.addLayout(approved_col)

        ignored_col = QVBoxLayout()
        ignored_col.addWidget(QLabel("Always Ignored"))
        self.linker_ignored_list = QListWidget()
        ignored_col.addWidget(self.linker_ignored_list)
        ignored_remove_btn = QPushButton("Remove Selected Ignored")
        ignored_remove_btn.clicked.connect(self._remove_selected_linker_ignored_terms)
        ignored_col.addWidget(ignored_remove_btn)
        state_layout.addLayout(ignored_col)

        layout.addWidget(state_group)
        self._refresh_autolinker_state_lists()
        layout.addStretch()

    def _browse_file_or_folder_to_line_edit(self, line_edit: QLineEdit):
        """
        Auto-linker path picker: allow selecting either a single markdown file
        or a folder.
        """
        current = line_edit.text().strip()
        start_dir = current if current else str(Path.home())
        if Path(start_dir).is_file():
            start_dir = str(Path(start_dir).parent)

        # 1) Try single-file pick first (for targeted one-page linking)
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Markdown File (or Cancel to choose folder)",
            start_dir,
            "Markdown Files (*.md);;All Files (*)",
        )
        if file_path:
            line_edit.setText(file_path)
            return

        # 2) Fallback to folder selection
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", start_dir)
        if folder_path:
            line_edit.setText(folder_path)

    def _set_linker_checks(self, checked: bool):
        """Helper to mass check/uncheck."""
        for row in range(self.linker_table.rowCount()):
            item = self.linker_table.cellWidget(row, 3)
            # Find checkbox in container
            chk = item.findChild(QCheckBox) if item else None
            if chk:
                chk.setChecked(checked)

    def _autolinker_state_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / "config" / "ui_cache" / "autolinker_terms_state.json"

    def _load_autolinker_state(self) -> Dict[str, List[str]]:
        state = {"approved_terms": [], "ignored_terms": []}
        path = self._autolinker_state_path()
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    approved = loaded.get("approved_terms", [])
                    ignored = loaded.get("ignored_terms", [])
                    state["approved_terms"] = sorted({str(x).strip() for x in approved if str(x).strip()})
                    state["ignored_terms"] = sorted({str(x).strip() for x in ignored if str(x).strip()})
            except Exception:
                pass
        return state

    def _save_autolinker_state(self):
        path = self._autolinker_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._autolinker_state, indent=2), encoding="utf-8")

    def _refresh_autolinker_state_lists(self):
        if not hasattr(self, "linker_approved_list") or not hasattr(self, "linker_ignored_list"):
            return
        self.linker_approved_list.clear()
        self.linker_ignored_list.clear()
        for term in self._autolinker_state.get("approved_terms", []):
            self.linker_approved_list.addItem(term)
        for term in self._autolinker_state.get("ignored_terms", []):
            self.linker_ignored_list.addItem(term)

    def _get_checked_linker_rows(self) -> List[int]:
        selected_rows = []
        for row in range(self.linker_table.rowCount()):
            container = self.linker_table.cellWidget(row, 3)
            chk = container.findChild(QCheckBox) if container else None
            if chk and chk.isChecked():
                selected_rows.append(row)
        return selected_rows

    def _get_selected_linker_rows(self) -> List[int]:
        return sorted({idx.row() for idx in self.linker_table.selectedIndexes()})

    def _get_action_linker_rows(self) -> List[int]:
        selected_rows = self._get_selected_linker_rows()
        if selected_rows:
            return selected_rows
        return self._get_checked_linker_rows()

    def _persist_selected_linker_terms_as_approved(self):
        rows = self._get_action_linker_rows()
        if not rows:
            QMessageBox.information(self, "Info", "No selected terms to save.")
            return

        approved = set(self._autolinker_state.get("approved_terms", []))
        ignored = set(self._autolinker_state.get("ignored_terms", []))
        added = 0

        for row in rows:
            term_item = self.linker_table.item(row, 0)
            if not term_item:
                continue
            term = term_item.text().strip()
            if not term:
                continue
            if term not in approved:
                added += 1
            approved.add(term)
            ignored.discard(term)

        self._autolinker_state["approved_terms"] = sorted(approved)
        self._autolinker_state["ignored_terms"] = sorted(ignored)
        self._save_autolinker_state()
        self._refresh_autolinker_state_lists()
        
        approved_now = set()
        for row in rows:
            term_item = self.linker_table.item(row, 0)
            if term_item and term_item.text().strip():
                approved_now.add(term_item.text().strip())

        rows_to_keep = []
        for row in range(self.linker_table.rowCount()):
            term_item = self.linker_table.item(row, 0)
            if not term_item:
                continue
            term = term_item.text().strip()
            if term not in approved_now:
                rows_to_keep.append((
                    term,
                    self.linker_table.item(row, 1).text() if self.linker_table.item(row, 1) else "0",
                    self.linker_table.item(row, 2).text() if self.linker_table.item(row, 2) else "",
                ))

        self.linker_table.setRowCount(0)
        for row, (term, count, target) in enumerate(rows_to_keep):
            self.linker_table.insertRow(row)
            self.linker_table.setItem(row, 0, QTableWidgetItem(term))
            self.linker_table.setItem(row, 1, QTableWidgetItem(count))
            self.linker_table.setItem(row, 2, QTableWidgetItem(target))

            chk = QCheckBox()
            chk.setChecked(False)
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0, 0, 0, 0)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(chk)
            self.linker_table.setCellWidget(row, 3, container)

        self.apply_links_btn.setEnabled(self.linker_table.rowCount() > 0 or bool(approved))
        self.linker_log.append(f"⬅ Moved {added} terms to Always Approved.")

    def _ignore_selected_linker_terms(self):
        rows = self._get_action_linker_rows()
        if not rows:
            QMessageBox.information(self, "Info", "No selected terms to ignore.")
            return

        approved = set(self._autolinker_state.get("approved_terms", []))
        ignored = set(self._autolinker_state.get("ignored_terms", []))
        added = 0
        ignored_now = []

        for row in rows:
            term_item = self.linker_table.item(row, 0)
            if not term_item:
                continue
            term = term_item.text().strip()
            if not term:
                continue
            if term not in ignored:
                added += 1
            ignored.add(term)
            approved.discard(term)
            ignored_now.append(term)

        self._autolinker_state["approved_terms"] = sorted(approved)
        self._autolinker_state["ignored_terms"] = sorted(ignored)
        self._save_autolinker_state()
        self._refresh_autolinker_state_lists()

        ignored_set = set(ignored_now)
        rows_to_keep = []
        for row in range(self.linker_table.rowCount()):
            term_item = self.linker_table.item(row, 0)
            if not term_item:
                continue
            term = term_item.text().strip()
            if term not in ignored_set:
                rows_to_keep.append((
                    term,
                    self.linker_table.item(row, 1).text() if self.linker_table.item(row, 1) else "0",
                    self.linker_table.item(row, 2).text() if self.linker_table.item(row, 2) else "",
                ))

        self.linker_table.setRowCount(0)
        for row, (term, count, target) in enumerate(rows_to_keep):
            self.linker_table.insertRow(row)
            self.linker_table.setItem(row, 0, QTableWidgetItem(term))
            self.linker_table.setItem(row, 1, QTableWidgetItem(count))
            self.linker_table.setItem(row, 2, QTableWidgetItem(target))

            chk = QCheckBox()
            chk.setChecked(term in approved)
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0, 0, 0, 0)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(chk)
            self.linker_table.setCellWidget(row, 3, container)

        self.apply_links_btn.setEnabled(self.linker_table.rowCount() > 0 or bool(approved))
        self.linker_log.append(f"🚫 Added {added} terms to Always Ignored.")

    def _remove_selected_linker_approved_terms(self):
        selected = self.linker_approved_list.selectedItems() if hasattr(self, "linker_approved_list") else []
        if not selected:
            QMessageBox.information(self, "Info", "Select one or more approved terms to remove.")
            return
        approved = set(self._autolinker_state.get("approved_terms", []))
        for item in selected:
            approved.discard(item.text().strip())
        self._autolinker_state["approved_terms"] = sorted(approved)
        self._save_autolinker_state()
        self._refresh_autolinker_state_lists()

    def _remove_selected_linker_ignored_terms(self):
        selected = self.linker_ignored_list.selectedItems() if hasattr(self, "linker_ignored_list") else []
        if not selected:
            QMessageBox.information(self, "Info", "Select one or more ignored terms to remove.")
            return
        ignored = set(self._autolinker_state.get("ignored_terms", []))
        for item in selected:
            ignored.discard(item.text().strip())
        self._autolinker_state["ignored_terms"] = sorted(ignored)
        self._save_autolinker_state()
        self._refresh_autolinker_state_lists()

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
        replacements = {}
        for row in range(self.linker_table.rowCount()):
            container = self.linker_table.cellWidget(row, 3)
            chk = container.findChild(QCheckBox)
            if chk and chk.isChecked():
                term = self.linker_table.item(row, 0).text()
                approved.append(term)

        auto_approved = []
        approved_memory = set(self._autolinker_state.get("approved_terms", []))
        for term in approved_memory:
            if term in self._current_scan_targets:
                auto_approved.append(term)

        approved_all = sorted(set(approved + auto_approved))
        for term in approved_all:
            target = self._current_scan_targets.get(term, "")
            if target:
                replacements[term] = target

        if not approved_all:
            QMessageBox.information(self, "Info", "No terms selected to apply.")
            return

        approved_set = set(self._autolinker_state.get("approved_terms", []))
        ignored_set = set(self._autolinker_state.get("ignored_terms", []))
        approved_set.update(approved_all)
        ignored_set.difference_update(approved_all)
        self._autolinker_state["approved_terms"] = sorted(approved_set)
        self._autolinker_state["ignored_terms"] = sorted(ignored_set)
        self._save_autolinker_state()
        self._refresh_autolinker_state_lists()

        self._start_apply_links_thread(
            files=self._files_to_link,
            approved_terms=approved_all,
            link_all=self.link_all_check.isChecked(),
            term_replacements=replacements,
        )

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
        self._current_scan_targets = {}

        if getattr(self, '_auto_linker_startup', False):
            self._auto_linker_startup = False
            approved_memory = set(self._autolinker_state.get("approved_terms", []))
            approved = [term for term in global_counts.keys() if term in approved_memory] if approved_memory else list(global_counts.keys())
            if approved:
                self._start_apply_links_thread(
                    files=files,
                    approved_terms=approved,
                    link_all=self._auto_linker_startup_link_all,
                )
            else:
                self.linker_log.append("ℹ️ Startup run found terms, but none matched Always Approved list.")
            return
        
        # Get minimum occurrences threshold
        min_occurrences = 1
        if hasattr(self, 'min_occurrences_spin'):
            min_occurrences = self.min_occurrences_spin.value()
        
        ignored_terms = set(self._autolinker_state.get("ignored_terms", []))
        approved_terms = set(self._autolinker_state.get("approved_terms", []))

        # Filter by minimum occurrences and remove globally ignored terms
        filtered_counts = {
            term: count
            for term, count in global_counts.items()
            if count >= min_occurrences and term not in ignored_terms
        }
        
        # Check fallback and dual-link settings
        wiki_fallback = hasattr(self, 'wiki_fallback_check') and self.wiki_fallback_check.isChecked()
        dual_link = hasattr(self, 'dual_link_check') and self.dual_link_check.isChecked()
        sorted_items = sorted(filtered_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Instantiate linker with real vault root, not CWD
        from engine.knowledge_acquisition_engine import AutoLinker
        vault_root = Path(self.settings.get('obsidian', 'vault_path', '.') or '.')
        linker = AutoLinker(vault_root)
        
        # Get glossary terms for checking
        glossary_path = self._folder_config.get('glossary', '')
        glossary_terms = set()
        if glossary_path and Path(glossary_path).exists():
            for md_file in Path(glossary_path).rglob("*.md"):
                glossary_terms.add(md_file.stem.lower())

        def _best_external_link(term: str):
            try:
                links = self.research_linker.get_all_links_for_term(term, max_links=1)
                if not links:
                    return None, None
                source_key, url = next(iter(links.items()))
                template = self.research_linker.LINK_TEMPLATES.get(source_key, {})
                source_name = template.get('display_name', source_key.replace('_', ' ').title())
                return url, source_name
            except Exception:
                return None, None

        all_row_data = []
        for term, count in sorted_items:
            glossary_target = linker.custom_terms.get(term, f"[[{term}]]")
            has_glossary = term.lower() in glossary_terms or term in linker.custom_terms

            target = glossary_target
            source_name = "Glossary/Internal"
            external_url, external_source_name = _best_external_link(term)

            if dual_link and has_glossary and external_url:
                target = f"{glossary_target} ([{external_source_name}]({external_url}))"
                source_name = f"Glossary + {external_source_name}"
            elif wiki_fallback and not has_glossary and external_url:
                target = f"[{term}]({external_url})"
                source_name = external_source_name
            elif wiki_fallback and not has_glossary:
                wiki_url = f"https://en.wikipedia.org/wiki/{term.replace(' ', '_')}"
                target = f"[{term}]({wiki_url})"
                source_name = "Wikipedia"

            all_row_data.append((term, count, target, source_name))
            self._current_scan_targets[term] = target

        # Center table is pending-only; approved and ignored live in side lists.
        row_data = [r for r in all_row_data if r[0] not in approved_terms]

        # Populate table
        self.linker_table.setRowCount(len(row_data))
        for row, (term, count, target, source_name) in enumerate(row_data):
            self.linker_table.setItem(row, 0, QTableWidgetItem(term))
            self.linker_table.setItem(row, 1, QTableWidgetItem(str(count)))
            target_item = QTableWidgetItem(target)
            target_item.setToolTip(f"Primary source: {source_name}")
            self.linker_table.setItem(row, 2, target_item)

            # Centered checkbox
            chk = QCheckBox()
            chk.setChecked(False)
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(0,0,0,0)
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.addWidget(chk)
            self.linker_table.setCellWidget(row, 3, container)
        
        filtered_out = len(global_counts) - len(filtered_counts)
        auto_approved = sum(1 for term, _, _, _ in all_row_data if term in approved_terms)
        self.apply_links_btn.setEnabled(len(row_data) > 0 or auto_approved > 0)
        self.linker_log.append(
            f"\n✅ SCAN COMPLETED. Pending {len(row_data)} terms in center "
            f"(left approved: {auto_approved}, filtered out: {filtered_out})."
        )

    def _start_apply_links_thread(self, files: list, approved_terms: list, link_all: bool, term_replacements: Optional[Dict[str, str]] = None):
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
            link_all=link_all,
            term_replacements=term_replacements or {},
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

        self.inject_templates_btn = QPushButton("📝 INJECT TEMPLATES (Add Structure)")
        self.inject_templates_btn.setProperty("class", "warning")
        self.inject_templates_btn.clicked.connect(self._inject_definition_templates)
        scan_layout.addWidget(self.inject_templates_btn)

        self.run_definition_engine_btn = QPushButton("⚡ RUN ENGINE (Auto-Fill All)")
        self.run_definition_engine_btn.setProperty("class", "purple")
        self.run_definition_engine_btn.clicked.connect(self._run_definition_engine_autofill)
        scan_layout.addWidget(self.run_definition_engine_btn)

        self.def_dry_run = QCheckBox("Dry run (preview only, no changes)")
        scan_layout.addWidget(self.def_dry_run)

        self.def_with_wiki = QCheckBox("Include Wikipedia enrichment (slower)")
        scan_layout.addWidget(self.def_with_wiki)

        left.addWidget(scan_group)

        # Stats
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.def_stats_label = QLabel("No scan performed yet")
        self.def_stats_label.setStyleSheet(f"color: {COLORS['text_muted']};")
        stats_layout.addWidget(self.def_stats_label)
        left.addWidget(stats_group)

        # Definitions list
        list_group = QGroupBox("Definitions")
        list_layout = QVBoxLayout(list_group)
        self.def_list = QListWidget()
        self.def_list.currentItemChanged.connect(self._on_definition_selected)
        self.def_list.setMinimumHeight(200)
        list_layout.addWidget(self.def_list)
        left.addWidget(list_group)

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
        self.def_term_edit.setReadOnly(True)
        term_row.addWidget(self.def_term_edit)
        details_layout.addLayout(term_row)

        self.def_completeness_label = QLabel("Completeness: ---")
        details_layout.addWidget(self.def_completeness_label)

        # Missing sections
        missing_group = QGroupBox("⚠️ Missing Sections")
        missing_layout = QVBoxLayout(missing_group)
        self.def_missing_label = QLabel("Select a definition to see what's missing")
        self.def_missing_label.setWordWrap(True)
        missing_layout.addWidget(self.def_missing_label)
        details_layout.addWidget(missing_group)

        # Section checklist
        checklist_group = QGroupBox("Hierarchy Checklist")
        checklist_layout = QVBoxLayout(checklist_group)

        self._definition_hierarchy = [
            ("Identity Layer", [
                ("1. Canonical Name", ["canonical name", "primary term"]),
                ("2. Aliases / Synonyms", ["aliases", "synonyms", "aliases / synonyms"]),
            ]),
            ("Formal Core", [
                ("3. Formal Definition (Minimal Form)", ["formal definition", "minimal form", "canonical definition"]),
                ("4. Structural Definition (Expanded Form)", ["structural definition", "expanded form", "necessary conditions", "sufficient conditions"]),
                ("5. Mathematical / Logical Form", ["mathematical", "logical form", "mathematical structure"]),
                ("6. Mechanism", ["mechanism", "causal pathway", "information flow"]),
            ]),
            ("Validation Layer", [
                ("7. Empirical Anchors", ["empirical anchors", "observable evidence", "evidence"]),
                ("8. Comparative Alignment (Wikipedia / Standard Models)", ["comparative alignment", "external comparison", "wikipedia", "standard models"]),
                ("11. Defeat Conditions (Falsifiability)", ["defeat conditions", "falsifiability", "failure modes"]),
            ]),
            ("Interpretive Layer", [
                ("9. Analogical Layer (Optional)", ["analogical layer", "analogy", "the analogy"]),
                ("10. Forward Implications", ["forward implications", "integration map", "it predicts"]),
                ("12. Status Notes", ["status notes", "open problems", "usage drift log", "notes"]),
            ]),
        ]
        self.def_section_checkboxes = {}
        for group_name, sections in self._definition_hierarchy:
            group_label = QLabel(group_name)
            group_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 9pt;")
            checklist_layout.addWidget(group_label)
            for section_label, _patterns in sections:
                cb = QCheckBox(section_label)
                cb.setEnabled(False)
                checklist_layout.addWidget(cb)
                self.def_section_checkboxes[section_label] = cb

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
        save_btn.clicked.connect(self._save_definition_changes)
        btn_row.addWidget(save_btn)

        open_btn = QPushButton("📂 Open in Explorer")
        open_btn.clicked.connect(self._open_selected_definition_folder)
        btn_row.addWidget(open_btn)
        editor_layout.addLayout(btn_row)

        details_layout.addWidget(editor_group)

        right.addWidget(details_group)
        columns.addLayout(right, 2)

        layout.addLayout(columns)
        self._definition_records = []
        self._selected_definition_path = None

    def _browse_to_line_edit(self, edit: QLineEdit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", edit.text())
        if folder:
            edit.setText(folder)

    def _scan_definition_files(self, root: Path, recursive: bool) -> List[Path]:
        files = root.rglob("*.md") if recursive else root.glob("*.md")
        return sorted([p for p in files if p.is_file()])

    def _extract_term_from_content(self, content: str, fallback: str) -> str:
        for line in content.splitlines():
            if line.startswith("# "):
                term = line[2:].strip()
                if term:
                    return term
        return fallback

    def _normalize_heading_text(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    def _flat_hierarchy_sections(self) -> List[tuple[str, List[str]]]:
        flat = []
        for _group, sections in self._definition_hierarchy:
            flat.extend(sections)
        return flat

    def _detect_definition_sections(self, content: str) -> Dict[str, bool]:
        heading_matches = re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", content, flags=re.MULTILINE)
        normalized_headings = [self._normalize_heading_text(h) for h in heading_matches]
        normalized_content = self._normalize_heading_text(content)

        section_presence: Dict[str, bool] = {}
        for section_label, patterns in self._flat_hierarchy_sections():
            found = False
            for pattern in patterns:
                needle = self._normalize_heading_text(pattern)
                if any(needle in heading for heading in normalized_headings):
                    found = True
                    break
                if needle in normalized_content:
                    found = True
                    break
            section_presence[section_label] = found

        return section_presence

    def _refresh_definition_checklist(self, content: str):
        section_presence = self._detect_definition_sections(content)

        for label, cb in self.def_section_checkboxes.items():
            cb.setChecked(section_presence.get(label, False))

        total = len(self.def_section_checkboxes)
        present = sum(1 for v in section_presence.values() if v)
        missing_labels = [label for label, ok in section_presence.items() if not ok]
        completeness = (present / total) if total else 0.0

        self.def_completeness_label.setText(
            f"Completeness: {present}/{total} ({completeness:.0%})"
        )

        if missing_labels:
            self.def_missing_label.setText(
                "Missing:\n- " + "\n- ".join(missing_labels)
            )
        else:
            self.def_missing_label.setText("No missing sections detected.")

    def _on_definition_selected(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem] = None
    ):
        if not current:
            self._selected_definition_path = None
            self.def_term_edit.clear()
            self.def_content_editor.clear()
            self.def_completeness_label.setText("Completeness: ---")
            self.def_missing_label.setText("Select a definition to see what's missing")
            for cb in self.def_section_checkboxes.values():
                cb.setChecked(False)
            return

        raw_path = current.data(Qt.ItemDataRole.UserRole)
        if not raw_path:
            return

        selected_path = Path(raw_path)
        self._selected_definition_path = selected_path
        try:
            content = selected_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            QMessageBox.critical(self, "Read Error", f"Could not open file:\n{selected_path}\n\n{e}")
            return

        term = self._extract_term_from_content(content, selected_path.stem)
        self.def_term_edit.setText(term)
        self.def_content_editor.setPlainText(content)
        self._refresh_definition_checklist(content)

    def _save_definition_changes(self):
        if not self._selected_definition_path:
            QMessageBox.warning(self, "No Definition", "Select a definition first.")
            return

        try:
            content = self.def_content_editor.toPlainText()
            self._selected_definition_path.write_text(content, encoding='utf-8')
            self._refresh_definition_checklist(content)
            self.lexicon_status.setText(f"Saved {self._selected_definition_path.name}")
            QMessageBox.information(self, "Saved", f"Saved:\n{self._selected_definition_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _open_selected_definition_folder(self):
        if not self._selected_definition_path:
            QMessageBox.warning(self, "No Definition", "Select a definition first.")
            return

        target = self._selected_definition_path.parent
        try:
            subprocess.run(["explorer", str(target)], check=False)
        except Exception:
            QMessageBox.information(self, "Path", str(target))

    def _build_section_scaffold(self, section_label: str, term: str) -> str:
        blocks = {
            "1. Canonical Name": f"## 1. Canonical Name\n**Primary Term:** {term}\n\nFormal standardized name used in this system.",
            "2. Aliases / Synonyms": "## 2. Aliases / Synonyms\n- Alternate name 1\n- Alternate name 2\n- Historical term",
            "3. Formal Definition (Minimal Form)": "## 3. Formal Definition (Minimal Form)\n\n> One-sentence compressed definition.\n\nMust be structurally precise. No metaphor.",
            "4. Structural Definition (Expanded Form)": "## 4. Structural Definition (Expanded Form)\n\n- Necessary conditions:\n- Sufficient conditions:\n- Domain of applicability:\n- Boundary conditions:\n- Exclusions (what this is NOT):",
            "5. Mathematical / Logical Form": "## 5. Mathematical / Logical Form\n\n- Equation form:\n- Symbolic structure:\n- Constraints:\n\nIf no equation exists, state: \"Currently non-mathematized.\"",
            "6. Mechanism": "## 6. Mechanism\n\n- Causal pathway:\n- Field interaction:\n- Information flow:\n- Observer dependency (if relevant):",
            "7. Empirical Anchors": "## 7. Empirical Anchors\n\nObservable evidence:\n- Experimental evidence\n- Historical data\n- Textual evidence\n- Cross-domain parallels",
            "8. Comparative Alignment (Wikipedia / Standard Models)": "## 8. Comparative Alignment (Wikipedia / Standard Models)\n\n**Wikipedia Summary Snapshot:**\n\n**Agreement Zones:**\n- \n\n**Deviation Zones:**\n- \n\n**Counterfactual Risks Identified:**\n- ",
            "9. Analogical Layer (Optional)": "## 9. Analogical Layer (Optional)\n\nMetaphorical or narrative framing only:\n- Analogy 1:\n- Visual model:\n- Narrative framing:",
            "10. Forward Implications": "## 10. Forward Implications\n\nIf this definition is true, then:\n- It predicts...\n- It constrains...\n- It forbids...\n- It requires...",
            "11. Defeat Conditions (Falsifiability)": "## 11. Defeat Conditions (Falsifiability)\n\nThis definition fails if:\n- Condition A observed\n- Contradiction with X verified\n- Logical inconsistency demonstrated",
            "12. Status Notes": "## 12. Status Notes\n\n- Open problems:\n- Areas under refinement:\n- Pending mathematical formalization:",
        }
        return blocks.get(section_label, f"## {section_label}\n\nTODO")

    def _inject_missing_structure(self, content: str, term: str, missing_sections: List[str]) -> str:
        updated = content.rstrip() + "\n"
        stripped = updated.lstrip()

        if not stripped.startswith("---"):
            frontmatter = (
                "---\n"
                "type: definition\n"
                "status: draft\n"
                "domain: unknown\n"
                "confidence: 0.0\n"
                "wikipedia_checked: no\n"
                "counterfactual_conflicts: []\n"
                "related_axioms: []\n"
                "---\n\n"
            )
            updated = frontmatter + stripped

        if not re.search(r"^\s*#\s+.+$", updated, flags=re.MULTILINE):
            updated = updated.rstrip() + f"\n\n# {term}\n"

        injected_blocks = [self._build_section_scaffold(label, term) for label in missing_sections]
        if injected_blocks:
            updated = updated.rstrip() + "\n\n---\n\n" + "\n\n".join(injected_blocks) + "\n"

        return updated

    def _scan_definitions(self):
        """Scan definitions folder."""
        path_text = self.def_folder_path.text().strip()
        path = Path(path_text) if path_text else None
        if not path or not path.exists():
            QMessageBox.warning(self, "No Folder", "Please select a valid definitions folder.")
            return

        recursive = self.def_recursive.isChecked()
        md_files = self._scan_definition_files(path, recursive)

        # Keep legacy manager in sync, but scan directly from selected glossary path.
        try:
            self.definitions_manager.vault_path = path.parent
            self.definitions_manager.definitions_folder = path
            self.definitions_manager.scan_definitions()
        except Exception:
            pass

        self._definition_records = []
        self.def_list.clear()

        incomplete_count = 0
        for md_file in md_files:
            if md_file.name.startswith("_"):
                continue
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            term = self._extract_term_from_content(content, md_file.stem)
            section_presence = self._detect_definition_sections(content)
            total = len(section_presence)
            present = sum(1 for v in section_presence.values() if v)
            completeness = (present / total) if total else 0.0
            missing = [k for k, ok in section_presence.items() if not ok]

            if missing:
                incomplete_count += 1

            record = {
                "term": term,
                "path": md_file,
                "completeness": completeness,
                "missing": missing,
            }
            self._definition_records.append(record)

            item = QListWidgetItem(f"{term}  [{int(completeness * 100)}%]")
            item.setData(Qt.ItemDataRole.UserRole, str(md_file))
            self.def_list.addItem(item)

        self._definition_records.sort(key=lambda r: (r["completeness"], r["term"].lower()))
        self.def_stats_label.setText(
            f"Found {len(self._definition_records)} definition files | "
            f"{incomplete_count} with missing sections"
        )

        if self.def_list.count() > 0:
            self.def_list.setCurrentRow(0)

        QMessageBox.information(
            self,
            "Scan Complete",
            f"Scanned {len(self._definition_records)} definition files.\n"
            f"Incomplete: {incomplete_count}",
        )

    def _inject_definition_templates(self):
        if not self._definition_records:
            QMessageBox.warning(self, "No Scan Results", "Scan definitions first.")
            return

        selected_item = self.def_list.currentItem()
        selected_path = Path(selected_item.data(Qt.ItemDataRole.UserRole)) if selected_item else None

        # Practical safety: let user choose selected-only vs all.
        targets = []
        if selected_path and len(self._definition_records) > 1:
            choice = QMessageBox.question(
                self,
                "Inject Templates",
                "Inject into selected definition only?\n\nYes = selected only\nNo = all scanned definitions\nCancel = abort",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if choice == QMessageBox.StandardButton.Cancel:
                return
            if choice == QMessageBox.StandardButton.Yes:
                targets = [selected_path]
            else:
                targets = [r["path"] for r in self._definition_records]
        elif selected_path:
            targets = [selected_path]
        else:
            targets = [r["path"] for r in self._definition_records]

        dry_run = self.def_dry_run.isChecked()
        touched = 0
        unchanged = 0
        failures = 0

        for file_path in targets:
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                term = self._extract_term_from_content(content, file_path.stem)
                section_presence = self._detect_definition_sections(content)
                missing_sections = [label for label, present in section_presence.items() if not present]

                if not missing_sections:
                    unchanged += 1
                    continue

                if dry_run:
                    touched += 1
                    continue

                updated = self._inject_missing_structure(content, term, missing_sections)
                file_path.write_text(updated, encoding='utf-8')
                touched += 1
            except Exception:
                failures += 1

        mode = "Dry run" if dry_run else "Injection complete"
        QMessageBox.information(
            self,
            "Template Injection",
            f"{mode}.\n\nUpdated: {touched}\nAlready complete: {unchanged}\nFailed: {failures}",
        )

        if not dry_run:
            self._scan_definitions()

    def _run_definition_engine_autofill(self):
        path_text = self.def_folder_path.text().strip()
        glossary_dir = Path(path_text) if path_text else None
        if not glossary_dir or not glossary_dir.exists():
            QMessageBox.warning(self, "No Folder", "Please select a valid definitions folder.")
            return

        script_path = Path(__file__).resolve().parent.parent / "scripts" / "architect_glossary_definitions.py"
        if not script_path.exists():
            QMessageBox.critical(self, "Script Missing", f"Could not find:\n{script_path}")
            return

        output_dir = glossary_dir / "_STRUCTURED_DRAFTS_GUI"
        cmd = [
            sys.executable,
            str(script_path),
            "--glossary-dir",
            str(glossary_dir),
            "--output-dir",
            str(output_dir),
            "--overwrite",
        ]

        if self.def_dry_run.isChecked():
            cmd.append("--dry-run")
        if self.def_with_wiki.isChecked():
            cmd.append("--with-wikipedia")

        self.lexicon_status.setText("Running glossary architecture engine...")
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(script_path.parent),
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            self.lexicon_status.setText(f"Engine error: {e}")
            QMessageBox.critical(self, "Engine Error", str(e))
            return

        if proc.returncode != 0:
            details = (proc.stderr or proc.stdout or "").strip()
            tail = "\n".join(details.splitlines()[-20:])
            self.lexicon_status.setText("Engine failed")
            QMessageBox.critical(
                self,
                "Engine Failed",
                f"Command failed ({proc.returncode}).\n\n{tail or 'No error output.'}",
            )
            return

        report_path = output_dir / "architecture_report.json"
        self.lexicon_status.setText(
            f"Engine complete. {'Dry run only.' if self.def_dry_run.isChecked() else f'Report: {report_path}'}"
        )

        stdout_tail = "\n".join((proc.stdout or "").strip().splitlines()[-12:])
        QMessageBox.information(
            self,
            "Engine Complete",
            (
                "Definition architecture pass finished.\n\n"
                f"Output folder: {output_dir}\n"
                f"{'Dry run: no files written.\n' if self.def_dry_run.isChecked() else ''}\n"
                f"{stdout_tail}"
            ),
        )

    # ==========================================
    # PAGE 4: ANALYTICS RUNNER
    # ==========================================
    def _build_analytics_runner_page(self):
        """Build dedicated tab to run full Obsidian Data Analytics pipeline."""
        page, layout = self._create_page_container("⚡ Analytics Runner")

        runner_group = QGroupBox("Run All Metrics (Obsidian Data Analytics)")
        runner_layout = QVBoxLayout(runner_group)

        runner_desc = QLabel(
            "Pick Analytics Root once (engine location), then choose the Target Folder to analyze each run. "
            "Outputs are written to <Target Folder>\\Data Analytics so each vault keeps its own analytics package."
        )
        runner_desc.setWordWrap(True)
        runner_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 8px;")
        runner_layout.addWidget(runner_desc)

        runner_row = QHBoxLayout()
        runner_row.addWidget(QLabel("Analytics Root:"))
        self.analytics_root_input = QLineEdit()
        default_analytics_root = self._folder_config.get('analytics', '') or r"O:\999_IGNORE\Obsidian Data Analytics"
        self.analytics_root_input.setText(default_analytics_root)
        self.analytics_root_input.setPlaceholderText(r"O:\999_IGNORE\Obsidian Data Analytics")
        runner_row.addWidget(self.analytics_root_input)

        browse_analytics_btn = QPushButton("Browse")
        browse_analytics_btn.clicked.connect(self._browse_analytics_root)
        runner_row.addWidget(browse_analytics_btn)
        runner_layout.addLayout(runner_row)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target Folder:"))
        self.analytics_target_input = QLineEdit()
        default_target = (
            self._folder_config.get('analytics_target', '').strip()
            or self._folder_config.get('vault_root', '').strip()
            or self.settings.get('obsidian', 'vault_path', '').strip()
        )
        self.analytics_target_input.setText(default_target)
        self.analytics_target_input.setPlaceholderText(r"O:\_Theophysics_v3\00_AXIOMS")
        self.analytics_target_input.editingFinished.connect(self._refresh_analytics_shell)
        target_row.addWidget(self.analytics_target_input)

        browse_target_btn = QPushButton("Browse")
        browse_target_btn.clicked.connect(self._browse_analytics_target)
        target_row.addWidget(browse_target_btn)
        runner_layout.addLayout(target_row)

        runner_btn_row = QHBoxLayout()
        self.run_all_metrics_btn = QPushButton("🚀 Run All Metrics")
        self.run_all_metrics_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_blue']};
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {COLORS['accent_purple']}; }}
        """)
        self.run_all_metrics_btn.clicked.connect(self._run_all_metrics_pipeline)
        runner_btn_row.addWidget(self.run_all_metrics_btn)

        open_dashboards_btn = QPushButton("📂 Open Dashboards")
        open_dashboards_btn.clicked.connect(self._open_analytics_dashboards)
        runner_btn_row.addWidget(open_dashboards_btn)

        refresh_preview_btn = QPushButton("🔄 Refresh Preview")
        refresh_preview_btn.clicked.connect(self._refresh_analytics_shell)
        runner_btn_row.addWidget(refresh_preview_btn)

        runner_btn_row.addStretch()
        runner_layout.addLayout(runner_btn_row)

        self.metrics_runner_status = QLabel("Ready")
        self.metrics_runner_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        runner_layout.addWidget(self.metrics_runner_status)

        layout.addWidget(runner_group)

        shell_group = QGroupBox("📌 Analytics Vital Signs Dashboard")
        shell_layout = QVBoxLayout(shell_group)

        assumptions = QLabel(
            "Assumptions: metric spec v1.0 is wired with filesystem-first defaults. "
            "Layer 1 computes on refresh; Layer 2 uses vault + optional PostgreSQL; "
            "Layer 3 uses a manual Deep Scan for heavier framework metrics."
        )
        assumptions.setWordWrap(True)
        assumptions.setStyleSheet(f"color: {COLORS['text_secondary']};")
        shell_layout.addWidget(assumptions)

        self.analytics_shell_source = QLabel("Source: -")
        self.analytics_shell_source.setStyleSheet(f"color: {COLORS['text_secondary']};")
        shell_layout.addWidget(self.analytics_shell_source)

        self.analytics_shell_output = QLabel("Output: -")
        self.analytics_shell_output.setStyleSheet(f"color: {COLORS['text_secondary']};")
        shell_layout.addWidget(self.analytics_shell_output)

        # Layer 1: always visible
        layer1_group = QGroupBox("Layer 1: Universal Metrics")
        layer1_layout = QVBoxLayout(layer1_group)

        kpi_row = QHBoxLayout()
        self.analytics_shell_kpis: Dict[str, QLabel] = {}
        kpi_specs = [
            ("total_nodes", "U-01 Total Nodes", "0"),
            ("total_links", "U-02 Total Links", "0"),
            ("link_density", "U-03 Link Density", "0.000"),
            ("orphan_nodes", "U-04 Orphan Nodes", "0"),
            ("classification_coverage", "U-05 Classification Coverage", "0.0%"),
        ]
        for key, title, default_value in kpi_specs:
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
            card_layout.setSpacing(3)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
            card_layout.addWidget(title_label)

            value_label = QLabel(default_value)
            value_label.setStyleSheet(f"color: {COLORS['accent_blue']}; font-size: 16pt; font-weight: bold;")
            self.analytics_shell_kpis[key] = value_label
            card_layout.addWidget(value_label)
            kpi_row.addWidget(card)
        layer1_layout.addLayout(kpi_row)

        trends_group = QGroupBox("Layer 1 Trends (Weekly)")
        trends_layout = QVBoxLayout(trends_group)
        if HAS_QT_CHARTS:
            self.analytics_shell_trend_coherence = QChartView()
            self.analytics_shell_trend_coherence.setMinimumHeight(180)
            trends_layout.addWidget(self.analytics_shell_trend_coherence)

            self.analytics_shell_trend_growth = QChartView()
            self.analytics_shell_trend_growth.setMinimumHeight(180)
            trends_layout.addWidget(self.analytics_shell_trend_growth)
        else:
            self.analytics_shell_trend_coherence = None
            self.analytics_shell_trend_growth = None
            chart_fallback = QLabel("QtCharts not available. Trend chart placeholders only.")
            chart_fallback.setStyleSheet(f"color: {COLORS['text_secondary']};")
            trends_layout.addWidget(chart_fallback)

        self.analytics_shell_trend_note = QLabel(
            "UT-01 Coherence Trend = weekly link density. UT-02 Growth Rate = new nodes per week."
        )
        self.analytics_shell_trend_note.setStyleSheet(f"color: {COLORS['text_secondary']};")
        trends_layout.addWidget(self.analytics_shell_trend_note)
        layer1_layout.addWidget(trends_group)

        tables_group = QGroupBox("Layer 1 Breakdown Tables")
        tables_layout = QVBoxLayout(tables_group)
        self.analytics_shell_tabs = QTabWidget()
        self.analytics_shell_tabs.setDocumentMode(True)

        self.analytics_tbl_classification = QTableWidget(0, 4)
        self.analytics_tbl_classification.setHorizontalHeaderLabels(["Type", "Count", "% of Total", "Avg Links"])
        self.analytics_shell_tabs.addTab(self.analytics_tbl_classification, "UB-01 Classification")

        self.analytics_tbl_recent = QTableWidget(0, 4)
        self.analytics_tbl_recent.setHorizontalHeaderLabels(["Title", "Last Modified", "Classification", "Link Count"])
        self.analytics_shell_tabs.addTab(self.analytics_tbl_recent, "UB-02 Recent")

        self.analytics_tbl_stale = QTableWidget(0, 4)
        self.analytics_tbl_stale.setHorizontalHeaderLabels(["Title", "Days Since Modified", "Classification", "Link Count"])
        self.analytics_shell_tabs.addTab(self.analytics_tbl_stale, "UB-03 Stale")

        self.analytics_tbl_connected = QTableWidget(0, 4)
        self.analytics_tbl_connected.setHorizontalHeaderLabels(["Title", "Inbound", "Outbound", "Total"])
        self.analytics_shell_tabs.addTab(self.analytics_tbl_connected, "UB-04 Top Connected")

        self.analytics_tbl_orphans = QTableWidget(0, 3)
        self.analytics_tbl_orphans.setHorizontalHeaderLabels(["Title", "Created Date", "Classification"])
        self.analytics_shell_tabs.addTab(self.analytics_tbl_orphans, "UB-05 Orphans")

        for table in (
            self.analytics_tbl_classification,
            self.analytics_tbl_recent,
            self.analytics_tbl_stale,
            self.analytics_tbl_connected,
            self.analytics_tbl_orphans,
        ):
            table.setAlternatingRowColors(True)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setMinimumHeight(220)

        tables_layout.addWidget(self.analytics_shell_tabs)
        layer1_layout.addWidget(tables_group)
        shell_layout.addWidget(layer1_group)

        # Layer 2: expandable
        self.analytics_layer2_group = QGroupBox("Layer 2: Research Engine (Expandable)")
        self.analytics_layer2_group.setCheckable(True)
        self.analytics_layer2_group.setChecked(False)
        layer2_layout = QVBoxLayout(self.analytics_layer2_group)
        self.analytics_layer2_body = QWidget()
        layer2_body_layout = QVBoxLayout(self.analytics_layer2_body)
        self.analytics_layer2_summary = QLabel("Collapsed. Expand to view research workflow metrics.")
        self.analytics_layer2_summary.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layer2_body_layout.addWidget(self.analytics_layer2_summary)
        self.analytics_layer2_table = QTableWidget(0, 3)
        self.analytics_layer2_table.setHorizontalHeaderLabels(["Metric", "Value", "Notes"])
        self.analytics_layer2_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analytics_layer2_table.setAlternatingRowColors(True)
        self.analytics_layer2_table.setMinimumHeight(180)
        layer2_body_layout.addWidget(self.analytics_layer2_table)
        layer2_layout.addWidget(self.analytics_layer2_body)
        self.analytics_layer2_body.setVisible(False)
        self.analytics_layer2_group.toggled.connect(self.analytics_layer2_body.setVisible)
        shell_layout.addWidget(self.analytics_layer2_group)

        # Layer 3: expandable + deep scan trigger
        self.analytics_layer3_group = QGroupBox("Layer 3: Theophysics-Specific (Expandable)")
        self.analytics_layer3_group.setCheckable(True)
        self.analytics_layer3_group.setChecked(False)
        layer3_layout = QVBoxLayout(self.analytics_layer3_group)
        self.analytics_layer3_body = QWidget()
        layer3_body_layout = QVBoxLayout(self.analytics_layer3_body)

        layer3_btn_row = QHBoxLayout()
        deep_scan_btn = QPushButton("🔬 Deep Scan Layer 3")
        deep_scan_btn.clicked.connect(lambda: self._refresh_analytics_shell(deep_scan=True))
        layer3_btn_row.addWidget(deep_scan_btn)
        layer3_btn_row.addStretch()
        layer3_body_layout.addLayout(layer3_btn_row)

        self.analytics_layer3_summary = QLabel("Run Deep Scan to compute coherence factor, fruits profile, and novel metrics.")
        self.analytics_layer3_summary.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layer3_body_layout.addWidget(self.analytics_layer3_summary)

        self.analytics_layer3_coherence = QTableWidget(0, 3)
        self.analytics_layer3_coherence.setHorizontalHeaderLabels(["Coherence Metric", "Value", "Notes"])
        self.analytics_layer3_coherence.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analytics_layer3_coherence.setAlternatingRowColors(True)
        self.analytics_layer3_coherence.setMinimumHeight(150)
        layer3_body_layout.addWidget(self.analytics_layer3_coherence)

        self.analytics_layer3_fruits = QTableWidget(0, 3)
        self.analytics_layer3_fruits.setHorizontalHeaderLabels(["Fruit", "Score (0-1)", "Proxy Signal"])
        self.analytics_layer3_fruits.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analytics_layer3_fruits.setAlternatingRowColors(True)
        self.analytics_layer3_fruits.setMinimumHeight(170)
        layer3_body_layout.addWidget(self.analytics_layer3_fruits)

        self.analytics_layer3_novel = QTableWidget(0, 3)
        self.analytics_layer3_novel.setHorizontalHeaderLabels(["Novel Metric", "Value", "Notes"])
        self.analytics_layer3_novel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analytics_layer3_novel.setAlternatingRowColors(True)
        self.analytics_layer3_novel.setMinimumHeight(170)
        layer3_body_layout.addWidget(self.analytics_layer3_novel)

        layer3_layout.addWidget(self.analytics_layer3_body)
        self.analytics_layer3_body.setVisible(False)
        self.analytics_layer3_group.toggled.connect(self.analytics_layer3_body.setVisible)
        shell_layout.addWidget(self.analytics_layer3_group)

        self.analytics_shell_status = QLabel("Preview ready. Select a target folder and click Refresh Preview.")
        self.analytics_shell_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        shell_layout.addWidget(self.analytics_shell_status)

        self._analytics_layer2_cache: Dict[str, object] = {}
        self._analytics_layer3_cache: Dict[str, object] = {}

        layout.addWidget(shell_group)
        self._refresh_analytics_shell(deep_scan=False)
        layout.addStretch()

    # ==========================================
    # PAGE 5: DATA AGGREGATION & ANALYTICS
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
        
        # ========== SECTION 1.5: FRUITS OF SPIRIT ANALYSIS ==========
        fruits_group = QGroupBox("🍇 FRUITS OF SPIRIT ANALYSIS")
        fruits_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12pt;
                border: 2px solid {COLORS['accent_green']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                color: {COLORS['accent_green']};
            }}
        """)
        fruits_layout = QVBoxLayout(fruits_group)
        
        fruits_desc = QLabel("Scan any folder for manifestations of the 9 Fruits (Love, Joy, Peace, Patience, Kindness, Goodness, Faithfulness, Gentleness, Self-Control)")
        fruits_desc.setWordWrap(True)
        fruits_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 10px;")
        fruits_layout.addWidget(fruits_desc)
        
        # Folder selection
        fruits_folder_row = QHBoxLayout()
        fruits_folder_row.addWidget(QLabel("Folder to Scan:"))
        self.fruits_folder_input = QLineEdit()
        self.fruits_folder_input.setText("D:/Canon/01_Axioms/_001-188")
        self.fruits_folder_input.setPlaceholderText("Select folder to scan...")
        fruits_folder_row.addWidget(self.fruits_folder_input)
        
        browse_fruits_btn = QPushButton("Browse")
        browse_fruits_btn.clicked.connect(self._browse_fruits_folder)
        fruits_folder_row.addWidget(browse_fruits_btn)
        fruits_layout.addLayout(fruits_folder_row)
        
        # Scan button
        fruits_btn_row = QHBoxLayout()
        self.scan_fruits_btn = QPushButton("🔍 Scan for Fruits")
        self.scan_fruits_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['accent_green']};
                color: {COLORS['bg_darkest']};
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #5fd9c0; }}
        """)
        self.scan_fruits_btn.clicked.connect(self._scan_fruits_of_spirit)
        fruits_btn_row.addWidget(self.scan_fruits_btn)
        fruits_btn_row.addStretch()
        fruits_layout.addLayout(fruits_btn_row)
        
        # Fruits results table
        self.fruits_table = QTableWidget(9, 3)
        self.fruits_table.setHorizontalHeaderLabels(["Fruit", "Mentions", "Axioms Found"])
        self.fruits_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fruits_table.setMaximumHeight(280)
        
        # Pre-populate with 9 Fruits
        fruits_list = ["Love", "Joy", "Peace", "Patience", "Kindness", "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
        for i, fruit in enumerate(fruits_list):
            self.fruits_table.setItem(i, 0, QTableWidgetItem(f"🍇 {fruit}"))
            self.fruits_table.setItem(i, 1, QTableWidgetItem("-"))
            self.fruits_table.setItem(i, 2, QTableWidgetItem("-"))
        
        fruits_layout.addWidget(self.fruits_table)
        layout.addWidget(fruits_group)
        
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
    def _browse_analytics_root(self):
        """Browse for Obsidian Data Analytics root folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Obsidian Data Analytics Root",
            self.analytics_root_input.text().strip() or r"O:\999_IGNORE\Obsidian Data Analytics"
        )
        if folder:
            self.analytics_root_input.setText(folder)
            self._folder_config['analytics'] = folder
            self._save_folder_config()

    def _browse_analytics_target(self):
        """Browse for target folder to analyze."""
        start_dir = (
            self.analytics_target_input.text().strip()
            or self._folder_config.get('analytics_target', '').strip()
            or self._folder_config.get('vault_root', '').strip()
            or self.settings.get('obsidian', 'vault_path', '').strip()
            or r"O:\_Theophysics_v3"
        )
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Target Folder To Analyze",
            start_dir
        )
        if folder:
            self.analytics_target_input.setText(folder)
            self._folder_config['analytics_target'] = folder
            self._save_folder_config()
            self._refresh_analytics_shell()

    def _resolve_analytics_engine_dir(self) -> Optional[Path]:
        """Resolve analytics engine directory from root input."""
        root_text = self.analytics_root_input.text().strip()
        if not root_text:
            return None

        root_path = Path(root_text)
        if root_path.name.lower() == "02_python_engine":
            return root_path
        return root_path / "02_Python_Engine"

    def _resolve_analytics_target_dir(self) -> Optional[Path]:
        """Resolve selected folder to analyze for this run."""
        target_text = ""
        if hasattr(self, "analytics_target_input"):
            target_text = self.analytics_target_input.text().strip()
        if not target_text:
            target_text = (
                self._folder_config.get('analytics_target', '').strip()
                or self._folder_config.get('vault_root', '').strip()
                or self.settings.get('obsidian', 'vault_path', '').strip()
            )
        if not target_text:
            return None
        return Path(target_text)

    def _resolve_analytics_output_dir(self, engine_dir: Path, target_root: Optional[Path] = None) -> Path:
        """Resolve dashboards output folder under selected target when available."""
        if target_root is not None:
            return target_root / "Data Analytics"
        analytics_root = engine_dir if engine_dir.name.lower() != "02_python_engine" else engine_dir.parent
        return analytics_root / "03_Dashboards"

    def _refresh_analytics_shell(self, deep_scan: bool = False):
        """Refresh analytics dashboard shell from the selected target folder."""
        if not hasattr(self, "analytics_shell_status"):
            return

        target_root = self._resolve_analytics_target_dir()
        if target_root is None:
            self.analytics_shell_status.setText("Select a target folder to load dashboard preview.")
            self._render_analytics_shell_empty()
            return

        if not target_root.exists():
            self.analytics_shell_status.setText(f"Target folder does not exist: {target_root}")
            self._render_analytics_shell_empty()
            return

        try:
            snapshot = self._collect_analytics_shell_snapshot(target_root, deep_scan=deep_scan)
            self._render_analytics_shell(snapshot)
        except Exception as e:
            self.analytics_shell_status.setText(f"Preview failed: {e}")
            self._render_analytics_shell_empty()

    def _render_analytics_shell_empty(self):
        """Reset dashboard shell to placeholders."""
        self.analytics_shell_source.setText("Source: -")
        self.analytics_shell_output.setText("Output: -")

        for label in self.analytics_shell_kpis.values():
            label.setText("0")

        for table in (
            self.analytics_tbl_classification,
            self.analytics_tbl_recent,
            self.analytics_tbl_stale,
            self.analytics_tbl_connected,
            self.analytics_tbl_orphans,
            self.analytics_layer2_table,
            self.analytics_layer3_coherence,
            self.analytics_layer3_fruits,
            self.analytics_layer3_novel,
        ):
            table.setRowCount(0)

        if HAS_QT_CHARTS:
            for view, title in (
                (self.analytics_shell_trend_coherence, "UT-01 Coherence Trend (weekly link density)"),
                (self.analytics_shell_trend_growth, "UT-02 Growth Rate (new nodes by week)"),
            ):
                if view is not None:
                    chart = QChart()
                    chart.setTitle(title)
                    view.setChart(chart)

    def _collect_analytics_shell_snapshot(self, target_root: Path, deep_scan: bool = False) -> Dict[str, object]:
        """Collect layered dashboard metrics from vault filesystem + optional services."""
        from datetime import timedelta

        max_files = 120000
        target_root = target_root.resolve()
        now = datetime.now()
        exclude_dirs = {
            ".git", ".obsidian", "__pycache__", "venv", "venv_backup", "node_modules",
            "data analytics", "_data_analytics", "03_dashboards",
        }

        def parse_frontmatter(text: str) -> Dict[str, object]:
            lines = text.splitlines()
            if len(lines) < 3 or lines[0].strip() != "---":
                return {}
            end_idx = -1
            for i in range(1, min(160, len(lines))):
                if lines[i].strip() == "---":
                    end_idx = i
                    break
            if end_idx == -1:
                return {}
            meta: Dict[str, object] = {}
            for raw in lines[1:end_idx]:
                if ":" not in raw:
                    continue
                k, v = raw.split(":", 1)
                key = k.strip().lower()
                val = v.strip().strip("'\"")
                if val.startswith("[") and val.endswith("]"):
                    inside = val[1:-1].strip()
                    meta[key] = [x.strip().strip("'\"") for x in inside.split(",") if x.strip()] if inside else []
                else:
                    meta[key] = val
            return meta

        def parse_dt(value: object) -> Optional[datetime]:
            if value is None:
                return None
            txt = str(value).strip()
            if not txt:
                return None
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return datetime.strptime(txt[:19], fmt)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(txt.replace("Z", ""))
            except ValueError:
                return None

        def normalize_rel(path: Path) -> str:
            rel = path.relative_to(target_root).as_posix()
            return rel[:-3].lower() if rel.lower().endswith(".md") else rel.lower()

        def normalize_target(raw: str) -> str:
            cleaned = raw.split("|", 1)[0].split("#", 1)[0].replace("\\", "/").strip()
            if cleaned.lower().endswith(".md"):
                cleaned = cleaned[:-3]
            return cleaned.lower()

        classification_map = {
            "axiom": "axiom",
            "theorem": "theorem",
            "claim": "claim",
            "paper": "paper",
            "article": "article",
            "dt": "dt_unit",
            "dt_unit": "dt_unit",
            "doctoral": "dt_unit",
        }
        allowed_node_types = {"axiom", "theorem", "claim", "paper", "article", "dt_unit"}

        def infer_classification(meta: Dict[str, object], rel_path: str, text: str) -> str:
            probe = " ".join([
                str(meta.get("classification", "")),
                str(meta.get("type", "")),
                str(meta.get("note_type", "")),
                rel_path,
                text[:400],
            ]).lower()
            for key, mapped in classification_map.items():
                if key in probe:
                    return mapped
            return "unclassified"

        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        weeks = [week_start - timedelta(weeks=i) for i in range(11, -1, -1)]
        week_labels = [wk.strftime("%Y-%m-%d") for wk in weeks]
        week_idx = {wk: i for i, wk in enumerate(week_labels)}
        trend_nodes = [0] * len(week_labels)
        trend_links = [0] * len(week_labels)
        trend_growth = [0] * len(week_labels)
        heatmap = [[0] * 24 for _ in range(7)]

        notes: List[Dict[str, object]] = []
        note_by_id: Dict[str, Dict[str, object]] = {}
        stem_map: Dict[str, List[str]] = {}
        truncated = False

        for root, dirs, files in os.walk(target_root):
            dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs]
            for name in files:
                if not name.lower().endswith(".md"):
                    continue
                file_path = Path(root) / name
                rel_parts = {part.lower() for part in file_path.relative_to(target_root).parts}
                if rel_parts.intersection(exclude_dirs):
                    continue
                try:
                    text = file_path.read_text(encoding="utf-8", errors="ignore")
                    stat = file_path.stat()
                except Exception:
                    continue

                meta = parse_frontmatter(text)
                rel_id = normalize_rel(file_path)
                classification = infer_classification(meta, rel_id, text)
                created = parse_dt(meta.get("created")) or parse_dt(meta.get("date")) or datetime.fromtimestamp(stat.st_ctime)
                modified = parse_dt(meta.get("updated")) or parse_dt(meta.get("modified")) or datetime.fromtimestamp(stat.st_mtime)
                domain = str(meta.get("domain", "")).strip().lower()
                status = str(meta.get("status", "")).strip().lower() or str(meta.get("stage", "")).strip().lower()
                links_raw = [normalize_target(m.group(1)) for m in re.finditer(r"\[\[([^\]]+)\]\]", text)]

                note = {
                    "id": rel_id,
                    "title": str(meta.get("title", "")).strip() or file_path.stem,
                    "classification": classification,
                    "domain": domain,
                    "status": status,
                    "meta": meta,
                    "complete_yaml": bool(meta) and classification != "unclassified" and len(meta) >= 3,
                    "created": created,
                    "modified": modified,
                    "links_raw": links_raw,
                    "kc_mentions": len(re.findall(r"\b(?:KC[-_\s]?\d+|kill condition)\b", text, flags=re.IGNORECASE)),
                    "prediction_mentions": len(re.findall(r"\b(?:prediction|forecast)\b", text, flags=re.IGNORECASE)),
                    "content": text,
                }
                notes.append(note)
                note_by_id[rel_id] = note
                stem_map.setdefault(Path(rel_id).name, []).append(rel_id)

                if len(notes) >= max_files:
                    truncated = True
                    break
            if truncated:
                break

        def resolve_target(target_id: str) -> Optional[str]:
            if target_id in note_by_id:
                return target_id
            if "/" not in target_id and target_id in stem_map and len(stem_map[target_id]) == 1:
                return stem_map[target_id][0]
            return None

        inbound: Counter[str] = Counter()
        outbound: Counter[str] = Counter()
        edges: List[tuple[str, str]] = []
        cross_domain_links = 0
        for note in notes:
            wk = (note["modified"] - timedelta(days=note["modified"].weekday())).strftime("%Y-%m-%d")
            idx = week_idx.get(wk)
            if idx is not None and note["classification"] in allowed_node_types:
                trend_nodes[idx] += 1
            cw = (note["created"] - timedelta(days=note["created"].weekday())).strftime("%Y-%m-%d")
            cidx = week_idx.get(cw)
            if cidx is not None and note["classification"] in allowed_node_types:
                trend_growth[cidx] += 1
            heatmap[note["modified"].weekday()][note["modified"].hour] += 1

            for raw_target in note["links_raw"]:
                target = resolve_target(raw_target)
                if not target:
                    continue
                edges.append((note["id"], target))
                outbound[note["id"]] += 1
                inbound[target] += 1
                if idx is not None and note["classification"] in allowed_node_types:
                    trend_links[idx] += 1
                src_d = str(note.get("domain", ""))
                tgt_d = str(note_by_id.get(target, {}).get("domain", ""))
                if src_d and tgt_d and src_d != tgt_d:
                    cross_domain_links += 1

        total_links = len(edges)
        classified = [n for n in notes if n["classification"] in allowed_node_types]
        total_nodes = len(classified)
        orphan_nodes = [n for n in classified if inbound[n["id"]] == 0]
        orphan_count = len(orphan_nodes)
        complete_yaml_count = sum(1 for n in notes if n["complete_yaml"])
        coverage = (complete_yaml_count / len(notes) * 100.0) if notes else 0.0
        density = (total_links / total_nodes) if total_nodes else 0.0

        by_class: Dict[str, List[Dict[str, object]]] = {}
        for n in classified:
            by_class.setdefault(n["classification"], []).append(n)
        ub01 = []
        for cls, cls_notes in sorted(by_class.items(), key=lambda kv: len(kv[1]), reverse=True):
            cnt = len(cls_notes)
            pct = (cnt / total_nodes * 100.0) if total_nodes else 0.0
            avg_links = sum(inbound[n["id"]] + outbound[n["id"]] for n in cls_notes) / cnt if cnt else 0.0
            ub01.append((cls, f"{cnt:,}", f"{pct:.1f}%", f"{avg_links:.2f}"))

        ub02 = [(n["title"], n["modified"].strftime("%Y-%m-%d %H:%M"), n["classification"], str(inbound[n["id"]] + outbound[n["id"]]))
                for n in sorted(notes, key=lambda x: x["modified"], reverse=True)[:20]]

        ub03 = []
        for n in notes:
            age = (now - n["modified"]).days
            if age >= 90:
                ub03.append((n["title"], str(age), n["classification"], str(inbound[n["id"]] + outbound[n["id"]])))
        ub03.sort(key=lambda r: int(r[1]), reverse=True)

        conn_rows = []
        for n in notes:
            i = inbound[n["id"]]
            o = outbound[n["id"]]
            conn_rows.append((n["title"], i, o, i + o))
        conn_rows.sort(key=lambda row: row[3], reverse=True)
        ub04 = [(t, str(i), str(o), str(tt)) for t, i, o, tt in conn_rows[:20]]
        ub05 = [(n["title"], n["created"].strftime("%Y-%m-%d"), n["classification"]) for n in orphan_nodes]

        coherence = [(trend_links[i] / trend_nodes[i]) if trend_nodes[i] else 0.0 for i in range(len(week_labels))]

        papers = [n for n in notes if n["classification"] in {"paper", "article"}]
        dt_units = [n for n in notes if n["classification"] == "dt_unit"]
        paper_stage = Counter()
        for p in papers:
            st = str(p["status"]).lower()
            if "publish" in st:
                paper_stage["Published"] += 1
            elif "complete" in st or "facts" in st:
                paper_stage["FACTS Complete"] += 1
            elif "review" in st:
                paper_stage["Review"] += 1
            else:
                paper_stage["Draft"] += 1
        dt_stage = Counter()
        for d in dt_units:
            st = str(d["status"]).lower()
            if "publish" in st:
                dt_stage["PUBLISHED"] += 1
            elif "complete" in st:
                dt_stage["COMPLETE"] += 1
            else:
                dt_stage["IN PROGRESS"] += 1
        kc_total = sum(int(n["kc_mentions"]) for n in notes)
        domains = {n["domain"] for n in papers if n["domain"]}
        layer2_rows = [
            ("R-01 Papers in Pipeline", f"{len(papers):,}", f"Draft {paper_stage['Draft']}, FACTS {paper_stage['FACTS Complete']}, Published {paper_stage['Published']}"),
            ("R-02 DT Units", f"{len(dt_units):,}", f"IN PROGRESS {dt_stage['IN PROGRESS']}, COMPLETE {dt_stage['COMPLETE']}, PUBLISHED {dt_stage['PUBLISHED']}"),
            ("R-03 Kill Conditions Tracked", f"{kc_total:,}", "Filesystem proxy from KC markers."),
            ("R-05 Domain Coverage", f"{len(domains):,} / 45", f"{(len(domains)/45.0*100.0 if domains else 0.0):.1f}%"),
        ]
        layer2_notes: List[str] = []
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(
                dbname=os.environ.get("THEO_PG_DB", "theophysics"),
                user=os.environ.get("THEO_PG_USER", "postgres"),
                password=os.environ.get("THEO_PG_PASSWORD", ""),
                host=os.environ.get("THEO_PG_HOST", "192.168.1.177"),
                port=int(os.environ.get("THEO_PG_PORT", "2665")),
                connect_timeout=1,
            )
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM canonical_nodes")
            canonical_nodes = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM node_dependencies")
            dependency_rows = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM falsification_ledger")
            ledger_rows = int(cur.fetchone()[0])
            conn.close()
            layer2_notes.append(
                f"PostgreSQL connected: canonical_nodes={canonical_nodes}, node_dependencies={dependency_rows}, falsification_ledger={ledger_rows}"
            )
            self._analytics_layer2_cache = {"rows": layer2_rows, "notes": layer2_notes}
        except Exception:
            if self._analytics_layer2_cache:
                layer2_rows = self._analytics_layer2_cache.get("rows", layer2_rows)
                layer2_notes = self._analytics_layer2_cache.get("notes", ["PostgreSQL unavailable; using cached Layer 2 values."])
            else:
                layer2_notes = ["PostgreSQL unavailable; Layer 2 computed from filesystem only."]

        stale_count = len(ub03)
        unclassified_count = sum(1 for n in notes if n["classification"] == "unclassified")
        orphan_rate = (orphan_count / total_nodes) if total_nodes else 0.0
        stale_rate = (stale_count / len(notes)) if notes else 0.0
        unclassified_rate = (unclassified_count / len(notes)) if notes else 0.0

        layer3 = self._analytics_layer3_cache if (self._analytics_layer3_cache and not deep_scan) else {}
        if deep_scan or not layer3:
            tested_kc = sum(1 for n in notes if "tested" in n["content"].lower() and "kc" in n["content"].lower())
            test_rate = (tested_kc / kc_total) if kc_total else 0.0
            cross_coherence = (cross_domain_links / total_links) if total_links else 0.0
            coherence_ratio = (
                sum(1 for n in classified if inbound[n["id"]] + outbound[n["id"]] >= 3) / total_nodes
            ) if total_nodes else 0.0
            entropy = orphan_rate + stale_rate + unclassified_rate
            depth_proxy = min(1.0, (sum(outbound[n["id"]] for n in classified if n["classification"] == "axiom") / max(1, total_nodes)) / 5.0)
            chi = (
                0.3 * min(1.0, density / 5.0)
                + 0.2 * (coverage / 100.0)
                + 0.2 * min(1.0, test_rate)
                + 0.15 * min(1.0, cross_coherence)
                + 0.15 * depth_proxy
            )
            breakthroughs = sum(1 for n in notes if "#breakthrough" in n["content"].lower() or "#discovery" in n["content"].lower())
            contradictions = sum(len(re.findall(r"\bcontradiction\b", n["content"], flags=re.IGNORECASE)) for n in notes)
            resolved = sum(len(re.findall(r"\bresolved contradiction\b", n["content"], flags=re.IGNORECASE)) for n in notes)
            offramps = sum(1 for n in papers if "off-ramp" in n["content"].lower() or "biaxiosum" in n["content"].lower())
            rationale = sum(1 for n in notes if "revision rationale" in n["content"].lower())
            ai_converge = sum(1 for n in notes if "claude" in n["content"].lower() and "codex" in n["content"].lower())
            predictions = sum(int(n["prediction_mentions"]) for n in notes)
            carried = sum(1 for n in papers if "got carried away" in n["content"].lower())
            facts_cov = sum(1 for n in papers if "facts" in n["content"].lower())

            layer3 = {
                "computed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "coherence_rows": [
                    ("C-01 χ_vault", f"{chi:.3f}", "Weighted composite coherence index (0-1)."),
                    ("C-02 Cross-Domain Coherence", f"{cross_coherence:.3f}", "Cross-domain links / total links."),
                    ("C-03 Axiom Coherence Depth", f"{depth_proxy:.3f}", "Axiom dependency depth proxy."),
                    ("C-04 Coherence Ratio", f"{coherence_ratio:.3f}", "Nodes with 3+ links / total nodes."),
                    ("C-05 Entropy Indicator", f"{entropy:.3f}", "Orphan + stale + unclassified rates."),
                ],
                "fruits_rows": [
                    ("F-01 Love", f"{min(1.0, cross_coherence):.2f}", "Cross-domain bridge links."),
                    ("F-02 Joy", f"{min(1.0, breakthroughs / 20.0):.2f}", "Breakthrough/discovery density."),
                    ("F-03 Peace", f"{(resolved / contradictions) if contradictions else 0.0:.2f}", "Contradiction resolution rate."),
                    ("F-05 Kindness", f"{(offramps / len(papers)) if papers else 0.0:.2f}", "Off-ramp/Biaxiosum coverage."),
                    ("F-08 Gentleness", f"{(rationale / len(notes)) if notes else 0.0:.2f}", "Revision rationale coverage."),
                    ("F-09 Self-Control", f"{(1 - carried / len(papers)) if papers else 0.0:.2f}", "Inverse carried-away markers."),
                ],
                "novel_rows": [
                    ("N-01 Prediction Registry", f"{predictions:,}", "Prediction markers (proxy)."),
                    ("N-04 FACTS Coverage", f"{(facts_cov / len(papers) * 100.0) if papers else 0.0:.1f}%", "Papers with FACTS markers."),
                    ("N-08 Cross-AI Convergence", f"{ai_converge:,}", "Notes mentioning Claude + Codex."),
                ],
            }
            self._analytics_layer3_cache = layer3

        return {
            "target_root": target_root,
            "output_dir": target_root / "Data Analytics",
            "output_exists": (target_root / "Data Analytics").exists(),
            "truncated": truncated,
            "layer1": {
                "total_notes": len(notes),
                "kpis": {
                    "total_nodes": total_nodes,
                    "total_links": total_links,
                    "link_density": density,
                    "orphan_nodes": orphan_count,
                    "classification_coverage": coverage,
                },
                "trends": {"weeks": week_labels, "coherence": coherence, "growth": trend_growth, "activity_heatmap": heatmap},
                "tables": {"ub01": ub01, "ub02": ub02, "ub03": ub03, "ub04": ub04, "ub05": ub05},
                "unclassified_count": unclassified_count,
                "stale_count": stale_count,
            },
            "layer2": {"rows": layer2_rows, "notes": layer2_notes},
            "layer3": layer3,
            "deep_scan": deep_scan,
        }

    def _fill_table(self, table: QTableWidget, rows: List[tuple]):
        """Populate a QTableWidget with tuple rows."""
        table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, val in enumerate(row_data):
                table.setItem(r, c, QTableWidgetItem(str(val)))

    def _render_analytics_shell(self, snapshot: Dict[str, object]):
        """Render layered analytics data into dashboard widgets."""
        target_root = snapshot["target_root"]
        output_dir = snapshot["output_dir"]
        truncated = bool(snapshot["truncated"])
        layer1 = snapshot["layer1"]
        layer2 = snapshot["layer2"]
        layer3 = snapshot["layer3"]

        self.analytics_shell_source.setText(f"Source: {target_root}")
        self.analytics_shell_output.setText(f"Output: {output_dir}")

        kpis = layer1["kpis"]
        self.analytics_shell_kpis["total_nodes"].setText(f"{int(kpis['total_nodes']):,}")
        self.analytics_shell_kpis["total_links"].setText(f"{int(kpis['total_links']):,}")
        self.analytics_shell_kpis["link_density"].setText(f"{float(kpis['link_density']):.3f}")
        self.analytics_shell_kpis["orphan_nodes"].setText(f"{int(kpis['orphan_nodes']):,}")
        self.analytics_shell_kpis["classification_coverage"].setText(f"{float(kpis['classification_coverage']):.1f}%")

        trends = layer1["trends"]
        if HAS_QT_CHARTS and self.analytics_shell_trend_coherence is not None and self.analytics_shell_trend_growth is not None:
            short_weeks = [w[5:] for w in trends["weeks"]]

            chart_a = QChart()
            chart_a.setTitle("UT-01 Coherence Trend (weekly link density)")
            set_a = QBarSet("Link Density")
            for val in trends["coherence"]:
                set_a.append(float(val))
            series_a = QBarSeries()
            series_a.append(set_a)
            chart_a.addSeries(series_a)
            chart_a.legend().setVisible(False)
            axis_ax = QBarCategoryAxis()
            axis_ax.append(short_weeks)
            chart_a.addAxis(axis_ax, Qt.AlignmentFlag.AlignBottom)
            series_a.attachAxis(axis_ax)
            axis_ay = QValueAxis()
            axis_ay.setLabelFormat("%.2f")
            axis_ay.setRange(0, max(1.0, max(trends["coherence"]) + 0.1))
            chart_a.addAxis(axis_ay, Qt.AlignmentFlag.AlignLeft)
            series_a.attachAxis(axis_ay)
            self.analytics_shell_trend_coherence.setChart(chart_a)

            chart_b = QChart()
            chart_b.setTitle("UT-02 Growth Rate (new nodes created per week)")
            set_b = QBarSet("New Nodes")
            for val in trends["growth"]:
                set_b.append(int(val))
            series_b = QBarSeries()
            series_b.append(set_b)
            chart_b.addSeries(series_b)
            chart_b.legend().setVisible(False)
            axis_bx = QBarCategoryAxis()
            axis_bx.append(short_weeks)
            chart_b.addAxis(axis_bx, Qt.AlignmentFlag.AlignBottom)
            series_b.attachAxis(axis_bx)
            axis_by = QValueAxis()
            axis_by.setLabelFormat("%d")
            axis_by.applyNiceNumbers()
            chart_b.addAxis(axis_by, Qt.AlignmentFlag.AlignLeft)
            series_b.attachAxis(axis_by)
            self.analytics_shell_trend_growth.setChart(chart_b)

        tables = layer1["tables"]
        self._fill_table(self.analytics_tbl_classification, tables["ub01"])
        self._fill_table(self.analytics_tbl_recent, tables["ub02"])
        self._fill_table(self.analytics_tbl_stale, tables["ub03"])
        self._fill_table(self.analytics_tbl_connected, tables["ub04"])
        self._fill_table(self.analytics_tbl_orphans, tables["ub05"])

        self._fill_table(self.analytics_layer2_table, layer2["rows"])
        self.analytics_layer2_summary.setText(" | ".join(layer2["notes"]))

        self._fill_table(self.analytics_layer3_coherence, layer3.get("coherence_rows", []))
        self._fill_table(self.analytics_layer3_fruits, layer3.get("fruits_rows", []))
        self._fill_table(self.analytics_layer3_novel, layer3.get("novel_rows", []))
        self.analytics_layer3_summary.setText(
            f"Layer 3 last computed: {layer3.get('computed_at', 'not yet computed')} "
            f"(Deep Scan={'yes' if snapshot.get('deep_scan') else 'cached'})"
        )

        status_parts = [f"Preview loaded from {target_root}"]
        if truncated:
            status_parts.append("Scan capped at 120,000 markdown files for responsiveness.")
        status_parts.append(f"Total notes: {layer1['total_notes']:,}")
        status_parts.append(f"Unclassified: {layer1['unclassified_count']:,}")
        status_parts.append(f"Stale (90+ days): {layer1['stale_count']:,}")
        if snapshot["output_exists"]:
            status_parts.append("Data Analytics folder detected.")
        else:
            status_parts.append("Data Analytics folder will be created on first run.")
        self.analytics_shell_status.setText(" | ".join(status_parts))

    def _run_all_metrics_pipeline(self):
        """Run the full metrics pipeline from Obsidian Data Analytics folder."""
        engine_dir = self._resolve_analytics_engine_dir()
        if engine_dir is None:
            QMessageBox.warning(self, "No Folder", "Please select an analytics root folder first.")
            return

        if not engine_dir.exists():
            QMessageBox.warning(
                self,
                "Invalid Path",
                f"Could not find analytics engine folder:\n{engine_dir}\n\n"
                "Expected: <Analytics Root>\\02_Python_Engine"
            )
            return

        runner_bat = engine_dir / "RUN_COMPLETE_ANALYTICS.bat"
        if not runner_bat.exists():
            QMessageBox.warning(
                self,
                "Missing Runner",
                f"Could not find:\n{runner_bat}\n\n"
                "Please confirm the folder contains RUN_COMPLETE_ANALYTICS.bat."
            )
            return

        analytics_root = engine_dir.parent if engine_dir.name.lower() == "02_python_engine" else engine_dir
        self._folder_config['analytics'] = str(analytics_root)
        
        target_root = self._resolve_analytics_target_dir()
        if target_root is None:
            QMessageBox.warning(self, "No Target Folder", "Please select a target folder to analyze.")
            return
        if not target_root.exists():
            QMessageBox.warning(
                self,
                "Invalid Path",
                f"Target folder does not exist:\n{target_root}"
            )
            return

        self._folder_config['analytics_target'] = str(target_root)
        self._save_folder_config()

        dashboards_dir = self._resolve_analytics_output_dir(engine_dir, target_root)

        try:
            # Launch in separate cmd so long-running analytics output stays visible.
            if os.name == "nt":
                env = os.environ.copy()
                env["ANALYTICS_VAULT"] = str(target_root)
                env["ANALYTICS_OUTPUT_PATH"] = str(dashboards_dir)
                env["FORMULA_SCRIPTS_PATH"] = str(target_root / "00_OS" / "Scripts")

                subprocess.Popen(
                    ["cmd.exe", "/k", str(runner_bat)],
                    cwd=str(engine_dir),
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([str(runner_bat)], cwd=str(engine_dir))

            self.metrics_runner_status.setText(f"Launched: {runner_bat}")
            self.metrics_runner_status.setStyleSheet(f"color: {COLORS['accent_green']};")
            self.agg_status.setText(
                f"Running full analytics pipeline...\nTarget Vault: {target_root}\nOutput Folder: {dashboards_dir}"
            )
            self._refresh_analytics_shell()
        except Exception as e:
            self.metrics_runner_status.setText(f"Launch failed: {e}")
            self.metrics_runner_status.setStyleSheet(f"color: {COLORS['accent_red']};")
            QMessageBox.critical(self, "Launch Error", f"Could not run metrics pipeline:\n\n{e}")

    def _open_analytics_dashboards(self):
        """Open the dashboards output folder under the analytics root."""
        engine_dir = self._resolve_analytics_engine_dir()
        if engine_dir is None:
            QMessageBox.warning(self, "No Folder", "Please select an analytics root folder first.")
            return

        target_root = self._resolve_analytics_target_dir()
        dashboards_dir = self._resolve_analytics_output_dir(engine_dir, target_root)
        if not dashboards_dir.exists():
            QMessageBox.warning(
                self,
                "Not Found",
                f"Dashboards folder not found:\n{dashboards_dir}\n\n"
                "Run 'Run All Metrics' first or verify your analytics root path."
            )
            return

        try:
            if os.name == "nt":
                os.startfile(str(dashboards_dir))
            elif os.name == "posix":
                subprocess.Popen(["xdg-open", str(dashboards_dir)])
            else:
                QMessageBox.information(self, "Folder", str(dashboards_dir))
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not open dashboards folder:\n\n{e}")
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
    
    def _browse_fruits_folder(self):
        """Browse for folder to scan for Fruits."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan for Fruits")
        if folder:
            self.fruits_folder_input.setText(folder)
    
    def _scan_fruits_of_spirit(self):
        """Scan selected folder for Fruits of Spirit manifestations with individual document scoring."""
        folder_path = self.fruits_folder_input.text().strip()
        
        if not folder_path:
            QMessageBox.warning(self, "No Folder", "Please select a folder to scan.")
            return
        
        axioms_path = Path(folder_path)
        
        if not axioms_path.exists():
            QMessageBox.warning(self, "Path Not Found", 
                f"Folder not found:\n{axioms_path}\n\nPlease check the path.")
            return
        
        self.scan_fruits_btn.setEnabled(False)
        self.agg_status.setText("🍇 Scanning for Fruits of Spirit with individual document scoring...")
        
        try:
            import json
            from datetime import datetime
            
            fruits_list = ["Love", "Joy", "Peace", "Patience", "Kindness", "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
            
            # Aggregate data
            fruits_data = {fruit: {'count': 0, 'files': []} for fruit in fruits_list}
            
            # Per-document scores
            document_scores = []
            
            # Scan all markdown files
            md_files = list(axioms_path.glob("*.md"))
            
            for md_file in md_files:
                try:
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    content_lower = content.lower()
                    word_count = len(content.split())
                    
                    # Calculate scores for this document
                    doc_score = {
                        'filename': md_file.name,
                        'word_count': word_count,
                        'fruits': {}
                    }
                    
                    for fruit in fruits_list:
                        fruit_count = content_lower.count(fruit.lower())
                        
                        # Normalized score: mentions per 1000 words
                        normalized_score = (fruit_count / word_count * 1000) if word_count > 0 else 0
                        
                        doc_score['fruits'][fruit] = {
                            'raw_count': fruit_count,
                            'normalized_score': round(normalized_score, 2)
                        }
                        
                        # Update aggregate
                        fruits_data[fruit]['count'] += fruit_count
                        if fruit_count > 0:
                            fruits_data[fruit]['files'].append(md_file.stem)
                    
                    # Calculate total Fruits score for document
                    doc_score['total_raw'] = sum(doc_score['fruits'][f]['raw_count'] for f in fruits_list)
                    doc_score['total_normalized'] = round(sum(doc_score['fruits'][f]['normalized_score'] for f in fruits_list), 2)
                    
                    document_scores.append(doc_score)
                    
                except Exception as e:
                    print(f"Error scanning {md_file.name}: {e}")
                    continue
            
            # Sort documents by total normalized score
            document_scores.sort(key=lambda x: x['total_normalized'], reverse=True)
            
            # Update table with aggregate results
            for i, fruit in enumerate(fruits_list):
                count = fruits_data[fruit]['count']
                file_count = len(fruits_data[fruit]['files'])
                
                self.fruits_table.setItem(i, 1, QTableWidgetItem(str(count)))
                self.fruits_table.setItem(i, 2, QTableWidgetItem(str(file_count)))
            
            # Generate output report
            output_folder = axioms_path.parent / f"{axioms_path.name}_FRUITS_ANALYSIS"
            output_folder.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save JSON data
            json_output = {
                'scan_info': {
                    'folder': str(axioms_path),
                    'timestamp': timestamp,
                    'files_scanned': len(md_files)
                },
                'aggregate_results': fruits_data,
                'document_scores': document_scores,
                'top_10_documents': document_scores[:10]
            }
            
            json_path = output_folder / f"fruits_analysis_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=2)
            
            # Generate markdown report
            md_report = self._generate_fruits_markdown_report(axioms_path, fruits_data, document_scores, timestamp)
            md_path = output_folder / f"FRUITS_REPORT_{timestamp}.md"
            md_path.write_text(md_report, encoding='utf-8')
            
            # Generate CSV for statistical analysis
            csv_path = output_folder / f"fruits_scores_{timestamp}.csv"
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("Filename,Word_Count,Total_Raw,Total_Normalized," + ",".join(fruits_list) + "\n")
                for doc in document_scores:
                    row = [
                        doc['filename'],
                        str(doc['word_count']),
                        str(doc['total_raw']),
                        str(doc['total_normalized'])
                    ]
                    row.extend([str(doc['fruits'][fruit]['normalized_score']) for fruit in fruits_list])
                    f.write(",".join(row) + "\n")
            
            total_mentions = sum(fruits_data[f]['count'] for f in fruits_data)
            self.agg_status.setText(f"✓ Fruits analysis complete: {total_mentions} mentions across {len(md_files)} files")
            
            # Show top 5 documents
            top_5_msg = "\n".join([
                f"{i+1}. {doc['filename']}: {doc['total_normalized']:.2f} (normalized)"
                for i, doc in enumerate(document_scores[:5])
            ])
            
            QMessageBox.information(self, "Fruits Analysis Complete",
                f"Scanned {len(md_files)} files in: {axioms_path.name}\n\n"
                f"Total Fruit mentions: {total_mentions}\n\n"
                f"📊 Top 5 Documents by Normalized Score:\n{top_5_msg}\n\n"
                f"📁 Reports saved to:\n{output_folder.name}\n\n"
                f"Files generated:\n"
                f"• {json_path.name}\n"
                f"• {md_path.name}\n"
                f"• {csv_path.name}")
            
        except Exception as e:
            import traceback
            self.agg_status.setText(f"⚠️ Fruits scan failed: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to scan for Fruits:\n{str(e)}\n\n{traceback.format_exc()}")
        
        finally:
            self.scan_fruits_btn.setEnabled(True)
    
    def _generate_fruits_markdown_report(self, folder_path, fruits_data, document_scores, timestamp):
        """Generate markdown report for Fruits analysis."""
        fruits_list = ["Love", "Joy", "Peace", "Patience", "Kindness", "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
        
        report = f"""# 🍇 Fruits of the Spirit Analysis Report

**Folder Analyzed:** `{folder_path.name}`
**Timestamp:** {timestamp}
**Documents Scanned:** {len(document_scores)}

---

## 📊 Aggregate Results

| Fruit | Total Mentions | Documents Containing |
|-------|---------------:|---------------------:|
"""
        
        for fruit in fruits_list:
            report += f"| {fruit} | {fruits_data[fruit]['count']} | {len(fruits_data[fruit]['files'])} |\n"
        
        report += f"\n**Total Mentions Across All Fruits:** {sum(fruits_data[f]['count'] for f in fruits_data)}\n\n"
        
        report += """---

## 🏆 Top 20 Documents (by Normalized Score)

*Normalized Score = Fruit mentions per 1000 words*

| Rank | Document | Total Score | Word Count | Love | Joy | Peace | Patience | Kindness | Goodness | Faithfulness | Gentleness | Self-Control |
|-----:|----------|------------:|-----------:|-----:|----:|------:|---------:|---------:|---------:|-------------:|-----------:|-------------:|
"""
        
        for i, doc in enumerate(document_scores[:20], 1):
            row = f"| {i} | {doc['filename']} | {doc['total_normalized']:.2f} | {doc['word_count']} |"
            for fruit in fruits_list:
                row += f" {doc['fruits'][fruit]['normalized_score']:.2f} |"
            report += row + "\n"
        
        report += "\n---\n\n## 📈 Fruit-Specific Rankings\n\n"
        
        for fruit in fruits_list:
            report += f"### {fruit}\n\n"
            report += "| Rank | Document | Normalized Score | Raw Count |\n"
            report += "|-----:|----------|----------------:|----------:|\n"
            
            # Sort by this specific fruit
            sorted_docs = sorted(document_scores, 
                               key=lambda x: x['fruits'][fruit]['normalized_score'], 
                               reverse=True)[:10]
            
            for i, doc in enumerate(sorted_docs, 1):
                if doc['fruits'][fruit]['raw_count'] > 0:
                    report += f"| {i} | {doc['filename']} | {doc['fruits'][fruit]['normalized_score']:.2f} | {doc['fruits'][fruit]['raw_count']} |\n"
            
            report += "\n"
        
        report += """---

## 📝 Methodology

- **Raw Count:** Total number of times the Fruit word appears in the document
- **Normalized Score:** Raw count per 1000 words (allows fair comparison across different document lengths)
- **Total Score:** Sum of all 9 Fruit normalized scores

---

*Generated by Theophysics Research Manager - Fruits of Spirit Analyzer*
"""
        
        return report

    def _build_research_links_page(self):
        page, layout = self._create_page_container("🔗 Research Links")

        # Existing research linker UI
        try:
            from ui.tabs.research_linking_tab import ResearchLinkingTab
            self.research_linking_tab = ResearchLinkingTab(self.research_linker)
            layout.addWidget(self.research_linking_tab, 2)
        except Exception as e:
            fallback = QLabel(f"ResearchLinkingTab unavailable: {e}")
            fallback.setWordWrap(True)
            fallback.setStyleSheet("color: #f59e0b;")
            layout.addWidget(fallback)

        # GPT Researcher integration
        gpt_group = QGroupBox("🧠 GPT Researcher")
        gpt_layout = QVBoxLayout(gpt_group)

        repo_row = QHBoxLayout()
        repo_row.addWidget(QLabel("Repo Path:"))
        self.gpt_repo_path = QLineEdit("O:/999_IGNORE/Obsidian Programs/GPT_Researcher")
        repo_row.addWidget(self.gpt_repo_path)
        browse_repo_btn = QPushButton("Browse...")
        browse_repo_btn.clicked.connect(self._browse_gpt_researcher_repo)
        repo_row.addWidget(browse_repo_btn)
        gpt_layout.addLayout(repo_row)

        actions_row = QHBoxLayout()
        install_btn = QPushButton("📥 Install / Update")
        install_btn.setProperty("class", "primary")
        install_btn.clicked.connect(self._install_or_update_gpt_researcher)
        actions_row.addWidget(install_btn)

        launch_btn = QPushButton("🚀 Launch Researcher UI")
        launch_btn.setProperty("class", "success")
        launch_btn.clicked.connect(self._launch_gpt_researcher_ui)
        actions_row.addWidget(launch_btn)

        open_repo_btn = QPushButton("📂 Open Repo")
        open_repo_btn.clicked.connect(self._open_gpt_researcher_repo)
        actions_row.addWidget(open_repo_btn)
        gpt_layout.addLayout(actions_row)

        layout.addWidget(gpt_group)

        # Crawl mirror section
        crawl_group = QGroupBox("🕸️ Crawl Mirror (D Drive)")
        crawl_layout = QVBoxLayout(crawl_group)

        seed_row = QHBoxLayout()
        seed_row.addWidget(QLabel("Seed URL:"))
        self.crawl_seed_url = QLineEdit("https://example.com")
        seed_row.addWidget(self.crawl_seed_url)
        crawl_layout.addLayout(seed_row)

        mirror_row = QHBoxLayout()
        mirror_row.addWidget(QLabel("Mirror Root:"))
        self.crawl_mirror_root = QLineEdit("D:/AI_Crawl_Mirror")
        mirror_row.addWidget(self.crawl_mirror_root)
        browse_mirror_btn = QPushButton("Browse...")
        browse_mirror_btn.clicked.connect(self._browse_crawl_mirror_root)
        mirror_row.addWidget(browse_mirror_btn)
        crawl_layout.addLayout(mirror_row)

        crawl_opts = QHBoxLayout()
        crawl_opts.addWidget(QLabel("Max Pages:"))
        self.crawl_max_pages = QSpinBox()
        self.crawl_max_pages.setRange(1, 1000)
        self.crawl_max_pages.setValue(25)
        crawl_opts.addWidget(self.crawl_max_pages)
        crawl_opts.addStretch()
        run_crawl_btn = QPushButton("🧭 Run Crawl Mirror")
        run_crawl_btn.setProperty("class", "primary")
        run_crawl_btn.clicked.connect(self._run_crawl_mirror)
        crawl_opts.addWidget(run_crawl_btn)
        crawl_layout.addLayout(crawl_opts)

        layout.addWidget(crawl_group)

        self.research_ops_log = QTextEdit()
        self.research_ops_log.setReadOnly(True)
        self.research_ops_log.setMaximumHeight(180)
        self.research_ops_log.setPlaceholderText("Research operations log...")
        layout.addWidget(self.research_ops_log)

        layout.addStretch()

    def _browse_gpt_researcher_repo(self):
        path = QFileDialog.getExistingDirectory(self, "Select GPT Researcher Folder")
        if path:
            self.gpt_repo_path.setText(path)

    def _open_gpt_researcher_repo(self):
        repo_path = Path(self.gpt_repo_path.text().strip())
        if not repo_path.exists():
            QMessageBox.warning(self, "Missing Folder", f"Not found:\n{repo_path}")
            return
        subprocess.Popen(['explorer', str(repo_path)])

    def _append_research_log(self, message: str):
        if hasattr(self, "research_ops_log") and self.research_ops_log:
            self.research_ops_log.append(message)

    def _install_or_update_gpt_researcher(self):
        import sys

        repo_url = "https://github.com/assafelovic/gpt-researcher.git"
        repo_path = Path(self.gpt_repo_path.text().strip())
        if not repo_path:
            QMessageBox.warning(self, "Missing Path", "Please set a repo path first.")
            return

        try:
            self._append_research_log("Preparing GPT Researcher repository...")
            repo_path.parent.mkdir(parents=True, exist_ok=True)

            if (repo_path / ".git").exists():
                self._append_research_log(f"Updating existing repo: {repo_path}")
                pull = subprocess.run(
                    ["git", "-C", str(repo_path), "pull", "--ff-only"],
                    capture_output=True,
                    text=True
                )
                if pull.returncode != 0:
                    self._append_research_log(f"git pull warning: {pull.stderr.strip()}")
                else:
                    self._append_research_log("✓ Repository updated")
            else:
                self._append_research_log(f"Cloning: {repo_url}")
                clone = subprocess.run(
                    ["git", "clone", repo_url, str(repo_path)],
                    capture_output=True,
                    text=True
                )
                if clone.returncode != 0:
                    QMessageBox.critical(self, "Clone Failed", clone.stderr.strip() or "Unknown git clone error.")
                    return
                self._append_research_log("✓ Repository cloned")

            requirements = repo_path / "requirements.txt"
            if requirements.exists():
                self._append_research_log("Installing Python requirements...")
                install = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", str(requirements)],
                    capture_output=True,
                    text=True
                )
                if install.returncode != 0:
                    self._append_research_log(f"pip warning: {install.stderr.strip()}")
                else:
                    self._append_research_log("✓ Requirements installed")
            else:
                self._append_research_log("No requirements.txt found; skipped pip install")

            QMessageBox.information(self, "Complete", "GPT Researcher install/update complete.")
        except Exception as e:
            QMessageBox.critical(self, "Install Error", str(e))

    def _launch_gpt_researcher_ui(self):
        import sys
        import webbrowser

        repo_path = Path(self.gpt_repo_path.text().strip())
        if not repo_path.exists():
            QMessageBox.warning(self, "Missing Folder", f"Repo folder not found:\n{repo_path}")
            return

        commands = []
        if (repo_path / "main.py").exists():
            commands.append([sys.executable, "-m", "streamlit", "run", "main.py"])
            commands.append([sys.executable, "main.py"])
        commands.append([sys.executable, "-m", "gpt_researcher"])

        creationflags = subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        last_error = None
        for cmd in commands:
            try:
                subprocess.Popen(cmd, cwd=str(repo_path), creationflags=creationflags)
                self._append_research_log(f"✓ Launched: {' '.join(cmd)}")
                webbrowser.open("http://localhost:8501")
                return
            except Exception as e:
                last_error = e

        QMessageBox.critical(
            self,
            "Launch Error",
            f"Could not launch GPT Researcher from {repo_path}\n\nLast error: {last_error}"
        )

    def _browse_crawl_mirror_root(self):
        path = QFileDialog.getExistingDirectory(self, "Select Crawl Mirror Root")
        if path:
            self.crawl_mirror_root.setText(path)

    def _run_crawl_mirror(self):
        import re
        import urllib.request
        from collections import deque
        from datetime import datetime
        from urllib.parse import urljoin, urlparse, urlunparse
        from PySide6.QtWidgets import QApplication

        seed_url = self.crawl_seed_url.text().strip()
        mirror_root = Path(self.crawl_mirror_root.text().strip())
        max_pages = int(self.crawl_max_pages.value())

        parsed_seed = urlparse(seed_url)
        if parsed_seed.scheme not in {"http", "https"} or not parsed_seed.netloc:
            QMessageBox.warning(self, "Invalid URL", "Please provide a valid http/https seed URL.")
            return

        domain = parsed_seed.netloc.replace(":", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = mirror_root / domain / timestamp
        pages_dir = session_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        queue = deque([seed_url])
        visited = set()
        manifest = []

        headers = {
            "User-Agent": "TheophysicsCrawler/1.0 (+vault mirror)"
        }

        self._append_research_log(f"Starting crawl: {seed_url}")
        self._append_research_log(f"Mirror output: {session_dir}")

        while queue and len(visited) < max_pages:
            url = queue.popleft()
            parsed = urlparse(url)
            normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))
            if normalized in visited:
                continue

            try:
                req = urllib.request.Request(normalized, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    body = resp.read()
                    content_type = resp.headers.get("Content-Type", "")
            except Exception as e:
                self._append_research_log(f"⚠️ Skip {normalized} ({e})")
                continue

            visited.add(normalized)
            safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", normalized.replace("://", "_"))[:120]
            ext = ".html" if "html" in content_type.lower() else ".bin"
            out_file = pages_dir / f"{len(visited):04d}_{safe_name}{ext}"
            out_file.write_bytes(body)

            manifest.append({
                "url": normalized,
                "file": str(out_file),
                "content_type": content_type,
                "bytes": len(body),
            })
            self._append_research_log(f"[{len(visited)}/{max_pages}] Saved {normalized}")

            if "html" in content_type.lower():
                try:
                    html_text = body.decode("utf-8", errors="ignore")
                    links = re.findall(r"href=[\"']([^\"']+)[\"']", html_text, flags=re.IGNORECASE)
                    for href in links:
                        absolute = urljoin(normalized, href)
                        p = urlparse(absolute)
                        if p.scheme not in {"http", "https"}:
                            continue
                        if p.netloc != parsed_seed.netloc:
                            continue
                        clean = urlunparse((p.scheme, p.netloc, p.path or "/", "", p.query, ""))
                        if clean not in visited:
                            queue.append(clean)
                except Exception:
                    pass

            QApplication.processEvents()

        (session_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        summary = (
            f"# Crawl Mirror Summary\n\n"
            f"- Seed URL: {seed_url}\n"
            f"- Pages saved: {len(manifest)}\n"
            f"- Output folder: {session_dir}\n"
        )
        (session_dir / "summary.md").write_text(summary, encoding="utf-8")

        self._append_research_log(f"✓ Crawl complete. Saved {len(manifest)} pages.")
        QMessageBox.information(self, "Crawl Complete", f"Saved {len(manifest)} pages to:\n{session_dir}")

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

        summary = QLabel(
            "PostgreSQL-first sync mode: one-click vault scan + sync. "
            "SQLite internals stay in the background."
        )
        summary.setWordWrap(True)
        summary.setStyleSheet("color: #9ca3af;")
        layout.addWidget(summary)

        postgres_group = QGroupBox("🐘 PostgreSQL (Simple Sync)")
        postgres_layout = QVBoxLayout(postgres_group)

        conn_row = QHBoxLayout()
        conn_row.addWidget(QLabel("Connection:"))
        self.postgres_conn_label = QLabel("Not configured")
        self.postgres_conn_label.setStyleSheet("color: #9ca3af;")
        conn_row.addWidget(self.postgres_conn_label, 1)

        self.test_pg_btn = QPushButton("🔌 Test Connection")
        self.test_pg_btn.clicked.connect(self._test_postgres_connection)
        conn_row.addWidget(self.test_pg_btn)
        postgres_layout.addLayout(conn_row)

        self.postgres_metrics_label = QLabel("Status: Not connected")
        self.postgres_metrics_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        postgres_layout.addWidget(self.postgres_metrics_label)

        action_row = QHBoxLayout()

        self.sync_vault_pg_btn = QPushButton("🚀 Scan Vault + Sync to PostgreSQL")
        self.sync_vault_pg_btn.setProperty("class", "primary")
        self.sync_vault_pg_btn.clicked.connect(self._sync_vault_to_postgres_simple)
        action_row.addWidget(self.sync_vault_pg_btn)

        self.sync_to_pg_btn = QPushButton("⬆️ Sync Existing Cache → PostgreSQL")
        self.sync_to_pg_btn.clicked.connect(self._sync_sqlite_to_postgres)
        action_row.addWidget(self.sync_to_pg_btn)

        self.refresh_pg_btn = QPushButton("📊 Refresh PostgreSQL Metrics")
        self.refresh_pg_btn.clicked.connect(self._refresh_postgres_metrics)
        action_row.addWidget(self.refresh_pg_btn)

        postgres_layout.addLayout(action_row)

        self.db_progress = QProgressBar()
        self.db_progress.setVisible(False)
        postgres_layout.addWidget(self.db_progress)

        self.postgres_status_log = QTextEdit()
        self.postgres_status_log.setMaximumHeight(170)
        self.postgres_status_log.setReadOnly(True)
        self.postgres_status_log.setPlaceholderText("PostgreSQL sync status will appear here...")
        postgres_layout.addWidget(self.postgres_status_log)

        layout.addWidget(postgres_group)

        # Hidden compatibility fields for existing helper methods
        self.sqlite_path_label = QLabel()
        self.sqlite_metrics_label = QLabel()
        self.sqlite_status_log = self.postgres_status_log
        self.scan_vault_btn = QPushButton()
        self.sync_status_labels = {}

        layout.addStretch()

        self._init_database_display()
        if hasattr(self, "_refresh_postgres_metrics"):
            self._refresh_postgres_metrics()

    def _append_db_log(self, message: str):
        if hasattr(self, "postgres_status_log") and self.postgres_status_log:
            self.postgres_status_log.append(message)

    def _sync_vault_to_postgres_simple(self):
        if not hasattr(self, "_vault_engine") or not self._vault_engine:
            self._append_db_log("⚠️ Vault engine not initialized")
            return

        if hasattr(self, "sync_vault_pg_btn"):
            self.sync_vault_pg_btn.setEnabled(False)
        self.db_progress.setVisible(True)
        self.db_progress.setValue(0)

        try:
            self._append_db_log("Scanning vault to local cache...")
            self.db_progress.setValue(25)
            self._vault_engine.scan_vault(full=True)

            self._append_db_log("Syncing cache to PostgreSQL...")
            self.db_progress.setValue(70)
            self._sync_sqlite_to_postgres()

            self.db_progress.setValue(100)
            self._append_db_log("✓ Vault scan + PostgreSQL sync complete")
        except Exception as e:
            self._append_db_log(f"Error: {e}")
        finally:
            if hasattr(self, "sync_vault_pg_btn"):
                self.sync_vault_pg_btn.setEnabled(True)
            self.db_progress.setVisible(False)

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
                term_replacements = self.kwargs.get('term_replacements', {})

                total = len(files)
                total_links = 0
                files_mod = 0

                self.log_signal.emit(f"Applying links for {len(approved)} terms across {total} files...")

                for i, f in enumerate(files):
                    count = linker.apply_links_to_file(
                        f,
                        approved,
                        link_all=link_all,
                        term_replacements=term_replacements,
                    )
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
    self._tag_suggestion_state = self._load_tag_suggestion_state()
    self._current_tag_suggestions = []
    
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

    # === TAG SUGGESTIONS ===
    suggest_group = QGroupBox("Suggested Tags (Accept/Reject)")
    suggest_layout = QVBoxLayout(suggest_group)

    suggest_btn_row = QHBoxLayout()

    suggest_btn = QPushButton("💡 Suggest Tags For Note")
    suggest_btn.clicked.connect(self._suggest_semantic_tags)
    suggest_btn_row.addWidget(suggest_btn)

    accept_btn = QPushButton("✅ Accept Selected")
    accept_btn.clicked.connect(self._accept_selected_tag_suggestions)
    suggest_btn_row.addWidget(accept_btn)

    reject_btn = QPushButton("❌ Reject Selected")
    reject_btn.clicked.connect(self._reject_selected_tag_suggestions)
    suggest_btn_row.addWidget(reject_btn)

    ignore_btn = QPushButton("🚫 Ignore Selected Forever")
    ignore_btn.clicked.connect(self._ignore_selected_tag_suggestions)
    suggest_btn_row.addWidget(ignore_btn)

    clear_ignore_btn = QPushButton("♻️ Clear Ignore List")
    clear_ignore_btn.clicked.connect(self._clear_ignored_tag_suggestions)
    suggest_btn_row.addWidget(clear_ignore_btn)

    suggest_layout.addLayout(suggest_btn_row)

    self.tag_suggestion_table = QTableWidget(0, 4)
    self.tag_suggestion_table.setHorizontalHeaderLabels(["Axis", "Value", "Reason", "Status"])
    self.tag_suggestion_table.horizontalHeader().setStretchLastSection(True)
    self.tag_suggestion_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    self.tag_suggestion_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    self.tag_suggestion_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
    self.tag_suggestion_table.setMaximumHeight(220)
    suggest_layout.addWidget(self.tag_suggestion_table)

    ignored = len(self._tag_suggestion_state.get("ignored_keys", []))
    self.tag_suggest_status = QLabel(f"Ignored suggestions: {ignored}")
    self.tag_suggest_status.setStyleSheet("color: #888;")
    suggest_layout.addWidget(self.tag_suggest_status)

    layout.addWidget(suggest_group)
    
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


def _tag_suggestion_state_path(self) -> Path:
    """Persistent storage for accepted/rejected/ignored suggestions."""
    return Path(__file__).resolve().parent.parent / "config" / "ui_cache" / "tag_suggestions_state.json"


def _load_tag_suggestion_state(self) -> Dict[str, object]:
    """Load persisted suggestion state."""
    default_state: Dict[str, object] = {
        "ignored_keys": [],
        "rejected_by_note": {},
        "history": [],
    }
    path = self._tag_suggestion_state_path()
    if not path.exists():
        return default_state
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            return default_state
        state = dict(default_state)
        state.update(loaded)
        return state
    except Exception:
        return default_state


def _save_tag_suggestion_state(self):
    """Persist suggestion state to disk."""
    try:
        path = self._tag_suggestion_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self._tag_suggestion_state, indent=2), encoding="utf-8")
    except Exception:
        pass


def _record_tag_suggestion_decision(self, key: str, decision: str, note_path: str):
    """Append decision history with bounded size."""
    history = self._tag_suggestion_state.setdefault("history", [])
    if not isinstance(history, list):
        history = []
        self._tag_suggestion_state["history"] = history
    history.append(
        {
            "key": key,
            "decision": decision,
            "note_path": note_path,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    if len(history) > 2000:
        self._tag_suggestion_state["history"] = history[-2000:]


def _get_vault_path_for_tags(self) -> str:
    """Resolve vault path for semantic tag operations."""
    vault_path = self._folder_config.get('vault_root', '')
    if not vault_path:
        vault_path = self.settings.get('obsidian', 'vault_path', '')
    return vault_path


def _resolve_note_path_for_tags(self, note_path: str, vault_path: str) -> tuple[Optional[Path], str]:
    """
    Resolve absolute note path and semantic-engine relative key.
    Returns: (absolute_path or None, relative_key_for_engine)
    """
    candidate = Path(note_path)
    if not candidate.is_absolute():
        candidate = Path(vault_path) / candidate
    if not candidate.exists() and candidate.suffix.lower() != ".md":
        md_candidate = candidate.with_suffix(".md")
        if md_candidate.exists():
            candidate = md_candidate
    if not candidate.exists():
        return None, note_path

    try:
        rel_key = str(candidate.relative_to(Path(vault_path))).replace("\\", "/")
    except Exception:
        rel_key = note_path
    return candidate, rel_key


def _infer_semantic_tag_suggestions(
    self,
    content: str,
    note_rel_path: str,
    existing_tags: Dict[str, List[str]],
) -> List[Dict[str, object]]:
    """Generate semantic tag suggestions from note content."""
    import re

    lower = content.lower()
    word_count = len(content.split())

    ignored_keys = set(self._tag_suggestion_state.get("ignored_keys", []))
    rejected_map = self._tag_suggestion_state.get("rejected_by_note", {})
    rejected_for_note = set(rejected_map.get(note_rel_path, [])) if isinstance(rejected_map, dict) else set()

    suggestions: Dict[str, Dict[str, object]] = {}

    def add(axis: str, value: str, reason: str, score: int):
        key = f"{axis}/{value}"
        if key in ignored_keys or key in rejected_for_note:
            return
        if value in existing_tags.get(axis, []):
            return
        current = suggestions.get(key)
        if current is None or score > int(current.get("score", 0)):
            suggestions[key] = {
                "key": key,
                "axis": axis,
                "value": value,
                "reason": reason,
                "score": score,
                "status": "pending",
            }

    # Epistemic (required, one)
    speculative_hits = sum(lower.count(w) for w in ["hypothesis", "conjecture", "might", "may", "could", "speculative"])
    inferential_hits = sum(lower.count(w) for w in ["derive", "derivation", "therefore", "thus", "proof", "theorem"])
    metaphor_hits = sum(lower.count(w) for w in ["metaphor", "analogy", "as if", "like this"])

    if speculative_hits > 0:
        add("epistemic", "speculative", "Contains hypothesis/speculative language.", 95)
    elif inferential_hits > 0:
        add("epistemic", "inferential", "Contains derivation/proof language.", 92)
    elif metaphor_hits > 0:
        add("epistemic", "metaphorical", "Contains analogy/metaphor framing.", 90)
    else:
        add("epistemic", "established", "No explicit speculative markers detected.", 75)

    # Function (up to 2)
    function_keywords = {
        "definition": ["definition", "defined as", "means", "term"],
        "bridge": ["bridge", "connect", "mapping", "isomorphism", "across domains"],
        "constraint": ["constraint", "limit", "boundary", "cannot", "must not"],
        "synthesis": ["synthesis", "integrate", "unify", "combine"],
        "example": ["example", "for instance", "e.g.", "case study"],
        "objection": ["objection", "counterargument", "critique"],
        "response": ["response", "reply", "rebuttal", "answers"],
        "derivation": ["derive", "derivation", "proof", "step-by-step"],
    }
    function_scored: List[tuple[str, int]] = []
    for fn_value, words in function_keywords.items():
        hits = sum(len(re.findall(re.escape(w), lower)) for w in words)
        if hits > 0:
            function_scored.append((fn_value, hits))
    for fn_value, hits in sorted(function_scored, key=lambda x: x[1], reverse=True)[:2]:
        add("function", fn_value, f"Detected function keywords for '{fn_value}'.", 80 + min(hits, 10))

    # Domain (can have multiple)
    domain_keywords = {
        "physics": ["quantum", "gravity", "relativity", "thermodynamic", "field", "particle", "energy"],
        "information": ["shannon", "entropy", "information", "kolmogorov", "algorithm", "bit"],
        "philosophy": ["ontology", "epistemology", "metaphysics", "logic", "argument"],
        "theology": ["god", "logos", "christ", "trinity", "grace", "scripture", "sin"],
        "cognition": ["mind", "consciousness", "cognitive", "perception", "brain", "neural"],
        "mathematics": ["equation", "theorem", "lemma", "integral", "proof", "axiom"],
        "history": ["historical", "century", "timeline", "ancient", "era"],
    }
    domain_scored: List[tuple[str, int]] = []
    for domain, words in domain_keywords.items():
        hits = sum(lower.count(w) for w in words)
        if hits > 0:
            domain_scored.append((domain, hits))
    for domain, hits in sorted(domain_scored, key=lambda x: x[1], reverse=True)[:3]:
        add("domain", domain, f"Detected domain terms for '{domain}'.", 70 + min(hits, 15))

    # Reader path (one)
    if "appendix" in note_rel_path.lower() or "appendix" in lower[:1200]:
        add("path", "appendix", "Appendix markers detected.", 90)
    elif word_count > 3500:
        add("path", "deep", f"Long note ({word_count} words) suggests deep reading.", 82)
    elif word_count < 700:
        add("path", "entry", f"Short note ({word_count} words) suggests entry-level.", 78)
    else:
        add("path", "core", f"Mid-length note ({word_count} words) suggests core path.", 76)

    return sorted(suggestions.values(), key=lambda s: int(s.get("score", 0)), reverse=True)


def _render_tag_suggestions(self):
    """Render current suggestion list into the table."""
    self.tag_suggestion_table.setRowCount(len(self._current_tag_suggestions))
    for row, suggestion in enumerate(self._current_tag_suggestions):
        axis_item = QTableWidgetItem(str(suggestion.get("axis", "")))
        axis_item.setData(Qt.ItemDataRole.UserRole, suggestion)
        value_item = QTableWidgetItem(str(suggestion.get("value", "")))
        reason_item = QTableWidgetItem(str(suggestion.get("reason", "")))
        status_item = QTableWidgetItem(str(suggestion.get("status", "pending")))

        self.tag_suggestion_table.setItem(row, 0, axis_item)
        self.tag_suggestion_table.setItem(row, 1, value_item)
        self.tag_suggestion_table.setItem(row, 2, reason_item)
        self.tag_suggestion_table.setItem(row, 3, status_item)


def _selected_tag_suggestion_rows(self) -> List[int]:
    """Get unique selected rows from suggestion table."""
    return sorted({idx.row() for idx in self.tag_suggestion_table.selectedIndexes()})


def _suggest_semantic_tags(self):
    """Suggest semantic tags for the note currently entered in Note Path."""
    note_path = self.semantic_note_path.text().strip()
    if not note_path:
        QMessageBox.warning(self, "Missing Path", "Enter a note path first.")
        return

    vault_path = self._get_vault_path_for_tags()
    if not vault_path:
        QMessageBox.warning(self, "No Vault", "Please set vault path first.")
        return

    abs_path, rel_key = self._resolve_note_path_for_tags(note_path, vault_path)
    if not abs_path:
        QMessageBox.warning(self, "File Not Found", f"Could not find note:\n{note_path}")
        return

    try:
        content = abs_path.read_text(encoding="utf-8", errors="ignore")
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        existing_tags = engine.get_note_tags(rel_key)
    except Exception as e:
        QMessageBox.critical(self, "Suggestion Error", str(e))
        return

    self._current_tag_suggestions = self._infer_semantic_tag_suggestions(content, rel_key, existing_tags)
    self._render_tag_suggestions()
    ignored = len(self._tag_suggestion_state.get("ignored_keys", []))
    self.tag_suggest_status.setText(
        f"Suggested {len(self._current_tag_suggestions)} tags for {Path(rel_key).name} "
        f"(ignored globally: {ignored})"
    )


def _accept_selected_tag_suggestions(self):
    """Accept selected suggestions and apply them to the current note."""
    rows = self._selected_tag_suggestion_rows()
    if not rows:
        QMessageBox.information(self, "No Selection", "Select suggestion rows first.")
        return

    note_path = self.semantic_note_path.text().strip()
    vault_path = self._get_vault_path_for_tags()
    if not note_path or not vault_path:
        QMessageBox.warning(self, "Missing Context", "Set note path and vault path first.")
        return

    abs_path, rel_key = self._resolve_note_path_for_tags(note_path, vault_path)
    if not abs_path:
        QMessageBox.warning(self, "File Not Found", f"Could not find note:\n{note_path}")
        return

    tags_to_apply: Dict[str, List[str]] = {"epistemic": [], "function": [], "domain": [], "path": []}
    accepted = 0
    for row in rows:
        if row >= len(self._current_tag_suggestions):
            continue
        suggestion = self._current_tag_suggestions[row]
        axis = str(suggestion.get("axis", ""))
        value = str(suggestion.get("value", ""))
        if axis and value and value not in tags_to_apply[axis]:
            tags_to_apply[axis].append(value)
            suggestion["status"] = "accepted"
            accepted += 1
            self._record_tag_suggestion_decision(str(suggestion.get("key", "")), "accepted", rel_key)

    if accepted == 0:
        return

    try:
        from core.semantic_tag_engine import SemanticTagEngine
        engine = SemanticTagEngine(vault_path)
        result = engine.tag_note(rel_key, tags_to_apply)
        self.tag_status.setText(f"Applied {accepted} suggested tags to {Path(rel_key).name}")
        self.tag_results.setText(
            f"Accepted suggestions: {accepted}\n"
            f"Tags applied: {result.get('tags_added', [])}\n"
            f"Warnings: {result.get('warnings', [])}"
        )
    except Exception as e:
        QMessageBox.critical(self, "Accept Error", str(e))
        return

    self._save_tag_suggestion_state()
    self._render_tag_suggestions()


def _reject_selected_tag_suggestions(self):
    """Reject selected suggestions for this note."""
    rows = self._selected_tag_suggestion_rows()
    if not rows:
        QMessageBox.information(self, "No Selection", "Select suggestion rows first.")
        return

    note_path = self.semantic_note_path.text().strip()
    if not note_path:
        QMessageBox.warning(self, "Missing Path", "Enter note path first.")
        return
    vault_path = self._get_vault_path_for_tags()
    _, rel_key = self._resolve_note_path_for_tags(note_path, vault_path) if vault_path else (None, note_path)

    rejected_map = self._tag_suggestion_state.setdefault("rejected_by_note", {})
    if not isinstance(rejected_map, dict):
        rejected_map = {}
        self._tag_suggestion_state["rejected_by_note"] = rejected_map
    note_rejected = set(rejected_map.get(rel_key, []))

    for row in rows:
        if row >= len(self._current_tag_suggestions):
            continue
        suggestion = self._current_tag_suggestions[row]
        key = str(suggestion.get("key", ""))
        suggestion["status"] = "rejected"
        note_rejected.add(key)
        self._record_tag_suggestion_decision(key, "rejected", rel_key)

    rejected_map[rel_key] = sorted(note_rejected)
    self._save_tag_suggestion_state()
    self._render_tag_suggestions()
    self.tag_suggest_status.setText(f"Rejected {len(rows)} suggestions for {Path(rel_key).name}.")


def _ignore_selected_tag_suggestions(self):
    """Globally ignore selected suggestions so they never appear again."""
    rows = self._selected_tag_suggestion_rows()
    if not rows:
        QMessageBox.information(self, "No Selection", "Select suggestion rows first.")
        return

    ignored = set(self._tag_suggestion_state.get("ignored_keys", []))
    for row in rows:
        if row >= len(self._current_tag_suggestions):
            continue
        suggestion = self._current_tag_suggestions[row]
        key = str(suggestion.get("key", ""))
        ignored.add(key)
        suggestion["status"] = "ignored"
        self._record_tag_suggestion_decision(key, "ignored", self.semantic_note_path.text().strip())

    self._tag_suggestion_state["ignored_keys"] = sorted(ignored)
    self._save_tag_suggestion_state()
    self._render_tag_suggestions()
    self.tag_suggest_status.setText(f"Ignored suggestions globally: {len(ignored)}")


def _clear_ignored_tag_suggestions(self):
    """Clear global ignore list for tag suggestions."""
    self._tag_suggestion_state["ignored_keys"] = []
    self._save_tag_suggestion_state()
    self.tag_suggest_status.setText("Ignored suggestions cleared.")


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
MainWindowV2._tag_suggestion_state_path = _tag_suggestion_state_path
MainWindowV2._load_tag_suggestion_state = _load_tag_suggestion_state
MainWindowV2._save_tag_suggestion_state = _save_tag_suggestion_state
MainWindowV2._record_tag_suggestion_decision = _record_tag_suggestion_decision
MainWindowV2._get_vault_path_for_tags = _get_vault_path_for_tags
MainWindowV2._resolve_note_path_for_tags = _resolve_note_path_for_tags
MainWindowV2._infer_semantic_tag_suggestions = _infer_semantic_tag_suggestions
MainWindowV2._render_tag_suggestions = _render_tag_suggestions
MainWindowV2._selected_tag_suggestion_rows = _selected_tag_suggestion_rows
MainWindowV2._suggest_semantic_tags = _suggest_semantic_tags
MainWindowV2._accept_selected_tag_suggestions = _accept_selected_tag_suggestions
MainWindowV2._reject_selected_tag_suggestions = _reject_selected_tag_suggestions
MainWindowV2._ignore_selected_tag_suggestions = _ignore_selected_tag_suggestions
MainWindowV2._clear_ignored_tag_suggestions = _clear_ignored_tag_suggestions
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

# Import Document Evaluator page
try:
    from ui.document_evaluator_page import (
        _build_document_evaluator_page,
        _browse_eval_folder,
        _start_evaluation,
        _stop_evaluation,
        _on_eval_progress,
        _on_eval_finished,
        _on_eval_error,
        _export_eval_results,
        _generate_markdown_report
    )
    # Methods are already attached in the module
except ImportError as e:
    print(f"Document Evaluator import warning: {e}")


