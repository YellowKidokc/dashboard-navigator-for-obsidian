"""
Theophysics Calculator — Core Mathematical Engine
===================================================
All formulas from the Theophysics framework as pure computation.
Outputs CSV files that open directly in Excel.

Usage:
    python theophysics_calculator.py              (runs all calculations, outputs CSVs)
    python theophysics_calculator.py --fruits     (Fruits of the Spirit only)
    python theophysics_calculator.py --master     (Master Equation simulation only)
    python theophysics_calculator.py --coherence  (Coherence decay model only)

Output:
    theophysics_master_equation.csv
    theophysics_fruits_of_spirit.csv
    theophysics_coherence_model.csv
    theophysics_grace_curves.csv
    theophysics_all_functions.csv
"""

import math
import csv
import os
import sys
from datetime import datetime

# ─── OUTPUT DIRECTORY ─────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
#  CORE FUNCTIONS — The Mathematical Engine
# ═══════════════════════════════════════════════════════════════════════════════

# ─── 1. GRACE FUNCTION G(Rp) ─────────────────────────────────────────────────
# G(Rp) = e^{-γ·S·(1-Rp)}
# Grace flows inversely proportional to sin, proportional to receptivity
# Rp = 0 (closed) → G ≈ 0 | Rp = 1 (fully open) → G = 1

def grace_function(Rp, sin_level, gamma=1.0):
    """
    Grace Function G(Rp)

    Parameters:
        Rp:        Receptivity (0 to 1). 0 = closed, 1 = fully receptive
        sin_level: Current sin/disorder level (0+)
        gamma:     Coupling constant (default 1.0)

    Returns: Grace value (0 to 1)
    """
    return math.exp(-gamma * sin_level * (1 - Rp))


# ─── 2. FAITH RESPONSE R(F) ──────────────────────────────────────────────────
# R(F) = F^1.5 / (1 + F^1.5)
# Sigmoid-like activation: faith below threshold has little effect,
# above threshold it saturates. Models "mustard seed" dynamics.

def faith_response(F):
    """
    Faith Response Function R(F)

    Parameters:
        F: Faith level (0 to 1+)

    Returns: Activation level (0 to 1)
    """
    f15 = F ** 1.5
    return f15 / (1.0 + f15)


# ─── 3. SPIRITUAL UTILITY U(Ss) ──────────────────────────────────────────────
# U(Ss) = 1 / (1 + e^{-2(Ss - 1)})
# Logistic function centered at Ss=1. Below 1: low utility. Above 1: high.

def spiritual_utility(Ss):
    """
    Spiritual Utility Function U(Ss)

    Parameters:
        Ss: Spiritual state value

    Returns: Utility (0 to 1)
    """
    return 1.0 / (1.0 + math.exp(-2.0 * (Ss - 1.0)))


# ─── 4. QUANTUM CHOICE FIELD P(Q,C) ──────────────────────────────────────────
# P(choice) = e^{-(Q·C)}
# Free will as probability space. Higher Q*C = more constrained choice.

def quantum_choice(Q, C):
    """
    Quantum Choice Field

    Parameters:
        Q: Quantum uncertainty parameter
        C: Coherence factor

    Returns: Choice probability (0 to 1)
    """
    return math.exp(-(Q * C))


# ─── 5. SPIRITUAL DECAY ──────────────────────────────────────────────────────
# chi(t) = chi_min + (chi_0 - chi_min) * e^{-delta*t}
# Faith decays exponentially without maintenance.

def spiritual_decay(chi_0, t, delta=0.03, chi_min=0.1):
    """
    Spiritual Decay Function

    Parameters:
        chi_0:   Initial spiritual state
        t:       Time
        delta:   Decay constant (default 0.03)
        chi_min: Minimum spiritual state floor

    Returns: chi(t) — spiritual state at time t
    """
    return chi_min + (chi_0 - chi_min) * math.exp(-delta * t)


# ─── 6. KARMA / CAUSAL FEEDBACK K(t) ─────────────────────────────────────────
# K(t) = integral of e^{-eta*(t-tau)} * S(tau) dtau
# Discretized: sum of past actions with exponential decay weighting

def karma_function(action_history, t, eta=0.1):
    """
    Karma Function K(t) — causal feedback from past actions

    Parameters:
        action_history: list of (time, action_value) tuples
        t:              current time
        eta:            decay rate for past actions

    Returns: Karma value at time t
    """
    K = 0.0
    for tau, action in action_history:
        if tau <= t:
            K += math.exp(-eta * (t - tau)) * action
    return K


# ─── 7. CHRIST REDEMPTION TRANSFORMATION ─────────────────────────────────────
# chi_redeemed = chi_natural * e^{-(sin) + kappa*(grace)}
# The singularity: entropy reversal through divine intervention

def christ_redemption(chi_natural, sin_level, grace_level, kappa=1.0):
    """
    Christ Redemption Transformation

    Parameters:
        chi_natural: Natural spiritual state
        sin_level:   Current sin/entropy level
        grace_level: Current grace level
        kappa:       Christ coefficient (default 1.0)

    Returns: Redeemed spiritual state
    """
    return chi_natural * math.exp(-sin_level + kappa * grace_level)


# ─── 8. COHERENCE DECAY MODEL C(t) ───────────────────────────────────────────
# C(t) = C0 * exp(-lambda*t) * product[1 - H(t - t_i)]
# Coherence decays, and drops to 0 at constraint-removal events.

def coherence_model(C0, t, lam, constraint_removals=None):
    """
    Coherence Decay Model C(t)

    Parameters:
        C0:                   Initial coherence
        t:                    Time
        lam:                  Natural decay rate (lambda)
        constraint_removals:  list of times when constraints are removed

    Returns: Coherence at time t
    """
    C = C0 * math.exp(-lam * t)
    if constraint_removals:
        for t_i in constraint_removals:
            if t >= t_i:
                # Heaviside step — sharp coherence drop
                C *= max(0.0, 1.0 - 0.3 * math.exp(-0.5 * (t - t_i)))
    return max(C, 0.0)


# ─── 9. ENTROPY (Shannon / Boltzmann) ────────────────────────────────────────
# S = -sum(p_i * ln(p_i))

def shannon_entropy(probabilities):
    """
    Shannon Entropy S = -Σ p_i ln(p_i)

    Parameters:
        probabilities: list of probabilities (must sum to ~1)

    Returns: Entropy value (bits, base e)
    """
    S = 0.0
    for p in probabilities:
        if p > 0:
            S -= p * math.log(p)
    return S


# ─── 10. INTEGRATED INFORMATION Φ (simplified) ───────────────────────────────
# Φ = information generated by whole above sum of parts

def integrated_information(whole_entropy, partition_entropies):
    """
    Integrated Information Φ (simplified Tononi measure)

    Parameters:
        whole_entropy:       Entropy of whole system
        partition_entropies: List of entropies of partitions

    Returns: Φ value
    """
    return whole_entropy - sum(partition_entropies)


# ═══════════════════════════════════════════════════════════════════════════════
#  FRUITS OF THE SPIRIT — Coherence Observables
# ═══════════════════════════════════════════════════════════════════════════════

FRUITS = [
    "Love",          # Agape     — integration with others
    "Joy",           # Chara     — positive valence
    "Peace",         # Eirene    — stability/resolution
    "Patience",      # Makrothumia — long-horizon planning
    "Kindness",      # Chrestotes — active benefit to others
    "Goodness",      # Agathosune — constructive intent
    "Faithfulness",  # Pistis    — consistency over time
    "Gentleness",    # Prautes   — calibrated force
    "Self-Control",  # Egkrateia — bounded action
]

# Measurement proxies (from the framework)
FRUIT_PROXIES = {
    "Love":          "Charitable giving, volunteerism, family stability",
    "Joy":           "Life satisfaction surveys, suicide rates (inverse)",
    "Peace":         "Crime rates (inverse), conflict metrics (inverse)",
    "Patience":      "Delayed gratification, savings rates",
    "Kindness":      "Trust metrics, social cohesion measures",
    "Goodness":      "Ethical behavior indices",
    "Faithfulness":  "Marriage duration, contract enforcement",
    "Gentleness":    "Violence rates (inverse), dispute resolution",
    "Self-Control":  "Addiction rates (inverse), obesity (inverse), debt (inverse)",
}

def fruit_score(sigma, coherence, noise_seed=0):
    """
    Calculate all 9 Fruit scores given sign-state and coherence.

    <F_i> > 0 iff sigma = +1
    Sum(F_i) <= C[chi]  (bounded by total coherence)

    Parameters:
        sigma:      Sign state (+1 aligned, -1 decoherent)
        coherence:  Total coherence level (0 to 1)
        noise_seed: For variation between fruits

    Returns: dict of {fruit_name: score}
    """
    scores = {}
    # Weights reflect dimensional coverage
    weights = [0.15, 0.10, 0.12, 0.10, 0.11, 0.10, 0.11, 0.10, 0.11]

    for i, fruit in enumerate(FRUITS):
        # Base score from coherence * sign
        base = sigma * coherence * weights[i] * 9  # scale so total ≈ coherence

        # Small variation per fruit
        variation = 0.05 * math.sin(noise_seed + i * 1.7)

        score = base + variation
        scores[fruit] = round(score, 4)

    return scores


def fruit_total(scores, weights=None):
    """
    Total Fruit Score: F_total = Σ w_i * <F_i>
    """
    if weights is None:
        weights = {f: 1.0/9.0 for f in FRUITS}
    return sum(scores[f] * weights.get(f, 1.0/9.0) for f in FRUITS)


def fruit_entropy_tradeoff(fruit_total_val, entropy_val):
    """
    Fruit-Entropy Trade-off: Σ<F_i> · S[ρ] ≈ const
    Returns the product (should be approximately constant for valid states)
    """
    return fruit_total_val * entropy_val


# ═══════════════════════════════════════════════════════════════════════════════
#  MASTER EQUATION — Full Simulation
# ═══════════════════════════════════════════════════════════════════════════════
# dχ/dt = G(Rp)(1+E+S) e^{-(Q·C)} R(F) U(Ss) - δχ + K(t)·D(Ss) + Ω·T

def master_equation_step(chi, Rp, sin_level, faith_level, coherence,
                         Q=0.5, delta=0.03, karma_val=0.0, omega=0.01,
                         gamma=1.0, dt=1.0):
    """
    One time-step of the Master Equation:
    dχ/dt = G(Rp)(1+E+S) e^{-(Q·C)} R(F) U(Ss) - δχ + K(t) + Ω

    Returns: (new_chi, components_dict)
    """
    G = grace_function(Rp, sin_level, gamma)
    R = faith_response(faith_level)
    U = spiritual_utility(chi)
    P = quantum_choice(Q, coherence)

    # Growth term
    growth = G * (1.0 + sin_level) * P * R * U

    # Decay term
    decay = delta * chi

    # Karma + divine mystery
    external = karma_val + omega

    # dχ/dt
    d_chi = growth - decay + external

    new_chi = chi + d_chi * dt

    components = {
        "Grace G(Rp)": round(G, 6),
        "Faith R(F)": round(R, 6),
        "Utility U(Ss)": round(U, 6),
        "Choice P(Q,C)": round(P, 6),
        "Growth": round(growth, 6),
        "Decay": round(decay, 6),
        "Karma": round(karma_val, 6),
        "Omega": round(omega, 6),
        "dChi/dt": round(d_chi, 6),
        "Chi": round(new_chi, 6),
    }

    return new_chi, components


# ═══════════════════════════════════════════════════════════════════════════════
#  CSV OUTPUT GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def write_csv(filename, headers, rows):
    """Write rows to CSV file in output directory."""
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    print(f"  Saved: {path}  ({len(rows)} rows)")
    return path


def generate_all_functions_csv():
    """
    Generates a table of ALL core functions evaluated across their input ranges.
    One sheet with columns for each function.
    """
    print("\n[1/5] All Core Functions...")
    headers = [
        "Input (0 to 1)",
        "Grace G(Rp) [sin=0.3]",
        "Grace G(Rp) [sin=0.6]",
        "Grace G(Rp) [sin=1.0]",
        "Faith R(F)",
        "Utility U(Ss)",
        "Choice P(Q=0.5,C=input)",
        "Decay chi(t) [chi0=1.0]",
        "Christ chi_red [sin=0.5]",
    ]

    rows = []
    for i in range(101):
        x = i / 100.0  # 0.00 to 1.00

        row = [
            round(x, 2),
            round(grace_function(x, 0.3), 6),
            round(grace_function(x, 0.6), 6),
            round(grace_function(x, 1.0), 6),
            round(faith_response(x), 6),
            round(spiritual_utility(x * 2), 6),  # scale to 0-2 range
            round(quantum_choice(0.5, x), 6),
            round(spiritual_decay(1.0, x * 100, 0.03), 6),  # t = 0..100
            round(christ_redemption(x, 0.5, x, 1.0), 6),
        ]
        rows.append(row)

    write_csv("theophysics_all_functions.csv", headers, rows)


def generate_master_equation_csv():
    """
    Simulate the Master Equation over 200 time steps with 3 scenarios:
    1. Natural decay (no grace, no faith)
    2. Growing faith (increasing F over time)
    3. Full redemption (grace + faith + Christ intervention at t=100)
    """
    print("[2/5] Master Equation Simulation...")

    headers = [
        "Time",
        # Scenario 1: Natural decay
        "S1_Chi", "S1_Grace", "S1_Faith", "S1_dChi",
        # Scenario 2: Growing faith
        "S2_Chi", "S2_Grace", "S2_Faith", "S2_dChi",
        # Scenario 3: Full redemption
        "S3_Chi", "S3_Grace", "S3_Faith", "S3_dChi",
    ]

    rows = []

    # Initial conditions
    chi1 = 0.8  # Scenario 1
    chi2 = 0.8  # Scenario 2
    chi3 = 0.8  # Scenario 3

    for t in range(201):
        # Scenario 1: No grace, no faith — pure decay
        Rp1, F1, sin1 = 0.0, 0.0, 0.5
        chi1, c1 = master_equation_step(chi1, Rp1, sin1, F1, 0.5)

        # Scenario 2: Growing faith, moderate receptivity
        F2 = min(1.0, t / 150.0)  # faith grows from 0 to ~1
        Rp2 = 0.6
        sin2 = max(0.1, 0.5 - t * 0.002)  # sin slowly decreases
        chi2, c2 = master_equation_step(chi2, Rp2, sin2, F2, 0.5)

        # Scenario 3: Christ intervention at t=100
        F3 = min(1.0, t / 100.0)
        Rp3 = 0.7
        sin3 = 0.5
        if t == 100:
            chi3 = christ_redemption(chi3, sin3, 0.8, kappa=2.0)
        chi3, c3 = master_equation_step(chi3, Rp3, sin3, F3, 0.5, omega=0.02)

        rows.append([
            t,
            round(chi1, 6), c1["Grace G(Rp)"], c1["Faith R(F)"], c1["dChi/dt"],
            round(chi2, 6), c2["Grace G(Rp)"], c2["Faith R(F)"], c2["dChi/dt"],
            round(chi3, 6), c3["Grace G(Rp)"], c3["Faith R(F)"], c3["dChi/dt"],
        ])

    write_csv("theophysics_master_equation.csv", headers, rows)


def generate_fruits_csv():
    """
    Fruits of the Spirit across coherence and sign-state values.
    Shows how each Fruit score changes with coherence level.
    """
    print("[3/5] Fruits of the Spirit...")

    headers = ["Coherence", "Sigma"] + FRUITS + [
        "F_total", "Entropy", "F*S_tradeoff",
        "Love_Proxy", "Joy_Proxy", "Peace_Proxy",
    ]

    rows = []

    for sigma in [+1, -1]:
        for c_idx in range(101):
            coherence = c_idx / 100.0

            scores = fruit_score(sigma, coherence, noise_seed=c_idx * 0.1)
            f_total = fruit_total(scores)

            # Entropy inversely related to coherence
            entropy = max(0.01, 1.0 - coherence + 0.05 * math.sin(c_idx))
            tradeoff = fruit_entropy_tradeoff(abs(f_total), entropy)

            row = [
                round(coherence, 2),
                sigma,
            ]
            for fruit in FRUITS:
                row.append(scores[fruit])

            row.extend([
                round(f_total, 4),
                round(entropy, 4),
                round(tradeoff, 4),
                FRUIT_PROXIES["Love"],
                FRUIT_PROXIES["Joy"],
                FRUIT_PROXIES["Peace"],
            ])
            rows.append(row)

    write_csv("theophysics_fruits_of_spirit.csv", headers, rows)


def generate_coherence_csv():
    """
    Coherence decay model C(t) with and without constraint removals.
    Models social/physical coherence collapse.
    """
    print("[4/5] Coherence Decay Model...")

    # Constraint removal events (analogous to historical moments)
    events = {
        "No Removals": [],
        "One Removal (t=50)": [50],
        "Two Removals (t=30,70)": [30, 70],
        "Cascading (t=20,40,60,80)": [20, 40, 60, 80],
    }

    headers = ["Time", "Lambda"] + list(events.keys())

    rows = []
    C0 = 1.0
    lam = 0.01

    for t in range(201):
        row = [t, lam]
        for scenario_name, removals in events.items():
            C = coherence_model(C0, t, lam, removals)
            row.append(round(C, 6))
        rows.append(row)

    write_csv("theophysics_coherence_model.csv", headers, rows)


def generate_grace_curves_csv():
    """
    Grace function curves across receptivity for different sin levels.
    Plus: the Christ transformation effect.
    """
    print("[5/5] Grace Curves & Christ Transformation...")

    headers = [
        "Receptivity_Rp",
        "Grace_sin=0.1", "Grace_sin=0.3", "Grace_sin=0.5",
        "Grace_sin=0.7", "Grace_sin=1.0", "Grace_sin=2.0",
        "Christ_chi_natural=0.3", "Christ_chi_natural=0.5",
        "Christ_chi_natural=0.8",
    ]

    rows = []
    sin_levels = [0.1, 0.3, 0.5, 0.7, 1.0, 2.0]

    for i in range(101):
        Rp = i / 100.0

        row = [round(Rp, 2)]

        # Grace curves
        for sin in sin_levels:
            row.append(round(grace_function(Rp, sin), 6))

        # Christ transformation at different natural states
        for chi_nat in [0.3, 0.5, 0.8]:
            row.append(round(christ_redemption(chi_nat, 0.5, Rp, kappa=1.5), 6))

        rows.append(row)

    write_csv("theophysics_grace_curves.csv", headers, rows)


# ═══════════════════════════════════════════════════════════════════════════════
#  EXCEL FORMULA REFERENCE (for manual recreation)
# ═══════════════════════════════════════════════════════════════════════════════

EXCEL_FORMULAS = """
EXCEL FORMULA REFERENCE
========================
Copy these into Excel cells. Replace A1 with your input cell.

Grace Function G(Rp):
  =EXP(-gamma * sin_level * (1 - A1))
  Example: =EXP(-1 * 0.5 * (1 - A1))

Faith Response R(F):
  =A1^1.5 / (1 + A1^1.5)

Spiritual Utility U(Ss):
  =1 / (1 + EXP(-2 * (A1 - 1)))

Quantum Choice P(Q,C):
  =EXP(-(Q * A1))
  Example: =EXP(-(0.5 * A1))

Spiritual Decay chi(t):
  =chi_min + (chi_0 - chi_min) * EXP(-delta * A1)
  Example: =0.1 + (1.0 - 0.1) * EXP(-0.03 * A1)

Christ Redemption:
  =chi_natural * EXP(-sin + kappa * grace)
  Example: =A1 * EXP(-0.5 + 1.5 * B1)

Shannon Entropy:
  =-SUMPRODUCT(A1:A9 * LN(A1:A9))

Coherence Decay:
  =C0 * EXP(-lambda * A1)
  Example: =1.0 * EXP(-0.01 * A1)

Master Equation (one step):
  Growth = G * (1 + S) * P * R * U
  Decay  = delta * chi
  dChi   = Growth - Decay + Karma + Omega
  NewChi = OldChi + dChi

Fruit Score (per fruit):
  =sigma * coherence * weight * 9
  Where sigma = +1 or -1, weight ≈ 1/9

Total Fruit:
  =AVERAGE(F1:F9)  or  =SUMPRODUCT(weights, scores) / SUM(weights)
"""


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]

    print("=" * 60)
    print("  THEOPHYSICS CALCULATOR")
    print("  Core Mathematical Engine — CSV Output for Excel")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if not args or "--all" in args:
        generate_all_functions_csv()
        generate_master_equation_csv()
        generate_fruits_csv()
        generate_coherence_csv()
        generate_grace_curves_csv()
    elif "--fruits" in args:
        generate_fruits_csv()
    elif "--master" in args:
        generate_master_equation_csv()
    elif "--coherence" in args:
        generate_coherence_csv()
    elif "--grace" in args:
        generate_grace_curves_csv()

    # Write Excel formula reference
    ref_path = os.path.join(OUTPUT_DIR, "EXCEL_FORMULA_REFERENCE.txt")
    with open(ref_path, "w", encoding="utf-8") as f:
        f.write(EXCEL_FORMULAS)
    print(f"\n  Excel formulas: {ref_path}")

    print("\n" + "=" * 60)
    print("  DONE — Open the CSV files in Excel")
    print(f"  Output folder: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
