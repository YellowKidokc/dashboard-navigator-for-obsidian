#!/usr/bin/env python3
"""
Render all 5 Paper 3 visualizations - The Algorithm of Reality
100% Standard with unique geometries for each
"""

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import os

OUTPUT_DIR = Path(os.getenv("THEOPHYSICS_P3_OUTPUT_DIR", r"O:\_Theophysics_v3\_META\Assets\Images\logos papers\P3_Algorithm_Reality"))

# TVE Colors
DARK_BG = '#0a0a0a'
CYAN_OBSERVER = '#00FFFF'
GOLD_LOGOS = '#FFD700'
PURPLE_FIELD = '#9933FF'
GREEN_ACTUAL = '#00FF00'
RED_CHAOS = '#FF0000'
WHITE_SOURCE = '#FFFFFF'
SON_INTERNAL = '#FF00FF'

def create_sphere(ax, x_center, y_center, z_center, radius, color, alpha):
    """Helper for spheres"""
    theta = np.linspace(0, 2 * np.pi, 60)
    phi = np.linspace(0, np.pi, 60)
    THETA, PHI = np.meshgrid(theta, phi)
    x = radius * np.sin(PHI) * np.cos(THETA) + x_center
    y = radius * np.sin(PHI) * np.sin(THETA) + y_center
    z = radius * np.cos(PHI) + z_center
    ax.plot_surface(x, y, z, color=color, alpha=alpha,
                    rstride=1, cstride=1, linewidth=0, antialiased=True)

def create_sphere_with_glow(ax, x_center, y_center, z_center, radius, core_color, glow_color, core_alpha, label_text=None, text_offset=0):
    """Helper for glowing spheres"""
    theta = np.linspace(0, 2 * np.pi, 60)
    phi = np.linspace(0, np.pi, 60)
    THETA, PHI = np.meshgrid(theta, phi)
    x_core = radius * np.sin(PHI) * np.cos(THETA) + x_center
    y_core = radius * np.sin(PHI) * np.sin(THETA) + y_center
    z_core = radius * np.cos(PHI) + z_center
    ax.plot_surface(x_core, y_core, z_core, color=core_color, alpha=core_alpha,
                    rstride=1, cstride=1, linewidth=0, antialiased=True)
    for r_glow_mult in [1.2, 1.5, 1.8]:
        r_glow = radius * r_glow_mult
        x_glow = r_glow * np.sin(PHI) * np.cos(THETA) + x_center
        y_glow = r_glow * np.sin(PHI) * np.sin(THETA) + y_center
        z_glow = r_glow * np.cos(PHI) + z_center
        ax.plot_surface(x_glow, y_glow, z_glow, color=glow_color, alpha=0.08 / r_glow_mult,
                        rstride=1, cstride=1, linewidth=0, antialiased=True)
    if label_text:
        ax.text(x_center, y_center, z_center + radius + text_offset, label_text,
                color=WHITE_SOURCE, ha='center', fontsize=24, weight='bold')

def plot_glowing_line(ax, x_data, y_data, z_data, core_color, glow_color, core_linewidth, glow_linewidth, alpha):
    """Helper for glowing lines"""
    ax.plot(x_data, y_data, z_data, color=glow_color, linewidth=glow_linewidth, alpha=alpha/2)
    ax.plot(x_data, y_data, z_data, color=core_color, linewidth=core_linewidth, alpha=alpha)

def render_kolmogorov_complexity():
    """1. Kolmogorov Complexity: Order vs. Chaos"""
    print("  Rendering 1: Kolmogorov Complexity...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Left Side: Low-K (Logos)
    ax.text(-8, 0, 8, 'Low-K Program (Simple)', color=GOLD_LOGOS,
            ha='center', fontsize=24, weight='bold')
    create_sphere(ax, -8, 0, 5, 0.5, GOLD_LOGOS, 1.0)

    # Crystal lattice
    x_l, y_l, z_l = np.meshgrid(np.linspace(-10, -6, 4),
                                np.linspace(-2, 2, 4),
                                np.linspace(-2, 2, 4))
    ax.scatter(x_l, y_l, z_l, c=GOLD_LOGOS, s=200, alpha=0.8, marker='D')
    for i in range(4):
        for j in range(4):
            ax.plot(x_l[i,j,:], y_l[i,j,:], z_l[i,j,:], 'w-', alpha=0.1)
            ax.plot(x_l[i,:,j], y_l[i,:,j], z_l[i,:,j], 'w-', alpha=0.1)
            ax.plot(x_l[:,i,j], y_l[:,i,j], z_l[:,i,j], 'w-', alpha=0.1)

    # Right Side: High-K (Chaos)
    ax.text(8, 0, 8, 'High-K Program (Complex)', color=RED_CHAOS,
            ha='center', fontsize=24, weight='bold')
    create_sphere(ax, 8, 0, 5, 2.5, RED_CHAOS, 0.7)

    np.random.seed(42)
    x_c = np.random.uniform(6, 10, 300)
    y_c = np.random.uniform(-2, 2, 300)
    z_c = np.random.uniform(-2, 2, 300)
    ax.scatter(x_c, y_c, z_c, c=RED_CHAOS, s=50, alpha=0.5)

    fig.text(0.5, 0.95, 'Paper 3: Kolmogorov Complexity (K(x))',
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'The "Program Size" of Reality',
             ha='center', fontsize=24, color=WHITE_SOURCE, style='italic')
    fig.text(0.5, 0.05, 'Low-K (Order) creates vast structure from a simple program. High-K (Chaos) requires a program as large as itself.',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=15, azim=0)
    ax.set_xlim([-12, 12])
    ax.set_ylim([-6, 6])
    ax.set_zlim([-4, 10])

    plt.savefig(OUTPUT_DIR / 'P03-01-Kolmogorov-Complexity-Order-vs-Chaos.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-01-Kolmogorov-Complexity-Order-vs-Chaos.png")

def render_compression_drive():
    """2. The Logos Compression Drive"""
    print("  Rendering 2: Logos Compression Drive...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Time = 0: High Entropy
    np.random.seed(1)
    z_start = 10
    x_cloud = np.random.normal(0, 5, 1000)
    y_cloud = np.random.normal(0, 5, 1000)
    z_cloud = np.random.normal(z_start, 0.5, 1000)
    ax.scatter(x_cloud, y_cloud, z_cloud, c=PURPLE_FIELD, s=80, alpha=0.1)
    ax.text(0, 0, 13, 'T=0: High Entropy (Λ ≈ 1)', color=PURPLE_FIELD,
            ha='center', fontsize=24, weight='bold')

    # Compression Funnel
    theta = np.linspace(0, 2 * np.pi, 100)
    z_cone = np.linspace(10, -10, 100)
    r_cone = np.linspace(6, 0.2, 100)
    X_cone = r_cone[:, np.newaxis] * np.cos(theta)
    Y_cone = r_cone[:, np.newaxis] * np.sin(theta)
    Z_cone = np.tile(z_cone[:, np.newaxis], (1, len(theta)))
    ax.plot_wireframe(X_cone, Y_cone, Z_cone, color=GOLD_LOGOS, alpha=0.4, linewidth=1)
    ax.text(7, 0, 0, 'Logos Compression Drive', color=GOLD_LOGOS,
            ha='center', fontsize=22, weight='bold')

    # Time = Final: Coherent State
    z_end = np.linspace(-10, -14, 50)
    x_end = np.zeros_like(z_end)
    y_end = np.zeros_like(z_end)
    plot_glowing_line(ax, x_end, y_end, z_end, GREEN_ACTUAL, GREEN_ACTUAL, 5, 15, 1.0)
    ax.text(0, 0, -16, 'T=Final: Coherent State (Λ ≈ 0)', color=GREEN_ACTUAL,
            ha='center', fontsize=24, weight='bold')

    fig.text(0.5, 0.95, 'Paper 3: The Logos Compression Drive',
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'Reality Evolves to Minimize Complexity (dΛ/dt < 0)',
             ha='center', fontsize=24, color=GOLD_LOGOS, style='italic')
    fig.text(0.5, 0.05, 'The universe is an algorithm compressing chaotic potential into coherent, ordered reality over time.',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=45)
    ax.set_xlim([-10, 10])
    ax.set_ylim([-10, 10])
    ax.set_zlim([-18, 15])

    plt.savefig(OUTPUT_DIR / 'P03-02-Logos-Compression-Drive-dLambda-dt.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-02-Logos-Compression-Drive-dLambda-dt.png")

def render_landauer_principle():
    """3. Landauer's Principle: The Cost of Erasure"""
    print("  Rendering 3: Landauer's Principle...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Stage 1: Bit in Superposition
    ax.text(-8, 0, 8, '1. Bit in Superposition (2 States)', color=WHITE_SOURCE,
            ha='center', fontsize=24, weight='bold')
    create_sphere_with_glow(ax, -8, 0, 3, 1.5, PURPLE_FIELD, PURPLE_FIELD, 0.4, "State '1'")
    create_sphere_with_glow(ax, -8, 0, -3, 1.5, PURPLE_FIELD, PURPLE_FIELD, 0.4, "State '0'")

    # Stage 2: Erasure
    ax.text(0, 0, 10, '2. Observer "Erasure"', color=CYAN_OBSERVER,
            ha='center', fontsize=24, weight='bold')
    create_sphere_with_glow(ax, 0, 5, 0, 2, CYAN_OBSERVER, CYAN_OBSERVER, 0.8)
    ax.plot([-8, 0], [0, 5], [3, 0], 'w--', alpha=0.5)
    ax.plot([-8, 0], [0, 5], [-3, 0], 'w--', alpha=0.5)
    create_sphere_with_glow(ax, 0, 0, -3, 1.5, GREEN_ACTUAL, GREEN_ACTUAL, 0.8, "Forced to '0'")

    # Stage 3: The Cost
    ax.text(8, 0, 8, '3. The "Cost" (Heat)', color=RED_CHAOS,
            ha='center', fontsize=24, weight='bold')
    np.random.seed(42)
    x_heat = np.random.normal(8, 1.5, 500)
    y_heat = np.random.normal(0, 1.5, 500)
    z_heat = np.random.normal(0, 1.5, 500)
    ax.scatter(x_heat, y_heat, z_heat, c=RED_CHAOS, s=70, alpha=0.2)
    ax.text(8, 0, 0, 'Q = k_B * T * ln(2)', color=RED_CHAOS,
            ha='center', fontsize=20, weight='bold')
    ax.plot([0, 8], [0, 0], [0, 0], color=RED_CHAOS,
            linewidth=5, alpha=0.7, linestyle='-')

    fig.text(0.5, 0.95, "Paper 3: Landauer's Principle",
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'The Physical Cost of Erasing Information',
             ha='center', fontsize=24, color=WHITE_SOURCE, style='italic')
    fig.text(0.5, 0.05, 'Erasing 1 bit of information (destroying 2 states to create 1) must release heat (entropy). Information is physical.',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=-45)
    ax.set_xlim([-12, 12])
    ax.set_ylim([-8, 8])
    ax.set_zlim([-8, 12])

    plt.savefig(OUTPUT_DIR / 'P03-03-Landauer-Principle-Cost-of-Erasure.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-03-Landauer-Principle-Cost-of-Erasure.png")

def render_gr_qm_duality():
    """4. GR-QM Unification: Compression Duality"""
    print("  Rendering 4: GR-QM Unification...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Top: Quantum Foam
    x_qm = np.linspace(-8, 8, 100)
    y_qm = np.linspace(-8, 8, 100)
    X_qm, Y_qm = np.meshgrid(x_qm, y_qm)
    np.random.seed(42)
    Z_qm = 0.5 * np.sin(X_qm) + 0.5 * np.cos(Y_qm) + np.random.normal(0, 0.3, X_qm.shape)
    Z_qm += 8
    ax.plot_surface(X_qm, Y_qm, Z_qm, color=PURPLE_FIELD, alpha=0.3,
                    rstride=5, cstride=5, linewidth=0)
    ax.text(0, 0, 11, 'Quantum Mechanics (QM): The Compression Process',
            color=PURPLE_FIELD, ha='center', fontsize=22, weight='bold')

    # Bottom: Smooth Spacetime
    x_gr = np.linspace(-8, 8, 100)
    y_gr = np.linspace(-8, 8, 100)
    X_gr, Y_gr = np.meshgrid(x_gr, y_gr)
    Z_gr = -2 * np.exp(-(X_gr**2 + Y_gr**2) / 20)
    Z_gr -= 8
    ax.plot_surface(X_gr, Y_gr, Z_gr, color=GOLD_LOGOS, alpha=0.7,
                    rstride=2, cstride=2, linewidth=0, antialiased=True)
    ax.text(0, 0, -5, 'General Relativity (GR): The Compressed Output',
            color=GOLD_LOGOS, ha='center', fontsize=22, weight='bold')

    # Collapse lines
    num_lines = 15
    np.random.seed(1)
    for i in range(num_lines):
        x_line = np.random.uniform(-7, 7)
        y_line = np.random.uniform(-7, 7)
        z_start = 0.5 * np.sin(x_line) + 0.5 * np.cos(y_line) + 8
        z_end = -2 * np.exp(-(x_line**2 + y_line**2) / 20) - 8
        ax.plot([x_line, x_line], [y_line, y_line], [z_start, z_end],
                color=CYAN_OBSERVER, linewidth=2, alpha=0.6, linestyle=':')
    ax.text(0, 0, 2, 'Conscious Observation (Compression)',
            color=CYAN_OBSERVER, ha='center', fontsize=24, weight='bold')

    fig.text(0.5, 0.95, 'Paper 3: GR-QM Unification',
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'GR is the Output, QM is the Process',
             ha='center', fontsize=24, color=WHITE_SOURCE, style='italic')
    fig.text(0.5, 0.05, 'QM is the chaotic foam of potential. GR is the smooth spacetime that emerges *after* compression.',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=45)
    ax.set_xlim([-10, 10])
    ax.set_ylim([-10, 10])
    ax.set_zlim([-12, 12])

    plt.savefig(OUTPUT_DIR / 'P03-04-GR-QM-Unification-Compression-Duality.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-04-GR-QM-Unification-Compression-Duality.png")

def render_dna_compression():
    """5. Biological Compression: The DNA Mechanism"""
    print("  Rendering 5: Biological Compression (DNA)...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Left: High-K Organism Data
    np.random.seed(1)
    x_cloud = np.random.normal(-8, 3, 2000)
    y_cloud = np.random.normal(0, 5, 2000)
    z_cloud = np.random.normal(0, 5, 2000)
    ax.scatter(x_cloud, y_cloud, z_cloud, c=PURPLE_FIELD, s=70, alpha=0.1)
    ax.text(-8, 0, 10, 'High-K "Organism" Data (Trillions of cells)',
            color=PURPLE_FIELD, ha='center', fontsize=22, weight='bold')

    # Right: DNA Double Helix
    t_helix = np.linspace(-8, 8, 100)
    x_h1 = 8 + np.cos(t_helix)
    y_h1 = np.sin(t_helix)
    z_h1 = t_helix
    plot_glowing_line(ax, x_h1, y_h1, z_h1, SON_INTERNAL, SON_INTERNAL, 4, 12, 0.9)
    x_h2 = 8 - np.cos(t_helix)
    y_h2 = -np.sin(t_helix)
    z_h2 = t_helix
    plot_glowing_line(ax, x_h2, y_h2, z_h2, SON_INTERNAL, SON_INTERNAL, 4, 12, 0.9)

    num_rungs = 20
    t_rungs = np.linspace(-8, 8, num_rungs)
    for t in t_rungs:
        ax.plot([8+np.cos(t), 8-np.cos(t)], [np.sin(t), -np.sin(t)], [t, t],
                color=WHITE_SOURCE, linewidth=2, alpha=0.5)
    ax.text(8, 0, 10, 'Low-K "DNA Program"', color=SON_INTERNAL,
            ha='center', fontsize=22, weight='bold')

    # Compression Funnel
    for i in range(50):
        start_idx = np.random.randint(0, 2000)
        end_idx = np.random.randint(0, 100)
        plot_glowing_line(ax,
            [x_cloud[start_idx], x_h1[end_idx]],
            [y_cloud[start_idx], y_h1[end_idx]],
            [z_cloud[start_idx], z_h1[end_idx]],
            CYAN_OBSERVER, CYAN_OBSERVER, 0.5, 2, 0.1
        )
    ax.text(0, 0, 0, 'Logos Compression Drive', color=CYAN_OBSERVER,
            ha='center', fontsize=24, weight='bold')

    fig.text(0.5, 0.95, 'Paper 3: Biological Compression',
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'DNA as a Low-Kolmogorov-Complexity Algorithm',
             ha='center', fontsize=24, color=SON_INTERNAL, style='italic')
    fig.text(0.5, 0.05, 'Evolution compresses the "data" of a full organism (High-K) into a simple, elegant program (Low-K DNA).',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=45)
    ax.set_xlim([-15, 15])
    ax.set_ylim([-8, 8])
    ax.set_zlim([-10, 12])

    plt.savefig(OUTPUT_DIR / 'P03-05-Biological-Compression-DNA-Mechanism.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-05-Biological-Compression-DNA-Mechanism.png")

def main():
    print("="*80)
    print("RENDERING PAPER 3: THE ALGORITHM OF REALITY (5 VISUALIZATIONS)")
    print("="*80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_kolmogorov_complexity()
    render_compression_drive()
    render_landauer_principle()
    render_gr_qm_duality()
    render_dna_compression()

    print("\n" + "="*80)
    print("✓ ALL 5 PAPER 3 VISUALIZATIONS COMPLETE!")
    print("="*80)
    print(f"\nOutput: {OUTPUT_DIR}")
    print("\nEach visualization uses unique geometry showing information compression!")

if __name__ == "__main__":
    main()
