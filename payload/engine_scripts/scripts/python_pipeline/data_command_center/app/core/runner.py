"""
Script Runner - Executes scripts and handles logging

Responsibilities:
- Execute script run() functions with config and db handle
- Capture and log output
- Record run metadata
- Handle errors gracefully
"""

import hashlib
import json
import logging
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .connections import ConnectionResolver
from .script_loader import ScriptInfo

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    """Result of a script execution."""

    script_name: str
    script_version: str
    status: str  # "success", "error", "cancelled"
    started_at: datetime
    completed_at: datetime
    config: dict[str, Any]
    target_db: str
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    config_hash: str = ""
    run_id: str = ""

    def __post_init__(self):
        if not self.config_hash:
            self.config_hash = self._compute_config_hash()
        if not self.run_id:
            self.run_id = self._generate_run_id()

    def _compute_config_hash(self) -> str:
        """Compute deterministic hash of the configuration."""
        config_str = json.dumps(self.config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]

    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        timestamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        return f"{self.script_name}_{timestamp}_{self.config_hash[:8]}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "run_id": self.run_id,
            "script_name": self.script_name,
            "script_version": self.script_version,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "duration_seconds": (self.completed_at - self.started_at).total_seconds(),
            "config": self.config,
            "config_hash": self.config_hash,
            "target_db": self.target_db,
            "result": self.result,
            "error": self.error,
        }


class ScriptRunner:
    """Executes dataset scripts."""

    def __init__(
        self,
        connection_resolver: ConnectionResolver,
        logs_dir: Path,
    ):
        self.connection_resolver = connection_resolver
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._run_history: list[RunResult] = []

    def run(
        self,
        script: ScriptInfo,
        config: dict[str, Any],
        target_db: str,
    ) -> RunResult:
        """
        Execute a script with the given configuration.

        Args:
            script: ScriptInfo object for the script to run.
            config: Configuration dictionary with parameter values.
            target_db: Name of the target database connection.

        Returns:
            RunResult with execution metadata.
        """
        started_at = datetime.now()
        logger.info(f"Starting script: {script.name} v{script.version}")
        logger.info(f"Config: {config}")
        logger.info(f"Target DB: {target_db}")

        db = None
        try:
            # Get database connection
            db = self.connection_resolver.get_connection(target_db)

            # Execute the script's run function
            result = script.run_func(config, db)

            completed_at = datetime.now()
            run_result = RunResult(
                script_name=script.name,
                script_version=script.version,
                status="success",
                started_at=started_at,
                completed_at=completed_at,
                config=config,
                target_db=target_db,
                result=result or {},
            )

            logger.info(f"Script completed successfully: {run_result.run_id}")

        except Exception as e:
            completed_at = datetime.now()
            error_msg = f"{type(e).__name__}: {str(e)}"
            error_trace = traceback.format_exc()

            run_result = RunResult(
                script_name=script.name,
                script_version=script.version,
                status="error",
                started_at=started_at,
                completed_at=completed_at,
                config=config,
                target_db=target_db,
                error=error_msg,
            )

            logger.error(f"Script failed: {error_msg}")
            logger.debug(error_trace)

        finally:
            # Close database connection
            if db is not None:
                try:
                    db.close()
                except Exception:
                    pass

        # Save run result
        self._run_history.append(run_result)
        self._save_run_log(run_result)

        return run_result

    def _save_run_log(self, run_result: RunResult) -> Path:
        """Save run result to a log file."""
        log_file = self.logs_dir / f"{run_result.run_id}.json"
        with open(log_file, "w") as f:
            json.dump(run_result.to_dict(), f, indent=2)
        return log_file

    def get_history(self, script_name: str | None = None) -> list[RunResult]:
        """Get run history, optionally filtered by script name."""
        if script_name is None:
            return list(self._run_history)
        return [r for r in self._run_history if r.script_name == script_name]

    def get_last_run(self, script_name: str) -> RunResult | None:
        """Get the most recent run for a script."""
        history = self.get_history(script_name)
        return history[-1] if history else None

    def load_history_from_logs(self) -> None:
        """Load run history from saved log files."""
        self._run_history.clear()

        for log_file in sorted(self.logs_dir.glob("*.json")):
            try:
                with open(log_file, "r") as f:
                    data = json.load(f)

                run_result = RunResult(
                    script_name=data["script_name"],
                    script_version=data["script_version"],
                    status=data["status"],
                    started_at=datetime.fromisoformat(data["started_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"]),
                    config=data["config"],
                    target_db=data["target_db"],
                    result=data.get("result", {}),
                    error=data.get("error"),
                    config_hash=data.get("config_hash", ""),
                    run_id=data.get("run_id", ""),
                )
                self._run_history.append(run_result)
            except Exception as e:
                logger.warning(f"Failed to load log file {log_file}: {e}")


def build_config_from_spec(
    script: ScriptInfo,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a configuration dictionary from a script's SCRIPT_SPEC.

    Uses default values from the spec, with optional overrides.

    Args:
        script: ScriptInfo with parameter definitions.
        overrides: Optional dictionary of parameter overrides.

    Returns:
        Complete configuration dictionary.
    """
    config = {}
    overrides = overrides or {}

    for param_name, param_def in script.parameters.items():
        if param_name in overrides:
            config[param_name] = overrides[param_name]
        elif "default" in param_def:
            config[param_name] = param_def["default"]
        else:
            raise ValueError(f"No value or default for required parameter: {param_name}")

    return config
