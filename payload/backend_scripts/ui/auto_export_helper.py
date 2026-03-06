"""
Auto-export helper for Document Evaluator
Automatically exports all formats to organized folder
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict


def auto_export_results(eval_results: Dict, scanned_folder: str, export_prompt_func, generate_markdown_func) -> str:
    """
    Automatically export all formats to organized folder.
    
    Returns: Path to the export folder
    """
    from ui.html_report_generator import generate_html_report
    
    # Create output folder in the scanned directory
    scanned_path = Path(scanned_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = scanned_path / f"Universal_Document_Evaluator_{timestamp}"
    output_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Export JSON (with prompt reference)
        json_path = output_folder / f"evaluation_results_{timestamp}.json"
        results_with_prompt = eval_results.copy()
        results_with_prompt["evaluation_prompt_file"] = f"EVALUATION_PROMPT_{timestamp}.md"
        results_with_prompt["export_folder"] = str(output_folder)
        results_with_prompt["export_timestamp"] = timestamp
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results_with_prompt, f, indent=2)
        
        # Export evaluation prompt
        prompt_path = output_folder / f"EVALUATION_PROMPT_{timestamp}.md"
        export_prompt_func(prompt_path)
        
        # 2. Export Markdown
        md_path = output_folder / f"evaluation_report_{timestamp}.md"
        md_content = generate_markdown_func(eval_results)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 3. Export HTML
        html_path = output_folder / f"evaluation_report_{timestamp}.html"
        html_content = generate_html_report(eval_results)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 4. Export CSV
        csv_path = output_folder / f"evaluation_results_{timestamp}.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Filename", "Word Count", "Chi Score", "Grade", "Top Fruit", "Top Fruit Score"])
            for doc in eval_results["documents"]:
                top_fruit = max(doc.get("fruits", {}).items(), key=lambda x: x[1]) if doc.get("fruits") else ("N/A", 0)
                writer.writerow([
                    doc["filename"],
                    doc.get("word_count", 0),
                    f"{doc['chi']:.3f}",
                    doc["grade"],
                    top_fruit[0],
                    top_fruit[1]
                ])
        
        # 5. Create README
        readme_path = output_folder / "README.txt"
        agg = eval_results["aggregate"]
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(f"""Universal Document Evaluator Results
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Scanned Folder: {scanned_folder}

===========================================
SUMMARY
===========================================
Total Documents: {agg['total_docs']}
Average Chi Score: {agg['avg_chi']:.3f}

===========================================
FILES IN THIS FOLDER
===========================================

1. evaluation_results_{timestamp}.json
   - Complete evaluation data in JSON format
   - Use this for statistical analysis or importing to other tools
   - Contains all Fruits/Anti-Fruits scores per document

2. EVALUATION_PROMPT_{timestamp}.md
   - The evaluation prompt used for this analysis
   - Send this + the JSON to 3 different AIs for consensus scoring
   - Models: GPT-4o, Claude-3.5-Sonnet, Gemini-1.5-Pro

3. evaluation_report_{timestamp}.md
   - Human-readable Markdown report
   - Summary statistics and document rankings
   - Easy to read in any text editor

4. evaluation_report_{timestamp}.html
   - Interactive HTML report with visualizations
   - Open in any web browser
   - Includes radar charts, histograms, and grade distributions
   - Perfect for presentations and sharing

5. evaluation_results_{timestamp}.csv
   - Spreadsheet-compatible format
   - Import to Excel, Google Sheets, or statistical software
   - One row per document with key metrics

===========================================
MULTI-AI CONSENSUS WORKFLOW
===========================================

To get consensus scores from 3 different AIs:

1. Open EVALUATION_PROMPT_{timestamp}.md
2. Copy the prompt text
3. Send to GPT-4o with evaluation_results_{timestamp}.json
4. Send to Claude-3.5-Sonnet with the same files
5. Send to Gemini-1.5-Pro with the same files
6. Compare the three outputs
7. Take the MEDIAN score for each document

Scores within ±10 points = Aligned ✅
Scores >15 points apart = Flagged for review ⚠️

===========================================
FRAMEWORK INFORMATION
===========================================

Evaluation Framework: Universal Document Evaluator v1.0 (Theophysics)
Three-Dimensional Assessment:
  - Fruits (9 positive coherence markers)
  - Anti-Fruits (9 decoherence signatures)
  - χ (Chi) - Direct coherence measurement (0-1 scale)

SCORING CALIBRATION NOTES:
- This is a keyword-based preliminary scorer
- Grade thresholds calibrated for observed distribution:
  * A+: χ ≥ 0.15 (exceptional)
  * A:  χ ≥ 0.12 (excellent)
  * B:  χ ≥ 0.06 (good)
  * C:  χ ≥ 0.02 (adequate)
  * D:  χ ≥ 0.005 (weak)
  * F:  χ < 0.005 (poor)

- Gentleness scoring adjusted to separate:
  * Academic hedging ("may", "suggest", "likely")
  * From actual relational gentleness ("humble", "meek", "tender")

- For full AI-based evaluation with higher precision,
  use the EVALUATION_PROMPT with GPT-4o/Claude/Gemini

For more information, see the evaluation prompt file.

===========================================
""")
        
        return str(output_folder)
        
    except Exception as e:
        raise Exception(f"Auto-export failed: {str(e)}")


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
