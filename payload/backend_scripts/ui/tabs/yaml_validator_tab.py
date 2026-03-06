"""
YAML VALIDATOR TAB
==================
Quick validation of YAML frontmatter in markdown files.
Checks for required fields, valid format, consistency.
"""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from collections import Counter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QGroupBox, QTableWidget, QTableWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal


class YAMLValidatorWorker(QThread):
    """Validate YAML frontmatter."""
    progress = Signal(str)
    result = Signal(dict)
    finished = Signal()
    
    def __init__(self, scan_path: str, required_fields: List[str]):
        super().__init__()
        self.scan_path = Path(scan_path)
        self.required_fields = required_fields
    
    def run(self):
        results = {
            'total_files': 0,
            'with_yaml': 0,
            'valid_yaml': 0,
            'invalid_yaml': [],
            'missing_fields': [],
            'field_stats': Counter(),
            'field_values': {},  # field -> Counter of values
        }
        
        if not self.scan_path.exists():
            self.result.emit(results)
            self.finished.emit()
            return
        
        md_files = list(self.scan_path.rglob("*.md"))
        results['total_files'] = len(md_files)
        
        yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
        
        for i, f in enumerate(md_files):
            if i % 50 == 0:
                self.progress.emit(f"Validating {i}/{len(md_files)}...")
            
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                
                match = yaml_pattern.match(content)
                if not match:
                    continue
                
                results['with_yaml'] += 1
                yaml_text = match.group(1)
                
                try:
                    data = yaml.safe_load(yaml_text)
                    if not isinstance(data, dict):
                        results['invalid_yaml'].append({
                            'file': str(f),
                            'error': 'YAML is not a dictionary'
                        })
                        continue
                    
                    results['valid_yaml'] += 1
                    
                    # Track field usage
                    for key in data.keys():
                        results['field_stats'][key] += 1
                        
                        # Track values for select fields
                        if key in ['status', 'type', 'category', 'paper', 'domain']:
                            if key not in results['field_values']:
                                results['field_values'][key] = Counter()
                            val = str(data[key]) if data[key] else '(empty)'
                            results['field_values'][key][val] += 1
                    
                    # Check required fields
                    missing = [rf for rf in self.required_fields if rf not in data]
                    if missing:
                        results['missing_fields'].append({
                            'file': str(f),
                            'missing': missing
                        })
                    
                except yaml.YAMLError as e:
                    results['invalid_yaml'].append({
                        'file': str(f),
                        'error': str(e)[:100]
                    })
            
            except Exception as e:
                pass
        
        self.result.emit(results)
        self.finished.emit()


class YAMLValidatorTab(QWidget):
    """YAML Frontmatter Validator Tab."""
    
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
        
        header = QLabel("📋 YAML Frontmatter Validator")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d9ff;")
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        self.validate_btn = QPushButton("✓ Validate All")
        self.validate_btn.clicked.connect(self._validate)
        self.validate_btn.setStyleSheet("""
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
        header_row.addWidget(self.validate_btn)
        
        layout.addLayout(header_row)
        
        # Required fields config
        config_group = QGroupBox("Required Fields")
        config_layout = QHBoxLayout(config_group)
        
        self.field_checks = {}
        for field in ['uuid', 'title', 'type', 'status', 'created', 'paper']:
            cb = QCheckBox(field)
            cb.setChecked(field in ['uuid', 'title'])
            self.field_checks[field] = cb
            config_layout.addWidget(cb)
        
        config_layout.addStretch()
        layout.addWidget(config_group)
        
        # Status
        self.status_label = QLabel("Configure required fields and click Validate")
        self.status_label.setStyleSheet("color: #667788;")
        layout.addWidget(self.status_label)
        
        # Results
        results_row = QHBoxLayout()
        
        # Field usage table
        field_group = QGroupBox("📊 Field Usage")
        field_layout = QVBoxLayout(field_group)
        self.field_table = QTableWidget()
        self.field_table.setColumnCount(2)
        self.field_table.setHorizontalHeaderLabels(["Field", "Files"])
        self.field_table.horizontalHeader().setStretchLastSection(True)
        field_layout.addWidget(self.field_table)
        results_row.addWidget(field_group)
        
        # Errors list
        errors_group = QGroupBox("⚠️ Invalid YAML")
        errors_layout = QVBoxLayout(errors_group)
        self.errors_list = QListWidget()
        self.errors_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #2d4a6f;
            }
            QListWidget::item { padding: 4px; }
        """)
        errors_layout.addWidget(self.errors_list)
        results_row.addWidget(errors_group)
        
        layout.addLayout(results_row)
        
        # Missing fields
        missing_group = QGroupBox("📝 Missing Required Fields")
        missing_layout = QVBoxLayout(missing_group)
        self.missing_list = QListWidget()
        self.missing_list.setMaximumHeight(150)
        self.missing_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a2e;
                border: 1px solid #2d4a6f;
            }
        """)
        missing_layout.addWidget(self.missing_list)
        layout.addWidget(missing_group)
        self._load_cached_results()

    def _cache_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "config" / "ui_cache" / "yaml_validator.json"

    def _save_cached_results(self, results: dict, required_fields: List[str]):
        try:
            cache_path = self._cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "scan_path": self._current_scan_path,
                "required_fields": list(required_fields),
                "total_files": int(results.get("total_files", 0)),
                "with_yaml": int(results.get("with_yaml", 0)),
                "valid_yaml": int(results.get("valid_yaml", 0)),
                "field_stats": dict(results.get("field_stats", {})),
                "invalid_yaml": list(results.get("invalid_yaml", []))[:30],
                "missing_fields": list(results.get("missing_fields", []))[:30],
                "invalid_yaml_count": len(results.get("invalid_yaml", [])),
                "missing_fields_count": len(results.get("missing_fields", [])),
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
            required_fields = payload.get("required_fields", [])
            if isinstance(required_fields, list):
                for field, cb in self.field_checks.items():
                    cb.setChecked(field in required_fields)
            self._apply_results(payload, cached=True)
        except Exception:
            pass

    def _apply_results(self, results: dict, cached: bool = False):
        fields = results.get("field_stats", {}) if isinstance(results.get("field_stats", {}), dict) else {}
        field_items = sorted(fields.items(), key=lambda x: -x[1])[:25]
        self.field_table.setRowCount(len(field_items))
        for i, (field, count) in enumerate(field_items):
            self.field_table.setItem(i, 0, QTableWidgetItem(str(field)))
            self.field_table.setItem(i, 1, QTableWidgetItem(str(count)))

        self.errors_list.clear()
        for item in list(results.get("invalid_yaml", []))[:30]:
            file_name = Path(str(item.get("file", ""))).name if isinstance(item, dict) else str(item)
            err = item.get("error", "") if isinstance(item, dict) else ""
            self.errors_list.addItem(f"{file_name}: {str(err)[:50]}")

        self.missing_list.clear()
        for item in list(results.get("missing_fields", []))[:30]:
            if isinstance(item, dict):
                file_name = Path(str(item.get("file", ""))).name
                missing = item.get("missing", [])
                if isinstance(missing, list):
                    self.missing_list.addItem(f"{file_name}: missing {', '.join(missing)}")

        total_files = int(results.get("total_files", 0))
        with_yaml = int(results.get("with_yaml", 0))
        valid_yaml = int(results.get("valid_yaml", 0))
        valid_pct = (valid_yaml / with_yaml * 100) if with_yaml else 0
        invalid_count = int(results.get("invalid_yaml_count", len(results.get("invalid_yaml", []))))

        if cached:
            generated_at = results.get("generated_at", "").replace("T", " ")
            self.status_label.setText(
                f"Loaded cached YAML validation ({generated_at[:19]}) | "
                f"{total_files} files, {valid_yaml}/{with_yaml} valid ({valid_pct:.0f}%), {invalid_count} errors"
            )
            self.status_label.setStyleSheet("color: #8899aa;")
            return

        self.status_label.setText(
            f"✅ {total_files} files | "
            f"{with_yaml} with YAML | "
            f"{valid_yaml} valid ({valid_pct:.0f}%) | "
            f"{invalid_count} errors"
        )
        self.status_label.setStyleSheet("color: #2ecc71;")
    
    def _validate(self):
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
        
        required = [f for f, cb in self.field_checks.items() if cb.isChecked()]
        
        self.validate_btn.setEnabled(False)
        self.errors_list.clear()
        self.missing_list.clear()
        self.status_label.setText("Validating...")
        self.status_label.setStyleSheet("color: #00d9ff;")
        
        self.worker = YAMLValidatorWorker(scan_path, required)
        self.worker.progress.connect(lambda msg: self.status_label.setText(msg))
        self.worker.result.connect(self._on_result)
        self.worker.finished.connect(lambda: self.validate_btn.setEnabled(True))
        self.worker.start()
    
    def _on_result(self, results: dict):
        self._apply_results(results, cached=False)
        required = [f for f, cb in self.field_checks.items() if cb.isChecked()]
        self._save_cached_results(results, required)
