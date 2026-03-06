"""
Chart Generator for Theophysics Analytics
Generates matplotlib charts for coherence metrics, paper comparisons, and analytics.
Charts are saved as PNG files that can be embedded in Obsidian markdown.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for file output

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Dark theme colors matching the app
CHART_COLORS = {
    'bg': '#0d0d0d',
    'surface': '#1a1a1a',
    'text': '#ffffff',
    'text_dim': '#b0b0b0',
    'accent_cyan': '#00d9ff',
    'accent_blue': '#007acc',
    'accent_green': '#4ec9b0',
    'accent_orange': '#ce9178',
    'accent_red': '#f44747',
    'accent_purple': '#c586c0',
    'accent_yellow': '#dcdcaa',
    'grid': '#2a2a2a',
}

# Paper colors for consistent identification
PAPER_COLORS = [
    '#00d9ff', '#007acc', '#4ec9b0', '#ce9178', 
    '#f44747', '#c586c0', '#dcdcaa', '#00ff88',
    '#ff6b6b', '#4dabf7', '#69db7c', '#ffd43b'
]


def setup_dark_style():
    """Configure matplotlib for dark theme."""
    plt.style.use('dark_background')
    plt.rcParams.update({
        'figure.facecolor': CHART_COLORS['bg'],
        'axes.facecolor': CHART_COLORS['surface'],
        'axes.edgecolor': CHART_COLORS['grid'],
        'axes.labelcolor': CHART_COLORS['text'],
        'text.color': CHART_COLORS['text'],
        'xtick.color': CHART_COLORS['text_dim'],
        'ytick.color': CHART_COLORS['text_dim'],
        'grid.color': CHART_COLORS['grid'],
        'legend.facecolor': CHART_COLORS['surface'],
        'legend.edgecolor': CHART_COLORS['grid'],
        'font.family': 'sans-serif',
        'font.size': 10,
    })


def generate_coherence_bar_chart(
    paper_data: List[Dict],
    output_path: Path,
    title: str = "Paper Coherence Comparison"
) -> Path:
    """
    Generate a horizontal bar chart comparing coherence scores across papers.
    
    Args:
        paper_data: List of dicts with 'name', 'coherence', 'grade' keys
        output_path: Directory to save the chart
        title: Chart title
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    names = [p['name'] for p in paper_data]
    scores = [p['coherence'] for p in paper_data]
    grades = [p.get('grade', '') for p in paper_data]
    
    # Color bars based on score
    colors = []
    for score in scores:
        if score >= 0.9:
            colors.append(CHART_COLORS['accent_green'])
        elif score >= 0.8:
            colors.append(CHART_COLORS['accent_cyan'])
        elif score >= 0.7:
            colors.append(CHART_COLORS['accent_blue'])
        elif score >= 0.6:
            colors.append(CHART_COLORS['accent_orange'])
        else:
            colors.append(CHART_COLORS['accent_red'])
    
    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, scores, color=colors, height=0.6, edgecolor='none')
    
    # Add score labels on bars
    for i, (bar, score, grade) in enumerate(zip(bars, scores, grades)):
        width = bar.get_width()
        label = f"{score:.3f} ({grade})" if grade else f"{score:.3f}"
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2,
                label, va='center', ha='left', fontsize=9, color=CHART_COLORS['text'])
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel('Coherence Score')
    ax.set_xlim(0, 1.15)
    ax.set_title(title, fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    # Add vertical lines for grade thresholds
    ax.axvline(x=0.9, color=CHART_COLORS['accent_green'], linestyle='--', alpha=0.5, label='A')
    ax.axvline(x=0.8, color=CHART_COLORS['accent_cyan'], linestyle='--', alpha=0.5, label='A-')
    ax.axvline(x=0.7, color=CHART_COLORS['accent_blue'], linestyle='--', alpha=0.5, label='B')
    
    ax.invert_yaxis()  # Top paper at top
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    output_file = output_path / "coherence_comparison.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


def generate_ten_laws_radar(
    law_scores: Dict[str, float],
    output_path: Path,
    title: str = "Ten Laws Coverage"
) -> Path:
    """
    Generate a radar/spider chart for Ten Laws coverage.
    
    Args:
        law_scores: Dict mapping law names to scores (0-1)
        output_path: Directory to save the chart
        title: Chart title
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    # Ten Laws in order
    laws = [
        "Gravity↔Belonging",
        "Strong↔Covenant", 
        "EM↔Truth",
        "Thermo↔Entropy",
        "Quantum↔Faith",
        "Measure↔Incarnation",
        "Negentropy↔Forgiveness",
        "Relativity↔Compassion",
        "Resonance↔Communion",
        "CPT↔Resurrection"
    ]
    
    # Get scores in order, default to 0
    scores = [law_scores.get(law, 0) for law in laws]
    
    # Number of variables
    N = len(laws)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    scores_plot = scores + scores[:1]  # Close the polygon
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.set_facecolor(CHART_COLORS['surface'])
    
    # Draw the polygon
    ax.plot(angles, scores_plot, 'o-', linewidth=2, color=CHART_COLORS['accent_cyan'])
    ax.fill(angles, scores_plot, alpha=0.25, color=CHART_COLORS['accent_cyan'])
    
    # Draw reference circles
    for level in [0.25, 0.5, 0.75, 1.0]:
        circle = [level] * (N + 1)
        ax.plot(angles, circle, '--', linewidth=0.5, color=CHART_COLORS['grid'], alpha=0.5)
    
    # Set the labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(laws, size=9)
    
    # Set y-axis limits
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'], size=8)
    
    ax.set_title(title, fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'], pad=20)
    
    plt.tight_layout()
    
    output_file = output_path / "ten_laws_radar.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


def generate_trinity_balance_pie(
    father: float,
    son: float,
    spirit: float,
    output_path: Path,
    title: str = "Trinity Balance"
) -> Path:
    """
    Generate a pie chart showing Trinity balance distribution.
    
    Args:
        father: Father/Source percentage
        son: Son/Form percentage
        spirit: Spirit/Coherence percentage
        output_path: Directory to save the chart
        title: Chart title
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    sizes = [father, son, spirit]
    labels = [f'Father (Source)\n{father:.1f}%', 
              f'Son (Form)\n{son:.1f}%', 
              f'Spirit (Coherence)\n{spirit:.1f}%']
    colors = [CHART_COLORS['accent_cyan'], CHART_COLORS['accent_green'], CHART_COLORS['accent_purple']]
    explode = (0.02, 0.02, 0.02)
    
    wedges, texts, autotexts = ax.pie(
        sizes, 
        explode=explode,
        labels=labels,
        colors=colors,
        autopct='',
        startangle=90,
        wedgeprops=dict(width=0.7, edgecolor=CHART_COLORS['bg'], linewidth=2)
    )
    
    # Style the labels
    for text in texts:
        text.set_color(CHART_COLORS['text'])
        text.set_fontsize(11)
    
    # Add center text with balance score
    total = father + son + spirit
    ideal = 33.33
    balance = 1 - (abs(father - ideal) + abs(son - ideal) + abs(spirit - ideal)) / 100
    
    ax.text(0, 0, f"Balance\n{balance:.3f}", ha='center', va='center', 
            fontsize=16, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    ax.set_title(title, fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    plt.tight_layout()
    
    output_file = output_path / "trinity_balance.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


def generate_grace_entropy_gauge(
    grace_ratio: float,
    output_path: Path,
    title: str = "Grace/Entropy Ratio"
) -> Path:
    """
    Generate a gauge chart showing grace vs entropy balance.
    
    Args:
        grace_ratio: Ratio from 0 (all entropy) to 1 (all grace)
        output_path: Directory to save the chart
        title: Chart title
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Create gauge background
    theta = np.linspace(0, np.pi, 100)
    r = 1
    
    # Background arc (entropy side = red, grace side = green)
    for i, t in enumerate(theta[:-1]):
        color_val = i / len(theta)
        if color_val < 0.5:
            color = CHART_COLORS['accent_red']
            alpha = 0.3 + 0.4 * (0.5 - color_val)
        else:
            color = CHART_COLORS['accent_green']
            alpha = 0.3 + 0.4 * (color_val - 0.5)
        ax.fill_between([theta[i], theta[i+1]], [0, 0], [r, r], 
                       color=color, alpha=alpha, transform=ax.transData)
    
    # Draw the arc outline
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    ax.plot(x, y, color=CHART_COLORS['text_dim'], linewidth=2)
    ax.plot([-r, r], [0, 0], color=CHART_COLORS['text_dim'], linewidth=2)
    
    # Draw needle
    needle_angle = np.pi * grace_ratio
    needle_x = 0.85 * np.cos(needle_angle)
    needle_y = 0.85 * np.sin(needle_angle)
    ax.annotate('', xy=(needle_x, needle_y), xytext=(0, 0),
                arrowprops=dict(arrowstyle='->', color=CHART_COLORS['accent_cyan'], lw=3))
    
    # Center circle
    circle = plt.Circle((0, 0), 0.08, color=CHART_COLORS['accent_cyan'])
    ax.add_patch(circle)
    
    # Labels
    ax.text(-1.1, -0.15, 'ENTROPY', ha='center', fontsize=10, color=CHART_COLORS['accent_red'])
    ax.text(1.1, -0.15, 'GRACE', ha='center', fontsize=10, color=CHART_COLORS['accent_green'])
    ax.text(0, -0.3, f'{grace_ratio:.3f}', ha='center', fontsize=20, 
            fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-0.5, 1.2)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.set_title(title, fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'], y=1.0)
    
    plt.tight_layout()
    
    output_file = output_path / "grace_entropy_gauge.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


def generate_concept_network_chart(
    concepts: Dict[str, int],
    output_path: Path,
    title: str = "Top Concepts",
    max_concepts: int = 15
) -> Path:
    """
    Generate a horizontal bar chart of top concepts by count.
    
    Args:
        concepts: Dict mapping concept names to counts
        output_path: Directory to save the chart
        title: Chart title
        max_concepts: Maximum number of concepts to show
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    # Sort and limit
    sorted_concepts = sorted(concepts.items(), key=lambda x: x[1], reverse=True)[:max_concepts]
    names = [c[0] for c in sorted_concepts]
    counts = [c[1] for c in sorted_concepts]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    y_pos = np.arange(len(names))
    
    # Gradient colors based on rank
    colors = [plt.cm.viridis(i / len(names)) for i in range(len(names))]
    
    bars = ax.barh(y_pos, counts, color=colors, height=0.6, edgecolor='none')
    
    # Add count labels
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width + max(counts) * 0.02, bar.get_y() + bar.get_height()/2,
                str(count), va='center', ha='left', fontsize=9, color=CHART_COLORS['text'])
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.set_xlabel('Occurrences')
    ax.set_title(title, fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    output_file = output_path / "top_concepts.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


def generate_all_analytics_charts(
    paper_data: List[Dict],
    law_scores: Dict[str, float],
    trinity: Tuple[float, float, float],
    grace_ratio: float,
    concepts: Dict[str, int],
    output_path: Path
) -> Dict[str, Path]:
    """
    Generate all analytics charts at once.
    
    Args:
        paper_data: List of paper dicts with coherence data
        law_scores: Ten Laws coverage scores
        trinity: Tuple of (father, son, spirit) percentages
        grace_ratio: Grace/entropy ratio (0-1)
        concepts: Top concepts with counts
        output_path: Directory to save charts
    
    Returns:
        Dict mapping chart names to file paths
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    charts = {}
    
    # Generate each chart
    if paper_data:
        charts['coherence'] = generate_coherence_bar_chart(paper_data, output_path)
    
    if law_scores:
        charts['ten_laws'] = generate_ten_laws_radar(law_scores, output_path)
    
    if trinity and len(trinity) == 3:
        charts['trinity'] = generate_trinity_balance_pie(trinity[0], trinity[1], trinity[2], output_path)
    
    if grace_ratio is not None:
        charts['grace_entropy'] = generate_grace_entropy_gauge(grace_ratio, output_path)
    
    if concepts:
        charts['concepts'] = generate_concept_network_chart(concepts, output_path)
    
    return charts


def generate_summary_dashboard(
    paper_data: List[Dict],
    global_metrics: Dict,
    output_path: Path
) -> Path:
    """
    Generate a combined dashboard image with multiple charts.
    
    Args:
        paper_data: List of paper dicts
        global_metrics: Dict with overall_coherence, law_coverage, trinity_balance, grace_entropy
        output_path: Directory to save the chart
    
    Returns:
        Path to the generated PNG file
    """
    setup_dark_style()
    
    fig = plt.figure(figsize=(16, 12))
    
    # Create grid layout
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. Coherence bar chart (top left, spans 2 columns)
    ax1 = fig.add_subplot(gs[0, :2])
    if paper_data:
        names = [p['name'][:15] for p in paper_data]
        scores = [p['coherence'] for p in paper_data]
        colors = [CHART_COLORS['accent_cyan'] if s >= 0.8 else CHART_COLORS['accent_orange'] for s in scores]
        y_pos = np.arange(len(names))
        ax1.barh(y_pos, scores, color=colors, height=0.6)
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(names, fontsize=8)
        ax1.set_xlim(0, 1)
        ax1.set_xlabel('Coherence')
        ax1.invert_yaxis()
    ax1.set_title('Paper Coherence', fontsize=12, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    # 2. Global metrics summary (top right)
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')
    metrics_text = f"""
    GLOBAL METRICS
    ─────────────────
    Overall Coherence: {global_metrics.get('overall_coherence', 0):.3f}
    Grade: {global_metrics.get('grade', '-')}
    Law Coverage: {global_metrics.get('law_coverage', 0):.1%}
    Trinity Balance: {global_metrics.get('trinity_balance', 0):.3f}
    Grace/Entropy: {global_metrics.get('grace_entropy', 0):.3f}
    Papers Analyzed: {global_metrics.get('papers_analyzed', 0)}
    """
    ax2.text(0.1, 0.9, metrics_text, transform=ax2.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             color=CHART_COLORS['text'],
             bbox=dict(boxstyle='round', facecolor=CHART_COLORS['surface'], edgecolor=CHART_COLORS['grid']))
    
    # 3. Grace/Entropy gauge (bottom left)
    ax3 = fig.add_subplot(gs[1, 0])
    grace = global_metrics.get('grace_entropy', 0.5)
    theta = np.linspace(0, np.pi, 50)
    x = np.cos(theta)
    y = np.sin(theta)
    ax3.plot(x, y, color=CHART_COLORS['text_dim'], linewidth=2)
    ax3.plot([-1, 1], [0, 0], color=CHART_COLORS['text_dim'], linewidth=2)
    needle_angle = np.pi * grace
    ax3.annotate('', xy=(0.8*np.cos(needle_angle), 0.8*np.sin(needle_angle)), 
                xytext=(0, 0), arrowprops=dict(arrowstyle='->', color=CHART_COLORS['accent_cyan'], lw=2))
    ax3.text(0, -0.2, f'{grace:.3f}', ha='center', fontsize=14, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    ax3.set_xlim(-1.3, 1.3)
    ax3.set_ylim(-0.4, 1.1)
    ax3.set_aspect('equal')
    ax3.axis('off')
    ax3.set_title('Grace/Entropy', fontsize=12, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    # 4. Trinity balance (bottom middle)
    ax4 = fig.add_subplot(gs[1, 1])
    trinity = [38.1, 28.6, 33.3]  # Default from validation report
    colors = [CHART_COLORS['accent_cyan'], CHART_COLORS['accent_green'], CHART_COLORS['accent_purple']]
    ax4.pie(trinity, colors=colors, startangle=90, 
            wedgeprops=dict(width=0.6, edgecolor=CHART_COLORS['bg']))
    ax4.text(0, 0, f"{global_metrics.get('trinity_balance', 0.883):.3f}", 
             ha='center', va='center', fontsize=14, fontweight='bold', color=CHART_COLORS['text'])
    ax4.set_title('Trinity Balance', fontsize=12, fontweight='bold', color=CHART_COLORS['accent_cyan'])
    
    # 5. Timestamp and info (bottom right)
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_text = f"""
    Generated: {timestamp}
    
    Theophysics Analytics
    Lowe Coherence Lagrangian
    
    Charts auto-regenerate
    on each scan.
    """
    ax5.text(0.1, 0.9, info_text, transform=ax5.transAxes, fontsize=10,
             verticalalignment='top', color=CHART_COLORS['text_dim'])
    
    plt.suptitle('📊 THEOPHYSICS ANALYTICS DASHBOARD', fontsize=16, fontweight='bold', 
                 color=CHART_COLORS['accent_cyan'], y=0.98)
    
    output_file = output_path / "analytics_dashboard.png"
    plt.savefig(output_file, dpi=150, facecolor=CHART_COLORS['bg'], edgecolor='none')
    plt.close()
    
    return output_file


if __name__ == "__main__":
    # Test chart generation
    test_output = Path("./test_charts")
    test_output.mkdir(exist_ok=True)
    
    # Sample data
    test_papers = [
        {"name": "P01 - Logos Principle", "coherence": 0.85, "grade": "A-"},
        {"name": "P02 - Quantum Bridge", "coherence": 0.78, "grade": "B+"},
        {"name": "P03 - Algorithm Reality", "coherence": 0.82, "grade": "A-"},
        {"name": "P04 - Hard Problem", "coherence": 0.75, "grade": "B"},
    ]
    
    test_laws = {
        "Gravity↔Belonging": 1.0,
        "Strong↔Covenant": 0.9,
        "EM↔Truth": 1.0,
        "Thermo↔Entropy": 1.0,
        "Quantum↔Faith": 0.95,
        "Measure↔Incarnation": 0.85,
        "Negentropy↔Forgiveness": 0.9,
        "Relativity↔Compassion": 0.88,
        "Resonance↔Communion": 0.75,
        "CPT↔Resurrection": 0.92,
    }
    
    print("Generating test charts...")
    generate_coherence_bar_chart(test_papers, test_output)
    generate_ten_laws_radar(test_laws, test_output)
    generate_trinity_balance_pie(38.1, 28.6, 33.3, test_output)
    generate_grace_entropy_gauge(0.5, test_output)
    generate_concept_network_chart({"quantum": 86, "consciousness": 55, "information": 102}, test_output)
    print(f"Charts saved to {test_output}")
