"""
Main Window - Obsidian Definitions Manager
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QLabel, 
    QStatusBar, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from typing import TYPE_CHECKING
from .styles import DARK_THEME_STYLESHEET

if TYPE_CHECKING:
    from core.settings_manager import SettingsManager
    from core.obsidian_definitions_manager import ObsidianDefinitionsManager
    from core.vault_system_installer import VaultSystemInstaller
    from core.global_analytics_aggregator import GlobalAnalyticsAggregator
    from core.research_linker import ResearchLinker
    from core.footnote_system import FootnoteSystem
    from core.postgres_manager import PostgresManager


class MainWindow(QMainWindow):
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

        self.setWindowTitle("🔬 Theophysics Research Manager")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the main user interface."""
        # Apply dark theme
        self.setStyleSheet(DARK_THEME_STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Title
        title = QLabel("🔬 Theophysics Research Manager")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Vault path selector
        vault_layout = QVBoxLayout()
        vault_label = QLabel("Obsidian Vault Path:")
        vault_layout.addWidget(vault_label)
        
        from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLineEdit
        vault_path_layout = QHBoxLayout()
        self.vault_path_edit = QLineEdit()
        self.vault_path_edit.setPlaceholderText("Select your Obsidian vault folder...")
        current_vault = self.definitions_manager.vault_path
        if current_vault:
            self.vault_path_edit.setText(str(current_vault))
        vault_path_layout.addWidget(self.vault_path_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_vault)
        vault_path_layout.addWidget(browse_btn)
        
        vault_layout.addLayout(vault_path_layout)
        layout.addLayout(vault_layout)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(True)
        layout.addWidget(self.tab_widget)

        # Add tabs
        self._add_tabs()

        # Add status bar
        self._setup_status_bar()

    def _browse_vault(self) -> None:
        """Browse for Obsidian vault folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Obsidian Vault Folder",
            str(self.vault_path_edit.text()) if self.vault_path_edit.text() else ""
        )
        if folder:
            self.vault_path_edit.setText(folder)
            self.definitions_manager.set_vault_path(folder)
            QMessageBox.information(
                self,
                "Vault Set",
                f"Vault path set to:\n{folder}\n\nScanning for definitions..."
            )
            # Refresh definitions view
            self._refresh_definitions_tab()

    def _add_tabs(self) -> None:
        """Add all tabs."""
        # Definitions tab
        from .tabs.definitions_tab import DefinitionsTab
        definitions_tab = DefinitionsTab(self.definitions_manager)
        self.tab_widget.addTab(definitions_tab, "Definitions")

        # Vault System tab
        from .tabs.vault_system_tab import VaultSystemTab
        vault_system_tab = VaultSystemTab(
            self.settings,
            self.vault_installer,
            self.global_aggregator
        )
        self.tab_widget.addTab(vault_system_tab, "🏗️ Vault System")

        # Data Aggregation tab
        from .tabs.data_aggregation_tab import DataAggregationTab
        data_aggregation_tab = DataAggregationTab()
        self.tab_widget.addTab(data_aggregation_tab, "🔗 Data Aggregation")

        # Research Linking tab
        from .tabs.research_linking_tab import ResearchLinkingTab
        research_linking_tab = ResearchLinkingTab(self.research_linker)
        self.tab_widget.addTab(research_linking_tab, "🔗 Research Links")

        # Footnote tab
        from .tabs.footnote_tab import FootnoteTab
        footnote_tab = FootnoteTab(
            self.footnote_system,
            self.research_linker,
            self.definitions_manager
        )
        self.tab_widget.addTab(footnote_tab, "📝 Footnotes")

        # TTS-Ready Pipeline tab
        from .tabs.tts_tab import TTSTab
        tts_tab = TTSTab()
        self.tab_widget.addTab(tts_tab, "🎙️ TTS Pipeline")

        # Database tab
        from .tabs.database_tab import DatabaseTab
        database_tab = DatabaseTab(self.postgres_manager)
        self.tab_widget.addTab(database_tab, "🗄️ Database")

        # Settings tab
        from .tabs.settings_tab import SettingsTab
        settings_tab = SettingsTab(self.settings, self.definitions_manager)
        self.tab_widget.addTab(settings_tab, "Settings")

    def _refresh_definitions_tab(self) -> None:
        """Refresh the definitions tab."""
        definitions_tab = self.tab_widget.widget(0)
        if hasattr(definitions_tab, 'refresh'):
            definitions_tab.refresh()

    def _setup_status_bar(self) -> None:
        """Setup the status bar."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Vault status
        if self.definitions_manager.vault_path:
            self.status_bar.showMessage(
                f"Vault: {self.definitions_manager.vault_path.name} | "
                f"Definitions: {len(self.definitions_manager.get_all_definitions())}"
            )


def create_main_window(
    settings: SettingsManager,
    definitions_manager: ObsidianDefinitionsManager,
    vault_installer: VaultSystemInstaller,
    global_aggregator: GlobalAnalyticsAggregator,
    research_linker: ResearchLinker,
    footnote_system: FootnoteSystem,
    postgres_manager: PostgresManager
) -> MainWindow:
    return MainWindow(
        settings=settings,
        definitions_manager=definitions_manager,
        vault_installer=vault_installer,
        global_aggregator=global_aggregator,
        research_linker=research_linker,
        footnote_system=footnote_system,
        postgres_manager=postgres_manager
    )

