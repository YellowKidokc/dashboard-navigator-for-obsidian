"""
Theophysics Definition Engine - Usage Examples
===============================================

Demonstrates how to use the computational definition system.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.theophysics_definitions import (
    DefinitionEngine, Coherence, TriadState, GraceFunction,
    Domain, C_CRIT
)


def example_1_basic_coherence():
    """Example 1: Creating and using Coherence objects"""
    print("=" * 70)
    print("Example 1: Basic Coherence Operations")
    print("=" * 70)
    
    # Create from different sources
    c_entropy = Coherence.from_entropy(S_obs=40, S_max=100)
    c_soc = Coherence.from_soc_score(0.8, 0.7, 0.9)
    c_triad = Coherence.from_triad(lambda_=0.7, pi=0.6, anthropos=0.5)
    
    print(f"\nFrom entropy: {c_entropy}")
    print(f"From SOC: {c_soc}")
    print(f"From Triad: {c_triad}")
    
    # Check states
    print(f"\nIs critical? {c_entropy.is_critical()}")
    print(f"Phase: {c_entropy.phase()}")
    print(f"Is stable? {c_entropy.is_stable()}")


def example_2_closed_system_decay():
    """Example 2: Simulate closed system decay (Theorem C3.2)"""
    print("\n" + "=" * 70)
    print("Example 2: Closed System Decay (No Grace)")
    print("=" * 70)
    
    c = Coherence(0.9, domain=Domain.PSYCHOLOGY)
    print(f"\nInitial coherence: {c}")
    
    gamma_D = 0.15  # Decoherence rate
    dt = 1.0  # Time step
    
    print("\nEvolution over 10 time steps:")
    for t in range(10):
        c = c.evolve_closed(gamma_D, dt)
        critical_marker = " ← CRITICAL!" if c.is_critical() else ""
        print(f"  t={t+1}: C = {c.value:.4f}{critical_marker}")


def example_3_grace_application():
    """Example 3: Apply grace to restore coherence"""
    print("\n" + "=" * 70)
    print("Example 3: Grace Application (Theorem C20.2)")
    print("=" * 70)
    
    # Start in fallen state (σ = -1, low coherence)
    fallen = Coherence(0.25, sigma=-1, domain=Domain.THEOLOGY)
    print(f"\nFallen state: {fallen}")
    print(f"  Is terminal? {fallen.is_terminal()}")
    
    # Apply grace
    restored = fallen.apply_grace(grace_strength=0.3)
    print(f"\nAfter grace: {restored}")
    print(f"  Sign flipped? {fallen.sigma} → {restored.sigma}")
    print(f"  Coherence increased? {fallen.value:.3f} → {restored.value:.3f}")


def example_4_open_system_warfare():
    """Example 4: Simulate spiritual warfare dynamics"""
    print("\n" + "=" * 70)
    print("Example 4: Spiritual Warfare Simulation")
    print("=" * 70)
    
    c = Coherence(0.6, domain=Domain.THEOLOGY)
    
    gamma_G = 0.2  # Grace rate
    gamma_D = 0.15  # Decoherence rate
    R_J = 1.5  # Post-resurrection factor
    
    print(f"\nInitial: {c}")
    print(f"Grace rate: {gamma_G}, Decoherence rate: {gamma_D}, R_J: {R_J}")
    
    history = c.simulate_warfare(
        gamma_G=gamma_G,
        gamma_D=gamma_D,
        steps=20,
        dt=0.5,
        grace_coupling=0.7,
        R_J=R_J
    )
    
    print("\nEvolution (every 5 steps):")
    for i, state in enumerate(history[::5]):
        print(f"  t={i*5}: {state}")


def example_5_triad_collapse():
    """Example 5: Simulate societal collapse cascade"""
    print("\n" + "=" * 70)
    print("Example 5: Triad Collapse Cascade (Λ → Π → A)")
    print("=" * 70)
    
    # Start with healthy society
    triad = TriadState(lambda_=0.85, pi=0.80, anthropos=0.75)
    print(f"\nInitial state: {triad}")
    print(f"Weakest link: {triad.weakest_link()}")
    
    # Simulate collapse starting from Logos decay
    collapse_history = triad.simulate_collapse(
        lambda_decay_rate=0.08,
        steps=15,
        dt=1.0
    )
    
    print("\nCollapse progression:")
    for i, state in enumerate(collapse_history[::3]):
        print(f"  Year {i*3}: {state}")


def example_6_triad_restoration():
    """Example 6: Simulate societal restoration"""
    print("\n" + "=" * 70)
    print("Example 6: Triad Restoration (A → Λ → Π)")
    print("=" * 70)
    
    # Start with collapsed society
    triad = TriadState(lambda_=0.25, pi=0.20, anthropos=0.15)
    print(f"\nCollapsed state: {triad}")
    print(f"Is critical? {triad.is_critical()}")
    
    # Simulate restoration via grace (enters through individuals)
    restoration_history = triad.simulate_restoration(
        grace_rate=0.05,
        steps=20,
        dt=1.0
    )
    
    print("\nRestoration progression:")
    for i, state in enumerate(restoration_history[::4]):
        print(f"  Year {i*4}: {state}")


def example_7_grace_function():
    """Example 7: Grace function dynamics"""
    print("\n" + "=" * 70)
    print("Example 7: Grace Function G(Rp, S)")
    print("=" * 70)
    
    grace_pre = GraceFunction(G0=1.0, R_J=1.0)  # Pre-resurrection
    grace_post = GraceFunction(G0=1.0, R_J=1.5)  # Post-resurrection
    
    print("\nGrace availability at different repentance/sin levels:")
    print("\n  Repentance | Sin | Pre-Res | Post-Res | Ratio")
    print("  " + "-" * 55)
    
    for rp in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for s in [0.2, 0.5, 0.8]:
            g_pre = grace_pre(rp, s)
            g_post = grace_post(rp, s)
            ratio = g_post / g_pre
            print(f"  {rp:10.1f} | {s:3.1f} | {g_pre:7.2f} | {g_post:8.2f} | {ratio:.2f}x")


def example_8_definition_engine():
    """Example 8: Using the Definition Engine"""
    print("\n" + "=" * 70)
    print("Example 8: Definition Engine")
    print("=" * 70)
    
    engine = DefinitionEngine()
    
    # Look up by alias
    print("\nLooking up 'SOC' (alias for Coherence):")
    defn = engine.get_definition("SOC")
    if defn:
        print(f"  Name: {defn.name}")
        print(f"  Symbol: {defn.symbol}")
        print(f"  Formula: {defn.canonical_formula}")
        print(f"  Aliases: {len(defn.aliases)} total")
        print(f"  Theorems: {[t.id for t in defn.theorems]}")
    
    # Validate usage
    print("\nValidating term usage:")
    context = "The quantum coherence between the two states is measured by interference"
    result = engine.validate_usage("coherence", context)
    print(f"  Valid: {result['valid']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Detected domain: {result.get('detected_domain', 'None')}")
    
    # Log drift
    print("\nLogging drift observation:")
    engine.log_drift(
        term="coherence",
        context="Paper-05",
        observation="Used 'coherence' to mean 'agreement' rather than informational correlation",
        resolution="Clarified in domain interpretations",
        severity="minor"
    )
    print(f"  Drift log entries: {len(defn.drift_log)}")


def example_9_composite_coherence():
    """Example 9: Composite coherence (multiplicative vulnerability)"""
    print("\n" + "=" * 70)
    print("Example 9: Composite Coherence")
    print("=" * 70)
    
    # Multiple subsystems
    c_physical = Coherence(0.9, domain=Domain.PHYSICS)
    c_mental = Coherence(0.7, domain=Domain.PSYCHOLOGY)
    c_social = Coherence(0.5, domain=Domain.SOCIOLOGY)
    c_spiritual = Coherence(0.6, domain=Domain.THEOLOGY)
    
    print("\nSubsystem coherences:")
    print(f"  Physical: {c_physical.value:.3f}")
    print(f"  Mental: {c_mental.value:.3f}")
    print(f"  Social: {c_social.value:.3f}")
    print(f"  Spiritual: {c_spiritual.value:.3f}")
    
    # Composite (geometric mean)
    c_total = Coherence.composite([c_physical, c_mental, c_social, c_spiritual])
    print(f"\nComposite (total): {c_total}")
    print(f"  Note: Lower than any individual component!")
    
    # Show vulnerability
    print("\nMultiplicative vulnerability:")
    c_collapsed_social = Coherence(0.1, domain=Domain.SOCIOLOGY)
    c_vulnerable = Coherence.composite([c_physical, c_mental, c_collapsed_social, c_spiritual])
    print(f"  If social collapses to 0.1: {c_vulnerable}")
    print(f"  Total drops from {c_total.value:.3f} to {c_vulnerable.value:.3f}")


def example_10_critical_threshold():
    """Example 10: Critical threshold dynamics"""
    print("\n" + "=" * 70)
    print("Example 10: Critical Threshold C_crit = 0.35")
    print("=" * 70)
    
    print(f"\nCritical threshold: {C_CRIT}")
    
    coherences = [0.1, 0.2, 0.35, 0.4, 0.5, 0.7, 0.9]
    
    print("\nCoherence | Critical? | Phase")
    print("-" * 45)
    for val in coherences:
        c = Coherence(val)
        critical = "YES" if c.is_critical() else "NO"
        print(f"  {val:5.2f}   | {critical:8s}  | {c.phase()}")


def main():
    """Run all examples"""
    examples = [
        example_1_basic_coherence,
        example_2_closed_system_decay,
        example_3_grace_application,
        example_4_open_system_warfare,
        example_5_triad_collapse,
        example_6_triad_restoration,
        example_7_grace_function,
        example_8_definition_engine,
        example_9_composite_coherence,
        example_10_critical_threshold,
    ]
    
    for example in examples:
        example()
        print()
    
    print("=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
