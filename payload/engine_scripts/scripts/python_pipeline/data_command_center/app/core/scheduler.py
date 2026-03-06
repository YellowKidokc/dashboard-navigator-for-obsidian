"""
Scheduler - Simple timer-based script runner

Responsibilities:
- Store schedules as data (JSON/YAML)
- Background thread checks due runs
- Execute scripts when scheduled

Design: No cron, no external orchestrator. Simple by design.
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ScheduleEntry:
    """A scheduled script run."""

    id: str
    script_name: str
    config: dict[str, Any]
    target_db: str
    interval_minutes: int
    enabled: bool = True
    last_run: datetime | None = None
    next_run: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.next_run is None and self.enabled:
            self.next_run = datetime.now()

    def is_due(self) -> bool:
        """Check if this schedule is due for execution."""
        if not self.enabled:
            return False
        if self.next_run is None:
            return False
        return datetime.now() >= self.next_run

    def mark_run(self) -> None:
        """Mark this schedule as having just run."""
        self.last_run = datetime.now()
        self.next_run = self.last_run + timedelta(minutes=self.interval_minutes)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "script_name": self.script_name,
            "config": self.config,
            "target_db": self.target_db,
            "interval_minutes": self.interval_minutes,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduleEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            script_name=data["script_name"],
            config=data["config"],
            target_db=data["target_db"],
            interval_minutes=data["interval_minutes"],
            enabled=data.get("enabled", True),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
        )


class Scheduler:
    """
    Simple timer-based scheduler for script execution.

    Runs as a background thread, checking for due schedules at regular intervals.
    """

    def __init__(
        self,
        schedules_file: Path,
        check_interval_seconds: int = 60,
    ):
        self.schedules_file = Path(schedules_file)
        self.check_interval = check_interval_seconds
        self._schedules: dict[str, ScheduleEntry] = {}
        self._run_callback: Callable[[str, dict, str], None] | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        self._load_schedules()

    def set_run_callback(
        self,
        callback: Callable[[str, dict, str], None],
    ) -> None:
        """
        Set the callback to execute when a schedule is due.

        Args:
            callback: Function taking (script_name, config, target_db)
        """
        self._run_callback = callback

    def add_schedule(
        self,
        script_name: str,
        config: dict[str, Any],
        target_db: str,
        interval_minutes: int,
        schedule_id: str | None = None,
    ) -> ScheduleEntry:
        """
        Add a new schedule.

        Args:
            script_name: Name of the script to run.
            config: Configuration for the script.
            target_db: Target database connection name.
            interval_minutes: Interval between runs in minutes.
            schedule_id: Optional custom ID (auto-generated if None).

        Returns:
            The created ScheduleEntry.
        """
        if schedule_id is None:
            schedule_id = f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        entry = ScheduleEntry(
            id=schedule_id,
            script_name=script_name,
            config=config,
            target_db=target_db,
            interval_minutes=interval_minutes,
        )

        with self._lock:
            self._schedules[schedule_id] = entry
            self._save_schedules()

        logger.info(f"Added schedule: {schedule_id} (every {interval_minutes} min)")
        return entry

    def remove_schedule(self, schedule_id: str) -> bool:
        """Remove a schedule by ID."""
        with self._lock:
            if schedule_id in self._schedules:
                del self._schedules[schedule_id]
                self._save_schedules()
                logger.info(f"Removed schedule: {schedule_id}")
                return True
        return False

    def enable_schedule(self, schedule_id: str) -> bool:
        """Enable a schedule."""
        with self._lock:
            if schedule_id in self._schedules:
                self._schedules[schedule_id].enabled = True
                self._schedules[schedule_id].next_run = datetime.now()
                self._save_schedules()
                return True
        return False

    def disable_schedule(self, schedule_id: str) -> bool:
        """Disable a schedule."""
        with self._lock:
            if schedule_id in self._schedules:
                self._schedules[schedule_id].enabled = False
                self._save_schedules()
                return True
        return False

    def get_schedule(self, schedule_id: str) -> ScheduleEntry | None:
        """Get a schedule by ID."""
        return self._schedules.get(schedule_id)

    def list_schedules(self) -> list[ScheduleEntry]:
        """List all schedules."""
        return list(self._schedules.values())

    def start(self) -> None:
        """Start the scheduler background thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Scheduler started")

    def stop(self) -> None:
        """Stop the scheduler background thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._thread is not None and self._thread.is_alive()

    def _run_loop(self) -> None:
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while not self._stop_event.is_set():
            try:
                self._check_schedules()
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

            # Wait for interval or stop event
            self._stop_event.wait(timeout=self.check_interval)

        logger.info("Scheduler loop ended")

    def _check_schedules(self) -> None:
        """Check for due schedules and execute them."""
        with self._lock:
            due_schedules = [s for s in self._schedules.values() if s.is_due()]

        for schedule in due_schedules:
            logger.info(f"Schedule due: {schedule.id}")

            if self._run_callback is not None:
                try:
                    self._run_callback(
                        schedule.script_name,
                        schedule.config,
                        schedule.target_db,
                    )
                except Exception as e:
                    logger.error(f"Scheduled run failed for {schedule.id}: {e}")

            with self._lock:
                schedule.mark_run()
                self._save_schedules()

    def _load_schedules(self) -> None:
        """Load schedules from file."""
        if not self.schedules_file.exists():
            return

        try:
            with open(self.schedules_file, "r") as f:
                data = json.load(f)

            for entry_data in data.get("schedules", []):
                entry = ScheduleEntry.from_dict(entry_data)
                self._schedules[entry.id] = entry

            logger.info(f"Loaded {len(self._schedules)} schedules")
        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")

    def _save_schedules(self) -> None:
        """Save schedules to file."""
        try:
            self.schedules_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "schedules": [s.to_dict() for s in self._schedules.values()],
                "saved_at": datetime.now().isoformat(),
            }

            with open(self.schedules_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")

    def run_now(self, schedule_id: str) -> bool:
        """Manually trigger a scheduled run immediately."""
        schedule = self.get_schedule(schedule_id)
        if schedule is None:
            return False

        if self._run_callback is not None:
            try:
                self._run_callback(
                    schedule.script_name,
                    schedule.config,
                    schedule.target_db,
                )
                with self._lock:
                    schedule.mark_run()
                    self._save_schedules()
                return True
            except Exception as e:
                logger.error(f"Manual run failed for {schedule_id}: {e}")
                return False

        return False
