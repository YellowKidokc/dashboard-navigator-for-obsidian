"""
Scan Theophysics vault and auto-generate definitions for key terms.

This script will:
1. Scan all markdown files in your vault
2. Extract key scientific/philosophical terms
3. Auto-generate definitions from Wikipedia
4. Track term frequency
5. Generate Obsidian-compatible definition files
"""

import re
from pathlib import Path
from collections import Counter
from typing import List, Set
from definition_manager import DefinitionManager


class VaultScanner:
    """Scan vault and extract key terms."""
    
    # Terms we definitely want to define
    PRIORITY_TERMS = [
        # Physics fundamentals
        'entropy', 'energy', 'field', 'quantum', 'wave', 'particle',
        'momentum', 'force', 'mass', 'spacetime', 'causality',
        
        # Thermodynamics
        'temperature', 'heat', 'work', 'equilibrium', 'disorder',
        
        # Information
        'information', 'bit', 'signal', 'noise', 'channel',
        
        # Theophysics
        'axiom', 'logos', 'coherence', 'grace', 'hope', 'faith',
        'love', 'patience', 'self-control', 'peace', 'truth',
        'humility', 'goodness', 'unity', 'joy', 'wisdom', 'knowledge',
        
        # Philosophy
        'being', 'existence', 'reality', 'essence', 'telos'
    ]
    
    # Patterns to identify scientific terms
    SCIENTIFIC_PATTERNS = [
        r'\b[A-Z][a-z]+\'s\s+(?:law|principle|theorem|equation)\b',  # Newton's law
        r'\b(?:law|principle|theorem)\s+of\s+[a-z]+\b',  # Law of thermodynamics
    ]
    
    def __init__(self, vault_path: Path):
        """Initialize scanner."""
        self.vault_path = Path(vault_path)
        self.term_frequency = Counter()
        self.terms_by_file = {}
    
    def scan_vault(self, min_frequency: int = 3) -> List[str]:
        """
        Scan vault and extract terms worth defining.
        
        Args:
            min_frequency: Minimum times a term must appear
        
        Returns:
            List of terms to define
        """
        print(f"📂 Scanning vault: {self.vault_path}")
        
        # Find all markdown files
        md_files = list(self.vault_path.rglob("*.md"))
        print(f"   Found {len(md_files)} markdown files")
        
        # Scan each file
        for md_file in md_files:
            try:
                self._scan_file(md_file)
            except Exception as e:
                print(f"   ⚠️  Error scanning {md_file.name}: {e}")
        
        print(f"✓ Scan complete!")
        print(f"   Total unique terms: {len(self.term_frequency)}")
        
        # Filter terms
        terms_to_define = self._filter_terms(min_frequency)
        
        print(f"\n📋 Terms to define ({len(terms_to_define)}):")
        for i, term in enumerate(terms_to_define[:20], 1):
            freq = self.term_frequency[term]
            print(f"   {i}. {term} ({freq} occurrences)")
        
        if len(terms_to_define) > 20:
            print(f"   ... and {len(terms_to_define) - 20} more")
        
        return terms_to_define
    
    def _scan_file(self, filepath: Path):
        """Scan a single file for terms."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove code blocks and frontmatter
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content = re.sub(r'^---\n.*?\n---', '', content, flags=re.DOTALL | re.MULTILINE)
        
        # Extract terms
        terms = self._extract_terms(content)
        
        # Update counters
        for term in terms:
            self.term_frequency[term] += 1
            
            if term not in self.terms_by_file:
                self.terms_by_file[term] = []
            self.terms_by_file[term].append(str(filepath))
    
    def _extract_terms(self, content: str) -> Set[str]:
        """Extract key terms from content."""
        terms = set()
        
        # Priority terms (case-insensitive)
        content_lower = content.lower()
        for priority_term in self.PRIORITY_TERMS:
            if priority_term in content_lower:
                terms.add(priority_term.capitalize())
        
        # Scientific patterns
        for pattern in self.SCIENTIFIC_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.update(matches)
        
        # Capitalized terms (likely proper nouns or important concepts)
        # But not at sentence start
        capitalized = re.findall(r'(?<!^\s)[A-Z][a-z]{3,}(?:\s+[A-Z][a-z]+)*', content)
        
        # Filter out common words
        common_words = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 
                       'What', 'Who', 'Which', 'However', 'Therefore', 'Thus'}
        capitalized = [term for term in capitalized if term not in common_words]
        
        terms.update(capitalized)
        
        return terms
    
    def _filter_terms(self, min_frequency: int) -> List[str]:
        """Filter terms by frequency and priority."""
        terms_to_define = []
        
        # Always include priority terms if they appear at all
        for priority_term in self.PRIORITY_TERMS:
            cap_term = priority_term.capitalize()
            if cap_term in self.term_frequency and self.term_frequency[cap_term] > 0:
                terms_to_define.append(cap_term)
        
        # Add frequent terms
        for term, freq in self.term_frequency.most_common():
            if freq >= min_frequency and term not in terms_to_define:
                # Skip very short terms
                if len(term) < 4:
                    continue
                # Skip if looks like a name (all caps or mixed case)
                if term.isupper() or (term[0].islower()):
                    continue
                terms_to_define.append(term)
        
        return sorted(set(terms_to_define))


def main():
    """Main scanning and definition generation."""
    print("""
╔══════════════════════════════════════════════════════════╗
║   THEOPHYSICS VAULT SCANNER & AUTO-DEFINER              ║
║   Scan vault, extract terms, generate definitions       ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Get vault path
    vault_path = input("\nPath to Theophysics vault (or press Enter for default): ").strip()
    if not vault_path:
        vault_path = Path.cwd().parent.parent / "Theophysics_Vault"
    else:
        vault_path = Path(vault_path)
    
    if not vault_path.exists():
        print(f"❌ Vault not found: {vault_path}")
        return
    
    # Scan vault
    scanner = VaultScanner(vault_path)
    
    min_freq = input("\nMinimum term frequency (default: 3): ").strip()
    min_freq = int(min_freq) if min_freq else 3
    
    terms = scanner.scan_vault(min_frequency=min_freq)
    
    if not terms:
        print("\n❌ No terms found to define")
        return
    
    # Initialize definition manager
    definitions_dir = Path(__file__).parent / "definitions"
    manager = DefinitionManager(definitions_dir)
    
    # Ask what to do
    print(f"\n{'='*60}")
    print(f"Found {len(terms)} terms to define")
    print(f"{'='*60}")
    print("\nOptions:")
    print("  1. Auto-generate all definitions from Wikipedia")
    print("  2. Show list and let me choose which to generate")
    print("  3. Export list to file for manual review")
    print("  4. Cancel")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == "1":
        auto_generate_all(manager, scanner, terms)
    elif choice == "2":
        selective_generate(manager, scanner, terms)
    elif choice == "3":
        export_term_list(terms, scanner)
    else:
        print("Cancelled")


def auto_generate_all(manager: DefinitionManager, scanner: VaultScanner, terms: List[str]):
    """Auto-generate definitions for all terms."""
    print(f"\n🚀 Auto-generating definitions for {len(terms)} terms...")
    print("   This may take a few minutes...")
    
    # Show excluded terms if any
    excluded = manager.get_excluded_terms()
    if excluded:
        print(f"\n📋 Currently excluded terms ({len(excluded)}):")
        for term in excluded[:10]:
            print(f"   - {term}")
        if len(excluded) > 10:
            print(f"   ... and {len(excluded) - 10} more")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        return
    
    success_count = 0
    failed_terms = []
    skipped_count = 0
    
    for i, term in enumerate(terms, 1):
        print(f"\n[{i}/{len(terms)}] {term}")
        
        # Check if already excluded
        if manager.is_excluded(term):
            print(f"   ⊘ Skipped (in exclusion list)")
            skipped_count += 1
            continue
        
        # Prompt user for accept/deny
        response = input(f"   Process '{term}'? (y=yes, n=skip once, x=exclude permanently): ").strip().lower()
        
        if response == 'x':
            manager.add_to_exclusion_list(term)
            skipped_count += 1
            continue
        elif response == 'n':
            print(f"   ⊘ Skipped")
            skipped_count += 1
            continue
        
        try:
            # Get term files for appearance tracking
            term_files = scanner.terms_by_file.get(term, [])
            
            defn = manager.create_or_update_definition(
                term=term,
                fetch_wikipedia=True,
                generate_examples=True,
                find_related=True
            )
            
            if defn:
                # Update appearance count
                defn.appearances_count = scanner.term_frequency.get(term, 0)
                defn.source_files = term_files
                manager.save_definitions()
                success_count += 1
            else:
                skipped_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed_terms.append(term)
    
    print(f"\n{'='*60}")
    print(f"✅ Auto-generation complete!")
    print(f"   Success: {success_count}/{len(terms)}")
    print(f"   Skipped: {skipped_count}")
    if failed_terms:
        print(f"   Failed: {len(failed_terms)}")
        print(f"   Failed terms: {', '.join(failed_terms[:5])}")
    print(f"{'='*60}")
    
    # Generate Obsidian files
    gen_files = input("\nGenerate Obsidian definition files? (Y/n): ").strip().lower() != 'n'
    if gen_files:
        output_dir = Path(__file__).parent / "definitions" / "obsidian_definitions"
        manager.generate_all_obsidian_files(output_dir)
        print(f"\n✓ Obsidian files generated: {output_dir}")


def selective_generate(manager: DefinitionManager, scanner: VaultScanner, terms: List[str]):
    """Let user choose which terms to generate."""
    print(f"\n📋 Review and select terms to define:")
    
    selected = []
    for i, term in enumerate(terms, 1):
        freq = scanner.term_frequency[term]
        print(f"\n{i}. {term} ({freq} occurrences)")
        
        choice = input("   Generate? (y/n/q to quit): ").strip().lower()
        if choice == 'y':
            selected.append(term)
        elif choice == 'q':
            break
    
    if not selected:
        print("❌ No terms selected")
        return
    
    print(f"\n✓ {len(selected)} terms selected")
    auto_generate_all(manager, scanner, selected)


def export_term_list(terms: List[str], scanner: VaultScanner):
    """Export term list to file for manual review."""
    output_file = Path(__file__).parent / "definitions" / "terms_to_define.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("THEOPHYSICS TERMS TO DEFINE\n")
        f.write("="*60 + "\n\n")
        
        for term in terms:
            freq = scanner.term_frequency[term]
            f.write(f"{term} ({freq} occurrences)\n")
    
    print(f"\n✓ Term list exported: {output_file}")


if __name__ == "__main__":
    main()
