"""
Create a SMART Excel workbook that interprets the unified_scorer output
The Excel AI can then read/extend these interpretations
"""

import pandas as pd
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference, LineChart
from openpyxl.utils.dataframe import dataframe_to_rows

def create_smart_excel():
    """Create Excel with raw data + interpretation formulas"""
    
    outputs_dir = Path(r"O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\scripts\from_Note\outputs")
    
    # Load all JSON scores
    json_files = list(outputs_dir.glob("*_scores.json"))
    all_scores = {}
    
    for json_file in json_files:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            title = json_file.stem.replace('_scores', '')
            all_scores[title] = data
    
    # Create workbook
    wb = Workbook()
    wb.remove(wb.active)
    
    # ========================================================================
    # SHEET 1: RAW SCORES (The source data)
    # ========================================================================
    ws_raw = wb.create_sheet("Raw Scores")
    
    # Headers
    headers = ['Paper', 'Chi', 'Kappa', 'Rho', 'Pi', 'A', 'Lambda', 
               'Metrics', 'Evidence', 'Vetoes', 'Warnings']
    
    for col, header in enumerate(headers, 1):
        cell = ws_raw.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    
    # Data
    row_idx = 2
    for title, data in sorted(all_scores.items()):
        ws_raw.cell(row=row_idx, column=1, value=title)
        ws_raw.cell(row=row_idx, column=2, value=data['chi'])
        ws_raw.cell(row=row_idx, column=3, value=data['kappa'])
        ws_raw.cell(row=row_idx, column=4, value=data['rho'])
        ws_raw.cell(row=row_idx, column=5, value=data['triad']['pi'])
        ws_raw.cell(row=row_idx, column=6, value=data['triad']['a'])
        ws_raw.cell(row=row_idx, column=7, value=data['triad']['lambda'])
        ws_raw.cell(row=row_idx, column=8, value=data['metrics_count'])
        ws_raw.cell(row=row_idx, column=9, value=data['evidence_units'])
        ws_raw.cell(row=row_idx, column=10, value=len(data['vetoes']))
        ws_raw.cell(row=row_idx, column=11, value=len(data['warnings']))
        row_idx += 1
    
    ws_raw.column_dimensions['A'].width = 30
    
    # ========================================================================
    # SHEET 2: INTERPRETATION (Auto-generated insights)
    # ========================================================================
    ws_interp = wb.create_sheet("Interpretation")
    
    # Title
    ws_interp['A1'] = "AUTO-GENERATED INSIGHTS"
    ws_interp['A1'].font = Font(size=14, bold=True, color="FFFFFF")
    ws_interp['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    ws_interp.merge_cells('A1:D1')
    
    # Headers
    ws_interp['A3'] = "Paper"
    ws_interp['B3'] = "Grade"
    ws_interp['C3'] = "Confidence"
    ws_interp['D3'] = "Key Issue"
    
    for col in range(1, 5):
        ws_interp.cell(row=3, column=col).font = Font(bold=True)
    
    # Interpretation logic (formulas reference Raw Scores sheet)
    row_idx = 4
    for i, (title, data) in enumerate(sorted(all_scores.items()), 2):
        ws_interp.cell(row=row_idx, column=1, value=title)
        
        # Grade interpretation
        chi = data['chi']
        if chi >= 7:
            grade = "Excellent"
            color = "C6EFCE"
        elif chi >= 5:
            grade = "Good"
            color = "FFEB9C"
        elif chi >= 3:
            grade = "Acceptable"
            color = "FFE699"
        else:
            grade = "Needs Work"
            color = "FFC7CE"
        
        cell = ws_interp.cell(row=row_idx, column=2, value=grade)
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        
        # Confidence interpretation
        kappa = data['kappa']
        if kappa >= 0.7:
            conf = "High"
        elif kappa >= 0.4:
            conf = "Medium"
        else:
            conf = "Low"
        ws_interp.cell(row=row_idx, column=3, value=conf)
        
        # Key issue detection
        issues = []
        if len(data['vetoes']) > 0:
            issues.append("VETO APPLIED")
        if data['defense']['claims_evidence_ratio'] > 5:
            issues.append("High claims/evidence ratio")
        if len([c for c in data['constraints'] if c['score'] == -1]) > 3:
            issues.append("Multiple constraint violations")
        
        key_issue = "; ".join(issues) if issues else "None detected"
        ws_interp.cell(row=row_idx, column=4, value=key_issue)
        
        row_idx += 1
    
    ws_interp.column_dimensions['A'].width = 30
    ws_interp.column_dimensions['D'].width = 40
    
    # ========================================================================
    # SHEET 3: ACTION ITEMS (What to fix)
    # ========================================================================
    ws_actions = wb.create_sheet("Action Items")
    
    ws_actions['A1'] = "RECOMMENDED FIXES"
    ws_actions['A1'].font = Font(size=14, bold=True, color="FFFFFF")
    ws_actions['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    ws_actions.merge_cells('A1:D1')
    
    ws_actions['A3'] = "Paper"
    ws_actions['B3'] = "Priority"
    ws_actions['C3'] = "Issue"
    ws_actions['D3'] = "Recommended Action"
    
    for col in range(1, 5):
        ws_actions.cell(row=3, column=col).font = Font(bold=True)
    
    row_idx = 4
    for title, data in sorted(all_scores.items()):
        # Veto issues (highest priority)
        if len(data['vetoes']) > 0:
            ws_actions.cell(row=row_idx, column=1, value=title)
            ws_actions.cell(row=row_idx, column=2, value="HIGH")
            ws_actions.cell(row=row_idx, column=2).fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            ws_actions.cell(row=row_idx, column=3, value=data['vetoes'][0])
            ws_actions.cell(row=row_idx, column=4, value="Fix constraint violation to unlock higher chi score")
            row_idx += 1
        
        # Claims/evidence ratio issues
        if data['defense']['claims_evidence_ratio'] > 5:
            ws_actions.cell(row=row_idx, column=1, value=title)
            ws_actions.cell(row=row_idx, column=2, value="MEDIUM")
            ws_actions.cell(row=row_idx, column=2).fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
            ws_actions.cell(row=row_idx, column=3, value=f"Claims/Evidence ratio: {data['defense']['claims_evidence_ratio']:.1f}")
            ws_actions.cell(row=row_idx, column=4, value="Add more evidence: citations, equations, test cases")
            row_idx += 1
        
        # Low confidence issues
        if data['kappa'] < 0.4:
            ws_actions.cell(row=row_idx, column=1, value=title)
            ws_actions.cell(row=row_idx, column=2, value="LOW")
            ws_actions.cell(row=row_idx, column=2).fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            ws_actions.cell(row=row_idx, column=3, value=f"Low confidence: κ = {data['kappa']:.2f}")
            ws_actions.cell(row=row_idx, column=4, value="Increase evidence density and quality")
            row_idx += 1
    
    ws_actions.column_dimensions['A'].width = 30
    ws_actions.column_dimensions['C'].width = 35
    ws_actions.column_dimensions['D'].width = 45
    
    # ========================================================================
    # SHEET 4: FRUIT STRENGTHS (Visual analysis)
    # ========================================================================
    ws_fruits = wb.create_sheet("Fruit Analysis")
    
    ws_fruits['A1'] = "FRUIT STRENGTH ACROSS PAPERS"
    ws_fruits['A1'].font = Font(size=14, bold=True, color="FFFFFF")
    ws_fruits['A1'].fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    ws_fruits.merge_cells('A1:C1')
    
    # Compute average fruit scores
    fruit_names = ['Love', 'Joy', 'Peace', 'Patience', 'Kindness', 'Goodness',
                   'Faithfulness', 'Gentleness', 'Self-Control', 'Truth', 'Wisdom', 'Grace']
    
    fruit_avgs = {}
    for fruit_name in fruit_names:
        scores = []
        for data in all_scores.values():
            for fruit in data['fruits']:
                if fruit['name'] == fruit_name:
                    scores.append(fruit['net'])
        fruit_avgs[fruit_name] = sum(scores) / len(scores) if scores else 0
    
    # Sort by strength
    sorted_fruits = sorted(fruit_avgs.items(), key=lambda x: x[1], reverse=True)
    
    ws_fruits['A3'] = "Fruit"
    ws_fruits['B3'] = "Avg Net Score"
    ws_fruits['C3'] = "Interpretation"
    
    for col in range(1, 4):
        ws_fruits.cell(row=3, column=col).font = Font(bold=True)
    
    row_idx = 4
    for fruit_name, avg_score in sorted_fruits:
        ws_fruits.cell(row=row_idx, column=1, value=fruit_name)
        ws_fruits.cell(row=row_idx, column=2, value=avg_score)
        
        # Interpretation
        if avg_score > 0.1:
            interp = "STRONG - Papers demonstrate this quality"
            color = "C6EFCE"
        elif avg_score > -0.05:
            interp = "NEUTRAL - Mixed signals"
            color = "FFEB9C"
        else:
            interp = "WEAK - Papers lack this quality"
            color = "FFC7CE"
        
        cell = ws_fruits.cell(row=row_idx, column=3, value=interp)
        cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        
        row_idx += 1
    
    ws_fruits.column_dimensions['A'].width = 15
    ws_fruits.column_dimensions['C'].width = 40
    
    # ========================================================================
    # SHEET 5: DETAILED SCORES (For Excel AI to parse)
    # ========================================================================
    ws_detail = wb.create_sheet("Detailed Metrics")
    
    # Flatten all data for easy querying
    headers = ['Paper', 'Chi', 'Kappa', 'Rho']
    
    # Add fruit columns
    for fruit in fruit_names:
        headers.extend([f"{fruit}_score", f"{fruit}_antiscore", f"{fruit}_net"])
    
    # Add constraint columns
    constraint_names = ['Non-Contradiction', 'Falsifiability', 'Predictive Power', 
                       'Explanatory Scope', 'Parsimony', 'Evidence Base',
                       'Internal Consistency', 'Completeness', 'Boundary Regulation']
    for c in constraint_names:
        headers.append(c.replace(' ', '_'))
    
    # Write headers
    for col, header in enumerate(headers, 1):
        ws_detail.cell(row=1, column=col, value=header)
        ws_detail.cell(row=1, column=col).font = Font(bold=True)
    
    # Write data rows
    row_idx = 2
    for title, data in sorted(all_scores.items()):
        col_idx = 1
        ws_detail.cell(row=row_idx, column=col_idx, value=title)
        col_idx += 1
        ws_detail.cell(row=row_idx, column=col_idx, value=data['chi'])
        col_idx += 1
        ws_detail.cell(row=row_idx, column=col_idx, value=data['kappa'])
        col_idx += 1
        ws_detail.cell(row=row_idx, column=col_idx, value=data['rho'])
        col_idx += 1
        
        # Fruits
        for fruit_name in fruit_names:
            for fruit in data['fruits']:
                if fruit['name'] == fruit_name:
                    ws_detail.cell(row=row_idx, column=col_idx, value=fruit['score'])
                    col_idx += 1
                    ws_detail.cell(row=row_idx, column=col_idx, value=fruit.get('anti_score', 0))
                    col_idx += 1
                    ws_detail.cell(row=row_idx, column=col_idx, value=fruit['net'])
                    col_idx += 1
                    break
        
        # Constraints
        for c_name in constraint_names:
            for constraint in data['constraints']:
                if constraint['name'] == c_name:
                    ws_detail.cell(row=row_idx, column=col_idx, value=constraint['score'])
                    col_idx += 1
                    break
        
        row_idx += 1
    
    # Save
    output_path = outputs_dir / "Unified_Scorer_SMART.xlsx"
    wb.save(output_path)
    
    print(f"\n[OK] SMART Excel created: {output_path}")
    print("\nSheets created:")
    print("  1. Raw Scores - Source data")
    print("  2. Interpretation - Auto-generated insights")
    print("  3. Action Items - What to fix")
    print("  4. Fruit Analysis - Visual breakdown")
    print("  5. Detailed Metrics - Full data for Excel AI")
    
    return output_path


if __name__ == "__main__":
    create_smart_excel()
