"""
Missing Content Detector
Scans axiom files for incomplete or missing sections
Quality control tool to ensure all axioms are fully documented
"""

import os
import re
from pathlib import Path
import yaml
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
    return None

class MissingContentDetector:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
        # Required sections for different axiom types
        self.required_sections = {
            'all': ['Formal Statement', 'Enables', 'Defeat Conditions'],
            'axiom': ['Standard Objections', 'Defense Summary'],
            'theorem': ['Physics Layer', 'Mathematical Layer'],
            'definition': ['Physics Layer']
        }
        
    def check_file(self, filepath):
        """Check a single axiom file for missing content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata = extract_yaml_frontmatter(content)
            axiom_id = metadata.get('axiom_id', '')
            status = metadata.get('status', '')
            
            if not axiom_id:
                self.issues['no_axiom_id'].append(filepath.name)
                return
            
            file_issues = []
            
            # Check required YAML fields
            required_yaml = ['axiom_id', 'chain_position', 'classification', 'status', 'stage']
            for field in required_yaml:
                if field not in metadata or not metadata[field]:
                    file_issues.append(f"Missing YAML field: {field}")
                    self.stats['missing_yaml_fields'] += 1
            
            # Check for TBD values
            if metadata.get('collapse_radius') == 'TBD':
                file_issues.append("Collapse radius is TBD")
                self.stats['tbd_collapse_radius'] += 1
            
            # Check required sections for all axioms
            for section in self.required_sections['all']:
                section_content = extract_section(content, section)
                if section_content is None:
                    file_issues.append(f"Missing section: {section}")
                    self.stats['missing_sections'] += 1
                elif len(section_content) < 20:
                    file_issues.append(f"Section too short: {section} ({len(section_content)} chars)")
                    self.stats['short_sections'] += 1
            
            # Check type-specific sections
            if status in self.required_sections:
                for section in self.required_sections[status]:
                    section_content = extract_section(content, section)
                    if section_content is None:
                        file_issues.append(f"Missing {status}-specific section: {section}")
                        self.stats['missing_type_sections'] += 1
            
            # Check for empty formal statement
            formal = extract_section(content, 'Formal Statement')
            if formal and len(formal) < 10:
                file_issues.append("Formal statement is too short")
                self.stats['short_formal_statements'] += 1
            
            # Check for broken wiki links
            broken_links = re.findall(r'\[\[\]\]', content)
            if broken_links:
                file_issues.append(f"Found {len(broken_links)} empty wiki links")
                self.stats['broken_links'] += len(broken_links)
            
            # Check for TODO markers
            todos = re.findall(r'TODO|TBD|FIXME|XXX', content, re.IGNORECASE)
            if todos:
                file_issues.append(f"Found {len(todos)} TODO markers")
                self.stats['todo_markers'] += len(todos)
            
            if file_issues:
                self.issues[axiom_id] = file_issues
                self.stats['files_with_issues'] += 1
            else:
                self.stats['complete_files'] += 1
                
        except Exception as e:
            self.issues['error'].append(f"{filepath.name}: {e}")
    
    def scan_all_files(self):
        """Scan all axiom files"""
        md_files = []
        for f in Path(self.axioms_folder).glob("*.md"):
            if f.is_file() and re.match(r'^\d{3}_', f.name):
                md_files.append(f)
        
        print(f"Scanning {len(md_files)} axiom files...\n")
        
        for filepath in md_files:
            self.check_file(filepath)
        
        self.stats['total_files'] = len(md_files)
    
    def generate_report(self):
        """Generate missing content report"""
        report = []
        report.append("=" * 80)
        report.append("MISSING CONTENT DETECTION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Statistics
        report.append("STATISTICS:")
        report.append(f"  Total Files Scanned: {self.stats['total_files']}")
        report.append(f"  Complete Files: {self.stats['complete_files']}")
        report.append(f"  Files with Issues: {self.stats['files_with_issues']}")
        report.append(f"  Missing YAML Fields: {self.stats['missing_yaml_fields']}")
        report.append(f"  Missing Sections: {self.stats['missing_sections']}")
        report.append(f"  Short Sections: {self.stats['short_sections']}")
        report.append(f"  TBD Collapse Radius: {self.stats['tbd_collapse_radius']}")
        report.append(f"  TODO Markers: {self.stats['todo_markers']}")
        report.append(f"  Broken Links: {self.stats['broken_links']}")
        report.append("")
        
        # Completion percentage
        if self.stats['total_files'] > 0:
            completion = (self.stats['complete_files'] / self.stats['total_files']) * 100
            report.append(f"COMPLETION RATE: {completion:.1f}%")
            report.append("")
        
        # Detailed issues
        if self.issues:
            report.append("=" * 80)
            report.append("DETAILED ISSUES BY AXIOM:")
            report.append("=" * 80)
            report.append("")
            
            for axiom_id, issues in sorted(self.issues.items()):
                if axiom_id not in ['no_axiom_id', 'error']:
                    report.append(f"{axiom_id}:")
                    for issue in issues:
                        report.append(f"  ❌ {issue}")
                    report.append("")
            
            # Errors
            if 'error' in self.issues:
                report.append("=" * 80)
                report.append("ERRORS:")
                report.append("=" * 80)
                for error in self.issues['error']:
                    report.append(f"  ⚠️  {error}")
                report.append("")
        
        report.append("=" * 80)
        if self.stats['files_with_issues'] == 0:
            report.append("✓ ALL FILES COMPLETE - No missing content detected!")
        else:
            report.append(f"⚠️  {self.stats['files_with_issues']} files need attention")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def generate_priority_list(self):
        """Generate prioritized list of axioms to complete"""
        priority = []
        
        for axiom_id, issues in sorted(self.issues.items()):
            if axiom_id not in ['no_axiom_id', 'error']:
                # Calculate priority score (higher = more urgent)
                score = 0
                for issue in issues:
                    if 'Missing section' in issue:
                        score += 10
                    elif 'Missing YAML' in issue:
                        score += 5
                    elif 'too short' in issue:
                        score += 3
                    elif 'TBD' in issue:
                        score += 1
                
                priority.append({
                    'axiom_id': axiom_id,
                    'score': score,
                    'issue_count': len(issues),
                    'issues': issues
                })
        
        # Sort by priority score
        priority.sort(key=lambda x: (-x['score'], x['axiom_id']))
        
        report = []
        report.append("=" * 80)
        report.append("PRIORITY COMPLETION LIST")
        report.append("=" * 80)
        report.append("")
        
        for i, item in enumerate(priority[:20], 1):  # Top 20
            report.append(f"{i}. {item['axiom_id']} (Priority Score: {item['score']}, Issues: {item['issue_count']})")
            for issue in item['issues'][:3]:  # Show first 3 issues
                report.append(f"   - {issue}")
            report.append("")
        
        if len(priority) > 20:
            report.append(f"... and {len(priority) - 20} more axioms")
        
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_dir = r"O:\Theophysics_Backend\Python_Backend"
    
    print("=" * 80)
    print("MISSING CONTENT DETECTOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    detector = MissingContentDetector(axioms_folder)
    detector.scan_all_files()
    
    # Generate reports
    report = detector.generate_report()
    print(report)
    
    priority = detector.generate_priority_list()
    print("\n" + priority)
    
    # Save reports
    report_file = os.path.join(output_dir, "missing_content_report.txt")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        f.write("\n\n")
        f.write(priority)
    
    print(f"\n✓ Report saved: {report_file}")

if __name__ == "__main__":
    main()
