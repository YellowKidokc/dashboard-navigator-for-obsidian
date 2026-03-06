"""
Ollama Workspace - Redesigned Interface
Split panel: Chat/Work Orders (left) | YAML Templates (right)
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QTextEdit, QLineEdit, QGroupBox, QCheckBox, QSpinBox, QProgressBar,
    QFrame, QFileDialog, QMessageBox, QInputDialog, QGridLayout
)
from PySide6.QtCore import Qt

def create_ollama_workspace(parent, colors):
    """Create the redesigned Ollama workspace."""
    page = QWidget()
    main_layout = QHBoxLayout(page)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(1)
    
    # ==========================================
    # LEFT PANEL: Chat & Work Orders
    # ==========================================
    left_panel = QWidget()
    left_panel.setMinimumWidth(500)
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(12, 12, 12, 12)
    
    # Header
    header = QLabel("💬 Ollama Chat & Work Orders")
    header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['accent_cyan']};")
    left_layout.addWidget(header)
    
    # Model & Status
    model_row = QHBoxLayout()
    model_row.addWidget(QLabel("Model:"))
    parent.ollama_model_combo = QComboBox()
    parent.ollama_model_combo.addItems([
        "llama3.2", "llama3.2:3b", "llama3.1", "llama3.1:8b", 
        "mistral", "mixtral", "phi3", "qwen2.5"
    ])
    parent.ollama_model_combo.setEditable(True)
    model_row.addWidget(parent.ollama_model_combo, 1)
    
    parent.ollama_check_btn = QPushButton("🔍 Check")
    parent.ollama_check_btn.setMaximumWidth(80)
    parent.ollama_check_btn.clicked.connect(parent._check_ollama_status)
    model_row.addWidget(parent.ollama_check_btn)
    
    parent.ollama_status_label = QLabel("❓ Not checked")
    parent.ollama_status_label.setStyleSheet("color: #6b7280; font-size: 10px;")
    model_row.addWidget(parent.ollama_status_label)
    left_layout.addLayout(model_row)
    
    # Chat History
    chat_group = QGroupBox("Chat History")
    chat_layout = QVBoxLayout(chat_group)
    
    parent.ollama_chat_history = QTextEdit()
    parent.ollama_chat_history.setReadOnly(True)
    parent.ollama_chat_history.setMinimumHeight(300)
    parent.ollama_chat_history.setStyleSheet(f"""
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
        font-family: 'Segoe UI', sans-serif;
        font-size: 11pt;
        padding: 8px;
    """)
    chat_layout.addWidget(parent.ollama_chat_history)
    left_layout.addWidget(chat_group)
    
    # Chat Input
    input_group = QGroupBox("Your Message")
    input_layout = QVBoxLayout(input_group)
    
    parent.ollama_chat_input = QTextEdit()
    parent.ollama_chat_input.setMaximumHeight(100)
    parent.ollama_chat_input.setPlaceholderText("Type your message to Ollama... (e.g., 'Find all mentions of grace in my papers')")
    input_layout.addWidget(parent.ollama_chat_input)
    
    chat_btn_row = QHBoxLayout()
    
    parent.ollama_send_btn = QPushButton("💬 Send Message")
    parent.ollama_send_btn.setProperty("class", "primary")
    parent.ollama_send_btn.clicked.connect(parent._send_ollama_message)
    chat_btn_row.addWidget(parent.ollama_send_btn)
    
    parent.ollama_to_work_order_btn = QPushButton("📋 Create Work Order")
    parent.ollama_to_work_order_btn.clicked.connect(parent._create_work_order_from_chat)
    chat_btn_row.addWidget(parent.ollama_to_work_order_btn)
    
    clear_chat_btn = QPushButton("🗑️ Clear")
    clear_chat_btn.setMaximumWidth(80)
    clear_chat_btn.clicked.connect(lambda: parent.ollama_chat_history.clear())
    chat_btn_row.addWidget(clear_chat_btn)
    
    input_layout.addLayout(chat_btn_row)
    left_layout.addWidget(input_group)
    
    # Work Orders Section
    work_order_group = QGroupBox("📋 Work Orders & Batch Operations")
    work_order_layout = QVBoxLayout(work_order_group)
    
    # Folder selection
    folder_row = QHBoxLayout()
    folder_row.addWidget(QLabel("Target Folder:"))
    parent.ollama_folder_edit = QLineEdit()
    parent.ollama_folder_edit.setPlaceholderText("Select folder for batch operations...")
    folder_row.addWidget(parent.ollama_folder_edit, 1)
    
    browse_btn = QPushButton("📁")
    browse_btn.setMaximumWidth(40)
    browse_btn.clicked.connect(parent._browse_ollama_folder)
    folder_row.addWidget(browse_btn)
    work_order_layout.addLayout(folder_row)
    
    # Work order prompt
    parent.ollama_work_order_prompt = QTextEdit()
    parent.ollama_work_order_prompt.setMaximumHeight(80)
    parent.ollama_work_order_prompt.setPlaceholderText("Work order prompt (e.g., 'Add tags based on content', 'Summarize each paper')...")
    work_order_layout.addWidget(parent.ollama_work_order_prompt)
    
    # Options
    options_row = QHBoxLayout()
    parent.ollama_recursive_check = QCheckBox("Recursive")
    parent.ollama_recursive_check.setChecked(True)
    options_row.addWidget(parent.ollama_recursive_check)
    
    parent.ollama_dry_run_check = QCheckBox("Dry run")
    options_row.addWidget(parent.ollama_dry_run_check)
    
    options_row.addWidget(QLabel("Limit:"))
    parent.ollama_limit_spin = QSpinBox()
    parent.ollama_limit_spin.setRange(0, 1000)
    parent.ollama_limit_spin.setValue(0)
    parent.ollama_limit_spin.setSpecialValueText("All")
    parent.ollama_limit_spin.setMaximumWidth(80)
    options_row.addWidget(parent.ollama_limit_spin)
    options_row.addStretch()
    work_order_layout.addLayout(options_row)
    
    # Execute button
    execute_row = QHBoxLayout()
    parent.ollama_execute_btn = QPushButton("🚀 Execute Work Order")
    parent.ollama_execute_btn.setProperty("class", "success")
    parent.ollama_execute_btn.setMinimumHeight(40)
    parent.ollama_execute_btn.clicked.connect(parent._execute_work_order)
    execute_row.addWidget(parent.ollama_execute_btn)
    
    parent.ollama_stop_btn = QPushButton("⏹️ Stop")
    parent.ollama_stop_btn.setEnabled(False)
    parent.ollama_stop_btn.clicked.connect(parent._stop_ollama_processing)
    execute_row.addWidget(parent.ollama_stop_btn)
    work_order_layout.addLayout(execute_row)
    
    # Progress
    parent.ollama_progress = QProgressBar()
    parent.ollama_progress.setVisible(False)
    work_order_layout.addWidget(parent.ollama_progress)
    
    left_layout.addWidget(work_order_group)
    
    # Processing log (compact)
    log_group = QGroupBox("📋 Log")
    log_layout = QVBoxLayout(log_group)
    
    parent.ollama_log = QTextEdit()
    parent.ollama_log.setReadOnly(True)
    parent.ollama_log.setMaximumHeight(150)
    parent.ollama_log.setStyleSheet(f"""
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
        font-family: 'Consolas', monospace;
        font-size: 9pt;
    """)
    log_layout.addWidget(parent.ollama_log)
    left_layout.addWidget(log_group)
    
    left_layout.addStretch()
    main_layout.addWidget(left_panel)
    
    # Separator
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.VLine)
    separator.setStyleSheet(f"background-color: {colors['border_dark']};")
    main_layout.addWidget(separator)
    
    # ==========================================
    # RIGHT PANEL: YAML Templates
    # ==========================================
    right_panel = QWidget()
    right_panel.setMinimumWidth(400)
    right_layout = QVBoxLayout(right_panel)
    right_layout.setContentsMargins(12, 12, 12, 12)
    
    # Header
    template_header = QLabel("📝 YAML Templates")
    template_header.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {colors['accent_cyan']};")
    right_layout.addWidget(template_header)
    
    # Template selector
    template_select_row = QHBoxLayout()
    template_select_row.addWidget(QLabel("Template:"))
    parent.ollama_template_combo = QComboBox()
    parent.ollama_template_combo.currentTextChanged.connect(parent._load_yaml_template)
    template_select_row.addWidget(parent.ollama_template_combo, 1)
    
    new_template_btn = QPushButton("➕")
    new_template_btn.setMaximumWidth(40)
    new_template_btn.setToolTip("Create new template")
    new_template_btn.clicked.connect(parent._create_new_yaml_template)
    template_select_row.addWidget(new_template_btn)
    
    delete_template_btn = QPushButton("🗑️")
    delete_template_btn.setMaximumWidth(40)
    delete_template_btn.setToolTip("Delete template")
    delete_template_btn.clicked.connect(parent._delete_yaml_template)
    template_select_row.addWidget(delete_template_btn)
    
    right_layout.addLayout(template_select_row)
    
    # Template editor
    editor_group = QGroupBox("Edit Template")
    editor_layout = QVBoxLayout(editor_group)
    
    parent.ollama_yaml_editor = QTextEdit()
    parent.ollama_yaml_editor.setPlaceholderText("Enter your YAML template here...\n\nExample:\n---\ntags: []\ncategory: \nsummary: \n---")
    parent.ollama_yaml_editor.setStyleSheet(f"""
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 10pt;
    """)
    editor_layout.addWidget(parent.ollama_yaml_editor)
    
    # Template actions
    template_btn_row = QHBoxLayout()
    
    save_template_btn = QPushButton("💾 Save Template")
    save_template_btn.clicked.connect(parent._save_yaml_template)
    template_btn_row.addWidget(save_template_btn)
    
    validate_btn = QPushButton("✓ Validate YAML")
    validate_btn.clicked.connect(parent._validate_yaml_template)
    template_btn_row.addWidget(validate_btn)
    
    template_btn_row.addStretch()
    editor_layout.addLayout(template_btn_row)
    
    right_layout.addWidget(editor_group)
    
    # Template usage options
    usage_group = QGroupBox("Template Usage")
    usage_layout = QVBoxLayout(usage_group)
    
    parent.ollama_template_position_combo = QComboBox()
    parent.ollama_template_position_combo.addItems([
        "Top of file (frontmatter)",
        "Bottom of file (footer)",
        "Custom position"
    ])
    usage_layout.addWidget(parent.ollama_template_position_combo)
    
    parent.ollama_skip_fm_check = QCheckBox("Skip files with existing frontmatter")
    usage_layout.addWidget(parent.ollama_skip_fm_check)
    
    parent.prompt_enabled_check = QCheckBox("Include hidden prompt in YAML")
    parent.prompt_enabled_check.setChecked(True)
    usage_layout.addWidget(parent.prompt_enabled_check)
    
    right_layout.addWidget(usage_group)
    
    # Hidden prompt section (collapsible)
    hidden_prompt_group = QGroupBox("🔒 Hidden Prompt (Optional)")
    hidden_prompt_layout = QVBoxLayout(hidden_prompt_group)
    
    parent.ollama_hidden_prompt = QTextEdit()
    parent.ollama_hidden_prompt.setMaximumHeight(100)
    parent.ollama_hidden_prompt.setPlaceholderText("Hidden prompt to embed in YAML...")
    parent.ollama_hidden_prompt.setPlainText("# Theophysics Framework Note\n# Part of the unified axiom system\n# See: https://theophysics.substack.com")
    hidden_prompt_layout.addWidget(parent.ollama_hidden_prompt)
    
    right_layout.addWidget(hidden_prompt_group)
    
    # Statistics
    stats_group = QGroupBox("📊 Statistics")
    stats_layout = QGridLayout(stats_group)
    
    parent.ollama_stats = {
        'processed': QLabel("0"),
        'updated': QLabel("0"),
        'skipped': QLabel("0"),
        'errors': QLabel("0"),
    }
    
    stats_items = [("Processed", 'processed'), ("Updated", 'updated'), ("Skipped", 'skipped'), ("Errors", 'errors')]
    for i, (label, key) in enumerate(stats_items):
        lbl = QLabel(f"{label}:")
        lbl.setStyleSheet("font-weight: bold; font-size: 9pt;")
        stats_layout.addWidget(lbl, i // 2, (i % 2) * 2)
        parent.ollama_stats[key].setStyleSheet(f"font-size: 14px; color: {colors['accent_green']};")
        stats_layout.addWidget(parent.ollama_stats[key], i // 2, (i % 2) * 2 + 1)
    
    right_layout.addWidget(stats_group)
    right_layout.addStretch()
    
    main_layout.addWidget(right_panel)
    
    # Initialize
    parent._ollama_worker = None
    parent._load_yaml_templates()
    
    return page
