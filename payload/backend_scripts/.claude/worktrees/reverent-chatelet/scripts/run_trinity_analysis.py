"""
Trinity Analysis
Analyzes tag patterns related to the Trinity (Father, Son, Spirit)
and triadic closure in the vault.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tag_analytics_engine import TagAnalyticsEngine
from collections import Counter
from datetime import datetime


# Trinity tag groups
TRINITY_TAGS = {
    "Father": ["#father", "#god-the-father", "#source", "#origin", "#i-am", "#creator", "#alpha"],
    "Son": ["#son", "#jesus", "#christ", "#logos", "#word", "#form", "#measurement", "#incarnation"],
    "Spirit": ["#spirit", "#holy-spirit", "#coherence", "#unity", "#breath", "#ruach", "#pneuma"]
}

TRIADIC_PATTERNS = {
    "Triadic Closure": ["#trinity", "#triadic", "#three-in-one", "#triune"],
    "Balance": ["#balance", "#equilibrium", "#harmony"],
    "Unity": ["#unity", "#oneness", "#coherence"]
}


def run_trinity_analysis(vault_path: str):
    """Run Trinity-focused tag analysis."""
    
    print("="*60)
    print("TRINITY TAG ANALYSIS")
    print("="*60)
    
    engine = TagAnalyticsEngine(vault_path)
    engine.load_vault(max_notes=1000)
    engine.build_tag_metrics()
    engine.compute_cooccurrence()
    
    # Count Trinity tags
    print("\n## Trinity Tag Distribution\n")
    
    trinity_counts = {"Father": 0, "Son": 0, "Spirit": 0}
    trinity_notes = {"Father": [], "Son": [], "Spirit": []}
    
    for note in engine.notes:
        note_tags = set(note.tags)
        for person, tags in TRINITY_TAGS.items():
            for tag in tags:
                if tag in note_tags:
                    trinity_counts[person] += 1
                    if note.path not in trinity_notes[person]:
                        trinity_notes[person].append(note.path)
                    break
    
    total = sum(trinity_counts.values()) or 1
    
    print("| Person | Count | % | Notes |")
    print("|--------|-------|---|-------|")
    for person, count in trinity_counts.items():
        pct = (count / total) * 100
        notes_count = len(trinity_notes[person])
        print(f"| {person} | {count} | {pct:.1f}% | {notes_count} |")
    
    # Trinity Balance Score
    values = list(trinity_counts.values())
    if max(values) > 0:
        balance = min(values) / max(values)
    else:
        balance = 0
    
    print(f"\n**Trinity Balance Score:** {balance:.1%}")
    if balance > 0.7:
        print("✅ Good balance across Father, Son, Spirit")
    elif balance > 0.4:
        print("⚠️ Moderate imbalance - some aspects underrepresented")
    else:
        print("❌ Significant imbalance - review Trinity coverage")
    
    # Co-occurrence with Trinity tags
    print("\n## Trinity Co-occurrences\n")
    print("What concepts appear WITH Trinity tags:\n")
    
    for person, tags in TRINITY_TAGS.items():
        print(f"### {person}")
        coocs = Counter()
        for tag in tags:
            if tag in engine.tag_metrics:
                for co_tag, count in engine.tag_metrics[tag].co_occurs_with.items():
                    if co_tag not in tags:  # Don't count self-group
                        coocs[co_tag] += count
        
        for tag, count in coocs.most_common(5):
            print(f"  - {tag}: {count}")
        print()
    
    # Triadic Closure Check
    print("\n## Triadic Closure Analysis\n")
    
    notes_with_all_three = []
    notes_with_two = []
    notes_with_one = []
    
    for note in engine.notes:
        note_tags = set(note.tags)
        persons_present = 0
        
        for person, tags in TRINITY_TAGS.items():
            if any(t in note_tags for t in tags):
                persons_present += 1
        
        if persons_present == 3:
            notes_with_all_three.append(note.path)
        elif persons_present == 2:
            notes_with_two.append(note.path)
        elif persons_present == 1:
            notes_with_one.append(note.path)
    
    print(f"- **All Three Persons:** {len(notes_with_all_three)} notes (complete triadic closure)")
    print(f"- **Two Persons:** {len(notes_with_two)} notes (partial)")
    print(f"- **One Person:** {len(notes_with_one)} notes (isolated)")
    
    if notes_with_all_three:
        print("\n### Notes with Complete Trinity:")
        for path in notes_with_all_three[:10]:
            print(f"  - [[{path}]]")
        if len(notes_with_all_three) > 10:
            print(f"  - ... and {len(notes_with_all_three) - 10} more")
    
    # Generate Report
    report = f"""---
type: trinity-analysis
generated: "{datetime.now().isoformat()}"
balance_score: {balance:.3f}
---

# Trinity Tag Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Trinity Distribution

| Person | Count | Percentage |
|--------|-------|------------|
| Father | {trinity_counts['Father']} | {(trinity_counts['Father']/total)*100:.1f}% |
| Son | {trinity_counts['Son']} | {(trinity_counts['Son']/total)*100:.1f}% |
| Spirit | {trinity_counts['Spirit']} | {(trinity_counts['Spirit']/total)*100:.1f}% |

**Balance Score:** {balance:.1%}

## Triadic Closure

- **Complete (all 3):** {len(notes_with_all_three)} notes
- **Partial (2 of 3):** {len(notes_with_two)} notes  
- **Isolated (1 of 3):** {len(notes_with_one)} notes

## Notes with Complete Trinity Representation

"""
    for path in notes_with_all_three[:20]:
        report += f"- [[{path}]]\n"
    
    report += "\n---\n*Auto-generated Trinity Analysis*\n"
    
    # Save report
    output_path = Path(vault_path) / "_TAG_NOTES" / "TRINITY_ANALYSIS.md"
    output_path.write_text(report, encoding='utf-8')
    print(f"\n📄 Report saved to {output_path}")
    
    return {
        "balance": balance,
        "counts": trinity_counts,
        "complete_trinity": len(notes_with_all_three),
        "partial": len(notes_with_two),
        "isolated": len(notes_with_one)
    }


if __name__ == "__main__":
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    results = run_trinity_analysis(vault)
    
    print("\n" + "="*60)
    print("TRINITY ANALYSIS COMPLETE")
    print("="*60)
    print(f"Balance: {results['balance']:.1%}")
    print(f"Complete Trinity Notes: {results['complete_trinity']}")
