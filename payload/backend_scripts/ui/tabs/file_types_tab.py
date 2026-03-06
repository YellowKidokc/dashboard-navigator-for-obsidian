"""
FILE TYPES TAB
==============
Breakdown of file types in your vault/workspace.
Quick overview of what you're working with.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor


class FileTypesWorker(QThread):
    """Scan for file types."""
    progress = Signal(str)
    result = Signal(dict)
    finished = Signal()
    
    def __init__(self, scan_path: str):
        super().__init__()
        self.scan_path = Path(scan_path)
    
    def run(self):
        results = {
            'by_extension': Counter(),
            'by_size': Counter(),
            'by_age': {
                'today': 0,
                'week': 0,
                'month': 0,
                'older': 0,
            },
            'total_files': 0,
            'total_size': 0,
            'largest_files': [],
            'newest_files': [],
        }
        
        if not self.scan_path.exists():
            self.result.emit(results)
            self.finished.emit()
            return
        
        now = datetime.now()
        all_files: List[tuple] = []  # (path, size, mtime)
        
        self.progress.emit("Scanning files...")
        
        for f in self.scan_path.rglob("*"):
            if f.is_file():
                try:
                    stat = f.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    
                    results['total_files'] += 1
                    results['total_size'] += size
                    
                    # By extension
                    ext = f.suffix.lower() or '(no ext)'
                    results['by_extension'][ext] += 1
                    
                    # By size category
                    if size < 1024:
                        results['by_size']['< 1KB'] += 1
                    elif size < 10 * 1024:
                        results['by_size']['1-10KB'] += 1
                    elif size < 100 * 1024:
                        results['by_size']['10-100KB'] += 1
                    elif size < 1024 * 1024:
                        results['by_size']['100KB-1MB'] += 1
                    else:
                        results['by_size']['> 1MB'] += 1
                    
                    # By age
                    age = now - mtime
                    if age < timedelta(days=1):
                        results['by_age']['today'] += 1
                    elif age < timedelta(days=7):
                        results['by_age']['week'] += 1
                    elif age < timedelta(days=30):
                        results['by_age']['month'] += 1
                    else:
                        results['by_age']['older'] += 1
                    
                    all_files.append((f, size, mtime))
                    
                except:
                    pass
        
        # Get top 10 largest
        all_files.sort(key=lambda x: -x[1])
        results['largest_files'] = [(str(f), s) for f, s, _ in all_files[:10]]
        
        # Get top 10 newest
        all_files.sort(key=lambda x: -x[2].timestamp())
        results['newest_files'] = [(str(f), m) for f, _, m in all_files[:10]]
        
        self.result.emit(results)
        self.finished.emit()


class FileTypesTab(QWidget):
    """File Types Analysis Tab."""
    
    def __init__(self, settings_mgr):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.worker = None
        self._current_scan_path = ""
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_row = QHBoxLayout()
        
        header = QLabel("📁 File Types Analysis")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d9ff;")
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        self.scan_btn = QPushButton("🔍 Scan Files")
        self.scan_btn.clicked.connect(self._scan)
        self.scan_btn.setStyleSheet("""
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
        header_row.addWidget(self.scan_btn)
        
        layout.addLayout(header_row)
        
        # Status
        self.status_label = QLabel("Click 'Scan Files' to analyze")
        self.status_label.setStyleSheet("color: #667788;")
        layout.addWidget(self.status_label)
        
        # Summary cards
        summary_row = QHBoxLayout()
        
        self.total_files_card = self._create_stat_card("📄 Total Files", "--")
        self.total_size_card = self._create_stat_card("💾 Total Size", "--")
        self.today_card = self._create_stat_card("📅 Modified Today", "--")
        self.week_card = self._create_stat_card("📆 This Week", "--")
        
        summary_row.addWidget(self.total_files_card)
        summary_row.addWidget(self.total_size_card)
        summary_row.addWidget(self.today_card)
        summary_row.addWidget(self.week_card)
        
        layout.addLayout(summary_row)
        
        # Tables row
        tables_row = QHBoxLayout()
        
        # By Extension table
        ext_group = QGroupBox("📊 By Extension")
        ext_layout = QVBoxLayout(ext_group)
        self.ext_table = QTableWidget()
        self.ext_table.setColumnCount(2)
        self.ext_table.setHorizontalHeaderLabels(["Extension", "Count"])
        self.ext_table.horizontalHeader().setStretchLastSection(True)
        ext_layout.addWidget(self.ext_table)
        tables_row.addWidget(ext_group)
        
        # By Size table
        size_group = QGroupBox("📦 By Size")
        size_layout = QVBoxLayout(size_group)
        self.size_table = QTableWidget()
        self.size_table.setColumnCount(2)
        self.size_table.setHorizontalHeaderLabels(["Size Range", "Count"])
        self.size_table.horizontalHeader().setStretchLastSection(True)
        size_layout.addWidget(self.size_table)
        tables_row.addWidget(size_group)
        
        layout.addLayout(tables_row)
        
        # Largest files
        largest_group = QGroupBox("🏋️ Largest Files")
        largest_layout = QVBoxLayout(largest_group)
        self.largest_table = QTableWidget()
        self.largest_table.setColumnCount(2)
        self.largest_table.setHorizontalHeaderLabels(["File", "Size"])
        self.largest_table.horizontalHeader().setStretchLastSection(True)
        self.largest_table.setMaximumHeight(200)
        largest_layout.addWidget(self.largest_table)
        layout.addWidget(largest_group)
        self._load_cached_results()

    def _cache_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "config" / "ui_cache" / "file_types.json"

    def _save_cached_results(self, results: dict):
        try:
            cache_path = self._cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "scan_path": self._current_scan_path,
                "total_files": int(results.get("total_files", 0)),
                "total_size": int(results.get("total_size", 0)),
                "by_extension": dict(results.get("by_extension", {})),
                "by_size": dict(results.get("by_size", {})),
                "by_age": dict(results.get("by_age", {})),
                "largest_files": list(results.get("largest_files", []))[:10],
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
        self._update_card(self.total_files_card, f"{int(results.get('total_files', 0)):,}")

        total_size = int(results.get("total_size", 0))
        size_mb = total_size / (1024 * 1024)
        if size_mb > 1000:
            self._update_card(self.total_size_card, f"{size_mb/1024:.1f} GB")
        else:
            self._update_card(self.total_size_card, f"{size_mb:.1f} MB")

        by_age = results.get("by_age", {}) if isinstance(results.get("by_age", {}), dict) else {}
        self._update_card(self.today_card, str(by_age.get("today", 0)))
        self._update_card(self.week_card, str(by_age.get("week", 0)))

        by_extension = results.get("by_extension", {}) if isinstance(results.get("by_extension", {}), dict) else {}
        ext_items = sorted(by_extension.items(), key=lambda x: -x[1])[:20]
        self.ext_table.setRowCount(len(ext_items))
        for i, (ext, count) in enumerate(ext_items):
            self.ext_table.setItem(i, 0, QTableWidgetItem(str(ext)))
            self.ext_table.setItem(i, 1, QTableWidgetItem(str(count)))

        by_size = results.get("by_size", {}) if isinstance(results.get("by_size", {}), dict) else {}
        size_order = ['< 1KB', '1-10KB', '10-100KB', '100KB-1MB', '> 1MB']
        self.size_table.setRowCount(len(size_order))
        for i, size_cat in enumerate(size_order):
            self.size_table.setItem(i, 0, QTableWidgetItem(size_cat))
            self.size_table.setItem(i, 1, QTableWidgetItem(str(by_size.get(size_cat, 0))))

        largest_files = list(results.get("largest_files", []))
        self.largest_table.setRowCount(len(largest_files))
        for i, item in enumerate(largest_files):
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                path, size = item[0], int(item[1])
            else:
                path, size = str(item), 0
            self.largest_table.setItem(i, 0, QTableWidgetItem(Path(str(path)).name))
            if size > 1024 * 1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            self.largest_table.setItem(i, 1, QTableWidgetItem(size_str))

        if cached:
            generated_at = results.get("generated_at", "").replace("T", " ")
            self.status_label.setText(f"Loaded cached file scan ({generated_at[:19]})")
            self.status_label.setStyleSheet("color: #8899aa;")
            return

        self.status_label.setText(f"✅ Scanned {int(results.get('total_files', 0)):,} files")
        self.status_label.setStyleSheet("color: #2ecc71;")
    
    def _create_stat_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1e2a3a;
                border: 1px solid #2d4a6f;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 10px; color: #667788;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00d9ff;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return card
    
    def _update_card(self, card: QFrame, value: str):
        label = card.findChild(QLabel, "value")
        if label:
            label.setText(value)
    
    def _scan(self):
        scan_path = ""
        if hasattr(self.settings_mgr, 'get'):
            scan_path = self.settings_mgr.get('obsidian', 'vault_path', '')
        
        if not scan_path:
            default = r"O:\Theophysics_Master"
            if Path(default).exists():
                scan_path = default
        
        if not scan_path or not Path(scan_path).exists():
            self.status_label.setText("⚠️ No valid path")
            return
        self._current_scan_path = str(scan_path)
        
        self.scan_btn.setEnabled(False)
        self.status_label.setText("Scanning...")
        self.status_label.setStyleSheet("color: #00d9ff;")
        
        self.worker = FileTypesWorker(scan_path)
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(lambda: self.scan_btn.setEnabled(True))
        self.worker.start()
    
    def _on_result(self, results: dict):
        self._apply_results(results, cached=False)
        self._save_cached_results(results)
