"""
Threaded Scanner Engine - Non-blocking vault scanning with parallelism
Uses QThread + ThreadPoolExecutor for maximum performance
"""

from __future__ import annotations

import os
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from PySide6.QtCore import QThread, Signal, QObject


# Patterns
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
TAG_PATTERN = re.compile(r'(?<!\S)#([A-Za-z][A-Za-z0-9_\-/]*)(?!\S)')
YAML_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# Directories to skip
SKIP_DIRS = {'.obsidian', '.trash', '.git', 'node_modules', '__pycache__', '.venv', 'venv'}


@dataclass
class NoteData:
    """Represents a parsed note."""
    path: str
    name: str
    content: str
    tags: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    yaml_data: Dict[str, Any] = field(default_factory=dict)
    word_count: int = 0
    char_count: int = 0
    modified_time: float = 0
    file_hash: str = ""
    folder: str = ""
    error: Optional[str] = None


@dataclass 
class ScanResult:
    """Results of a vault scan."""
    notes: List[NoteData] = field(default_factory=list)
    total_files: int = 0
    total_words: int = 0
    total_chars: int = 0
    unique_tags: Set[str] = field(default_factory=set)
    unique_links: Set[str] = field(default_factory=set)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0
    folder_stats: Dict[str, int] = field(default_factory=dict)


def parse_note(file_path: Path) -> NoteData:
    """Parse a single markdown note. Thread-safe."""
    note = NoteData(
        path=str(file_path),
        name=file_path.stem,
        content="",
        folder=file_path.parent.name
    )
    
    try:
        # Try multiple encodings
        content = None
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        
        # Strip BOM if present
        if content.startswith('\ufeff'):
            content = content[1:]
        
        note.content = content
        note.char_count = len(content)
        note.word_count = len(content.split())
        
        # Get file stats
        stat = file_path.stat()
        note.modified_time = stat.st_mtime
        note.file_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        
        # Parse YAML frontmatter
        yaml_match = YAML_PATTERN.match(content)
        if yaml_match:
            yaml_text = yaml_match.group(1)
            # Simple YAML parsing (key: value)
            for line in yaml_text.split('\n'):
                if ':' in line:
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        # Handle list values
                        if value.startswith('[') and value.endswith(']'):
                            value = [v.strip().strip('"\'') for v in value[1:-1].split(',')]
                        note.yaml_data[key] = value
            
            # Extract tags from YAML
            if 'tags' in note.yaml_data:
                yaml_tags = note.yaml_data['tags']
                if isinstance(yaml_tags, list):
                    note.tags.extend(yaml_tags)
                elif isinstance(yaml_tags, str):
                    note.tags.extend([t.strip() for t in yaml_tags.split(',')])
        
        # Extract inline tags (skip code blocks)
        text_for_tags = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        text_for_tags = re.sub(r'`[^`]+`', '', text_for_tags)
        inline_tags = TAG_PATTERN.findall(text_for_tags)
        note.tags.extend(inline_tags)
        note.tags = list(set(note.tags))  # Dedupe
        
        # Extract wikilinks
        links = WIKILINK_PATTERN.findall(content)
        # Clean links (remove heading refs)
        note.links = list(set(link.split('#')[0].strip() for link in links if link.strip()))
        
    except Exception as e:
        note.error = f"{type(e).__name__}: {str(e)}"
    
    return note


class ScanWorker(QThread):
    """
    Background worker for vault scanning.
    Emits progress signals while scanning in parallel.
    """
    
    # Signals
    progress = Signal(int, str)  # (percent, current_file)
    file_scanned = Signal(object)  # NoteData
    finished = Signal(object)  # ScanResult
    error = Signal(str)
    
    def __init__(
        self,
        scan_path: Path,
        recursive: bool = True,
        max_workers: int = 8,
        file_filter: Optional[Callable[[Path], bool]] = None
    ):
        super().__init__()
        self.scan_path = Path(scan_path)
        self.recursive = recursive
        self.max_workers = max_workers
        self.file_filter = file_filter
        self._cancelled = False
    
    def cancel(self):
        """Cancel the scan."""
        self._cancelled = True
    
    def run(self):
        """Execute the scan in background thread."""
        start_time = datetime.now()
        result = ScanResult()
        
        try:
            # Collect all markdown files
            md_files: List[Path] = []
            
            if self.recursive:
                for root, dirs, files in os.walk(self.scan_path):
                    # Filter out skip directories
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                    
                    for file in files:
                        if self._cancelled:
                            return
                        if file.endswith('.md') and not file.startswith('.'):
                            file_path = Path(root) / file
                            if self.file_filter is None or self.file_filter(file_path):
                                md_files.append(file_path)
            else:
                # Non-recursive - just this folder
                for file in self.scan_path.iterdir():
                    if file.is_file() and file.suffix == '.md' and not file.name.startswith('.'):
                        if self.file_filter is None or self.file_filter(file):
                            md_files.append(file)
            
            result.total_files = len(md_files)
            
            if result.total_files == 0:
                self.progress.emit(100, "No files found")
                self.finished.emit(result)
                return
            
            # Parallel processing
            completed = 0
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_path = {
                    executor.submit(parse_note, path): path 
                    for path in md_files
                }
                
                # Process as they complete
                for future in as_completed(future_to_path):
                    if self._cancelled:
                        executor.shutdown(wait=False, cancel_futures=True)
                        return
                    
                    path = future_to_path[future]
                    completed += 1
                    
                    try:
                        note = future.result()
                        result.notes.append(note)
                        
                        # Aggregate stats
                        result.total_words += note.word_count
                        result.total_chars += note.char_count
                        result.unique_tags.update(note.tags)
                        result.unique_links.update(note.links)
                        
                        # Folder stats
                        folder = note.folder or 'root'
                        result.folder_stats[folder] = result.folder_stats.get(folder, 0) + 1
                        
                        if note.error:
                            result.errors.append(f"{path}: {note.error}")
                        
                        # Emit progress
                        self.file_scanned.emit(note)
                        
                    except Exception as e:
                        result.errors.append(f"{path}: {type(e).__name__}: {str(e)}")
                    
                    # Update progress
                    percent = int((completed / result.total_files) * 100)
                    self.progress.emit(percent, path.name)
            
            # Finalize
            result.duration_seconds = (datetime.now() - start_time).total_seconds()
            self.progress.emit(100, "Complete")
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(f"Scan failed: {type(e).__name__}: {str(e)}")


class QuickScanWorker(QThread):
    """
    Lighter scan that only checks file metadata (no content parsing).
    Good for large vaults when you just need counts.
    """
    
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, scan_path: Path, recursive: bool = True):
        super().__init__()
        self.scan_path = Path(scan_path)
        self.recursive = recursive
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        result = {
            'total_files': 0,
            'total_size_bytes': 0,
            'folders': {},
            'newest_file': None,
            'oldest_file': None,
        }
        
        try:
            if self.recursive:
                for root, dirs, files in os.walk(self.scan_path):
                    if self._cancelled:
                        return
                    
                    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
                    folder_name = Path(root).name
                    
                    for file in files:
                        if file.endswith('.md') and not file.startswith('.'):
                            file_path = Path(root) / file
                            try:
                                stat = file_path.stat()
                                result['total_files'] += 1
                                result['total_size_bytes'] += stat.st_size
                                
                                # Track by folder
                                if folder_name not in result['folders']:
                                    result['folders'][folder_name] = {'count': 0, 'size': 0}
                                result['folders'][folder_name]['count'] += 1
                                result['folders'][folder_name]['size'] += stat.st_size
                                
                                # Track newest/oldest
                                if result['newest_file'] is None or stat.st_mtime > result['newest_file'][1]:
                                    result['newest_file'] = (str(file_path), stat.st_mtime)
                                if result['oldest_file'] is None or stat.st_mtime < result['oldest_file'][1]:
                                    result['oldest_file'] = (str(file_path), stat.st_mtime)
                                    
                            except Exception:
                                pass
                    
                    # Emit progress occasionally
                    self.progress.emit(0, folder_name)
            
            self.finished.emit(result)
            
        except Exception as e:
            self.error.emit(str(e))


# Convenience function for sync scanning (for testing)
def scan_vault_sync(
    path: Path,
    recursive: bool = True,
    max_workers: int = 8
) -> ScanResult:
    """Synchronous vault scan (blocks). Use ScanWorker for GUI."""
    result = ScanResult()
    start_time = datetime.now()
    
    md_files = []
    if recursive:
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for file in files:
                if file.endswith('.md'):
                    md_files.append(Path(root) / file)
    else:
        md_files = [f for f in path.iterdir() if f.suffix == '.md']
    
    result.total_files = len(md_files)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        notes = list(executor.map(parse_note, md_files))
    
    for note in notes:
        result.notes.append(note)
        result.total_words += note.word_count
        result.total_chars += note.char_count
        result.unique_tags.update(note.tags)
        result.unique_links.update(note.links)
        if note.error:
            result.errors.append(f"{note.path}: {note.error}")
    
    result.duration_seconds = (datetime.now() - start_time).total_seconds()
    return result
