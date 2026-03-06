"""
Theophysics Research Manager V2 - Sidebar Navigation Edition
Launch this for the enhanced UI with:
- Sidebar navigation (no horizontal tabs)
- Threaded scanning (no freezing)
- Configurable folder slots
- Dashboard with statistics
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from core.settings_manager import SettingsManager
from core.obsidian_definitions_manager import ObsidianDefinitionsManager
from core.vault_system_installer import VaultSystemInstaller
from core.global_analytics_aggregator import GlobalAnalyticsAggregator
from core.research_linker import ResearchLinker
from core.footnote_system import FootnoteSystem
from core.postgres_manager import PostgresManager, DatabaseConfig
from ui.main_window_v2 import create_main_window_v2


def main() -> None:
    """Launch the V2 application."""
    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)

    # Initialize Qt app
    app = QApplication(sys.argv)
    app.setApplicationName("Theophysics Research Manager V2")
    app.setStyle("Fusion")  # Consistent cross-platform look
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Load settings
    settings = SettingsManager(config_dir / "settings.ini")
    settings.load()

    # Initialize core systems
    definitions_manager = ObsidianDefinitionsManager(settings)
    vault_installer = VaultSystemInstaller(settings)
    global_aggregator = GlobalAnalyticsAggregator(vault_installer)
    research_linker = ResearchLinker(config_dir / "research_links.json")
    footnote_system = FootnoteSystem(
        research_linker,
        vault_path=definitions_manager.vault_path
    )
    
    # PostgreSQL manager
    postgres_manager = PostgresManager()
    db_host = settings.get("database", "host", "localhost")
    db_port = int(settings.get("database", "port", "5432"))
    db_name = settings.get("database", "database", "theophysics_research")
    db_user = settings.get("database", "user", "postgres")
    db_password = settings.get("database", "password", "")
    postgres_manager.config = DatabaseConfig(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )

    # Create and show the V2 window
    window = create_main_window_v2(
        settings=settings,
        definitions_manager=definitions_manager,
        vault_installer=vault_installer,
        global_aggregator=global_aggregator,
        research_linker=research_linker,
        footnote_system=footnote_system,
        postgres_manager=postgres_manager
    )
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
