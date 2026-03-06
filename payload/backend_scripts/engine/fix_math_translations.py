"""
THEOPHYSICS MATH TRANSLATION FIXER
===================================
This script helps identify and fix incorrect translations in the math table.
Run against MATH_TRANSLATION_MASTER_FIXED.xlsx to improve plain English explanations.
"""

import pandas as pd
import re

# THEOPHYSICS SYMBOL DEFINITIONS
# These override generic AI translations with correct Theophysics meanings

SYMBOL_DEFINITIONS = {
    # Core symbols
    r'\\chi': 'the Logos Field (χ), the fundamental informational substrate of reality',
    r'chi': 'the Logos Field (χ)',
    r'\\Phi': 'Integrated Information (Φ), measuring consciousness',
    r'Phi': 'Integrated Information (Φ)',
    r'\\Psi': 'the quantum/consciousness state (Ψ)',
    r'Psi': 'the quantum state (Ψ)',
    
    # Grace symbols
    r'G_0': 'the infinite grace reservoir (G₀)',
    r'G\\(t\\)': 'grace available at time t',
    r'\\tau_{\\text{grace}}': 'the grace time constant (τ_grace)',
    r'\\Theta\\(\\text{faith}\\)': 'the faith activation function (= 1 if faith present, 0 otherwise)',
    r'E_{\\text{grace}}': 'grace energy',
    r'\\Lambda_{\\text{grace}}': 'the grace cosmological constant',
    
    # Moral symbols
    r'D\\(t\\)': 'moral decay/sin accumulation at time t',
    r'C_{\\text{child}}': 'moral culpability of a child',
    r'C_{\\text{adult}}': 'moral culpability of an adult',
    r'C_{\\text{zombie}}': 'moral culpability of a philosophical zombie (unconscious being)',
    
    # Physics
    r'G_{\\mu\\nu}': 'the Einstein tensor (spacetime curvature)',
    r'T_{\\mu\\nu}': 'the stress-energy tensor (energy/momentum distribution)',
    r'K\\(x\\)': 'Kolmogorov complexity of x (shortest program length)',
    r'\\Phi_{\\text{terminal}}': 'the Terminal Observer (God, with Φ = ∞)',
}

# WRONG PHRASES TO FIX
BAD_TRANSLATIONS = {
    'variable called chi': 'the Logos Field (χ), the fundamental substrate of all information',
    'cost for a child': 'moral culpability of a child',
    'cost for an adult': 'moral culpability of an adult', 
    'zombie concentration': 'philosophical zombie (a being with no consciousness)',
    'This expression states:': '',  # Remove this useless phrase
    'The equation represents': '',  # Often followed by nothing useful
    'a parameter': 'a variable',
    'parameter p': 'program p',
}

def identify_theophysics_context(latex):
    """Determine what domain this equation belongs to"""
    latex_lower = latex.lower()
    
    if any(x in latex_lower for x in ['grace', 'faith', 'sin', 'salvation', 'christ']):
        return 'THEOLOGICAL'
    elif any(x in latex_lower for x in ['chi', 'logos', 'coherence']):
        return 'LOGOS_FIELD'
    elif any(x in latex_lower for x in ['phi', 'consciousness', 'observer']):
        return 'CONSCIOUSNESS'
    elif any(x in latex_lower for x in ['child', 'adult', 'zombie', 'culpab']):
        return 'MORAL'
    elif any(x in latex_lower for x in ['g_{', 't_{', 'mu', 'nu', 'lambda']):
        return 'PHYSICS'
    elif any(x in latex_lower for x in ['k(x)', 'entropy', 'information']):
        return 'INFORMATION'
    else:
        return 'GENERAL'

def fix_translation(row):
    """Fix common translation errors based on Theophysics context"""
    latex = str(row['latex']) if pd.notna(row['latex']) else ''
    tts = str(row['tts_audio']) if pd.notna(row['tts_audio']) else ''
    
    fixed_tts = tts
    issues = []
    
    # Apply bad translation fixes
    for bad, good in BAD_TRANSLATIONS.items():
        if bad in fixed_tts:
            fixed_tts = fixed_tts.replace(bad, good)
            issues.append(f"Replaced '{bad}' with '{good}'")
    
    # Context-specific fixes
    context = identify_theophysics_context(latex)
    
    if context == 'THEOLOGICAL':
        if 'G' in latex and 'gravity' in fixed_tts.lower():
            fixed_tts = fixed_tts.replace('gravity', 'grace')
            issues.append("Changed 'gravity' to 'grace' in theological context")
    
    if context == 'MORAL':
        if 'C' in latex and 'cost' in fixed_tts.lower():
            fixed_tts = fixed_tts.replace('cost', 'moral culpability')
            issues.append("Changed 'cost' to 'moral culpability'")
    
    if context == 'CONSCIOUSNESS':
        if 'Phi' in latex and 'function' in fixed_tts.lower() and 'consciousness' not in fixed_tts.lower():
            fixed_tts = fixed_tts + " (Φ measures integrated information/consciousness)"
            issues.append("Added consciousness context for Φ")
    
    return {
        'id': row['id'],
        'context': context,
        'original': tts,
        'fixed': fixed_tts,
        'issues': issues
    }

def analyze_file(filepath):
    """Analyze the translation file and report issues"""
    df = pd.read_excel(filepath)
    
    results = []
    for idx, row in df.iterrows():
        result = fix_translation(row)
        if result['issues']:  # Only include rows with changes
            results.append(result)
    
    return results, df

def main():
    filepath = 'MATH_TRANSLATION_MASTER_FIXED.xlsx'
    
    print("="*80)
    print("THEOPHYSICS MATH TRANSLATION ANALYZER")
    print("="*80)
    
    results, df = analyze_file(filepath)
    
    print(f"\nTotal equations: {len(df)}")
    print(f"Equations with issues found: {len(results)}")
    
    print("\n" + "="*80)
    print("TRANSLATIONS THAT NEED FIXING:")
    print("="*80)
    
    for r in results[:20]:
        print(f"\n--- ID {r['id']} [{r['context']}] ---")
        print(f"ORIGINAL: {r['original'][:100]}...")
        print(f"FIXED: {r['fixed'][:100]}...")
        print(f"CHANGES: {', '.join(r['issues'])}")
    
    # Save fixed version
    # (Uncomment to actually save)
    # df_fixed = df.copy()
    # for r in results:
    #     df_fixed.loc[df_fixed['id'] == r['id'], 'tts_audio'] = r['fixed']
    # df_fixed.to_excel('MATH_TRANSLATION_FIXED_V2.xlsx', index=False)
    
    return results

if __name__ == '__main__':
    main()
