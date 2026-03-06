"""
SEMANTIC MERMAID GRAPH GENERATOR
================================
Generates Mermaid relationship graphs from semantic markup in Obsidian notes.
Can visualize how papers connect, concept relationships, and argument flow.

Author: David Lowe & Claude
Date: 2025-12-14

Usage:
    from core.semantic_mermaid_generator import SemanticMermaidGenerator
    
    generator = SemanticMermaidGenerator(vault_path)
    generator.scan_folder("path/to/papers")
    mermaid_code = generator.generate_mermaid()
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


class SemanticMermaidGenerator:
    """Generates Mermaid graphs from semantic markup in Obsidian notes"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.nodes: Dict[str, dict] = {}  # id -> {label, type, file}
        self.edges: List[Tuple[str, str, str]] = []  # (from, to, label)
        self.papers: Dict[str, dict] = {}  # paper_id -> {title, concepts, refs}
        
        # Color scheme for different semantic types
        self.type_colors = {
            'axiom': '#ff6b6b',       # Red
            'hypothesis': '#4ecdc4',   # Teal
            'evidence': '#45b7d1',     # Blue
            'theorem': '#96ceb4',      # Green
            'claim': '#ffeaa7',        # Yellow
            'definition': '#dfe6e9',   # Gray
            'variable': '#a29bfe',     # Purple
            'equation': '#fd79a8',     # Pink
            'law': '#00b894',          # Emerald
            'bridge': '#e17055',       # Orange
            'objection': '#d63031',    # Dark red
            'response': '#00cec9',     # Cyan
            'paper': '#6c5ce7',        # Deep purple
            'part': '#0984e3',         # Bright blue
            'section': '#74b9ff',      # Light blue
        }
        
        # Paper hierarchy
        self.paper_structure = {
            'P01': {'title': 'Logos Principle', 'part': 'I'},
            'P02': {'title': 'Quantum Bridge', 'part': 'I'},
            'P03': {'title': 'Algorithm Reality', 'part': 'I'},
            'P04': {'title': 'Hard Problem', 'part': 'I'},
            'P05': {'title': 'Soul Observer', 'part': 'II'},
            'P06': {'title': 'Physics of Principalities', 'part': 'II'},
            'P07': {'title': 'Grace Function', 'part': 'II'},
            'P08': {'title': 'Stretched Heavens', 'part': 'II'},
            'P09': {'title': 'Moral Universe', 'part': 'III'},
            'P10': {'title': 'Creatio ex Silico', 'part': 'III'},
            'P11': {'title': 'Protocols Validation', 'part': 'III'},
            'P12': {'title': 'Decalogue Cosmos', 'part': 'IV'},
        }
    
    def parse_semantic_blocks(self, content: str, file_path: str) -> List[dict]:
        """Extract semantic blocks from note content"""
        blocks = []
        
        # Pattern 1: %%semantic JSON blocks
        json_pattern = r'%%semantic\s*\n({.*?})\s*\n%%'
        for match in re.finditer(json_pattern, content, re.DOTALL):
            try:
                data = json.loads(match.group(1))
                if 'classifications' in data:
                    for cls in data['classifications']:
                        blocks.append({
                            'content': cls.get('content', ''),
                            'type': cls.get('type', 'unknown'),
                            'file': file_path
                        })
            except json.JSONDecodeError:
                pass
        
        # Pattern 2: Inline ==TYPE:subtype:ref:uuid== markers
        inline_pattern = r'==(\w+):(\w+):([^:]+):([^=]+)==\s*([^=]*)==?'
        for match in re.finditer(inline_pattern, content):
            blocks.append({
                'block_type': match.group(1),
                'semantic_type': match.group(2),
                'ref_id': match.group(3),
                'uuid': match.group(4),
                'content': match.group(5).strip(),
                'file': file_path
            })
        
        # Pattern 3: YAML frontmatter extraction
        yaml_pattern = r'^---\s*\n(.*?)\n---'
        yaml_match = re.match(yaml_pattern, content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
            
            # Extract title
            title_match = re.search(r'title:\s*["\']?([^"\'\n]+)', yaml_content)
            if title_match:
                blocks.append({
                    'type': 'title',
                    'content': title_match.group(1).strip(),
                    'file': file_path
                })
            
            # Extract tags
            tags_match = re.search(r'tags:\s*\n((?:\s*-\s*.+\n)+)', yaml_content)
            if tags_match:
                tags = re.findall(r'-\s*(.+)', tags_match.group(1))
                for tag in tags:
                    blocks.append({
                        'type': 'tag',
                        'content': tag.strip(),
                        'file': file_path
                    })
        
        return blocks
    
    def extract_relationships(self, content: str, file_path: str) -> List[Tuple[str, str, str]]:
        """Extract relationships from wikilinks and cross-references"""
        relationships = []
        source_name = Path(file_path).stem
        
        # Wikilinks: [[Target]] or [[Target|Alias]]
        wikilink_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        for match in re.finditer(wikilink_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'links_to'))
        
        # Paper references: P01, P02, etc.
        paper_ref_pattern = r'\b(P(?:0[1-9]|1[0-2]))\b'
        for match in re.finditer(paper_ref_pattern, content):
            target = match.group(1)
            if target != source_name[:3]:  # Don't self-reference
                relationships.append((source_name, target, 'references'))
        
        # Law references: Law I, Law V, etc.
        law_pattern = r'\bLaw\s+([IVX]+)\b'
        for match in re.finditer(law_pattern, content):
            target = f"Law_{match.group(1)}"
            relationships.append((source_name, target, 'invokes'))
        
        # Cross-references in semantic markup
        crossref_pattern = r'==sent:cross-ref:([^:]+):'
        for match in re.finditer(crossref_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'cross_refs'))
        
        # Evidence-for relationships
        evidence_pattern = r'==\w+:evidence:([^:]+):'
        for match in re.finditer(evidence_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'supports'))
        
        return relationships
    
    def scan_folder(self, folder: str) -> None:
        """Scan a specific folder for semantic markup"""
        search_path = Path(folder) if Path(folder).is_absolute() else self.vault_path / folder
        
        if not search_path.exists():
            print(f"Warning: Path does not exist: {search_path}")
            return
        
        for md_file in search_path.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                file_path = str(md_file)
                file_name = md_file.stem
                
                # Check if this is a paper file
                paper_match = re.search(r'P(0[1-9]|1[0-2])', file_name)
                if paper_match:
                    paper_id = f"P{paper_match.group(1)}"
                    if paper_id in self.paper_structure:
                        self.papers[paper_id] = {
                            'title': self.paper_structure[paper_id]['title'],
                            'part': self.paper_structure[paper_id]['part'],
                            'file': file_path,
                            'concepts': [],
                            'refs': []
                        }
                
                # Parse semantic blocks
                blocks = self.parse_semantic_blocks(content, file_path)
                for block in blocks:
                    node_id = block.get('ref_id') or block.get('content', '')[:30]
                    if node_id:
                        self.nodes[node_id] = {
                            'label': block.get('content', node_id)[:50],
                            'type': block.get('semantic_type') or block.get('type', 'unknown'),
                            'file': file_path
                        }
                
                # Extract relationships
                relationships = self.extract_relationships(content, file_path)
                self.edges.extend(relationships)
                
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
    
    def generate_paper_hierarchy_graph(self) -> str:
        """Generate a Mermaid graph showing paper structure and connections"""
        
        lines = ["flowchart TD"]
        lines.append("")
        lines.append("    %% Style definitions")
        lines.append("    classDef partI fill:#ff6b6b,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef partII fill:#4ecdc4,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef partIII fill:#45b7d1,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef partIV fill:#6c5ce7,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef partV fill:#00b894,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("")
        
        # Subgraphs for each Part
        parts = {
            'I': {'title': 'THE CRISIS', 'papers': []},
            'II': {'title': 'THE FRAMEWORK', 'papers': []},
            'III': {'title': 'EVIDENCE & FALSIFIABILITY', 'papers': []},
            'IV': {'title': 'IDENTIFICATION', 'papers': []},
            'V': {'title': 'IMPLICATIONS', 'papers': []},
        }
        
        for paper_id, info in self.paper_structure.items():
            part = info['part']
            if part in parts:
                parts[part]['papers'].append((paper_id, info['title']))
        
        # Generate subgraphs
        for part_num, part_info in parts.items():
            if part_info['papers']:
                lines.append(f"    subgraph PART_{part_num}[\"Part {part_num}: {part_info['title']}\"]")
                for paper_id, title in part_info['papers']:
                    safe_id = paper_id.replace('-', '_')
                    lines.append(f'        {safe_id}["{paper_id}: {title}"]')
                lines.append("    end")
                lines.append("")
        
        # Add inter-paper relationships
        lines.append("    %% Paper Dependencies")
        
        # Define logical flow
        dependencies = [
            ('P01', 'P02', 'establishes'),
            ('P02', 'P03', 'extends'),
            ('P03', 'P04', 'leads to'),
            ('P04', 'P05', 'requires'),
            ('P05', 'P06', 'reveals'),
            ('P06', 'P07', 'necessitates'),
            ('P07', 'P08', 'explains'),
            ('P08', 'P09', 'grounds'),
            ('P09', 'P10', 'applies to'),
            ('P10', 'P11', 'tested by'),
            ('P11', 'P12', 'validates'),
            # Cross-part connections
            ('P02', 'P07', 'von Neumann → Grace'),
            ('P05', 'P09', 'Soul → Moral'),
            ('P07', 'P08', 'Grace → Dark Energy'),
            ('P01', 'P12', 'Logos → Decalogue'),
        ]
        
        for source, target, label in dependencies:
            lines.append(f'    {source} -->|"{label}"| {target}')
        
        lines.append("")
        lines.append("    %% Apply part styles")
        for paper_id, info in self.paper_structure.items():
            part = info['part']
            lines.append(f"    class {paper_id} part{part}")
        
        return '\n'.join(lines)
    
    def generate_concept_graph(self, 
                               filter_types: List[str] = None,
                               max_nodes: int = 50) -> str:
        """Generate Mermaid diagram of concepts and relationships"""
        
        # Filter nodes if specified
        filtered_nodes = self.nodes
        if filter_types:
            filtered_nodes = {
                k: v for k, v in self.nodes.items() 
                if v['type'] in filter_types
            }
        
        # Limit nodes
        if len(filtered_nodes) > max_nodes:
            filtered_nodes = dict(list(filtered_nodes.items())[:max_nodes])
        
        lines = ["flowchart LR"]
        lines.append("")
        lines.append("    %% Style definitions")
        for sem_type, color in self.type_colors.items():
            lines.append(f"    classDef {sem_type} fill:{color},stroke:#333,stroke-width:2px")
        
        lines.append("")
        lines.append("    %% Nodes")
        
        node_ids = set()
        for node_id, node_data in filtered_nodes.items():
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)[:20]
            label = node_data['label'].replace('"', "'")[:40]
            sem_type = node_data['type']
            
            # Different shapes for different types
            if sem_type in ['axiom', 'law']:
                lines.append(f'    {safe_id}["{label}"]')
            elif sem_type in ['hypothesis', 'claim']:
                lines.append(f'    {safe_id}("{label}")')
            elif sem_type in ['evidence']:
                lines.append(f'    {safe_id}[/"{label}"/]')
            elif sem_type in ['equation', 'variable']:
                lines.append(f'    {safe_id}{{"{label}"}}')
            else:
                lines.append(f'    {safe_id}["{label}"]')
            
            node_ids.add(safe_id)
        
        lines.append("")
        lines.append("    %% Relationships")
        
        for source, target, rel_type in self.edges:
            safe_source = re.sub(r'[^a-zA-Z0-9_]', '_', source)[:20]
            safe_target = re.sub(r'[^a-zA-Z0-9_]', '_', target)[:20]
            
            if safe_source in node_ids or safe_target in node_ids:
                if rel_type == 'supports':
                    lines.append(f'    {safe_source} -->|supports| {safe_target}')
                elif rel_type == 'references':
                    lines.append(f'    {safe_source} -.->|refs| {safe_target}')
                elif rel_type == 'invokes':
                    lines.append(f'    {safe_source} ==>|invokes| {safe_target}')
                else:
                    lines.append(f'    {safe_source} --> {safe_target}')
        
        lines.append("")
        lines.append("    %% Apply styles")
        for node_id, node_data in filtered_nodes.items():
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)[:20]
            sem_type = node_data['type']
            if sem_type in self.type_colors:
                lines.append(f'    class {safe_id} {sem_type}')
        
        return '\n'.join(lines)
    
    def generate_thesis_structure_graph(self) -> str:
        """Generate the master thesis structure showing Parts → Papers → Key Concepts"""
        
        lines = ["flowchart TB"]
        lines.append("")
        lines.append("    %% Master Thesis Structure")
        lines.append("    classDef thesis fill:#2d3436,stroke:#fff,stroke-width:3px,color:#fff")
        lines.append("    classDef crisis fill:#d63031,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef framework fill:#0984e3,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef evidence fill:#00b894,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef identity fill:#6c5ce7,stroke:#333,stroke-width:2px,color:#fff")
        lines.append("    classDef implication fill:#fdcb6e,stroke:#333,stroke-width:2px,color:#000")
        lines.append("")
        
        lines.append('    THESIS["THE LOGOS THESIS"]')
        lines.append("")
        
        # Part I: Crisis
        lines.append("    subgraph PART_I[\"PART I: THE CRISIS\"]")
        lines.append('        I1["Compression Crisis<br/>10^120 Problem"]')
        lines.append('        I2["Measurement Boundary<br/>Von Neumann Chain"]')
        lines.append('        I3["Consciousness Problem<br/>Hard Problem"]')
        lines.append("    end")
        lines.append("")
        
        # Part II: Framework
        lines.append("    subgraph PART_II[\"PART II: THE FRAMEWORK\"]")
        lines.append('        II1["χ-Field Formalization<br/>Master Equation"]')
        lines.append('        II2["GR/QM Unification<br/>Coherence Limits"]')
        lines.append('        II3["Moral Physics<br/>Decoherence"]')
        lines.append('        II4["Dark Energy<br/>W_Ĝ = Λ"]')
        lines.append("    end")
        lines.append("")
        
        # Part III: Evidence
        lines.append("    subgraph PART_III[\"PART III: EVIDENCE\"]")
        lines.append('        III1["PEAR/GCP Data<br/>6σ Anomalies"]')
        lines.append('        III2["ODCR Prediction<br/>Testable"]')
        lines.append('        III3["Kill-Criteria<br/>Falsifiable"]')
        lines.append("    end")
        lines.append("")
        
        # Part IV: Identification
        lines.append("    subgraph PART_IV[\"PART IV: IDENTIFICATION\"]")
        lines.append('        IV1["Triadic Necessity<br/>Non-Commutative"]')
        lines.append('        IV2["Competing Ontologies<br/>Fail Constraints"]')
        lines.append('        IV3["Trinity Isomorphism<br/>Minimal Solution"]')
        lines.append("    end")
        lines.append("")
        
        # Part V: Implications
        lines.append("    subgraph PART_V[\"PART V: IMPLICATIONS\"]")
        lines.append('        V1["Physics Reframed<br/>Information Primary"]')
        lines.append('        V2["Ethics = Coherence<br/>Dynamics"]')
        lines.append('        V3["AI Substrate<br/>Independence"]')
        lines.append("    end")
        lines.append("")
        
        # Connections
        lines.append("    %% Main Flow")
        lines.append("    THESIS --> PART_I")
        lines.append("    PART_I --> PART_II")
        lines.append("    PART_II --> PART_III")
        lines.append("    PART_III --> PART_IV")
        lines.append("    PART_IV --> PART_V")
        lines.append("")
        
        lines.append("    %% Internal Connections")
        lines.append("    I1 --> II1")
        lines.append("    I2 --> II2")
        lines.append("    I3 --> II3")
        lines.append("    II4 --> III1")
        lines.append("    III2 --> III3")
        lines.append("    III3 --> IV1")
        lines.append("    IV1 --> IV2")
        lines.append("    IV2 --> IV3")
        lines.append("    IV3 --> V1")
        lines.append("")
        
        lines.append("    %% Apply styles")
        lines.append("    class THESIS thesis")
        lines.append("    class I1,I2,I3 crisis")
        lines.append("    class II1,II2,II3,II4 framework")
        lines.append("    class III1,III2,III3 evidence")
        lines.append("    class IV1,IV2,IV3 identity")
        lines.append("    class V1,V2,V3 implication")
        
        return '\n'.join(lines)
    
    def save_graph_to_note(self, 
                          output_path: str, 
                          graph_type: str = 'thesis_structure',
                          title: str = "Logos Thesis Structure") -> None:
        """Save generated graph as an Obsidian note"""
        
        if graph_type == 'thesis_structure':
            mermaid_code = self.generate_thesis_structure_graph()
        elif graph_type == 'paper_hierarchy':
            mermaid_code = self.generate_paper_hierarchy_graph()
        elif graph_type == 'concepts':
            mermaid_code = self.generate_concept_graph()
        else:
            mermaid_code = self.generate_thesis_structure_graph()
        
        content = f"""---
title: {title}
type: visualization
generated: true
date: 2025-12-14
---

# {title}

```mermaid
{mermaid_code}
```

## Legend

| Color | Meaning |
|-------|---------|
| 🔴 Red | Part I: The Crisis |
| 🔵 Blue | Part II: The Framework |
| 🟢 Green | Part III: Evidence |
| 🟣 Purple | Part IV: Identification |
| 🟡 Yellow | Part V: Implications |

## Statistics

- **Papers:** {len(self.paper_structure)}
- **Semantic Nodes:** {len(self.nodes)}
- **Relationships:** {len(self.edges)}

---

*Generated by SemanticMermaidGenerator*
"""
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(content, encoding='utf-8')
        print(f"[OK] Saved graph to {output_path}")
    
    def get_stats(self) -> dict:
        """Return statistics about scanned content"""
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'total_papers': len(self.papers),
            'node_types': dict(defaultdict(int, {
                n['type']: sum(1 for x in self.nodes.values() if x['type'] == n['type'])
                for n in self.nodes.values()
            }))
        }


def generate_logos_maps(vault_path: str, logos_folder: str, output_folder: str):
    """Convenience function to generate all Logos thesis maps"""
    
    generator = SemanticMermaidGenerator(vault_path)
    
    print("Scanning Logos folder...")
    generator.scan_folder(logos_folder)
    
    stats = generator.get_stats()
    print(f"Found: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    
    # Generate thesis structure
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    generator.save_graph_to_note(
        str(output_path / "LOGOS_THESIS_STRUCTURE_MAP.md"),
        graph_type='thesis_structure',
        title="Logos Thesis Structure"
    )
    
    generator.save_graph_to_note(
        str(output_path / "LOGOS_PAPER_HIERARCHY_MAP.md"),
        graph_type='paper_hierarchy',
        title="Logos Papers Hierarchy"
    )
    
    print("\n[OK] All maps generated!")
    return generator


if __name__ == "__main__":
    # Default paths
    vault_path = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    logos_folder = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC\2.5_Drafting\Logos"
    output_folder = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC\00_VAULT_SYSTEM\Generated"
    
    generate_logos_maps(vault_path, logos_folder, output_folder)
