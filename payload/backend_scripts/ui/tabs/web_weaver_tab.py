"""
Web Weaver Tab - GUI for automated wiki-link generation in Obsidian axiom files.

Creates a tangled web of interconnected notes by finding and converting
plain-text axiom references to [[wiki-links]].
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSplitter, QGroupBox, QCheckBox, QProgressBar,
    QLineEdit, QSpinBox, QComboBox, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from core.web_weaver import WebWeaver, LinkSuggestion


class ScanWorker(QThread):
    """Background worker for scanning files."""
    finished = Signal(list)  # List of suggestions
    progress = Signal(int, int)  # current, total

    def __init__(self, weaver: 'WebWeaver', file_path: Optional[Path] = None):
        super().__init__()
        self.weaver = weaver
        self.file_path = file_path

    def run(self):
        suggestions = self.weaver.find_link_opportunities(self.file_path)
        self.finished.emit(suggestions)


class WebWeaverTab(QWidget):
    """Tab for weaving wiki-links between axiom files."""

    def __init__(self, vault_path: Optional[Path] = None):
        super().__init__()
        self.vault_path = vault_path

        # Import here to avoid circular imports
        from core.web_weaver import WebWeaver
        self.weaver = WebWeaver(vault_path)

        self.suggestions: List['LinkSuggestion'] = []
        self._setup_ui()

        if vault_path:
            self._scan_vault()

    def set_vault_path(self, path: Path) -> None:
        """Set vault path and rescan."""
        self.vault_path = path
        self.weaver.set_vault_path(path)
        self._update_stats()

    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("🕸️ Web Weaver - Axiom Link Generator")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Automatically find and convert plain-text axiom references (like A1.1, O2.3, BC7.1) "
            "to [[wiki-links]], creating an interconnected web of notes."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Vault path display
        vault_group = QGroupBox("Vault")
        vault_layout = QHBoxLayout()

        self.vault_label = QLabel("No vault selected")
        if self.vault_path:
            self.vault_label.setText(str(self.vault_path))
        vault_layout.addWidget(self.vault_label, 1)

        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self._browse_vault)
        vault_layout.addWidget(browse_btn)

        vault_group.setLayout(vault_layout)
        layout.addWidget(vault_group)

        # Stats section
        stats_group = QGroupBox("📊 Vault Statistics")
        stats_layout = QHBoxLayout()

        self.files_label = QLabel("Files: 0")
        stats_layout.addWidget(self.files_label)

        self.links_label = QLabel("Existing Links: 0")
        stats_layout.addWidget(self.links_label)

        self.unlinked_label = QLabel("Unlinked References: 0")
        stats_layout.addWidget(self.unlinked_label)

        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self._update_stats)
        stats_layout.addWidget(refresh_btn)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Main splitter
        splitter = QSplitter(Qt.Vertical)
        layout.addWidget(splitter, 1)

        # Suggestions panel
        suggestions_panel = self._create_suggestions_panel()
        splitter.addWidget(suggestions_panel)

        # Preview panel
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)

        splitter.setSizes([400, 200])

    def _create_suggestions_panel(self) -> QWidget:
        """Create the suggestions table panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Controls
        controls_layout = QHBoxLayout()

        scan_btn = QPushButton("🔍 Scan for Link Opportunities")
        scan_btn.clicked.connect(self._scan_for_links)
        controls_layout.addWidget(scan_btn)

        self.select_all_cb = QCheckBox("Select All")
        self.select_all_cb.stateChanged.connect(self._toggle_select_all)
        controls_layout.addWidget(self.select_all_cb)

        controls_layout.addStretch()

        self.apply_btn = QPushButton("✅ Apply Selected Links")
        self.apply_btn.clicked.connect(self._apply_selected)
        self.apply_btn.setEnabled(False)
        controls_layout.addWidget(self.apply_btn)

        layout.addLayout(controls_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Suggestions table
        self.suggestions_table = QTableWidget()
        self.suggestions_table.setColumnCount(5)
        self.suggestions_table.setHorizontalHeaderLabels([
            "✓", "File", "Line", "Found", "Will Become"
        ])
        self.suggestions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.suggestions_table.setColumnWidth(0, 30)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.suggestions_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.suggestions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.suggestions_table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.suggestions_table)

        # Filter controls
        filter_layout = QHBoxLayout()

        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by file or axiom ID...")
        self.filter_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.filter_input)

        layout.addLayout(filter_layout)

        return panel

    def _create_preview_panel(self) -> QWidget:
        """Create the preview panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        # Preview label
        preview_label = QLabel("📄 Preview (context around selected suggestion)")
        layout.addWidget(preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select a suggestion above to see context...")
        layout.addWidget(self.preview_text)

        # Mermaid graph section
        graph_group = QGroupBox("🗺️ Connection Graph (Mermaid)")
        graph_layout = QVBoxLayout()

        graph_controls = QHBoxLayout()
        generate_graph_btn = QPushButton("Generate Graph")
        generate_graph_btn.clicked.connect(self._generate_graph)
        graph_controls.addWidget(generate_graph_btn)

        self.max_nodes_spin = QSpinBox()
        self.max_nodes_spin.setRange(10, 200)
        self.max_nodes_spin.setValue(50)
        self.max_nodes_spin.setPrefix("Max nodes: ")
        graph_controls.addWidget(self.max_nodes_spin)

        copy_graph_btn = QPushButton("📋 Copy")
        copy_graph_btn.clicked.connect(self._copy_graph)
        graph_controls.addWidget(copy_graph_btn)

        graph_controls.addStretch()
        graph_layout.addLayout(graph_controls)

        self.graph_output = QTextEdit()
        self.graph_output.setReadOnly(True)
        self.graph_output.setMaximumHeight(150)
        self.graph_output.setPlaceholderText("Click 'Generate Graph' to see connections...")
        graph_layout.addWidget(self.graph_output)

        graph_group.setLayout(graph_layout)
        layout.addWidget(graph_group)

        return panel

    def _browse_vault(self) -> None:
        """Browse for vault folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Axioms Folder",
            str(self.vault_path) if self.vault_path else ""
        )
        if folder:
            self.vault_path = Path(folder)
            self.vault_label.setText(str(self.vault_path))
            self.weaver.set_vault_path(self.vault_path)
            self._update_stats()

    def _scan_vault(self) -> None:
        """Initial vault scan."""
        if self.vault_path:
            self.weaver.set_vault_path(self.vault_path)
            self._update_stats()

    def _update_stats(self) -> None:
        """Update vault statistics."""
        if not self.vault_path:
            return

        count = self.weaver.scan_axiom_files()
        stats = self.weaver.get_link_stats()

        self.files_label.setText(f"Files: {stats['total_files']}")
        self.links_label.setText(f"Existing Links: {stats['total_existing_links']}")
        self.unlinked_label.setText(f"Unlinked References: {stats['unlinked_references']}")

    def _scan_for_links(self) -> None:
        """Scan for linking opportunities."""
        if not self.vault_path:
            QMessageBox.warning(self, "No Vault", "Please select a vault folder first.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Run scan
        self.suggestions = self.weaver.find_link_opportunities()
        self._populate_suggestions_table()

        self.progress_bar.setVisible(False)
        self._update_stats()

    def _populate_suggestions_table(self) -> None:
        """Populate the suggestions table."""
        self.suggestions_table.setRowCount(0)

        for suggestion in self.suggestions:
            row = self.suggestions_table.rowCount()
            self.suggestions_table.insertRow(row)

            # Checkbox
            cb = QCheckBox()
            cb.setChecked(True)
            cb_widget = QWidget()
            cb_layout = QHBoxLayout(cb_widget)
            cb_layout.addWidget(cb)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            self.suggestions_table.setCellWidget(row, 0, cb_widget)

            # File
            file_item = QTableWidgetItem(suggestion.file_path.stem)
            file_item.setData(Qt.UserRole, suggestion)
            self.suggestions_table.setItem(row, 1, file_item)

            # Line number
            self.suggestions_table.setItem(row, 2, QTableWidgetItem(str(suggestion.line_number)))

            # Original text
            self.suggestions_table.setItem(row, 3, QTableWidgetItem(suggestion.original_text))

            # Suggested link
            self.suggestions_table.setItem(row, 4, QTableWidgetItem(suggestion.suggested_link))

        self.apply_btn.setEnabled(len(self.suggestions) > 0)
        self.select_all_cb.setChecked(True)

    def _toggle_select_all(self, state: int) -> None:
        """Toggle all checkboxes."""
        checked = state == Qt.Checked
        for row in range(self.suggestions_table.rowCount()):
            cb_widget = self.suggestions_table.cellWidget(row, 0)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb:
                    cb.setChecked(checked)

    def _on_selection_changed(self) -> None:
        """Handle selection change in table."""
        selected = self.suggestions_table.selectedItems()
        if selected:
            row = selected[0].row()
            file_item = self.suggestions_table.item(row, 1)
            if file_item:
                suggestion = file_item.data(Qt.UserRole)
                if suggestion:
                    self._show_preview(suggestion)

    def _show_preview(self, suggestion: 'LinkSuggestion') -> None:
        """Show preview of the suggestion context."""
        try:
            content = suggestion.file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Get context lines
            line_idx = suggestion.line_number - 1
            start = max(0, line_idx - 3)
            end = min(len(lines), line_idx + 4)

            preview_lines = []
            for i in range(start, end):
                prefix = ">>> " if i == line_idx else "    "
                preview_lines.append(f"{i+1:4d} {prefix}{lines[i]}")

            preview = f"File: {suggestion.file_path.name}\n"
            preview += f"Change: {suggestion.original_text} → {suggestion.suggested_link}\n"
            preview += "-" * 60 + "\n"
            preview += '\n'.join(preview_lines)

            self.preview_text.setText(preview)

        except Exception as e:
            self.preview_text.setText(f"Error reading file: {e}")

    def _apply_filter(self, text: str) -> None:
        """Filter the suggestions table."""
        text = text.lower()
        for row in range(self.suggestions_table.rowCount()):
            file_item = self.suggestions_table.item(row, 1)
            found_item = self.suggestions_table.item(row, 3)

            show = True
            if text:
                file_text = file_item.text().lower() if file_item else ""
                found_text = found_item.text().lower() if found_item else ""
                show = text in file_text or text in found_text

            self.suggestions_table.setRowHidden(row, not show)

    def _apply_selected(self) -> None:
        """Apply selected suggestions."""
        selected_suggestions = []

        for row in range(self.suggestions_table.rowCount()):
            if self.suggestions_table.isRowHidden(row):
                continue

            cb_widget = self.suggestions_table.cellWidget(row, 0)
            if cb_widget:
                cb = cb_widget.findChild(QCheckBox)
                if cb and cb.isChecked():
                    file_item = self.suggestions_table.item(row, 1)
                    if file_item:
                        suggestion = file_item.data(Qt.UserRole)
                        if suggestion:
                            selected_suggestions.append(suggestion)

        if not selected_suggestions:
            QMessageBox.warning(self, "No Selection", "No suggestions selected to apply.")
            return

        # Confirm
        reply = QMessageBox.question(
            self,
            "Apply Links",
            f"Apply {len(selected_suggestions)} link(s) to files?\n\n"
            "This will modify the files. Make sure you have backups!",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Apply
        results = self.weaver.apply_suggestions(selected_suggestions)

        total_changes = sum(results.values())
        files_changed = len(results)

        QMessageBox.information(
            self,
            "Links Applied",
            f"Applied {total_changes} link(s) to {files_changed} file(s)."
        )

        # Rescan
        self._scan_for_links()

    def _generate_graph(self) -> None:
        """Generate Mermaid connection graph."""
        if not self.vault_path:
            QMessageBox.warning(self, "No Vault", "Please select a vault folder first.")
            return

        max_nodes = self.max_nodes_spin.value()
        graph = self.weaver.generate_mermaid_graph(max_nodes)
        self.graph_output.setText(graph)

    def _copy_graph(self) -> None:
        """Copy graph to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.graph_output.toPlainText())
        QMessageBox.information(self, "Copied", "Graph copied to clipboard.")
