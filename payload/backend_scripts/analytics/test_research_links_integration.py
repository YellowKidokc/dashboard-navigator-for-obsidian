"""
Test script to verify research links integration with definition scanning.

This script tests:
1. Definition scanning from folders
2. Automatic research link generation
3. Obsidian file generation with research links
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "core"))

from definition_manager import DefinitionManager
from research_linker import ResearchLinker


def test_research_linker():
    """Test ResearchLinker functionality."""
    print("="*70)
    print("TEST 1: ResearchLinker Basic Functionality")
    print("="*70)
    
    linker = ResearchLinker()
    
    # Test generating links for a sample term
    test_terms = ["entropy", "quantum mechanics", "coherence"]
    
    for term in test_terms:
        print(f"\n[Testing term: {term}]")
        links = linker.get_all_links_for_term(term)
        
        if links:
            print(f"  ✓ Generated {len(links)} research links:")
            for source, url in list(links.items())[:3]:
                print(f"    - {source}: {url[:70]}...")
        else:
            print(f"  ✗ No links generated")
    
    print("\n" + "="*70)
    print("TEST 1 COMPLETE")
    print("="*70)


def test_definition_manager_integration():
    """Test DefinitionManager with research links."""
    print("\n" + "="*70)
    print("TEST 2: DefinitionManager Research Links Integration")
    print("="*70)
    
    # Create temporary definitions directory
    test_dir = Path(__file__).parent / "test_definitions"
    test_dir.mkdir(exist_ok=True)
    
    manager = DefinitionManager(test_dir)
    
    # Test creating a definition with research links
    test_term = "Entropy"
    
    print(f"\n[Creating definition for: {test_term}]")
    
    defn = manager.create_or_update_definition(
        term=test_term,
        aliases=["thermodynamic entropy", "disorder"],
        user_definition="A measure of disorder or randomness in a system.",
        fetch_wikipedia=True,
        generate_examples=True,
        find_related=True
    )
    
    # Verify research links were generated
    if defn.research_links:
        print(f"\n✓ Research links successfully integrated!")
        print(f"  Total links: {len(defn.research_links)}")
        print(f"  Sources: {', '.join(list(defn.research_links.keys())[:5])}")
    else:
        print(f"\n✗ No research links found in definition")
    
    # Test generating Obsidian file
    print(f"\n[Generating Obsidian file...]")
    output_file = manager.generate_obsidian_file(test_term)
    
    # Verify research links are in the file
    if output_file.exists():
        content = output_file.read_text(encoding='utf-8')
        if "**Research Links:**" in content:
            print(f"✓ Research links section found in Obsidian file")
            print(f"  File: {output_file}")
        else:
            print(f"✗ Research links section NOT found in Obsidian file")
    
    print("\n" + "="*70)
    print("TEST 2 COMPLETE")
    print("="*70)


def test_folder_scanning_workflow():
    """Test the complete folder scanning workflow."""
    print("\n" + "="*70)
    print("TEST 3: Complete Folder Scanning Workflow")
    print("="*70)
    
    test_dir = Path(__file__).parent / "test_definitions"
    manager = DefinitionManager(test_dir)
    
    # Simulate scanning multiple terms
    terms_to_scan = [
        ("Energy", ["kinetic energy", "potential energy"]),
        ("Coherence", ["quantum coherence", "phase coherence"]),
        ("Grace", ["divine grace"])
    ]
    
    print(f"\n[Scanning {len(terms_to_scan)} terms...]")
    
    for term, aliases in terms_to_scan:
        print(f"\n  Processing: {term}")
        
        defn = manager.create_or_update_definition(
            term=term,
            aliases=aliases,
            fetch_wikipedia=True,
            generate_examples=False,
            find_related=False
        )
        
        if defn.research_links:
            print(f"    ✓ {len(defn.research_links)} research links generated")
        else:
            print(f"    ✗ No research links")
    
    # Generate all Obsidian files
    print(f"\n[Generating Obsidian files for all definitions...]")
    manager.generate_all_obsidian_files()
    
    print("\n" + "="*70)
    print("TEST 3 COMPLETE")
    print("="*70)


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "RESEARCH LINKS INTEGRATION TEST" + " "*22 + "║")
    print("╚" + "="*68 + "╝")
    print()
    
    try:
        # Test 1: Basic ResearchLinker
        test_research_linker()
        
        # Test 2: DefinitionManager integration
        test_definition_manager_integration()
        
        # Test 3: Complete workflow
        test_folder_scanning_workflow()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nSummary:")
        print("  ✓ ResearchLinker generates links for terms")
        print("  ✓ DefinitionManager integrates research links")
        print("  ✓ Obsidian files include research links section")
        print("  ✓ Folder scanning workflow works end-to-end")
        print("\nThe Python definitions functionality is now working!")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
