"""
Exclusion List Management Tool

Manage terms that should be excluded from definition scanning and research linking.
This tool allows you to:
- View current exclusion list
- Add terms to exclusion list
- Remove terms from exclusion list
- Clear entire exclusion list
- Import/export exclusion lists
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent / "core"))

from definition_manager import DefinitionManager
from research_linker import ResearchLinker


def display_menu():
    """Display the main menu."""
    print("\n" + "="*70)
    print("EXCLUSION LIST MANAGEMENT")
    print("="*70)
    print("\n1. View excluded terms")
    print("2. Add term to exclusion list")
    print("3. Remove term from exclusion list")
    print("4. Bulk add terms (comma-separated)")
    print("5. Clear all exclusions")
    print("6. Export exclusion list")
    print("7. Import exclusion list")
    print("8. Sync exclusion lists (DefinitionManager ↔ ResearchLinker)")
    print("9. Exit")
    print("\n" + "="*70)


def view_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """View all excluded terms."""
    print("\n" + "="*70)
    print("EXCLUDED TERMS")
    print("="*70)
    
    def_excluded = def_manager.get_excluded_terms()
    res_excluded = res_linker.get_excluded_terms()
    
    # Combine and deduplicate
    all_excluded = sorted(set(def_excluded + res_excluded))
    
    if not all_excluded:
        print("\n✓ No terms are currently excluded")
    else:
        print(f"\nTotal excluded terms: {len(all_excluded)}")
        print("\nExcluded terms:")
        for i, term in enumerate(all_excluded, 1):
            sources = []
            if term in def_excluded:
                sources.append("Definitions")
            if term in res_excluded:
                sources.append("Research")
            print(f"  {i:3d}. {term:30s} [{', '.join(sources)}]")


def add_exclusion(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Add a term to exclusion list."""
    term = input("\nEnter term to exclude: ").strip()
    if not term:
        print("❌ No term entered")
        return
    
    def_manager.add_to_exclusion_list(term)
    res_linker.add_to_exclusion_list(term)
    print(f"✓ '{term}' added to exclusion lists")


def remove_exclusion(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Remove a term from exclusion list."""
    term = input("\nEnter term to remove from exclusion: ").strip()
    if not term:
        print("❌ No term entered")
        return
    
    def_manager.remove_from_exclusion_list(term)
    res_linker.remove_from_exclusion_list(term)
    print(f"✓ '{term}' removed from exclusion lists")


def bulk_add_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Add multiple terms at once."""
    print("\nEnter terms separated by commas (e.g., John, Smith, MyName):")
    terms_input = input("> ").strip()
    
    if not terms_input:
        print("❌ No terms entered")
        return
    
    terms = [t.strip() for t in terms_input.split(',') if t.strip()]
    
    if not terms:
        print("❌ No valid terms found")
        return
    
    print(f"\nAdding {len(terms)} terms to exclusion lists...")
    for term in terms:
        def_manager.add_to_exclusion_list(term)
        res_linker.add_to_exclusion_list(term)
        print(f"  ✓ {term}")
    
    print(f"\n✓ {len(terms)} terms added to exclusion lists")


def clear_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Clear all exclusions."""
    confirm = input("\n⚠️  Clear ALL exclusions? This cannot be undone! (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        def_manager.clear_exclusion_list()
        res_linker.clear_exclusion_list()
        print("✓ All exclusions cleared")
    else:
        print("❌ Cancelled")


def export_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Export exclusion list to a text file."""
    output_file = Path(__file__).parent / "exclusion_list_export.txt"
    
    def_excluded = def_manager.get_excluded_terms()
    res_excluded = res_linker.get_excluded_terms()
    all_excluded = sorted(set(def_excluded + res_excluded))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Excluded Terms Export\n")
        f.write(f"# Total: {len(all_excluded)} terms\n")
        f.write("# One term per line\n\n")
        for term in all_excluded:
            f.write(f"{term}\n")
    
    print(f"\n✓ Exported {len(all_excluded)} terms to: {output_file}")


def import_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Import exclusion list from a text file."""
    file_path = input("\nEnter path to import file (or press Enter for default): ").strip()
    
    if not file_path:
        file_path = Path(__file__).parent / "exclusion_list_export.txt"
    else:
        file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    terms = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            terms.append(line)
    
    if not terms:
        print("❌ No terms found in file")
        return
    
    print(f"\nImporting {len(terms)} terms...")
    for term in terms:
        def_manager.add_to_exclusion_list(term)
        res_linker.add_to_exclusion_list(term)
    
    print(f"✓ Imported {len(terms)} terms")


def sync_exclusions(def_manager: DefinitionManager, res_linker: ResearchLinker):
    """Sync exclusion lists between DefinitionManager and ResearchLinker."""
    def_excluded = set(def_manager.get_excluded_terms())
    res_excluded = set(res_linker.get_excluded_terms())
    
    # Find differences
    only_in_def = def_excluded - res_excluded
    only_in_res = res_excluded - def_excluded
    
    if not only_in_def and not only_in_res:
        print("\n✓ Exclusion lists are already in sync")
        return
    
    print(f"\nSyncing exclusion lists...")
    
    # Add missing terms
    for term in only_in_def:
        res_linker.add_to_exclusion_list(term)
        print(f"  → Added '{term}' to ResearchLinker")
    
    for term in only_in_res:
        def_manager.add_to_exclusion_list(term)
        print(f"  → Added '{term}' to DefinitionManager")
    
    total_synced = len(only_in_def) + len(only_in_res)
    print(f"\n✓ Synced {total_synced} terms")


def main():
    """Main menu loop."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*18 + "EXCLUSION LIST MANAGER" + " "*28 + "║")
    print("╚" + "="*68 + "╝")
    
    # Initialize managers
    definitions_dir = Path(__file__).parent / "definitions"
    def_manager = DefinitionManager(definitions_dir)
    res_linker = ResearchLinker()
    
    while True:
        display_menu()
        choice = input("\nSelect option (1-9): ").strip()
        
        if choice == '1':
            view_exclusions(def_manager, res_linker)
        elif choice == '2':
            add_exclusion(def_manager, res_linker)
        elif choice == '3':
            remove_exclusion(def_manager, res_linker)
        elif choice == '4':
            bulk_add_exclusions(def_manager, res_linker)
        elif choice == '5':
            clear_exclusions(def_manager, res_linker)
        elif choice == '6':
            export_exclusions(def_manager, res_linker)
        elif choice == '7':
            import_exclusions(def_manager, res_linker)
        elif choice == '8':
            sync_exclusions(def_manager, res_linker)
        elif choice == '9':
            print("\n✓ Goodbye!")
            break
        else:
            print("\n❌ Invalid option")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
