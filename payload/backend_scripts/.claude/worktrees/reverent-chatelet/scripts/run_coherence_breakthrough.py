"""
Coherence Factor & Breakthrough Factor Analysis
Based on the Lowe Coherence Lagrangian metrics.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.tag_analytics_engine import TagAnalyticsEngine
from collections import Counter, defaultdict
from datetime import datetime
import re


# Coherence indicators (tags that signal coherent structure)
COHERENCE_TAGS = [
    "#coherence", "#unity", "#order", "#structure", "#harmony",
    "#integration", "#synthesis", "#connection", "#pattern", "#law",
    "#logos", "#trinity", "#balance", "#equilibrium"
]

# Entropy/disorder indicators
ENTROPY_TAGS = [
    "#entropy", "#chaos", "#disorder", "#noise", "#decay",
    "#fragmentation", "#contradiction", "#confusion", "#sin", "#fall"
]

# Grace/negentropy indicators (external restoration)
GRACE_TAGS = [
    "#grace", "#negentropy", "#restoration", "#redemption", "#healing",
    "#resurrection", "#renewal", "#salvation", "#miracle", "#intervention"
]

# Breakthrough indicators (paradigm shifts, insights)
BREAKTHROUGH_TAGS = [
    "#breakthrough", "#insight", "#discovery", "#revelation", "#eureka",
    "#paradigm", "#shift", "#unification", "#proof", "#solution",
    "#master-equation", "#unified", "#synthesis"
]

# Ten Laws coverage
TEN_LAWS_TAGS = {
    "Law1_Gravity": ["#gravity", "#sin", "#fall", "#attraction"],
    "Law2_Motion": ["#momentum", "#motion", "#force", "#inertia"],
    "Law3_Conservation": ["#conservation", "#transformation", "#eternal", "#energy"],
    "Law4_Entropy": ["#entropy", "#thermodynamics", "#decay", "#disorder"],
    "Law5_Light": ["#light", "#truth", "#electromagnetic", "#revelation"],
    "Law6_Causality": ["#causality", "#sowing", "#reaping", "#consequence"],
    "Law7_Grace": ["#grace", "#negentropy", "#open-system", "#external"],
    "Law8_Quantum": ["#quantum", "#faith", "#observer", "#measurement"],
    "Law9_Relativity": ["#relativity", "#perspective", "#frame", "#spacetime"],
    "Law10_Consciousness": ["#consciousness", "#soul", "#awareness", "#witness"]
}


def compute_coherence_factor(engine: TagAnalyticsEngine) -> dict:
    """
    Compute Lowe Coherence Factor.
    
    Components:
    1. Tag Concentration - how focused vs scattered
    2. Co-occurrence Density - how connected concepts are
    3. Law Coverage - how many of 10 Laws are represented
    4. Grace-Entropy Ratio - redemptive vs entropic content
    5. Trinity Balance - Father/Son/Spirit distribution
    """
    
    results = {}
    
    # 1. Tag Concentration (fewer dominant tags = more coherent)
    freq = engine.compute_tag_frequency()
    total_uses = sum(freq.values())
    if total_uses > 0:
        top_10_share = sum(c for _, c in freq.most_common(10)) / total_uses
        top_5_share = sum(c for _, c in freq.most_common(5)) / total_uses
    else:
        top_10_share = 0
        top_5_share = 0
    
    results["tag_concentration"] = {
        "top_5_share": round(top_5_share, 3),
        "top_10_share": round(top_10_share, 3),
        "unique_tags": len(freq),
        "total_uses": total_uses
    }
    
    # 2. Co-occurrence Density
    cooc = engine.compute_cooccurrence()
    if cooc:
        avg_cooc = sum(cooc.values()) / len(cooc)
        max_cooc = max(cooc.values())
        density = len(cooc) / max(len(freq) * (len(freq) - 1) / 2, 1)
    else:
        avg_cooc = 0
        max_cooc = 0
        density = 0
    
    results["cooccurrence"] = {
        "total_pairs": len(cooc),
        "avg_strength": round(avg_cooc, 2),
        "max_strength": max_cooc,
        "density": round(density, 4)
    }
    
    # 3. Law Coverage Score
    laws_covered = 0
    law_details = {}
    for law_name, law_tags in TEN_LAWS_TAGS.items():
        law_count = sum(freq.get(f"#{t.strip('#')}", 0) for t in law_tags)
        law_details[law_name] = law_count
        if law_count > 0:
            laws_covered += 1
    
    results["law_coverage"] = {
        "laws_covered": laws_covered,
        "coverage_pct": round(laws_covered / 10, 2),
        "by_law": law_details
    }
    
    # 4. Grace-Entropy Ratio
    grace_count = sum(freq.get(f"#{t.strip('#')}", 0) for t in GRACE_TAGS)
    entropy_count = sum(freq.get(f"#{t.strip('#')}", 0) for t in ENTROPY_TAGS)
    coherence_count = sum(freq.get(f"#{t.strip('#')}", 0) for t in COHERENCE_TAGS)
    
    if entropy_count > 0:
        grace_entropy_ratio = grace_count / entropy_count
    else:
        grace_entropy_ratio = grace_count if grace_count > 0 else 1.0
    
    results["grace_entropy"] = {
        "grace_tags": grace_count,
        "entropy_tags": entropy_count,
        "coherence_tags": coherence_count,
        "ratio": round(grace_entropy_ratio, 2)
    }
    
    # 5. Overall Coherence Score (weighted)
    coherence_score = (
        top_5_share * 0.20 +                    # Tag focus
        min(density * 10, 1.0) * 0.15 +         # Connection density
        (laws_covered / 10) * 0.25 +            # Law coverage
        min(grace_entropy_ratio / 2, 1.0) * 0.20 +  # Grace dominance
        min(coherence_count / 50, 1.0) * 0.20   # Explicit coherence
    )
    
    results["overall_coherence"] = round(coherence_score, 3)
    
    # Letter grade
    if coherence_score >= 0.9:
        grade = "A"
    elif coherence_score >= 0.8:
        grade = "B"
    elif coherence_score >= 0.7:
        grade = "C"
    elif coherence_score >= 0.6:
        grade = "D"
    else:
        grade = "F"
    
    results["grade"] = grade
    
    return results


def compute_breakthrough_factor(engine: TagAnalyticsEngine) -> dict:
    """
    Compute Breakthrough Factor.
    
    Detects:
    1. Breakthrough tag presence
    2. Concept integration moments (many tags converging)
    3. Novel combinations (rare co-occurrences)
    4. Velocity spikes (sudden emergence)
    """
    
    results = {}
    freq = engine.compute_tag_frequency()
    cooc = engine.compute_cooccurrence()
    velocity = engine.compute_tag_velocity(days=30)
    
    # 1. Explicit breakthrough tags
    breakthrough_count = sum(freq.get(f"#{t.strip('#')}", 0) for t in BREAKTHROUGH_TAGS)
    results["explicit_breakthroughs"] = breakthrough_count
    
    # 2. Integration moments (notes with 10+ unique tags)
    high_integration_notes = []
    for note in engine.notes:
        unique_tags = len(set(note.tags))
        if unique_tags >= 10:
            high_integration_notes.append({
                "path": note.path,
                "tag_count": unique_tags,
                "tags": note.tags[:15]
            })
    
    results["integration_moments"] = {
        "count": len(high_integration_notes),
        "notes": high_integration_notes[:10]
    }
    
    # 3. Novel combinations (co-occurrences that appear only 1-2 times)
    rare_pairs = [(pair, count) for pair, count in cooc.items() if count <= 2]
    results["novel_combinations"] = {
        "count": len(rare_pairs),
        "examples": rare_pairs[:10]
    }
    
    # 4. Velocity spikes (tags with high positive velocity)
    emerging = [(tag, vel) for tag, vel in velocity.items() if vel > 0.5]
    emerging.sort(key=lambda x: x[1], reverse=True)
    
    results["velocity_spikes"] = {
        "count": len(emerging),
        "top_emerging": emerging[:10]
    }
    
    # 5. Cross-domain bridges (tags that connect different law domains)
    bridges = []
    for (tag_a, tag_b), count in cooc.most_common(50):
        domain_a = None
        domain_b = None
        for law, tags in TEN_LAWS_TAGS.items():
            if any(t in tag_a for t in tags):
                domain_a = law
            if any(t in tag_b for t in tags):
                domain_b = law
        if domain_a and domain_b and domain_a != domain_b:
            bridges.append({
                "pair": (tag_a, tag_b),
                "domains": (domain_a, domain_b),
                "strength": count
            })
    
    results["cross_domain_bridges"] = bridges[:10]
    
    # 6. Overall Breakthrough Score
    breakthrough_score = (
        min(breakthrough_count / 20, 1.0) * 0.25 +
        min(len(high_integration_notes) / 10, 1.0) * 0.25 +
        min(len(emerging) / 20, 1.0) * 0.25 +
        min(len(bridges) / 10, 1.0) * 0.25
    )
    
    results["breakthrough_score"] = round(breakthrough_score, 3)
    
    return results


def run_full_analysis(vault_path: str):
    """Run complete coherence and breakthrough analysis."""
    
    print("="*60)
    print("COHERENCE & BREAKTHROUGH ANALYSIS")
    print("="*60)
    
    engine = TagAnalyticsEngine(vault_path)
    engine.load_vault(max_notes=1000)
    engine.build_tag_metrics()
    
    # Coherence
    print("\n## COHERENCE FACTOR\n")
    coherence = compute_coherence_factor(engine)
    
    print(f"**Overall Coherence Score:** {coherence['overall_coherence']:.1%} (Grade: {coherence['grade']})")
    print(f"\n### Components:")
    print(f"- Tag Concentration (top 5): {coherence['tag_concentration']['top_5_share']:.1%}")
    print(f"- Co-occurrence Density: {coherence['cooccurrence']['density']:.2%}")
    print(f"- Law Coverage: {coherence['law_coverage']['laws_covered']}/10 ({coherence['law_coverage']['coverage_pct']:.0%})")
    print(f"- Grace-Entropy Ratio: {coherence['grace_entropy']['ratio']:.2f}")
    print(f"  - Grace tags: {coherence['grace_entropy']['grace_tags']}")
    print(f"  - Entropy tags: {coherence['grace_entropy']['entropy_tags']}")
    
    print("\n### Law Coverage Detail:")
    for law, count in coherence['law_coverage']['by_law'].items():
        status = "✅" if count > 0 else "❌"
        print(f"  {status} {law}: {count}")
    
    # Breakthrough
    print("\n" + "="*60)
    print("\n## BREAKTHROUGH FACTOR\n")
    breakthrough = compute_breakthrough_factor(engine)
    
    print(f"**Breakthrough Score:** {breakthrough['breakthrough_score']:.1%}")
    print(f"\n### Components:")
    print(f"- Explicit Breakthrough Tags: {breakthrough['explicit_breakthroughs']}")
    print(f"- High Integration Notes (10+ tags): {breakthrough['integration_moments']['count']}")
    print(f"- Velocity Spikes: {breakthrough['velocity_spikes']['count']}")
    print(f"- Cross-Domain Bridges: {len(breakthrough['cross_domain_bridges'])}")
    
    if breakthrough['integration_moments']['notes']:
        print("\n### High Integration Notes:")
        for note in breakthrough['integration_moments']['notes'][:5]:
            print(f"  - [[{note['path']}]] ({note['tag_count']} tags)")
    
    if breakthrough['velocity_spikes']['top_emerging']:
        print("\n### Emerging Concepts (velocity spikes):")
        for tag, vel in breakthrough['velocity_spikes']['top_emerging'][:5]:
            print(f"  - {tag}: +{vel:.2f}/day")
    
    if breakthrough['cross_domain_bridges']:
        print("\n### Cross-Domain Bridges:")
        for bridge in breakthrough['cross_domain_bridges'][:5]:
            print(f"  - {bridge['pair'][0]} ↔ {bridge['pair'][1]}")
            print(f"    ({bridge['domains'][0]} ↔ {bridge['domains'][1]}, strength: {bridge['strength']})")
    
    # Generate Report
    report = f"""---
type: coherence-breakthrough-analysis
generated: "{datetime.now().isoformat()}"
coherence_score: {coherence['overall_coherence']}
coherence_grade: "{coherence['grade']}"
breakthrough_score: {breakthrough['breakthrough_score']}
---

# Coherence & Breakthrough Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Coherence Factor

| Metric | Value |
|--------|-------|
| **Overall Score** | {coherence['overall_coherence']:.1%} |
| **Grade** | {coherence['grade']} |
| Tag Concentration | {coherence['tag_concentration']['top_5_share']:.1%} |
| Co-occurrence Density | {coherence['cooccurrence']['density']:.2%} |
| Law Coverage | {coherence['law_coverage']['laws_covered']}/10 |
| Grace-Entropy Ratio | {coherence['grace_entropy']['ratio']:.2f} |

### Grace-Entropy Balance
- Grace/Negentropy Tags: {coherence['grace_entropy']['grace_tags']}
- Entropy/Disorder Tags: {coherence['grace_entropy']['entropy_tags']}
- Coherence Tags: {coherence['grace_entropy']['coherence_tags']}

### Ten Laws Coverage
"""
    for law, count in coherence['law_coverage']['by_law'].items():
        status = "✅" if count > 0 else "❌"
        report += f"- {status} **{law}**: {count}\n"
    
    report += f"""

## Breakthrough Factor

| Metric | Value |
|--------|-------|
| **Breakthrough Score** | {breakthrough['breakthrough_score']:.1%} |
| Explicit Breakthrough Tags | {breakthrough['explicit_breakthroughs']} |
| High Integration Notes | {breakthrough['integration_moments']['count']} |
| Velocity Spikes | {breakthrough['velocity_spikes']['count']} |
| Cross-Domain Bridges | {len(breakthrough['cross_domain_bridges'])} |

### High Integration Notes (10+ tags)
"""
    for note in breakthrough['integration_moments']['notes'][:10]:
        report += f"- [[{note['path']}]] ({note['tag_count']} tags)\n"
    
    report += "\n### Emerging Concepts\n"
    for tag, vel in breakthrough['velocity_spikes']['top_emerging'][:10]:
        report += f"- **{tag}**: +{vel:.2f}/day\n"
    
    report += "\n---\n*Auto-generated Coherence & Breakthrough Analysis*\n"
    
    # Save
    output_path = Path(vault_path) / "_TAG_NOTES" / "COHERENCE_BREAKTHROUGH_ANALYSIS.md"
    output_path.write_text(report, encoding='utf-8')
    print(f"\n📄 Report saved to {output_path}")
    
    return {"coherence": coherence, "breakthrough": breakthrough}


if __name__ == "__main__":
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    results = run_full_analysis(vault)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print(f"Coherence: {results['coherence']['overall_coherence']:.1%} ({results['coherence']['grade']})")
    print(f"Breakthrough: {results['breakthrough']['breakthrough_score']:.1%}")
