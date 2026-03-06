# engine/vault_engine.py

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, List

from .utils import parse_yaml_block, extract_tags, extract_links


class VaultEngine:
    def __init__(self, settings, db_engine):
        self.settings = settings
        self.db = db_engine
        self.last_scan_errors = []

    def scan_vault(self, full: bool = True):
        """
        Scan the vault for all markdown files.
        
        Args:
            full: If True, replace all notes. If False, only update changed notes.
        
        Raises:
            ValueError: If vault path is not set or doesn't exist.
        """
        vault = self.settings.vault_path
        
        if vault is None:
            raise ValueError("Vault path not set. Please configure the vault path in settings.")
        
        if not vault.exists():
            raise ValueError(f"Vault path does not exist: {vault}")
        
        if not vault.is_dir():
            raise ValueError(f"Vault path is not a directory: {vault}")

        self.last_scan_errors = []
        notes: List[Dict[str, Any]] = []
        
        # Count files first for progress info
        md_files = []
        for root, dirs, files in os.walk(vault):
            # Skip hidden directories and common non-content folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for f in files:
                if f.endswith(".md") and not f.startswith('.'):
                    md_files.append(Path(root) / f)
        
        # Process files
        for path in md_files:
            try:
                note = self._process_note(path)
                notes.append(note)
            except Exception as e:
                self.last_scan_errors.append({
                    "path": str(path),
                    "error": str(e)
                })

        self.db.store_notes(notes, replace=full)

    def _process_note(self, path: Path) -> Dict[str, Any]:
        """
        Process a single markdown file.
        
        Args:
            path: Path to the markdown file.
        
        Returns:
            Dict containing note metadata.
        """
        # Read with multiple encoding attempts
        text = None
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                text = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            # Last resort: read with error handling
            text = path.read_text(encoding='utf-8', errors='replace')
        
        # Strip BOM if present
        if text.startswith('\ufeff'):
            text = text[1:]
        
        # Parse content
        yaml_block = parse_yaml_block(text)
        tags = extract_tags(text)
        links = extract_links(text)
        note_hash = hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()

        return {
            "path": str(path),
            "title": path.stem,
            "yaml": yaml_block,
            "tags": tags,
            "links": links,
            "hash": note_hash,
        }

    def get_metrics(self) -> dict:
        """Get vault metrics from database."""
        metrics = self.db.get_metrics()
        metrics["errors"] = len(self.last_scan_errors)
        return metrics

    def get_scan_errors(self) -> List[Dict[str, str]]:
        """Get list of errors from the last scan."""
        return self.last_scan_errors.copy()

    def get_note(self, path: str) -> Dict[str, Any] | None:
        """Get a specific note by path."""
        return self.db.get_note_by_path(path)

    def rescan_note(self, path: str) -> Dict[str, Any]:
        """Rescan a single note and update the database."""
        note = self._process_note(Path(path))
        self.db.store_notes([note], replace=False)
        return note
