#!/usr/bin/env python3
"""
Definition 2.0 System Validation Script
========================================
Validates that all components are properly integrated and coherent.
"""

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_status(message, status='info'):
    """Print colored status message."""
    if status == 'pass':
        print(f"{GREEN}✓{RESET} {message}")
    elif status == 'fail':
        print(f"{RED}✗{RESET} {message}")
    elif status == 'warn':
        print(f"{YELLOW}⚠{RESET} {message}")
    else:
        print(f"{BLUE}ℹ{RESET} {message}")

def validate_imports():
    """Validate all imports work."""
    print("\n" + "="*70)
    print("1. IMPORT VALIDATION")
    print("="*70)
    
    tests = []
    
    # Test 1: Enhanced Definition Engine
    try:
        from engine.enhanced_definition_engine import (
            VaultIndexer, DriftDetector, ExternalComparator,
            EnhancedDefinitionEngine
        )
        print_status("Enhanced Definition Engine imports", 'pass')
        tests.append(True)
    except Exception as e:
        print_status(f"Enhanced Definition Engine imports: {e}", 'fail')
        tests.append(False)
    
    # Test 2: Knowledge Acquisition Engine
    try:
        from engine.knowledge_acquisition_engine import (
            SourceLookup, ContentDownloader, EnhancedEntityExtractor
        )
        print_status("Knowledge Acquisition Engine imports", 'pass')
        tests.append(True)
    except Exception as e:
        print_status(f"Knowledge Acquisition Engine imports: {e}", 'fail')
        tests.append(False)
    
    # Test 3: Structure Engine
    try:
        from engine.structure_engine import StructureEngine
        print_status("Structure Engine imports", 'pass')
        tests.append(True)
    except Exception as e:
        print_status(f"Structure Engine imports: {e}", 'fail')
        tests.append(False)
    
    # Test 4: Definition Processor V2
    try:
        from engine.definition_processor_v2 import (
            DefinitionProcessorV2, ProvenanceEntry, ProcessedDefinition
        )
        print_status("Definition Processor V2 imports", 'pass')
        tests.append(True)
    except Exception as e:
        print_status(f"Definition Processor V2 imports: {e}", 'fail')
        tests.append(False)
    
    return all(tests)

def validate_dependencies():
    """Validate external dependencies."""
    print("\n" + "="*70)
    print("2. DEPENDENCY VALIDATION")
    print("="*70)
    
    tests = []
    
    # Required dependencies
    required = [
        ('requests', 'HTTP requests'),
        ('yaml', 'YAML parsing'),
    ]
    
    for module, desc in required:
        try:
            __import__(module)
            print_status(f"{desc} ({module})", 'pass')
            tests.append(True)
        except ImportError:
            print_status(f"{desc} ({module}) - MISSING", 'fail')
            tests.append(False)
    
    # Optional dependencies
    optional = [
        ('bs4', 'BeautifulSoup (web scraping)'),
        ('markdownify', 'HTML to Markdown'),
        ('fitz', 'PyMuPDF (PDF processing)'),
    ]
    
    for module, desc in optional:
        try:
            __import__(module)
            print_status(f"{desc} ({module})", 'pass')
        except ImportError:
            print_status(f"{desc} ({module}) - Optional, not installed", 'warn')
    
    return all(tests)

def validate_configuration():
    """Validate configuration consistency."""
    print("\n" + "="*70)
    print("3. CONFIGURATION VALIDATION")
    print("="*70)
    
    tests = []
    
    try:
        from engine.definition_processor_v2 import MIN_CONFIDENCE, SOURCE_PRIORITY
        from engine.knowledge_acquisition_engine import SOURCE_PRIORITY as KA_PRIORITY
        
        # Check MIN_CONFIDENCE
        if MIN_CONFIDENCE == 0.90:
            print_status(f"MIN_CONFIDENCE = {MIN_CONFIDENCE}", 'pass')
            tests.append(True)
        else:
            print_status(f"MIN_CONFIDENCE = {MIN_CONFIDENCE} (expected 0.90)", 'fail')
            tests.append(False)
        
        # Check SOURCE_PRIORITY consistency
        if SOURCE_PRIORITY == KA_PRIORITY:
            print_status("SOURCE_PRIORITY consistent across modules", 'pass')
            tests.append(True)
        else:
            print_status("SOURCE_PRIORITY mismatch between modules", 'fail')
            tests.append(False)
        
        # Check priority values
        if SOURCE_PRIORITY.get("Stanford Encyclopedia of Philosophy") == 1:
            print_status("SEP has highest priority (1)", 'pass')
            tests.append(True)
        else:
            print_status("SEP priority incorrect", 'fail')
            tests.append(False)
        
        if SOURCE_PRIORITY.get("Wikipedia") == 7:
            print_status("Wikipedia has lowest priority (7)", 'pass')
            tests.append(True)
        else:
            print_status("Wikipedia priority incorrect", 'fail')
            tests.append(False)
    
    except Exception as e:
        print_status(f"Configuration validation error: {e}", 'fail')
        tests.append(False)
    
    return all(tests)

def validate_file_structure():
    """Validate file structure."""
    print("\n" + "="*70)
    print("4. FILE STRUCTURE VALIDATION")
    print("="*70)
    
    tests = []
    
    required_files = [
        'engine/definition_processor_v2.py',
        'engine/enhanced_definition_engine.py',
        'engine/knowledge_acquisition_engine.py',
        'engine/structure_engine.py',
        'templates/definition_template.md',
        'prompts/definition_copilot_prompt.md',
        'DEFINITION_V2_README.md',
        'DEFINITION_V2_SUMMARY.md',
        'docs/DEFINITION_V2_GUIDE.md',
        'INTEGRATION_CHECKLIST.md',
        'requirements_v2.txt',
        'examples/process_definitions_example.py',
    ]
    
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print_status(f"{file_path}", 'pass')
            tests.append(True)
        else:
            print_status(f"{file_path} - MISSING", 'fail')
            tests.append(False)
    
    return all(tests)

def validate_template():
    """Validate definition template."""
    print("\n" + "="*70)
    print("5. TEMPLATE VALIDATION")
    print("="*70)
    
    tests = []
    
    template_path = Path('templates/definition_template.md')
    
    if not template_path.exists():
        print_status("Template file missing", 'fail')
        return False
    
    content = template_path.read_text(encoding='utf-8')
    
    # Check for required sections
    required_sections = [
        '## 1. Canonical Definition',
        '## 2. Axioms',
        '## 3. Mathematical Structure',
        '## 4. Domain Interpretations',
        '## 5. Operationalization',
        '## 6. Failure Modes',
        '## 7. Integration Map',
        '## 8. Usage Drift Log',
        '## 9. External Comparison',
        '## 10. Notes & Examples',
    ]
    
    for section in required_sections:
        if section in content:
            print_status(f"Section: {section}", 'pass')
            tests.append(True)
        else:
            print_status(f"Section missing: {section}", 'fail')
            tests.append(False)
    
    # Check for placeholders
    placeholders = ['{{TERM_SLUG}}', '{{SYMBOL}}', '{{NAME}}', '{{DATE}}']
    
    for placeholder in placeholders:
        if placeholder in content:
            print_status(f"Placeholder: {placeholder}", 'pass')
            tests.append(True)
        else:
            print_status(f"Placeholder missing: {placeholder}", 'fail')
            tests.append(False)
    
    return all(tests)

def validate_integration():
    """Validate integration points."""
    print("\n" + "="*70)
    print("6. INTEGRATION VALIDATION")
    print("="*70)
    
    tests = []
    
    try:
        from engine.definition_processor_v2 import DefinitionProcessorV2
        from pathlib import Path
        
        # Test instantiation
        processor = DefinitionProcessorV2(
            vault_path=Path("."),
            max_workers=2
        )
        print_status("DefinitionProcessorV2 instantiation", 'pass')
        tests.append(True)
        
        # Check attributes
        if hasattr(processor, 'enhanced_engine'):
            print_status("Has enhanced_engine attribute", 'pass')
            tests.append(True)
        else:
            print_status("Missing enhanced_engine attribute", 'fail')
            tests.append(False)
        
        if hasattr(processor, 'source_fetcher'):
            print_status("Has source_fetcher attribute", 'pass')
            tests.append(True)
        else:
            print_status("Missing source_fetcher attribute", 'fail')
            tests.append(False)
        
        if hasattr(processor, 'downloader'):
            print_status("Has downloader attribute", 'pass')
            tests.append(True)
        else:
            print_status("Missing downloader attribute", 'fail')
            tests.append(False)
    
    except Exception as e:
        print_status(f"Integration validation error: {e}", 'fail')
        tests.append(False)
    
    return all(tests)

def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("DEFINITION 2.0 SYSTEM VALIDATION")
    print("="*70)
    
    results = []
    
    # Run all validation tests
    results.append(('Imports', validate_imports()))
    results.append(('Dependencies', validate_dependencies()))
    results.append(('Configuration', validate_configuration()))
    results.append(('File Structure', validate_file_structure()))
    results.append(('Template', validate_template()))
    results.append(('Integration', validate_integration()))
    
    # Summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = 'pass' if passed else 'fail'
        print_status(f"{name}: {'PASS' if passed else 'FAIL'}", status)
    
    # Overall result
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print(f"{GREEN}✓ ALL TESTS PASSED - SYSTEM VALIDATED{RESET}")
        print("="*70)
        print("\nSystem is coherent and ready for production use.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements_v2.txt")
        print("  2. Test on small vault (3-5 definitions)")
        print("  3. Run on full vault")
        return 0
    else:
        print(f"{RED}✗ VALIDATION FAILED{RESET}")
        print("="*70)
        print("\nPlease fix the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
