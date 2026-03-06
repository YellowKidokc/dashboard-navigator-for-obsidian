"""
Research Linking Tab - GUI for managing research links and auto-linking.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QSplitter, QGroupBox, QCheckBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.research_linker import ResearchLinker


class ResearchLinkingTab(QWidget):
    """Tab for managing research links and auto-linking text."""
    
    def __init__(self, research_linker: ResearchLinker):
        super().__init__()
        self.research_linker = research_linker
        self._setup_ui()
        self._load_custom_links()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🔗 Research Linking System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel: Link management
        left_panel = self._create_link_management_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Text processing
        right_panel = self._create_text_processing_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
    
    def _create_link_management_panel(self) -> QWidget:
        """Create the left panel for managing links."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Add custom link section
        add_group = QGroupBox("Add Custom Link")
        add_layout = QVBoxLayout()
        
        # Term input
        term_label = QLabel("Term:")
        add_layout.addWidget(term_label)
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("e.g., 'quantum mechanics'")
        add_layout.addWidget(self.term_input)
        
        # Source selection
        source_label = QLabel("Source:")
        add_layout.addWidget(source_label)
        self.source_combo = QComboBox()
        # Get all available sources from linker
        all_sources = list(self.research_linker.LINK_TEMPLATES.keys())
        self.source_combo.addItems(sorted(all_sources) + ['custom'])
        add_layout.addWidget(self.source_combo)
        
        # URL input
        url_label = QLabel("URL:")
        add_layout.addWidget(url_label)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        add_layout.addWidget(self.url_input)
        
        # Add button
        add_btn = QPushButton("➕ Add Link")
        add_btn.clicked.connect(self._add_custom_link)
        add_layout.addWidget(add_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Test link section
        test_group = QGroupBox("Test Link")
        test_layout = QVBoxLayout()
        
        test_term_label = QLabel("Term to test:")
        test_layout.addWidget(test_term_label)
        self.test_term_input = QLineEdit()
        self.test_term_input.setPlaceholderText("Enter term...")
        self.test_term_input.returnPressed.connect(self._test_link)
        test_layout.addWidget(self.test_term_input)
        
        test_btn = QPushButton("🔍 Test")
        test_btn.clicked.connect(self._test_link)
        test_layout.addWidget(test_btn)
        
        self.test_result = QTextEdit()
        self.test_result.setReadOnly(True)
        self.test_result.setMaximumHeight(150)
        test_layout.addWidget(self.test_result)
        
        test_group.setLayout(test_layout)
        layout.addWidget(test_group)
        
        # Custom links table
        table_label = QLabel("Custom Links:")
        layout.addWidget(table_label)
        
        self.links_table = QTableWidget()
        self.links_table.setColumnCount(3)
        self.links_table.setHorizontalHeaderLabels(["Term", "Source", "URL"])
        self.links_table.horizontalHeader().setStretchLastSection(True)
        self.links_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.links_table)
        
        # Delete button
        delete_btn = QPushButton("🗑️ Delete Selected")
        delete_btn.clicked.connect(self._delete_selected_link)
        layout.addWidget(delete_btn)
        
        # Priority configuration section
        priority_group = QGroupBox("🔀 Link Priority Order (Cascade)")
        priority_layout = QVBoxLayout()
        
        priority_info = QLabel("Drag to reorder. Higher sources are tried first.")
        priority_info.setStyleSheet("font-size: 10px; color: #888;")
        priority_layout.addWidget(priority_info)
        
        self.priority_list = QListWidget()
        self.priority_list.setDragDropMode(QListWidget.InternalMove)
        self._load_priority_list()
        priority_layout.addWidget(self.priority_list)
        
        # Priority buttons
        priority_btn_layout = QHBoxLayout()
        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.clicked.connect(self._reset_priority)
        priority_btn_layout.addWidget(reset_btn)
        
        save_priority_btn = QPushButton("💾 Save Priority")
        save_priority_btn.clicked.connect(self._save_priority)
        priority_btn_layout.addWidget(save_priority_btn)
        priority_layout.addLayout(priority_btn_layout)
        
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)
        
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
        self.input_text.setPlaceholderText("Paste text here to add research links...")
        input_layout.addWidget(self.input_text)
        
        # Terms to link
        terms_label = QLabel("Terms to link (comma-separated):")
        input_layout.addWidget(terms_label)
        self.terms_input = QLineEdit()
        self.terms_input.setPlaceholderText("quantum mechanics, general relativity, consciousness")
        input_layout.addWidget(self.terms_input)
        
        # Process button
        process_btn = QPushButton("🔗 Process & Add Links")
        process_btn.clicked.connect(self._process_text)
        input_layout.addWidget(process_btn)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("Output (with links)")
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
        
        # Generate link section
        section_group = QGroupBox("Generate Link Section")
        section_layout = QVBoxLayout()
        
        section_terms_label = QLabel("Terms (one per line):")
        section_layout.addWidget(section_terms_label)
        self.section_terms_input = QTextEdit()
        self.section_terms_input.setPlaceholderText("quantum mechanics\ngeneral relativity\nconsciousness")
        self.section_terms_input.setMaximumHeight(100)
        section_layout.addWidget(self.section_terms_input)
        
        section_title_label = QLabel("Section Title:")
        section_layout.addWidget(section_title_label)
        self.section_title_input = QLineEdit()
        self.section_title_input.setText("Research Links")
        section_layout.addWidget(self.section_title_input)
        
        generate_btn = QPushButton("📝 Generate Link Section")
        generate_btn.clicked.connect(self._generate_link_section)
        section_layout.addWidget(generate_btn)
        
        self.section_output = QTextEdit()
        self.section_output.setReadOnly(True)
        section_layout.addWidget(self.section_output)
        
        section_group.setLayout(section_layout)
        layout.addWidget(section_group)
        
        return panel
    
    def _add_custom_link(self) -> None:
        """Add a custom link."""
        term = self.term_input.text().strip()
        source = self.source_combo.currentText()
        url = self.url_input.text().strip()
        
        if not term or not url:
            QMessageBox.warning(self, "Missing Information", "Please enter both term and URL.")
            return
        
        self.research_linker.add_custom_link(term, source, url)
        self._load_custom_links()
        
        # Clear inputs
        self.term_input.clear()
        self.url_input.clear()
        
        QMessageBox.information(self, "Success", f"Added link for '{term}' from {source}.")
    
    def _test_link(self) -> None:
        """Test link generation for a term."""
        term = self.test_term_input.text().strip()
        if not term:
            return
        
        links = self.research_linker.get_all_links_for_term(term)
        
        if links:
            result = f"Links for '{term}':\n\n"
            for source, url in sorted(links.items()):
                source_name = source.replace('_', ' ').title()
                result += f"• {source_name}: {url}\n"
        else:
            result = f"No links found for '{term}'.\n\n"
            result += "You can add a custom link using the form on the left."
        
        self.test_result.setText(result)
    
    def _process_text(self) -> None:
        """Process input text and add links."""
        text = self.input_text.toPlainText()
        terms_str = self.terms_input.text().strip()
        
        if not text:
            QMessageBox.warning(self, "No Text", "Please enter text to process.")
            return
        
        if not terms_str:
            QMessageBox.warning(self, "No Terms", "Please specify terms to link.")
            return
        
        # Parse terms
        terms = [t.strip() for t in terms_str.split(',') if t.strip()]
        
        # Process text
        result = self.research_linker.process_text_for_links(text, terms)
        self.output_text.setText(result)
    
    def _copy_output(self) -> None:
        """Copy output text to clipboard."""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.output_text.toPlainText())
        QMessageBox.information(self, "Copied", "Output copied to clipboard.")
    
    def _generate_link_section(self) -> None:
        """Generate a markdown link section."""
        terms_str = self.section_terms_input.toPlainText().strip()
        title = self.section_title_input.text().strip() or "Research Links"
        
        if not terms_str:
            QMessageBox.warning(self, "No Terms", "Please enter terms (one per line).")
            return
        
        # Parse terms
        terms = [t.strip() for t in terms_str.split('\n') if t.strip()]
        
        # Generate section
        section = self.research_linker.generate_link_section(terms, title)
        self.section_output.setText(section)
    
    def _load_custom_links(self) -> None:
        """Load custom links into the table."""
        custom_links = self.research_linker.custom_links
        
        self.links_table.setRowCount(0)
        
        for term, sources in custom_links.items():
            for source, url in sources.items():
                row = self.links_table.rowCount()
                self.links_table.insertRow(row)
                self.links_table.setItem(row, 0, QTableWidgetItem(term))
                self.links_table.setItem(row, 1, QTableWidgetItem(source))
                self.links_table.setItem(row, 2, QTableWidgetItem(url))
    
    def _delete_selected_link(self) -> None:
        """Delete selected link from custom links."""
        selected_rows = self.links_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a link to delete.")
            return
        
        # Get selected term and source
        row = selected_rows[0].row()
        term = self.links_table.item(row, 0).text()
        source = self.links_table.item(row, 1).text()
        
        # Remove from custom links
        if term in self.research_linker.custom_links:
            if source in self.research_linker.custom_links[term]:
                del self.research_linker.custom_links[term][source]
                if not self.research_linker.custom_links[term]:
                    del self.research_linker.custom_links[term]
                self.research_linker._save_custom_links()
                self._load_custom_links()
                QMessageBox.information(self, "Deleted", f"Deleted link for '{term}' from {source}.")
    
    def _load_priority_list(self) -> None:
        """Load priority order into the list widget."""
        self.priority_list.clear()
        priority = self.research_linker.get_priority_order()
        
        for source in priority:
            if source in self.research_linker.LINK_TEMPLATES:
                template = self.research_linker.LINK_TEMPLATES[source]
                display_name = template.get('display_name', source.replace('_', ' ').title())
                item = QListWidgetItem(f"{display_name} ({source})")
                item.setData(Qt.UserRole, source)
                self.priority_list.addItem(item)
    
    def _save_priority(self) -> None:
        """Save the current priority order from the list."""
        priority = []
        for i in range(self.priority_list.count()):
            item = self.priority_list.item(i)
            source = item.data(Qt.UserRole)
            if source:
                priority.append(source)
        
        if priority:
            self.research_linker.set_priority_order(priority)
            QMessageBox.information(self, "Saved", "Priority order saved successfully.")
    
    def _reset_priority(self) -> None:
        """Reset priority to default order."""
        reply = QMessageBox.question(
            self,
            "Reset Priority",
            "Reset to default cascade order?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.research_linker.set_priority_order(self.research_linker.DEFAULT_LINK_PRIORITY)
            self._load_priority_list()
            QMessageBox.information(self, "Reset", "Priority order reset to default.")

