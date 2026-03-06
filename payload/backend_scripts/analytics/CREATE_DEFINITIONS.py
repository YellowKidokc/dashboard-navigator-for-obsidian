"""
Interactive Definition Creator for Theophysics

Run this script to:
- Create new definitions
- Update existing definitions
- Validate against Wikipedia
- Generate Obsidian-compatible files
"""

from pathlib import Path
from definition_manager import DefinitionManager


def main():
    """Interactive definition creation."""
    print("""
╔══════════════════════════════════════════════════════════╗
║   THEOPHYSICS DEFINITION CREATOR                         ║
║   Auto-populate, validate, and generate definitions     ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Initialize manager
    definitions_dir = Path(__file__).parent / "definitions"
    manager = DefinitionManager(definitions_dir)
    
    print(f"📁 Definitions database: {definitions_dir}")
    print(f"📊 Current definitions: {len(manager.definitions)}")
    print()
    
    while True:
        print("\nWhat would you like to do?")
        print("  1. Create/update a single definition")
        print("  2. Batch create from list")
        print("  3. View definition report")
        print("  4. Generate all Obsidian files")
        print("  5. Search for a definition")
        print("  6. Exit")
        
        choice = input("\nChoice (1-6): ").strip()
        
        if choice == "1":
            create_single_definition(manager)
        elif choice == "2":
            batch_create_definitions(manager)
        elif choice == "3":
            print(manager.get_report())
        elif choice == "4":
            output_dir = input("\nOutput directory (press Enter for default): ").strip()
            output_dir = Path(output_dir) if output_dir else None
            manager.generate_all_obsidian_files(output_dir)
        elif choice == "5":
            search_definitions(manager)
        elif choice == "6":
            print("\n👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


def create_single_definition(manager: DefinitionManager):
    """Create or update a single definition interactively."""
    print("\n" + "="*60)
    print("CREATE/UPDATE DEFINITION")
    print("="*60)
    
    term = input("\nTerm to define: ").strip()
    if not term:
        print("❌ Term cannot be empty")
        return
    
    # Check if exists
    existing = manager.definitions.get(term)
    if existing:
        print(f"\n⚠️  Definition for '{term}' already exists")
        print(f"   User def: {existing.definition_user[:100]}...")
        update = input("   Update it? (y/n): ").strip().lower()
        if update != 'y':
            return
    
    # Aliases
    aliases_input = input("Aliases (comma-separated, or press Enter to skip): ").strip()
    aliases = [a.strip() for a in aliases_input.split(",")] if aliases_input else []
    
    # User definition
    print("\nYour custom definition:")
    print("(Press Enter for empty line, then Ctrl+D or Ctrl+Z+Enter to finish)")
    print("(Or just press Enter twice to use Wikipedia definition only)")
    user_def_lines = []
    try:
        while True:
            line = input()
            if not line and not user_def_lines:
                # Empty - will use Wikipedia
                break
            user_def_lines.append(line)
    except EOFError:
        pass
    
    user_def = "\n".join(user_def_lines).strip() if user_def_lines else None
    
    # Options
    fetch_wiki = input("\nFetch Wikipedia definition? (Y/n): ").strip().lower() != 'n'
    gen_examples = input("Generate usage examples? (Y/n): ").strip().lower() != 'n'
    find_related = input("Find related terms? (Y/n): ").strip().lower() != 'n'
    
    # Create!
    defn = manager.create_or_update_definition(
        term=term,
        aliases=aliases,
        user_definition=user_def,
        fetch_wikipedia=fetch_wiki,
        generate_examples=gen_examples,
        find_related=find_related
    )
    
    # Show result
    print("\n" + "="*60)
    print(f"DEFINITION CREATED: {term}")
    print("="*60)
    print(f"\nAliases: {', '.join(defn.aliases) if defn.aliases else 'None'}")
    print(f"\nDefinition: {defn.definition_user[:200]}...")
    if defn.similarity_score is not None:
        print(f"\nValidation: {defn.validation_status} ({defn.similarity_score:.2%} similar to Wikipedia)")
    print(f"\nRelated terms: {len(defn.related_terms)} found")
    print(f"Usage examples: {len(defn.usage_examples)} generated")
    
    # Generate Obsidian file?
    gen_file = input("\nGenerate Obsidian file now? (Y/n): ").strip().lower() != 'n'
    if gen_file:
        filepath = manager.generate_obsidian_file(term)
        print(f"✓ File created: {filepath}")


def batch_create_definitions(manager: DefinitionManager):
    """Create multiple definitions from a list."""
    print("\n" + "="*60)
    print("BATCH CREATE DEFINITIONS")
    print("="*60)
    
    print("\nEnter terms (one per line, press Enter twice to finish):")
    terms = []
    while True:
        term = input().strip()
        if not term:
            break
        terms.append(term)
    
    if not terms:
        print("❌ No terms provided")
        return
    
    print(f"\n📝 Processing {len(terms)} terms...")
    print("   This will:")
    print("   - Fetch Wikipedia definitions")
    print("   - Generate usage examples")
    print("   - Find related terms")
    
    proceed = input("\nProceed? (y/n): ").strip().lower()
    if proceed != 'y':
        return
    
    for i, term in enumerate(terms, 1):
        print(f"\n[{i}/{len(terms)}] Processing: {term}")
        try:
            manager.create_or_update_definition(
                term=term,
                fetch_wikipedia=True,
                generate_examples=True,
                find_related=True
            )
        except Exception as e:
            print(f"❌ Error processing '{term}': {e}")
            continue
    
    print(f"\n✅ Batch processing complete!")
    print(f"   {len(terms)} definitions processed")
    
    # Generate all files?
    gen_files = input("\nGenerate all Obsidian files? (Y/n): ").strip().lower() != 'n'
    if gen_files:
        manager.generate_all_obsidian_files()


def search_definitions(manager: DefinitionManager):
    """Search and display definitions."""
    query = input("\nSearch term: ").strip().lower()
    if not query:
        return
    
    matches = []
    for term, defn in manager.definitions.items():
        if query in term.lower() or any(query in alias.lower() for alias in defn.aliases):
            matches.append(defn)
    
    if not matches:
        print(f"❌ No definitions found matching '{query}'")
        return
    
    print(f"\n✓ Found {len(matches)} matches:")
    for i, defn in enumerate(matches, 1):
        print(f"\n{i}. {defn.term}")
        if defn.aliases:
            print(f"   Aliases: {', '.join(defn.aliases)}")
        print(f"   Definition: {defn.definition_user[:150]}...")
        print(f"   Status: {defn.validation_status}")
        if defn.similarity_score:
            print(f"   Similarity: {defn.similarity_score:.2%}")
        print(f"   Views: {defn.views_count}, Appearances: {defn.appearances_count}")


if __name__ == "__main__":
    main()
