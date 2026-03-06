"""
FORCE ADD MERMAID METHODS
Adds Mermaid methods without checking if they exist
"""

from pathlib import Path

main_window_path = Path(r"O:\Theophysics_Backend\Backend Python\ui\main_window_v2.py")

print("=" * 70)
print("FORCE ADDING MERMAID METHODS")
print("=" * 70)

with open(main_window_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"[READING] {content.count(chr(10))} lines")

# Add methods at the end
methods_code = '''

def _scan_mermaid_diagrams(self):
    """Scan folder for Mermaid diagrams in markdown files."""
    folder = self.semantic_folder_edit.text()
    if not folder:
        QMessageBox.warning(self, "No Folder", "Please select a folder to scan.")
        return
    
    self.mermaid_count_label.setText("Scanning...")
    self._mermaid_diagrams = []
    
    try:
        from pathlib import Path
        import re
        
        folder_path = Path(folder)
        recursive = self.semantic_recursive_check.isChecked()
        
        # Get all markdown files
        if recursive:
            md_files = list(folder_path.rglob("*.md"))
        else:
            md_files = list(folder_path.glob("*.md"))
        
        # Extract Mermaid blocks
        mermaid_pattern = re.compile(r'```mermaid\\n(.*?)```', re.DOTALL | re.IGNORECASE)
        
        for md_file in md_files:
            try:
                file_content = md_file.read_text(encoding='utf-8')
                matches = mermaid_pattern.findall(file_content)
                
                for i, mermaid_code in enumerate(matches):
                    self._mermaid_diagrams.append({
                        'file': md_file.name,
                        'full_path': str(md_file),
                        'index': i + 1,
                        'code': mermaid_code.strip(),
                        'paper': self._extract_paper_name(md_file.name)
                    })
            except Exception as e:
                print(f"Error reading {md_file.name}: {e}")
        
        self._render_mermaid_diagrams()
        self.mermaid_count_label.setText(f"{len(self._mermaid_diagrams)} diagrams found")
        
        if len(self._mermaid_diagrams) == 0:
            QMessageBox.information(
                self, "No Mermaids Found",
                "No Mermaid diagrams found.\\n\\nMake sure files contain:\\n```mermaid\\\\ngraph TD\\\\n  A-->B\\\\n```"
            )
    except Exception as e:
        self.mermaid_count_label.setText("Error")
        QMessageBox.critical(self, "Error", f"Failed to scan:\\n{e}")

def _extract_paper_name(self, filename):
    """Extract paper name from filename."""
    import re
    match = re.match(r'(P\\d+)', filename, re.IGNORECASE)
    return match.group(1).upper() if match else "Unknown"

def _render_mermaid_diagrams(self):
    """Render all extracted Mermaid diagrams."""
    while self.mermaid_container_layout.count():
        child = self.mermaid_container_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
    if not self._mermaid_diagrams:
        empty_label = QLabel("No diagrams. Click 'Scan for Mermaids'.")
        empty_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 20px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mermaid_container_layout.addWidget(empty_label)
        return
    
    from collections import defaultdict
    diagrams_by_paper = defaultdict(list)
    for diagram in self._mermaid_diagrams:
        diagrams_by_paper[diagram['paper']].append(diagram)
    
    for paper, diagrams in sorted(diagrams_by_paper.items()):
        paper_header = QLabel(f"📄 {paper} ({len(diagrams)} diagram{'s' if len(diagrams) > 1 else ''})")
        paper_header.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: bold;
            color: {COLORS['accent_cyan']};
            padding: 10px 0;
        """)
        self.mermaid_container_layout.addWidget(paper_header)
        
        for diagram in diagrams:
            diagram_widget = self._create_mermaid_widget(diagram)
            self.mermaid_container_layout.addWidget(diagram_widget)
    
    self.mermaid_container_layout.addStretch()

def _create_mermaid_widget(self, diagram):
    """Create widget for single Mermaid diagram."""
    widget = QWidget()
    widget.setStyleSheet(f"""
        background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 8px;
    """)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(15, 15, 15, 15)
    
    header = QLabel(f"📄 {diagram['file']} (Diagram #{diagram['index']})")
    header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
    layout.addWidget(header)
    
    code_preview = diagram['code'][:200] + ('...' if len(diagram['code']) > 200 else '')
    code_label = QLabel(f"<pre>{code_preview}</pre>")
    code_label.setWordWrap(True)
    code_label.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_muted']};
        padding: 10px;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 9pt;
    """)
    layout.addWidget(code_label)
    
    btn_row = QHBoxLayout()
    
    view_btn = QPushButton("👁️ View Full")
    view_btn.clicked.connect(lambda: self._show_mermaid_code(diagram))
    btn_row.addWidget(view_btn)
    
    render_btn = QPushButton("🎨 Render")
    render_btn.setProperty("class", "primary")
    render_btn.clicked.connect(lambda: self._render_single_mermaid(diagram))
    btn_row.addWidget(render_btn)
    
    copy_btn = QPushButton("📋 Copy")
    copy_btn.clicked.connect(lambda: self._copy_mermaid_code(diagram))
    btn_row.addWidget(copy_btn)
    
    btn_row.addStretch()
    layout.addLayout(btn_row)
    
    return widget

def _show_mermaid_code(self, diagram):
    """Show full Mermaid code."""
    dialog = QDialog(self)
    dialog.setWindowTitle(f"Mermaid - {diagram['file']}")
    dialog.setMinimumSize(600, 400)
    
    layout = QVBoxLayout(dialog)
    
    text_edit = QTextEdit()
    text_edit.setPlainText(diagram['code'])
    text_edit.setReadOnly(True)
    text_edit.setStyleSheet(f"""
        background-color: {COLORS['bg_dark']};
        color: {COLORS['text_primary']};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
    """)
    layout.addWidget(text_edit)
    
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    dialog.exec()

def _render_single_mermaid(self, diagram):
    """Render single Mermaid diagram."""
    QMessageBox.information(
        self, "Render Mermaid",
        f"Rendering: {diagram['file']}\\n\\nCode: {len(diagram['code'])} chars\\n\\nTODO: MCP integration"
    )

def _copy_mermaid_code(self, diagram):
    """Copy Mermaid code to clipboard."""
    from PyQt6.QtWidgets import QApplication
    clipboard = QApplication.clipboard()
    clipboard.setText(diagram['code'])
    self.mermaid_count_label.setText(f"Copied from {diagram['file']}")

def _combine_axiom_diagrams(self):
    """Combine all axiom diagrams."""
    axiom_diagrams = [
        d for d in self._mermaid_diagrams
        if 'axiom' in d['code'].lower() or 'axiom' in d['file'].lower()
    ]
    
    if not axiom_diagrams:
        QMessageBox.information(
            self, "No Axioms",
            "No axiom diagrams found.\\n\\nMake sure diagrams contain 'axiom' in code or filename."
        )
        return
    
    msg = f"Found {len(axiom_diagrams)} axiom diagrams:\\n\\n"
    for d in axiom_diagrams:
        msg += f"• {d['paper']} - {d['file']}\\n"
    msg += "\\nTODO: Merge into master diagram"
    
    QMessageBox.information(self, "Combine Axioms", msg)

# Attach to class
MainWindowV2._scan_mermaid_diagrams = _scan_mermaid_diagrams
MainWindowV2._extract_paper_name = _extract_paper_name
MainWindowV2._render_mermaid_diagrams = _render_mermaid_diagrams
MainWindowV2._create_mermaid_widget = _create_mermaid_widget
MainWindowV2._show_mermaid_code = _show_mermaid_code
MainWindowV2._render_single_mermaid = _render_single_mermaid
MainWindowV2._copy_mermaid_code = _copy_mermaid_code
MainWindowV2._combine_axiom_diagrams = _combine_axiom_diagrams
'''

content = content.rstrip() + methods_code + '\n'

with open(main_window_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"[OK] Methods added!")
print(f"[OK] Total lines: {content.count(chr(10))}")
print("\n[COMPLETE] Mermaid integration finished!")
print("Restart app to test!")
