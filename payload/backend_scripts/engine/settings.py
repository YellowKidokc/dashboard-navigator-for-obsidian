# engine/settings.py

from dataclasses import dataclass
from pathlib import Path
import json
import os

# Look for config file relative to this file's location
_THIS_DIR = Path(__file__).parent.parent
CONFIG_FILE = _THIS_DIR / "theophysics_config.json"


@dataclass
class SettingsManager:
    vault_path: Path | None = None
    sqlite_path: Path | None = None
    postgres_conn_str: str | None = None
    model_name: str | None = "none"

    def load(self):
        """Load settings from config file."""
        if not CONFIG_FILE.exists():
            # Create default config
            self.save()
            return
        
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            
            vp = data.get("vault_path")
            sp = data.get("sqlite_path")
            
            self.vault_path = Path(vp) if vp else None
            self.sqlite_path = Path(sp) if sp else None
            self.postgres_conn_str = data.get("postgres_conn_str")
            self.model_name = data.get("model_name", "none")
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config: {e}")
            self.save()  # Create fresh config

    def save(self):
        """Save settings to config file."""
        data = {
            "vault_path": str(self.vault_path) if self.vault_path else None,
            "sqlite_path": str(self.sqlite_path) if self.sqlite_path else None,
            "postgres_conn_str": self.postgres_conn_str,
            "model_name": self.model_name,
        }
        
        try:
            CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except IOError as e:
            print(f"Warning: Could not save config: {e}")

    def validate(self) -> list[str]:
        """Validate settings and return list of issues."""
        issues = []
        
        if self.vault_path is None:
            issues.append("Vault path not set")
        elif not self.vault_path.exists():
            issues.append(f"Vault path does not exist: {self.vault_path}")
        elif not self.vault_path.is_dir():
            issues.append(f"Vault path is not a directory: {self.vault_path}")
        
        return issues

    @property
    def config_path(self) -> Path:
        """Return the path to the config file."""
        return CONFIG_FILE
