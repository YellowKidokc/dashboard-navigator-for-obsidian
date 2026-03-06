"""
Dependency Graph Generator
Creates visual dependency graphs showing axiom relationships
Outputs: PNG image, DOT file, and interactive HTML
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

class DependencyGraphGenerator:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.axioms = {}
        self.graph_data = defaultdict(list)
        
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
                        'chain_position': metadata.get('chain_position', 999),
                        'classification': str(metadata.get('classification', '')),
                        'status': metadata.get('status', ''),
                        'depends_on': metadata.get('depends_on', []) or [],
                        'stage': metadata.get('stage', 0)
                    }
            except Exception as e:
                print(f"Error loading {filepath.name}: {e}")
        
        print(f"✓ Loaded {len(self.axioms)} axioms\n")
    
    def build_graph(self):
        """Build dependency graph structure"""
        print("Building dependency graph...")
        
        for axiom_id, data in self.axioms.items():
            depends_on = data['depends_on']
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                if dep and dep in self.axioms:
                    self.graph_data[dep].append(axiom_id)
        
        print(f"✓ Built graph with {len(self.graph_data)} nodes\n")
    
    def get_node_color(self, classification, status):
        """Get color based on axiom type"""
        if 'Primitive' in classification or status == 'primitive':
            return '#90EE90'  # Light green
        elif 'Definition' in classification or status == 'definition':
            return '#87CEEB'  # Sky blue
        elif 'Theorem' in classification or status == 'theorem':
            return '#FFB6C1'  # Light pink
        elif status == 'equation':
            return '#FFD700'  # Gold
        elif status == 'property':
            return '#DDA0DD'  # Plum
        elif status == 'boundary':
            return '#FF6347'  # Tomato
        else:
            return '#D3D3D3'  # Light gray
    
    def generate_dot_file(self, output_file):
        """Generate Graphviz DOT file"""
        print("Generating DOT file...")
        
        lines = ['digraph AxiomDependencies {']
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style=filled, fontname="Arial"];')
        lines.append('    edge [color="#666666"];')
        lines.append('')
        
        # Add nodes
        for axiom_id, data in sorted(self.axioms.items(), key=lambda x: x[1]['chain_position']):
            color = self.get_node_color(data['classification'], data['status'])
            label = f"{axiom_id}\\n(pos {data['chain_position']})"
            lines.append(f'    "{axiom_id}" [label="{label}", fillcolor="{color}"];')
        
        lines.append('')
        
        # Add edges
        for source, targets in sorted(self.graph_data.items()):
            for target in targets:
                lines.append(f'    "{source}" -> "{target}";')
        
        lines.append('}')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✓ DOT file saved: {output_file}\n")
    
    def generate_html_interactive(self, output_file):
        """Generate interactive HTML visualization using vis.js"""
        print("Generating interactive HTML...")
        
        # Build nodes and edges for vis.js
        nodes = []
        edges = []
        
        for axiom_id, data in self.axioms.items():
            color = self.get_node_color(data['classification'], data['status'])
            nodes.append({
                'id': axiom_id,
                'label': axiom_id,
                'title': f"Position: {data['chain_position']}<br>Status: {data['status']}<br>Stage: {data['stage']}",
                'color': color,
                'level': data['stage']
            })
        
        for source, targets in self.graph_data.items():
            for target in targets:
                edges.append({
                    'from': source,
                    'to': target,
                    'arrows': 'to'
                })
        
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Theophysics Axiom Dependency Graph</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            background: white;
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .legend {{
            margin: 20px 0;
            padding: 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border: 1px solid #999;
        }}
    </style>
</head>
<body>
    <h1>Theophysics Axiom Dependency Graph (001-188)</h1>
    
    <div class="legend">
        <div class="legend-item"><span class="legend-color" style="background: #90EE90;"></span> Primitive</div>
        <div class="legend-item"><span class="legend-color" style="background: #87CEEB;"></span> Definition</div>
        <div class="legend-item"><span class="legend-color" style="background: #FFB6C1;"></span> Theorem</div>
        <div class="legend-item"><span class="legend-color" style="background: #FFD700;"></span> Equation</div>
        <div class="legend-item"><span class="legend-color" style="background: #DDA0DD;"></span> Property</div>
        <div class="legend-item"><span class="legend-color" style="background: #FF6347;"></span> Boundary</div>
    </div>
    
    <div id="mynetwork"></div>
    
    <script type="text/javascript">
        var nodes = new vis.DataSet({nodes});
        var edges = new vis.DataSet({edges});
        
        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};
        
        var options = {{
            layout: {{
                hierarchical: {{
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 150,
                    nodeSpacing: 100
                }}
            }},
            physics: {{
                enabled: false
            }},
            nodes: {{
                shape: 'box',
                margin: 10,
                widthConstraint: {{
                    maximum: 150
                }}
            }},
            edges: {{
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                color: {{
                    color: '#666666',
                    highlight: '#FF0000'
                }},
                smooth: {{
                    type: 'cubicBezier'
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                zoomView: true,
                dragView: true
            }}
        }};
        
        var network = new vis.Network(container, data, options);
        
        network.on("selectNode", function(params) {{
            console.log("Selected node:", params.nodes[0]);
        }});
    </script>
</body>
</html>"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)
        
        print(f"✓ Interactive HTML saved: {output_file}\n")
    
    def generate_statistics(self):
        """Generate graph statistics"""
        print("=" * 80)
        print("DEPENDENCY GRAPH STATISTICS")
        print("=" * 80)
        
        # Count nodes by type
        type_counts = defaultdict(int)
        for data in self.axioms.values():
            type_counts[data['status']] += 1
        
        print(f"\nTotal Axioms: {len(self.axioms)}")
        print(f"Total Dependencies: {sum(len(targets) for targets in self.graph_data.values())}")
        print(f"\nAxioms by Type:")
        for axiom_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {axiom_type}: {count}")
        
        # Find root nodes (no dependencies)
        roots = [aid for aid, data in self.axioms.items() if not data['depends_on']]
        print(f"\nRoot Axioms (no dependencies): {len(roots)}")
        for root in sorted(roots)[:10]:
            print(f"  - {root}")
        
        # Find leaf nodes (nothing depends on them)
        referenced = set()
        for targets in self.graph_data.values():
            referenced.update(targets)
        leaves = [aid for aid in self.axioms if aid not in referenced]
        print(f"\nLeaf Axioms (nothing depends on them): {len(leaves)}")
        for leaf in sorted(leaves)[:10]:
            print(f"  - {leaf}")
        
        print("\n" + "=" * 80)

def main():
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    output_dir = r"O:\Theophysics_Backend\Python_Backend"
    
    print("=" * 80)
    print("DEPENDENCY GRAPH GENERATOR")
    print("=" * 80)
    print(f"\nSource: {axioms_folder}\n")
    
    generator = DependencyGraphGenerator(axioms_folder)
    generator.load_axioms()
    generator.build_graph()
    
    # Generate outputs
    dot_file = os.path.join(output_dir, "axiom_dependencies.dot")
    html_file = os.path.join(output_dir, "axiom_dependencies.html")
    
    generator.generate_dot_file(dot_file)
    generator.generate_html_interactive(html_file)
    generator.generate_statistics()
    
    print(f"\n✓ Graph files generated:")
    print(f"  - DOT: {dot_file}")
    print(f"  - HTML: {html_file}")
    print(f"\nOpen the HTML file in your browser to explore the interactive graph!")

if __name__ == "__main__":
    main()
