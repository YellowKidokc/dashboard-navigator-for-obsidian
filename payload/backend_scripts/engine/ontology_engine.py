# engine/ontology_engine.py

"""
Ontology Engine for concept mapping and relationship building.

Features:
- Build concept graphs
- Track parent/child relationships
- Find related concepts
- Detect ontology conflicts
- Visualize concept networks
"""

from typing import List, Dict, Any, Set, Tuple, Optional
import sqlite3
import json
from collections import defaultdict, deque


class OntologyNode:
    """Represents a concept in the ontology."""
    
    def __init__(self, term: str, classification: str = ""):
        self.term = term
        self.classification = classification
        self.parents: Set[str] = set()
        self.children: Set[str] = set()
        self.related: Set[str] = set()
        self.aliases: List[str] = []
        self.properties: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "classification": self.classification,
            "parents": list(self.parents),
            "children": list(self.children),
            "related": list(self.related),
            "aliases": self.aliases,
            "properties": self.properties
        }


class OntologyEngine:
    """
    Manage concept ontology and relationships.
    """
    
    def __init__(self, settings, db_engine):
        self.settings = settings
        self.db = db_engine
        self.nodes: Dict[str, OntologyNode] = {}
    
    def build_ontology_from_definitions(self):
        """
        Build ontology graph from all definitions in database.
        Extracts relationships from:
        - Wiki-links in definitions
        - Classification hierarchies
        - Explicit relationship markers
        """
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        
        c.execute("SELECT term, body, classification, aliases FROM definitions")
        rows = c.fetchall()
        conn.close()
        
        self.nodes.clear()
        
        # First pass: create all nodes
        for term, body, classification, aliases_json in rows:
            node = OntologyNode(term, classification or "")
            
            if aliases_json:
                try:
                    node.aliases = json.loads(aliases_json)
                except:
                    pass
            
            self.nodes[term.lower()] = node
        
        # Second pass: extract relationships
        for term, body, classification, _ in rows:
            if not body:
                continue
            
            node = self.nodes[term.lower()]
            
            # Extract wiki-links as related concepts
            import re
            links = re.findall(r'\[\[(.+?)\]\]', body)
            for link in links:
                link_term = link.split('|')[0].strip()
                if link_term.lower() in self.nodes:
                    node.related.add(link_term)
            
            # Look for explicit relationship markers
            # "is a type of", "is an instance of", "belongs to"
            parent_patterns = [
                r'(?:is\s+a\s+(?:type|kind|form)\s+of)\s+\[\[(.+?)\]\]',
                r'(?:is\s+an?\s+instance\s+of)\s+\[\[(.+?)\]\]',
                r'(?:belongs\s+to)\s+\[\[(.+?)\]\]'
            ]
            
            for pattern in parent_patterns:
                matches = re.findall(pattern, body, re.IGNORECASE)
                for match in matches:
                    parent_term = match.split('|')[0].strip()
                    if parent_term.lower() in self.nodes:
                        node.parents.add(parent_term)
                        self.nodes[parent_term.lower()].children.add(term)
        
        # Build classification hierarchy
        self._build_classification_hierarchy()
    
    def _build_classification_hierarchy(self):
        """Build parent-child relationships based on classification."""
        # Group by classification
        by_class: Dict[str, List[str]] = defaultdict(list)
        for term, node in self.nodes.items():
            if node.classification:
                by_class[node.classification].append(term)
        
        # For each classification, create virtual parent nodes if needed
        # This helps organize concepts by type
        for classification, terms in by_class.items():
            # If there are multiple terms of same classification,
            # they're siblings (related)
            if len(terms) > 1:
                for i, term1 in enumerate(terms):
                    for term2 in terms[i+1:]:
                        self.nodes[term1].related.add(self.nodes[term2].term)
                        self.nodes[term2].related.add(self.nodes[term1].term)
    
    def get_node(self, term: str) -> Optional[OntologyNode]:
        """Get a node by term name."""
        return self.nodes.get(term.lower())
    
    def get_ancestors(self, term: str, max_depth: int = 10) -> List[str]:
        """Get all ancestor concepts (parents, grandparents, etc.)."""
        node = self.get_node(term)
        if not node:
            return []
        
        ancestors = []
        visited = set()
        queue = deque([(term, 0)])
        
        while queue:
            current_term, depth = queue.popleft()
            
            if depth >= max_depth or current_term in visited:
                continue
            
            visited.add(current_term)
            current_node = self.get_node(current_term)
            
            if current_node and current_node.parents:
                for parent in current_node.parents:
                    if parent not in visited:
                        ancestors.append(parent)
                        queue.append((parent, depth + 1))
        
        return ancestors
    
    def get_descendants(self, term: str, max_depth: int = 10) -> List[str]:
        """Get all descendant concepts (children, grandchildren, etc.)."""
        node = self.get_node(term)
        if not node:
            return []
        
        descendants = []
        visited = set()
        queue = deque([(term, 0)])
        
        while queue:
            current_term, depth = queue.popleft()
            
            if depth >= max_depth or current_term in visited:
                continue
            
            visited.add(current_term)
            current_node = self.get_node(current_term)
            
            if current_node and current_node.children:
                for child in current_node.children:
                    if child not in visited:
                        descendants.append(child)
                        queue.append((child, depth + 1))
        
        return descendants
    
    def find_shortest_path(self, term1: str, term2: str) -> Optional[List[str]]:
        """Find shortest path between two concepts."""
        node1 = self.get_node(term1)
        node2 = self.get_node(term2)
        
        if not node1 or not node2:
            return None
        
        if term1.lower() == term2.lower():
            return [term1]
        
        # BFS to find shortest path
        queue = deque([(term1.lower(), [term1])])
        visited = {term1.lower()}
        
        while queue:
            current, path = queue.popleft()
            current_node = self.get_node(current)
            
            if not current_node:
                continue
            
            # Check all connected nodes
            connected = (
                current_node.parents | 
                current_node.children | 
                current_node.related
            )
            
            for next_term in connected:
                next_key = next_term.lower()
                
                if next_key == term2.lower():
                    return path + [next_term]
                
                if next_key not in visited:
                    visited.add(next_key)
                    queue.append((next_key, path + [next_term]))
        
        return None
    
    def get_concept_cluster(self, term: str, radius: int = 2) -> Dict[str, Any]:
        """
        Get all concepts within 'radius' hops of a term.
        Returns cluster with relationship types.
        """
        node = self.get_node(term)
        if not node:
            return {"center": term, "nodes": [], "edges": []}
        
        nodes_in_cluster = {term.lower()}
        edges = []
        
        # BFS with depth limit
        queue = deque([(term.lower(), 0)])
        visited = {term.lower()}
        
        while queue:
            current, depth = queue.popleft()
            
            if depth >= radius:
                continue
            
            current_node = self.get_node(current)
            if not current_node:
                continue
            
            # Add edges for parents
            for parent in current_node.parents:
                parent_key = parent.lower()
                edges.append({
                    "from": current,
                    "to": parent_key,
                    "type": "parent"
                })
                if parent_key not in visited:
                    visited.add(parent_key)
                    nodes_in_cluster.add(parent_key)
                    queue.append((parent_key, depth + 1))
            
            # Add edges for children
            for child in current_node.children:
                child_key = child.lower()
                edges.append({
                    "from": current,
                    "to": child_key,
                    "type": "child"
                })
                if child_key not in visited:
                    visited.add(child_key)
                    nodes_in_cluster.add(child_key)
                    queue.append((child_key, depth + 1))
            
            # Add edges for related
            for related in current_node.related:
                related_key = related.lower()
                edges.append({
                    "from": current,
                    "to": related_key,
                    "type": "related"
                })
                if related_key not in visited:
                    visited.add(related_key)
                    nodes_in_cluster.add(related_key)
                    queue.append((related_key, depth + 1))
        
        # Get node details
        nodes = []
        for term_key in nodes_in_cluster:
            node = self.get_node(term_key)
            if node:
                nodes.append(node.to_dict())
        
        return {
            "center": term,
            "nodes": nodes,
            "edges": edges,
            "size": len(nodes)
        }
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect circular relationships (usually errors)."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(term: str, path: List[str]) -> bool:
            """DFS to detect cycles."""
            if term in rec_stack:
                # Found a cycle
                cycle_start = path.index(term)
                cycles.append(path[cycle_start:] + [term])
                return True
            
            if term in visited:
                return False
            
            visited.add(term)
            rec_stack.add(term)
            path.append(term)
            
            node = self.get_node(term)
            if node:
                for parent in node.parents:
                    dfs(parent.lower(), path.copy())
            
            rec_stack.remove(term)
            return False
        
        for term in self.nodes:
            if term not in visited:
                dfs(term, [])
        
        return cycles
    
    def get_ontology_statistics(self) -> Dict[str, Any]:
        """Get statistics about the ontology."""
        total_nodes = len(self.nodes)
        
        nodes_with_parents = sum(1 for n in self.nodes.values() if n.parents)
        nodes_with_children = sum(1 for n in self.nodes.values() if n.children)
        nodes_with_related = sum(1 for n in self.nodes.values() if n.related)
        
        total_relationships = sum(
            len(n.parents) + len(n.children) + len(n.related)
            for n in self.nodes.values()
        )
        
        classifications = defaultdict(int)
        for node in self.nodes.values():
            if node.classification:
                classifications[node.classification] += 1
        
        return {
            "total_concepts": total_nodes,
            "nodes_with_parents": nodes_with_parents,
            "nodes_with_children": nodes_with_children,
            "nodes_with_related": nodes_with_related,
            "total_relationships": total_relationships,
            "avg_relationships_per_node": total_relationships / total_nodes if total_nodes > 0 else 0,
            "classifications": dict(classifications),
            "cycles_detected": len(self.detect_cycles())
        }
    
    def export_to_graph_format(self, format: str = "json") -> str:
        """
        Export ontology to graph visualization format.
        Supports: json, graphviz, cytoscape
        """
        if format == "json":
            graph = {
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": []
            }
            
            for node in self.nodes.values():
                for parent in node.parents:
                    graph["edges"].append({
                        "source": node.term,
                        "target": parent,
                        "type": "parent"
                    })
                for child in node.children:
                    graph["edges"].append({
                        "source": node.term,
                        "target": child,
                        "type": "child"
                    })
                for related in node.related:
                    graph["edges"].append({
                        "source": node.term,
                        "target": related,
                        "type": "related"
                    })
            
            return json.dumps(graph, indent=2)
        
        elif format == "graphviz":
            dot = ["digraph Ontology {"]
            dot.append("  rankdir=TB;")
            dot.append("  node [shape=box];")
            
            for node in self.nodes.values():
                label = node.term
                if node.classification:
                    label += f"\\n({node.classification})"
                dot.append(f'  "{node.term}" [label="{label}"];')
            
            for node in self.nodes.values():
                for parent in node.parents:
                    dot.append(f'  "{node.term}" -> "{parent}" [label="is-a"];')
                for related in list(node.related)[:5]:  # Limit for clarity
                    dot.append(f'  "{node.term}" -> "{related}" [style=dashed, label="related"];')
            
            dot.append("}")
            return "\n".join(dot)
        
        return "{}"

