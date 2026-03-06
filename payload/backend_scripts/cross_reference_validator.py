"""
Cross-Reference Validator
Validates that all axiom dependencies and enables references are valid
Detects broken chains, circular dependencies, and orphaned axioms
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

def extract_enables_from_content(content):
    """Extract enables references from markdown content"""
    section_pattern = r'^##\s+Enables\s*\n(.*?)(?=^##\s|\Z)'
    match = re.search(section_pattern, content, re.MULTILINE | re.DOTALL)
    
    enables = []
    if match:
        section = match.group(1)
        # Find all axiom references like [[002_A1.2_Distinction|A1.2]] or A1.2
        refs = re.findall(r'(?:\[\[.*?\|)?([A-Z]+\d+(?:\.\d+)?)', section)
        enables.extend(refs)
    
    return enables

class AxiomValidator:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.axioms = {}
        self.errors = []
        self.warnings = []
        self.stats = defaultdict(int)
        
    def load_axioms(self):
        """Load all axiom files"""
        md_files = []
        for f in Path(self.axioms_folder).glob("*.md"):
            if f.is_file() and re.match(r'^\d{3}_', f.name):
                md_files.append(f)
        
        print(f"Loading {len(md_files)} axiom files...")
        
        for filepath in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = extract_yaml_frontmatter(content)
                axiom_id = metadata.get('axiom_id', '')
                
                if axiom_id:
                    self.axioms[axiom_id] = {
                        'file': filepath.name,
                        'chain_position': metadata.get('chain_position', None),
                        'depends_on': metadata.get('depends_on', []) or [],
                        'enables_yaml': metadata.get('enables', []) or [],
                        'enables_content': extract_enables_from_content(content),
                        'metadata': metadata
                    }
                    self.stats['total_axioms'] += 1
            except Exception as e:
                self.errors.append(f"Error loading {filepath.name}: {e}")
        
        print(f"✓ Loaded {len(self.axioms)} axioms\n")
    
    def validate_dependencies(self):
        """Check that all depends_on references exist"""
        print("Validating dependencies...")
        
        for axiom_id, data in self.axioms.items():
            depends_on = data['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                if dep and dep not in self.axioms:
                    self.errors.append(f"{axiom_id} depends on non-existent axiom: {dep}")
                    self.stats['broken_dependencies'] += 1
        
        print(f"✓ Checked {self.stats['total_axioms']} axioms for broken dependencies\n")
    
    def validate_enables(self):
        """Check that all enables references exist"""
        print("Validating enables references...")
        
        for axiom_id, data in self.axioms.items():
            # Check YAML enables
            enables_yaml = data['enables_yaml']
            if isinstance(enables_yaml, str):
                enables_yaml = [enables_yaml]
            
            for enable in enables_yaml:
                if enable and enable not in self.axioms:
                    self.errors.append(f"{axiom_id} enables non-existent axiom (YAML): {enable}")
                    self.stats['broken_enables'] += 1
            
            # Check content enables
            for enable in data['enables_content']:
                if enable and enable not in self.axioms:
                    self.warnings.append(f"{axiom_id} references non-existent axiom (content): {enable}")
        
        print(f"✓ Checked enables references\n")
    
    def detect_circular_dependencies(self):
        """Detect circular dependency chains"""
        print("Detecting circular dependencies...")
        
        def has_cycle(axiom_id, visited, rec_stack):
            visited.add(axiom_id)
            rec_stack.add(axiom_id)
            
            depends_on = self.axioms[axiom_id]['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                if dep and dep in self.axioms:
                    if dep not in visited:
                        if has_cycle(dep, visited, rec_stack):
                            return True
                    elif dep in rec_stack:
                        self.errors.append(f"Circular dependency detected: {axiom_id} → {dep}")
                        self.stats['circular_deps'] += 1
                        return True
            
            rec_stack.remove(axiom_id)
            return False
        
        visited = set()
        for axiom_id in self.axioms:
            if axiom_id not in visited:
                has_cycle(axiom_id, visited, set())
        
        print(f"✓ Checked for circular dependencies\n")
    
    def find_orphaned_axioms(self):
        """Find axioms that nothing depends on or enables"""
        print("Finding orphaned axioms...")
        
        referenced = set()
        
        for axiom_id, data in self.axioms.items():
            # Add all dependencies
            depends_on = data['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            referenced.update(dep for dep in depends_on if dep)
            
            # Add all enables
            enables = data['enables_yaml']
            if isinstance(enables, str):
                enables = [enables]
            referenced.update(en for en in enables if en)
        
        for axiom_id in self.axioms:
            if axiom_id not in referenced:
                chain_pos = self.axioms[axiom_id]['chain_position']
                # Only warn if it's not a terminal axiom (last few in chain)
                if chain_pos and chain_pos < 185:
                    self.warnings.append(f"{axiom_id} (pos {chain_pos}) is not referenced by any other axiom")
                    self.stats['orphaned'] += 1
        
        print(f"✓ Checked for orphaned axioms\n")
    
    def validate_chain_sequence(self):
        """Validate that chain positions are sequential and complete"""
        print("Validating chain sequence...")
        
        positions = {}
        for axiom_id, data in self.axioms.items():
            pos = data['chain_position']
            if pos:
                if pos in positions:
                    self.errors.append(f"Duplicate chain position {pos}: {axiom_id} and {positions[pos]}")
                    self.stats['duplicate_positions'] += 1
                positions[pos] = axiom_id
        
        # Check for gaps
        if positions:
            max_pos = max(positions.keys())
            for i in range(1, max_pos + 1):
                if i not in positions:
                    self.warnings.append(f"Gap in chain sequence at position {i}")
                    self.stats['gaps'] += 1
        
        print(f"✓ Validated chain sequence (1-{max(positions.keys()) if positions else 0})\n")
    
    def generate_report(self):
        """Generate validation report"""
        report = []
        report.append("=" * 80)
        report.append("AXIOM CROSS-REFERENCE VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Statistics
        report.append("STATISTICS:")
        report.append(f"  Total Axioms: {self.stats['total_axioms']}")
        report.append(f"  Broken Dependencies: {self.stats['broken_dependencies']}")
        report.append(f"  Broken Enables: {self.stats['broken_enables']}")
        report.append(f"  Circular Dependencies: {self.stats['circular_deps']}")
        report.append(f"  Orphaned Axioms: {self.stats['orphaned']}")
        report.append(f"  Duplicate Positions: {self.stats['duplicate_positions']}")
        report.append(f"  Chain Gaps: {self.stats['gaps']}")
        report.append("")
        
        # Errors
        if self.errors:
            report.append("=" * 80)
            report.append(f"ERRORS ({len(self.errors)}):")
            report.append("=" * 80)
            for error in self.errors:
                report.append(f"  ❌ {error}")
            report.append("")
        else:
            report.append("✓ NO ERRORS FOUND")
            report.append("")
        
        # Warnings
        if self.warnings:
            report.append("=" * 80)
            report.append(f"WARNINGS ({len(self.warnings)}):")
            report.append("=" * 80)
            for warning in self.warnings[:20]:  # Limit to first 20
                report.append(f"  ⚠️  {warning}")
            if len(self.warnings) > 20:
                report.append(f"  ... and {len(self.warnings) - 20} more warnings")
            report.append("")
        else:
            report.append("✓ NO WARNINGS")
            report.append("")
        
        report.append("=" * 80)
        if not self.errors:
            report.append("✓ VALIDATION PASSED - Axiom chain integrity verified!")
        else:
            report.append("❌ VALIDATION FAILED - Please fix errors above")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_validations(self):
        """Run all validation checks"""
        self.load_axioms()
        self.validate_dependencies()
        self.validate_enables()
        self.detect_circular_dependencies()
        self.find_orphaned_axioms()
        self.validate_chain_sequence()
        
        return self.generate_report()

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_file = r"O:\Theophysics_Backend\Python_Backend\validation_report.txt"
    
    print("=" * 80)
    print("AXIOM CROSS-REFERENCE VALIDATOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    validator = AxiomValidator(axioms_folder)
    report = validator.run_all_validations()
    
    # Print to console
    print(report)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ Report saved to: {output_file}")

if __name__ == "__main__":
    main()
