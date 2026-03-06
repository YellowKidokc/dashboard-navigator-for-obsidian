"""
Vault System Installer Tab
GUI for installing and managing vault analytics systems
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QGroupBox,
    QMessageBox, QFileDialog, QCheckBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt

from .base import BaseTab
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.settings_manager import SettingsManager
    from core.vault_system_installer import VaultSystemInstaller
    from core.global_analytics_aggregator import GlobalAnalyticsAggregator


class VaultSystemTab(BaseTab):
    """Tab for installing and managing vault analytics systems."""

    def __init__(
        self,
        settings: SettingsManager,
        installer: VaultSystemInstaller,
        aggregator: GlobalAnalyticsAggregator
    ):
        super().__init__()
        self.settings = settings
        self.installer = installer
        self.aggregator = aggregator
        self._build_ui()
        self.refresh_instances()

    def _build_ui(self) -> None:
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title = QLabel("🏗️ Vault Analytics System Installer")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT: Install new system
        install_widget = QWidget()
        install_layout = QVBoxLayout(install_widget)

        install_group = QGroupBox("📦 Install New System")
        install_group_layout = QVBoxLayout()

        # Vault path
        vault_layout = QHBoxLayout()
        vault_layout.addWidget(QLabel("Vault Path:"))
        self.vault_path_edit = QLineEdit()
        self.vault_path_edit.setPlaceholderText("Select vault folder to install system...")
        vault_layout.addWidget(self.vault_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_layout.addWidget(browse_btn)
        install_group_layout.addLayout(vault_layout)

        # Vault name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Vault Name:"))
        self.vault_name_edit = QLineEdit()
        self.vault_name_edit.setPlaceholderText("Auto-detected from folder name")
        name_layout.addWidget(self.vault_name_edit)
        install_group_layout.addLayout(name_layout)

        # Global analytics
        self.global_analytics_check = QCheckBox("Enable Global Analytics")
        self.global_analytics_check.setChecked(True)
        install_group_layout.addWidget(self.global_analytics_check)

        # Install button
        install_btn = QPushButton("🚀 Install System")
        install_btn.setStyleSheet("padding: 10px; font-weight: bold; font-size: 12pt;")
        install_btn.clicked.connect(self._install_system)
        install_group_layout.addWidget(install_btn)

        install_group.setLayout(install_group_layout)
        install_layout.addWidget(install_group)

        # Global Analytics
        global_group = QGroupBox("🌐 Global Analytics")
        global_layout = QVBoxLayout()

        aggregate_btn = QPushButton("📊 Aggregate All Instances")
        aggregate_btn.clicked.connect(self._aggregate_all)
        global_layout.addWidget(aggregate_btn)

        self.global_status = QTextEdit()
        self.global_status.setReadOnly(True)
        self.global_status.setMaximumHeight(150)
        global_layout.addWidget(self.global_status)

        global_group.setLayout(global_layout)
        install_layout.addWidget(global_group)

        install_layout.addStretch()

        # RIGHT: Installed instances
        instances_widget = QWidget()
        instances_layout = QVBoxLayout(instances_widget)

        instances_label = QLabel("📋 Installed Instances:")
        instances_layout.addWidget(instances_label)

        self.instances_list = QListWidget()
        self.instances_list.itemDoubleClicked.connect(self._view_instance)
        instances_layout.addWidget(self.instances_list)

        # Instance actions
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_instances)
        actions_layout.addWidget(refresh_btn)

        view_btn = QPushButton("👁️ View")
        view_btn.clicked.connect(self._view_instance)
        actions_layout.addWidget(view_btn)

        unregister_btn = QPushButton("❌ Unregister")
        unregister_btn.clicked.connect(self._unregister_instance)
        actions_layout.addWidget(unregister_btn)

        instances_layout.addLayout(actions_layout)

        # Instance details
        self.instance_details = QTextEdit()
        self.instance_details.setReadOnly(True)
        self.instance_details.setMaximumHeight(200)
        instances_layout.addWidget(self.instance_details)

        instances_layout.addStretch()

        # Add to splitter
        splitter.addWidget(install_widget)
        splitter.addWidget(instances_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)

    def _browse_vault(self) -> None:
        """Browse for vault folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Vault Folder",
            str(self.vault_path_edit.text()) if self.vault_path_edit.text() else ""
        )
        if folder:
            self.vault_path_edit.setText(folder)
            # Auto-fill vault name
            if not self.vault_name_edit.text():
                from pathlib import Path
                self.vault_name_edit.setText(Path(folder).name)

    def _install_system(self) -> None:
        """Install the vault analytics system."""
        vault_path = self.vault_path_edit.text().strip()
        vault_name = self.vault_name_edit.text().strip() or None
        enable_global = self.global_analytics_check.isChecked()

        if not vault_path:
            QMessageBox.warning(self, "Validation", "Please select a vault path.")
            return

        try:
            from pathlib import Path
            instance = self.installer.install_system(
                vault_path=Path(vault_path),
                vault_name=vault_name,
                enable_global_analytics=enable_global
            )

            QMessageBox.information(
                self,
                "Installation Complete",
                f"Vault analytics system installed successfully!\n\n"
                f"Instance ID: {instance.instance_id}\n"
                f"Vault: {instance.vault_name}\n"
                f"Location: {instance.vault_path}\n\n"
                f"Global Analytics: {'Enabled' if enable_global else 'Disabled'}"
            )

            # Clear form
            self.vault_path_edit.clear()
            self.vault_name_edit.clear()
            
            # Refresh instances list
            self.refresh_instances()

        except Exception as e:
            QMessageBox.critical(self, "Installation Failed", f"Error: {str(e)}")

    def refresh_instances(self) -> None:
        """Refresh the instances list."""
        self.instances_list.clear()
        instances = self.installer.list_instances()
        
        for instance in instances:
            item = QListWidgetItem(f"{instance.vault_name} ({instance.instance_id})")
            item.setData(Qt.ItemDataRole.UserRole, instance)
            status = "🌐 Global" if instance.global_analytics_enabled else "📁 Local"
            item.setText(f"{status} | {instance.vault_name}")
            self.instances_list.addItem(item)

    def _view_instance(self) -> None:
        """View instance details."""
        current_item = self.instances_list.currentItem()
        if not current_item:
            return
        
        instance = current_item.data(Qt.ItemDataRole.UserRole)
        if instance:
            details = f"""Instance ID: {instance.instance_id}
Vault Name: {instance.vault_name}
Vault Path: {instance.vault_path}
Installed: {instance.installed_date}
Version: {instance.version}
Global Analytics: {'Enabled' if instance.global_analytics_enabled else 'Disabled'}
Features: {', '.join(instance.features_enabled)}
Master Sheets: {instance.master_sheets_path}
Data Analytics: {instance.data_analytics_path}
"""
            self.instance_details.setPlainText(details)

    def _unregister_instance(self) -> None:
        """Unregister an instance."""
        current_item = self.instances_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select an instance to unregister.")
            return
        
        instance = current_item.data(Qt.ItemDataRole.UserRole)
        if instance:
            reply = QMessageBox.question(
                self, "Confirm Unregister",
                f"Unregister instance '{instance.vault_name}'?\n\n"
                f"This will not delete files, only remove it from the registry.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.installer.unregister_instance(instance.instance_id):
                    QMessageBox.information(self, "Success", "Instance unregistered.")
                    self.refresh_instances()
                else:
                    QMessageBox.warning(self, "Error", "Failed to unregister instance.")

    def _aggregate_all(self) -> None:
        """Aggregate all instances."""
        try:
            self.global_status.append("Starting global aggregation...")
            result = self.aggregator.aggregate_all()
            
            if "error" in result:
                self.global_status.append(f"Error: {result['error']}")
            else:
                self.global_status.append(f"✅ Aggregation complete!")
                self.global_status.append(f"Instances: {result['instances_count']}")
                self.global_status.append(f"Vaults: {', '.join(result['instances'])}")
                self.global_status.append("\nMaster Sheets:")
                
                for sheet_type, data in result["master_sheets"].items():
                    self.global_status.append(
                        f"  • {sheet_type}: {data['total_unique_items']} items"
                    )
                
                QMessageBox.information(
                    self,
                    "Aggregation Complete",
                    f"Global analytics aggregated from {result['instances_count']} instances.\n\n"
                    f"Results saved to: {self.aggregator.global_output_path}"
                )
        except Exception as e:
            self.global_status.append(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Aggregation Failed", f"Error: {str(e)}")

