"""
Bible Prophecy Analyzer
Extracts, analyzes, and organizes Bible prophecy data from Excel
Generates comprehensive reports and cross-references
"""

import pandas as pd
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class BibleProphecyAnalyzer:
    def __init__(self, excel_file):
        self.excel_file = excel_file
        self.data = None
        self.sheets = {}
        self.stats = defaultdict(int)
        
    def load_excel(self):
        """Load Excel file and all sheets"""
        print(f"Loading Excel file: {self.excel_file}\n")
        
        try:
            # Load all sheets
            excel_file = pd.ExcelFile(self.excel_file)
            print(f"Found {len(excel_file.sheet_names)} sheet(s):")
            for sheet_name in excel_file.sheet_names:
                print(f"  - {sheet_name}")
                self.sheets[sheet_name] = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            print(f"\n✓ Loaded {len(self.sheets)} sheet(s)\n")
            return True
            
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            return False
    
    def analyze_structure(self):
        """Analyze the structure of each sheet"""
        print("=" * 80)
        print("EXCEL STRUCTURE ANALYSIS")
        print("=" * 80)
        print()
        
        for sheet_name, df in self.sheets.items():
            print(f"Sheet: {sheet_name}")
            print(f"  Rows: {len(df)}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Column Names:")
            for col in df.columns:
                non_null = df[col].notna().sum()
                print(f"    - {col} ({non_null} non-null values)")
            print()
    
    def extract_prophecies(self):
        """Extract and categorize prophecies"""
        print("=" * 80)
        print("EXTRACTING PROPHECIES")
        print("=" * 80)
        print()
        
        all_prophecies = []
        
        for sheet_name, df in self.sheets.items():
            print(f"Processing sheet: {sheet_name}")
            
            # Try to identify key columns
            prophecy_data = {
                'sheet': sheet_name,
                'total_rows': len(df),
                'data': df
            }
            
            all_prophecies.append(prophecy_data)
            print(f"  ✓ Extracted {len(df)} rows\n")
        
        return all_prophecies
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        report = []
        report.append("=" * 80)
        report.append("BIBLE PROPHECY DATABASE SUMMARY")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall statistics
        total_rows = sum(len(df) for df in self.sheets.values())
        report.append("OVERALL STATISTICS:")
        report.append(f"  Total Sheets: {len(self.sheets)}")
        report.append(f"  Total Prophecies/Rows: {total_rows}")
        report.append("")
        
        # Sheet breakdown
        report.append("SHEET BREAKDOWN:")
        for sheet_name, df in self.sheets.items():
            report.append(f"\n{sheet_name}:")
            report.append(f"  Rows: {len(df)}")
            report.append(f"  Columns: {list(df.columns)}")
            
            # Show first few rows as sample
            if len(df) > 0:
                report.append(f"  Sample data (first row):")
                for col in df.columns:
                    value = df[col].iloc[0] if len(df) > 0 else "N/A"
                    report.append(f"    {col}: {value}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def export_to_organized_excel(self, output_file):
        """Export to organized Excel with analysis"""
        print(f"Exporting organized data to: {output_file}")
        
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        wb.remove(wb.active)
        
        # Define styles
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=11)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Create summary sheet
        ws_summary = wb.create_sheet("Summary", 0)
        summary_data = []
        for sheet_name, df in self.sheets.items():
            summary_data.append({
                'Sheet Name': sheet_name,
                'Total Rows': len(df),
                'Columns': len(df.columns),
                'Column Names': ', '.join(df.columns)
            })
        
        df_summary = pd.DataFrame(summary_data)
        
        # Write summary
        for col_num, column_title in enumerate(df_summary.columns, 1):
            cell = ws_summary.cell(row=1, column=col_num)
            cell.value = column_title
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border
        
        for row_num, row_data in enumerate(df_summary.values, 2):
            for col_num, value in enumerate(row_data, 1):
                cell = ws_summary.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = border
                cell.alignment = Alignment(vertical='top', wrap_text=True)
        
        ws_summary.column_dimensions['A'].width = 25
        ws_summary.column_dimensions['B'].width = 15
        ws_summary.column_dimensions['C'].width = 15
        ws_summary.column_dimensions['D'].width = 60
        
        # Copy original sheets with formatting
        for sheet_name, df in self.sheets.items():
            ws = wb.create_sheet(sheet_name[:31])  # Excel sheet name limit
            
            # Write headers
            for col_num, column_title in enumerate(df.columns, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = column_title
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = border
            
            # Write data
            for row_num, row_data in enumerate(df.values, 2):
                for col_num, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    if pd.isna(value):
                        cell.value = ""
                    else:
                        cell.value = value
                    cell.border = border
                    cell.alignment = Alignment(vertical='top', wrap_text=True)
            
            # Auto-adjust column widths
            for col_num, column in enumerate(df.columns, 1):
                max_length = max(
                    len(str(column)),
                    df[column].astype(str).str.len().max() if len(df) > 0 else 0
                )
                ws.column_dimensions[chr(64 + col_num)].width = min(max_length + 2, 50)
            
            ws.freeze_panes = 'A2'
        
        wb.save(output_file)
        print(f"✓ Organized Excel saved: {output_file}\n")
    
    def search_prophecies(self, keyword):
        """Search for keyword across all prophecies"""
        print(f"Searching for: '{keyword}'\n")
        results = []
        
        for sheet_name, df in self.sheets.items():
            for idx, row in df.iterrows():
                # Search in all columns
                for col in df.columns:
                    value = str(row[col]).lower()
                    if keyword.lower() in value:
                        results.append({
                            'sheet': sheet_name,
                            'row': idx + 2,  # Excel row number
                            'column': col,
                            'value': row[col]
                        })
                        break  # Only count once per row
        
        print(f"Found {len(results)} result(s):")
        for i, result in enumerate(results[:20], 1):
            print(f"{i}. Sheet: {result['sheet']}, Row: {result['row']}, Column: {result['column']}")
            print(f"   Value: {result['value']}")
        
        if len(results) > 20:
            print(f"\n... and {len(results) - 20} more results")
        
        return results

def main():
    excel_file = r"C:\Users\lowes\Downloads\Bible prophecies full.xlsx"
    output_dir = r"O:\Theophysics_Backend\Python_Backend"
    
    print("=" * 80)
    print("BIBLE PROPHECY ANALYZER")
    print("=" * 80)
    print()
    
    analyzer = BibleProphecyAnalyzer(excel_file)
    
    # Load Excel
    if not analyzer.load_excel():
        print("Failed to load Excel file. Exiting.")
        return
    
    # Analyze structure
    analyzer.analyze_structure()
    
    # Extract prophecies
    prophecies = analyzer.extract_prophecies()
    
    # Generate summary report
    report = analyzer.generate_summary_report()
    print(report)
    
    # Save report
    report_file = os.path.join(output_dir, "bible_prophecy_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n✓ Report saved: {report_file}")
    
    # Export organized Excel
    output_excel = os.path.join(output_dir, "bible_prophecies_organized.xlsx")
    analyzer.export_to_organized_excel(output_excel)
    
    print("\n" + "=" * 80)
    print("✓ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nOutputs:")
    print(f"  - Report: {report_file}")
    print(f"  - Organized Excel: {output_excel}")
    
    # Interactive search option
    print("\n" + "=" * 80)
    print("SEARCH MODE (optional)")
    print("=" * 80)
    print("Enter keywords to search, or 'quit' to exit")
    
    while True:
        try:
            keyword = input("\nSearch: ").strip()
            if keyword.lower() in ['quit', 'exit', 'q', '']:
                break
            analyzer.search_prophecies(keyword)
        except KeyboardInterrupt:
            break
    
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
