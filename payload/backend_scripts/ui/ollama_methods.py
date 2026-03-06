"""
Ollama Workspace Methods
Helper methods for the redesigned Ollama interface
"""

from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QInputDialog, QFileDialog

def check_ollama_status(self):
    """Check if Ollama is running and model is available."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            self.ollama_status_label.setText(f"✓ Running ({len(models)} models)")
            self.ollama_status_label.setStyleSheet("color: #22c55e;")
            
            # Update combo with available models
            current = self.ollama_model_combo.currentText()
            self.ollama_model_combo.clear()
            self.ollama_model_combo.addItems(model_names)
            if current in model_names:
                self.ollama_model_combo.setCurrentText(current)
        else:
            self.ollama_status_label.setText("✗ Not responding")
            self.ollama_status_label.setStyleSheet("color: #f44747;")
    except Exception as e:
        self.ollama_status_label.setText("✗ Not running")
        self.ollama_status_label.setStyleSheet("color: #f44747;")
        QMessageBox.warning(self, "Ollama Not Running", 
            f"Could not connect to Ollama.\n\nMake sure Ollama is installed and running.\n\nError: {e}")

def send_ollama_message(self):
    """Send a message to Ollama and get response."""
    message = self.ollama_chat_input.toPlainText().strip()
    if not message:
        return
    
    model = self.ollama_model_combo.currentText()
    
    # Add user message to chat
    self.ollama_chat_history.append(f"\n**You:** {message}\n")
    self.ollama_chat_input.clear()
    
    # Send to Ollama
    try:
        import requests
        
        self.ollama_send_btn.setEnabled(False)
        self.ollama_send_btn.setText("⏳ Thinking...")
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": message,
                "stream": False
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            reply = result.get('response', 'No response')
            self.ollama_chat_history.append(f"**Ollama:** {reply}\n")
        else:
            self.ollama_chat_history.append(f"**Error:** Failed to get response (status {response.status_code})\n")
    
    except Exception as e:
        self.ollama_chat_history.append(f"**Error:** {str(e)}\n")
    
    finally:
        self.ollama_send_btn.setEnabled(True)
        self.ollama_send_btn.setText("💬 Send Message")

def create_work_order_from_chat(self):
    """Convert the last chat message into a work order prompt."""
    message = self.ollama_chat_input.toPlainText().strip()
    if message:
        self.ollama_work_order_prompt.setPlainText(message)
        QMessageBox.information(self, "Work Order Created", 
            "Chat message converted to work order prompt.\n\nSelect a folder and click 'Execute Work Order' to run.")

def load_yaml_templates(self):
    """Load saved YAML templates from config."""
    config_path = Path(__file__).parent.parent / "config" / "ollama_templates"
    config_path.mkdir(parents=True, exist_ok=True)
    
    templates = []
    for template_file in config_path.glob("*.yaml"):
        templates.append(template_file.stem)
    
    self.ollama_template_combo.clear()
    if templates:
        self.ollama_template_combo.addItems(templates)
    else:
        # Create default template
        default_yaml = """---
tags: []
category: 
author: 
date: {{date}}
summary: 
---"""
        default_path = config_path / "default.yaml"
        default_path.write_text(default_yaml, encoding='utf-8')
        self.ollama_template_combo.addItem("default")

def load_yaml_template(self, template_name):
    """Load a specific YAML template into the editor."""
    if not template_name:
        return
    
    config_path = Path(__file__).parent.parent / "config" / "ollama_templates" / f"{template_name}.yaml"
    if config_path.exists():
        try:
            content = config_path.read_text(encoding='utf-8')
            self.ollama_yaml_editor.setPlainText(content)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load template:\n{e}")

def save_yaml_template(self):
    """Save the current YAML template."""
    template_name = self.ollama_template_combo.currentText()
    if not template_name:
        template_name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not template_name:
            return
    
    config_path = Path(__file__).parent.parent / "config" / "ollama_templates" / f"{template_name}.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        content = self.ollama_yaml_editor.toPlainText()
        config_path.write_text(content, encoding='utf-8')
        QMessageBox.information(self, "Saved", f"Template '{template_name}' saved successfully.")
        
        # Refresh combo
        self._load_yaml_templates()
        self.ollama_template_combo.setCurrentText(template_name)
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to save template:\n{e}")

def create_new_yaml_template(self):
    """Create a new YAML template."""
    name, ok = QInputDialog.getText(self, "New Template", "Template name:")
    if ok and name:
        self.ollama_yaml_editor.clear()
        self.ollama_yaml_editor.setPlainText("---\n\n---")
        self.ollama_template_combo.setCurrentText(name)

def delete_yaml_template(self):
    """Delete the current YAML template."""
    template_name = self.ollama_template_combo.currentText()
    if not template_name:
        return
    
    confirm = QMessageBox.question(
        self, "Delete Template",
        f"Delete template '{template_name}'?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if confirm == QMessageBox.StandardButton.Yes:
        config_path = Path(__file__).parent.parent / "config" / "ollama_templates" / f"{template_name}.yaml"
        if config_path.exists():
            config_path.unlink()
            self._load_yaml_templates()
            QMessageBox.information(self, "Deleted", f"Template '{template_name}' deleted.")

def validate_yaml_template(self):
    """Validate the YAML syntax."""
    try:
        import yaml
        content = self.ollama_yaml_editor.toPlainText()
        yaml.safe_load(content)
        QMessageBox.information(self, "Valid", "YAML syntax is valid!")
    except Exception as e:
        QMessageBox.warning(self, "Invalid YAML", f"YAML syntax error:\n\n{e}")

def execute_work_order(self):
    """Execute the work order on selected folder."""
    folder = self.ollama_folder_edit.text()
    prompt = self.ollama_work_order_prompt.toPlainText().strip()
    
    if not folder or not Path(folder).exists():
        QMessageBox.warning(self, "No Folder", "Please select a valid folder.")
        return
    
    if not prompt:
        QMessageBox.warning(self, "No Prompt", "Please enter a work order prompt.")
        return
    
    # Log the work order
    self.ollama_log.append(f"[Work Order] Starting batch operation...")
    self.ollama_log.append(f"[Folder] {folder}")
    self.ollama_log.append(f"[Prompt] {prompt}")
    
    # TODO: Implement actual Ollama batch processing
    QMessageBox.information(self, "Work Order", 
        "Work order execution would start here.\n\n(Full implementation pending)")

def browse_ollama_folder(self):
    """Browse for a folder."""
    folder = QFileDialog.getExistingDirectory(self, "Select Folder")
    if folder:
        self.ollama_folder_edit.setText(folder)

def stop_ollama_processing(self):
    """Stop the current Ollama processing."""
    if hasattr(self, '_ollama_worker') and self._ollama_worker:
        self._ollama_worker.stop()
        self.ollama_log.append("[STOP] Processing stopped by user.")

def save_ollama_prompt_default(self):
    """Save the hidden prompt as default."""
    config_path = Path(__file__).parent.parent / "config" / "ollama_hidden_prompt.txt"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(self.ollama_hidden_prompt.toPlainText(), encoding='utf-8')
    QMessageBox.information(self, "Saved", "Hidden prompt saved as default.")

def preview_ollama_yaml(self):
    """Preview how YAML would look in first file."""
    folder = self.ollama_folder_edit.text()
    if not folder or not Path(folder).exists():
        QMessageBox.warning(self, "No Folder", "Please select a folder first.")
        return
    
    # Find first markdown file
    md_files = list(Path(folder).rglob("*.md"))
    if not md_files:
        QMessageBox.warning(self, "No Files", "No markdown files found in folder.")
        return
    
    first_file = md_files[0]
    template = self.ollama_yaml_editor.toPlainText()
    
    preview_text = f"File: {first_file.name}\n\n{template}\n\n[Rest of file content...]"
    
    QMessageBox.information(self, "Preview", preview_text)

def export_ollama_log(self):
    """Export the processing log."""
    file_path, _ = QFileDialog.getSaveFileName(self, "Export Log", "", "Text Files (*.txt)")
    if file_path:
        try:
            Path(file_path).write_text(self.ollama_log.toPlainText(), encoding='utf-8')
            QMessageBox.information(self, "Exported", f"Log exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export log:\n{e}")
