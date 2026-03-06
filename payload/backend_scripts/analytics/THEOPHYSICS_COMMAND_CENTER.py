"""
THEOPHYSICS COMMAND CENTER
===========================
A dashboard to run all statistics and analysis scripts with one click.

Author: Claude + David Lowe
Date: January 2026
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import sys
from datetime import datetime
from pathlib import Path

# Get the analytics folder path
ANALYTICS_DIR = Path(__file__).parent
BACKEND_DIR = ANALYTICS_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_ANALYTICS_DIR = Path(r"O:\999_IGNORE\Obsidian Data Analytics\02_Python_Engine")

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPTS = {
    "📊 Paper Metrics (NEW!)": [
        {
            "name": "🎯 50-Metric Paper Analysis",
            "desc": "Calculate all 50 baseline metrics for papers",
            "script": str(ANALYTICS_DIR / "paper_metrics_engine.py"),
            "type": "python"
        },
        {
            "name": "📈 Paper Comparison Engine",
            "desc": "Compare individual papers & aggregates (P1,P3,P5 etc)",
            "script": str(ANALYTICS_DIR / "paper_comparison_engine.py"),
            "type": "python"
        },
        {
            "name": "🌟 COMPREHENSIVE DASHBOARD",
            "desc": "★ MAIN DASHBOARD - 50+ metrics, trends, wisdom/knowledge ★",
            "script": str(ANALYTICS_DIR / "comprehensive_dashboard_generator.py"),
            "type": "python"
        },
    ],
    "📊 Data Analytics": [
        {
            "name": "🚀 RUN COMPLETE PIPELINE (All 11 Steps)",
            "desc": "★ ONE CLICK - Runs all analytics, deep metrics, dashboards ★",
            "script": str(DATA_ANALYTICS_DIR / "RUN_COMPLETE_ANALYTICS.bat"),
            "type": "batch",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "📋 Local Stats (All Notes)",
            "desc": "Generate per-file statistics for every note in vault",
            "script": str(DATA_ANALYTICS_DIR / "generate_stats.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "🌍 Global Vault Analytics",
            "desc": "Aggregate all local stats into vault-wide analytics",
            "script": str(DATA_ANALYTICS_DIR / "generate_global.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "⚛️ Axiom Analytics",
            "desc": "Axiom consistency, coherence, concept density analysis",
            "script": str(DATA_ANALYTICS_DIR / "generate_axiom_analytics.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "✝️ Theology Dashboards",
            "desc": "Trinity analysis, symmetry, Logos, Grace metrics",
            "script": str(DATA_ANALYTICS_DIR / "generate_theology_dashboards.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "📊 Export to Excel (10 Workbooks)",
            "desc": "Generate all 10 Excel workbooks from analytics data",
            "script": str(DATA_ANALYTICS_DIR / "export_to_excel.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "🌐 HTML Dashboards (5 Original)",
            "desc": "Generate master, trinity, fruits, coherence, math dashboards",
            "script": str(DATA_ANALYTICS_DIR / "generate_html_dashboards.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "🔬 Deep Backend Metrics (50/paper)",
            "desc": "Run 50-metric analysis on Logos papers, output 7 JSON files",
            "script": str(DATA_ANALYTICS_DIR / "generate_deep_metrics.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "📈 Deep Plotly Dashboard",
            "desc": "Interactive Plotly charts from deep metrics (CHI, W/K, Fruits)",
            "script": str(DATA_ANALYTICS_DIR / "generate_deep_dashboards.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "📝 Executive Summary",
            "desc": "Generate EXECUTIVE_SUMMARY.md with key findings & rankings",
            "script": str(DATA_ANALYTICS_DIR / "generate_llm_summary.py"),
            "type": "python",
            "cwd": str(DATA_ANALYTICS_DIR)
        },
        {
            "name": "📂 Open Output Folder",
            "desc": "Open the dashboards output directory in Explorer",
            "script": r'start "" "O:\_Theophysics\999_Exclude\Obsidian Data Analytics\03_Dashboards"',
            "type": "powershell"
        },
    ],
    "Corpus Analysis": [
        {
            "name": "📊 Full Corpus Statistics",
            "desc": "Word counts, axioms, citations across all 5.3M words",
            "script": str(ANALYTICS_DIR / "theophysics_stats.py"),
            "type": "python"
        },
        {
            "name": "📄 Logos Paper Analysis",
            "desc": "Publication readiness scores for P00-P13",
            "script": str(ANALYTICS_DIR / "logos_paper_analysis.py"),
            "type": "python"
        },
        {
            "name": "🔬 Experimental Stats Scan",
            "desc": "Find sigma values, p-values, trial counts",
            "script": str(ANALYTICS_DIR / "experimental_stats.py"),
            "type": "python"
        },
        {
            "name": "⚛️ Axiom Coherence Scorer",
            "desc": "Score all axioms for linguistic coherence",
            "script": str(ANALYTICS_DIR / "axiom_scorer.py"),
            "type": "python"
        },
        {
            "name": "🎯 Coherence Calibration Test",
            "desc": "Test coherence scorer with known documents",
            "script": str(ANALYTICS_DIR / "coherence_scorer.py"),
            "type": "python"
        },
    ],
    "Dashboard Generation": [
        {
            "name": "📊 Generate HTML Dashboard",
            "desc": "Create interactive Plotly dashboard",
            "script": str(BACKEND_DIR / "core" / "html_dashboard_generator.py"),
            "type": "python"
        },
        {
            "name": "🌍 Global Analytics Aggregator",
            "desc": "Aggregate all vault analytics",
            "script": str(BACKEND_DIR / "scripts" / "vault_analytics.py"),
            "type": "python"
        },
        {
            "name": "📈 Comprehensive Dashboard",
            "desc": "Generate unified analytics dashboard",
            "script": str(ANALYTICS_DIR / "dashboard_aggregator.py"),
            "type": "python"
        },
    ],
    "Data Files": [
        {
            "name": "📐 Isomorphism Score",
            "desc": "Logical-Narrative correlation analysis",
            "script": r"O:\Theophysics_Data\isomorphism_score.txt",
            "type": "view"
        },
        {
            "name": "🗺️ Statements Map",
            "desc": "All axioms, theorems, claims in JSON",
            "script": r"O:\Theophysics_Data\statements_map.json",
            "type": "view"
        },
        {
            "name": "📦 Evidence Bundles",
            "desc": "PEAR, GCP, Fine-tuning evidence",
            "script": r"O:\Theophysics_Data\evidence_bundles_new.yaml",
            "type": "view"
        },
        {
            "name": "🔗 External Theories List",
            "desc": "All referenced external theories",
            "script": str(ANALYTICS_DIR / "external_theories_list.txt"),
            "type": "view"
        },
        {
            "name": "📊 Axiom Coherence Results",
            "desc": "Full coherence analysis JSON",
            "script": str(ANALYTICS_DIR / "axiom_coherence_results.json"),
            "type": "view"
        },
    ],
    "Existing Scripts": [
        {
            "name": "🧮 Extract Math Formulas",
            "desc": "Pull equations from documents",
            "script": r"O:\extract_math_formulas.py",
            "type": "python"
        },
        {
            "name": "🔍 Filter Evidence",
            "desc": "Filter evidence by criteria",
            "script": r"O:\filter_evidence.py",
            "type": "python"
        },
        {
            "name": "⛏️ Mine Evidence",
            "desc": "Extract evidence from corpus",
            "script": r"O:\mine_evidence.py",
            "type": "python"
        },
        {
            "name": "📖 Biblical Mapping",
            "desc": "Map axioms to scripture",
            "script": r"O:\Theophysics_Data\biblical_mapping.py",
            "type": "python"
        },
        {
            "name": "🌳 Generate Tree HTML",
            "desc": "Visual hierarchy of framework",
            "script": r"O:\generate_tree_html.py",
            "type": "python"
        },
        {
            "name": "📊 Read Math Table",
            "desc": "Parse mathematical tables",
            "script": r"O:\read_math_table_v2.py",
            "type": "python"
        },
    ],
    "🎨 Term Filter (NEW!)": [
        {
            "name": "🔴🔵 Interactive Term Review",
            "desc": "Review undecided terms - mark RED (exclude) or BLUE (include)",
            "script": str(ANALYTICS_DIR / "term_filter_manager.py"),
            "type": "python"
        },
        {
            "name": "📊 Analyze Paper Terms",
            "desc": "See term breakdown: RED vs BLUE vs undecided",
            "script": str(ANALYTICS_DIR / "term_filter_manager.py"),
            "type": "python"
        },
        {
            "name": "📝 View Filter Config",
            "desc": "See your blacklist and whitelist",
            "script": str(ANALYTICS_DIR / "term_filter_config.json"),
            "type": "view"
        },
    ],
    "Quick Stats": [
        {
            "name": "📈 Count All MD Files",
            "desc": "How many markdown files total?",
            "script": "Get-ChildItem -Path 'O:\\Theophysics_Master' -Recurse -Filter *.md | Measure-Object | Select-Object -ExpandProperty Count",
            "type": "powershell"
        },
        {
            "name": "💾 Total Corpus Size",
            "desc": "Size of Theophysics_Master folder",
            "script": "(Get-ChildItem -Path 'O:\\Theophysics_Master' -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB",
            "type": "powershell"
        },
        {
            "name": "📅 Most Recent Files",
            "desc": "Last 10 modified files",
            "script": "Get-ChildItem -Path 'O:\\Theophysics_Master' -Recurse -Filter *.md | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name, LastWriteTime | Format-Table",
            "type": "powershell"
        },
        {
            "name": "🔢 Python Scripts Count",
            "desc": "How many Python scripts?",
            "script": "Get-ChildItem -Path 'O:\\' -Filter *.py | Measure-Object | Select-Object -ExpandProperty Count",
            "type": "powershell"
        },
    ],
    "📁 Custom Dashboard (NEW!)": [
        {
            "name": "🎯 Vault Analytics Dashboard",
            "desc": "Pick folder → Generate comprehensive vault analytics",
            "script": str(ANALYTICS_DIR / "run_vault_dashboard.py"),
            "type": "python_with_folders"
        },
        {
            "name": "📊 Master Dashboard Generator",
            "desc": "Run MASTER_DASHBOARD from Python folder",
            "script": r"O:\Theophysics_Backend\Python_Backend\Python\MASTER_DASHBOARD.py",
            "type": "python"
        },
        {
            "name": "🌟 Custom Metrics Dashboard",
            "desc": "Pick input/output folders → Generate custom dashboard",
            "script": str(ANALYTICS_DIR / "custom_dashboard_runner.py"),
            "type": "python_with_folders"
        },
    ]
}

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class TheophysicsCommandCenter:
    def __init__(self, root):
        self.root = root
        self.root.title("⚛️ THEOPHYSICS COMMAND CENTER")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a2e')
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Build UI
        self.create_header()
        self.create_main_content()
        self.create_status_bar()
        
    def configure_styles(self):
        self.style.configure('TNotebook', background='#1a1a2e')
        self.style.configure('TNotebook.Tab', padding=[20, 10], font=('Consolas', 11, 'bold'))
        self.style.configure('TFrame', background='#1a1a2e')
        self.style.configure('TLabel', background='#1a1a2e', foreground='#e0e0e0')
        self.style.configure('TButton', padding=[10, 5], font=('Consolas', 10))
        
    def create_header(self):
        header = tk.Frame(self.root, bg='#0f3460', height=100)
        header.pack(fill='x', padx=0, pady=0)
        header.pack_propagate(False)
        
        title = tk.Label(
            header, 
            text="⚛️ THEOPHYSICS COMMAND CENTER", 
            font=('Consolas', 26, 'bold'),
            bg='#0f3460',
            fg='#00d9ff'
        )
        title.pack(pady=15)
        
        subtitle = tk.Label(
            header,
            text="Comprehensive Analytics Dashboard | Python Backend v2.0",
            font=('Consolas', 11),
            bg='#0f3460',
            fg='#888888'
        )
        subtitle.pack()
        
    def create_main_content(self):
        # Main container
        main = tk.Frame(self.root, bg='#1a1a2e')
        main.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Script buttons
        left_panel = tk.Frame(main, bg='#16213e', width=450)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Notebook for categories
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        for category, scripts in SCRIPTS.items():
            tab = tk.Frame(notebook, bg='#16213e')
            notebook.add(tab, text=category)
            
            # Create scrollable frame
            canvas = tk.Canvas(tab, bg='#16213e', highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg='#16213e')
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            for script_info in scripts:
                self.create_script_button(scrollable_frame, script_info)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # Right panel - Output
        right_panel = tk.Frame(main, bg='#16213e')
        right_panel.pack(side='right', fill='both', expand=True)
        
        output_label = tk.Label(
            right_panel,
            text="📤 OUTPUT",
            font=('Consolas', 14, 'bold'),
            bg='#16213e',
            fg='#00d9ff'
        )
        output_label.pack(pady=(10, 5))
        
        # Output text area
        self.output_text = scrolledtext.ScrolledText(
            right_panel,
            font=('Consolas', 10),
            bg='#0a0a0f',
            fg='#00ff00',
            insertbackground='#00ff00',
            wrap='word'
        )
        self.output_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Button panel
        button_panel = tk.Frame(right_panel, bg='#16213e')
        button_panel.pack(pady=(0, 10), padx=10, fill='x')
        
        clear_btn = tk.Button(
            button_panel,
            text="🗑️ Clear Output",
            command=self.clear_output,
            bg='#e94560',
            fg='white',
            font=('Consolas', 10, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        clear_btn.pack(side='left', padx=5)
        
        save_btn = tk.Button(
            button_panel,
            text="💾 Save Output",
            command=self.save_output,
            bg='#4ec9b0',
            fg='white',
            font=('Consolas', 10, 'bold'),
            relief='flat',
            cursor='hand2'
        )
        save_btn.pack(side='left', padx=5)
        
    def create_script_button(self, parent, script_info):
        frame = tk.Frame(parent, bg='#16213e')
        frame.pack(fill='x', padx=10, pady=5)
        
        btn = tk.Button(
            frame,
            text=script_info['name'],
            command=lambda s=script_info: self.run_script(s),
            bg='#0f3460',
            fg='white',
            font=('Consolas', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=35,
            anchor='w',
            padx=10
        )
        btn.pack(fill='x')
        
        desc = tk.Label(
            frame,
            text=f"  {script_info['desc']}",
            font=('Consolas', 8),
            bg='#16213e',
            fg='#666666',
            anchor='w'
        )
        desc.pack(fill='x')
        
    def run_script(self, script_info):
        """Run a script based on its type"""
        self.output_text.delete(1.0, tk.END)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] Running: {script_info['name']}\n")
        self.output_text.insert(tk.END, f"Script: {script_info['script']}\n")
        self.output_text.insert(tk.END, "=" * 70 + "\n\n")
        self.output_text.update()
        self.update_status(f"Running: {script_info['name']}")
        
        # If script needs folder selection, show dialogs
        if script_info['type'] == 'python_with_folders':
            input_folder = filedialog.askdirectory(
                title="Select INPUT folder to analyze",
                initialdir="O:\\"
            )
            if not input_folder:
                self.output_text.insert(tk.END, "❌ Cancelled - no input folder selected\n")
                self.update_status("Ready")
                return
            
            output_folder = filedialog.askdirectory(
                title="Select OUTPUT folder for results",
                initialdir="O:\\"
            )
            if not output_folder:
                self.output_text.insert(tk.END, "❌ Cancelled - no output folder selected\n")
                self.update_status("Ready")
                return
            
            # Pass folders to script
            script_info['input_folder'] = input_folder
            script_info['output_folder'] = output_folder
            self.output_text.insert(tk.END, f"📁 Input:  {input_folder}\n")
            self.output_text.insert(tk.END, f"📤 Output: {output_folder}\n")
            self.output_text.insert(tk.END, "=" * 70 + "\n\n")
            self.output_text.update()
        
        # Run in thread to keep UI responsive
        thread = threading.Thread(target=self._execute_script, args=(script_info,))
        thread.daemon = True
        thread.start()
        
    def _execute_script(self, script_info):
        """Execute the script and capture output"""
        try:
            # Determine working directory (use cwd from script_info if set)
            cwd = script_info.get('cwd', None)

            if script_info['type'] == 'python' or script_info['type'] == 'python_with_folders':
                if os.path.exists(script_info['script']):
                    cmd = [sys.executable, script_info['script']]

                    # Add folder arguments if this is a python_with_folders script
                    if script_info['type'] == 'python_with_folders':
                        cmd.append(script_info['input_folder'])
                        cmd.append(script_info['output_folder'])

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=600,
                        cwd=cwd
                    )
                    output = result.stdout + result.stderr
                else:
                    output = f"ERROR: Script not found: {script_info['script']}"

            elif script_info['type'] == 'batch':
                if os.path.exists(script_info['script']):
                    result = subprocess.run(
                        ['cmd', '/c', script_info['script']],
                        capture_output=True,
                        text=True,
                        timeout=900,
                        cwd=cwd
                    )
                    output = result.stdout + result.stderr
                else:
                    output = f"ERROR: Batch file not found: {script_info['script']}"

            elif script_info['type'] == 'powershell':
                result = subprocess.run(
                    ['powershell', '-Command', script_info['script']],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                output = result.stdout + result.stderr

            elif script_info['type'] == 'view':
                if os.path.exists(script_info['script']):
                    with open(script_info['script'], 'r', encoding='utf-8', errors='ignore') as f:
                        output = f.read()[:100000]  # Limit to 100K chars
                else:
                    output = f"ERROR: File not found: {script_info['script']}"
            else:
                output = "Unknown script type"
                
        except subprocess.TimeoutExpired:
            output = "ERROR: Script timed out (5 min limit)"
        except Exception as e:
            output = f"ERROR: {str(e)}"
            
        # Update output in main thread
        self.root.after(0, self._update_output, output)
        
    def _update_output(self, text):
        """Update output text in main thread"""
        self.output_text.insert(tk.END, text)
        self.output_text.insert(tk.END, "\n\n" + "=" * 70 + "\n")
        self.output_text.insert(tk.END, "✅ Complete\n")
        self.output_text.see(tk.END)
        self.update_status("Ready")
        
    def clear_output(self):
        self.output_text.delete(1.0, tk.END)
        
    def save_output(self):
        """Save current output to a file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = ANALYTICS_DIR / f"output_{timestamp}.txt"
        
        content = self.output_text.get(1.0, tk.END)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.update_status(f"Output saved to: {output_file}")
        messagebox.showinfo("Saved", f"Output saved to:\n{output_file}")
        
    def create_status_bar(self):
        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            font=('Consolas', 10),
            bg='#0f3460',
            fg='#888888',
            anchor='w',
            padx=10
        )
        self.status_bar.pack(fill='x', side='bottom')
        
    def update_status(self, text):
        self.status_bar.config(text=text)

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = TheophysicsCommandCenter(root)
    root.mainloop()
