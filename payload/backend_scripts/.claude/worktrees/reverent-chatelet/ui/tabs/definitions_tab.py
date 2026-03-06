"""
Definitions Tab - Main interface for managing definitions
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QTextEdit, QGroupBox,
    QMessageBox, QSplitter, QHeaderView, QListWidget, QListWidgetItem,
    QComboBox
)
from PySide6.QtCore import Qt

from .base import BaseTab
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.obsidian_definitions_manager import ObsidianDefinitionsManager


class DefinitionsTab(BaseTab):
    """Tab for managing definitions."""

    def __init__(self, definitions_manager: ObsidianDefinitionsManager):
        super().__init__()
        self.definitions_manager = definitions_manager
        self._current_definition = None
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("Definitions Manager")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: Definitions list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)

        list_label = QLabel("All Definitions:")
        list_layout.addWidget(list_label)

        self.definitions_list = QListWidget()
        self.definitions_list.itemSelectionChanged.connect(self._on_definition_selected)
        self.definitions_list.itemDoubleClicked.connect(self._on_definition_selected)
        list_layout.addWidget(self.definitions_list)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        list_layout.addWidget(refresh_btn)

        # RIGHT: Definition editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        editor_label = QLabel("Definition Editor:")
        editor_layout.addWidget(editor_label)

        # Phrase
        phrase_layout = QHBoxLayout()
        phrase_layout.addWidget(QLabel("Phrase:"))
        self.phrase_edit = QLineEdit()
        self.phrase_edit.setPlaceholderText("Word or phrase to define")
        self.phrase_edit.setMinimumHeight(35)
        self.phrase_edit.setStyleSheet("font-size: 11pt; padding: 6px;")
        phrase_layout.addWidget(self.phrase_edit)
        editor_layout.addLayout(phrase_layout)

        # Aliases
        aliases_layout = QHBoxLayout()
        aliases_layout.addWidget(QLabel("Aliases (comma-separated):"))
        self.aliases_edit = QLineEdit()
        self.aliases_edit.setPlaceholderText("alias1, alias2, alias3")
        self.aliases_edit.setMinimumHeight(35)
        self.aliases_edit.setStyleSheet("font-size: 11pt; padding: 6px;")
        aliases_layout.addWidget(self.aliases_edit)
        editor_layout.addLayout(aliases_layout)
        
        # Classification
        classification_layout = QHBoxLayout()
        classification_layout.addWidget(QLabel("Classification:"))
        self.classification_combo = QComboBox()
        self.classification_combo.addItems([
            "", "Theory", "Proper Name", "Scientific Method", 
            "Mathematical Formalism", "Regular Word", "Domain Term",
            "Concept", "Principle", "Law", "Axiom"
        ])
        self.classification_combo.setEditable(True)  # Allow custom classifications
        self.classification_combo.setMinimumHeight(35)
        self.classification_combo.setStyleSheet("font-size: 11pt; padding: 6px;")
        classification_layout.addWidget(self.classification_combo)
        editor_layout.addLayout(classification_layout)
        
        # Folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Folder (Domain):"))
        self.folder_combo = QComboBox()
        self.folder_combo.addItems([
            "", "physics", "theories", "terms", "mathematics",
            "philosophy", "theology", "concepts", "principles"
        ])
        self.folder_combo.setEditable(True)  # Allow custom folders
        self.folder_combo.setMinimumHeight(35)
        self.folder_combo.setStyleSheet("font-size: 11pt; padding: 6px;")
        folder_layout.addWidget(self.folder_combo)
        editor_layout.addLayout(folder_layout)

        # Definition
        def_layout = QVBoxLayout()
        def_layout.addWidget(QLabel("Definition:"))
        self.definition_edit = QTextEdit()
        self.definition_edit.setPlaceholderText("Enter the definition here...")
        self.definition_edit.setMinimumHeight(300)
        def_layout.addWidget(self.definition_edit)
        editor_layout.addLayout(def_layout)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.add_save_btn = QPushButton("Add/Save")
        self.add_save_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        self.add_save_btn.clicked.connect(self._add_save_definition)
        buttons_layout.addWidget(self.add_save_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_definition)
        buttons_layout.addWidget(delete_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_form)
        buttons_layout.addWidget(clear_btn)

        buttons_layout.addStretch()
        editor_layout.addLayout(buttons_layout)

        editor_layout.addStretch()

        # Add to splitter
        splitter.addWidget(list_widget)
        splitter.addWidget(editor_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def refresh(self) -> None:
        """Refresh the definitions list."""
        self.definitions_manager.scan_definitions()
        definitions = self.definitions_manager.get_all_definitions()
        
        self.definitions_list.clear()
        for def_obj in definitions:
            item = QListWidgetItem(def_obj.phrase)
            item.setData(Qt.ItemDataRole.UserRole, def_obj)
            if def_obj.aliases:
                item.setToolTip(f"Aliases: {', '.join(def_obj.aliases)}")
            self.definitions_list.addItem(item)

    def _on_definition_selected(self) -> None:
        """Handle definition selection."""
        current_item = self.definitions_list.currentItem()
        if current_item:
            def_obj = current_item.data(Qt.ItemDataRole.UserRole)
            if def_obj:
                self._current_definition = def_obj
                self.phrase_edit.setText(def_obj.phrase)
                self.aliases_edit.setText(', '.join(def_obj.aliases))
                self.definition_edit.setPlainText(def_obj.definition)
                # Set classification and folder if they exist
                if hasattr(def_obj, 'classification'):
                    index = self.classification_combo.findText(def_obj.classification)
                    if index >= 0:
                        self.classification_combo.setCurrentIndex(index)
                    else:
                        self.classification_combo.setCurrentText(def_obj.classification)
                if hasattr(def_obj, 'folder'):
                    index = self.folder_combo.findText(def_obj.folder)
                    if index >= 0:
                        self.folder_combo.setCurrentIndex(index)
                    else:
                        self.folder_combo.setCurrentText(def_obj.folder)
                self.add_save_btn.setText("Save")

    def _add_save_definition(self) -> None:
        """Add or save a definition."""
        phrase = self.phrase_edit.text().strip()
        definition = self.definition_edit.toPlainText().strip()
        aliases_str = self.aliases_edit.text().strip()
        aliases = [a.strip() for a in aliases_str.split(',') if a.strip()] if aliases_str else []
        classification = self.classification_combo.currentText().strip()
        folder = self.folder_combo.currentText().strip()

        if not phrase:
            QMessageBox.warning(self, "Validation", "Phrase is required.")
            return

        if not definition:
            QMessageBox.warning(self, "Validation", "Definition is required.")
            return

        try:
            if self._current_definition:
                # Update existing
                success = self.definitions_manager.update_definition(
                    self._current_definition.phrase,
                    phrase,
                    definition,
                    aliases,
                    classification=classification,
                    folder=folder
                )
                if success:
                    QMessageBox.information(self, "Success", "Definition updated!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to update definition.")
            else:
                # Add new
                success = self.definitions_manager.add_definition(
                    phrase, definition, aliases,
                    classification=classification,
                    folder=folder
                )
                if success:
                    QMessageBox.information(self, "Success", "Definition added!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to add definition.")

            self.refresh()
            self._clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")

    def _delete_definition(self) -> None:
        """Delete the selected definition."""
        if not self._current_definition:
            QMessageBox.warning(self, "No Selection", "Please select a definition to delete.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete definition '{self._current_definition.phrase}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.definitions_manager.delete_definition(self._current_definition.phrase)
            if success:
                QMessageBox.information(self, "Success", "Definition deleted!")
                self.refresh()
                self._clear_form()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete definition.")

    def _clear_form(self) -> None:
        """Clear the editor form."""
        self._current_definition = None
        self.phrase_edit.clear()
        self.aliases_edit.clear()
        self.definition_edit.clear()
        self.classification_combo.setCurrentIndex(0)
        self.folder_combo.setCurrentIndex(0)
        self.add_save_btn.setText("Add/Save")
        self.definitions_list.clearSelection()

