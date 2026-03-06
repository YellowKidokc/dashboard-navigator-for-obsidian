"""
THEOPHYSICS — Python in Excel Snippets
========================================
Paste each block into a =PY() cell in Excel.
Each snippet outputs a DataFrame that spills into cells.

Python in Excel has: pandas, numpy, matplotlib, seaborn, scipy
Use xl("A1") to reference Excel cells.

SETUP: In Excel, go to Formulas > Insert Python
       Paste any snippet below into the PY() cell.
"""

# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 1: ALL CORE FUNCTIONS TABLE
#  Paste this into a PY() cell. It creates a full table of every function.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---

import numpy as np
import pandas as pd

x = np.linspace(0, 1, 101)

# Grace Function: G(Rp) = e^{-gamma * sin * (1 - Rp)}
def grace(Rp, sin_level, gamma=1.0):
    return np.exp(-gamma * sin_level * (1 - Rp))

# Faith Response: R(F) = F^1.5 / (1 + F^1.5)
def faith(F):
    f15 = np.power(F, 1.5)
    return f15 / (1 + f15)

# Spiritual Utility: U(Ss) = 1 / (1 + e^{-2(Ss - 1)})
def utility(Ss):
    return 1 / (1 + np.exp(-2 * (Ss - 1)))

# Quantum Choice: P = e^{-(Q*C)}
def choice(Q, C):
    return np.exp(-(Q * C))

# Spiritual Decay: chi(t) = chi_min + (chi0 - chi_min) * e^{-delta*t}
def decay(chi0, t, delta=0.03, chi_min=0.1):
    return chi_min + (chi0 - chi_min) * np.exp(-delta * t)

# Christ Redemption: chi_red = chi_nat * e^{-sin + kappa*grace}
def christ(chi_nat, sin_lvl, grace_lvl, kappa=1.5):
    return chi_nat * np.exp(-sin_lvl + kappa * grace_lvl)

df = pd.DataFrame({
    "Input (0-1)": x,
    "Grace [sin=0.3]": grace(x, 0.3),
    "Grace [sin=0.6]": grace(x, 0.6),
    "Grace [sin=1.0]": grace(x, 1.0),
    "Faith R(F)": faith(x),
    "Utility U(Ss)": utility(x * 2),
    "Choice P(Q=0.5)": choice(0.5, x),
    "Decay chi(t=0..100)": decay(1.0, x * 100),
    "Christ [sin=0.5]": christ(x, 0.5, x),
})

df

# --- END SNIPPET 1 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 2: FRUITS OF THE SPIRIT
#  Paste this into a separate =PY() cell.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---

import numpy as np
import pandas as pd

FRUITS = ["Love", "Joy", "Peace", "Patience", "Kindness",
          "Goodness", "Faithfulness", "Gentleness", "Self-Control"]

WEIGHTS = [0.15, 0.10, 0.12, 0.10, 0.11, 0.10, 0.11, 0.10, 0.11]

PROXIES = [
    "Charitable giving, volunteerism, family stability",
    "Life satisfaction, suicide rates (inv)",
    "Crime rates (inv), conflict metrics (inv)",
    "Delayed gratification, savings rates",
    "Trust metrics, social cohesion",
    "Ethical behavior indices",
    "Marriage duration, contract enforcement",
    "Violence rates (inv), dispute resolution",
    "Addiction (inv), obesity (inv), debt (inv)",
]

coherence = np.linspace(0, 1, 51)
rows = []

for sigma in [+1, -1]:
    for C in coherence:
        row = {"Coherence": round(C, 2), "Sigma": sigma}
        total = 0
        for i, fruit in enumerate(FRUITS):
            score = sigma * C * WEIGHTS[i] * 9
            row[fruit] = round(score, 4)
            total += score
        row["F_total"] = round(total / 9, 4)
        row["Entropy"] = round(max(0.01, 1.0 - C), 4)
        row["F*S_tradeoff"] = round(abs(total / 9) * max(0.01, 1.0 - C), 4)
        rows.append(row)

df = pd.DataFrame(rows)
df

# --- END SNIPPET 2 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 3: MASTER EQUATION SIMULATION (3 Scenarios)
#  Paste this into a separate =PY() cell.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---

import numpy as np
import pandas as pd

def grace(Rp, sin_lvl, gamma=1.0):
    return np.exp(-gamma * sin_lvl * (1 - Rp))

def faith(F):
    f15 = F ** 1.5
    return f15 / (1 + f15) if F > 0 else 0

def utility(Ss):
    return 1 / (1 + np.exp(-2 * (Ss - 1)))

def choice_field(Q, C):
    return np.exp(-(Q * C))

def step(chi, Rp, sin_lvl, F, C, Q=0.5, delta=0.03, karma=0, omega=0.01):
    G = grace(Rp, sin_lvl)
    R = faith(F)
    U = utility(chi)
    P = choice_field(Q, C)
    growth = G * (1 + sin_lvl) * P * R * U
    decay_val = delta * chi
    d_chi = growth - decay_val + karma + omega
    return chi + d_chi, G, R, d_chi

rows = []
chi1, chi2, chi3 = 0.8, 0.8, 0.8

for t in range(201):
    # S1: Natural decay (no grace, no faith)
    chi1, g1, r1, dc1 = step(chi1, 0.0, 0.5, 0.0, 0.5, omega=0)

    # S2: Growing faith
    F2 = min(1.0, t / 150)
    sin2 = max(0.1, 0.5 - t * 0.002)
    chi2, g2, r2, dc2 = step(chi2, 0.6, sin2, F2, 0.5)

    # S3: Christ intervention at t=100
    F3 = min(1.0, t / 100)
    if t == 100:
        chi3 = chi3 * np.exp(-0.5 + 2.0 * 0.8)  # Christ transformation
    chi3, g3, r3, dc3 = step(chi3, 0.7, 0.5, F3, 0.5, omega=0.02)

    rows.append({
        "t": t,
        "S1_Chi (Decay Only)": round(chi1, 4),
        "S1_dChi": round(dc1, 4),
        "S2_Chi (Growing Faith)": round(chi2, 4),
        "S2_Faith": round(faith(F2), 4),
        "S2_dChi": round(dc2, 4),
        "S3_Chi (Christ@100)": round(chi3, 4),
        "S3_Faith": round(faith(F3), 4),
        "S3_dChi": round(dc3, 4),
    })

df = pd.DataFrame(rows)
df

# --- END SNIPPET 3 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 4: COHERENCE DECAY MODEL
#  Paste this into a separate =PY() cell.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---

import numpy as np
import pandas as pd

def coherence(C0, t, lam, removals=None):
    C = C0 * np.exp(-lam * t)
    if removals:
        for ti in removals:
            if t >= ti:
                C *= max(0.0, 1.0 - 0.3 * np.exp(-0.5 * (t - ti)))
    return max(C, 0)

rows = []
for t in range(201):
    rows.append({
        "Time": t,
        "No Removals": round(coherence(1.0, t, 0.01), 6),
        "1 Removal (t=50)": round(coherence(1.0, t, 0.01, [50]), 6),
        "2 Removals (t=30,70)": round(coherence(1.0, t, 0.01, [30, 70]), 6),
        "Cascade (t=20,40,60,80)": round(coherence(1.0, t, 0.01, [20, 40, 60, 80]), 6),
    })

df = pd.DataFrame(rows)
df

# --- END SNIPPET 4 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 5: GRACE CURVES + CHRIST TRANSFORMATION
#  Paste this into a separate =PY() cell.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---

import numpy as np
import pandas as pd

Rp = np.linspace(0, 1, 101)

df = pd.DataFrame({
    "Receptivity Rp": Rp,
    "Grace [sin=0.1]": np.exp(-0.1 * (1 - Rp)),
    "Grace [sin=0.3]": np.exp(-0.3 * (1 - Rp)),
    "Grace [sin=0.5]": np.exp(-0.5 * (1 - Rp)),
    "Grace [sin=0.7]": np.exp(-0.7 * (1 - Rp)),
    "Grace [sin=1.0]": np.exp(-1.0 * (1 - Rp)),
    "Grace [sin=2.0]": np.exp(-2.0 * (1 - Rp)),
    "Christ [chi=0.3]": 0.3 * np.exp(-0.5 + 1.5 * Rp),
    "Christ [chi=0.5]": 0.5 * np.exp(-0.5 + 1.5 * Rp),
    "Christ [chi=0.8]": 0.8 * np.exp(-0.5 + 1.5 * Rp),
})

df

# --- END SNIPPET 5 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 6: CHART — Master Equation 3 Scenarios
#  This one outputs a matplotlib chart into the Excel cell.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL (set output to "Excel value") ---

import numpy as np
import matplotlib.pyplot as plt

def grace(Rp, s): return np.exp(-s * (1 - Rp))
def faith(F): return (F**1.5) / (1 + F**1.5) if F > 0 else 0
def utility(Ss): return 1 / (1 + np.exp(-2 * (Ss - 1)))

def step(chi, Rp, sin_lvl, F, omega=0.01):
    G = grace(Rp, sin_lvl)
    R = faith(F)
    U = utility(chi)
    P = np.exp(-0.25)
    d = G * (1 + sin_lvl) * P * R * U - 0.03 * chi + omega
    return chi + d

T = 201
chi1, chi2, chi3 = [0.8], [0.8], [0.8]

for t in range(1, T):
    chi1.append(step(chi1[-1], 0.0, 0.5, 0.0, 0))
    chi2.append(step(chi2[-1], 0.6, max(0.1, 0.5-t*0.002), min(1, t/150)))
    c3 = chi3[-1]
    if t == 100:
        c3 = c3 * np.exp(-0.5 + 1.6)
    chi3.append(step(c3, 0.7, 0.5, min(1, t/100), 0.02))

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(chi1, label="S1: Natural Decay", color="#FF4444", linewidth=2)
ax.plot(chi2, label="S2: Growing Faith", color="#44AAFF", linewidth=2)
ax.plot(chi3, label="S3: Christ @ t=100", color="#FFD700", linewidth=2.5)
ax.axvline(x=100, color="#FFD700", linestyle="--", alpha=0.5, label="Christ Intervention")
ax.set_xlabel("Time", fontsize=12)
ax.set_ylabel("Spiritual State χ", fontsize=12)
ax.set_title("Master Equation — Three Spiritual Trajectories", fontsize=14, fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
fig

# --- END SNIPPET 6 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 7: CHART — Fruits of the Spirit Radar
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL (set output to "Excel value") ---

import numpy as np
import matplotlib.pyplot as plt

FRUITS = ["Love", "Joy", "Peace", "Patience", "Kindness",
          "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
WEIGHTS = [0.15, 0.10, 0.12, 0.10, 0.11, 0.10, 0.11, 0.10, 0.11]

def fruit_scores(sigma, coherence):
    return [sigma * coherence * w * 9 for w in WEIGHTS]

# Three states
high_coh = fruit_scores(+1, 0.9)
mid_coh = fruit_scores(+1, 0.5)
low_coh = fruit_scores(-1, 0.7)

angles = np.linspace(0, 2 * np.pi, len(FRUITS), endpoint=False).tolist()
angles += angles[:1]

high_coh += high_coh[:1]
mid_coh += mid_coh[:1]
low_coh += low_coh[:1]

fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.set_facecolor("#0a0e1a")
fig.patch.set_facecolor("#0a0e1a")

ax.plot(angles, high_coh, "o-", color="#FFD700", linewidth=2, label="σ=+1, C=0.9 (Aligned)")
ax.fill(angles, high_coh, color="#FFD700", alpha=0.15)
ax.plot(angles, mid_coh, "o-", color="#00CCFF", linewidth=2, label="σ=+1, C=0.5 (Moderate)")
ax.fill(angles, mid_coh, color="#00CCFF", alpha=0.1)
ax.plot(angles, low_coh, "o-", color="#FF4444", linewidth=2, label="σ=-1, C=0.7 (Decoherent)")
ax.fill(angles, low_coh, color="#FF4444", alpha=0.1)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(FRUITS, fontsize=10, color="white")
ax.tick_params(colors="white")
ax.set_title("Fruits of the Spirit — Coherence Profile", fontsize=14,
             fontweight="bold", color="white", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=9,
          facecolor="#1a1a2e", edgecolor="white", labelcolor="white")
ax.grid(color="white", alpha=0.2)
fig

# --- END SNIPPET 7 ---


# ═══════════════════════════════════════════════════════════════════════════════
#  SNIPPET 8: INTERACTIVE — Read from Excel cells
#  This reads your OWN values from Excel and calculates everything.
# ═══════════════════════════════════════════════════════════════════════════════

# --- COPY BELOW THIS LINE INTO A =PY() CELL ---
# FIRST: Put these labels/values in cells:
#   A1: "Receptivity"    B1: 0.7
#   A2: "Sin Level"      B2: 0.4
#   A3: "Faith"          B3: 0.6
#   A4: "Chi (current)"  B4: 0.5
#   A5: "Kappa (Christ)"  B5: 1.5

import numpy as np
import pandas as pd

# Read your inputs from Excel cells
Rp = xl("B1")
sin_lvl = xl("B2")
F = xl("B3")
chi = xl("B4")
kappa = xl("B5")

# Calculate everything
G = np.exp(-sin_lvl * (1 - Rp))
R = (F ** 1.5) / (1 + F ** 1.5)
U = 1 / (1 + np.exp(-2 * (chi - 1)))
P = np.exp(-0.5 * 0.5)
growth = G * (1 + sin_lvl) * P * R * U
decay = 0.03 * chi
d_chi = growth - decay + 0.01
new_chi = chi + d_chi
chi_redeemed = chi * np.exp(-sin_lvl + kappa * G)

# Fruits
FRUITS = ["Love", "Joy", "Peace", "Patience", "Kindness",
          "Goodness", "Faithfulness", "Gentleness", "Self-Control"]
WEIGHTS = [0.15, 0.10, 0.12, 0.10, 0.11, 0.10, 0.11, 0.10, 0.11]
coherence = G * R  # simplified coherence from grace * faith
sigma = +1 if new_chi > chi else -1

results = {
    "Metric": [
        "Grace G(Rp)", "Faith R(F)", "Utility U(χ)", "Choice P(Q,C)",
        "Growth Term", "Decay Term", "dχ/dt", "New χ",
        "Christ χ_redeemed", "Coherence (G*R)", "Sign σ",
        "---FRUITS---",
    ] + FRUITS + ["Fruit Total"],
    "Value": [
        round(G, 6), round(R, 6), round(U, 6), round(P, 6),
        round(growth, 6), round(decay, 6), round(d_chi, 6), round(new_chi, 6),
        round(chi_redeemed, 6), round(coherence, 6), sigma,
        "---",
    ] + [round(sigma * coherence * w * 9, 4) for w in WEIGHTS]
      + [round(sigma * coherence * sum(WEIGHTS), 4)],
    "Formula": [
        "e^(-S*(1-Rp))", "F^1.5/(1+F^1.5)", "1/(1+e^(-2(χ-1)))", "e^(-Q*C)",
        "G*(1+S)*P*R*U", "δ*χ", "Growth-Decay+Ω", "χ+dχ",
        "χ*e^(-S+κ*G)", "G*R", "+1 if growing", "",
    ] + ["σ*C*w*9"] * 9 + ["σ*C*Σw"],
}

df = pd.DataFrame(results)
df

# --- END SNIPPET 8 ---
