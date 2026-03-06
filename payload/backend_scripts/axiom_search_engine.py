"""
Axiom Search Engine
Fast keyword search across all 188 axioms
Searches in titles, formal statements, content, and metadata
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

class AxiomSearchEngine:
    def __init__(self, axioms_folder):
        self.axioms_folder = axioms_folder
        self.index = {}
        
    def build_index(self):
        """Build search index from all axiom files"""
        md_files = []
        for f in Path(self.axioms_folder).glob("*.md"):
            if f.is_file() and re.match(r'^\d{3}_', f.name):
                md_files.append(f)
        
        print(f"Indexing {len(md_files)} axiom files...")
        
        for filepath in md_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = extract_yaml_frontmatter(content)
                axiom_id = metadata.get('axiom_id', '')
                
                if axiom_id:
                    # Remove YAML frontmatter from content for searching
                    content_only = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
                    
                    self.index[axiom_id] = {
                        'file': filepath.name,
                        'filepath': str(filepath),
                        'chain_position': metadata.get('chain_position', 999),
                        'classification': str(metadata.get('classification', '')),
                        'status': metadata.get('status', ''),
                        'domain': metadata.get('domain', []),
                        'stage': metadata.get('stage', 0),
                        'content': content_only.lower(),
                        'metadata': metadata
                    }
            except Exception as e:
                print(f"Error indexing {filepath.name}: {e}")
        
        print(f"✓ Indexed {len(self.index)} axioms\n")
    
    def search(self, query, search_in=['content', 'axiom_id', 'domain', 'status']):
        """Search for query across axioms"""
        query_lower = query.lower()
        results = []
        
        for axiom_id, data in self.index.items():
            score = 0
            matches = []
            
            # Search in axiom ID
            if 'axiom_id' in search_in and query_lower in axiom_id.lower():
                score += 100
                matches.append(f"Axiom ID: {axiom_id}")
            
            # Search in domain
            if 'domain' in search_in:
                domains = data['domain']
                if isinstance(domains, str):
                    domains = [domains]
                for domain in domains:
                    if query_lower in domain.lower():
                        score += 50
                        matches.append(f"Domain: {domain}")
            
            # Search in status/classification
            if 'status' in search_in:
                if query_lower in data['status'].lower():
                    score += 30
                    matches.append(f"Status: {data['status']}")
                if query_lower in data['classification'].lower():
                    score += 30
                    matches.append(f"Classification: {data['classification']}")
            
            # Search in content
            if 'content' in search_in and query_lower in data['content']:
                # Count occurrences
                count = data['content'].count(query_lower)
                score += count * 10
                matches.append(f"Content: {count} occurrence(s)")
                
                # Extract context snippets
                snippets = self.extract_snippets(data['content'], query_lower, max_snippets=3)
                for snippet in snippets:
                    matches.append(f"  → {snippet}")
            
            if score > 0:
                results.append({
                    'axiom_id': axiom_id,
                    'file': data['file'],
                    'filepath': data['filepath'],
                    'chain_position': data['chain_position'],
                    'score': score,
                    'matches': matches,
                    'status': data['status'],
                    'domain': data['domain']
                })
        
        # Sort by score (descending)
        results.sort(key=lambda x: (-x['score'], x['chain_position']))
        
        return results
    
    def extract_snippets(self, content, query, context_chars=100, max_snippets=3):
        """Extract text snippets around query matches"""
        snippets = []
        query_lower = query.lower()
        content_lower = content.lower()
        
        start = 0
        for _ in range(max_snippets):
            pos = content_lower.find(query_lower, start)
            if pos == -1:
                break
            
            # Extract context
            snippet_start = max(0, pos - context_chars)
            snippet_end = min(len(content), pos + len(query) + context_chars)
            snippet = content[snippet_start:snippet_end]
            
            # Clean up snippet
            snippet = snippet.replace('\n', ' ').strip()
            if snippet_start > 0:
                snippet = "..." + snippet
            if snippet_end < len(content):
                snippet = snippet + "..."
            
            snippets.append(snippet)
            start = pos + len(query)
        
        return snippets
    
    def search_by_domain(self, domain):
        """Search axioms by domain"""
        results = []
        for axiom_id, data in self.index.items():
            domains = data['domain']
            if isinstance(domains, str):
                domains = [domains]
            
            if any(domain.lower() in d.lower() for d in domains):
                results.append({
                    'axiom_id': axiom_id,
                    'file': data['file'],
                    'chain_position': data['chain_position'],
                    'domains': domains,
                    'status': data['status']
                })
        
        results.sort(key=lambda x: x['chain_position'])
        return results
    
    def search_by_stage(self, stage):
        """Search axioms by stage"""
        results = []
        for axiom_id, data in self.index.items():
            if data['stage'] == stage:
                results.append({
                    'axiom_id': axiom_id,
                    'file': data['file'],
                    'chain_position': data['chain_position'],
                    'status': data['status']
                })
        
        results.sort(key=lambda x: x['chain_position'])
        return results
    
    def print_results(self, results, max_results=20):
        """Print search results"""
        if not results:
            print("No results found.")
            return
        
        print(f"\nFound {len(results)} result(s):\n")
        print("=" * 80)
        
        for i, result in enumerate(results[:max_results], 1):
            print(f"\n{i}. {result['axiom_id']} (Position: {result['chain_position']}, Score: {result.get('score', 'N/A')})")
            print(f"   File: {result['file']}")
            if 'matches' in result:
                print(f"   Matches:")
                for match in result['matches']:
                    print(f"     {match}")
        
        if len(results) > max_results:
            print(f"\n... and {len(results) - max_results} more results")
        
        print("\n" + "=" * 80)

def interactive_search():
    """Interactive search mode"""
    axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
    
    print("=" * 80)
    print("AXIOM SEARCH ENGINE - Interactive Mode")
    print("=" * 80)
    print("\nCommands:")
    print("  search <query>     - Search for keywords")
    print("  domain <domain>    - Search by domain")
    print("  stage <number>     - Search by stage")
    print("  quit               - Exit")
    print("=" * 80)
    
    engine = AxiomSearchEngine(axioms_folder)
    engine.build_index()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            
            if command == 'search' and len(parts) > 1:
                query = parts[1]
                results = engine.search(query)
                engine.print_results(results)
            
            elif command == 'domain' and len(parts) > 1:
                domain = parts[1]
                results = engine.search_by_domain(domain)
                engine.print_results(results)
            
            elif command == 'stage' and len(parts) > 1:
                try:
                    stage = int(parts[1])
                    results = engine.search_by_stage(stage)
                    engine.print_results(results)
                except ValueError:
                    print("Invalid stage number")
            
            else:
                # Default to search
                results = engine.search(user_input)
                engine.print_results(results)
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main function for command-line usage"""
    import sys
    
    if len(sys.argv) > 1:
        # Command-line search
        query = ' '.join(sys.argv[1:])
        axioms_folder = r"O:\Theophysics_Master\TMSUB\GO FOLDER\_AXIOMS_001-188"
        
        engine = AxiomSearchEngine(axioms_folder)
        engine.build_index()
        results = engine.search(query)
        engine.print_results(results)
    else:
        # Interactive mode
        interactive_search()

if __name__ == "__main__":
    main()
