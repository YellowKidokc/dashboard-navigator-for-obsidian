"""
VAULT HEALTH TAB
================
Quick health checks for your Obsidian vault.
Finds broken links, missing files, orphan notes.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
from collections import Counter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QListWidget,
    QListWidgetItem, QGroupBox, QProgressBar, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor


class HealthCheckWorker(QThread):
    """Background worker for vault health checks."""
    progress = Signal(str)
    result = Signal(dict)
    finished = Signal()
    
    def __init__(self, vault_path: str):
        super().__init__()
        self.vault_path = Path(vault_path)
    
    def run(self):
        results = {
            'broken_links': [],
            'orphan_notes': [],
            'empty_files': [],
            'missing_yaml': [],
            'duplicate_titles': [],
            'large_files': [],
            'total_files': 0,
            'total_links': 0,
        }
        
        if not self.vault_path.exists():
            self.result.emit(results)
            self.finished.emit()
            return
        
        # Get all markdown files
        md_files = list(self.vault_path.rglob("*.md"))
        results['total_files'] = len(md_files)
        
        # Build file index (for link checking)
        self.progress.emit("Building file index...")
        file_index: Set[str] = set()
        file_titles: Dict[str, List[Path]] = {}
        
        for f in md_files:
            # Add both filename (without extension) and full relative path
            name = f.stem.lower()
            file_index.add(name)
            file_index.add(f.stem)  # case-sensitive version
            
            # Track duplicates
            if name not in file_titles:
                file_titles[name] = []
            file_titles[name].append(f)
        
        # Check for duplicates
        for name, paths in file_titles.items():
            if len(paths) > 1:
                results['duplicate_titles'].append((name, [str(p) for p in paths]))
        
        # Link pattern
        link_pattern = re.compile(r'\[\[([^\]|#]+)(?:\|[^\]]+)?(?:#[^\]]+)?\]\]')
        
        # Analyze each file
        incoming_links: Dict[str, int] = Counter()
        
        for i, f in enumerate(md_files):
            if i % 50 == 0:
                self.progress.emit(f"Checking {i}/{len(md_files)} files...")
            
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                
                # Check for empty files
                if len(content.strip()) < 10:
                    results['empty_files'].append(str(f))
                
                # Check for large files (>100KB)
                if f.stat().st_size > 100 * 1024:
                    results['large_files'].append((str(f), f.stat().st_size // 1024))
                
                # Check for YAML frontmatter
                if not content.strip().startswith('---'):
                    results['missing_yaml'].append(str(f))
                
                # Check links
                links = link_pattern.findall(content)
                results['total_links'] += len(links)
                
                for link in links:
                    link_lower = link.lower().strip()
                    incoming_links[link_lower] += 1
                    
                    # Check if link target exists
                    if link_lower not in file_index and link.strip() not in file_index:
                        results['broken_links'].append({
                            'source': str(f),
                            'target': link,
                        })
            
            except Exception as e:
                pass
        
        # Find orphan notes (no incoming links)
        self.progress.emit("Finding orphan notes...")
        for f in md_files:
            name = f.stem.lower()
            if incoming_links.get(name, 0) == 0:
                # Skip index/MOC files
                if not any(skip in f.stem.lower() for skip in ['index', 'moc', 'readme', '_']):
                    results['orphan_notes'].append(str(f))
        
        self.result.emit(results)
        self.finished.emit()


class VaultHealthTab(QWidget):
    """Vault Health Check Tab."""
    
    def __init__(self, settings_mgr):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.worker = None
        self._current_vault_path = ""
        self._last_results: Dict[str, object] = {}
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_row = QHBoxLayout()
        
        header = QLabel("🏥 Vault Health Check")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d9ff;")
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        self.run_btn = QPushButton("🔍 Run Health Check")
        self.run_btn.clicked.connect(self._run_check)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d4a6f;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3d5a7f; }
        """)
        header_row.addWidget(self.run_btn)

        self.copy_btn = QPushButton("📋 Copy All Findings")
        self.copy_btn.clicked.connect(self._copy_all_findings)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #345b3a;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3d6b45; }
        """)
        header_row.addWidget(self.copy_btn)
        
        layout.addLayout(header_row)
        
        # Status
        self.status_label = QLabel("Click 'Run Health Check' to analyze your vault")
        self.status_label.setStyleSheet("color: #667788;")
        layout.addWidget(self.status_label)
        
        # Results grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)
        
        # Create result sections
        self.broken_links_list = self._create_result_section(
            "🔗 Broken Links", "Links pointing to non-existent files", grid, 0, 0
        )
        self.orphan_notes_list = self._create_result_section(
            "📄 Orphan Notes", "Files with no incoming links", grid, 0, 1
        )
        self.empty_files_list = self._create_result_section(
            "📭 Empty Files", "Files with < 10 characters", grid, 1, 0
        )
        self.missing_yaml_list = self._create_result_section(
            "📋 Missing YAML", "Files without frontmatter", grid, 1, 1
        )
        self.duplicates_list = self._create_result_section(
            "👥 Duplicate Titles", "Files with same name", grid, 2, 0
        )
        self.large_files_list = self._create_result_section(
            "📦 Large Files", "Files > 100KB", grid, 2, 1
        )
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        self._load_cached_results()

    def _cache_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "config" / "ui_cache" / "vault_health.json"

    def _save_cached_results(self, results: dict):
        try:
            cache_path = self._cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "vault_path": self._current_vault_path,
                "total_files": int(results.get("total_files", 0)),
                "total_links": int(results.get("total_links", 0)),
                "broken_links": list(results.get("broken_links", [])),
                "orphan_notes": list(results.get("orphan_notes", [])),
                "empty_files": list(results.get("empty_files", [])),
                "missing_yaml": list(results.get("missing_yaml", [])),
                "duplicate_titles": list(results.get("duplicate_titles", [])),
                "large_files": list(results.get("large_files", [])),
                "counts": {
                    "broken_links": len(results.get("broken_links", [])),
                    "orphan_notes": len(results.get("orphan_notes", [])),
                    "empty_files": len(results.get("empty_files", [])),
                    "missing_yaml": len(results.get("missing_yaml", [])),
                    "duplicate_titles": len(results.get("duplicate_titles", [])),
                    "large_files": len(results.get("large_files", [])),
                },
            }
            cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_cached_results(self):
        cache_path = self._cache_path()
        if not cache_path.exists():
            return
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            self._apply_results(payload, cached=True)
        except Exception:
            pass

    def _apply_results(self, results: dict, cached: bool = False):
        self._last_results = dict(results)
        for lst in [
            self.broken_links_list,
            self.orphan_notes_list,
            self.empty_files_list,
            self.missing_yaml_list,
            self.duplicates_list,
            self.large_files_list,
        ]:
            lst.clear()

        broken_links = list(results.get("broken_links", []))
        orphan_notes = list(results.get("orphan_notes", []))
        empty_files = list(results.get("empty_files", []))
        missing_yaml = list(results.get("missing_yaml", []))
        duplicate_titles = list(results.get("duplicate_titles", []))
        large_files = list(results.get("large_files", []))

        for item in broken_links[:50]:
            source = item.get("source", "") if isinstance(item, dict) else ""
            target = item.get("target", "") if isinstance(item, dict) else str(item)
            self.broken_links_list.addItem(f"{Path(source).name} → {target}")

        for item in orphan_notes[:50]:
            self.orphan_notes_list.addItem(Path(str(item)).name)

        for item in empty_files[:50]:
            self.empty_files_list.addItem(Path(str(item)).name)

        for item in missing_yaml[:50]:
            self.missing_yaml_list.addItem(Path(str(item)).name)

        for item in duplicate_titles[:20]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                name, paths = item[0], item[1]
                self.duplicates_list.addItem(f"{name} ({len(paths)} copies)")

        for item in large_files[:20]:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                path, size = item[0], item[1]
                self.large_files_list.addItem(f"{Path(str(path)).name} ({size}KB)")

        counts = results.get("counts", {}) if isinstance(results.get("counts", {}), dict) else {}
        broken_count = counts.get("broken_links", len(broken_links))
        orphan_count = counts.get("orphan_notes", len(orphan_notes))
        empty_count = counts.get("empty_files", len(empty_files))
        total_files = int(results.get("total_files", 0))
        total_links = int(results.get("total_links", 0))

        if cached:
            generated_at = results.get("generated_at", "").replace("T", " ")
            self.status_label.setText(
                f"Loaded cached health check ({generated_at[:19]}) | "
                f"{total_files} files, {broken_count} broken, {orphan_count} orphans, {empty_count} empty"
            )
            self.status_label.setStyleSheet("color: #8899aa;")
            return

        self.status_label.setText(
            f"✅ Checked {total_files} files, {total_links} links | "
            f"Found: {broken_count} broken, "
            f"{orphan_count} orphans, "
            f"{empty_count} empty"
        )
        self.status_label.setStyleSheet("color: #2ecc71;")

    def _format_findings_for_copy(self) -> str:
        data = self._last_results or {}
        generated_at = str(data.get("generated_at", datetime.now().isoformat(timespec="seconds")))
        lines: List[str] = []
        lines.append("Vault Health Check Export")
        lines.append(f"Generated: {generated_at}")
        lines.append(f"Vault Path: {self._current_vault_path or data.get('vault_path', '')}")
        lines.append(f"Total Files: {data.get('total_files', 0)}")
        lines.append(f"Total Links: {data.get('total_links', 0)}")
        lines.append("")

        broken_links = list(data.get("broken_links", []))
        orphan_notes = list(data.get("orphan_notes", []))
        empty_files = list(data.get("empty_files", []))
        missing_yaml = list(data.get("missing_yaml", []))
        duplicate_titles = list(data.get("duplicate_titles", []))
        large_files = list(data.get("large_files", []))

        lines.append(f"Broken Links ({len(broken_links)}):")
        for item in broken_links:
            if isinstance(item, dict):
                source = str(item.get("source", ""))
                target = str(item.get("target", ""))
                lines.append(f"- {source} -> {target}")
            else:
                lines.append(f"- {item}")
        lines.append("")

        lines.append(f"Orphan Notes ({len(orphan_notes)}):")
        for item in orphan_notes:
            lines.append(f"- {item}")
        lines.append("")

        lines.append(f"Empty Files ({len(empty_files)}):")
        for item in empty_files:
            lines.append(f"- {item}")
        lines.append("")

        lines.append(f"Missing YAML ({len(missing_yaml)}):")
        for item in missing_yaml:
            lines.append(f"- {item}")
        lines.append("")

        lines.append(f"Duplicate Titles ({len(duplicate_titles)}):")
        for item in duplicate_titles:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                name, paths = item[0], item[1]
                lines.append(f"- {name}")
                for path in paths:
                    lines.append(f"  - {path}")
            else:
                lines.append(f"- {item}")
        lines.append("")

        lines.append(f"Large Files ({len(large_files)}):")
        for item in large_files:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                path, size = item[0], item[1]
                lines.append(f"- {path} ({size} KB)")
            else:
                lines.append(f"- {item}")

        return "\n".join(lines)

    def _copy_all_findings(self):
        if not self._last_results:
            self.status_label.setText("No findings yet. Run health check first.")
            self.status_label.setStyleSheet("color: #e74c3c;")
            return
        QApplication.clipboard().setText(self._format_findings_for_copy())
        self.status_label.setText("Copied full health findings to clipboard.")
        self.status_label.setStyleSheet("color: #2ecc71;")
    
    def _create_result_section(self, title: str, desc: str, grid, row, col) -> QListWidget:
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #2d4a6f;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        layout = QVBoxLayout(group)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #667788; font-size: 10px;")
        layout.addWidget(desc_label)
        
        list_widget = QListWidget()
        list_widget.setMaximumHeight(150)
        list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #2d4a6f;
                border-radius: 4px;
            }
            QListWidget::item { padding: 4px; }
            QListWidget::item:hover { background-color: #2d4a6f; }
        """)
        layout.addWidget(list_widget)
        
        grid.addWidget(group, row, col)
        return list_widget
    
    def _run_check(self):
        # Get vault path
        vault_path = ""
        if hasattr(self.settings_mgr, 'get'):
            vault_path = self.settings_mgr.get('obsidian', 'vault_path', '')
        
        if not vault_path:
            default = r"O:\Theophysics_Master"
            if Path(default).exists():
                vault_path = default
        
        if not vault_path or not Path(vault_path).exists():
            self.status_label.setText("⚠️ No valid vault path. Check Settings.")
            self.status_label.setStyleSheet("color: #e74c3c;")
            return
        self._current_vault_path = str(vault_path)
        
        # Clear lists
        for lst in [self.broken_links_list, self.orphan_notes_list, 
                    self.empty_files_list, self.missing_yaml_list,
                    self.duplicates_list, self.large_files_list]:
            lst.clear()
        
        self.run_btn.setEnabled(False)
        self.status_label.setText("Scanning vault...")
        self.status_label.setStyleSheet("color: #00d9ff;")
        
        self.worker = HealthCheckWorker(vault_path)
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(lambda: self.run_btn.setEnabled(True))
        self.worker.start()
    
    def _on_result(self, results: dict):
        self._apply_results(results, cached=False)
        self._save_cached_results(results)
