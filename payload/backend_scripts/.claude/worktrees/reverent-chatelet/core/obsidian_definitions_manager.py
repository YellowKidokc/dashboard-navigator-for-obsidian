"""
Obsidian Definitions Manager - Core logic for managing definitions
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from .settings_manager import SettingsManager


@dataclass
class Definition:
    """Represents a single definition."""
    phrase: str
    aliases: List[str]
    definition: str
    file_path: str
    line_number: int = 0
    classification: str = ""  # theory, proper_name, scientific_method, mathematical_formalism, regular_word, etc.
    folder: str = ""  # domain folder like "physics", "theories", "terms", etc.


@dataclass
class DefinitionFile:
    """Represents a definition file."""
    path: Path
    file_type: str  # "consolidated" or "atomic"
    definitions: List[Definition]


class ObsidianDefinitionsManager:
    """Manages Obsidian definitions outside of Obsidian."""

    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.vault_path: Optional[Path] = None
        self.definitions_folder: Optional[Path] = None
        self.definition_files: List[DefinitionFile] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from settings."""
        # Try to auto-detect vault if app is inside a vault
        # App is at: THEOPHYSICS_MASTER/Apps/Obsidian-Definitions-Manager/
        # Vault root is: THEOPHYSICS_MASTER/
        app_path = Path(__file__).resolve().parent.parent.parent
        # Check if we're in a typical Obsidian vault structure
        # Look for .obsidian folder (sign of Obsidian vault)
        potential_vault = app_path
        max_levels = 5  # Don't go too far up
        level = 0
        while potential_vault != potential_vault.parent and level < max_levels:
            if (potential_vault / ".obsidian").exists():
                # Found vault root!
                self.vault_path = potential_vault
                break
            potential_vault = potential_vault.parent
            level += 1
        
        # If not auto-detected, try parent of Apps folder
        if not self.vault_path:
            apps_parent = app_path.parent if app_path.name == "Apps" else app_path.parent.parent
            if apps_parent and apps_parent.exists():
                self.vault_path = apps_parent
        
        # If still not found, use settings
        if not self.vault_path:
            vault_path_str = self.settings.get("obsidian", "vault_path", "")
            if vault_path_str:
                self.vault_path = Path(vault_path_str)
        
        def_folder_str = self.settings.get("obsidian", "definitions_folder", "definitions")
        if self.vault_path:
            self.definitions_folder = self.vault_path / def_folder_str

    def set_vault_path(self, vault_path: Path) -> None:
        """Set the Obsidian vault path."""
        self.vault_path = Path(vault_path)
        def_folder = self.settings.get("obsidian", "definitions_folder", "definitions")
        self.definitions_folder = self.vault_path / def_folder
        self.settings.set("obsidian", "vault_path", str(vault_path))
        self.scan_definitions()

    def scan_definitions(self) -> List[DefinitionFile]:
        """Scan for definition files in the vault."""
        if not self.definitions_folder or not self.definitions_folder.exists():
            return []

        self.definition_files = []
        
        # Find all markdown files in definitions folder
        for md_file in self.definitions_folder.rglob("*.md"):
            def_file = self._parse_definition_file(md_file)
            if def_file:
                self.definition_files.append(def_file)

        return self.definition_files

    def _parse_definition_file(self, file_path: Path) -> Optional[DefinitionFile]:
        """Parse a definition file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Check frontmatter for def-type
            file_type = "consolidated"  # default
            if content.startswith("---"):
                fm_end = content.find("---", 3)
                if fm_end > 0:
                    frontmatter = content[3:fm_end]
                    if "def-type:" in frontmatter:
                        if "atomic" in frontmatter:
                            file_type = "atomic"
                        elif "consolidated" in frontmatter:
                            file_type = "consolidated"
                    content = content[fm_end + 3:].lstrip()

            if file_type == "atomic":
                return self._parse_atomic_file(file_path, content)
            else:
                return self._parse_consolidated_file(file_path, content)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _parse_atomic_file(self, file_path: Path, content: str) -> DefinitionFile:
        """Parse an atomic definition file (one definition per file)."""
        phrase = file_path.stem  # File name is the phrase
        
        # Extract aliases from frontmatter if present
        aliases = []
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                frontmatter = content[3:fm_end]
                # Look for aliases: list
                alias_match = re.search(r'aliases:\s*\n((?:\s*-\s*[^\n]+\n?)+)', frontmatter)
                if alias_match:
                    alias_lines = alias_match.group(1)
                    aliases = re.findall(r'-\s*([^\n]+)', alias_lines)
                content = content[fm_end + 3:].lstrip()

        definition = Definition(
            phrase=phrase,
            aliases=aliases,
            definition=content.strip(),
            file_path=str(file_path),
            line_number=0
        )

        return DefinitionFile(
            path=file_path,
            file_type="atomic",
            definitions=[definition]
        )

    def _parse_consolidated_file(self, file_path: Path, content: str) -> DefinitionFile:
        """Parse a consolidated definition file (multiple definitions)."""
        definitions = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for phrase header: # Phrase
            if line.startswith('# '):
                phrase = line[2:].strip()
                aliases = []
                definition_lines = []
                
                i += 1
                # Check for alias line (italic line)
                if i < len(lines) and lines[i].strip().startswith('*') and lines[i].strip().endswith('*'):
                    alias_line = lines[i].strip()
                    aliases = [a.strip() for a in alias_line.strip('*').split(',')]
                    i += 1
                
                # Collect definition lines until divider
                while i < len(lines):
                    line = lines[i].strip()
                    if line == '---' or line == '___':
                        break
                    definition_lines.append(lines[i])
                    i += 1
                
                definition_text = '\n'.join(definition_lines).strip()
                
                if phrase and definition_text:
                    definitions.append(Definition(
                        phrase=phrase,
                        aliases=aliases,
                        definition=definition_text,
                        file_path=str(file_path),
                        line_number=i
                    ))
            
            i += 1

        return DefinitionFile(
            path=file_path,
            file_type="consolidated",
            definitions=definitions
        )

    def get_all_definitions(self) -> List[Definition]:
        """Get all definitions from all files."""
        all_defs = []
        for def_file in self.definition_files:
            all_defs.extend(def_file.definitions)
        return all_defs

    def add_definition(
        self,
        phrase: str,
        definition: str,
        aliases: List[str] = None,
        target_file: Optional[Path] = None,
        classification: str = "",
        folder: str = ""
    ) -> bool:
        """Add a new definition to a file."""
        if not self.definitions_folder:
            return False

        # Determine target file based on folder
        if target_file is None:
            if folder:
                # Create folder structure
                folder_path = self.definitions_folder / folder
                folder_path.mkdir(parents=True, exist_ok=True)
                target_file = folder_path / "definitions.md"
            else:
                target_file = self.definitions_folder / "definitions.md"
            
            if not target_file.exists():
                target_file.write_text("---\ndef-type: consolidated\n---\n\n", encoding="utf-8")

        try:
            content = target_file.read_text(encoding="utf-8")
            
            # Ensure it's a consolidated file
            if "def-type: consolidated" not in content:
                if content.startswith("---"):
                    content = content.replace("---", "---\ndef-type: consolidated\n---", 1)
                else:
                    content = "---\ndef-type: consolidated\n---\n\n" + content

            # Append new definition with metadata
            new_def = f"\n# {phrase}\n"
            
            # Add metadata in frontmatter-style comment
            metadata = []
            if classification:
                metadata.append(f"classification: {classification}")
            if folder:
                metadata.append(f"folder: {folder}")
            if metadata:
                new_def += f"<!-- {' | '.join(metadata)} -->\n"
            
            if aliases:
                new_def += f"*{', '.join(aliases)}*\n\n"
            new_def += f"{definition}\n\n---\n"
            
            content += new_def
            target_file.write_text(content, encoding="utf-8")
            
            # Rescan
            self.scan_definitions()
            return True
        except Exception as e:
            print(f"Error adding definition: {e}")
            return False

    def update_definition(
        self,
        old_phrase: str,
        new_phrase: str,
        new_definition: str,
        new_aliases: List[str] = None,
        classification: str = "",
        folder: str = ""
    ) -> bool:
        """Update an existing definition."""
        # Find the definition
        for def_file in self.definition_files:
            for def_obj in def_file.definitions:
                if def_obj.phrase == old_phrase:
                    # Update logic here
                    # This is simplified - full implementation would rewrite the file
                    return self.add_definition(
                        new_phrase,
                        new_definition,
                        new_aliases,
                        Path(def_obj.file_path),
                        classification=classification,
                        folder=folder
                    )
        return False

    def delete_definition(self, phrase: str) -> bool:
        """Delete a definition."""
        # Find and remove from file
        # Simplified - full implementation would rewrite file without that definition
        return False

