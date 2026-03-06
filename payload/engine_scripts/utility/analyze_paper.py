"""
THEOPHYSICS LOCAL PAPER ANALYZER
Self-contained analysis for individual papers

Run: python analyze_paper.py
Adjust params in config.json, re-run to see changes
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
try:
    import numpy as np
    import matplotlib.pyplot as plt
    import networkx as nx
except ImportError:
    print("WARNING: Some packages not installed. Run: pip install -r requirements.txt")
    np = None
from datetime import datetime

class LocalPaperAnalyzer:
    def __init__(self, config_path='config.json'):
        self.load_config(config_path)
        self.paper_path = self.find_paper_file()
        self.analysis_dir = Path('_LOCAL_ANALYSIS')
        self.analysis_dir.mkdir(exist_ok=True)

        # Data structures
        self.paper_content = None
        self.concepts = Counter()
        self.tags = []
        self.tag_network = defaultdict(list)
        self.breakthroughs = []

    def load_config(self, config_path):
        """Load adjustable parameters from config.json"""
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.params = config['analysis_parameters']
        self.core_concepts = config['core_concepts']
        self.core_tags = config['core_tags']

        print(f"Loaded config with parameters:")
        print(f"  - Integration order min: {self.params['breakthrough_detection']['integration_order_min']}")
        print(f"  - Word proximity window: {self.params['network_analysis']['word_proximity_window']}")

    def find_paper_file(self):
        """Find the main paper markdown file in parent directory"""
        # Check parent directory first
        parent_papers = list(Path('..').glob('Paper*.md'))
        if parent_papers:
            return parent_papers[0]

        # Then check current directory
        candidates = list(Path('.').glob('Paper*.md'))

        if not candidates:
            raise FileNotFoundError("No Paper*.md file found in current or parent directory")

        if len(candidates) > 1:
            print(f"Multiple paper files found, using: {candidates[0]}")

        return candidates[0]

    def analyze_all(self):
        """Run complete analysis pipeline"""
        print("\n" + "="*60)
        print("THEOPHYSICS LOCAL PAPER ANALYSIS")
        print("="*60)

        self.load_paper()
        self.extract_concepts()
        self.extract_tags()
        self.detect_breakthroughs()
        self.analyze_tag_proximity()
        self.build_concept_network()
        self.calculate_coherence()
        self.generate_dashboard()

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        print(f"\nResults saved to: {self.analysis_dir}/")
        print(f"View dashboard: LOCAL_DASHBOARD.md")

    def load_paper(self):
        """Load paper content"""
        print(f"\n[1/7] Loading paper: {self.paper_path.name}")

        with open(self.paper_path, 'r', encoding='utf-8') as f:
            self.paper_content = f.read()

        word_count = len(self.paper_content.split())
        print(f"  Loaded {word_count:,} words")

    def extract_concepts(self):
        """Extract and count core concepts"""
        print(f"\n[2/7] Extracting concepts...")

        for concept in self.core_concepts:
            count = self.paper_content.lower().count(concept.lower())
            if count > 0:
                self.concepts[concept] = count

        print(f"  Found {len(self.concepts)} core concepts")
        if self.concepts:
            print(f"  Top 3: {self.concepts.most_common(3)}")

    def extract_tags(self):
        """Extract tags (links to tag notes)"""
        print(f"\n[3/7] Extracting tags...")

        # Pattern: [[tag_name]]
        tag_pattern = r'\[\[([^\]]+)\]\]'
        matches = re.findall(tag_pattern, self.paper_content)

        self.tags = [tag for tag in matches if tag.lower() in [t.lower() for t in self.core_tags]]

        print(f"  Found {len(self.tags)} tag references")
        if self.tags:
            print(f"  Unique tags: {set(self.tags)}")

    def detect_breakthroughs(self):
        """Detect breakthrough moments based on config parameters"""
        print(f"\n[4/7] Detecting breakthroughs...")

        params = self.params['breakthrough_detection']

        # Breakthrough trigger phrases
        patterns = [
            r'this resolves',
            r'for the first time',
            r'we can now show',
            r'this unifies',
            r'unprecedented',
            r'novel connection',
            r'breakthrough',
            r'revolutionary'
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, self.paper_content, re.IGNORECASE)

            for match in matches:
                # Get context (200 chars before/after)
                start = max(0, match.start() - 200)
                end = min(len(self.paper_content), match.end() + 200)
                context = self.paper_content[start:end]

                # Extract concepts in context
                context_concepts = [
                    c for c in self.core_concepts
                    if c.lower() in context.lower()
                ]

                # Calculate integration order
                order = self.calculate_integration_order(context_concepts)
                novelty = self.calculate_novelty(context_concepts)

                # Check if meets threshold
                if (order >= params['integration_order_min'] and
                    novelty >= params['novelty_score_min']):

                    self.breakthroughs.append({
                        'trigger': match.group(),
                        'context': context,
                        'concepts': context_concepts,
                        'integration_order': order,
                        'novelty_score': novelty,
                        'position': match.start()
                    })

        print(f"  Detected {len(self.breakthroughs)} breakthroughs")
        if self.breakthroughs:
            print(f"  Orders: {[b['integration_order'] for b in self.breakthroughs]}")

    def calculate_integration_order(self, concepts):
        """Calculate integration order based on concept domains"""
        domains = {
            'physics': ['gravity', 'mass', 'energy', 'entropy', 'quantum', 'spacetime'],
            'theology': ['grace', 'sin', 'soul', 'resurrection', 'faith', 'covenant'],
            'information': ['χ', 'coherence', 'information', 'observer', 'collapse'],
            'consciousness': ['consciousness', 'awareness', 'choice', 'agency']
        }

        domains_involved = set()
        for concept in concepts:
            for domain, terms in domains.items():
                if any(term in concept.lower() for term in terms):
                    domains_involved.add(domain)

        domain_count = len(domains_involved)
        concept_count = len(concepts)

        # Order calculation
        if domain_count >= 4 and concept_count >= 10:
            return 4
        elif domain_count >= 3 and concept_count >= 5:
            return 3
        elif domain_count >= 2 and concept_count >= 3:
            return 2
        else:
            return 1

    def calculate_novelty(self, concepts):
        """Calculate novelty score (0-1)"""
        # Simple heuristic: more concepts = potentially more novel
        base_score = min(len(concepts) / 10.0, 1.0)
        return base_score

    def analyze_tag_proximity(self):
        """Find tags within N words of each other"""
        print(f"\n[5/7] Analyzing tag proximity...")

        window = self.params['network_analysis']['word_proximity_window']
        words = self.paper_content.split()

        # Find tag positions
        tag_positions = defaultdict(list)
        for i, word in enumerate(words):
            for tag in self.core_tags:
                if tag.lower() in word.lower():
                    tag_positions[tag].append(i)

        # Find co-occurrences within window
        for tag1, positions1 in tag_positions.items():
            for tag2, positions2 in tag_positions.items():
                if tag1 >= tag2:
                    continue

                # Check if any positions are within window
                for pos1 in positions1:
                    for pos2 in positions2:
                        if abs(pos1 - pos2) <= window:
                            self.tag_network[tag1].append(tag2)
                            break

        print(f"  Found {len(self.tag_network)} tag connections")
        if self.tag_network:
            print(f"  Sample: {dict(list(self.tag_network.items())[:3])}")

    def build_concept_network(self):
        """Build network graph of concept connections"""
        print(f"\n[6/7] Building concept network...")

        if not np:
            print("  Skipping (numpy not available)")
            self.network_stats = {'nodes': 0, 'edges': 0, 'density': 0, 'avg_clustering': 0}
            return

        try:
            import networkx as nx

            max_depth = self.params['network_analysis']['max_connection_depth']

            G = nx.Graph()

            # Add nodes (concepts)
            for concept in self.concepts.keys():
                G.add_node(concept, weight=self.concepts[concept])

            # Add edges (co-occurrences)
            for i, concept1 in enumerate(list(self.concepts.keys())):
                for concept2 in list(self.concepts.keys())[i+1:]:
                    # Add edge if both concepts appear
                    G.add_edge(concept1, concept2, weight=1)

            # Save network stats
            self.network_stats = {
                'nodes': G.number_of_nodes(),
                'edges': G.number_of_edges(),
                'density': nx.density(G),
                'avg_clustering': nx.average_clustering(G) if G.number_of_edges() > 0 else 0
            }

            print(f"  Network: {self.network_stats['nodes']} nodes, {self.network_stats['edges']} edges")

            # Save for visualization
            self.network = G
        except Exception as e:
            print(f"  Warning: Network build failed: {e}")
            self.network_stats = {'nodes': len(self.concepts), 'edges': 0, 'density': 0, 'avg_clustering': 0}

    def calculate_coherence(self):
        """Calculate coherence score with weighted formula"""
        print(f"\n[7/7] Calculating coherence...")

        weights = self.params['coherence_weights']

        # Simplified metrics
        cross_ref_score = min(len(self.breakthroughs) * 10, 100)
        concept_score = (len(self.concepts) / len(self.core_concepts)) * 100 if self.core_concepts else 0
        term_score = (self.network_stats.get('density', 0) * 100)

        overall_coherence = (
            cross_ref_score * weights['cross_reference_weight'] +
            concept_score * weights['concept_coverage_weight'] +
            term_score * weights['term_consistency_weight']
        )

        self.coherence_scores = {
            'cross_reference': cross_ref_score,
            'concept_coverage': concept_score,
            'term_consistency': term_score,
            'overall': overall_coherence
        }

        print(f"  Overall coherence: {overall_coherence:.1f}/100")

    def generate_dashboard(self):
        """Generate LOCAL_DASHBOARD.md with results"""
        print(f"\nGenerating dashboard...")

        dashboard = f"""---
type: local_dashboard
paper: {self.paper_path.stem}
generated: {datetime.now().isoformat()}
---

# 📊 LOCAL PAPER ANALYSIS DASHBOARD
**Paper:** {self.paper_path.name}
**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 🎛️ CURRENT PARAMETERS
*(Edit config.json and re-run to adjust)*

**Breakthrough Detection:**
- Integration Order Min: **{self.params['breakthrough_detection']['integration_order_min']}**
- Novelty Score Min: **{self.params['breakthrough_detection']['novelty_score_min']}**
- Domains Required: **{self.params['breakthrough_detection']['domains_required']}**

**Coherence Weights:**
- Cross-Reference: **{self.params['coherence_weights']['cross_reference_weight']:.0%}**
- Concept Coverage: **{self.params['coherence_weights']['concept_coverage_weight']:.0%}**
- Term Consistency: **{self.params['coherence_weights']['term_consistency_weight']:.0%}**

**Network Analysis:**
- Max Depth: **{self.params['network_analysis']['max_connection_depth']}** hops
- Proximity Window: **{self.params['network_analysis']['word_proximity_window']}** words

---

## 📈 COHERENCE METRICS

**Overall Coherence:** {self.coherence_scores['overall']:.1f}/100

| Metric | Score |
|--------|-------|
| Cross-Reference Density | {self.coherence_scores['cross_reference']:.1f}/100 |
| Concept Coverage | {self.coherence_scores['concept_coverage']:.1f}/100 |
| Term Consistency | {self.coherence_scores['term_consistency']:.1f}/100 |

---

## 🎯 DETECTED BREAKTHROUGHS

**Found:** {len(self.breakthroughs)} breakthroughs

"""

        for i, bt in enumerate(self.breakthroughs, 1):
            dashboard += f"""
### Breakthrough {i}: Order {bt['integration_order']}
- **Trigger:** "{bt['trigger']}"
- **Integration Order:** {bt['integration_order']}
- **Novelty Score:** {bt['novelty_score']:.2f}
- **Concepts Unified:** {', '.join(bt['concepts'])}

**Context:**
> {bt['context'][:200]}...

---
"""

        dashboard += f"""

## 🔗 TAG NETWORK

**Total Tag Connections:** {len(self.tag_network)}

"""

        for tag, connected in list(self.tag_network.items())[:10]:
            dashboard += f"- **{tag}** → {', '.join(set(connected))}\n"

        dashboard += f"""

---

## 💡 TOP CONCEPTS

| Concept | Count |
|---------|-------|
"""

        for concept, count in self.concepts.most_common(15):
            dashboard += f"| {concept} | {count} |\n"

        dashboard += f"""

---

## 🌐 CONCEPT NETWORK STATS

- **Nodes:** {self.network_stats.get('nodes', 0)}
- **Edges:** {self.network_stats.get('edges', 0)}
- **Density:** {self.network_stats.get('density', 0):.3f}
- **Avg Clustering:** {self.network_stats.get('avg_clustering', 0):.3f}

---

## ⚙️ HOW TO ADJUST PARAMETERS

1. Edit `config.json`
2. Change any parameter values
3. Run: `python analyze_paper.py`
4. Watch this dashboard update!

**Try These Experiments:**
- Lower integration_order_min to 2 → Find more breakthroughs
- Increase word_proximity_window to 50 → Find more tag connections
- Adjust coherence weights → See score change
"""

        # Save dashboard
        dashboard_path = Path('LOCAL_DASHBOARD.md')
        dashboard_path.write_text(dashboard, encoding='utf-8')

        print(f"  Saved: {dashboard_path}")

        # Save detailed JSON
        json_data = {
            'parameters': self.params,
            'breakthroughs': self.breakthroughs,
            'coherence': self.coherence_scores,
            'concepts': dict(self.concepts),
            'tag_network': dict(self.tag_network),
            'network_stats': self.network_stats
        }

        json_path = self.analysis_dir / 'analysis_results.json'
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)

        print(f"  Saved: {json_path}")

def main():
    """Main entry point"""
    import sys

    if '--init' in sys.argv:
        print("Initializing local analysis system...")

    try:
        analyzer = LocalPaperAnalyzer()
        analyzer.analyze_all()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
