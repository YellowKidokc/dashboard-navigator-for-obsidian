"""
Settings Tab
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QHBoxLayout, QFileDialog, QMessageBox
)

from .base import BaseTab
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.settings_manager import SettingsManager
    from core.obsidian_definitions_manager import ObsidianDefinitionsManager


class SettingsTab(BaseTab):
    """Settings tab."""

    def __init__(self, settings: SettingsManager, definitions_manager: ObsidianDefinitionsManager):
        super().__init__()
        self.settings = settings
        self.definitions_manager = definitions_manager
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = QLabel("⚙️ Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Obsidian Settings
        obsidian_group = QGroupBox("📚 Obsidian Settings")
        obsidian_layout = QVBoxLayout()

        # Vault path
        vault_layout = QHBoxLayout()
        vault_layout.addWidget(QLabel("Vault Path:"))
        self.vault_path_edit = QLineEdit()
        current_vault = self.definitions_manager.vault_path
        if current_vault:
            self.vault_path_edit.setText(str(current_vault))
        vault_layout.addWidget(self.vault_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_layout.addWidget(browse_btn)
        obsidian_layout.addLayout(vault_layout)

        # Definitions folder
        def_folder_layout = QHBoxLayout()
        def_folder_layout.addWidget(QLabel("Definitions Folder:"))
        self.def_folder_edit = QLineEdit()
        self.def_folder_edit.setText(
            self.settings.get("obsidian", "definitions_folder", "definitions")
        )
        def_folder_layout.addWidget(self.def_folder_edit)
        obsidian_layout.addLayout(def_folder_layout)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)
        obsidian_layout.addWidget(save_btn)

        obsidian_group.setLayout(obsidian_layout)
        layout.addWidget(obsidian_group)

        layout.addStretch()

    def _browse_vault(self) -> None:
        """Browse for vault folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Obsidian Vault Folder",
            str(self.vault_path_edit.text()) if self.vault_path_edit.text() else ""
        )
        if folder:
            self.vault_path_edit.setText(folder)

    def _save_settings(self) -> None:
        """Save settings."""
        vault_path = self.vault_path_edit.text().strip()
        def_folder = self.def_folder_edit.text().strip()

        if vault_path:
            self.settings.set("obsidian", "vault_path", vault_path)
            self.definitions_manager.set_vault_path(vault_path)
        
        if def_folder:
            self.settings.set("obsidian", "definitions_folder", def_folder)

        QMessageBox.information(self, "Saved", "Settings saved successfully!")

