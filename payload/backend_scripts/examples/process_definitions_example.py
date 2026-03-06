"""
Example: Process Definitions with Definition 2.0
=================================================

This example shows how to:
1. Index your vault
2. Process definitions with external sources
3. Detect drift
4. Generate definition notes
5. View reports
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.definition_processor_v2 import DefinitionProcessorV2
from engine.enhanced_definition_engine import EnhancedDefinitionEngine
from engine.structure_engine import StructureEngine


def example_1_basic_processing():
    """Example 1: Basic processing of all definitions."""
    print("=" * 70)
    print("Example 1: Basic Processing")
    print("=" * 70)
    
    # Set your vault path
    vault_path = Path("path/to/your/obsidian/vault")
    
    # Create processor
    processor = DefinitionProcessorV2(
        vault_path=vault_path,
        max_workers=8  # Use 8 CPU cores
    )
    
    # Process all definitions
    stats = processor.process_all_definitions()
    
    print("\nResults:")
    print(f"  Total: {stats['total']}")
    print(f"  Success: {stats['success']}")
    print(f"  Partial: {stats['partial']}")
    print(f"  Failed: {stats['failed']}")


def example_2_custom_configuration():
    """Example 2: Custom configuration."""
    print("=" * 70)
    print("Example 2: Custom Configuration")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    output_dir = Path("custom_output")
    
    processor = DefinitionProcessorV2(
        vault_path=vault_path,
        output_dir=output_dir,
        max_workers=16  # Use more workers for faster processing
    )
    
    # Force reprocess all (even if already processed)
    stats = processor.process_all_definitions(force_reprocess=True)
    
    print(f"\nOutput saved to: {output_dir}")


def example_3_single_definition():
    """Example 3: Process a single definition."""
    print("=" * 70)
    print("Example 3: Single Definition")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    
    # Create enhanced engine
    engine = EnhancedDefinitionEngine(vault_path)
    
    # Index vault first
    print("Indexing vault...")
    engine.full_index()
    
    # Get status for a specific term
    term_id = "def-coherence"
    status = engine.get_definition_status(term_id)
    
    print(f"\nDefinition: {status['definition'].get('name', term_id)}")
    print(f"Usage count: {status['usage_count']}")
    print(f"Equation count: {status['equation_count']}")
    
    # Check for drift
    print("\nChecking for drift...")
    drift_report = engine.check_drift(term_id)
    print(f"Drifts detected: {drift_report['total_drifts']}")


def example_4_generate_notes():
    """Example 4: Generate definition notes."""
    print("=" * 70)
    print("Example 4: Generate Definition Notes")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    
    processor = DefinitionProcessorV2(vault_path)
    
    # Process first
    print("Processing definitions...")
    processor.process_all_definitions()
    
    # Generate notes for specific terms
    terms = ["def-coherence", "def-grace", "def-logos-field"]
    
    for term_id in terms:
        print(f"\nGenerating note for {term_id}...")
        path = processor.generate_definition_note(term_id)
        if path:
            print(f"  ✓ Created: {path}")
        else:
            print(f"  ✗ Failed")


def example_5_structure_builder():
    """Example 5: Use structure builder to create new definitions."""
    print("=" * 70)
    print("Example 5: Structure Builder")
    print("=" * 70)
    
    from engine.settings import Settings
    from engine.database_engine import DatabaseEngine
    
    settings = Settings()
    settings.set("vault_path", "path/to/your/obsidian/vault")
    
    db = DatabaseEngine(settings)
    structure = StructureEngine(settings, db)
    
    # Create a new definition note
    path = structure.build_definition_structure(
        term="Quantum Entanglement",
        symbol="E_q",
        output_dir=Path("Definitions")
    )
    
    print(f"\nCreated definition note: {path}")


def example_6_provenance_tracking():
    """Example 6: Access provenance data."""
    print("=" * 70)
    print("Example 6: Provenance Tracking")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    output_dir = vault_path / "Definitions_v2"
    
    # Read provenance log
    provenance_log = output_dir / "provenance_log.json"
    
    if provenance_log.exists():
        import json
        data = json.loads(provenance_log.read_text())
        
        print(f"\nTotal definitions: {data['total_definitions']}")
        print(f"Generated: {data['generated']}")
        
        # Show first 5 entries
        print("\nSample entries:")
        for entry in data['entries'][:5]:
            print(f"\n  Term: {entry['term_name']}")
            print(f"  Status: {entry['status']}")
            print(f"  Sources: {len(entry['external_sources'])}")
            print(f"  Drift: {'Yes' if entry['drift_detected'] else 'No'}")
    else:
        print("No provenance log found. Run processing first.")


def example_7_drift_analysis():
    """Example 7: Analyze drift across all definitions."""
    print("=" * 70)
    print("Example 7: Drift Analysis")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    
    engine = EnhancedDefinitionEngine(vault_path)
    engine.full_index()
    
    # Check drift for all terms
    print("Checking drift for all definitions...")
    drift_report = engine.check_drift()
    
    print(f"\nTotal drifts: {drift_report['total_drifts']}")
    print(f"\nBy severity:")
    for severity, count in drift_report['by_severity'].items():
        print(f"  {severity}: {count}")
    
    print(f"\nTop 5 terms with most drift:")
    by_term = drift_report['by_term']
    sorted_terms = sorted(by_term.items(), key=lambda x: -x[1])[:5]
    for term, count in sorted_terms:
        print(f"  {term}: {count} drifts")


def example_8_ai_integration():
    """Example 8: Integrate with AI for enhanced drift detection."""
    print("=" * 70)
    print("Example 8: AI Integration")
    print("=" * 70)
    
    vault_path = Path("path/to/your/obsidian/vault")
    
    # You would need to implement your AI engine wrapper
    # This is a placeholder showing the interface
    
    class MyAIEngine:
        def is_available(self):
            return {"any": True}
        
        def generate_completion(self, prompt):
            # Call your AI API here
            return "AI response..."
    
    ai_engine = MyAIEngine()
    
    engine = EnhancedDefinitionEngine(
        vault_path=vault_path,
        ai_engine=ai_engine
    )
    
    engine.full_index()
    
    # AI-powered drift detection
    drift_report = engine.check_drift("def-coherence")
    
    print(f"Drifts detected: {drift_report['total_drifts']}")


def main():
    """Run all examples."""
    examples = [
        ("Basic Processing", example_1_basic_processing),
        ("Custom Configuration", example_2_custom_configuration),
        ("Single Definition", example_3_single_definition),
        ("Generate Notes", example_4_generate_notes),
        ("Structure Builder", example_5_structure_builder),
        ("Provenance Tracking", example_6_provenance_tracking),
        ("Drift Analysis", example_7_drift_analysis),
        ("AI Integration", example_8_ai_integration),
    ]
    
    print("\nDefinition 2.0 Examples")
    print("=" * 70)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nTo run an example, uncomment it in the code below:")
    print("=" * 70)
    
    # Uncomment the example you want to run:
    
    # example_1_basic_processing()
    # example_2_custom_configuration()
    # example_3_single_definition()
    # example_4_generate_notes()
    # example_5_structure_builder()
    # example_6_provenance_tracking()
    # example_7_drift_analysis()
    # example_8_ai_integration()


if __name__ == "__main__":
    main()
