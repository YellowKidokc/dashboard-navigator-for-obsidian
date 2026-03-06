"""
Chain Validator
Validates the logical continuity of the axiom chain from 001 to 188
Ensures each axiom properly depends on previous axioms
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

class ChainValidator:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.axioms = {}
        self.chain_order = []
        self.errors = []
        self.warnings = []
        
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
                chain_pos = metadata.get('chain_position')
                
                if axiom_id and chain_pos:
                    self.axioms[axiom_id] = {
                        'file': filepath.name,
                        'chain_position': chain_pos,
                        'depends_on': metadata.get('depends_on', []) or [],
                        'stage': metadata.get('stage', 0),
                        'status': metadata.get('status', '')
                    }
                    self.chain_order.append((chain_pos, axiom_id))
            except Exception as e:
                self.errors.append(f"Error loading {filepath.name}: {e}")
        
        # Sort by chain position
        self.chain_order.sort()
        
        print(f"✓ Loaded {len(self.axioms)} axioms\n")
    
    def validate_forward_dependencies(self):
        """Ensure axioms only depend on earlier axioms in the chain"""
        print("Validating forward dependencies...")
        
        position_map = {aid: pos for pos, aid in self.chain_order}
        
        for axiom_id, data in self.axioms.items():
            current_pos = data['chain_position']
            depends_on = data['depends_on']
            
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                if dep and dep in position_map:
                    dep_pos = position_map[dep]
                    if dep_pos >= current_pos:
                        self.errors.append(
                            f"{axiom_id} (pos {current_pos}) depends on {dep} (pos {dep_pos}) "
                            f"which comes later in the chain!"
                        )
                elif dep:
                    self.warnings.append(f"{axiom_id} depends on unknown axiom: {dep}")
        
        print(f"✓ Checked forward dependencies\n")
    
    def validate_stage_progression(self):
        """Ensure stages progress logically"""
        print("Validating stage progression...")
        
        prev_stage = -1
        stage_transitions = []
        
        for pos, axiom_id in self.chain_order:
            current_stage = self.axioms[axiom_id]['stage']
            
            if current_stage < prev_stage - 1:
                self.warnings.append(
                    f"{axiom_id} (pos {pos}) stage {current_stage} jumps backward from stage {prev_stage}"
                )
            
            if current_stage > prev_stage:
                stage_transitions.append((pos, axiom_id, prev_stage, current_stage))
                prev_stage = current_stage
        
        print(f"  Found {len(stage_transitions)} stage transitions")
        for pos, axiom_id, old_stage, new_stage in stage_transitions[:10]:
            print(f"    Position {pos} ({axiom_id}): Stage {old_stage} → {new_stage}")
        
        print()
    
    def validate_dependency_reachability(self):
        """Ensure all dependencies form a connected graph back to roots"""
        print("Validating dependency reachability...")
        
        def get_all_ancestors(axiom_id, visited=None):
            """Recursively get all ancestor axioms"""
            if visited is None:
                visited = set()
            
            if axiom_id in visited:
                return visited
            
            visited.add(axiom_id)
            
            if axiom_id not in self.axioms:
                return visited
            
            depends_on = self.axioms[axiom_id]['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                if dep and dep in self.axioms:
                    get_all_ancestors(dep, visited)
            
            return visited
        
        # Find root axioms (no dependencies)
        roots = [aid for aid, data in self.axioms.items() if not data['depends_on']]
        print(f"  Found {len(roots)} root axioms: {', '.join(sorted(roots)[:5])}")
        
        # Check if all axioms can reach a root
        unreachable = []
        for axiom_id in self.axioms:
            ancestors = get_all_ancestors(axiom_id)
            if not any(root in ancestors for root in roots):
                unreachable.append(axiom_id)
        
        if unreachable:
            self.warnings.append(f"{len(unreachable)} axioms cannot reach a root axiom")
            for axiom_id in unreachable[:5]:
                self.warnings.append(f"  - {axiom_id}")
        
        print(f"✓ Checked reachability\n")
    
    def validate_chain_completeness(self):
        """Ensure the chain is complete from 1 to 188"""
        print("Validating chain completeness...")
        
        positions = [pos for pos, _ in self.chain_order]
        
        if not positions:
            self.errors.append("No axioms found in chain!")
            return
        
        min_pos = min(positions)
        max_pos = max(positions)
        
        print(f"  Chain range: {min_pos} to {max_pos}")
        
        # Check for gaps
        gaps = []
        for i in range(min_pos, max_pos + 1):
            if i not in positions:
                gaps.append(i)
        
        if gaps:
            self.warnings.append(f"Found {len(gaps)} gaps in chain sequence")
            if len(gaps) <= 10:
                self.warnings.append(f"  Missing positions: {gaps}")
            else:
                self.warnings.append(f"  Missing positions: {gaps[:10]} ... and {len(gaps)-10} more")
        
        # Check for duplicates
        duplicates = defaultdict(list)
        for pos, axiom_id in self.chain_order:
            duplicates[pos].append(axiom_id)
        
        for pos, axioms in duplicates.items():
            if len(axioms) > 1:
                self.errors.append(f"Position {pos} has multiple axioms: {', '.join(axioms)}")
        
        print(f"✓ Checked completeness\n")
    
    def analyze_dependency_depth(self):
        """Analyze how deep dependency chains go"""
        print("Analyzing dependency depth...")
        
        def get_depth(axiom_id, visited=None):
            """Get maximum dependency depth"""
            if visited is None:
                visited = set()
            
            if axiom_id in visited:
                return 0  # Circular dependency
            
            if axiom_id not in self.axioms:
                return 0
            
            visited.add(axiom_id)
            
            depends_on = self.axioms[axiom_id]['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            if not depends_on or not any(d for d in depends_on if d):
                return 0
            
            max_depth = 0
            for dep in depends_on:
                if dep and dep in self.axioms:
                    depth = get_depth(dep, visited.copy())
                    max_depth = max(max_depth, depth)
            
            return max_depth + 1
        
        depths = {}
        for axiom_id in self.axioms:
            depths[axiom_id] = get_depth(axiom_id)
        
        max_depth = max(depths.values()) if depths else 0
        avg_depth = sum(depths.values()) / len(depths) if depths else 0
        
        print(f"  Maximum dependency depth: {max_depth}")
        print(f"  Average dependency depth: {avg_depth:.1f}")
        
        # Find deepest chains
        deepest = sorted(depths.items(), key=lambda x: -x[1])[:5]
        print(f"  Deepest dependency chains:")
        for axiom_id, depth in deepest:
            pos = self.axioms[axiom_id]['chain_position']
            print(f"    {axiom_id} (pos {pos}): depth {depth}")
        
        print()
    
    def generate_report(self):
        """Generate validation report"""
        report = []
        report.append("=" * 80)
        report.append("CHAIN VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Statistics
        report.append("CHAIN STATISTICS:")
        if self.chain_order:
            positions = [pos for pos, _ in self.chain_order]
            report.append(f"  Total Axioms: {len(self.axioms)}")
            report.append(f"  Chain Range: {min(positions)} to {max(positions)}")
            report.append(f"  Total Positions: {max(positions) - min(positions) + 1}")
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
            report.append("✓ NO ERRORS - Chain integrity verified!")
            report.append("")
        
        # Warnings
        if self.warnings:
            report.append("=" * 80)
            report.append(f"WARNINGS ({len(self.warnings)}):")
            report.append("=" * 80)
            for warning in self.warnings[:20]:
                report.append(f"  ⚠️  {warning}")
            if len(self.warnings) > 20:
                report.append(f"  ... and {len(self.warnings) - 20} more warnings")
            report.append("")
        
        report.append("=" * 80)
        if not self.errors:
            report.append("✓ CHAIN VALIDATION PASSED")
        else:
            report.append("❌ CHAIN VALIDATION FAILED")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def run_all_validations(self):
        """Run all validation checks"""
        self.load_axioms()
        self.validate_chain_completeness()
        self.validate_forward_dependencies()
        self.validate_stage_progression()
        self.validate_dependency_reachability()
        self.analyze_dependency_depth()
        
        return self.generate_report()

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_file = r"O:\Theophysics_Backend\Python_Backend\chain_validation_report.txt"
    
    print("=" * 80)
    print("CHAIN VALIDATOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    validator = ChainValidator(axioms_folder)
    report = validator.run_all_validations()
    
    print(report)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ Report saved: {output_file}")

if __name__ == "__main__":
    main()
