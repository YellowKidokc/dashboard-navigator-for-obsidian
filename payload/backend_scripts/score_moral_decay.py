"""
Score the entire Moral Decay of America project using the unified coherence scorer.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.coherence.unified_scorer import UnifiedCoherenceScorer

def collect_markdown_files(base_path: str) -> list[tuple[str, str]]:
    """Collect all markdown files from the Moral Decay project."""
    files = []
    base = Path(base_path)
    
    # Priority folders for theoretical content
    priority_folders = [
        "04_Theoretical_Framework",
        "02_Introductions", 
        "06_Methodology",
        "11_Amish_Control_Group",
        "13_Social_Physics",
    ]
    
    for folder in priority_folders:
        folder_path = base / folder
        if folder_path.exists():
            for md_file in folder_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    files.append((md_file.name, content))
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
    
    return files

def main():
    # Path to Moral Decay project
    project_path = r"O:\_THEO\THEO\TM SUBSTACK\TM SUBSTACK\03_PUBLICATIONS\TRANS_DOMAIN_UNITY\The_Moral_Decay_of_America_Project"
    
    print("=" * 80)
    print("UNIFIED COHERENCE SCORER - MORAL DECAY OF AMERICA PROJECT")
    print("=" * 80)
    print()
    
    # Initialize scorer
    rubrics_path = Path(__file__).parent / "core" / "coherence" / "rubrics"
    scorer = UnifiedCoherenceScorer(rubrics_path=str(rubrics_path))
    
    # Collect files
    print("Collecting markdown files...")
    files = collect_markdown_files(project_path)
    print(f"Found {len(files)} files in priority folders")
    print()
    
    # Aggregate all content
    print("Aggregating content...")
    all_content = []
    file_list = []
    for filename, content in files:
        if len(content) > 500:  # Skip very short files
            all_content.append(f"\n\n--- {filename} ---\n\n{content}")
            file_list.append(filename)
    
    combined_text = "\n".join(all_content)
    print(f"Total content: {len(combined_text):,} characters")
    print(f"Files included: {len(file_list)}")
    print()
    
    # Score the combined corpus
    print("Running unified scorer...")
    print("-" * 80)
    result = scorer.score_document(combined_text, "The Moral Decay of America Project (Combined)")
    
    # Generate and save report
    report = scorer.generate_report(result)
    
    # Save to file to avoid console encoding issues
    output_file = Path(__file__).parent / "moral_decay_score_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n[OK] Full report saved to: {output_file}")
    
    # Print summary to console (ASCII-safe)
    print(f"\nSUMMARY:")
    print(f"  Coherence (chi): {result.chi:.2f}/10")
    print(f"  Confidence (kappa): {result.kappa:.2%}")
    print(f"  Robustness (rho): {result.rho:.2%}")
    print(f"  Triad - Polis: {result.triad.pi:.2f}")
    print(f"  Triad - Anthropos: {result.triad.a:.2f}")
    print(f"  Triad - Logos: {result.triad.lambda_:.2f}")
    
    # Also score individual key papers
    print("\n" + "=" * 80)
    print("INDIVIDUAL PAPER SCORES")
    print("=" * 80)
    
    key_papers = [
        "P 01 THE PHYSICS OF COHERENCE.md",
        "P 02 The Variable Substitution.md",
        "P 03 The Nine Domains of Social Coherence.md",
        "P 04 The Empirical Evidence.md",
        "P 05 Implications and Falsifiability.md",
        "FORMAL_THESIS_Moral_Coherence_Analysis.md",
        "Moral_Collapse_Framework.md",
        "Moral_Decline_America_FACTS_Paper.md",
    ]
    
    individual_scores = []
    for filename, content in files:
        if filename in key_papers:
            r = scorer.score_document(content, filename)
            individual_scores.append((filename, r.chi, r.kappa, r.rho, r.triad.pi, r.triad.a, r.triad.lambda_))
    
    # Sort by chi score
    individual_scores.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n{'Paper':<50} {'Chi':>6} {'Kappa':>6} {'Rho':>6} {'Pi':>6} {'A':>6} {'Lambda':>6}")
    print("-" * 86)
    for name, chi, kappa, rho, pi, a, lam in individual_scores:
        short_name = name[:47] + "..." if len(name) > 50 else name
        print(f"{short_name:<50} {chi:>6.2f} {kappa:>6.2f} {rho:>6.2f} {pi:>6.2f} {a:>6.2f} {lam:>6.2f}")
    
    print("\n" + "=" * 80)
    print("SCORING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
