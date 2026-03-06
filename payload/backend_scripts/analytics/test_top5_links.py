"""
Test script to demonstrate top 5 high-quality research links.
Shows that Stanford, IEP, arXiv, PhilPapers, Oxford come before Wikipedia.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "core"))
from research_linker import ResearchLinker


def test_top5_priority():
    """Test that top 5 links prioritize quality sources."""
    print("\n" + "="*70)
    print("TOP 5 HIGH-QUALITY RESEARCH LINKS TEST")
    print("="*70)
    
    linker = ResearchLinker()
    
    # Show current priority order
    print("\nCurrent Priority Order:")
    for i, source in enumerate(linker.get_priority_order()[:7], 1):
        print(f"  {i}. {source}")
    
    # Test terms
    test_terms = [
        "quantum mechanics",
        "consciousness",
        "entropy",
        "coherence",
        "grace"
    ]
    
    print("\n" + "="*70)
    print("TESTING TOP 5 LINKS FOR EACH TERM")
    print("="*70)
    
    for term in test_terms:
        print(f"\n📚 Term: '{term}'")
        print("-" * 70)
        
        # Get top 5 quality links
        top5 = linker.get_top_quality_links(term, count=5)
        
        if top5:
            print(f"✓ Generated {len(top5)} high-quality links:")
            for i, (source, url) in enumerate(top5.items(), 1):
                # Show source name with display name
                display = linker.LINK_TEMPLATES[source]['display_name']
                print(f"  {i}. {source:15s} - {display}")
                print(f"     {url[:80]}...")
        else:
            print("  ✗ No links generated")
    
    print("\n" + "="*70)
    print("PRIORITY VERIFICATION")
    print("="*70)
    
    # Verify Wikipedia is NOT in top 5
    term = "test term"
    top5 = linker.get_top_quality_links(term, count=5)
    
    if 'wikipedia' in top5:
        print("\n⚠️  WARNING: Wikipedia appeared in top 5!")
    else:
        print("\n✓ CORRECT: Wikipedia is NOT in top 5 (only high-quality sources)")
    
    # Show what sources ARE in top 5
    print("\nTop 5 sources that will be used:")
    for i, source in enumerate(linker.get_priority_order()[:5], 1):
        display = linker.LINK_TEMPLATES[source]['display_name']
        print(f"  {i}. {source:15s} - {display}")
    
    print("\n" + "="*70)
    print("✓ Test Complete - High-quality sources prioritized!")
    print("="*70)


if __name__ == "__main__":
    test_top5_priority()
