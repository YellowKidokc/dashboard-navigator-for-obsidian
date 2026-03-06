# main.py
"""
Theophysics Research Manager v2.1
- Compact sidebar navigation (not ugly tabs across top)
- Robust error handling
- Proper metrics
"""

import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QFileDialog, QComboBox, QStackedWidget, QListWidget,
    QListWidgetItem, QFrame, QSplitter, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon

from engine.settings import SettingsManager
from engine.vault_engine import VaultEngine
from engine.definition_engine import DefinitionEngine
from engine.research_engine import ResearchLinkEngine
from engine.structure_engine import StructureEngine
from engine.database_engine import DatabaseEngine
from engine.ai_engine import AIEngine
from engine.ontology_engine import OntologyEngine


class TheophysicsManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theophysics Research Manager v2.1")
        self.resize(1400, 850)
        self.setStyleSheet(self._get_stylesheet())

        # Backend components
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()

        self.db_engine = DatabaseEngine(self.settings_mgr)
        self.vault_engine = VaultEngine(self.settings_mgr, self.db_engine)
        self.def_engine = DefinitionEngine(self.settings_mgr, self.db_engine)
        self.rl_engine = ResearchLinkEngine(self.settings_mgr, self.db_engine)
        self.struct_engine = StructureEngine(self.settings_mgr, self.db_engine)
        self.ai_engine = AIEngine(self.settings_mgr, self.db_engine)
        self.onto_engine = OntologyEngine(self.settings_mgr, self.db_engine)

        self._init_ui()

    def _get_stylesheet(self) -> str:
        return """
        QMainWindow {
            background-color: #1a1a2e;
        }
        QWidget {
            background-color: #1a1a2e;
            color: #eaeaea;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QListWidget {
            background-color: #16213e;
            border: none;
            border-radius: 8px;
            padding: 8px;
            outline: none;
        }
        QListWidget::item {
            padding: 12px 16px;
            margin: 4px 0;
            border-radius: 6px;
            color: #b8b8b8;
        }
        QListWidget::item:selected {
            background-color: #0f3460;
            color: #00d9ff;
            font-weight: bold;
        }
        QListWidget::item:hover:!selected {
            background-color: #1f4068;
        }
        QGroupBox {
            background-color: #16213e;
            border: 1px solid #0f3460;
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #00d9ff;
        }
        QPushButton {
            background-color: #0f3460;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            color: #eaeaea;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1f4068;
        }
        QPushButton:pressed {
            background-color: #0a2647;
        }
        QPushButton#primaryBtn {
            background-color: #00d9ff;
            color: #1a1a2e;
        }
        QPushButton#primaryBtn:hover {
            background-color: #00b8d4;
        }
        QPushButton#dangerBtn {
            background-color: #e94560;
        }
        QPushButton#dangerBtn:hover {
            background-color: #c73e54;
        }
        QLineEdit, QTextEdit {
            background-color: #0f3460;
            border: 1px solid #1f4068;
            border-radius: 6px;
            padding: 8px;
            color: #eaeaea;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #00d9ff;
        }
        QTableWidget {
            background-color: #16213e;
            border: 1px solid #0f3460;
            border-radius: 6px;
            gridline-color: #1f4068;
        }
        QTableWidget::item {
            padding: 8px;
        }
        QTableWidget::item:selected {
            background-color: #0f3460;
        }
        QHeaderView::section {
            background-color: #0f3460;
            padding: 8px;
            border: none;
            font-weight: bold;
            color: #00d9ff;
        }
        QComboBox {
            background-color: #0f3460;
            border: 1px solid #1f4068;
            border-radius: 6px;
            padding: 8px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QProgressBar {
            background-color: #0f3460;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #00d9ff;
            border-radius: 4px;
        }
        QLabel#titleLabel {
            font-size: 24px;
            font-weight: bold;
            color: #00d9ff;
            padding: 16px;
        }
        QLabel#subtitleLabel {
            font-size: 11px;
            color: #666;
            padding-bottom: 8px;
        }
        QLabel#metricsLabel {
            background-color: #0f3460;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Consolas', monospace;
        }
        QFrame#separator {
            background-color: #1f4068;
        }
        """

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # LEFT SIDEBAR
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("background-color: #16213e;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)

        title = QLabel("Theophysics")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)

        subtitle = QLabel("Research Manager v2.1")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(subtitle)

        self.nav_list = QListWidget()
        self.nav_list.setSpacing(2)

        nav_items = [
            ("Vault", 0),
            ("Definitions", 1),
            ("Research", 2),
            ("Ontology", 3),
            ("AI Features", 4),
            ("Structure", 5),
            ("Database", 6),
            ("Settings", 7),
        ]

        for label, idx in nav_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, idx)
            item.setSizeHint(QSize(200, 44))
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self._switch_page)
        sidebar_layout.addWidget(self.nav_list)

        sidebar_layout.addStretch()

        version_label = QLabel("SQLite + PostgreSQL")
        version_label.setStyleSheet("color: #444; font-size: 10px;")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

        main_layout.addWidget(sidebar)

        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFixedWidth(1)
        main_layout.addWidget(separator)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_vault_page())
        self.pages.addWidget(self._build_definitions_page())
        self.pages.addWidget(self._build_research_page())
        self.pages.addWidget(self._build_ontology_page())
        self.pages.addWidget(self._build_ai_page())
        self.pages.addWidget(self._build_structure_page())
        self.pages.addWidget(self._build_database_page())
        self.pages.addWidget(self._build_settings_page())

        main_layout.addWidget(self.pages, 1)

    def _switch_page(self, index: int):
        self.pages.setCurrentIndex(index)

    # PAGE 0: VAULT
    def _build_vault_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Vault Scanner")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        path_box = QGroupBox("Vault Location")
        path_layout = QVBoxLayout(path_box)

        path_row = QHBoxLayout()
        self.vault_path_edit = QLineEdit()
        self.vault_path_edit.setPlaceholderText("Select your Obsidian vault folder...")
        if self.settings_mgr.vault_path:
            self.vault_path_edit.setText(str(self.settings_mgr.vault_path))

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_vault)

        path_row.addWidget(self.vault_path_edit, 1)
        path_row.addWidget(browse_btn)
        path_layout.addLayout(path_row)

        layout.addWidget(path_box)

        scan_box = QGroupBox("Scan Operations")
        scan_layout = QVBoxLayout(scan_box)

        btn_row = QHBoxLayout()

        full_btn = QPushButton("Full Scan")
        full_btn.setObjectName("primaryBtn")
        full_btn.clicked.connect(lambda: self._run_vault_scan(full=True))

        incr_btn = QPushButton("Quick Scan")
        incr_btn.clicked.connect(lambda: self._run_vault_scan(full=False))

        btn_row.addWidget(full_btn)
        btn_row.addWidget(incr_btn)
        btn_row.addStretch()

        scan_layout.addLayout(btn_row)

        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        scan_layout.addWidget(self.scan_progress)

        self.scan_status = QLabel("Ready to scan")
        self.scan_status.setStyleSheet("color: #888;")
        scan_layout.addWidget(self.scan_status)

        layout.addWidget(scan_box)

        metrics_box = QGroupBox("Vault Metrics")
        metrics_layout = QVBoxLayout(metrics_box)

        self.metrics_label = QLabel("Notes: 0  |  Tags: 0  |  Links: 0  |  Definitions: 0")
        self.metrics_label.setObjectName("metricsLabel")
        metrics_layout.addWidget(self.metrics_label)

        layout.addWidget(metrics_box)

        layout.addStretch()
        return page

    def _browse_vault(self):
        path = QFileDialog.getExistingDirectory(self, "Select Obsidian Vault")
        if path:
            self.vault_path_edit.setText(path)
            self.settings_mgr.vault_path = Path(path)
            self.settings_mgr.save()
            self.scan_status.setText(f"Vault set: {path}")

    def _run_vault_scan(self, full: bool):
        vault_path = self.vault_path_edit.text().strip()

        if not vault_path:
            QMessageBox.warning(self, "No Vault", "Please select a vault folder first.")
            return

        if not Path(vault_path).exists():
            QMessageBox.warning(self, "Invalid Path", f"Vault path does not exist:\n{vault_path}")
            return

        self.settings_mgr.vault_path = Path(vault_path)
        self.settings_mgr.save()

        self.scan_status.setText("Scanning..." if full else "Quick scanning...")
        self.scan_progress.setVisible(True)
        self.scan_progress.setRange(0, 0)
        QApplication.processEvents()

        try:
            self.vault_engine.scan_vault(full=full)
            metrics = self.vault_engine.get_metrics()

            self.metrics_label.setText(
                f"Notes: {metrics['notes']:,}  |  "
                f"Tags: {metrics['tags']:,}  |  "
                f"Links: {metrics['links']:,}  |  "
                f"Definitions: {metrics['definitions']:,}"
            )

            self.scan_status.setText(
                f"Scan complete - {metrics['notes']:,} notes processed"
            )
            self.scan_status.setStyleSheet("color: #00d9ff;")

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}"
            self.scan_status.setText(error_msg)
            self.scan_status.setStyleSheet("color: #e94560;")

            QMessageBox.critical(
                self,
                "Scan Error",
                f"Error during vault scan:\n\n{error_msg}\n\nDetails:\n{traceback.format_exc()}"
            )

        finally:
            self.scan_progress.setVisible(False)

    # PAGE 1: DEFINITIONS
    def _build_definitions_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Definition Manager")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.def_table = QTableWidget(0, 3)
        self.def_table.setHorizontalHeaderLabels(["Term", "Status", "File"])
        self.def_table.horizontalHeader().setStretchLastSection(True)
        self.def_table.setSelectionBehavior(QTableWidget.SelectRows)
        left_layout.addWidget(self.def_table)

        scan_btn = QPushButton("Scan for Missing Definitions")
        scan_btn.clicked.connect(self._scan_definitions)
        left_layout.addWidget(scan_btn)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        editor_box = QGroupBox("Definition Editor")
        editor_layout = QVBoxLayout(editor_box)

        self.def_term_edit = QLineEdit()
        self.def_term_edit.setPlaceholderText("Term name...")
        editor_layout.addWidget(QLabel("Term:"))
        editor_layout.addWidget(self.def_term_edit)

        self.def_aliases_edit = QLineEdit()
        self.def_aliases_edit.setPlaceholderText("alias1, alias2, ...")
        editor_layout.addWidget(QLabel("Aliases:"))
        editor_layout.addWidget(self.def_aliases_edit)

        self.def_class_edit = QLineEdit()
        self.def_class_edit.setPlaceholderText("physics, theology, math")
        editor_layout.addWidget(QLabel("Classification:"))
        editor_layout.addWidget(self.def_class_edit)

        self.def_body_edit = QTextEdit()
        self.def_body_edit.setPlaceholderText("Definition content...")
        editor_layout.addWidget(QLabel("Definition:"))
        editor_layout.addWidget(self.def_body_edit)

        save_btn = QPushButton("Save Definition")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_definition)
        editor_layout.addWidget(save_btn)

        right_layout.addWidget(editor_box)
        splitter.addWidget(right_widget)

        splitter.setSizes([400, 500])
        layout.addWidget(splitter)

        return page

    def _scan_definitions(self):
        try:
            self.def_engine.scan_for_missing()
            defs = self.def_engine.list_definitions()
            self.def_table.setRowCount(len(defs))
            for row, d in enumerate(defs):
                self.def_table.setItem(row, 0, QTableWidgetItem(d["term"]))
                self.def_table.setItem(row, 1, QTableWidgetItem(d["status"]))
                self.def_table.setItem(row, 2, QTableWidgetItem(d.get("file_path", "")))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Definition scan failed: {e}")

    def _save_definition(self):
        data = {
            "term": self.def_term_edit.text().strip(),
            "aliases": [a.strip() for a in self.def_aliases_edit.text().split(",") if a.strip()],
            "classification": self.def_class_edit.text().strip(),
            "body": self.def_body_edit.toPlainText().strip(),
        }
        if not data["term"]:
            QMessageBox.warning(self, "Missing Term", "Please enter a term name.")
            return

        try:
            self.def_engine.save_definition(data)
            self._scan_definitions()
            QMessageBox.information(self, "Saved", f"Definition '{data['term']}' saved.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Save failed: {e}")

    # PAGE 2: RESEARCH
    def _build_research_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Research Links")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        link_box = QGroupBox("Add Custom Research Link")
        link_layout = QHBoxLayout(link_box)

        self.link_term_edit = QLineEdit()
        self.link_term_edit.setPlaceholderText("Term...")
        self.link_source_edit = QLineEdit()
        self.link_source_edit.setPlaceholderText("Source...")
        self.link_url_edit = QLineEdit()
        self.link_url_edit.setPlaceholderText("URL...")

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_research_link)

        link_layout.addWidget(self.link_term_edit)
        link_layout.addWidget(self.link_source_edit)
        link_layout.addWidget(self.link_url_edit)
        link_layout.addWidget(add_btn)

        layout.addWidget(link_box)

        proc_box = QGroupBox("Link Processor")
        proc_layout = QVBoxLayout(proc_box)

        self.rl_input_edit = QTextEdit()
        self.rl_input_edit.setPlaceholderText("Paste text here...")
        self.rl_input_edit.setMaximumHeight(120)
        proc_layout.addWidget(QLabel("Input Text:"))
        proc_layout.addWidget(self.rl_input_edit)

        self.rl_terms_edit = QLineEdit()
        self.rl_terms_edit.setPlaceholderText("term1, term2...")
        proc_layout.addWidget(QLabel("Terms:"))
        proc_layout.addWidget(self.rl_terms_edit)

        process_btn = QPushButton("Process Links")
        process_btn.clicked.connect(self._process_research_links)
        proc_layout.addWidget(process_btn)

        self.rl_output_edit = QTextEdit()
        self.rl_output_edit.setReadOnly(True)
        proc_layout.addWidget(QLabel("Output:"))
        proc_layout.addWidget(self.rl_output_edit)

        layout.addWidget(proc_box)

        return page

    def _add_research_link(self):
        try:
            self.rl_engine.add_custom_link(
                term=self.link_term_edit.text().strip(),
                source=self.link_source_edit.text().strip(),
                url=self.link_url_edit.text().strip(),
            )
            self.link_term_edit.clear()
            self.link_source_edit.clear()
            self.link_url_edit.clear()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _process_research_links(self):
        text = self.rl_input_edit.toPlainText()
        terms = [t.strip() for t in self.rl_terms_edit.text().split(",") if t.strip()]
        out = self.rl_engine.process_text_links(text, terms)
        self.rl_output_edit.setPlainText(out)

    # PAGE 3: ONTOLOGY
    def _build_ontology_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Ontology Builder")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        build_box = QGroupBox("Build Ontology")
        build_layout = QVBoxLayout(build_box)

        build_btn = QPushButton("Build Ontology from Definitions")
        build_btn.setObjectName("primaryBtn")
        build_btn.clicked.connect(self._build_ontology)
        build_layout.addWidget(build_btn)

        self.onto_stats_label = QLabel("Ontology not built yet")
        self.onto_stats_label.setObjectName("metricsLabel")
        build_layout.addWidget(self.onto_stats_label)

        layout.addWidget(build_box)

        explore_box = QGroupBox("Concept Explorer")
        explore_layout = QVBoxLayout(explore_box)

        search_row = QHBoxLayout()
        self.onto_search_edit = QLineEdit()
        self.onto_search_edit.setPlaceholderText("Enter concept name...")
        explore_btn = QPushButton("Explore")
        explore_btn.clicked.connect(self._explore_concept)
        search_row.addWidget(self.onto_search_edit, 1)
        search_row.addWidget(explore_btn)
        explore_layout.addLayout(search_row)

        self.onto_details_edit = QTextEdit()
        self.onto_details_edit.setReadOnly(True)
        explore_layout.addWidget(self.onto_details_edit)

        layout.addWidget(explore_box)

        export_box = QGroupBox("Export")
        export_layout = QHBoxLayout(export_box)

        json_btn = QPushButton("Export JSON")
        json_btn.clicked.connect(lambda: self._export_ontology("json"))
        gv_btn = QPushButton("Export GraphViz")
        gv_btn.clicked.connect(lambda: self._export_ontology("graphviz"))

        export_layout.addWidget(json_btn)
        export_layout.addWidget(gv_btn)
        export_layout.addStretch()

        layout.addWidget(export_box)

        return page

    def _build_ontology(self):
        try:
            self.onto_engine.build_ontology_from_definitions()
            stats = self.onto_engine.get_ontology_statistics()

            self.onto_stats_label.setText(
                f"Concepts: {stats['total_concepts']}  |  "
                f"Relationships: {stats['total_relationships']}  |  "
                f"Avg/Node: {stats['avg_relationships_per_node']:.1f}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Ontology build failed: {e}")

    def _explore_concept(self):
        term = self.onto_search_edit.text().strip()
        if not term:
            return

        try:
            node = self.onto_engine.build_ontology_node(term)

            if not node.get("exists"):
                self.onto_details_edit.setPlainText(f"Concept '{term}' not found.")
                return

            info = f"Term: {node['term']}\n"
            info += f"Classification: {node.get('classification', 'N/A')}\n"
            info += f"Completeness: {node.get('completeness', 0):.0%}\n\n"
            info += f"Links To: {', '.join(node.get('links_to', [])) or 'None'}\n"
            info += f"Related: {', '.join(node.get('related_by_type', [])) or 'None'}"

            self.onto_details_edit.setPlainText(info)
        except Exception as e:
            self.onto_details_edit.setPlainText(f"Error: {e}")

    def _export_ontology(self, fmt: str):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Ontology",
            f"ontology.{'json' if fmt == 'json' else 'dot'}"
        )
        if path:
            try:
                data = self.onto_engine.export_to_graph_format(fmt)
                Path(path).write_text(data, encoding="utf-8")
                QMessageBox.information(self, "Exported", f"Saved to {path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # PAGE 4: AI
    def _build_ai_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("AI Features")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        status_box = QGroupBox("AI Status")
        status_layout = QVBoxLayout(status_box)

        check_btn = QPushButton("Check AI Availability")
        check_btn.clicked.connect(self._check_ai_status)
        status_layout.addWidget(check_btn)

        self.ai_status_label = QLabel("Click to check AI status")
        self.ai_status_label.setObjectName("metricsLabel")
        status_layout.addWidget(self.ai_status_label)

        layout.addWidget(status_box)

        search_box = QGroupBox("Semantic Search")
        search_layout = QVBoxLayout(search_box)

        search_row = QHBoxLayout()
        self.ai_search_edit = QLineEdit()
        self.ai_search_edit.setPlaceholderText("Search your vault...")
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._semantic_search)
        search_row.addWidget(self.ai_search_edit, 1)
        search_row.addWidget(search_btn)
        search_layout.addLayout(search_row)

        self.ai_search_results = QTextEdit()
        self.ai_search_results.setReadOnly(True)
        self.ai_search_results.setMaximumHeight(150)
        search_layout.addWidget(self.ai_search_results)

        layout.addWidget(search_box)

        defgen_box = QGroupBox("AI Definition Generator")
        defgen_layout = QVBoxLayout(defgen_box)

        term_row = QHBoxLayout()
        self.ai_defgen_term = QLineEdit()
        self.ai_defgen_term.setPlaceholderText("Term to define...")
        term_row.addWidget(QLabel("Term:"))
        term_row.addWidget(self.ai_defgen_term, 1)
        defgen_layout.addLayout(term_row)

        self.ai_defgen_context = QTextEdit()
        self.ai_defgen_context.setPlaceholderText("Context (optional)...")
        self.ai_defgen_context.setMaximumHeight(60)
        defgen_layout.addWidget(self.ai_defgen_context)

        gen_btn = QPushButton("Generate Definition")
        gen_btn.clicked.connect(self._generate_definition)
        defgen_layout.addWidget(gen_btn)

        self.ai_defgen_result = QTextEdit()
        self.ai_defgen_result.setReadOnly(True)
        defgen_layout.addWidget(self.ai_defgen_result)

        layout.addWidget(defgen_box)

        return page

    def _check_ai_status(self):
        try:
            status = self.ai_engine.get_ai_status()
            self.ai_status_label.setText(
                f"OpenAI: {'Yes' if status['openai_available'] else 'No'}  |  "
                f"Anthropic: {'Yes' if status['anthropic_available'] else 'No'}  |  "
                f"Model: {status['model_name']}"
            )
        except Exception as e:
            self.ai_status_label.setText(f"Error: {e}")

    def _semantic_search(self):
        query = self.ai_search_edit.text().strip()
        if not query:
            return

        try:
            results = self.ai_engine.semantic_search(query, top_k=5)
            if not results:
                self.ai_search_results.setPlainText("No results found.")
                return

            output = ""
            for i, r in enumerate(results, 1):
                output += f"{i}. {r['title']} (sim: {r['similarity']:.2f})\n"
            self.ai_search_results.setPlainText(output)
        except Exception as e:
            self.ai_search_results.setPlainText(f"Error: {e}")

    def _generate_definition(self):
        term = self.ai_defgen_term.text().strip()
        context = self.ai_defgen_context.toPlainText().strip()
        if not term:
            return

        try:
            definition = self.ai_engine.generate_definition(term, context)
            self.ai_defgen_result.setPlainText(definition)
        except Exception as e:
            self.ai_defgen_result.setPlainText(f"Error: {e}")

    # PAGE 5: STRUCTURE
    def _build_structure_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Structure Builder")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        struct_box = QGroupBox("Inject Structure")
        struct_layout = QVBoxLayout(struct_box)

        path_row = QHBoxLayout()
        self.struct_note_path = QLineEdit()
        self.struct_note_path.setPlaceholderText("Select a note...")
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_structure_note)
        path_row.addWidget(self.struct_note_path, 1)
        path_row.addWidget(browse_btn)
        struct_layout.addLayout(path_row)

        build_btn = QPushButton("Inject Structure / Footnote Section")
        build_btn.setObjectName("primaryBtn")
        build_btn.clicked.connect(self._build_structure_for_note)
        struct_layout.addWidget(build_btn)

        layout.addWidget(struct_box)
        layout.addStretch()

        return page

    def _browse_structure_note(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Note", filter="Markdown (*.md)")
        if path:
            self.struct_note_path.setText(path)

    def _build_structure_for_note(self):
        p = self.struct_note_path.text().strip()
        if not p:
            QMessageBox.warning(self, "No File", "Please select a note file.")
            return

        try:
            self.struct_engine.build_structure_for_note(Path(p))
            QMessageBox.information(self, "Done", "Structure injected.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # PAGE 6: DATABASE
    def _build_database_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Database Management")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        sqlite_box = QGroupBox("SQLite Database")
        sqlite_layout = QVBoxLayout(sqlite_box)

        path_row = QHBoxLayout()
        self.sqlite_path_edit = QLineEdit()
        if self.settings_mgr.sqlite_path:
            self.sqlite_path_edit.setText(str(self.settings_mgr.sqlite_path))
        else:
            self.sqlite_path_edit.setPlaceholderText("Default: theophysics.db")

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_sqlite)
        path_row.addWidget(self.sqlite_path_edit, 1)
        path_row.addWidget(browse_btn)
        sqlite_layout.addLayout(path_row)

        vacuum_btn = QPushButton("Vacuum/Optimize SQLite")
        vacuum_btn.clicked.connect(self._vacuum_sqlite)
        sqlite_layout.addWidget(vacuum_btn)

        layout.addWidget(sqlite_box)

        pg_box = QGroupBox("PostgreSQL Export")
        pg_layout = QVBoxLayout(pg_box)

        self.pg_conn_edit = QLineEdit()
        self.pg_conn_edit.setPlaceholderText("postgresql://user:pass@host:5432/dbname")
        if self.settings_mgr.postgres_conn_str:
            self.pg_conn_edit.setText(self.settings_mgr.postgres_conn_str)
        pg_layout.addWidget(QLabel("Connection String:"))
        pg_layout.addWidget(self.pg_conn_edit)

        export_btn = QPushButton("Export to PostgreSQL")
        export_btn.clicked.connect(self._export_pg)
        pg_layout.addWidget(export_btn)

        self.db_result_label = QLabel("No export run yet.")
        self.db_result_label.setStyleSheet("color: #888;")
        pg_layout.addWidget(self.db_result_label)

        layout.addWidget(pg_box)
        layout.addStretch()

        return page

    def _browse_sqlite(self):
        path, _ = QFileDialog.getSaveFileName(self, "SQLite DB", filter="SQLite (*.db)")
        if path:
            self.sqlite_path_edit.setText(path)
            self.settings_mgr.sqlite_path = Path(path)
            self.settings_mgr.save()
            self.db_engine.update_db_path(Path(path))

    def _vacuum_sqlite(self):
        try:
            self.db_engine.vacuum_sqlite()
            QMessageBox.information(self, "Done", "SQLite database optimized.")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _export_pg(self):
        conn_str = self.pg_conn_edit.text().strip()
        if not conn_str:
            QMessageBox.warning(self, "Missing", "Enter a PostgreSQL connection string.")
            return

        self.settings_mgr.postgres_conn_str = conn_str
        self.settings_mgr.save()

        try:
            ok, msg = self.db_engine.export_to_postgres()
            self.db_result_label.setText(msg)
            self.db_result_label.setStyleSheet(f"color: {'#00d9ff' if ok else '#e94560'};")
        except Exception as e:
            self.db_result_label.setText(f"Error: {e}")
            self.db_result_label.setStyleSheet("color: #e94560;")

    # PAGE 7: SETTINGS
    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("Settings")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(header)

        settings_box = QGroupBox("General Settings")
        settings_layout = QVBoxLayout(settings_box)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Default AI Model:"))

        self.model_combo = QComboBox()
        self.model_combo.addItems(["none", "gpt-4.1", "gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514"])
        if self.settings_mgr.model_name:
            idx = self.model_combo.findText(self.settings_mgr.model_name)
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        self.model_combo.currentTextChanged.connect(lambda t: setattr(self.settings_mgr, 'model_name', t))
        model_row.addWidget(self.model_combo, 1)

        settings_layout.addLayout(model_row)

        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_settings)
        settings_layout.addWidget(save_btn)

        layout.addWidget(settings_box)

        info_box = QGroupBox("About")
        info_layout = QVBoxLayout(info_box)
        info_layout.addWidget(QLabel(
            "Theophysics Research Manager v2.1\n\n"
            "Knowledge management for Theophysics research.\n"
            "SQLite (local) + PostgreSQL (remote) sync."
        ))
        layout.addWidget(info_box)

        layout.addStretch()
        return page

    def _save_settings(self):
        self.settings_mgr.save()
        QMessageBox.information(self, "Saved", "Settings saved.")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = TheophysicsManager()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
