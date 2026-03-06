#!/usr/bin/env python3
"""
Render REVISED Paper 3 visualizations with fixes:
1. Kolmogorov - Massive scale, better mechanism
2. Landauer - Clear layout, readable text
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
RED_CHAOS = '#FF0000'
GREEN_ACTUAL = '#00FF00'
WHITE_SOURCE = '#FFFFFF'

def create_sphere_with_glow(ax, x_center, y_center, z_center, radius, core_color, glow_color, core_alpha):
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

def render_kolmogorov_revised():
    """REVISED: Kolmogorov Complexity - Massive scale, better mechanism"""
    print("  Rendering REVISED: Kolmogorov Complexity...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Left Side: Low-K (Logos)
    # Tiny program
    create_sphere_with_glow(ax, -10, 0, 0, 0.5, GOLD_LOGOS, GOLD_LOGOS, 1.0)
    ax.text(-10, 0, 2, 'Low-K Program (Simple)', color=GOLD_LOGOS,
            ha='center', fontsize=24, weight='bold')

    # MASSIVE ordered output
    ax.text(-2, 0, 10, 'MASSIVE Ordered Output (K(x) ≈ 0)', color=GOLD_LOGOS,
            ha='center', fontsize=22, style='italic')
    x_l, y_l, z_l = np.meshgrid(np.linspace(-5, 5, 5),
                                np.linspace(-5, 5, 5),
                                np.linspace(-5, 5, 5))
    ax.scatter(x_l, y_l, z_l, c=GOLD_LOGOS, s=300, alpha=0.8, marker='D')
    for i in range(5):
        for j in range(5):
            ax.plot(x_l[i,j,:], y_l[i,j,:], z_l[i,j,:], 'w-', alpha=0.1)
            ax.plot(x_l[i,:,j], y_l[i,:,j], z_l[i,:,j], 'w-', alpha=0.1)
            ax.plot(x_l[:,i,j], y_l[:,i,j], z_l[:,i,j], 'w-', alpha=0.1)
    ax.plot([-10, -3], [0, 0], [0, 0], color=GOLD_LOGOS,
            linewidth=4, alpha=0.7, linestyle='--')

    # Right Side: High-K (Chaos)
    ax.text(8, 0, 8, 'High-K Program (Complex)', color=RED_CHAOS,
            ha='center', fontsize=24, weight='bold')
    np.random.seed(42)
    x_prog_c = np.random.normal(8, 2, 800)
    y_prog_c = np.random.normal(0, 2, 800)
    z_prog_c = np.random.normal(0, 2, 800)
    ax.scatter(x_prog_c, y_prog_c, z_prog_c, c=RED_CHAOS, s=60, alpha=0.15)
    create_sphere_with_glow(ax, 8, 0, 0, 2.0, RED_CHAOS, RED_CHAOS, 0.5)

    # Tiny chaotic output
    ax.text(8, 0, -6, 'TINY Chaotic Output (K(x) ≈ |x|)', color=RED_CHAOS,
            ha='center', fontsize=22, style='italic')
    x_out_c = np.random.normal(8, 0.5, 100)
    y_out_c = np.random.normal(0, 0.5, 100)
    z_out_c = np.random.normal(-4, 0.5, 100)
    ax.scatter(x_out_c, y_out_c, z_out_c, c=RED_CHAOS, s=30, alpha=0.5)
    ax.plot([8, 8], [0, 0], [0, -3.5], color=RED_CHAOS,
            linewidth=4, alpha=0.7, linestyle='--')

    fig.text(0.5, 0.95, 'Paper 3: Kolmogorov Complexity (REVISED)',
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'The "Program Size" of Reality: Efficiency vs. Inefficiency',
             ha='center', fontsize=24, color=WHITE_SOURCE, style='italic')
    fig.text(0.5, 0.05, 'Low-K (Order) creates vast structure from a simple program. High-K (Chaos) requires a massive program for a tiny, chaotic result.',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=25)
    ax.set_xlim([-12, 12])
    ax.set_ylim([-8, 8])
    ax.set_zlim([-8, 12])

    plt.savefig(OUTPUT_DIR / 'P03-01-Kolmogorov-Complexity-REVISED.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-01-Kolmogorov-Complexity-REVISED.png")

def render_landauer_revised():
    """REVISED: Landauer's Principle - Clear layout, readable text"""
    print("  Rendering REVISED: Landauer's Principle...")

    fig = plt.figure(figsize=(20, 14), facecolor=DARK_BG)
    ax = fig.add_subplot(111, projection='3d', facecolor=DARK_BG)
    ax.set_axis_off()

    # Stage 1: Superposition (LEFT)
    ax.text(-8, 0, 10, '1. Superposition (2 States)', color=WHITE_SOURCE,
            ha='center', fontsize=24, weight='bold')
    create_sphere_with_glow(ax, -8, 0, 5, 2.5, PURPLE_FIELD, PURPLE_FIELD, 0.5)
    ax.text(-8, 0, 8.5, "State '1'", color=PURPLE_FIELD, ha='center', fontsize=22, weight='bold')
    create_sphere_with_glow(ax, -8, 0, -5, 2.5, PURPLE_FIELD, PURPLE_FIELD, 0.5)
    ax.text(-8, 0, -1.5, "State '0'", color=PURPLE_FIELD, ha='center', fontsize=22, weight='bold')

    # Stage 2: Erasure (CENTER)
    ax.text(0, 0, 10, '2. Observer "Erasure"', color=CYAN_OBSERVER,
            ha='center', fontsize=24, weight='bold')
    ax.plot([-5, 0], [0, 0], [5, 5], color=CYAN_OBSERVER, linewidth=8, alpha=0.9)
    np.random.seed(42)
    x_shatter = np.random.normal(0.5, 0.5, 100)
    y_shatter = np.random.normal(0, 0.5, 100)
    z_shatter = np.random.normal(5, 0.5, 100)
    ax.scatter(x_shatter, y_shatter, z_shatter, c=PURPLE_FIELD, s=50, alpha=0.5)
    create_sphere_with_glow(ax, 0, 0, -5, 2.5, GREEN_ACTUAL, GREEN_ACTUAL, 0.9)
    ax.text(0, 0, -1.5, "Forced to '0'", color=GREEN_ACTUAL, ha='center', fontsize=22, weight='bold')
    ax.plot([-8, 0], [0, 0], [-5, -5], 'w--', alpha=0.3)

    # Stage 3: Cost (RIGHT)
    ax.text(8, 0, 10, '3. The "Cost" (Heat/Entropy)', color=RED_CHAOS,
            ha='center', fontsize=24, weight='bold')
    np.random.seed(1)
    x_heat = np.random.normal(8, 2, 800)
    y_heat = np.random.normal(0, 2, 800)
    z_heat = np.random.normal(0, 2, 800)
    ax.scatter(x_heat, y_heat, z_heat, c=RED_CHAOS, s=80, alpha=0.15)
    ax.plot([1, 7], [0, 0], [5, 0], color=RED_CHAOS,
            linewidth=4, alpha=0.7, linestyle='--')
    ax.text(8, 0, -6, 'Q = k_B * T * ln(2)', color=RED_CHAOS,
            ha='center', fontsize=28, weight='bold',
            bbox=dict(facecolor=DARK_BG, alpha=0.5, edgecolor='none', pad=10))

    fig.text(0.5, 0.95, "Paper 3: Landauer's Principle (REVISED)",
             ha='center', fontsize=60, color='white', weight='bold')
    fig.text(0.5, 0.90, 'The Physical Cost of Erasing Information',
             ha='center', fontsize=24, color=WHITE_SOURCE, style='italic')
    fig.text(0.5, 0.05, 'Erasing 1 bit (destroying 2 states to create 1) is not free. The lost information is released as heat (entropy).',
             ha='center', fontsize=20, color='gray', style='italic')

    ax.view_init(elev=20, azim=25)
    ax.set_xlim([-12, 12])
    ax.set_ylim([-8, 8])
    ax.set_zlim([-10, 12])

    plt.savefig(OUTPUT_DIR / 'P03-03-Landauer-Principle-REVISED.png',
                dpi=300, facecolor=DARK_BG, bbox_inches='tight')
    plt.close()
    print("    ✓ Saved P03-03-Landauer-Principle-REVISED.png")

def main():
    print("="*80)
    print("RENDERING REVISED PAPER 3 VISUALIZATIONS")
    print("="*80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_kolmogorov_revised()
    render_landauer_revised()

    print("\n" + "="*80)
    print("✓ REVISED VISUALIZATIONS COMPLETE!")
    print("="*80)
    print("\nFixed:")
    print("  - Kolmogorov: Massive scale, better mechanism")
    print("  - Landauer: Clear layout, readable text")

if __name__ == "__main__":
    main()
