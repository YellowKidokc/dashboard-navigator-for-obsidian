# ui/tabs/api_query_tab.py
"""
API Query Tab - GUI for API Query Builder
Part of Theophysics Backend
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QGroupBox, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QCheckBox, QMessageBox, QInputDialog, QFileDialog,
    QFrame, QSplitter, QTabWidget, QListWidget, QListWidgetItem,
    QFormLayout, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

import json
from pathlib import Path
from datetime import datetime


class APIWorker(QThread):
    """Worker thread for API calls"""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(list)  # results
    error = Signal(str)
    
    def __init__(self, api_manager, endpoint_id, params, job_id=None):
        super().__init__()
        self.api_manager = api_manager
        self.endpoint_id = endpoint_id
        self.params = params
        self.job_id = job_id
    
    def run(self):
        try:
            result = self.api_manager.call_api(
                self.endpoint_id, 
                self.params,
                self.job_id
            )
            self.finished.emit([result])
        except Exception as e:
            self.error.emit(str(e))


class APIQueryTab(QWidget):
    """
    Tab for building and running API queries with:
    - Endpoint management
    - Query templates with dropdowns
    - Job saving/loading
    - Results display
    """
    
    def __init__(self, api_manager, query_engine):
        super().__init__()
        self.api_manager = api_manager
        self.query_engine = query_engine
        self.current_endpoint = None
        self.current_template = None
        self.variable_widgets = {}  # {var_name: widget}
        
        self._setup_ui()
        self._refresh_endpoints()
        self._refresh_jobs()
        self._refresh_templates()
    
    def _setup_ui(self):
        """Build the UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("🔌 API Query Builder")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # =========================================
        # LEFT PANEL - Endpoints & Jobs
        # =========================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Endpoints section
        ep_group = QGroupBox("📡 API Endpoints")
        ep_layout = QVBoxLayout(ep_group)
        
        self.endpoint_list = QListWidget()
        self.endpoint_list.itemClicked.connect(self._on_endpoint_selected)
        ep_layout.addWidget(self.endpoint_list)
        
        ep_btn_layout = QHBoxLayout()
        self.add_endpoint_btn = QPushButton("➕ Add")
        self.add_endpoint_btn.clicked.connect(self._add_endpoint)
        self.delete_endpoint_btn = QPushButton("🗑️ Delete")
        self.delete_endpoint_btn.clicked.connect(self._delete_endpoint)
        ep_btn_layout.addWidget(self.add_endpoint_btn)
        ep_btn_layout.addWidget(self.delete_endpoint_btn)
        ep_layout.addLayout(ep_btn_layout)
        
        left_layout.addWidget(ep_group)
        
        # Jobs section
        jobs_group = QGroupBox("💼 Saved Jobs")
        jobs_layout = QVBoxLayout(jobs_group)
        
        self.jobs_list = QListWidget()
        self.jobs_list.itemClicked.connect(self._on_job_selected)
        jobs_layout.addWidget(self.jobs_list)
        
        job_btn_layout = QHBoxLayout()
        self.run_job_btn = QPushButton("▶️ Run")
        self.run_job_btn.clicked.connect(self._run_selected_job)
        self.delete_job_btn = QPushButton("🗑️")
        self.delete_job_btn.clicked.connect(self._delete_job)
        job_btn_layout.addWidget(self.run_job_btn)
        job_btn_layout.addWidget(self.delete_job_btn)
        jobs_layout.addLayout(job_btn_layout)
        
        left_layout.addWidget(jobs_group)
        
        # Templates section  
        tpl_group = QGroupBox("📋 Query Templates")
        tpl_layout = QVBoxLayout(tpl_group)
        
        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        tpl_layout.addWidget(self.template_combo)
        
        left_layout.addWidget(tpl_group)
        
        splitter.addWidget(left_panel)
        
        # =========================================
        # CENTER PANEL - Query Builder
        # =========================================
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Endpoint details
        details_group = QGroupBox("🔧 Query Configuration")
        details_layout = QFormLayout(details_group)
        
        self.endpoint_name_label = QLabel("(Select an endpoint)")
        details_layout.addRow("Endpoint:", self.endpoint_name_label)
        
        self.endpoint_url_label = QLabel("")
        details_layout.addRow("URL:", self.endpoint_url_label)
        
        center_layout.addWidget(details_group)
        
        # Variable dropdowns area
        self.vars_group = QGroupBox("📊 Parameters (Dropdowns)")
        self.vars_layout = QVBoxLayout(self.vars_group)
        
        self.vars_scroll = QScrollArea()
        self.vars_scroll.setWidgetResizable(True)
        self.vars_container = QWidget()
        self.vars_container_layout = QFormLayout(self.vars_container)
        self.vars_scroll.setWidget(self.vars_container)
        self.vars_layout.addWidget(self.vars_scroll)
        
        center_layout.addWidget(self.vars_group)
        
        # Custom params
        params_group = QGroupBox("⚙️ Additional Parameters (JSON)")
        params_layout = QVBoxLayout(params_group)
        
        self.params_edit = QTextEdit()
        self.params_edit.setMaximumHeight(100)
        self.params_edit.setPlaceholderText('{"key": "value"}')
        params_layout.addWidget(self.params_edit)
        
        center_layout.addWidget(params_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.run_btn = QPushButton("▶️ Run Query")
        self.run_btn.setMinimumHeight(40)
        self.run_btn.clicked.connect(self._run_query)
        
        self.run_all_btn = QPushButton("🔄 Run ALL Options")
        self.run_all_btn.clicked.connect(self._run_all_options)
        
        self.save_job_btn = QPushButton("💾 Save as Job")
        self.save_job_btn.clicked.connect(self._save_as_job)
        
        action_layout.addWidget(self.run_btn)
        action_layout.addWidget(self.run_all_btn)
        action_layout.addWidget(self.save_job_btn)
        
        center_layout.addLayout(action_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        center_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(center_panel)
        
        # =========================================
        # RIGHT PANEL - Results
        # =========================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        results_group = QGroupBox("📋 Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        results_layout.addWidget(self.results_text)
        
        results_btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Copy")
        self.copy_btn.clicked.connect(self._copy_results)
        self.export_btn = QPushButton("💾 Export JSON")
        self.export_btn.clicked.connect(self._export_results)
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.clicked.connect(lambda: self.results_text.clear())
        
        results_btn_layout.addWidget(self.copy_btn)
        results_btn_layout.addWidget(self.export_btn)
        results_btn_layout.addWidget(self.clear_btn)
        results_layout.addLayout(results_btn_layout)
        
        right_layout.addWidget(results_group)
        
        # History
        history_group = QGroupBox("📜 Recent Calls")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Time", "Endpoint", "Status", "Call ID"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        history_layout.addWidget(self.history_table)
        
        self.refresh_history_btn = QPushButton("🔄 Refresh")
        self.refresh_history_btn.clicked.connect(self._refresh_history)
        history_layout.addWidget(self.refresh_history_btn)
        
        right_layout.addWidget(history_group)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([250, 400, 350])
        
        layout.addWidget(splitter)
    
    # =========================================
    # REFRESH METHODS
    # =========================================
    
    def _refresh_endpoints(self):
        """Refresh endpoint list"""
        self.endpoint_list.clear()
        for ep in self.api_manager.list_endpoints():
            item = QListWidgetItem(f"📡 {ep['name']}")
            item.setData(Qt.UserRole, ep['id'])
            self.endpoint_list.addItem(item)
        
        # Add built-in APIs
        from core.api_manager import BUILTIN_APIS
        for key, api in BUILTIN_APIS.items():
            item = QListWidgetItem(f"🔧 {api['name']} (Built-in)")
            item.setData(Qt.UserRole, f"builtin:{key}")
            self.endpoint_list.addItem(item)
    
    def _refresh_jobs(self):
        """Refresh jobs list"""
        self.jobs_list.clear()
        for job in self.api_manager.list_jobs():
            item = QListWidgetItem(f"💼 {job['name']}")
            item.setData(Qt.UserRole, job['id'])
            self.jobs_list.addItem(item)
    
    def _refresh_templates(self):
        """Refresh template dropdown"""
        self.template_combo.clear()
        self.template_combo.addItem("-- Select Template --")
        
        # User templates
        for name in self.query_engine.list_templates():
            self.template_combo.addItem(f"📋 {name}")
        
        # Preset templates
        from engine.api_query_engine import PRESET_TEMPLATES
        for name in PRESET_TEMPLATES.keys():
            self.template_combo.addItem(f"🔧 {name} (Preset)")
    
    def _get_endpoint_name(self, endpoint_id: str) -> str:
        """Get endpoint name from ID (checks saved and built-in)"""
        if not endpoint_id:
            return "Unknown"
        
        # Check built-in APIs first
        if endpoint_id.startswith("builtin:"):
            from core.api_manager import BUILTIN_APIS
            key = endpoint_id.replace("builtin:", "")
            if key in BUILTIN_APIS:
                return BUILTIN_APIS[key].get('name', key)
        
        # Check saved endpoints
        ep = self.api_manager.get_endpoint(endpoint_id)
        if ep:
            return ep.get('name', endpoint_id[:15])
        
        # Check all built-in by matching ID
        from core.api_manager import BUILTIN_APIS
        for key, api in BUILTIN_APIS.items():
            if endpoint_id == f"builtin:{key}":
                return api.get('name', key)
        
        return endpoint_id[:15] + "..."
    
    def _refresh_history(self):
        """Refresh call history"""
        history = self.api_manager.get_call_history(20)
        self.history_table.setRowCount(len(history))
        
        for i, call in enumerate(history):
            self.history_table.setItem(i, 0, QTableWidgetItem(
                call['timestamp'][:19] if call['timestamp'] else ""
            ))
            # Show endpoint NAME instead of ID
            ep_name = self._get_endpoint_name(call.get('endpoint_id', ''))
            self.history_table.setItem(i, 1, QTableWidgetItem(ep_name))
            status = "✅" if call['success'] else "❌"
            self.history_table.setItem(i, 2, QTableWidgetItem(status))
            self.history_table.setItem(i, 3, QTableWidgetItem(
                call['call_id'][:8] if call['call_id'] else ""
            ))
    
    # =========================================
    # EVENT HANDLERS
    # =========================================
    
    def _on_endpoint_selected(self, item):
        """Handle endpoint selection"""
        ep_id = item.data(Qt.UserRole)
        
        if ep_id.startswith("builtin:"):
            # Built-in API
            from core.api_manager import BUILTIN_APIS
            key = ep_id.replace("builtin:", "")
            api = BUILTIN_APIS.get(key, {})
            self.endpoint_name_label.setText(api.get('name', key))
            self.endpoint_url_label.setText(api.get('url', ''))
            self.current_endpoint = {"id": ep_id, **api}
        else:
            # User endpoint
            ep = self.api_manager.get_endpoint(ep_id)
            if ep:
                self.endpoint_name_label.setText(ep['name'])
                self.endpoint_url_label.setText(ep['url'])
                self.current_endpoint = ep
    
    def _on_template_selected(self, text):
        """Handle template selection"""
        if not text or text.startswith("--"):
            return
        
        # Clean up name
        name = text.replace("📋 ", "").replace("🔧 ", "").replace(" (Preset)", "")
        
        # Check presets first
        from engine.api_query_engine import PRESET_TEMPLATES
        if name in PRESET_TEMPLATES:
            self.current_template = PRESET_TEMPLATES[name]
        else:
            self.current_template = self.query_engine.get_template(name)
        
        self._build_variable_widgets()
    
    def _on_job_selected(self, item):
        """Handle job selection"""
        job_id = item.data(Qt.UserRole)
        job = self.api_manager.get_job(job_id)
        
        if job:
            self.results_text.append(f"\n📋 Job: {job['name']}")
            self.results_text.append(f"   Runs: {job.get('run_count', 0)}")
            self.results_text.append(f"   Last: {job.get('last_run', 'Never')}")
            self.results_text.append(f"   Folder: {job.get('output_folder', 'N/A')}")
    
    def _build_variable_widgets(self):
        """Build dropdown widgets for template variables"""
        # Clear existing
        for i in reversed(range(self.vars_container_layout.count())):
            item = self.vars_container_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        self.variable_widgets = {}
        
        if not self.current_template:
            return
        
        for var_name, var_config in self.current_template.variables.items():
            label = QLabel(var_config.get('label', var_name))
            
            if var_config.get('type') == 'dropdown':
                widget = QComboBox()
                for opt in var_config.get('options', []):
                    widget.addItem(str(opt))
                # Set default
                default = var_config.get('default')
                if default:
                    idx = widget.findText(str(default))
                    if idx >= 0:
                        widget.setCurrentIndex(idx)
            else:
                widget = QLineEdit()
                widget.setText(str(var_config.get('default', '')))
            
            self.vars_container_layout.addRow(label, widget)
            self.variable_widgets[var_name] = widget
    
    def _get_variable_values(self) -> dict:
        """Get current values from variable widgets"""
        values = {}
        for var_name, widget in self.variable_widgets.items():
            if isinstance(widget, QComboBox):
                text = widget.currentText()
                # Try to convert to number
                try:
                    values[var_name] = int(text)
                except ValueError:
                    try:
                        values[var_name] = float(text)
                    except ValueError:
                        values[var_name] = text
            else:
                values[var_name] = widget.text()
        return values
    
    # =========================================
    # ACTIONS
    # =========================================
    
    def _add_endpoint(self):
        """Add new endpoint dialog"""
        name, ok = QInputDialog.getText(self, "Add Endpoint", "Endpoint Name:")
        if not ok or not name:
            return
        
        url, ok = QInputDialog.getText(self, "Add Endpoint", "URL:")
        if not ok or not url:
            return
        
        method, ok = QInputDialog.getItem(
            self, "Add Endpoint", "Method:",
            ["GET", "POST"], 0, False
        )
        if not ok:
            return
        
        self.api_manager.add_endpoint(name, url, method)
        self._refresh_endpoints()
        self.results_text.append(f"✅ Added endpoint: {name}")
    
    def _delete_endpoint(self):
        """Delete selected endpoint"""
        item = self.endpoint_list.currentItem()
        if not item:
            return
        
        ep_id = item.data(Qt.UserRole)
        if ep_id.startswith("builtin:"):
            QMessageBox.warning(self, "Warning", "Cannot delete built-in endpoints")
            return
        
        self.api_manager.delete_endpoint(ep_id)
        self._refresh_endpoints()
    
    def _run_query(self):
        """Run the current query"""
        if not self.current_endpoint:
            QMessageBox.warning(self, "Warning", "Select an endpoint first")
            return
        
        # Build params
        params = {}
        
        # From template
        if self.current_template:
            var_values = self._get_variable_values()
            params = self.current_template.build_params(var_values)
        
        # From custom JSON
        try:
            custom = self.params_edit.toPlainText().strip()
            if custom:
                custom_params = json.loads(custom)
                params.update(custom_params)
        except json.JSONDecodeError:
            QMessageBox.warning(self, "Error", "Invalid JSON in custom parameters")
            return
        
        # Make the call
        self.results_text.append(f"\n🔄 Calling API...")
        self.results_text.append(f"   Params: {json.dumps(params, indent=2)}")
        
        ep_id = self.current_endpoint.get('id', '')
        
        if ep_id.startswith("builtin:"):
            # Need to register built-in first
            from core.api_manager import BUILTIN_APIS
            key = ep_id.replace("builtin:", "")
            api = BUILTIN_APIS[key]
            ep_id = self.api_manager.add_endpoint(
                api['name'], api['url'], api['method'],
                params=api.get('default_params', {})
            )
        
        result = self.api_manager.call_api(ep_id, params)
        
        if result.get('success'):
            self.results_text.append(f"✅ Success! Status: {result.get('status_code')}")
            self.results_text.append(f"📊 Data:\n{json.dumps(result.get('data', {}), indent=2)[:2000]}")
        else:
            self.results_text.append(f"❌ Error: {result.get('error', 'Unknown')}")
        
        self._refresh_history()
    
    def _run_all_options(self):
        """Run query with all variable combinations"""
        if not self.current_template or not self.current_endpoint:
            QMessageBox.warning(self, "Warning", "Select endpoint and template first")
            return
        
        # Count combinations
        import itertools
        var_options = [
            self.current_template.variables[v]["options"] 
            for v in self.current_template.variables
            if self.current_template.variables[v].get("type") == "dropdown"
        ]
        
        if var_options:
            total = len(list(itertools.product(*var_options)))
            confirm = QMessageBox.question(
                self, "Confirm",
                f"This will run {total} API calls. Continue?"
            )
            if confirm != QMessageBox.Yes:
                return
        
        self.results_text.append(f"\n🔄 Running all options...")
        # TODO: Run in thread with progress
        self.results_text.append("⚠️ Batch execution coming soon!")
    
    def _save_as_job(self):
        """Save current query as a job"""
        if not self.current_endpoint:
            QMessageBox.warning(self, "Warning", "Select an endpoint first")
            return
        
        name, ok = QInputDialog.getText(self, "Save Job", "Job Name:")
        if not ok or not name:
            return
        
        params = {}
        param_variants = {}
        
        if self.current_template:
            params = self.current_template.base_params.copy()
            for var_name, var_config in self.current_template.variables.items():
                if var_config.get("type") == "dropdown":
                    param_variants[var_name] = var_config.get("options", [])
                else:
                    params[var_name] = self._get_variable_values().get(var_name, "")
        
        ep_id = self.current_endpoint.get('id', '')
        job_id = self.api_manager.create_job(name, ep_id, params, param_variants)
        
        self._refresh_jobs()
        self.results_text.append(f"✅ Saved job: {name}")
    
    def _run_selected_job(self):
        """Run the selected job"""
        item = self.jobs_list.currentItem()
        if not item:
            return
        
        job_id = item.data(Qt.UserRole)
        self.results_text.append(f"\n🔄 Running job...")
        
        results = self.api_manager.run_job(job_id)
        
        for r in results:
            if r.get('success'):
                self.results_text.append(f"✅ Success!")
                if r.get('file_path'):
                    self.results_text.append(f"   Saved to: {r['file_path']}")
            else:
                self.results_text.append(f"❌ Error: {r.get('error')}")
        
        self._refresh_history()
    
    def _delete_job(self):
        """Delete selected job"""
        item = self.jobs_list.currentItem()
        if not item:
            return
        
        job_id = item.data(Qt.UserRole)
        self.api_manager.delete_job(job_id)
        self._refresh_jobs()
    
    def _copy_results(self):
        """Copy results to clipboard"""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.results_text.toPlainText())
    
    def _export_results(self):
        """Export results to JSON file"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "JSON Files (*.json)"
        )
        if path:
            with open(path, 'w') as f:
                f.write(self.results_text.toPlainText())
