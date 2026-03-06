"""
Mermaid Diagram Aggregator
Scans vault for semantic-tagged notes, extracts Mermaid diagrams,
and combines them into master mega-map
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Optional, Set
import re
from datetime import datetime
from collections import defaultdict


class MermaidAggregator:
    """
    Aggregates Mermaid diagrams from semantic-tagged notes.
    Auto-inserts diagrams at note end, creates master diagram.
    """
    
    MERMAID_PATTERN = re.compile(
        r'```mermaid\s*(.*?)\s*```',
        re.DOTALL | re.MULTILINE
    )
    
    SEMANTIC_MARKER = re.compile(r'%%semantic\s*\{', re.IGNORECASE)
    
    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self.diagrams: List[Dict] = []
        self.semantic_notes: List[Path] = []
        self.stats = {
            'notes_scanned': 0,
            'diagrams_found': 0,
            'diagrams_inserted': 0,
            'semantic_notes': 0,
        }
    
    def scan_vault(self, folder: Optional[Path] = None) -> int:
        """
        Scan vault for Mermaid diagrams in semantic-tagged notes.
        
        Returns:
            Number of diagrams found
        """
        search_path = folder if folder else self.vault_path
        
        if not search_path.exists():
            print(f"Vault path not found: {search_path}")
            return 0
        
        print(f"📂 Scanning: {search_path}")
        
        for md_file in search_path.rglob('*.md'):
            self._process_note(md_file)
        
        print(f"\n✓ Scan complete:")
        print(f"  • Notes scanned: {self.stats['notes_scanned']}")
        print(f"  • Semantic notes: {self.stats['semantic_notes']}")
        print(f"  • Diagrams found: {self.stats['diagrams_found']}")
        
        return self.stats['diagrams_found']
    
    def _process_note(self, filepath: Path):
        """Process a single note file."""
        self.stats['notes_scanned'] += 1
        
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"⚠️  Error reading {filepath.name}: {e}")
            return
        
        # Check for semantic tags
        has_semantics = bool(self.SEMANTIC_MARKER.search(content))
        
        if has_semantics:
            self.stats['semantic_notes'] += 1
            self.semantic_notes.append(filepath)
        
        # Extract Mermaid diagrams
        diagrams = self.MERMAID_PATTERN.findall(content)
        
        if diagrams:
            for diagram_code in diagrams:
                self.diagrams.append({
                    'file': filepath,
                    'name': filepath.stem,
                    'code': diagram_code.strip(),
                    'has_semantics': has_semantics,
                })
                self.stats['diagrams_found'] += 1
    
    def auto_insert_diagrams(self) -> int:
        """
        Auto-insert Mermaid diagrams at end of semantic notes that don't have them.
        
        Returns:
            Number of diagrams inserted
        """
        from engine.mermaid_generator import MermaidGenerator
        
        generator = MermaidGenerator()
        inserted_count = 0
        
        print(f"\n📝 Auto-inserting diagrams...")
        
        for note_path in self.semantic_notes:
            try:
                content = note_path.read_text(encoding='utf-8', errors='ignore')
                
                # Skip if already has diagram
                if '```mermaid' in content.lower():
                    continue
                
                # Generate diagram
                diagram_code = generator._generate_mermaid_code(note_path)
                
                if not diagram_code:
                    continue
                
                # Insert at end
                new_content = content.rstrip() + "\n\n## Logical Flow\n\n```mermaid\n" + diagram_code + "\n```\n"
                
                # Write back
                note_path.write_text(new_content, encoding='utf-8')
                
                inserted_count += 1
                print(f"  ✓ Inserted: {note_path.name}")
                
            except Exception as e:
                print(f"  ✗ Failed: {note_path.name} - {e}")
        
        self.stats['diagrams_inserted'] = inserted_count
        print(f"\n✓ Inserted {inserted_count} diagrams")
        
        return inserted_count
    
    def generate_master_diagram(self, output_path: Optional[Path] = None) -> str:
        """
        Generate master diagram combining all semantic-tagged diagrams.
        
        Returns:
            Mermaid code for master diagram
        """
        if not self.diagrams:
            print("No diagrams found to aggregate")
            return ""
        
        print(f"\n🔗 Generating master diagram...")
        
        # Group by type (extract from diagram code)
        by_type = self._group_diagrams_by_type()
        
        # Build master diagram
        master_code = self._build_master_diagram(by_type)
        
        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as markdown with diagram
            full_content = f"""# Master Theophysics Diagram
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Aggregated from {len(self.diagrams)} semantic-tagged notes.

```mermaid
{master_code}
```
"""
            output_path.write_text(full_content, encoding='utf-8')
            print(f"✓ Master diagram saved: {output_path}")
        
        return master_code
    
    def _group_diagrams_by_type(self) -> Dict[str, List[Dict]]:
        """Group diagrams by element type (Axiom, Theorem, etc.)."""
        by_type = defaultdict(list)
        
        for diagram in self.diagrams:
            # Extract node types from diagram code
            code = diagram['code']
            
            # Simple heuristic - look for common patterns
            if 'axiom' in code.lower() or re.search(r'A\d+', code):
                by_type['Axioms'].append(diagram)
            elif 'theorem' in code.lower() or re.search(r'T\d+', code):
                by_type['Theorems'].append(diagram)
            elif 'claim' in code.lower() or re.search(r'C\d+', code):
                by_type['Claims'].append(diagram)
            else:
                by_type['Other'].append(diagram)
        
        return by_type
    
    def _build_master_diagram(self, by_type: Dict[str, List[Dict]]) -> str:
        """Build master Mermaid diagram from grouped diagrams."""
        lines = [
            "graph TB",
            "  %% Master Theophysics Diagram",
            "  %% Auto-generated from semantic vault scan",
            ""
        ]
        
        # Create color-coded nodes for each type
        node_id = 0
        connections = []
        
        for type_name, diagrams in by_type.items():
            if not diagrams:
                continue
            
            # Create subgraph for this type
            lines.append(f"  subgraph {type_name}")
            
            for diagram in diagrams:
                node_id += 1
                node_name = diagram['name'].replace(' ', '_')
                
                # Extract first node from diagram as representative
                first_line = diagram['code'].split('\n')[0] if '\n' in diagram['code'] else diagram['code']
                
                lines.append(f"    N{node_id}[{node_name}]")
                
                # Try to extract connections
                if '-->' in diagram['code']:
                    # Has explicit connections
                    matches = re.findall(r'(\w+)\s*-->\s*(\w+)', diagram['code'])
                    for src, dst in matches:
                        connections.append(f"  {src} --> {dst}")
            
            lines.append("  end")
            lines.append("")
        
        # Add connections
        if connections:
            lines.append("  %% Cross-references")
            lines.extend(connections[:20])  # Limit to 20 connections to avoid clutter
        
        # Add styling
        lines.extend([
            "",
            "  %% Styling",
            "  classDef axiomClass fill:#1a237e,color:#fff",
            "  classDef theoremClass fill:#e65100,color:#fff",
            "  classDef claimClass fill:#1b5e20,color:#fff",
        ])
        
        return "\n".join(lines)
    
    def export_master_png(
        self,
        master_diagram_path: Path,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """
        Export master diagram to PNG using mmdc.
        
        Args:
            master_diagram_path: Path to markdown file with master diagram
            output_path: Optional output PNG path
            
        Returns:
            Path to generated PNG or None
        """
        import subprocess
        
        if not output_path:
            output_path = master_diagram_path.with_suffix('.png')
        
        try:
            # Use mmdc (mermaid-cli)
            result = subprocess.run(
                ['mmdc', '-i', str(master_diagram_path), '-o', str(output_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✓ Master PNG exported: {output_path}")
                return output_path
            else:
                print(f"✗ PNG export failed: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("✗ mmdc not found. Install with:")
            print("   npm install -g @mermaid-js/mermaid-cli")
            return None
        except Exception as e:
            print(f"✗ Export failed: {e}")
            return None
    
    def generate_index(self, output_path: Path):
        """Generate index page with all diagrams."""
        lines = [
            "# Theophysics Semantic Diagram Index",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            f"Total diagrams: {self.stats['diagrams_found']}",
            f"Semantic notes: {self.stats['semantic_notes']}",
            "",
            "## Diagrams by Note",
            ""
        ]
        
        # Group by file
        by_file = defaultdict(list)
        for diagram in self.diagrams:
            by_file[diagram['file']].append(diagram)
        
        for filepath, file_diagrams in sorted(by_file.items()):
            lines.append(f"### [[{filepath.stem}]]")
            lines.append("")
            
            for diagram in file_diagrams:
                lines.append("```mermaid")
                lines.append(diagram['code'])
                lines.append("```")
                lines.append("")
        
        output_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"✓ Index generated: {output_path}")


# === CONVENIENCE FUNCTIONS ===

def aggregate_vault_diagrams(
    vault_path: Path | str,
    auto_insert: bool = False,
    generate_master: bool = True,
    export_png: bool = False
) -> MermaidAggregator:
    """
    Convenience function for full vault aggregation workflow.
    
    Example:
        agg = aggregate_vault_diagrams(
            "O:/THEOPHYSICS",
            auto_insert=True,
            generate_master=True,
            export_png=True
        )
    """
    agg = MermaidAggregator(Path(vault_path))
    
    # Scan vault
    agg.scan_vault()
    
    # Auto-insert diagrams
    if auto_insert:
        agg.auto_insert_diagrams()
    
    # Generate master
    if generate_master:
        master_path = Path(vault_path) / "_Index" / "Master_Diagram.md"
        agg.generate_master_diagram(master_path)
        
        # Export PNG
        if export_png:
            agg.export_master_png(master_path)
    
    return agg


if __name__ == "__main__":
    # Test script
    print("=" * 70)
    print("MERMAID AGGREGATOR TEST")
    print("=" * 70)
    
    vault_path = Path("O:/THEOPHYSICS")
    
    if not vault_path.exists():
        print(f"\nVault not found: {vault_path}")
        print("Update vault_path and try again.")
    else:
        agg = MermaidAggregator(vault_path)
        agg.scan_vault()
        
        if agg.diagrams:
            print(f"\nFound {len(agg.diagrams)} diagrams")
            print("\nRun full workflow with:")
            print("  python -c \"from engine.mermaid_aggregator import *; ")
            print("  aggregate_vault_diagrams('O:/THEOPHYSICS', auto_insert=True)\"")
        else:
            print("\nNo Mermaid diagrams found in vault")
