"""
Script Loader - Discovers scripts and reads SCRIPT_SPEC

Responsibilities:
- Scan scripts directory for Python files
- Load and validate SCRIPT_SPEC from each script
- Provide registry of available scripts
"""

import importlib.util
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class ScriptInfo:
    """Metadata about a discovered script."""

    name: str
    version: str
    path: Path
    spec: dict[str, Any]
    run_func: Callable[[dict, Any], dict]

    @property
    def parameters(self) -> dict[str, Any]:
        return self.spec.get("parameters", {})

    @property
    def target_db_options(self) -> list[str]:
        target_db = self.spec.get("target_db", {})
        return target_db.get("options", [])

    @property
    def default_target_db(self) -> str | None:
        target_db = self.spec.get("target_db", {})
        return target_db.get("default")

    @property
    def variable_mapping(self) -> dict[str, Any]:
        return self.spec.get("variable_mapping", {})
    
    @property
    def description(self) -> str:
        return self.spec.get("description", "")
    
    @property
    def requires_db(self) -> bool:
        """Check if this script requires a database connection."""
        return "target_db" in self.spec


class ScriptLoader:
    """Discovers and loads dataset scripts."""

    # Only name, version, and parameters are required
    # target_db is optional (conversion scripts don't need it)
    REQUIRED_SPEC_FIELDS = {"name", "version", "parameters"}

    def __init__(self, scripts_dir: Path):
        self.scripts_dir = Path(scripts_dir)
        self._registry: dict[str, ScriptInfo] = {}

    def discover(self) -> dict[str, ScriptInfo]:
        """
        Scan scripts directory and load all valid scripts.

        Returns:
            Dictionary mapping script names to ScriptInfo objects.
        """
        self._registry.clear()

        if not self.scripts_dir.exists():
            logger.warning(f"Scripts directory does not exist: {self.scripts_dir}")
            return self._registry

        for script_path in self.scripts_dir.glob("*.py"):
            if script_path.name.startswith("_"):
                continue

            try:
                script_info = self._load_script(script_path)
                if script_info:
                    self._registry[script_info.name] = script_info
                    logger.info(f"Loaded script: {script_info.name} v{script_info.version}")
            except Exception as e:
                logger.error(f"Failed to load script {script_path.name}: {e}")

        return self._registry

    def _load_script(self, script_path: Path) -> ScriptInfo | None:
        """Load a single script and extract its SCRIPT_SPEC."""
        spec = importlib.util.spec_from_file_location(
            script_path.stem,
            script_path
        )
        if spec is None or spec.loader is None:
            logger.warning(f"Cannot create module spec for {script_path}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Validate SCRIPT_SPEC exists
        if not hasattr(module, "SCRIPT_SPEC"):
            logger.warning(f"No SCRIPT_SPEC found in {script_path.name}")
            return None

        script_spec = module.SCRIPT_SPEC

        # Validate required fields
        missing = self.REQUIRED_SPEC_FIELDS - set(script_spec.keys())
        if missing:
            logger.warning(f"Missing required fields in {script_path.name}: {missing}")
            return None

        # Validate run function exists
        if not hasattr(module, "run"):
            logger.warning(f"No run() function found in {script_path.name}")
            return None

        run_func = module.run
        if not callable(run_func):
            logger.warning(f"run is not callable in {script_path.name}")
            return None

        return ScriptInfo(
            name=script_spec["name"],
            version=script_spec["version"],
            path=script_path,
            spec=script_spec,
            run_func=run_func,
        )

    def get_script(self, name: str) -> ScriptInfo | None:
        """Get a script by name."""
        return self._registry.get(name)

    def list_scripts(self) -> list[str]:
        """List all discovered script names."""
        return list(self._registry.keys())

    def reload_script(self, name: str) -> ScriptInfo | None:
        """Reload a specific script."""
        script_info = self._registry.get(name)
        if script_info is None:
            return None

        try:
            new_info = self._load_script(script_info.path)
            if new_info:
                self._registry[name] = new_info
                return new_info
        except Exception as e:
            logger.error(f"Failed to reload script {name}: {e}")

        return None


def validate_script_spec(spec: dict) -> list[str]:
    """
    Validate a SCRIPT_SPEC dictionary.

    Returns:
        List of validation errors (empty if valid).
    """
    errors = []

    # Check required top-level fields
    for field in ["name", "version", "parameters"]:
        if field not in spec:
            errors.append(f"Missing required field: {field}")

    # Validate parameters structure
    if "parameters" in spec:
        params = spec["parameters"]
        if not isinstance(params, dict):
            errors.append("parameters must be a dictionary")
        else:
            for param_name, param_def in params.items():
                if not isinstance(param_def, dict):
                    errors.append(f"Parameter {param_name} must be a dictionary")
                    continue
                if "type" not in param_def:
                    errors.append(f"Parameter {param_name} missing 'type'")

    # Validate target_db structure (if present)
    if "target_db" in spec:
        target_db = spec["target_db"]
        if not isinstance(target_db, dict):
            errors.append("target_db must be a dictionary")
        elif "options" not in target_db:
            errors.append("target_db missing 'options'")

    return errors
