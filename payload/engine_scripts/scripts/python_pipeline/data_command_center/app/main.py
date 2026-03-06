"""
Data Command Center - Main Entry Point

Personal Scientific OS for dataset ingestion, S/G/O computation,
and academic reproducibility tracking.
"""

import logging
import sys
import threading
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def load_settings() -> dict:
    """Load application settings from YAML."""
    settings_path = get_project_root() / "app" / "config" / "settings.yaml"
    if settings_path.exists():
        with open(settings_path, "r") as f:
            return yaml.safe_load(f)
    return {}


class DataCommandCenter:
    """Main application controller."""

    def __init__(self):
        self.root = get_project_root()
        self.settings = load_settings()

        # Initialize core components
        self._init_components()

    def _init_components(self) -> None:
        """Initialize all core components."""
        from .core.script_loader import ScriptLoader
        from .core.connections import ConnectionResolver
        from .core.runner import ScriptRunner
        from .core.scheduler import Scheduler

        # Paths
        scripts_dir = self.root / self.settings.get("paths", {}).get("scripts_dir", "scripts")
        logs_dir = self.root / self.settings.get("paths", {}).get("logs_dir", "logs")
        connections_path = self.root / "app" / "config" / "connections.yaml"
        schedules_path = self.root / "logs" / "schedules.json"

        # Components
        self.script_loader = ScriptLoader(scripts_dir)
        self.connection_resolver = ConnectionResolver(connections_path)
        self.runner = ScriptRunner(self.connection_resolver, logs_dir)
        self.scheduler = Scheduler(
            schedules_path,
            self.settings.get("scheduler", {}).get("check_interval_seconds", 60),
        )

        # Set scheduler callback
        self.scheduler.set_run_callback(self._scheduled_run)

        # Discover scripts
        self.script_loader.discover()

        # Load run history
        self.runner.load_history_from_logs()

        logger.info(f"Loaded {len(self.script_loader.list_scripts())} scripts")
        logger.info(f"Available connections: {self.connection_resolver.list_connections()}")

    def _scheduled_run(self, script_name: str, config: dict, target_db: str) -> None:
        """Execute a scheduled run."""
        script = self.script_loader.get_script(script_name)
        if script is None:
            logger.error(f"Scheduled script not found: {script_name}")
            return

        logger.info(f"Executing scheduled run: {script_name}")
        result = self.runner.run(script, config, target_db)

        if self.window:
            # Update GUI from scheduler thread
            self.window.after(0, lambda: self.window.show_run_result(result.to_dict()))
            self.window.after(0, lambda: self.window.log_message(
                f"Scheduled run completed: {script_name}",
                "SUCCESS" if result.status == "success" else "ERROR"
            ))

    def run_gui(self) -> None:
        """Run the GUI application."""
        from .gui.app_window import AppWindow

        self.window = AppWindow()

        # Set callbacks
        self.window.set_run_callback(self._handle_run)
        self.window.set_schedule_callback(self._handle_schedule)
        self.window.set_refresh_callback(self._handle_refresh)
        
        # Pass connection resolver for Postgres tab
        self.window.set_connection_resolver(self.connection_resolver)

        # Populate initial data
        self._refresh_scripts()
        self.window.set_connections(self.connection_resolver.list_connections())

        # Start scheduler
        if self.settings.get("scheduler", {}).get("enabled", True):
            self.scheduler.start()
            self.window.set_scheduler_status(True)

        self.window.log_message("Data Command Center started", "INFO")
        self.window.log_message(f"Found {len(self.script_loader.list_scripts())} scripts", "INFO")

        # Run main loop
        try:
            self.window.mainloop()
        finally:
            self.scheduler.stop()

    def _handle_run(self, script_name: str, config: dict, target_db: str) -> None:
        """Handle run request from GUI."""
        script = self.script_loader.get_script(script_name)
        if script is None:
            self.window.log_message(f"Script not found: {script_name}", "ERROR")
            return

        self.window.log_message(f"Starting {script_name}...", "INFO")

        # Run in background thread to keep GUI responsive
        def run_thread():
            try:
                result = self.runner.run(script, config, target_db)

                # Update GUI from main thread
                self.window.after(0, lambda: self.window.show_run_result(result.to_dict()))
                self.window.after(0, lambda: self.window.set_status("Ready"))

            except Exception as e:
                self.window.after(0, lambda: self.window.log_message(str(e), "ERROR"))
                self.window.after(0, lambda: self.window.set_status("Error"))

        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()

    def _handle_schedule(
        self,
        script_name: str,
        config: dict,
        target_db: str,
        interval: int,
    ) -> None:
        """Handle schedule request from GUI."""
        self.scheduler.add_schedule(
            script_name=script_name,
            config=config,
            target_db=target_db,
            interval_minutes=interval,
        )
        self.window.log_message(
            f"Scheduled {script_name} to run every {interval} minutes",
            "INFO",
        )

    def _handle_refresh(self) -> None:
        """Handle refresh request from GUI."""
        self._refresh_scripts()

    def _refresh_scripts(self) -> None:
        """Refresh the script list."""
        scripts = self.script_loader.discover()

        script_list = [
            {
                "name": info.name,
                "version": info.version,
                "spec": info.spec,
            }
            for info in scripts.values()
        ]

        self.window.set_scripts(script_list)


def main():
    """Main entry point."""
    try:
        app = DataCommandCenter()
        app.run_gui()
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()
