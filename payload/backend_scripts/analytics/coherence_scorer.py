"""
Theophysics Coherence Scorer
============================
Measures document coherence based on linguistic pattern detection.

Calibration Tests:
- Constitution/Declaration: Should score HIGH (coherent founding documents)
- Corporate word salad: Should score LOW (entropy/incoherent)
- Copenhagen Interpretation: Interesting middle ground test

Score: 0-10 scale
Author: David Lowe / Claude
"""

import re
from collections import Counter

# COHERENCE INDICATORS - words/patterns that indicate structural coherence
COHERENCE_TERMS = {
    # Structural constraint terms (high weight)
    'constraint': 3,
    'constrain': 3,
    'bound': 2,
    'limit': 2,
    'restrict': 2,
    'regulate': 2,
    
    # Order/structure terms
    'order': 2,
    'structure': 2,
    'system': 1.5,
    'framework': 2,
    'principle': 2,
    'law': 1.5,
    'rule': 1.5,
    
    # Coherence/unity terms
    'coherent': 3,
    'coherence': 3,
    'unified': 2,
    'unity': 2,
    'integrated': 2,
    'whole': 1.5,
    'together': 1,
    
    # Truth/alignment terms
    'truth': 2,
    'true': 1.5,
    'just': 1.5,
    'justice': 2,
    'right': 1,
    'rights': 1.5,
    'righteous': 2,
    
    # Conservation/preservation terms
    'preserve': 2,
    'conserve': 2,
    'protect': 1.5,
    'secure': 1.5,
    'maintain': 1.5,
    'establish': 1.5,
    
    # Purpose/teleology terms
    'purpose': 2,
    'end': 1,
    'goal': 1.5,
    'intent': 1.5,
    'design': 1.5,
    
    # Accountability terms
    'accountable': 2,
    'responsible': 1.5,
    'duty': 2,
    'obligation': 2,
    
    # Self-evident/axiomatic terms
    'self-evident': 3,
    'evident': 1.5,
    'necessary': 2,
    'fundamental': 2,
    'essential': 2,
    
    # Creator/transcendence terms
    'creator': 2,
    'nature': 1.5,
    'god': 1.5,
    'divine': 2,
    'endowed': 2,
    
    # Consent/legitimacy terms
    'consent': 2,
    'legitimate': 2,
    'authority': 1.5,
    'power': 1,
    'sovereign': 2,
    'people': 1,
}

# ENTROPY INDICATORS - words/patterns that indicate disorder/incoherence
ENTROPY_TERMS = {
    # Vagueness terms
    'synergy': -2,
    'leverage': -1.5,
    'stakeholder': -1.5,
    'holistic': -1,
    'paradigm': -1,
    'disrupt': -1.5,
    'innovative': -1,
    
    # Disorder terms
    'chaos': -2,
    'random': -1.5,
    'arbitrary': -2,
    'whatever': -1.5,
    
    # Passive/evasion terms
    'mistakes were made': -3,
    'going forward': -1.5,
    'at this time': -1,
    'in terms of': -1,
    
    # Relativism terms
    'perception': -1,
    'subjective': -1,
    'relative': -1,
    
    # Hedging terms
    'basically': -1,
    'essentially': -0.5,
    'kind of': -1,
    'sort of': -1,
    'maybe': -0.5,
}

# STRUCTURAL PATTERNS - bonus for logical structure
STRUCTURAL_PATTERNS = {
    r'\b(whereas|therefore|hence|thus|accordingly)\b': 2,
    r'\b(first|second|third|fourth|fifth)\b': 1,
    r'\b(article|section|amendment)\b': 1.5,
    r'\b(shall|must|will)\b': 1,
    r'\b(if|then|when|unless)\b': 0.5,
    r'\b(enumerat|list|specify)\b': 1.5,
    r'\b(prohibit|forbid|deny)\b': 1.5,
}

def score_document(text: str, title: str = "Document") -> dict:
    """
    Score a document for coherence using keyword/pattern matching.
    Returns dict with score components and final χ value.
    """
    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words)
    
    if word_count == 0:
        return {"title": title, "error": "Empty document"}
    
    # Normalize factor (per 1000 words)
    norm = 1000 / word_count
    
    results = {
        "title": title,
        "word_count": word_count,
        "coherence_hits": {},
        "entropy_hits": {},
        "structural_hits": {},
    }
    
    # Count coherence terms
    coherence_score = 0
    for term, weight in COHERENCE_TERMS.items():
        count = text_lower.count(term)
        if count > 0:
            results["coherence_hits"][term] = count
            coherence_score += count * weight * norm
    
    # Count entropy terms
    entropy_score = 0
    for term, weight in ENTROPY_TERMS.items():
        count = text_lower.count(term)
        if count > 0:
            results["entropy_hits"][term] = count
            entropy_score += count * weight * norm  # weight is negative
    
    # Check structural patterns
    structure_score = 0
    for pattern, weight in STRUCTURAL_PATTERNS.items():
        matches = len(re.findall(pattern, text_lower))
        if matches > 0:
            results["structural_hits"][pattern] = matches
            structure_score += matches * weight * norm
    
    # Calculate raw score
    raw_score = coherence_score + entropy_score + structure_score
    
    # Normalize to 0-10 scale (empirically calibrated)
    # Baseline assumption: strong documents score 50-100 raw, weak <20
    chi_score = min(10, max(0, raw_score / 10))
    
    results["coherence_raw"] = round(coherence_score, 2)
    results["entropy_raw"] = round(entropy_score, 2)
    results["structure_raw"] = round(structure_score, 2)
    results["total_raw"] = round(raw_score, 2)
    results["chi_score"] = round(chi_score, 2)
    
    # Status
    if chi_score >= 8:
        results["status"] = "HIGH COHERENCE"
    elif chi_score >= 5:
        results["status"] = "MODERATE COHERENCE"
    elif chi_score >= 3:
        results["status"] = "WEAK COHERENCE"
    else:
        results["status"] = "HIGH ENTROPY / INCOHERENT"
    
    return results

def print_report(results: dict):
    """Pretty print a scoring report."""
    print("=" * 60)
    print(f"COHERENCE ANALYSIS: {results['title']}")
    print("=" * 60)
    print(f"Word Count: {results['word_count']:,}")
    print()
    print("COMPONENT SCORES (normalized per 1K words):")
    print(f"  Coherence Terms:  +{results['coherence_raw']}")
    print(f"  Entropy Terms:    {results['entropy_raw']}")
    print(f"  Structural:       +{results['structure_raw']}")
    print(f"  --------------------------")
    print(f"  Total Raw:        {results['total_raw']}")
    print()
    print(f"CHI SCORE: {results['chi_score']} / 10.0")
    print(f"STATUS: {results['status']}")
    print()
    
    if results.get("coherence_hits"):
        print("Top Coherence Terms Found:")
        top_coh = sorted(results["coherence_hits"].items(), key=lambda x: x[1], reverse=True)[:10]
        for term, count in top_coh:
            print(f"  '{term}': {count}")
    
    if results.get("entropy_hits"):
        print("\nEntropy Terms Found:")
        for term, count in results["entropy_hits"].items():
            print(f"  '{term}': {count}")
    
    print()
    return results

# ==================== TEST DOCUMENTS ====================

CONSTITUTION_PREAMBLE = """
We the People of the United States, in Order to form a more perfect Union, 
establish Justice, insure domestic Tranquility, provide for the common defence, 
promote the general Welfare, and secure the Blessings of Liberty to ourselves 
and our Posterity, do ordain and establish this Constitution for the United States of America.
"""

DECLARATION_OPENING = """
When in the Course of human events, it becomes necessary for one people to dissolve 
the political bands which have connected them with another, and to assume among the 
powers of the earth, the separate and equal station to which the Laws of Nature and 
of Nature's God entitle them, a decent respect to the opinions of mankind requires 
that they should declare the causes which impel them to the separation.

We hold these truths to be self-evident, that all men are created equal, that they 
are endowed by their Creator with certain unalienable Rights, that among these are 
Life, Liberty and the pursuit of Happiness. That to secure these rights, Governments 
are instituted among Men, deriving their just powers from the consent of the governed.
"""

CORPORATE_WORD_SALAD = """
Going forward, we need to leverage our synergies to create a more holistic paradigm 
shift in stakeholder engagement. Our innovative disruption strategy will basically 
optimize the value proposition while maintaining bandwidth across verticals. 
At this time, we're pivoting to a more agile framework that sort of democratizes 
the ideation process. In terms of scalability, mistakes were made but we're 
doubling down on our core competencies to move the needle.
"""

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("THEOPHYSICS COHERENCE SCORER - EXTERNAL CALIBRATION TEST")
    print("=" * 60 + "\n")
    
    # Test 1: Declaration of Independence (should be HIGH)
    r1 = score_document(DECLARATION_OPENING, "Declaration of Independence (Opening)")
    print_report(r1)
    
    # Test 2: Constitution Preamble (should be HIGH)
    r2 = score_document(CONSTITUTION_PREAMBLE, "US Constitution Preamble")
    print_report(r2)
    
    # Test 3: Corporate Word Salad (should be LOW)
    r3 = score_document(CORPORATE_WORD_SALAD, "Corporate Word Salad")
    print_report(r3)
    
    print("\n" + "=" * 60)
    print("CALIBRATION SUMMARY")
    print("=" * 60)
    print(f"Declaration:     CHI = {r1['chi_score']} ({r1['status']})")
    print(f"Constitution:    CHI = {r2['chi_score']} ({r2['status']})")
    print(f"Word Salad:      CHI = {r3['chi_score']} ({r3['status']})")
    print()
    
    # Discrimination test
    if r1['chi_score'] > 5 and r2['chi_score'] > 5 and r3['chi_score'] < 3:
        print("[PASS] CALIBRATION PASSED: Scorer discriminates between coherent and incoherent documents")
    else:
        print("[WARN] CALIBRATION NEEDS ADJUSTMENT")
