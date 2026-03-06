"""
THEOPHYSICS MERMAID GENERATOR
=============================
Generates Mermaid dependency graphs from semantic tags.

Dual output:
1. Inline mermaid code block for markdown dashboards
2. Full-size PNG exported to O:\00_MEDIA\Mermaid\

Usage:
    from engine.mermaid_generator import MermaidGenerator
    
    gen = MermaidGenerator()
    gen.generate_for_file("path/to/axiom.md")
    gen.generate_for_folder("path/to/folder")
"""

import re
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class MermaidGenerator:
    """Generate Mermaid graphs from semantic tags."""
    
    # Output directory for PNG exports
    MEDIA_OUTPUT = Path(r"O:\00_MEDIA\Mermaid")
    
    # Node colors by type
    NODE_COLORS = {
        'Axiom': '#1a237e',        # Deep blue
        'Theorem': '#e65100',       # Orange
        'Equation': '#7b1fa2',      # Purple
        'Claim': '#00838f',         # Teal
        'EvidenceBundle': '#2e7d32', # Green
        'Relationship': '#546e7a',   # Blue-grey
        'BoundaryCondition': '#c62828', # Red
        'Definition': '#4527a0',    # Deep purple
        'Law': '#ffd600',           # Gold
    }
    
    # Semantic tag pattern: %%tag::Type::UUID::"Title"::ParentUUID%%
    TAG_PATTERN = re.compile(
        r'%%tag::(\w+)::([a-f0-9-]+)::"([^"]+)"(?:::([a-f0-9-]+))?%%',
        re.IGNORECASE
    )
    
    def __init__(self, media_output: Optional[Path] = None):
        """Initialize generator with optional custom output path."""
        self.media_output = media_output or self.MEDIA_OUTPUT
        self.media_output.mkdir(parents=True, exist_ok=True)
    
    def extract_tags(self, filepath: Path) -> List[Dict]:
        """Extract semantic tags from a markdown file."""
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        tags = []
        
        for match in self.TAG_PATTERN.finditer(content):
            tag_type, uuid, title, parent_uuid = match.groups()
            tags.append({
                'type': tag_type,
                'uuid': uuid,
                'title': title,
                'parent_uuid': parent_uuid,
                'source_file': filepath.name
            })
        
        return tags
    
    def generate_mermaid_code(self, tags: List[Dict], title: str = "Dependency Graph") -> str:
        """Generate Mermaid flowchart code from tags."""
        if not tags:
            return ""
        
        lines = [
            f"---",
            f"title: {title}",
            f"---",
            "flowchart LR"
        ]
        
        # Track nodes we've defined
        defined_nodes = set()
        
        # Define all nodes first
        for tag in tags:
            uuid_short = tag['uuid'][:8]
            node_type = tag['type']
            title_clean = tag['title'].replace('"', "'")[:30]  # Truncate long titles
            
            # Get color for this type
            color = self.NODE_COLORS.get(node_type, '#607d8b')
            
            if uuid_short not in defined_nodes:
                # Node shape based on type
                if node_type == 'Axiom':
                    lines.append(f'    {uuid_short}["{title_clean}"]')
                elif node_type == 'Theorem':
                    lines.append(f'    {uuid_short}(("{title_clean}"))')
                elif node_type == 'Equation':
                    lines.append(f'    {uuid_short}[/"{title_clean}"/]')
                elif node_type == 'EvidenceBundle':
                    lines.append(f'    {uuid_short}>"{title_clean}"]')
                else:
                    lines.append(f'    {uuid_short}("{title_clean}")')
                
                defined_nodes.add(uuid_short)
        
        # Add edges from parent relationships
        for tag in tags:
            if tag['parent_uuid']:
                parent_short = tag['parent_uuid'][:8]
                child_short = tag['uuid'][:8]
                if parent_short in defined_nodes:
                    lines.append(f'    {parent_short} --> {child_short}')
        
        # Add style classes
        lines.append("")
        lines.append("    %% Styles")
        for tag in tags:
            uuid_short = tag['uuid'][:8]
            color = self.NODE_COLORS.get(tag['type'], '#607d8b')
            lines.append(f'    style {uuid_short} fill:{color},color:#fff')
        
        return "\n".join(lines)
    
    def generate_inline_mermaid(self, tags: List[Dict], title: str = "Dependency Graph") -> str:
        """Generate inline mermaid code block for markdown embedding."""
        mermaid_code = self.generate_mermaid_code(tags, title)
        if not mermaid_code:
            return ""
        
        return f"```mermaid\n{mermaid_code}\n```"
    
    def export_to_png(self, mermaid_code: str, output_name: str) -> Optional[Path]:
        """Export mermaid code to PNG using mermaid-cli."""
        if not mermaid_code:
            return None
        
        output_path = self.media_output / f"{output_name}.png"
        
        # Write mermaid code to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False, encoding='utf-8') as f:
            f.write(mermaid_code)
            temp_mmd = f.name
        
        try:
            # Run mermaid-cli
            result = subprocess.run(
                ['cmd', '/c', f'npx @mermaid-js/mermaid-cli -i "{temp_mmd}" -o "{output_path}" -w 2000 -H 1200 -b transparent'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if output_path.exists():
                print(f"✅ PNG exported: {output_path}")
                return output_path
            else:
                print(f"❌ PNG export failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Mermaid CLI timed out")
            return None
        except Exception as e:
            print(f"❌ PNG export error: {e}")
            return None
        finally:
            # Clean up temp file
            Path(temp_mmd).unlink(missing_ok=True)
    
    def generate_for_file(self, filepath: str, export_png: bool = True) -> Tuple[str, Optional[Path]]:
        """
        Generate mermaid for a single file.
        
        Returns:
            (inline_mermaid, png_path)
        """
        path = Path(filepath)
        if not path.exists():
            print(f"❌ File not found: {filepath}")
            return "", None
        
        tags = self.extract_tags(path)
        if not tags:
            print(f"⚠️ No semantic tags found in: {path.name}")
            return "", None
        
        title = path.stem.replace('_', ' ')
        mermaid_code = self.generate_mermaid_code(tags, title)
        inline = self.generate_inline_mermaid(tags, title)
        
        png_path = None
        if export_png:
            png_path = self.export_to_png(mermaid_code, path.stem)
        
        return inline, png_path
    
    def generate_for_folder(self, folder_path: str, export_png: bool = True) -> Dict[str, Tuple[str, Optional[Path]]]:
        """
        Generate mermaid for all .md files in a folder.
        
        Returns:
            Dict mapping filename to (inline_mermaid, png_path)
        """
        folder = Path(folder_path)
        if not folder.exists():
            print(f"❌ Folder not found: {folder_path}")
            return {}
        
        results = {}
        md_files = list(folder.glob("*.md"))
        
        print(f"🔍 Found {len(md_files)} markdown files")
        
        for i, md_file in enumerate(md_files, 1):
            print(f"[{i}/{len(md_files)}] Processing: {md_file.name}")
            inline, png_path = self.generate_for_file(md_file, export_png)
            results[md_file.name] = (inline, png_path)
        
        return results
    
    def add_to_dashboard(self, dashboard_path: str, inline_mermaid: str, png_path: Optional[Path] = None) -> bool:
        """
        Add mermaid graph to an existing dashboard markdown file.
        
        Adds both:
        - Inline mermaid code block
        - Link to full PNG (if available)
        """
        path = Path(dashboard_path)
        if not path.exists():
            print(f"❌ Dashboard not found: {dashboard_path}")
            return False
        
        content = path.read_text(encoding='utf-8')
        
        # Build the mermaid section
        mermaid_section = "\n\n---\n\n## Dependency Graph\n\n"
        
        if png_path and png_path.exists():
            # Add link to full-size PNG
            mermaid_section += f"📊 [View Full Size]({png_path})\n\n"
        
        mermaid_section += inline_mermaid
        mermaid_section += "\n"
        
        # Check if there's already a dependency graph section
        if "## Dependency Graph" in content:
            # Replace existing
            content = re.sub(
                r'## Dependency Graph.*?(?=\n## |\n---|\Z)',
                mermaid_section.strip() + "\n",
                content,
                flags=re.DOTALL
            )
        else:
            # Append before final signature or at end
            if "*Generated by" in content:
                content = content.replace(
                    "*Generated by",
                    mermaid_section + "\n*Generated by"
                )
            else:
                content += mermaid_section
        
        path.write_text(content, encoding='utf-8')
        print(f"✅ Updated dashboard: {path.name}")
        return True


def main():
    """CLI for mermaid generation."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python mermaid_generator.py <file.md>        - Generate for single file")
        print("  python mermaid_generator.py folder <path>    - Generate for all files in folder")
        print("")
        print(f"PNG output: {MermaidGenerator.MEDIA_OUTPUT}")
        return
    
    gen = MermaidGenerator()
    
    if sys.argv[1] == "folder" and len(sys.argv) > 2:
        results = gen.generate_for_folder(sys.argv[2])
        print(f"\n✅ Processed {len(results)} files")
        successful = sum(1 for _, (inline, png) in results.items() if inline)
        print(f"   {successful} had semantic tags")
    else:
        inline, png_path = gen.generate_for_file(sys.argv[1])
        if inline:
            print("\n--- Inline Mermaid ---")
            print(inline[:500] + "..." if len(inline) > 500 else inline)
            if png_path:
                print(f"\n--- PNG ---")
                print(f"{png_path}")


if __name__ == "__main__":
    main()
