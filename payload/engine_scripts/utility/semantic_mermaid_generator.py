"""
SEMANTIC TO MERMAID GRAPH GENERATOR
====================================
Parses semantic markup blocks from Obsidian notes and generates
Mermaid relationship graphs.

Author: David Lowe & Claude
Date: 2025-12-14
"""

import re
import json
from pathlib import Path
import os
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class SemanticMermaidGenerator:
    """Generates Mermaid graphs from semantic markup in Obsidian notes"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.nodes: Dict[str, dict] = {}  # id -> {label, type, file}
        self.edges: List[Tuple[str, str, str]] = []  # (from, to, label)

        # Color scheme for different semantic types
        self.type_colors = {
            'axiom': '#ff6b6b',      # Red
            'hypothesis': '#4ecdc4',  # Teal
            'evidence': '#45b7d1',    # Blue
            'theorem': '#96ceb4',     # Green
            'claim': '#ffeaa7',       # Yellow
            'definition': '#dfe6e9',  # Gray
            'variable': '#a29bfe',    # Purple
            'equation': '#fd79a8',    # Pink
            'law': '#00b894',         # Emerald
            'bridge': '#e17055',      # Orange
            'objection': '#d63031',   # Dark red
            'response': '#00cec9',    # Cyan
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

        # Pattern 3: YAML frontmatter tags
        yaml_pattern = r'^---\s*\n(.*?)\n---'
        yaml_match = re.match(yaml_pattern, content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)
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

        # Wikilinks: [[Target]] or [[Target|Alias]]
        wikilink_pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
        source_name = Path(file_path).stem

        for match in re.finditer(wikilink_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'links_to'))

        # Cross-references in semantic markup
        crossref_pattern = r'==sent:cross-ref:([^:]+):'
        for match in re.finditer(crossref_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'references'))

        # Evidence-for relationships
        evidence_pattern = r'==\w+:evidence:([^:]+):'
        for match in re.finditer(evidence_pattern, content):
            target = match.group(1)
            relationships.append((source_name, target, 'supports'))

        return relationships

    def scan_vault(self, folder: str = None) -> None:
        """Scan vault for semantic markup"""
        search_path = self.vault_path / folder if folder else self.vault_path

        for md_file in search_path.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                file_path = str(md_file.relative_to(self.vault_path))

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

    def generate_mermaid(self,
                         graph_type: str = 'flowchart',
                         direction: str = 'TD',
                         max_nodes: int = 50,
                         filter_types: List[str] = None) -> str:
        """Generate Mermaid diagram from collected data"""

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

        lines = [f"{graph_type} {direction}"]

        # Add style definitions
        lines.append("")
        lines.append("    %% Style definitions")
        for sem_type, color in self.type_colors.items():
            lines.append(f"    classDef {sem_type} fill:{color},stroke:#333,stroke-width:2px")

        lines.append("")
        lines.append("    %% Nodes")

        # Add nodes
        node_ids = set()
        for node_id, node_data in filtered_nodes.items():
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
            label = node_data['label'].replace('"', "'")
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

        # Add edges
        for source, target, rel_type in self.edges:
            safe_source = re.sub(r'[^a-zA-Z0-9_]', '_', source)
            safe_target = re.sub(r'[^a-zA-Z0-9_]', '_', target)

            # Only include edges where both nodes exist
            if safe_source in node_ids or safe_target in node_ids:
                if rel_type == 'supports':
                    lines.append(f'    {safe_source} -->|supports| {safe_target}')
                elif rel_type == 'references':
                    lines.append(f'    {safe_source} -.->|refs| {safe_target}')
                else:
                    lines.append(f'    {safe_source} --> {safe_target}')

        lines.append("")
        lines.append("    %% Apply styles")
        for node_id, node_data in filtered_nodes.items():
            safe_id = re.sub(r'[^a-zA-Z0-9_]', '_', node_id)
            sem_type = node_data['type']
            if sem_type in self.type_colors:
                lines.append(f'    class {safe_id} {sem_type}')

        return '\n'.join(lines)

    def generate_relationship_graph(self,
                                    center_node: str = None,
                                    depth: int = 2) -> str:
        """Generate a focused relationship graph around a central concept"""

        if not center_node:
            # Use most connected node as center
            connection_counts = defaultdict(int)
            for source, target, _ in self.edges:
                connection_counts[source] += 1
                connection_counts[target] += 1
            center_node = max(connection_counts, key=connection_counts.get) if connection_counts else None

        if not center_node:
            return "flowchart TD\n    empty[No relationships found]"

        # BFS to find connected nodes within depth
        visited = {center_node}
        frontier = {center_node}

        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                for source, target, _ in self.edges:
                    if source == node and target not in visited:
                        new_frontier.add(target)
                        visited.add(target)
                    elif target == node and source not in visited:
                        new_frontier.add(source)
                        visited.add(source)
            frontier = new_frontier

        # Generate subgraph
        lines = ["flowchart LR"]
        lines.append(f'    center["{center_node}"]')
        lines.append('    style center fill:#ff6b6b,stroke:#333,stroke-width:4px')

        for source, target, rel_type in self.edges:
            if source in visited and target in visited:
                safe_source = re.sub(r'[^a-zA-Z0-9_]', '_', source)
                safe_target = re.sub(r'[^a-zA-Z0-9_]', '_', target)
                lines.append(f'    {safe_source} --> {safe_target}')

        return '\n'.join(lines)

    def save_mermaid_note(self, output_path: str, title: str = "Semantic Graph"):
        """Save Mermaid graph as an Obsidian note"""

        mermaid_code = self.generate_mermaid()

        content = f"""---
title: {title}
type: visualization
generated: true
---

# {title}

## Full Concept Network

```mermaid
{mermaid_code}
```

## Statistics

- **Total Nodes:** {len(self.nodes)}
- **Total Relationships:** {len(self.edges)}
- **Semantic Types:** {', '.join(set(n['type'] for n in self.nodes.values()))}

## Node Index

| ID | Type | File |
|----|------|------|
"""
        for node_id, node_data in list(self.nodes.items())[:50]:
            content += f"| {node_id[:30]} | {node_data['type']} | {node_data['file'][:40]} |\n"

        Path(output_path).write_text(content, encoding='utf-8')
        print(f"✓ Saved Mermaid graph to {output_path}")


def main():
    """Example usage"""
    vault_path = os.getenv("THEOPHYSICS_VAULT_PATH", r"O:\_Theophysics_v3")

    generator = SemanticMermaidGenerator(vault_path)

    # Scan specific folder
    print("Scanning vault for semantic markup...")
    generator.scan_vault("00_CANONICAL/PAPERS")

    print(f"Found {len(generator.nodes)} semantic nodes")
    print(f"Found {len(generator.edges)} relationships")

    # Generate and save
    output_path = Path(vault_path) / "00_VAULT_SYSTEM" / "Generated" / "SEMANTIC_GRAPH.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generator.save_mermaid_note(str(output_path), "Theophysics Semantic Network")

    # Also print sample mermaid
    print("\n--- Sample Mermaid Output ---")
    print(generator.generate_mermaid(max_nodes=20))


if __name__ == "__main__":
    main()
