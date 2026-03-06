"""
Quick test of the Definition Management System

Run this to see it in action with example terms!
"""

from pathlib import Path
from definition_manager import DefinitionManager


def main():
    print("""
╔══════════════════════════════════════════════════════════╗
║   DEFINITION SYSTEM TEST                                 ║
║   Testing with sample Theophysics terms                  ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Initialize manager
    test_dir = Path(__file__).parent / "test_definitions"
    manager = DefinitionManager(test_dir)
    
    # Test terms - mix of standard physics and Theophysics
    test_terms = [
        {
            'term': 'Entropy',
            'aliases': ['thermodynamic entropy', 'disorder'],
            'user_def': None  # Will use Wikipedia
        },
        {
            'term': 'Grace',
            'aliases': ['divine grace', 'unmerited favor'],
            'user_def': 'In Theophysics, grace represents the capacity of a system to absorb entropy without catastrophic failure. It is the structural resilience that allows for error correction and maintains coherence under stress.'
        },
        {
            'term': 'Coherence',
            'aliases': ['structural coherence', 'system coherence'],
            'user_def': 'The degree to which parts of a system maintain consistent relationships and preserve information. High coherence indicates low internal contradiction and high fidelity to structure.'
        },
    ]
    
    print(f"📋 Testing with {len(test_terms)} terms:")
    for term_data in test_terms:
        print(f"   - {term_data['term']}")
    print()
    
    # Process each term
    for i, term_data in enumerate(test_terms, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(test_terms)}] PROCESSING: {term_data['term']}")
        print(f"{'='*60}")
        
        defn = manager.create_or_update_definition(
            term=term_data['term'],
            aliases=term_data['aliases'],
            user_definition=term_data['user_def'],
            fetch_wikipedia=True,
            generate_examples=True,
            find_related=True
        )
        
        # Show results
        print(f"\n📊 RESULTS:")
        print(f"   Term: {defn.term}")
        print(f"   Aliases: {', '.join(defn.aliases)}")
        print(f"   Has user definition: {'Yes' if defn.definition_user else 'No'}")
        print(f"   Has Wikipedia definition: {'Yes' if defn.definition_wikipedia else 'No'}")
        
        if defn.similarity_score is not None:
            print(f"   Similarity: {defn.similarity_score:.2%}")
            print(f"   Status: {defn.validation_status}")
            if defn.discrepancies:
                print(f"   Discrepancies: {len(defn.discrepancies)}")
                for disc in defn.discrepancies[:2]:
                    print(f"      - {disc}")
        
        print(f"   Usage examples: {len(defn.usage_examples)}")
        if defn.usage_examples:
            print(f"      Example: {defn.usage_examples[0][:80]}...")
        
        print(f"   Related terms: {len(defn.related_terms)}")
        if defn.related_terms:
            print(f"      Top 10: {', '.join(defn.related_terms[:10])}")
    
    # Generate report
    print(f"\n\n{'='*60}")
    print(manager.get_report())
    
    # Generate Obsidian files
    print(f"\n{'='*60}")
    print("GENERATING OBSIDIAN FILES")
    print(f"{'='*60}\n")
    
    output_dir = test_dir / "obsidian_test"
    manager.generate_all_obsidian_files(output_dir)
    
    print(f"\n{'='*60}")
    print("✅ TEST COMPLETE!")
    print(f"{'='*60}")
    print(f"\nCheck the generated files:")
    print(f"   Database: {test_dir / 'definitions_database.json'}")
    print(f"   Obsidian files: {output_dir}")
    print(f"\nYou can now:")
    print(f"   1. Review the JSON database")
    print(f"   2. Check the generated .md files")
    print(f"   3. Run CREATE_DEFINITIONS.py for interactive mode")
    print(f"   4. Run SCAN_AND_DEFINE.py to scan your vault")
    print()


if __name__ == "__main__":
    main()
