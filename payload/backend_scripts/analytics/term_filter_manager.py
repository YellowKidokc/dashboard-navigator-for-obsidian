"""
Interactive Term Filter Manager
================================
Allows user to mark terms as:
- RED (exclude) - noise terms, common words, names that appear too often
- BLUE (include) - important terms to track
- UNDECIDED (gray) - needs review

Saves preferences to JSON so you only review each term once.
"""

import json
from pathlib import Path
from typing import Dict, List, Set
from collections import Counter
import re


class TermFilterManager:
    """Manage term filtering with persistent preferences."""
    
    def __init__(self, config_file: str = None):
        self.config_file = Path(config_file) if config_file else Path(__file__).parent / "term_filter_config.json"
        self.blacklist: Set[str] = set()  # RED - excluded
        self.whitelist: Set[str] = set()  # BLUE - included
        self.load_config()
    
    def load_config(self):
        """Load saved preferences."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.blacklist = set(config.get('blacklist', []))
                    self.whitelist = set(config.get('whitelist', []))
                print(f"Loaded {len(self.blacklist)} blacklist and {len(self.whitelist)} whitelist terms")
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
    
    def save_config(self):
        """Save preferences to disk."""
        config = {
            'blacklist': sorted(list(self.blacklist)),
            'whitelist': sorted(list(self.whitelist)),
            'last_updated': str(Path(__file__).parent)
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Saved config: {len(self.blacklist)} blacklist, {len(self.whitelist)} whitelist")
    
    def mark_red(self, term: str):
        """Mark term as excluded (RED)."""
        term_lower = term.lower()
        self.blacklist.add(term_lower)
        if term_lower in self.whitelist:
            self.whitelist.remove(term_lower)
        self.save_config()
    
    def mark_blue(self, term: str):
        """Mark term as included (BLUE)."""
        term_lower = term.lower()
        self.whitelist.add(term_lower)
        if term_lower in self.blacklist:
            self.blacklist.remove(term_lower)
        self.save_config()
    
    def is_blacklisted(self, term: str) -> bool:
        """Check if term is blacklisted."""
        return term.lower() in self.blacklist
    
    def is_whitelisted(self, term: str) -> bool:
        """Check if term is whitelisted."""
        return term.lower() in self.whitelist
    
    def is_decided(self, term: str) -> bool:
        """Check if term has been decided (red or blue)."""
        term_lower = term.lower()
        return term_lower in self.blacklist or term_lower in self.whitelist
    
    def get_status(self, term: str) -> str:
        """Get term status: 'red', 'blue', or 'undecided'."""
        term_lower = term.lower()
        if term_lower in self.blacklist:
            return 'red'
        elif term_lower in self.whitelist:
            return 'blue'
        else:
            return 'undecided'
    
    def extract_terms(self, text: str, min_length: int = 3) -> Counter:
        """
        Extract all terms from text with frequency count.
        
        Args:
            text: Text to analyze
            min_length: Minimum term length (default 3)
        
        Returns:
            Counter of terms and their frequencies
        """
        # Extract words (alphanumeric, allow hyphens)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\-]*\b', text.lower())
        
        # Filter by length
        words = [w for w in words if len(w) >= min_length]
        
        return Counter(words)
    
    def filter_terms(self, terms: Counter) -> Dict[str, List[tuple]]:
        """
        Categorize terms by status.
        
        Returns:
            {
                'red': [(term, count), ...],
                'blue': [(term, count), ...],
                'undecided': [(term, count), ...]
            }
        """
        categorized = {
            'red': [],
            'blue': [],
            'undecided': []
        }
        
        for term, count in terms.most_common():
            status = self.get_status(term)
            categorized[status].append((term, count))
        
        return categorized
    
    def get_undecided_terms(self, text: str, top_n: int = 50) -> List[tuple]:
        """
        Get top undecided terms from text.
        
        Args:
            text: Text to analyze
            top_n: Number of top terms to return
        
        Returns:
            List of (term, count) tuples for undecided terms
        """
        all_terms = self.extract_terms(text)
        categorized = self.filter_terms(all_terms)
        
        # Return top N undecided terms by frequency
        return categorized['undecided'][:top_n]
    
    def get_filtered_terms(self, text: str, include_counts: bool = True) -> List:
        """
        Get only whitelisted terms from text.
        
        Args:
            text: Text to analyze
            include_counts: If True, return (term, count), else just terms
        
        Returns:
            Filtered list of terms
        """
        all_terms = self.extract_terms(text)
        categorized = self.filter_terms(all_terms)
        
        if include_counts:
            return categorized['blue']
        else:
            return [term for term, count in categorized['blue']]
    
    def analyze_paper(self, filepath: Path) -> Dict:
        """
        Analyze a paper and categorize terms.
        
        Returns:
            {
                'total_terms': int,
                'red': [(term, count), ...],
                'blue': [(term, count), ...],
                'undecided': [(term, count), ...],
                'summary': {...}
            }
        """
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e)}
        
        all_terms = self.extract_terms(content)
        categorized = self.filter_terms(all_terms)
        
        # Calculate statistics
        total_unique = len(all_terms)
        red_count = sum(count for term, count in categorized['red'])
        blue_count = sum(count for term, count in categorized['blue'])
        undecided_count = sum(count for term, count in categorized['undecided'])
        total_occurrences = red_count + blue_count + undecided_count
        
        return {
            'filepath': str(filepath),
            'total_unique_terms': total_unique,
            'total_occurrences': total_occurrences,
            'red': categorized['red'],
            'blue': categorized['blue'],
            'undecided': categorized['undecided'],
            'summary': {
                'red_terms': len(categorized['red']),
                'blue_terms': len(categorized['blue']),
                'undecided_terms': len(categorized['undecided']),
                'red_occurrences': red_count,
                'blue_occurrences': blue_count,
                'undecided_occurrences': undecided_count,
                'red_percentage': (red_count / total_occurrences * 100) if total_occurrences > 0 else 0,
                'blue_percentage': (blue_count / total_occurrences * 100) if total_occurrences > 0 else 0,
            }
        }
    
    def print_analysis(self, analysis: Dict, show_red: bool = True, show_blue: bool = True, 
                      show_undecided: bool = True, top_n: int = 20):
        """Pretty print analysis results."""
        print("\n" + "=" * 80)
        print(f"TERM ANALYSIS: {Path(analysis['filepath']).name}")
        print("=" * 80)
        
        summary = analysis['summary']
        print(f"\nTotal unique terms: {analysis['total_unique_terms']}")
        print(f"Total occurrences: {analysis['total_occurrences']}")
        print()
        
        if show_red and analysis['red']:
            print(f"🔴 RED (Excluded) - {summary['red_terms']} terms, {summary['red_occurrences']} occurrences ({summary['red_percentage']:.1f}%)")
            print("-" * 40)
            for term, count in analysis['red'][:top_n]:
                print(f"  {count:>5} | {term}")
            if len(analysis['red']) > top_n:
                print(f"  ... and {len(analysis['red']) - top_n} more")
            print()
        
        if show_blue and analysis['blue']:
            print(f"🔵 BLUE (Included) - {summary['blue_terms']} terms, {summary['blue_occurrences']} occurrences ({summary['blue_percentage']:.1f}%)")
            print("-" * 40)
            for term, count in analysis['blue'][:top_n]:
                print(f"  {count:>5} | {term}")
            if len(analysis['blue']) > top_n:
                print(f"  ... and {len(analysis['blue']) - top_n} more")
            print()
        
        if show_undecided and analysis['undecided']:
            undecided_pct = 100 - summary['red_percentage'] - summary['blue_percentage']
            print(f"⚪ UNDECIDED (Needs Review) - {summary['undecided_terms']} terms, {summary['undecided_occurrences']} occurrences ({undecided_pct:.1f}%)")
            print("-" * 40)
            for term, count in analysis['undecided'][:top_n]:
                print(f"  {count:>5} | {term}")
            if len(analysis['undecided']) > top_n:
                print(f"  ... and {len(analysis['undecided']) - top_n} more")
            print()


def interactive_review_session(manager: TermFilterManager, paper_path: Path):
    """Interactive session to review and mark terms."""
    analysis = manager.analyze_paper(paper_path)
    undecided = analysis['undecided']
    
    if not undecided:
        print("✅ All terms have been decided! No undecided terms.")
        return
    
    print("\n" + "=" * 80)
    print("INTERACTIVE TERM REVIEW")
    print("=" * 80)
    print(f"\nPaper: {paper_path.name}")
    print(f"Undecided terms: {len(undecided)}")
    print("\nCommands:")
    print("  r = mark RED (exclude)")
    print("  b = mark BLUE (include)")
    print("  s = skip (decide later)")
    print("  q = quit")
    print("=" * 80)
    print()
    
    for i, (term, count) in enumerate(undecided, 1):
        print(f"\n[{i}/{len(undecided)}] Term: '{term}' (appears {count} times)")
        
        while True:
            choice = input("  Mark as [r]ed, [b]lue, [s]kip, or [q]uit? ").lower().strip()
            
            if choice == 'r':
                manager.mark_red(term)
                print(f"  🔴 Marked '{term}' as RED (excluded)")
                break
            elif choice == 'b':
                manager.mark_blue(term)
                print(f"  🔵 Marked '{term}' as BLUE (included)")
                break
            elif choice == 's':
                print(f"  ⚪ Skipped '{term}'")
                break
            elif choice == 'q':
                print("\nQuitting review session...")
                return
            else:
                print("  Invalid choice. Use r, b, s, or q")
    
    print("\n✅ Review session complete!")


def main():
    """Test the term filter manager."""
    import sys
    
    manager = TermFilterManager()
    
    # Find a test paper
    import os
    base_path = Path(os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3'))
    test_papers = list(base_path.rglob("*canonical*.md"))[:1]
    
    if not test_papers:
        print("No test papers found")
        return
    
    paper = test_papers[0]
    print(f"Analyzing: {paper.name}\n")
    
    # Analyze
    analysis = manager.analyze_paper(paper)
    manager.print_analysis(analysis, show_red=False, show_blue=False, show_undecided=True, top_n=30)
    
    # Offer interactive session
    if analysis['undecided']:
        print("\n" + "=" * 80)
        choice = input("Start interactive review session? [y/n]: ").lower().strip()
        if choice == 'y':
            interactive_review_session(manager, paper)
            
            # Show updated analysis
            print("\n\nUpdated analysis:")
            analysis = manager.analyze_paper(paper)
            manager.print_analysis(analysis, top_n=20)


if __name__ == "__main__":
    main()
