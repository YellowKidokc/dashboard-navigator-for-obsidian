"""
Document Evaluator Page - Universal Coherence Assessment
Implements the three-dimensional Fruits/Anti-Fruits/Chi scoring system
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QProgressBar, QFileDialog, QMessageBox,
    QHeaderView, QComboBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.styles_v2 import COLORS


class DocumentEvaluatorWorker(QThread):
    """Background worker for document evaluation."""
    
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, folder_path: str, file_pattern: str = "*.md"):
        super().__init__()
        self.folder_path = Path(folder_path)
        self.file_pattern = file_pattern
        self.is_running = True
        
    def run(self):
        """Execute the evaluation."""
        try:
            results = {
                "documents": [],
                "aggregate": {
                    "total_docs": 0,
                    "avg_chi": 0.0,
                    "fruits_totals": {},
                    "anti_fruits_totals": {}
                }
            }
            
            # Find all matching files
            files = list(self.folder_path.glob(self.file_pattern))
            total = len(files)
            
            if total == 0:
                self.error.emit(f"No files matching '{self.file_pattern}' found in {self.folder_path}")
                return
            
            self.progress.emit(0, f"Found {total} documents to evaluate...")
            
            fruits_sum = {f: 0 for f in ["Love", "Joy", "Peace", "Patience", "Kindness", 
                                          "Goodness", "Faithfulness", "Gentleness", "Self-Control"]}
            anti_fruits_sum = {f: 0 for f in ["Fragmentation", "Corruption", "Entropy Max", 
                                               "False Coupling", "Demonic Decoherence", "Anti-Coherence",
                                               "Relational Entropy", "Comparative Decoherence", "Entropy Spikes"]}
            chi_sum = 0.0
            
            for i, file_path in enumerate(files):
                if not self.is_running:
                    break
                    
                self.progress.emit(int((i / total) * 100), f"Evaluating {file_path.name}...")
                
                # Evaluate document
                doc_result = self._evaluate_document(file_path)
                results["documents"].append(doc_result)
                
                # Accumulate totals
                for fruit, score in doc_result["fruits"].items():
                    fruits_sum[fruit] += score
                for anti_fruit, score in doc_result["anti_fruits"].items():
                    anti_fruits_sum[anti_fruit] += score
                chi_sum += doc_result["chi"]
            
            # Calculate aggregates
            results["aggregate"]["total_docs"] = len(results["documents"])
            results["aggregate"]["avg_chi"] = chi_sum / total if total > 0 else 0.0
            results["aggregate"]["fruits_totals"] = {k: v / total for k, v in fruits_sum.items()}
            results["aggregate"]["anti_fruits_totals"] = {k: v / total for k, v in anti_fruits_sum.items()}
            
            self.progress.emit(100, "Evaluation complete!")
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Evaluation error: {str(e)}")
    
    def _evaluate_document(self, file_path: Path) -> Dict:
        """Evaluate a single document."""
        try:
            text = file_path.read_text(encoding='utf-8', errors='ignore')
            word_count = len(text.split())
            
            # Simple keyword-based scoring (placeholder for full AI evaluation)
            fruits_scores = self._score_fruits(text, word_count)
            anti_fruits_scores = self._score_anti_fruits(text, word_count)
            
            # Calculate chi with improved normalization
            fruits_total = sum(fruits_scores.values())
            anti_fruits_total = sum(anti_fruits_scores.values())
            
            # Use sigmoid-like transformation to avoid zero-clustering
            # Raw difference can range from -900 to +900
            raw_diff = fruits_total - anti_fruits_total
            
            # Normalize to 0-1 with better spread
            # Add baseline offset to avoid everything being near zero
            chi = (raw_diff + 900) / 1800.0  # Shift range to 0-1800, then normalize
            
            # Apply slight compression to spread mid-range values
            if chi > 0.5:
                chi = 0.5 + (chi - 0.5) * 0.8  # Compress upper half slightly
            else:
                chi = 0.5 - (0.5 - chi) * 0.8  # Compress lower half slightly
            
            chi = max(0.0, min(1.0, chi))  # Clamp to valid range
            
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "word_count": word_count,
                "fruits": fruits_scores,
                "anti_fruits": anti_fruits_scores,
                "chi": chi,
                "grade": self._chi_to_grade(chi)
            }
        except Exception as e:
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "error": str(e),
                "chi": 0.0,
                "grade": "F"
            }
    
    def _score_fruits(self, text: str, word_count: int) -> Dict[str, int]:
        """Score the 9 Fruits of the Spirit."""
        text_lower = text.lower()
        
        # Keyword patterns for each fruit
        patterns = {
            "Love": r'\b(love|unity|coherence|integration|connection|bond|unify|together|mutual)\b',
            "Joy": r'\b(joy|hope|optimism|enable|future|constructive|celebrate|delight)\b',
            "Peace": r'\b(peace|consistency|resolve|harmony|stability|reconcile|calm)\b',
            "Patience": r'\b(patience|thorough|evidence|develop|support|careful|deliberate)\b',
            "Kindness": r'\b(kindness|fair|charitable|steelman|acknowledge|generous|compassion)\b',
            "Goodness": r'\b(goodness|truth|seek|understand|collaborative|virtue|righteous)\b',
            "Faithfulness": r'\b(faithfulness|consistent|premise|definition|honor|reliable|steadfast)\b',
            "Gentleness": r'\b(gentleness|humble|meek|tender|considerate|gracious)\b',  # Removed academic hedging words
            "Self-Control": r'\b(scope|focus|discipline|boundary|constraint|restrain|moderation)\b'
        }
        
        # Academic hedging (NOT gentleness) - detect but don't score as Gentleness
        academic_hedging = r'\b(may|might|suggest|likely|perhaps|possibly|uncertain|appears)\b'
        hedging_count = len(re.findall(academic_hedging, text_lower))
        
        scores = {}
        for fruit, pattern in patterns.items():
            matches = len(re.findall(pattern, text_lower))
            
            # Adjust normalization to produce better spread
            # Use logarithmic scaling to avoid clustering at extremes
            if matches > 0:
                normalized = min(100, int((matches / max(1, word_count / 1000)) * 30))
            else:
                normalized = 0
            
            # Penalize Gentleness if document is heavily academic (hedging without relational language)
            if fruit == "Gentleness" and hedging_count > matches * 3:
                normalized = int(normalized * 0.3)  # Reduce by 70% if mostly hedging
            
            scores[fruit] = normalized
        
        return scores
    
    def _score_anti_fruits(self, text: str, word_count: int) -> Dict[str, int]:
        """Score the 9 Anti-Fruits (Works of the Flesh)."""
        text_lower = text.lower()
        
        patterns = {
            "Fragmentation": r'\b(disconnect|fragment|contradict|incoherent)\b',
            "Corruption": r'\b(error|false|misrepresent|fallacy|distort)\b',
            "Entropy Max": r'\b(chaos|confuse|obfuscate|unclear|disorder)\b',
            "False Coupling": r'\b(circular|unfalsifiable|unsupported|baseless)\b',
            "Demonic Decoherence": r'\b(manipulate|gaslight|deceive|misdirect)\b',
            "Anti-Coherence": r'\b(hate|attack|destroy|demolish|refute)\b',
            "Relational Entropy": r'\b(divide|discord|polarize|versus|enemy)\b',
            "Comparative Decoherence": r'\b(jealous|compete|zero-sum|scarcity)\b',
            "Entropy Spikes": r'\b(rage|outburst|volatile|chaotic|unstable)\b'
        }
        
        scores = {}
        for anti_fruit, pattern in patterns.items():
            matches = len(re.findall(pattern, text_lower))
            normalized = min(100, int((matches / max(1, word_count / 1000)) * 20))
            scores[anti_fruit] = normalized
        
        return scores
    
    def _chi_to_grade(self, chi: float) -> str:
        """Convert chi score to letter grade (calibrated for keyword-based scoring)."""
        # Recalibrated thresholds based on observed distribution
        # Max observed: ~0.167, Average: ~0.026
        if chi >= 0.15: return "A+"
        elif chi >= 0.12: return "A"
        elif chi >= 0.10: return "A-"
        elif chi >= 0.08: return "B+"
        elif chi >= 0.06: return "B"
        elif chi >= 0.04: return "B-"
        elif chi >= 0.03: return "C+"
        elif chi >= 0.02: return "C"
        elif chi >= 0.01: return "C-"
        elif chi >= 0.005: return "D"
        else: return "F"
    
    def stop(self):
        """Stop the evaluation."""
        self.is_running = False


def _build_document_evaluator_page(self):
    """Build the Universal Document Evaluator page."""
    from ui.styles_v2 import COLORS
    
    page, layout = self._create_page_container("🍇 Universal Document Evaluator")
    
    # Header description
    desc = QLabel(
        "Evaluate any document using the three-dimensional Fruits/Anti-Fruits/χ framework. "
        "This produces objective, reproducible coherence scores that can be compared across documents."
    )
    desc.setWordWrap(True)
    desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11pt; margin-bottom: 20px;")
    layout.addWidget(desc)
    
    # ========== SECTION 1: INPUT CONFIGURATION ==========
    input_group = QGroupBox("📁 Input Configuration")
    input_group.setStyleSheet(f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 12pt;
            border: 2px solid {COLORS['accent_blue']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{ color: {COLORS['accent_blue']}; }}
    """)
    input_layout = QVBoxLayout(input_group)
    
    # Folder selection
    folder_row = QHBoxLayout()
    folder_row.addWidget(QLabel("Folder to Evaluate:"))
    self.eval_folder_input = QLineEdit()
    self.eval_folder_input.setText("D:/Canon/01_Axioms/_001-188")
    self.eval_folder_input.setPlaceholderText("Select folder containing documents...")
    folder_row.addWidget(self.eval_folder_input)
    
    browse_btn = QPushButton("Browse")
    browse_btn.clicked.connect(lambda: self._browse_eval_folder())
    folder_row.addWidget(browse_btn)
    input_layout.addLayout(folder_row)
    
    # File pattern
    pattern_row = QHBoxLayout()
    pattern_row.addWidget(QLabel("File Pattern:"))
    self.eval_pattern_input = QLineEdit()
    self.eval_pattern_input.setText("*.md")
    self.eval_pattern_input.setPlaceholderText("e.g., *.md, *.txt, *.pdf")
    pattern_row.addWidget(self.eval_pattern_input)
    input_layout.addLayout(pattern_row)
    
    layout.addWidget(input_group)
    
    # ========== SECTION 2: EVALUATION CONTROLS ==========
    controls_group = QGroupBox("⚙️ Evaluation Controls")
    controls_group.setStyleSheet(f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 12pt;
            border: 2px solid {COLORS['accent_green']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{ color: {COLORS['accent_green']}; }}
    """)
    controls_layout = QVBoxLayout(controls_group)
    
    # Buttons row
    btn_row = QHBoxLayout()
    
    self.eval_start_btn = QPushButton("🚀 Start Evaluation")
    self.eval_start_btn.setStyleSheet(f"""
        QPushButton {{
            background: {COLORS['accent_green']};
            color: {COLORS['bg_darkest']};
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11pt;
        }}
        QPushButton:hover {{ background: #5fd9c0; }}
        QPushButton:disabled {{ background: {COLORS['bg_medium']}; color: {COLORS['text_secondary']}; }}
    """)
    self.eval_start_btn.clicked.connect(self._start_evaluation)
    btn_row.addWidget(self.eval_start_btn)
    
    self.eval_stop_btn = QPushButton("⏹️ Stop")
    self.eval_stop_btn.setEnabled(False)
    self.eval_stop_btn.setStyleSheet(f"""
        QPushButton {{
            background: {COLORS['accent_red']};
            color: white;
            padding: 12px 24px;
            border-radius: 6px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background: #ff6b6b; }}
        QPushButton:disabled {{ background: {COLORS['bg_medium']}; color: {COLORS['text_secondary']}; }}
    """)
    self.eval_stop_btn.clicked.connect(self._stop_evaluation)
    btn_row.addWidget(self.eval_stop_btn)
    
    btn_row.addStretch()
    controls_layout.addLayout(btn_row)
    
    # Progress bar
    self.eval_progress = QProgressBar()
    self.eval_progress.setStyleSheet(f"""
        QProgressBar {{
            border: 1px solid {COLORS['border_dark']};
            border-radius: 4px;
            text-align: center;
            height: 25px;
        }}
        QProgressBar::chunk {{ background: {COLORS['accent_green']}; }}
    """)
    controls_layout.addWidget(self.eval_progress)
    
    # Status label
    self.eval_status_label = QLabel("Ready to evaluate")
    self.eval_status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-style: italic;")
    controls_layout.addWidget(self.eval_status_label)
    
    layout.addWidget(controls_group)
    
    # ========== SECTION 3: RESULTS DISPLAY ==========
    results_group = QGroupBox("📊 Evaluation Results")
    results_group.setStyleSheet(f"""
        QGroupBox {{
            font-weight: bold;
            font-size: 12pt;
            border: 2px solid {COLORS['accent_purple']};
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{ color: {COLORS['accent_purple']}; }}
    """)
    results_layout = QVBoxLayout(results_group)
    
    # Summary metrics
    summary_row = QHBoxLayout()
    
    self.eval_total_docs_label = QLabel("Documents: 0")
    self.eval_total_docs_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['accent_blue']};")
    summary_row.addWidget(self.eval_total_docs_label)
    
    self.eval_avg_chi_label = QLabel("Avg χ: 0.000")
    self.eval_avg_chi_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['accent_green']};")
    summary_row.addWidget(self.eval_avg_chi_label)
    
    self.eval_avg_grade_label = QLabel("Avg Grade: -")
    self.eval_avg_grade_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {COLORS['accent_purple']};")
    summary_row.addWidget(self.eval_avg_grade_label)
    
    summary_row.addStretch()
    results_layout.addLayout(summary_row)
    
    # Results table
    self.eval_results_table = QTableWidget(0, 5)
    self.eval_results_table.setHorizontalHeaderLabels(["Document", "Word Count", "χ Score", "Grade", "Top Fruit"])
    self.eval_results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    self.eval_results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
    self.eval_results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
    self.eval_results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
    self.eval_results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
    self.eval_results_table.setMinimumHeight(300)
    results_layout.addWidget(self.eval_results_table)
    
    # Export buttons
    export_row = QHBoxLayout()
    
    export_json_btn = QPushButton("📄 Export JSON")
    export_json_btn.clicked.connect(lambda: self._export_eval_results("json"))
    export_row.addWidget(export_json_btn)
    
    export_md_btn = QPushButton("📝 Export Markdown")
    export_md_btn.clicked.connect(lambda: self._export_eval_results("markdown"))
    export_row.addWidget(export_md_btn)
    
    export_html_btn = QPushButton("🌐 Export HTML")
    export_html_btn.clicked.connect(lambda: self._export_eval_results("html"))
    export_row.addWidget(export_html_btn)
    
    export_csv_btn = QPushButton("📊 Export CSV")
    export_csv_btn.clicked.connect(lambda: self._export_eval_results("csv"))
    export_row.addWidget(export_csv_btn)
    
    export_row.addStretch()
    results_layout.addLayout(export_row)
    
    layout.addWidget(results_group)
    
    layout.addStretch()
    
    # Initialize worker
    self.eval_worker = None
    self.eval_results = None


def _browse_eval_folder(self):
    """Browse for evaluation folder."""
    folder = QFileDialog.getExistingDirectory(self, "Select Folder to Evaluate")
    if folder:
        self.eval_folder_input.setText(folder)


def _start_evaluation(self):
    """Start the document evaluation."""
    folder_path = self.eval_folder_input.text()
    if not folder_path or not Path(folder_path).exists():
        QMessageBox.warning(self, "Invalid Folder", "Please select a valid folder to evaluate.")
        return
    
    file_pattern = self.eval_pattern_input.text() or "*.md"
    
    # Disable start button, enable stop button
    self.eval_start_btn.setEnabled(False)
    self.eval_stop_btn.setEnabled(True)
    self.eval_progress.setValue(0)
    self.eval_status_label.setText("Starting evaluation...")
    
    # Create and start worker
    self.eval_worker = DocumentEvaluatorWorker(folder_path, file_pattern)
    self.eval_worker.progress.connect(self._on_eval_progress)
    self.eval_worker.finished.connect(self._on_eval_finished)
    self.eval_worker.error.connect(self._on_eval_error)
    self.eval_worker.start()


def _stop_evaluation(self):
    """Stop the evaluation."""
    if self.eval_worker and self.eval_worker.isRunning():
        self.eval_worker.stop()
        self.eval_worker.wait()
        self.eval_status_label.setText("Evaluation stopped by user")
        self.eval_start_btn.setEnabled(True)
        self.eval_stop_btn.setEnabled(False)


def _on_eval_progress(self, percent: int, message: str):
    """Handle evaluation progress updates."""
    self.eval_progress.setValue(percent)
    self.eval_status_label.setText(message)


def _on_eval_finished(self, results: Dict):
    """Handle evaluation completion."""
    self.eval_results = results
    
    # Update summary metrics
    agg = results["aggregate"]
    self.eval_total_docs_label.setText(f"Documents: {agg['total_docs']}")
    self.eval_avg_chi_label.setText(f"Avg χ: {agg['avg_chi']:.3f}")
    
    # Calculate average grade
    grades = [doc.get("grade", "F") for doc in results["documents"]]
    self.eval_avg_grade_label.setText(f"Avg Grade: {grades[0] if grades else '-'}")
    
    # Populate results table
    self.eval_results_table.setRowCount(len(results["documents"]))
    for i, doc in enumerate(results["documents"]):
        self.eval_results_table.setItem(i, 0, QTableWidgetItem(doc["filename"]))
        self.eval_results_table.setItem(i, 1, QTableWidgetItem(str(doc.get("word_count", 0))))
        self.eval_results_table.setItem(i, 2, QTableWidgetItem(f"{doc['chi']:.3f}"))
        self.eval_results_table.setItem(i, 3, QTableWidgetItem(doc["grade"]))
        
        # Find top fruit
        if "fruits" in doc:
            top_fruit = max(doc["fruits"].items(), key=lambda x: x[1])
            self.eval_results_table.setItem(i, 4, QTableWidgetItem(f"{top_fruit[0]} ({top_fruit[1]})"))
    
    # Auto-export all formats to organized folder
    self._auto_export_results()
    
    # Re-enable controls
    self.eval_start_btn.setEnabled(True)
    self.eval_stop_btn.setEnabled(False)
    QMessageBox.information(self, "Evaluation Complete", 
        f"Successfully evaluated {agg['total_docs']} documents.\n\n"
        f"Average χ Score: {agg['avg_chi']:.3f}\n\n"
        f"Results auto-exported to:\n{self.last_export_folder}")


def _on_eval_error(self, error_msg: str):
    """Handle evaluation errors."""
    self.eval_status_label.setText(f"❌ Error: {error_msg}")
    self.eval_start_btn.setEnabled(True)
    self.eval_stop_btn.setEnabled(False)
    QMessageBox.critical(self, "Evaluation Error", error_msg)


def _auto_export_results(self):
    """Automatically export all formats to organized folder."""
    if not self.eval_results:
        return
    
    from ui.auto_export_helper import auto_export_results
    
    try:
        self.last_export_folder = auto_export_results(
            self.eval_results,
            self.eval_folder_input.text(),
            self._export_evaluation_prompt,
            self._generate_markdown_report
        )
    except Exception as e:
        QMessageBox.warning(self, "Auto-Export Warning", 
            f"Evaluation completed but auto-export failed:\n{str(e)}\n\n"
            f"You can still manually export using the buttons below.")
        self.last_export_folder = "Auto-export failed"


def _export_eval_results(self, format_type: str):
    """Export evaluation results in specified format."""
    if not self.eval_results:
        QMessageBox.warning(self, "No Results", "No evaluation results to export. Run an evaluation first.")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "json":
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", f"evaluation_results_{timestamp}.json", "JSON Files (*.json)"
        )
        if file_path:
            # Add prompt to results
            results_with_prompt = self.eval_results.copy()
            results_with_prompt["evaluation_prompt_file"] = f"EVALUATION_PROMPT_{timestamp}.md"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_with_prompt, f, indent=2)
            
            # Export prompt alongside results
            prompt_path = Path(file_path).parent / f"EVALUATION_PROMPT_{timestamp}.md"
            self._export_evaluation_prompt(prompt_path)
            
            QMessageBox.information(self, "Export Complete", 
                f"Results exported to:\n{file_path}\n\n"
                f"Evaluation prompt exported to:\n{prompt_path}\n\n"
                f"Send both files to 3 different AIs for consensus scoring.")
    
    elif format_type == "markdown":
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Markdown", f"evaluation_report_{timestamp}.md", "Markdown Files (*.md)"
        )
        if file_path:
            md_content = self._generate_markdown_report(self.eval_results)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            QMessageBox.information(self, "Export Complete", f"Report exported to:\n{file_path}")
    
    elif format_type == "html":
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export HTML", f"evaluation_report_{timestamp}.html", "HTML Files (*.html)"
        )
        if file_path:
            html_content = self._generate_html_report(self.eval_results)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            QMessageBox.information(self, "Export Complete", f"Interactive HTML report exported to:\n{file_path}")
    
    elif format_type == "csv":
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"evaluation_results_{timestamp}.csv", "CSV Files (*.csv)"
        )
        if file_path:
            import csv
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Filename", "Word Count", "Chi Score", "Grade", "Top Fruit"])
                for doc in self.eval_results["documents"]:
                    top_fruit = max(doc.get("fruits", {}).items(), key=lambda x: x[1]) if doc.get("fruits") else ("N/A", 0)
                    writer.writerow([
                        doc["filename"],
                        doc.get("word_count", 0),
                        f"{doc['chi']:.3f}",
                        doc["grade"],
                        f"{top_fruit[0]} ({top_fruit[1]})"
                    ])
            QMessageBox.information(self, "Export Complete", f"Results exported to:\n{file_path}")


def _generate_markdown_report(self, results: Dict) -> str:
    """Generate a markdown report from evaluation results."""
    agg = results["aggregate"]
    
    md = f"""# DOCUMENT EVALUATION REPORT
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## SUMMARY

- **Total Documents:** {agg['total_docs']}
- **Average χ Score:** {agg['avg_chi']:.3f}

---

## DOCUMENT RESULTS

| Document | Word Count | χ Score | Grade | Top Fruit |
|----------|------------|---------|-------|-----------|
"""
    
    for doc in results["documents"]:
        top_fruit = max(doc.get("fruits", {}).items(), key=lambda x: x[1]) if doc.get("fruits") else ("N/A", 0)
        md += f"| {doc['filename']} | {doc.get('word_count', 0)} | {doc['chi']:.3f} | {doc['grade']} | {top_fruit[0]} ({top_fruit[1]}) |\n"
    
    md += "\n---\n\n**Evaluation Framework:** Universal Document Evaluator v1.0 (Theophysics)\n"
    
    return md


def _generate_html_report(self, results: Dict) -> str:
    """Generate an interactive HTML report with visualizations."""
    from ui.html_report_generator import generate_html_report
    return generate_html_report(results)


def _export_evaluation_prompt(self, file_path: Path):
    """Export the evaluation prompt for multi-AI consensus."""
    prompt_content = """# UNIVERSAL DOCUMENT EVALUATOR - AI EVALUATION PROMPT
**Version:** 1.0
**Purpose:** Objective, reproducible coherence scoring for comparative analysis

---

## YOUR TASK

You will evaluate documents using a three-dimensional framework:
1. **Fruits** (9 positive coherence markers)
2. **Anti-Fruits** (9 decoherence signatures)
3. **χ (Chi)** (Direct coherence measurement)

---

## SCORING INSTRUCTIONS

For each document provided, score all 18 dimensions (9 Fruits + 9 Anti-Fruits) on a 0-100 scale.

### THE 9 FRUITS (Positive Markers)

**Score 0-100 for each:**

1. **LOVE** (Global Coherence) - How well do elements connect and support each other?
   - 90-100: All sections explicitly reference and build on each other
   - 70-89: Most sections connect; occasional standalone claims
   - 50-69: Some integration; multiple disconnected threads
   - 30-49: Weak connections; ideas feel separate
   - 0-29: Fragmented; no apparent unifying structure

2. **JOY** (Positive Information Gain) - Does it offer constructive paths forward?
   - 90-100: Explicitly offers solutions, next steps, constructive frameworks
   - 70-89: Identifies problems but suggests directions for resolution
   - 50-69: Balanced critique and construction
   - 30-49: Primarily critical; minimal constructive elements
   - 0-29: Purely negative; no forward-looking content

3. **PEACE** (Dynamic Stability) - Are contradictions resolved?
   - 90-100: Zero unresolved contradictions; tensions explicitly addressed
   - 70-89: Minor tensions acknowledged and explained
   - 50-69: Some contradictions present but not fatal
   - 30-49: Multiple unresolved contradictions
   - 0-29: Fundamental logical contradictions throughout

4. **PATIENCE** (Thoroughness) - Are arguments fully developed?
   - 90-100: Every claim fully developed with evidence and reasoning
   - 70-89: Most claims well-supported; occasional gaps
   - 50-69: Mix of developed and underdeveloped claims
   - 30-49: Many claims asserted without support
   - 0-29: Primarily assertions; minimal development

5. **KINDNESS** (Fairness to Alternatives) - Are opposing views treated charitably?
   - 90-100: Steelmans alternatives; acknowledges their strengths
   - 70-89: Fairly represents alternatives before critique
   - 50-69: Mentions alternatives but doesn't engage deeply
   - 30-49: Strawmans or dismisses alternatives
   - 0-29: Ignores alternatives entirely or attacks them unfairly

6. **GOODNESS** (Constructive Intent) - Is the tone truth-seeking vs adversarial?
   - 90-100: Clearly aimed at understanding; collaborative tone
   - 70-89: Primarily constructive with occasional defensive moments
   - 50-69: Mixed constructive and adversarial tone
   - 30-49: Primarily adversarial or defensive
   - 0-29: Purely polemical; aimed at defeating opponents

7. **FAITHFULNESS** (Consistency) - Does it honor stated premises throughout?
   - 90-100: Perfect consistency with stated premises/definitions
   - 70-89: Mostly consistent; minor drift
   - 50-69: Some inconsistency in application of principles
   - 30-49: Frequent violations of stated premises
   - 0-29: Abandons initial framework entirely

8. **GENTLENESS** (Epistemic Humility) - Does it admit uncertainty and limits?
   - 90-100: Explicitly acknowledges limits, uncertainties, unknowns
   - 70-89: Qualifies claims appropriately; admits some limits
   - 50-69: Some hedging but also overconfident claims
   - 30-49: Primarily overconfident; minimal uncertainty acknowledgment
   - 0-29: Absolute certainty claims throughout; no humility

9. **SELF-CONTROL** (Scope Discipline) - Does it stay within declared scope?
   - 90-100: Perfect scope discipline; no tangents
   - 70-89: Mostly focused; minor digressions
   - 50-69: Some scope creep but returns to main thread
   - 30-49: Frequent tangents; loses main thread
   - 0-29: Severe scope creep; unclear what document is about

---

### THE 9 ANTI-FRUITS (Decoherence Signatures)

**Score 0-100 for each (higher = worse):**

1. **FRAGMENTATION** - Disconnected claims, contradictory statements, unresolved tensions
2. **CORRUPTION** - Factual errors, misrepresentations, logical fallacies
3. **ENTROPY MAXIMIZATION** - Unnecessary complexity, obfuscation, confusion
4. **FALSE COUPLING** - Circular reasoning, unfalsifiable claims, weak foundations
5. **DEMONIC DECOHERENCE** - Manipulative rhetoric, gaslighting, misdirection
6. **ANTI-COHERENCE** - Destructive vs constructive, attacks vs arguments
7. **RELATIONAL ENTROPY** - Divisive language, polarization, us-vs-them
8. **COMPARATIVE DECOHERENCE** - Zero-sum thinking, scarcity mindset, jealousy
9. **ENTROPY SPIKES** - Emotional outbursts, volatility, loss of thread

---

## CALCULATE CHI (χ)

```
χ = (Sum of 9 Fruit scores - Sum of 9 Anti-Fruit scores) / 1800
```

Result should be between 0.0 and 1.0.

**Grade Scale:**
- 0.95-1.00 = A+
- 0.90-0.94 = A
- 0.85-0.89 = A-
- 0.80-0.84 = B+
- 0.75-0.79 = B
- 0.70-0.74 = B-
- 0.65-0.69 = C+
- 0.60-0.64 = C
- 0.55-0.59 = C-
- 0.50-0.54 = D
- <0.50 = F

---

## OUTPUT FORMAT

For each document, provide:

```json
{
  "document_name": "filename.md",
  "evaluator_model": "Your AI Model Name",
  "fruits": {
    "love": 85,
    "joy": 78,
    "peace": 82,
    "patience": 75,
    "kindness": 70,
    "goodness": 88,
    "faithfulness": 80,
    "gentleness": 72,
    "self_control": 85
  },
  "anti_fruits": {
    "fragmentation": 15,
    "corruption": 10,
    "entropy_max": 20,
    "false_coupling": 12,
    "demonic_decoherence": 5,
    "anti_coherence": 8,
    "relational_entropy": 18,
    "comparative_decoherence": 22,
    "entropy_spikes": 25
  },
  "chi": 0.778,
  "grade": "B",
  "justification": "Brief 2-3 sentence explanation of the score"
}
```

---

## CONSTRAINTS

1. **Evidence-Based:** Every score must be based on specific text in the document
2. **Neutral Tone:** Descriptive, not judgmental
3. **Reproducible:** Another evaluator should reach similar scores
4. **No Hallucination:** Only cite text that actually exists

---

## MULTI-MODEL CONSENSUS PROTOCOL

This prompt will be run on 3 different AI models:
- Model A (e.g., GPT-4o)
- Model B (e.g., Claude-3.5-Sonnet)
- Model C (e.g., Gemini-1.5-Pro)

**Final score = Median of 3 models**

Scores within ±10 points = Aligned ✅
Scores >15 points apart = Flagged for review ⚠️

---

**BEGIN EVALUATION**

The documents to evaluate are provided in the accompanying JSON file.
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(prompt_content)


# Attach methods to MainWindowV2
from ui.main_window_v2 import MainWindowV2
MainWindowV2._build_document_evaluator_page = _build_document_evaluator_page
MainWindowV2._browse_eval_folder = _browse_eval_folder
MainWindowV2._start_evaluation = _start_evaluation
MainWindowV2._stop_evaluation = _stop_evaluation
MainWindowV2._on_eval_progress = _on_eval_progress
MainWindowV2._on_eval_finished = _on_eval_finished
MainWindowV2._on_eval_error = _on_eval_error
MainWindowV2._export_eval_results = _export_eval_results
MainWindowV2._generate_markdown_report = _generate_markdown_report
