"""
Score all Adam and Eve papers using unified_scorer.py
Generates individual reports + comparison summary
"""

import sys
import json
import io
from pathlib import Path
from unified_scorer import UnifiedCoherenceScorer

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    """Score all Adam and Eve papers"""
    
    # Paper directory
    papers_dir = Path(r"O:\_Theophysics_v3\02_THEOPHYSICS\Theological\Adam and Eve")
    output_dir = Path(r"O:\_Theophysics_v3\00_SYSTEM\01_ENGINE\scripts\from_Note\outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize scorer
    print("Initializing unified scorer...")
    scorer = UnifiedCoherenceScorer()
    
    # Get all markdown files
    papers = sorted(papers_dir.glob("*.md"))
    
    if not papers:
        print(f"[X] No papers found in {papers_dir}")
        return 1
    
    print(f"\nFound {len(papers)} papers to score\n")
    print("=" * 80)
    
    # Score each paper
    results = []
    
    for paper_path in papers:
        print(f"\nScoring: {paper_path.name}")
        print("-" * 80)
        
        try:
            # Read paper
            with open(paper_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Score it
            result = scorer.score_document(text, title=paper_path.stem)
            
            # Generate individual report
            report = scorer.generate_report(result, title=paper_path.stem)
            
            # Save individual report
            report_path = output_dir / f"{paper_path.stem}_report.txt"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Save JSON
            json_path = output_dir / f"{paper_path.stem}_scores.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2)
            
            # Print summary
            print(f"  χ = {result.chi:.1f}  |  κ = {result.kappa:.2f}  |  ρ = {result.rho:.2f}")
            print(f"  Metrics: {result.metrics_count}  |  Evidence: {result.evidence_units_count}")
            
            if result.vetoes_applied:
                print(f"  [!] Vetoes: {len(result.vetoes_applied)}")
            
            if result.warnings:
                print(f"  [!] Warnings: {len(result.warnings)}")
            
            # Store for comparison
            results.append({
                'title': paper_path.stem,
                'chi': result.chi,
                'kappa': result.kappa,
                'rho': result.rho,
                'triad_pi': result.triad.pi,
                'triad_a': result.triad.a,
                'triad_lambda': result.triad.lambda_,
                'metrics_count': result.metrics_count,
                'evidence_count': result.evidence_units_count,
                'vetoes': len(result.vetoes_applied),
                'warnings': len(result.warnings),
                'result': result
            })
            
            print(f"  [OK] Saved: {report_path.name}")
            
        except Exception as e:
            print(f"  [X] Error: {e}")
            continue
    
    # Generate comparison summary
    print("\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    if not results:
        print("[X] No papers successfully scored")
        return 1
    
    # Sort by chi
    results_sorted = sorted(results, key=lambda x: x['chi'], reverse=True)
    
    # Table header
    print(f"\n{'Rank':<6}{'Paper':<40}{'χ':<8}{'κ':<8}{'ρ':<8}{'Π':<8}{'A':<8}{'Λ':<8}")
    print("-" * 88)
    
    # Table rows
    for i, r in enumerate(results_sorted, 1):
        title_short = r['title'][:37] + "..." if len(r['title']) > 40 else r['title']
        print(f"{i:<6}{title_short:<40}{r['chi']:<8.1f}{r['kappa']:<8.2f}{r['rho']:<8.2f}"
              f"{r['triad_pi']:<8.2f}{r['triad_a']:<8.2f}{r['triad_lambda']:<8.2f}")
    
    # Statistics
    print("\n" + "-" * 88)
    avg_chi = sum(r['chi'] for r in results) / len(results)
    avg_kappa = sum(r['kappa'] for r in results) / len(results)
    avg_rho = sum(r['rho'] for r in results) / len(results)
    
    print(f"{'AVG':<6}{'':<40}{avg_chi:<8.1f}{avg_kappa:<8.2f}{avg_rho:<8.2f}")
    
    max_chi = max(results, key=lambda x: x['chi'])
    min_chi = min(results, key=lambda x: x['chi'])
    
    print(f"\nBest:  {max_chi['title']} (chi = {max_chi['chi']:.1f})")
    print(f"Worst: {min_chi['title']} (chi = {min_chi['chi']:.1f})")
    print(f"Range: {max_chi['chi'] - min_chi['chi']:.1f} points")
    
    # Save comparison CSV
    csv_path = output_dir / "adam_eve_comparison.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("Rank,Title,Chi,Kappa,Rho,Pi,A,Lambda,Metrics,Evidence,Vetoes,Warnings\n")
        for i, r in enumerate(results_sorted, 1):
            f.write(f"{i},\"{r['title']}\",{r['chi']:.2f},{r['kappa']:.2f},{r['rho']:.2f},"
                   f"{r['triad_pi']:.2f},{r['triad_a']:.2f},{r['triad_lambda']:.2f},"
                   f"{r['metrics_count']},{r['evidence_count']},{r['vetoes']},{r['warnings']}\n")
    
    print(f"\n[OK] Comparison saved: {csv_path}")
    
    # Detailed fruit analysis
    print("\n" + "=" * 80)
    print("FRUIT ANALYSIS ACROSS PAPERS")
    print("=" * 80)
    
    # Collect all fruit scores
    fruit_totals = {}
    for r in results:
        for fruit in r['result'].fruits:
            if fruit.code not in fruit_totals:
                fruit_totals[fruit.code] = {'name': fruit.name, 'scores': []}
            fruit_totals[fruit.code]['scores'].append(fruit.net)
    
    # Compute averages
    fruit_avgs = []
    for code, data in fruit_totals.items():
        avg = sum(data['scores']) / len(data['scores'])
        fruit_avgs.append({'code': code, 'name': data['name'], 'avg': avg})
    
    # Sort by average
    fruit_avgs.sort(key=lambda x: x['avg'], reverse=True)
    
    print(f"\n{'Rank':<6}{'Fruit':<20}{'Avg Net':<12}{'Bar'}")
    print("-" * 60)
    
    for i, f in enumerate(fruit_avgs, 1):
        bar_len = int(abs(f['avg']) * 20)
        bar = "█" * bar_len if f['avg'] >= 0 else "░" * bar_len
        print(f"{i:<6}{f['name']:<20}{f['avg']:+.3f}        {bar}")
    
    print("\n" + "=" * 80)
    print(f"[OK] All reports saved to: {output_dir}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
