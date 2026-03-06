"""
Worldview Comparison Matrix Extractor
Extracts which worldviews fail at which axioms
Creates comparison matrix showing where each worldview breaks down
"""

import os
import re
from pathlib import Path
import yaml
import pandas as pd
from collections import defaultdict

def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from markdown content"""
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1))
        except yaml.YAMLError:
            return {}
    return {}

def extract_section(content, section_name):
    """Extract content from a specific markdown section"""
    pattern = rf'^##\s+{re.escape(section_name)}\s*\n(.*?)(?=^##\s|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

class WorldviewMatrixExtractor:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.worldview_failures = defaultdict(list)
        self.axiom_challenges = defaultdict(list)
        
        # Known worldviews to track
        self.worldviews = [
            'Atheism', 'Materialism', 'Physicalism', 'Naturalism',
            'Buddhism', 'Hinduism', 'Islam', 'Judaism',
            'Panpsychism', 'Idealism', 'Dualism',
            'Nihilism', 'Relativism', 'Determinism',
            'Pelagianism', 'Works-Salvation', 'Unitarianism'
        ]
    
    def extract_worldview_mentions(self, content, axiom_id, chain_pos):
        """Extract worldview mentions from axiom content"""
        content_lower = content.lower()
        
        # Check Standard Objections section
        objections = extract_section(content, "Standard Objections")
        
        for worldview in self.worldviews:
            worldview_lower = worldview.lower()
            
            # Check if worldview is mentioned
            if worldview_lower in content_lower:
                # Try to determine if it's a challenge or failure
                context = self.get_worldview_context(content, worldview)
                
                self.worldview_failures[worldview].append({
                    'axiom_id': axiom_id,
                    'chain_position': chain_pos,
                    'context': context,
                    'severity': self.assess_severity(context)
                })
                
                self.axiom_challenges[axiom_id].append({
                    'worldview': worldview,
                    'context': context
                })
    
    def get_worldview_context(self, content, worldview):
        """Get context around worldview mention"""
        worldview_lower = worldview.lower()
        content_lower = content.lower()
        
        # Find position of worldview mention
        pos = content_lower.find(worldview_lower)
        if pos == -1:
            return ""
        
        # Extract surrounding context
        start = max(0, pos - 200)
        end = min(len(content), pos + 200)
        context = content[start:end]
        
        # Clean up
        context = re.sub(r'\s+', ' ', context).strip()
        
        return context
    
    def assess_severity(self, context):
        """Assess how severely the worldview is challenged"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['fails', 'cannot', 'impossible', 'refuted', 'defeated']):
            return 'FATAL'
        elif any(word in context_lower for word in ['challenge', 'difficult', 'problem', 'objection']):
            return 'CHALLENGE'
        else:
            return 'MENTION'
    
    def load_and_analyze(self):
        """Load all axioms and analyze worldview challenges"""
        md_files = []
        for f in Path(self.axioms_folder).glob("*.md"):
            if f.is_file() and re.match(r'^\d{3}_', f.name):
                md_files.append(f)
        
        print(f"Analyzing {len(md_files)} axiom files for worldview challenges...\n")
        
        for filepath in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = extract_yaml_frontmatter(content)
                axiom_id = metadata.get('axiom_id', '')
                chain_pos = metadata.get('chain_position', 999)
                
                if axiom_id:
                    self.extract_worldview_mentions(content, axiom_id, chain_pos)
                    
            except Exception as e:
                print(f"Error processing {filepath.name}: {e}")
        
        print(f"✓ Analysis complete\n")
    
    def generate_matrix_report(self):
        """Generate worldview comparison matrix report"""
        report = []
        report.append("=" * 80)
        report.append("WORLDVIEW COMPARISON MATRIX")
        report.append("=" * 80)
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  Worldviews Tracked: {len(self.worldviews)}")
        report.append(f"  Worldviews with Challenges: {len(self.worldview_failures)}")
        report.append(f"  Axioms with Worldview Challenges: {len(self.axiom_challenges)}")
        report.append("")
        
        # Worldview breakdown
        report.append("=" * 80)
        report.append("WORLDVIEW CHALLENGE BREAKDOWN:")
        report.append("=" * 80)
        report.append("")
        
        for worldview in sorted(self.worldview_failures.keys()):
            failures = self.worldview_failures[worldview]
            fatal = sum(1 for f in failures if f['severity'] == 'FATAL')
            challenges = sum(1 for f in failures if f['severity'] == 'CHALLENGE')
            mentions = sum(1 for f in failures if f['severity'] == 'MENTION')
            
            report.append(f"{worldview}:")
            report.append(f"  Total References: {len(failures)}")
            report.append(f"  Fatal Failures: {fatal}")
            report.append(f"  Challenges: {challenges}")
            report.append(f"  Mentions: {mentions}")
            
            # List fatal failures
            if fatal > 0:
                report.append(f"  Fatal at axioms:")
                for failure in sorted(failures, key=lambda x: x['chain_position']):
                    if failure['severity'] == 'FATAL':
                        report.append(f"    - {failure['axiom_id']} (pos {failure['chain_position']})")
            
            report.append("")
        
        # Axiom breakdown
        report.append("=" * 80)
        report.append("MOST CONTESTED AXIOMS:")
        report.append("=" * 80)
        report.append("")
        
        contested = sorted(self.axiom_challenges.items(), key=lambda x: -len(x[1]))
        
        for axiom_id, challenges in contested[:15]:
            worldviews = [c['worldview'] for c in challenges]
            report.append(f"{axiom_id}: Challenges {len(challenges)} worldview(s)")
            report.append(f"  Worldviews: {', '.join(worldviews)}")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_matrix_excel(self, output_file):
        """Generate Excel matrix showing worldview vs axiom"""
        print("Generating worldview matrix Excel...")
        
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Worldview Matrix"
        
        # Get all axioms that have challenges
        axioms = sorted(set(self.axiom_challenges.keys()))
        
        # Create matrix data
        matrix_data = []
        for worldview in sorted(self.worldview_failures.keys()):
            row = {'Worldview': worldview}
            
            for axiom_id in axioms:
                # Check if this worldview is challenged by this axiom
                challenges = self.axiom_challenges.get(axiom_id, [])
                worldview_challenge = next((c for c in challenges if c['worldview'] == worldview), None)
                
                if worldview_challenge:
                    # Find severity
                    failures = self.worldview_failures[worldview]
                    failure = next((f for f in failures if f['axiom_id'] == axiom_id), None)
                    if failure:
                        row[axiom_id] = failure['severity']
                    else:
                        row[axiom_id] = 'X'
                else:
                    row[axiom_id] = ''
            
            matrix_data.append(row)
        
        # Write to Excel
        df = pd.DataFrame(matrix_data)
        
        # Define styles
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True, size=10)
        fatal_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
        challenge_fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
        mention_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Write headers
        for col_num, column_title in enumerate(df.columns, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = column_title
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True, text_rotation=90)
            cell.border = border
        
        # Write data with color coding
        for row_num, row_data in enumerate(df.values, 2):
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value if value else ''
                cell.border = border
                cell.alignment = Alignment(horizontal='center', vertical='center')
                
                # Color code by severity
                if value == 'FATAL':
                    cell.fill = fatal_fill
                    cell.font = Font(color="FFFFFF", bold=True)
                elif value == 'CHALLENGE':
                    cell.fill = challenge_fill
                elif value == 'MENTION':
                    cell.fill = mention_fill
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 20
        for col in range(2, len(df.columns) + 1):
            ws.column_dimensions[chr(64 + col)].width = 12
        
        # Set row height for header
        ws.row_dimensions[1].height = 100
        
        wb.save(output_file)
        print(f"✓ Matrix Excel saved: {output_file}\n")

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_dir = r"O:\Theophysics_Backend\Python_Backend"
    
    print("=" * 80)
    print("WORLDVIEW COMPARISON MATRIX EXTRACTOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    extractor = WorldviewMatrixExtractor(axioms_folder)
    extractor.load_and_analyze()
    
    # Generate report
    report = extractor.generate_matrix_report()
    print(report)
    
    # Save report
    report_file = os.path.join(output_dir, "worldview_matrix_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✓ Report saved: {report_file}")
    
    # Generate Excel matrix
    excel_file = os.path.join(output_dir, "worldview_comparison_matrix.xlsx")
    extractor.generate_matrix_excel(excel_file)
    
    print(f"\n✓ Worldview matrix analysis complete!")

if __name__ == "__main__":
    main()
