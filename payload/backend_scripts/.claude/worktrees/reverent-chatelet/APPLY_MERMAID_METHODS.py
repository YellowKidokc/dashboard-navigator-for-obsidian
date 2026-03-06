"""
APPLY MERMAID METHODS
Adds all Mermaid-related methods to main_window_v2.py
"""

from pathlib import Path
import shutil
from datetime import datetime

def add_mermaid_methods():
    """Add Mermaid methods to main_window_v2.py"""
    
    main_window_path = Path(__file__).parent / "ui" / "main_window_v2.py"
    
    print("=" * 70)
    print("ADDING MERMAID METHODS")
    print("=" * 70)
    
    # Read file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"[READING] {content.count(chr(10))} lines")
    
    # Check if already added
    if '_scan_mermaid_diagrams' in content:
        print("\n[WARNING] Mermaid methods appear to already exist!")
        response = input("      Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("[CANCELLED]")
            return False
    
    # Add methods at the end (before the last line)
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
        
        # Extract Mermaid blocks from each file
        mermaid_pattern = re.compile(
            r'```mermaid\\n(.*?)```',
            re.DOTALL | re.IGNORECASE
        )
        
        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                matches = mermaid_pattern.findall(content)
                
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
        
        # Update UI
        self._render_mermaid_diagrams()
        self.mermaid_count_label.setText(f"{len(self._mermaid_diagrams)} diagrams found")
        
        if len(self._mermaid_diagrams) == 0:
            QMessageBox.information(
                self,
                "No Mermaids Found",
                "No Mermaid diagrams found in the selected folder.\\n\\n"
                "Make sure your files contain Mermaid blocks like:\\n"
                "```mermaid\\\\ngraph TD\\\\n  A-->B\\\\n```"
            )
        
    except Exception as e:
        self.mermaid_count_label.setText("Error")
        QMessageBox.critical(self, "Error", f"Failed to scan for Mermaid diagrams:\\n{e}")

def _extract_paper_name(self, filename):
    """Extract paper name from filename (e.g., 'P01_Logos_Principle.md' -> 'P01')."""
    import re
    match = re.match(r'(P\\d+)', filename, re.IGNORECASE)
    return match.group(1).upper() if match else "Unknown"

def _render_mermaid_diagrams(self):
    """Render all extracted Mermaid diagrams."""
    # Clear existing diagrams
    while self.mermaid_container_layout.count():
        child = self.mermaid_container_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
    
    if not self._mermaid_diagrams:
        empty_label = QLabel("No Mermaid diagrams found. Click 'Scan for Mermaids' to extract diagrams.")
        empty_label.setStyleSheet("color: #6b7280; font-style: italic; padding: 20px;")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mermaid_container_layout.addWidget(empty_label)
        return
    
    # Group diagrams by paper
    from collections import defaultdict
    diagrams_by_paper = defaultdict(list)
    for diagram in self._mermaid_diagrams:
        diagrams_by_paper[diagram['paper']].append(diagram)
    
    # Render each paper's diagrams
    for paper, diagrams in sorted(diagrams_by_paper.items()):
        # Paper header
        paper_header = QLabel(f"📄 {paper} ({len(diagrams)} diagram{'s' if len(diagrams) > 1 else ''})")
        paper_header.setStyleSheet(f"""
            font-size: 14pt;
            font-weight: bold;
            color: {COLORS['accent_cyan']};
            padding: 10px 0;
        """)
        self.mermaid_container_layout.addWidget(paper_header)
        
        # Render each diagram
        for diagram in diagrams:
            diagram_widget = self._create_mermaid_widget(diagram)
            self.mermaid_container_layout.addWidget(diagram_widget)
    
    self.mermaid_container_layout.addStretch()

def _create_mermaid_widget(self, diagram):
    """Create a widget displaying a single Mermaid diagram."""
    widget = QWidget()
    widget.setStyleSheet(f"""
        background-color: {COLORS['bg_medium']};
        border: 1px solid {COLORS['border_dark']};
        border-radius: 8px;
    """)
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(15, 15, 15, 15)
    
    # Header with file info
    header = QLabel(f"📄 {diagram['file']} (Diagram #{diagram['index']})")
    header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10pt;")
    layout.addWidget(header)
    
    # Mermaid code display (truncated)
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
    
    # Action buttons
    btn_row = QHBoxLayout()
    
    view_btn = QPushButton("👁️ View Full Code")
    view_btn.clicked.connect(lambda: self._show_mermaid_code(diagram))
    btn_row.addWidget(view_btn)
    
    render_btn = QPushButton("🎨 Render Diagram")
    render_btn.setProperty("class", "primary")
    render_btn.clicked.connect(lambda: self._render_single_mermaid(diagram))
    btn_row.addWidget(render_btn)
    
    copy_btn = QPushButton("📋 Copy Code")
    copy_btn.clicked.connect(lambda: self._copy_mermaid_code(diagram))
    btn_row.addWidget(copy_btn)
    
    btn_row.addStretch()
    layout.addLayout(btn_row)
    
    return widget

def _show_mermaid_code(self, diagram):
    """Show full Mermaid code in a dialog."""
    dialog = QDialog(self)
    dialog.setWindowTitle(f"Mermaid Code - {diagram['file']}")
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
    """Render a single Mermaid diagram using Mermaid Chart MCP tool."""
    try:
        # TODO: Call Mermaid Chart MCP tool to render the diagram
        # For now, show a placeholder
        QMessageBox.information(
            self,
            "Render Mermaid",
            f"Rendering Mermaid diagram from {diagram['file']}\\n\\n"
            f"Code length: {len(diagram['code'])} characters\\n\\n"
            "TODO: Integrate with Mermaid Chart MCP tool to render and display image."
        )
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to render diagram:\\n{e}")

def _copy_mermaid_code(self, diagram):
    """Copy Mermaid code to clipboard."""
    from PyQt6.QtWidgets import QApplication
    clipboard = QApplication.clipboard()
    clipboard.setText(diagram['code'])
    self.mermaid_count_label.setText(f"Copied code from {diagram['file']}")

def _combine_axiom_diagrams(self):
    """Combine all axiom Mermaid diagrams into one master diagram."""
    # Filter for axiom diagrams (look for "axiom" in code or filename)
    axiom_diagrams = [
        d for d in self._mermaid_diagrams
        if 'axiom' in d['code'].lower() or 'axiom' in d['file'].lower()
    ]
    
    if not axiom_diagrams:
        QMessageBox.information(
            self,
            "No Axioms Found",
            "No Mermaid diagrams containing 'axiom' were found.\\n\\n"
            "Make sure your axiom diagrams include the word 'axiom' in the code or filename."
        )
        return
    
    # TODO: Implement logic to merge axiom diagrams
    # For now, show a dialog with the list
    msg = f"Found {len(axiom_diagrams)} axiom diagrams:\\n\\n"
    for d in axiom_diagrams:
        msg += f"• {d['paper']} - {d['file']}\\n"
    msg += "\\nTODO: Merge these into one master axiom flow diagram."
    
    QMessageBox.information(self, "Combine Axioms", msg)

# Attach methods to MainWindowV2 class
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
    
    # Write file
    print(f"\n[SAVING] Adding methods...")
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] Methods added!")
    print(f"[OK] Total lines: {content.count(chr(10))}")
    
    print("\n" + "=" * 70)
    print("[COMPLETE] Mermaid methods added successfully!")
    print("=" * 70)
    print("\nYou can now restart the app and test the Mermaid scanner!")
    
    return True

if __name__ == "__main__":
    try:
        success = add_mermaid_methods()
        if not success:
            print("\n[ERROR] Failed to add methods")
        input("\nPress Enter to close...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
