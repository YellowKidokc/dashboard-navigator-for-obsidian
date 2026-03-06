"""
Theophysics Research Manager - Standalone GUI Application
Comprehensive research management system for Obsidian vaults
"""

from pathlib import Path
from PySide6.QtWidgets import QApplication

from core.settings_manager import SettingsManager
from core.obsidian_definitions_manager import ObsidianDefinitionsManager
from core.vault_system_installer import VaultSystemInstaller
from core.global_analytics_aggregator import GlobalAnalyticsAggregator
from core.research_linker import ResearchLinker
from core.footnote_system import FootnoteSystem
from core.postgres_manager import PostgresManager
from ui.main_window import create_main_window


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "config"
    config_dir.mkdir(exist_ok=True)

    # Settings
    settings = SettingsManager(config_dir / "settings.ini")
    settings.load()

    app = QApplication([])
    app.setApplicationName("Theophysics Research Manager")

    # Core systems
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
    # Load database config from settings
    db_host = settings.get("database", "host", "localhost")
    db_port = int(settings.get("database", "port", "5432"))
    db_name = settings.get("database", "database", "theophysics_research")
    db_user = settings.get("database", "user", "postgres")
    db_password = settings.get("database", "password", "")
    from core.postgres_manager import DatabaseConfig
    postgres_manager.config = DatabaseConfig(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )

    # Main window
    window = create_main_window(
        settings=settings,
        definitions_manager=definitions_manager,
        vault_installer=vault_installer,
        global_aggregator=global_aggregator,
        research_linker=research_linker,
        footnote_system=footnote_system,
        postgres_manager=postgres_manager
    )
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
