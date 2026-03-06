"""
Settings Manager - Same as Stratum
"""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path


class SettingsManager:
    def __init__(self, ini_path: Path):
        self._path = Path(ini_path)
        self._config = ConfigParser()

    def load(self) -> None:
        if not self._path.exists():
            self._create_default()
        self._config.read(self._path, encoding="utf-8")

    def _create_default(self) -> None:
        self._config["obsidian"] = {
            "vault_path": "",
            "definitions_folder": "definitions"
        }
        self._config["openai"] = {"api_key": "", "model": "gpt-4"}
        self._config["claude"] = {"api_key": "", "model": "claude-3-5-sonnet-20241022"}
        self._config["app"] = {"theme": "dark", "window_on_top": "false"}
        with self._path.open("w", encoding="utf-8") as f:
            self._config.write(f)

    def save(self) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            self._config.write(f)

    @property
    def config(self) -> ConfigParser:
        return self._config

    def get(self, section: str, key: str, fallback: str = "") -> str:
        return self._config.get(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save()

