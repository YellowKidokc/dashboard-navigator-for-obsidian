"""
Main Application Window - Data Command Center

Tabbed interface with:
- Scripts (API downloaders)
- PostgreSQL Browser
- Conversions (file format converters)
- Settings/Data Lake in header
"""

import logging
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from typing import Callable, Optional
import threading
import os

import customtkinter as ctk

from .script_panel import ScriptPanel
from .log_panel import LogPanel

logger = logging.getLogger(__name__)


class AppWindow(ctk.CTk):
    """Main application window with tabbed interface."""

    def __init__(
        self,
        title: str = "Data Command Center",
        geometry: str = "1400x900",
    ):
        super().__init__()

        self.title(title)
        self.geometry(geometry)
        self.minsize(1000, 700)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Callbacks
        self._on_run_script: Callable | None = None
        self._on_schedule_script: Callable | None = None
        self._on_refresh_scripts: Callable | None = None
        
        # Connection resolver
        self.connection_resolver = None
        self.current_pg_connection = None
        
        # Data lake path
        self.data_lake_path = Path("./data_lake")

        # Build UI
        self._create_layout()
        self._create_header()
        self._create_tabs()
        self._create_status_bar()

    def _create_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Tabs
        self.grid_rowconfigure(2, weight=0)  # Status

    def _create_header(self) -> None:
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header.grid_columnconfigure(2, weight=1)

        # Title
        ctk.CTkLabel(
            self.header,
            text="⚡ Data Command Center",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Subtitle
        ctk.CTkLabel(
            self.header,
            text="Theophysics Infrastructure v1.0",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).grid(row=0, column=1, padx=10, pady=15, sticky="w")
        
        # Right side - Data Lake & Settings
        right_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        right_frame.grid(row=0, column=3, padx=15, pady=10, sticky="e")
        
        # Data Lake path indicator
        self.data_lake_btn = ctk.CTkButton(
            right_frame,
            text=f"📁 {self.data_lake_path}",
            width=200,
            command=self._change_data_lake_path,
            fg_color="transparent",
            border_width=1
        )
        self.data_lake_btn.pack(side="left", padx=5)
        
        # Settings button
        ctk.CTkButton(
            right_frame,
            text="⚙️",
            width=40,
            command=self._open_settings
        ).pack(side="left", padx=5)

    def _create_tabs(self) -> None:
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Tabs
        self.tab_scripts = self.tabview.add("📜 Scripts")
        self.tab_postgres = self.tabview.add("🐘 PostgreSQL")
        self.tab_conversions = self.tabview.add("🔄 Conversions")
        
        self._build_scripts_tab()
        self._build_postgres_tab()
        self._build_conversions_tab()

    def _build_scripts_tab(self) -> None:
        """Build the Scripts tab content."""
        self.tab_scripts.grid_columnconfigure(0, weight=2)
        self.tab_scripts.grid_columnconfigure(1, weight=3)
        self.tab_scripts.grid_rowconfigure(0, weight=1)

        self.script_panel = ScriptPanel(
            self.tab_scripts,
            on_run=self._handle_run,
            on_schedule=self._handle_schedule,
        )
        self.script_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.log_panel = LogPanel(self.tab_scripts)
        self.log_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Bottom buttons
        btn_frame = ctk.CTkFrame(self.tab_scripts, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        
        ctk.CTkButton(
            btn_frame, text="↻ Refresh Scripts", width=140,
            command=self._handle_refresh
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame, text="📂 Open Data Lake", width=140,
            command=self._open_data_lake_folder
        ).pack(side="left", padx=5)

    def _build_postgres_tab(self) -> None:
        """Build the PostgreSQL browser tab."""
        self.tab_postgres.grid_columnconfigure(0, weight=1)
        self.tab_postgres.grid_columnconfigure(1, weight=2)
        self.tab_postgres.grid_rowconfigure(1, weight=1)
        
        # Top bar
        pg_top = ctk.CTkFrame(self.tab_postgres)
        pg_top.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(pg_top, text="Connection:", font=("", 13)).pack(side="left", padx=10)
        
        self.pg_connection_var = ctk.StringVar(value="Select database...")
        self.pg_connection_dropdown = ctk.CTkOptionMenu(
            pg_top, variable=self.pg_connection_var,
            values=["Select database..."],
            command=self._on_pg_connection_change,
            width=200
        )
        self.pg_connection_dropdown.pack(side="left", padx=5)
        
        ctk.CTkButton(pg_top, text="Connect", width=100, command=self._pg_connect).pack(side="left", padx=5)
        ctk.CTkButton(pg_top, text="↻ Refresh", width=80, command=self._pg_refresh_schema).pack(side="left", padx=5)
        
        self.pg_status = ctk.CTkLabel(pg_top, text="● Disconnected", text_color="gray")
        self.pg_status.pack(side="right", padx=15)
        
        # Left - schema tree
        pg_left = ctk.CTkFrame(self.tab_postgres, width=350)
        pg_left.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        pg_left.grid_propagate(False)
        pg_left.grid_rowconfigure(1, weight=1)
        pg_left.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(pg_left, text="📊 Schemas & Tables", font=("", 14, "bold")).grid(row=0, column=0, pady=10, sticky="w", padx=10)
        
        tree_frame = ctk.CTkFrame(pg_left)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=25)
        style.configure("Treeview.Heading", background="#3b3b3b", foreground="white")
        style.map("Treeview", background=[("selected", "#1f538d")])
        
        self.schema_tree = ttk.Treeview(tree_frame, show="tree headings", columns=("type", "rows"), selectmode="browse")
        self.schema_tree.heading("#0", text="Name", anchor="w")
        self.schema_tree.heading("type", text="Type", anchor="w")
        self.schema_tree.heading("rows", text="Rows", anchor="e")
        self.schema_tree.column("#0", width=180, minwidth=100)
        self.schema_tree.column("type", width=80, minwidth=60)
        self.schema_tree.column("rows", width=70, minwidth=50)
        self.schema_tree.grid(row=0, column=0, sticky="nsew")
        self.schema_tree.bind("<<TreeviewSelect>>", self._on_table_select)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.schema_tree.yview)
        tree_scroll.grid(row=0, column=1, sticky="ns")
        self.schema_tree.configure(yscrollcommand=tree_scroll.set)
        
        # Right - table details
        pg_right = ctk.CTkFrame(self.tab_postgres)
        pg_right.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        pg_right.grid_rowconfigure(2, weight=1)
        pg_right.grid_rowconfigure(4, weight=2)
        pg_right.grid_columnconfigure(0, weight=1)
        
        # Table info
        self.table_info_frame = ctk.CTkFrame(pg_right)
        self.table_info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        self.table_name_label = ctk.CTkLabel(self.table_info_frame, text="Select a table", font=("", 16, "bold"))
        self.table_name_label.pack(anchor="w")
        
        self.table_info_label = ctk.CTkLabel(self.table_info_frame, text="", text_color="gray")
        self.table_info_label.pack(anchor="w")
        
        # Columns
        ctk.CTkLabel(pg_right, text="📋 Columns", font=("", 13, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=(10, 5))
        self.columns_frame = ctk.CTkScrollableFrame(pg_right, height=150)
        self.columns_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Data preview
        ctk.CTkLabel(pg_right, text="👁 Data Preview", font=("", 13, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=(15, 5))
        
        preview_frame = ctk.CTkFrame(pg_right)
        preview_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=5)
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        self.data_tree = ttk.Treeview(preview_frame, show="headings")
        self.data_tree.grid(row=0, column=0, sticky="nsew")
        
        data_scroll_y = ttk.Scrollbar(preview_frame, orient="vertical", command=self.data_tree.yview)
        data_scroll_y.grid(row=0, column=1, sticky="ns")
        data_scroll_x = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.data_tree.xview)
        data_scroll_x.grid(row=1, column=0, sticky="ew")
        self.data_tree.configure(yscrollcommand=data_scroll_y.set, xscrollcommand=data_scroll_x.set)
        
        # Import/Export buttons
        import_frame = ctk.CTkFrame(pg_right, fg_color="transparent")
        import_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(import_frame, text="📥 Import CSV", command=self._pg_import_csv, width=150).pack(side="left", padx=5)
        ctk.CTkButton(import_frame, text="📤 Export Table", command=self._pg_export_csv, width=150).pack(side="left", padx=5)

    def _build_conversions_tab(self) -> None:
        """Build the Conversions tab for file format conversion."""
        self.tab_conversions.grid_columnconfigure(0, weight=1)
        self.tab_conversions.grid_columnconfigure(1, weight=1)
        self.tab_conversions.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(self.tab_conversions)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(header, text="🔄 File Conversions", font=("", 18, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Convert between HTML, Markdown, CSV, and Text formats", text_color="gray").pack(side="left", padx=20)
        
        # Left panel - conversion options
        left = ctk.CTkFrame(self.tab_conversions)
        left.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        left.grid_columnconfigure(0, weight=1)
        
        # Conversion type selector
        ctk.CTkLabel(left, text="Conversion Type:", font=("", 13, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        self.conversion_type_var = ctk.StringVar(value="html_to_md")
        
        conversions = [
            ("html_to_md", "HTML → Markdown"),
            ("md_to_html", "Markdown → HTML"),
            ("text_to_md", "Text → Markdown"),
            ("html_tables_csv", "HTML Tables → CSV"),
        ]
        
        for i, (value, label) in enumerate(conversions):
            ctk.CTkRadioButton(
                left, text=label, variable=self.conversion_type_var, value=value,
                command=self._on_conversion_type_change
            ).grid(row=i+1, column=0, sticky="w", padx=25, pady=5)
        
        # Input file
        ctk.CTkLabel(left, text="Input File:", font=("", 13, "bold")).grid(row=10, column=0, sticky="w", padx=15, pady=(20, 5))
        
        input_frame = ctk.CTkFrame(left, fg_color="transparent")
        input_frame.grid(row=11, column=0, sticky="ew", padx=15)
        input_frame.grid_columnconfigure(0, weight=1)
        
        self.conv_input_var = ctk.StringVar()
        ctk.CTkEntry(input_frame, textvariable=self.conv_input_var, width=300).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(input_frame, text="Browse", width=80, command=self._browse_conv_input).grid(row=0, column=1)
        
        # Output file
        ctk.CTkLabel(left, text="Output File:", font=("", 13, "bold")).grid(row=12, column=0, sticky="w", padx=15, pady=(15, 5))
        
        output_frame = ctk.CTkFrame(left, fg_color="transparent")
        output_frame.grid(row=13, column=0, sticky="ew", padx=15)
        output_frame.grid_columnconfigure(0, weight=1)
        
        self.conv_output_var = ctk.StringVar()
        ctk.CTkEntry(output_frame, textvariable=self.conv_output_var, width=300).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkButton(output_frame, text="Browse", width=80, command=self._browse_conv_output).grid(row=0, column=1)
        
        # Options frame (changes based on conversion type)
        ctk.CTkLabel(left, text="Options:", font=("", 13, "bold")).grid(row=14, column=0, sticky="w", padx=15, pady=(20, 5))
        
        self.conv_options_frame = ctk.CTkFrame(left)
        self.conv_options_frame.grid(row=15, column=0, sticky="ew", padx=15, pady=5)
        
        # Default options for HTML → MD
        self.conv_strip_var = ctk.BooleanVar(value=True)
        self.conv_strip_check = ctk.CTkCheckBox(self.conv_options_frame, text="Strip extra whitespace", variable=self.conv_strip_var)
        self.conv_strip_check.pack(anchor="w", padx=10, pady=5)
        
        # Run button
        ctk.CTkButton(
            left, text="▶ Convert", font=("", 14, "bold"),
            command=self._run_conversion, width=200, height=40
        ).grid(row=20, column=0, pady=30)
        
        # Right panel - log output
        right = ctk.CTkFrame(self.tab_conversions)
        right.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(right, text="📋 Output Log", font=("", 14, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        self.conv_log = ctk.CTkTextbox(right, wrap="word")
        self.conv_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Quick actions
        quick_frame = ctk.CTkFrame(right, fg_color="transparent")
        quick_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(quick_frame, text="📂 Open Output Folder", command=self._open_conv_output_folder, width=150).pack(side="left", padx=5)
        ctk.CTkButton(quick_frame, text="🗑 Clear Log", command=lambda: self.conv_log.delete("1.0", "end"), width=100).pack(side="left", padx=5)

    def _create_status_bar(self) -> None:
        self.status_bar = ctk.CTkFrame(self, height=30, corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        self.status_bar.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready", font=ctk.CTkFont(size=11))
        self.status_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")

        self.scheduler_label = ctk.CTkLabel(self.status_bar, text="Scheduler: Stopped", font=ctk.CTkFont(size=11), text_color="gray")
        self.scheduler_label.grid(row=0, column=2, padx=15, pady=5, sticky="e")

    # ========================================================================
    # Header actions
    # ========================================================================
    
    def _change_data_lake_path(self):
        path = filedialog.askdirectory(title="Select Data Lake Directory")
        if path:
            self.data_lake_path = Path(path)
            self.data_lake_btn.configure(text=f"📁 {self.data_lake_path}")
    
    def _open_settings(self):
        SettingsDialog(self, self.data_lake_path)
    
    def _open_data_lake_folder(self):
        os.makedirs(self.data_lake_path, exist_ok=True)
        os.startfile(str(self.data_lake_path))

    # ========================================================================
    # Conversions tab methods
    # ========================================================================
    
    def _on_conversion_type_change(self):
        """Update options based on conversion type."""
        conv_type = self.conversion_type_var.get()
        
        # Clear options frame
        for widget in self.conv_options_frame.winfo_children():
            widget.destroy()
        
        if conv_type == "html_to_md":
            self.conv_strip_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(self.conv_options_frame, text="Strip extra whitespace", variable=self.conv_strip_var).pack(anchor="w", padx=10, pady=5)
        
        elif conv_type == "md_to_html":
            self.conv_template_var = ctk.StringVar(value="minimal")
            ctk.CTkLabel(self.conv_options_frame, text="Template:").pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkOptionMenu(self.conv_options_frame, variable=self.conv_template_var, values=["minimal", "github", "academic"], width=150).pack(anchor="w", padx=10, pady=5)
            
            self.conv_toc_var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(self.conv_options_frame, text="Include Table of Contents", variable=self.conv_toc_var).pack(anchor="w", padx=10, pady=5)
        
        elif conv_type == "text_to_md":
            self.conv_title_var = ctk.StringVar()
            ctk.CTkLabel(self.conv_options_frame, text="Title (optional):").pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkEntry(self.conv_options_frame, textvariable=self.conv_title_var, width=200).pack(anchor="w", padx=10, pady=5)
        
        elif conv_type == "html_tables_csv":
            self.conv_table_idx_var = ctk.StringVar(value="0")
            ctk.CTkLabel(self.conv_options_frame, text="Table index (0 = first):").pack(anchor="w", padx=10, pady=(5, 0))
            ctk.CTkEntry(self.conv_options_frame, textvariable=self.conv_table_idx_var, width=100).pack(anchor="w", padx=10, pady=5)
    
    def _browse_conv_input(self):
        conv_type = self.conversion_type_var.get()
        
        filetypes = [("All files", "*.*")]
        if conv_type in ["html_to_md", "html_tables_csv"]:
            filetypes = [("HTML files", "*.html;*.htm"), ("All files", "*.*")]
        elif conv_type == "md_to_html":
            filetypes = [("Markdown files", "*.md;*.markdown"), ("All files", "*.*")]
        elif conv_type == "text_to_md":
            filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        
        path = filedialog.askopenfilename(title="Select Input File", filetypes=filetypes)
        if path:
            self.conv_input_var.set(path)
            # Auto-set output
            base, _ = os.path.splitext(path)
            if conv_type == "html_to_md":
                self.conv_output_var.set(base + ".md")
            elif conv_type == "md_to_html":
                self.conv_output_var.set(base + ".html")
            elif conv_type == "text_to_md":
                self.conv_output_var.set(base + ".md")
            elif conv_type == "html_tables_csv":
                self.conv_output_var.set(base + "_table.csv")
    
    def _browse_conv_output(self):
        path = filedialog.asksaveasfilename(title="Select Output File")
        if path:
            self.conv_output_var.set(path)
    
    def _conv_log_msg(self, msg: str):
        self.conv_log.insert("end", f"{msg}\n")
        self.conv_log.see("end")
    
    def _run_conversion(self):
        conv_type = self.conversion_type_var.get()
        input_path = self.conv_input_var.get()
        output_path = self.conv_output_var.get()
        
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("Error", "Please select a valid input file")
            return
        
        self._conv_log_msg(f"\n{'='*50}")
        self._conv_log_msg(f"Starting conversion: {conv_type}")
        self._conv_log_msg(f"Input: {input_path}")
        
        try:
            if conv_type == "html_to_md":
                from markdownify import markdownify as md
                html = open(input_path, "r", encoding="utf-8", errors="ignore").read()
                markdown = md(html)
                if getattr(self, 'conv_strip_var', None) and self.conv_strip_var.get():
                    markdown = markdown.strip() + "\n"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown)
                self._conv_log_msg(f"✓ Converted to Markdown: {output_path}")
            
            elif conv_type == "md_to_html":
                import markdown as md_lib
                md_text = open(input_path, "r", encoding="utf-8", errors="ignore").read()
                template = getattr(self, 'conv_template_var', ctk.StringVar(value="minimal")).get()
                extensions = ['fenced_code', 'tables']
                if getattr(self, 'conv_toc_var', None) and self.conv_toc_var.get():
                    extensions.append('toc')
                html_content = md_lib.markdown(md_text, extensions=extensions)
                
                templates = {
                    "minimal": f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{font-family:system-ui;max-width:800px;margin:40px auto;padding:0 20px}}</style></head><body>{html_content}</body></html>",
                    "github": f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial;max-width:980px;margin:0 auto;padding:45px}}code{{background:#f6f8fa;padding:2px 6px}}pre{{background:#f6f8fa;padding:16px}}</style></head><body>{html_content}</body></html>",
                    "academic": f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{{font-family:Georgia,serif;max-width:700px;margin:60px auto;line-height:1.8}}</style></head><body>{html_content}</body></html>"
                }
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(templates.get(template, templates["minimal"]))
                self._conv_log_msg(f"✓ Converted to HTML ({template}): {output_path}")
            
            elif conv_type == "text_to_md":
                txt = open(input_path, "r", encoding="utf-8", errors="ignore").read()
                md_content = ""
                title = getattr(self, 'conv_title_var', ctk.StringVar()).get()
                if title:
                    md_content += f"# {title}\n\n"
                md_content += txt.strip() + "\n"
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(md_content)
                self._conv_log_msg(f"✓ Converted to Markdown: {output_path}")
            
            elif conv_type == "html_tables_csv":
                import pandas as pd
                tables = pd.read_html(input_path)
                idx = int(getattr(self, 'conv_table_idx_var', ctk.StringVar(value="0")).get())
                if idx >= len(tables):
                    raise IndexError(f"Table {idx} not found. File has {len(tables)} tables.")
                df = tables[idx]
                df.to_csv(output_path, index=False)
                self._conv_log_msg(f"✓ Found {len(tables)} tables, exported table {idx} ({len(df)} rows)")
                self._conv_log_msg(f"Output: {output_path}")
            
            self._conv_log_msg("✓ Conversion complete!")
            self.set_status("Conversion complete")
            
        except Exception as e:
            self._conv_log_msg(f"✗ Error: {e}")
            self.set_status(f"Conversion failed: {e}")
    
    def _open_conv_output_folder(self):
        output = self.conv_output_var.get()
        if output:
            folder = os.path.dirname(output)
            if os.path.exists(folder):
                os.startfile(folder)

    # ========================================================================
    # PostgreSQL Tab Methods (same as before)
    # ========================================================================
    
    def _on_pg_connection_change(self, choice):
        pass
    
    def _pg_connect(self):
        db_name = self.pg_connection_var.get()
        if db_name == "Select database..." or not self.connection_resolver:
            return
        
        try:
            self.pg_status.configure(text="● Connecting...", text_color="yellow")
            self.update()
            
            self.current_pg_connection = self.connection_resolver.get_connection(db_name)
            self.pg_status.configure(text=f"● Connected to {db_name}", text_color="green")
            self._pg_refresh_schema()
            self.log_message(f"Connected to {db_name}", "SUCCESS")
        except Exception as e:
            self.pg_status.configure(text="● Connection failed", text_color="red")
            self.log_message(f"Connection failed: {e}", "ERROR")
    
    def _pg_refresh_schema(self):
        if not self.current_pg_connection:
            return
        
        for item in self.schema_tree.get_children():
            self.schema_tree.delete(item)
        
        try:
            cursor = self.current_pg_connection.cursor()
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """)
            schemas = cursor.fetchall()
            
            for (schema_name,) in schemas:
                schema_node = self.schema_tree.insert("", "end", text=f"📁 {schema_name}", values=("schema", ""))
                
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, (schema_name,))
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                        row_count = cursor.fetchone()[0]
                        row_str = f"{row_count:,}"
                    except:
                        row_str = "?"
                    
                    self.schema_tree.insert(schema_node, "end", text=f"📋 {table_name}", values=("table", row_str), tags=(schema_name, table_name))
            
            cursor.close()
        except Exception as e:
            self.log_message(f"Error loading schema: {e}", "ERROR")
    
    def _on_table_select(self, event):
        selection = self.schema_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        item_type = self.schema_tree.item(item)["values"][0] if self.schema_tree.item(item)["values"] else ""
        
        if item_type != "table":
            return
        
        tags = self.schema_tree.item(item)["tags"]
        if len(tags) >= 2:
            schema_name, table_name = tags[0], tags[1]
            self._load_table_details(schema_name, table_name)
    
    def _load_table_details(self, schema_name: str, table_name: str):
        if not self.current_pg_connection:
            return
        
        self.table_name_label.configure(text=f"{schema_name}.{table_name}")
        
        try:
            cursor = self.current_pg_connection.cursor()
            
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (schema_name, table_name))
            columns = cursor.fetchall()
            
            for widget in self.columns_frame.winfo_children():
                widget.destroy()
            
            for col_name, data_type, nullable, default in columns:
                col_frame = ctk.CTkFrame(self.columns_frame, fg_color="transparent")
                col_frame.pack(fill="x", pady=2)
                
                null_indicator = "○" if nullable == "YES" else "●"
                type_color = self._get_type_color(data_type)
                
                ctk.CTkLabel(col_frame, text=f"{null_indicator} {col_name}", width=200, anchor="w").pack(side="left")
                ctk.CTkLabel(col_frame, text=data_type, text_color=type_color, width=150, anchor="w").pack(side="left")
            
            self.table_info_label.configure(text=f"{len(columns)} columns")
            self._load_data_preview(schema_name, table_name, [c[0] for c in columns])
            cursor.close()
            
        except Exception as e:
            self.log_message(f"Error loading table: {e}", "ERROR")
    
    def _get_type_color(self, data_type: str) -> str:
        type_lower = data_type.lower()
        if "int" in type_lower or "serial" in type_lower:
            return "#4fc3f7"
        elif "char" in type_lower or "text" in type_lower:
            return "#81c784"
        elif "timestamp" in type_lower or "date" in type_lower:
            return "#ffb74d"
        elif "bool" in type_lower:
            return "#e57373"
        elif "numeric" in type_lower or "decimal" in type_lower or "float" in type_lower:
            return "#ba68c8"
        return "white"
    
    def _load_data_preview(self, schema_name: str, table_name: str, columns: list):
        self.data_tree.delete(*self.data_tree.get_children())
        self.data_tree["columns"] = columns
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100, minwidth=50)
        
        try:
            cursor = self.current_pg_connection.cursor()
            cursor.execute(f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT 100')
            rows = cursor.fetchall()
            
            for row in rows:
                display_row = [str(v)[:50] if v is not None else "NULL" for v in row]
                self.data_tree.insert("", "end", values=display_row)
            
            cursor.close()
        except Exception as e:
            self.log_message(f"Error loading data: {e}", "ERROR")
    
    def _pg_import_csv(self):
        if not self.current_pg_connection:
            self.log_message("Not connected to database", "ERROR")
            return
        
        filepath = filedialog.askopenfilename(
            title="Select CSV to import",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(self.data_lake_path)
        )
        
        if filepath:
            ImportDialog(self, filepath, self.current_pg_connection, self.log_message)
    
    def _pg_export_csv(self):
        selection = self.schema_tree.selection()
        if not selection or not self.current_pg_connection:
            return
        
        tags = self.schema_tree.item(selection[0])["tags"]
        if len(tags) < 2:
            return
        
        schema_name, table_name = tags[0], tags[1]
        
        filepath = filedialog.asksaveasfilename(
            title="Export to CSV",
            defaultextension=".csv",
            initialfile=f"{table_name}.csv",
            initialdir=str(self.data_lake_path),
            filetypes=[("CSV files", "*.csv")]
        )
        
        if filepath:
            try:
                import csv
                cursor = self.current_pg_connection.cursor()
                cursor.execute(f'SELECT * FROM "{schema_name}"."{table_name}"')
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)
                
                cursor.close()
                self.log_message(f"Exported {len(rows)} rows to {filepath}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Export failed: {e}", "ERROR")

    # ========================================================================
    # Public methods
    # ========================================================================

    def set_connection_resolver(self, resolver):
        self.connection_resolver = resolver
        connections = resolver.list_connections()
        self.pg_connection_dropdown.configure(values=["Select database..."] + connections)

    def set_run_callback(self, callback: Callable) -> None:
        self._on_run_script = callback

    def set_schedule_callback(self, callback: Callable) -> None:
        self._on_schedule_script = callback

    def set_refresh_callback(self, callback: Callable) -> None:
        self._on_refresh_scripts = callback

    def set_scripts(self, scripts: list) -> None:
        self.script_panel.set_scripts(scripts)

    def set_connections(self, connections: list) -> None:
        self.script_panel.set_connections(connections)

    def log_message(self, message: str, level: str = "INFO") -> None:
        self.log_panel.log(message, level)

    def set_status(self, message: str) -> None:
        self.status_label.configure(text=message)

    def set_scheduler_status(self, running: bool) -> None:
        if running:
            self.scheduler_label.configure(text="Scheduler: Running", text_color="green")
        else:
            self.scheduler_label.configure(text="Scheduler: Stopped", text_color="gray")

    def show_run_result(self, result: dict) -> None:
        self.log_panel.show_run_result(result)

    def _handle_run(self, script_name: str, config: dict, target_db: str) -> None:
        if self._on_run_script:
            self.set_status(f"Running {script_name}...")
            self._on_run_script(script_name, config, target_db)

    def _handle_schedule(self, script_name: str, config: dict, target_db: str, interval: int) -> None:
        if self._on_schedule_script:
            self._on_schedule_script(script_name, config, target_db, interval)
            self.log_message(f"Scheduled {script_name} every {interval} minutes", "INFO")

    def _handle_refresh(self) -> None:
        if self._on_refresh_scripts:
            self.set_status("Refreshing scripts...")
            self._on_refresh_scripts()
            self.set_status("Scripts refreshed")


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog."""
    
    def __init__(self, parent, data_lake_path):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("500x400")
        
        ctk.CTkLabel(self, text="⚙️ Settings", font=("", 18, "bold")).pack(pady=20)
        
        # Data Lake path
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(frame, text="Data Lake Path:").pack(anchor="w", padx=10, pady=(10, 0))
        
        path_frame = ctk.CTkFrame(frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=5)
        
        self.path_var = ctk.StringVar(value=str(data_lake_path))
        ctk.CTkEntry(path_frame, textvariable=self.path_var, width=300).pack(side="left", padx=(0, 5))
        ctk.CTkButton(path_frame, text="Browse", width=80, command=self._browse).pack(side="left")
        
        ctk.CTkLabel(frame, text="Raw data files are saved here before loading to PostgreSQL", text_color="gray").pack(anchor="w", padx=10, pady=(0, 10))
        
        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=20)
        
        self.transient(parent)
        self.grab_set()
    
    def _browse(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)


class ImportDialog(ctk.CTkToplevel):
    """Dialog for importing CSV to PostgreSQL."""
    
    def __init__(self, parent, filepath: str, connection, log_callback):
        super().__init__(parent)
        self.filepath = filepath
        self.connection = connection
        self.log_callback = log_callback
        
        self.title("Import CSV to PostgreSQL")
        self.geometry("500x450")
        
        ctk.CTkLabel(self, text=f"📥 Import: {Path(filepath).name}", font=("", 14, "bold")).pack(pady=15)
        
        # Table name
        ctk.CTkLabel(self, text="Table name:").pack(pady=(10, 0))
        self.table_var = ctk.StringVar(value=Path(filepath).stem.lower().replace("-", "_").replace(" ", "_"))
        ctk.CTkEntry(self, textvariable=self.table_var, width=300).pack(pady=5)
        
        # Schema
        ctk.CTkLabel(self, text="Schema:").pack(pady=(10, 0))
        self.schema_var = ctk.StringVar(value="public")
        ctk.CTkEntry(self, textvariable=self.schema_var, width=300).pack(pady=5)
        
        # Options
        self.create_table_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Create table if not exists", variable=self.create_table_var).pack(pady=5)
        
        self.truncate_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self, text="Truncate table before import", variable=self.truncate_var).pack(pady=5)
        
        # Preview
        ctk.CTkLabel(self, text="Preview:").pack(pady=(10, 0))
        self.preview_text = ctk.CTkTextbox(self, height=100, width=450)
        self.preview_text.pack(pady=5)
        self._load_preview()
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Cancel", command=self.destroy, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Import", command=self._do_import, width=100).pack(side="left", padx=10)
        
        self.transient(parent)
        self.grab_set()
    
    def _load_preview(self):
        try:
            import csv
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                lines = []
                for i, row in enumerate(reader):
                    if i >= 6:
                        break
                    lines.append(", ".join(row[:5]) + ("..." if len(row) > 5 else ""))
                self.preview_text.insert("1.0", "\n".join(lines))
        except Exception as e:
            self.preview_text.insert("1.0", f"Error: {e}")
    
    def _do_import(self):
        import csv
        
        table_name = self.table_var.get()
        schema_name = self.schema_var.get()
        
        try:
            cursor = self.connection.cursor()
            
            with open(self.filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                rows = list(reader)
            
            columns = [h.lower().replace(" ", "_").replace("-", "_") for h in headers]
            
            if self.create_table_var.get():
                col_defs = ", ".join([f'"{c}" TEXT' for c in columns])
                cursor.execute(f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" ({col_defs})')
            
            if self.truncate_var.get():
                cursor.execute(f'TRUNCATE TABLE "{schema_name}"."{table_name}"')
            
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join([f'"{c}"' for c in columns])
            insert_sql = f'INSERT INTO "{schema_name}"."{table_name}" ({col_names}) VALUES ({placeholders})'
            
            for row in rows:
                while len(row) < len(columns):
                    row.append(None)
                cursor.execute(insert_sql, row[:len(columns)])
            
            self.connection.commit()
            cursor.close()
            
            self.log_callback(f"Imported {len(rows)} rows to {schema_name}.{table_name}", "SUCCESS")
            self.destroy()
            
        except Exception as e:
            self.log_callback(f"Import failed: {e}", "ERROR")
