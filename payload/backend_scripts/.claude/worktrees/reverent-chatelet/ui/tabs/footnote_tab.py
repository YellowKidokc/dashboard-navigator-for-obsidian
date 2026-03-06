"""
Footnote Tab - GUI for generating footnotes with academic and vault links.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QSplitter, QGroupBox, QCheckBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.footnote_system import FootnoteSystem
    from core.research_linker import ResearchLinker
    from core.obsidian_definitions_manager import ObsidianDefinitionsManager


class FootnoteTab(QWidget):
    """Tab for managing footnotes."""
    
    def __init__(
        self,
        footnote_system: FootnoteSystem,
        research_linker: ResearchLinker,
        definitions_manager: ObsidianDefinitionsManager
    ):
        super().__init__()
        self.footnote_system = footnote_system
        self.research_linker = research_linker
        self.definitions_manager = definitions_manager
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("📝 Footnote System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: Footnote management
        left_panel = self._create_footnote_management_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Text processing
        right_panel = self._create_text_processing_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def _create_footnote_management_panel(self) -> QWidget:
        """Create the left panel for managing footnotes."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add footnote section
        add_group = QGroupBox("Add Footnote")
        add_layout = QVBoxLayout()
        
        # Term input
        term_label = QLabel("Term:")
        add_layout.addWidget(term_label)
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("e.g., 'quantum mechanics'")
        add_layout.addWidget(self.term_input)
        
        # Vault link
        vault_label = QLabel("Vault Link (Obsidian):")
        add_layout.addWidget(vault_label)
        self.vault_link_input = QLineEdit()
        self.vault_link_input.setPlaceholderText("[[Glossary#Term]] or leave empty for auto")
        add_layout.addWidget(self.vault_link_input)
        
        # Academic sources
        sources_label = QLabel("Academic Sources (check to include):")
        add_layout.addWidget(sources_label)
        self.source_checkboxes = {}
        sources_layout = QVBoxLayout()
        for source in ['stanford', 'iep', 'arxiv', 'scholar']:
            cb = QCheckBox(self.research_linker.LINK_TEMPLATES.get(source, {}).get('display_name', source))
            cb.setChecked(source == 'stanford')  # Default to Stanford
            self.source_checkboxes[source] = cb
            sources_layout.addWidget(cb)
        add_layout.addLayout(sources_layout)
        
        # Explanation
        explanation_label = QLabel("Simple Explanation:")
        add_layout.addWidget(explanation_label)
        self.explanation_input = QTextEdit()
        self.explanation_input.setPlaceholderText("Brief, simple explanation (not 42 pages of formalism!)")
        self.explanation_input.setMaximumHeight(100)
        add_layout.addWidget(self.explanation_input)
        
        # Add button
        add_btn = QPushButton("➕ Add Footnote")
        add_btn.clicked.connect(self._add_footnote)
        add_layout.addWidget(add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Current footnotes list
        list_label = QLabel("Current Footnotes:")
        layout.addWidget(list_label)
        
        self.footnotes_list = QListWidget()
        self.footnotes_list.itemDoubleClicked.connect(self._edit_footnote)
        layout.addWidget(self.footnotes_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.clicked.connect(self._clear_footnotes)
        btn_layout.addWidget(clear_btn)
        
        preview_btn = QPushButton("👁️ Preview Section")
        preview_btn.clicked.connect(self._preview_footnotes)
        btn_layout.addWidget(preview_btn)
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        return panel
    
    def _create_text_processing_panel(self) -> QWidget:
        """Create the right panel for processing text."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Input section
        input_group = QGroupBox("Input Text")
        input_layout = QVBoxLayout()
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Paste your text here...")
        input_layout.addWidget(self.input_text)
        
        # Terms to footnote
        terms_label = QLabel("Terms to footnote (one per line, or comma-separated):")
        input_layout.addWidget(terms_label)
        self.terms_input = QTextEdit()
        self.terms_input.setPlaceholderText("quantum mechanics\ngeneral relativity\nconsciousness")
        self.terms_input.setMaximumHeight(100)
        input_layout.addWidget(self.terms_input)
        
        # Process button
        process_btn = QPushButton("📝 Process & Add Footnotes")
        process_btn.clicked.connect(self._process_text)
        input_layout.addWidget(process_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Output (with footnotes)")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        # Copy button
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_output)
        output_layout.addWidget(copy_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Footnotes section preview
        footnotes_group = QGroupBox("Footnotes Section")
        footnotes_layout = QVBoxLayout()
        
        self.footnotes_preview = QTextEdit()
        self.footnotes_preview.setReadOnly(True)
        footnotes_layout.addWidget(self.footnotes_preview)
        
        copy_footnotes_btn = QPushButton("📋 Copy Footnotes Section")
        copy_footnotes_btn.clicked.connect(self._copy_footnotes)
        footnotes_layout.addWidget(copy_footnotes_btn)
        
        footnotes_group.setLayout(footnotes_layout)
        layout.addWidget(footnotes_group)
        
        return panel
    
    def _add_footnote(self) -> None:
        """Add a footnote manually."""
        term = self.term_input.text().strip()
        vault_link = self.vault_link_input.text().strip() or None
        explanation = self.explanation_input.toPlainText().strip()
        
        # Get selected academic sources
        academic_sources = [
            source for source, cb in self.source_checkboxes.items()
            if cb.isChecked()
        ] or None  # None means auto-select
        
        if not term:
            QMessageBox.warning(self, "Missing Term", "Please enter a term.")
            return
        
        marker = self.footnote_system.add_footnote(
            term=term,
            vault_link=vault_link,
            academic_sources=academic_sources,
            explanation=explanation
        )
        
        self._refresh_footnotes_list()
        self._clear_footnote_form()
        
        QMessageBox.information(self, "Added", f"Footnote [{marker}] added for '{term}'.")
    
    def _process_text(self) -> None:
        """Process input text and add footnotes."""
        text = self.input_text.toPlainText()
        terms_str = self.terms_input.toPlainText().strip()
        
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to process.")
            return
        
        if not terms_str:
            QMessageBox.warning(self, "No Terms", "Please specify terms to footnote.")
            return
        
        # Parse terms (support both newline and comma-separated)
        terms = []
        for line in terms_str.split('\n'):
            terms.extend([t.strip() for t in line.split(',') if t.strip()])
        
        # Clear existing footnotes
        self.footnote_system.clear()
        
        # Process text
        processed_text, footnotes_section = self.footnote_system.process_text(text, terms)
        
        # Update outputs
        self.output_text.setText(processed_text)
        self.footnotes_preview.setText(footnotes_section)
        self._refresh_footnotes_list()
        
        QMessageBox.information(
            self,
            "Processed",
            f"Processed {len(terms)} terms. Added {len(self.footnote_system.footnotes)} footnotes."
        )
    
    def _copy_output(self) -> None:
        """Copy output text to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        
        # Combine text and footnotes
        text = self.output_text.toPlainText()
        footnotes = self.footnotes_preview.toPlainText()
        full_content = f"{text}\n\n---\n\n{footnotes}"
        
        clipboard.setText(full_content)
        QMessageBox.information(self, "Copied", "Output copied to clipboard.")
    
    def _copy_footnotes(self) -> None:
        """Copy footnotes section to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.footnotes_preview.toPlainText())
        QMessageBox.information(self, "Copied", "Footnotes section copied to clipboard.")
    
    def _clear_footnotes(self) -> None:
        """Clear all footnotes."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Clear all footnotes?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.footnote_system.clear()
            self._refresh_footnotes_list()
            self.footnotes_preview.clear()
    
    def _preview_footnotes(self) -> None:
        """Preview the footnotes section."""
        section = self.footnote_system.generate_footnotes_section()
        self.footnotes_preview.setText(section)
    
    def _refresh_footnotes_list(self) -> None:
        """Refresh the footnotes list."""
        self.footnotes_list.clear()
        for footnote in self.footnote_system.footnotes:
            item_text = f"[{footnote.marker}] {footnote.term}"
            if footnote.explanation:
                item_text += f" - {footnote.explanation[:50]}..."
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, footnote)
            self.footnotes_list.addItem(item)
    
    def _edit_footnote(self, item: QListWidgetItem) -> None:
        """Edit a footnote (double-click)."""
        footnote = item.data(Qt.UserRole)
        if footnote:
            self.term_input.setText(footnote.term)
            self.vault_link_input.setText(footnote.vault_link or "")
            self.explanation_input.setPlainText(footnote.explanation)
            # Set checkboxes for academic sources
            for source, cb in self.source_checkboxes.items():
                cb.setChecked(source in footnote.academic_links)
    
    def _clear_footnote_form(self) -> None:
        """Clear the footnote form."""
        self.term_input.clear()
        self.vault_link_input.clear()
        self.explanation_input.clear()
        for cb in self.source_checkboxes.values():
            cb.setChecked(False)
        self.source_checkboxes['stanford'].setChecked(True)

