"""
Interactive HTML Dashboard Generator for Theophysics Analytics
Uses Plotly for interactive charts that can handle complex cross-paper/cross-theory analysis.
Generates self-contained HTML files that open in any browser.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import html


# Dark theme colors
DARK_THEME = {
    'bg': '#0d0d0d',
    'surface': '#1a1a1a',
    'panel': '#242424',
    'text': '#ffffff',
    'text_dim': '#b0b0b0',
    'grid': '#2a2a2a',
    'accent_cyan': '#00d9ff',
    'accent_blue': '#007acc',
    'accent_green': '#4ec9b0',
    'accent_orange': '#ce9178',
    'accent_red': '#f44747',
    'accent_purple': '#c586c0',
    'accent_yellow': '#dcdcaa',
}

# Plotly layout template
PLOTLY_DARK_TEMPLATE = {
    'layout': {
        'paper_bgcolor': DARK_THEME['bg'],
        'plot_bgcolor': DARK_THEME['surface'],
        'font': {'color': DARK_THEME['text'], 'family': 'Segoe UI, sans-serif'},
        'title': {'font': {'color': DARK_THEME['accent_cyan'], 'size': 18}},
        'xaxis': {
            'gridcolor': DARK_THEME['grid'],
            'linecolor': DARK_THEME['grid'],
            'tickfont': {'color': DARK_THEME['text_dim']}
        },
        'yaxis': {
            'gridcolor': DARK_THEME['grid'],
            'linecolor': DARK_THEME['grid'],
            'tickfont': {'color': DARK_THEME['text_dim']}
        },
        'legend': {
            'bgcolor': DARK_THEME['surface'],
            'bordercolor': DARK_THEME['grid'],
            'font': {'color': DARK_THEME['text']}
        }
    }
}


def create_coherence_comparison_chart(paper_data: List[Dict]) -> go.Figure:
    """Create interactive horizontal bar chart for paper coherence."""
    
    names = [p['name'] for p in paper_data]
    scores = [p['coherence'] for p in paper_data]
    grades = [p.get('grade', '') for p in paper_data]
    
    # Color based on score
    colors = []
    for score in scores:
        if score >= 0.9:
            colors.append(DARK_THEME['accent_green'])
        elif score >= 0.8:
            colors.append(DARK_THEME['accent_cyan'])
        elif score >= 0.7:
            colors.append(DARK_THEME['accent_blue'])
        elif score >= 0.6:
            colors.append(DARK_THEME['accent_orange'])
        else:
            colors.append(DARK_THEME['accent_red'])
    
    fig = go.Figure(go.Bar(
        x=scores,
        y=names,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.3f} ({g})" for s, g in zip(scores, grades)],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Coherence: %{x:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Paper Coherence Comparison',
        xaxis_title='Coherence Score',
        yaxis_title='',
        xaxis_range=[0, 1.15],
        height=max(400, len(names) * 40),
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    # Add grade threshold lines
    for threshold, label, color in [(0.9, 'A', DARK_THEME['accent_green']), 
                                     (0.8, 'A-', DARK_THEME['accent_cyan']),
                                     (0.7, 'B', DARK_THEME['accent_blue'])]:
        fig.add_vline(x=threshold, line_dash="dash", line_color=color, opacity=0.5,
                     annotation_text=label, annotation_position="top")
    
    fig.update_yaxes(autorange="reversed")
    
    return fig


def create_ten_laws_radar(law_scores: Dict[str, float]) -> go.Figure:
    """Create interactive radar chart for Ten Laws coverage."""
    
    laws = list(law_scores.keys())
    scores = list(law_scores.values())
    
    # Close the polygon
    laws_closed = laws + [laws[0]]
    scores_closed = scores + [scores[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=laws_closed,
        fill='toself',
        fillcolor=f'rgba(0, 217, 255, 0.2)',
        line_color=DARK_THEME['accent_cyan'],
        name='Coverage',
        hovertemplate='<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Ten Laws Coverage (Physical ↔ Spiritual)',
        polar=dict(
            bgcolor=DARK_THEME['surface'],
            radialaxis=dict(
                visible=True,
                range=[0, 1.1],
                gridcolor=DARK_THEME['grid'],
                tickfont=dict(color=DARK_THEME['text_dim'])
            ),
            angularaxis=dict(
                gridcolor=DARK_THEME['grid'],
                tickfont=dict(color=DARK_THEME['text'], size=10)
            )
        ),
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def create_trinity_balance_chart(father: float, son: float, spirit: float) -> go.Figure:
    """Create interactive donut chart for Trinity balance."""
    
    labels = ['Father (Source)', 'Son (Form)', 'Spirit (Coherence)']
    values = [father, son, spirit]
    colors = [DARK_THEME['accent_cyan'], DARK_THEME['accent_green'], DARK_THEME['accent_purple']]
    
    # Calculate balance score
    ideal = 33.33
    balance = 1 - (abs(father - ideal) + abs(son - ideal) + abs(spirit - ideal)) / 100
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker_colors=colors,
        textinfo='label+percent',
        textfont=dict(color=DARK_THEME['text']),
        hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>'
    ))
    
    fig.add_annotation(
        text=f"Balance<br><b>{balance:.3f}</b>",
        x=0.5, y=0.5,
        font=dict(size=20, color=DARK_THEME['accent_cyan']),
        showarrow=False
    )
    
    fig.update_layout(
        title='Trinity Balance Distribution',
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def create_grace_entropy_gauge(grace_ratio: float) -> go.Figure:
    """Create interactive gauge for grace/entropy ratio."""
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=grace_ratio,
        number={'suffix': '', 'font': {'color': DARK_THEME['accent_cyan'], 'size': 40}},
        gauge={
            'axis': {'range': [0, 1], 'tickcolor': DARK_THEME['text_dim']},
            'bar': {'color': DARK_THEME['accent_cyan']},
            'bgcolor': DARK_THEME['surface'],
            'bordercolor': DARK_THEME['grid'],
            'steps': [
                {'range': [0, 0.3], 'color': DARK_THEME['accent_red']},
                {'range': [0.3, 0.5], 'color': DARK_THEME['accent_orange']},
                {'range': [0.5, 0.7], 'color': DARK_THEME['accent_yellow']},
                {'range': [0.7, 1], 'color': DARK_THEME['accent_green']}
            ],
            'threshold': {
                'line': {'color': DARK_THEME['text'], 'width': 4},
                'thickness': 0.75,
                'value': grace_ratio
            }
        },
        title={'text': 'Grace/Entropy Ratio', 'font': {'color': DARK_THEME['accent_cyan']}}
    ))
    
    fig.update_layout(
        height=300,
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def create_concept_network_chart(concepts: Dict[str, int], max_concepts: int = 20) -> go.Figure:
    """Create interactive bar chart for top concepts."""
    
    sorted_concepts = sorted(concepts.items(), key=lambda x: x[1], reverse=True)[:max_concepts]
    names = [c[0] for c in sorted_concepts]
    counts = [c[1] for c in sorted_concepts]
    
    # Gradient colors
    colors = [f'rgb({int(0 + i*10)}, {int(217 - i*5)}, {int(255 - i*3)})' for i in range(len(names))]
    
    fig = go.Figure(go.Bar(
        x=counts,
        y=names,
        orientation='h',
        marker_color=colors,
        text=counts,
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Top Concepts by Frequency',
        xaxis_title='Occurrences',
        height=max(400, len(names) * 30),
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    fig.update_yaxes(autorange="reversed")
    
    return fig


def create_cross_paper_heatmap(
    papers: List[str],
    connection_matrix: List[List[float]],
    title: str = "Cross-Paper Connection Strength"
) -> go.Figure:
    """Create interactive heatmap showing connections between papers."""
    
    fig = go.Figure(go.Heatmap(
        z=connection_matrix,
        x=papers,
        y=papers,
        colorscale=[
            [0, DARK_THEME['bg']],
            [0.5, DARK_THEME['accent_blue']],
            [1, DARK_THEME['accent_cyan']]
        ],
        hovertemplate='<b>%{x}</b> ↔ <b>%{y}</b><br>Connection: %{z:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='',
        yaxis_title='',
        height=600,
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def create_theory_comparison_chart(
    theories: List[Dict],
    metrics: List[str] = None
) -> go.Figure:
    """
    Create grouped bar chart comparing multiple theories across metrics.
    
    Args:
        theories: List of dicts with 'name' and metric values
        metrics: List of metric names to compare
    """
    if not metrics:
        metrics = ['coherence', 'law_coverage', 'trinity_balance', 'grace_entropy']
    
    fig = go.Figure()
    
    colors = [DARK_THEME['accent_cyan'], DARK_THEME['accent_green'], 
              DARK_THEME['accent_purple'], DARK_THEME['accent_orange'],
              DARK_THEME['accent_blue'], DARK_THEME['accent_yellow']]
    
    for i, theory in enumerate(theories):
        values = [theory.get(m, 0) for m in metrics]
        fig.add_trace(go.Bar(
            name=theory['name'],
            x=metrics,
            y=values,
            marker_color=colors[i % len(colors)],
            hovertemplate=f"<b>{theory['name']}</b><br>%{{x}}: %{{y:.3f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title='Theory Comparison Across Metrics',
        barmode='group',
        xaxis_title='Metric',
        yaxis_title='Score',
        yaxis_range=[0, 1.1],
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def create_timeline_chart(
    events: List[Dict],
    title: str = "Research Timeline"
) -> go.Figure:
    """
    Create timeline visualization for breakthroughs and milestones.
    
    Args:
        events: List of dicts with 'date', 'title', 'description', 'type'
    """
    
    dates = [e['date'] for e in events]
    titles = [e['title'] for e in events]
    descriptions = [e.get('description', '') for e in events]
    types = [e.get('type', 'event') for e in events]
    
    # Color by type
    type_colors = {
        'breakthrough': DARK_THEME['accent_green'],
        'milestone': DARK_THEME['accent_cyan'],
        'publication': DARK_THEME['accent_purple'],
        'event': DARK_THEME['accent_blue']
    }
    colors = [type_colors.get(t, DARK_THEME['accent_blue']) for t in types]
    
    fig = go.Figure(go.Scatter(
        x=dates,
        y=[1] * len(dates),
        mode='markers+text',
        marker=dict(size=20, color=colors, symbol='diamond'),
        text=titles,
        textposition='top center',
        hovertemplate='<b>%{text}</b><br>%{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_visible=False,
        height=300,
        **PLOTLY_DARK_TEMPLATE['layout']
    )
    
    return fig


def generate_full_html_dashboard(
    paper_data: List[Dict],
    law_scores: Dict[str, float],
    trinity: Tuple[float, float, float],
    grace_ratio: float,
    concepts: Dict[str, int],
    global_metrics: Dict,
    cross_paper_matrix: Optional[List[List[float]]] = None,
    external_theories: Optional[List[Dict]] = None,
    output_path: Path = None,
    title: str = "Theophysics Analytics Dashboard"
) -> Path:
    """
    Generate a complete interactive HTML dashboard with all analytics.
    
    Returns:
        Path to the generated HTML file
    """
    
    output_path = Path(output_path) if output_path else Path(".")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate all figures
    figures = {}
    
    if paper_data:
        figures['coherence'] = create_coherence_comparison_chart(paper_data)
    
    if law_scores:
        figures['laws'] = create_ten_laws_radar(law_scores)
    
    if trinity:
        figures['trinity'] = create_trinity_balance_chart(trinity[0], trinity[1], trinity[2])
    
    if grace_ratio is not None:
        figures['grace'] = create_grace_entropy_gauge(grace_ratio)
    
    if concepts:
        figures['concepts'] = create_concept_network_chart(concepts)
    
    if cross_paper_matrix and paper_data:
        paper_names = [p['name'] for p in paper_data]
        figures['heatmap'] = create_cross_paper_heatmap(paper_names, cross_paper_matrix)
    
    if external_theories:
        all_theories = [{'name': 'Theophysics Framework', **global_metrics}] + external_theories
        figures['comparison'] = create_theory_comparison_chart(all_theories)
    
    # Build HTML
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
            background-color: {DARK_THEME['bg']};
            color: {DARK_THEME['text']};
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, {DARK_THEME['surface']} 0%, {DARK_THEME['panel']} 100%);
            padding: 30px 40px;
            border-bottom: 2px solid {DARK_THEME['accent_cyan']};
        }}
        
        .header h1 {{
            color: {DARK_THEME['accent_cyan']};
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: {DARK_THEME['text_dim']};
            font-size: 14px;
        }}
        
        .metrics-bar {{
            display: flex;
            gap: 20px;
            padding: 20px 40px;
            background: {DARK_THEME['surface']};
            border-bottom: 1px solid {DARK_THEME['grid']};
            flex-wrap: wrap;
        }}
        
        .metric-card {{
            background: {DARK_THEME['panel']};
            border: 1px solid {DARK_THEME['grid']};
            border-radius: 8px;
            padding: 15px 25px;
            min-width: 150px;
        }}
        
        .metric-card .label {{
            color: {DARK_THEME['text_dim']};
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .metric-card .value {{
            color: {DARK_THEME['accent_cyan']};
            font-size: 28px;
            font-weight: bold;
        }}
        
        .metric-card .grade {{
            color: {DARK_THEME['accent_green']};
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 30px 40px;
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .chart-card {{
            background: {DARK_THEME['surface']};
            border: 1px solid {DARK_THEME['grid']};
            border-radius: 12px;
            padding: 20px;
            overflow: hidden;
        }}
        
        .chart-card.full-width {{
            grid-column: 1 / -1;
        }}
        
        .chart-card h3 {{
            color: {DARK_THEME['accent_cyan']};
            margin-bottom: 15px;
            font-size: 16px;
            border-bottom: 1px solid {DARK_THEME['grid']};
            padding-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: {DARK_THEME['text_dim']};
            font-size: 12px;
            border-top: 1px solid {DARK_THEME['grid']};
            margin-top: 40px;
        }}
        
        .tabs {{
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 2px solid {DARK_THEME['grid']};
            padding-bottom: 10px;
        }}
        
        .tab {{
            padding: 10px 20px;
            background: {DARK_THEME['surface']};
            border: 1px solid {DARK_THEME['grid']};
            border-radius: 6px 6px 0 0;
            cursor: pointer;
            color: {DARK_THEME['text_dim']};
            transition: all 0.2s;
        }}
        
        .tab:hover {{
            background: {DARK_THEME['panel']};
            color: {DARK_THEME['text']};
        }}
        
        .tab.active {{
            background: {DARK_THEME['accent_cyan']};
            color: {DARK_THEME['bg']};
            font-weight: bold;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            .metrics-bar {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 {html.escape(title)}</h1>
        <div class="subtitle">
            Lowe Coherence Lagrangian Analysis | Generated: {timestamp}
        </div>
    </div>
    
    <div class="metrics-bar">
        <div class="metric-card">
            <div class="label">Overall Coherence</div>
            <div class="value">{global_metrics.get('overall_coherence', 0):.3f}</div>
        </div>
        <div class="metric-card">
            <div class="label">Grade</div>
            <div class="value grade">{global_metrics.get('grade', '-')}</div>
        </div>
        <div class="metric-card">
            <div class="label">Law Coverage</div>
            <div class="value">{global_metrics.get('law_coverage', 0):.1%}</div>
        </div>
        <div class="metric-card">
            <div class="label">Trinity Balance</div>
            <div class="value">{global_metrics.get('trinity_balance', 0):.3f}</div>
        </div>
        <div class="metric-card">
            <div class="label">Grace/Entropy</div>
            <div class="value">{global_metrics.get('grace_entropy', 0):.3f}</div>
        </div>
        <div class="metric-card">
            <div class="label">Papers Analyzed</div>
            <div class="value">{global_metrics.get('papers_analyzed', 0)}</div>
        </div>
    </div>
    
    <div class="container">
        <div class="tabs">
            <div class="tab active" onclick="showTab('overview')">📊 Overview</div>
            <div class="tab" onclick="showTab('papers')">📄 Papers</div>
            <div class="tab" onclick="showTab('laws')">⚖️ Ten Laws</div>
            <div class="tab" onclick="showTab('concepts')">💡 Concepts</div>
            {"<div class='tab' onclick=\"showTab('comparison')\">🔬 Theory Comparison</div>" if external_theories else ""}
        </div>
        
        <!-- Overview Tab -->
        <div id="overview" class="tab-content active">
            <div class="grid">
                <div class="chart-card">
                    <h3>🎯 Grace/Entropy Balance</h3>
                    <div id="grace-chart"></div>
                </div>
                <div class="chart-card">
                    <h3>✝️ Trinity Distribution</h3>
                    <div id="trinity-chart"></div>
                </div>
            </div>
        </div>
        
        <!-- Papers Tab -->
        <div id="papers" class="tab-content">
            <div class="grid">
                <div class="chart-card full-width">
                    <h3>📈 Paper Coherence Comparison</h3>
                    <div id="coherence-chart"></div>
                </div>
                {"<div class='chart-card full-width'><h3>🔗 Cross-Paper Connections</h3><div id='heatmap-chart'></div></div>" if cross_paper_matrix else ""}
            </div>
        </div>
        
        <!-- Laws Tab -->
        <div id="laws" class="tab-content">
            <div class="grid">
                <div class="chart-card full-width">
                    <h3>⚖️ Ten Laws Coverage (Physical ↔ Spiritual)</h3>
                    <div id="laws-chart"></div>
                </div>
            </div>
        </div>
        
        <!-- Concepts Tab -->
        <div id="concepts" class="tab-content">
            <div class="grid">
                <div class="chart-card full-width">
                    <h3>💡 Top Concepts by Frequency</h3>
                    <div id="concepts-chart"></div>
                </div>
            </div>
        </div>
        
        {"<!-- Comparison Tab --><div id='comparison' class='tab-content'><div class='grid'><div class='chart-card full-width'><h3>🔬 Theory Comparison</h3><div id='comparison-chart'></div></div></div></div>" if external_theories else ""}
    </div>
    
    <div class="footer">
        <p>Theophysics Analytics Dashboard | Lowe Coherence Lagrangian Framework</p>
        <p>Generated by Python Backend | {timestamp}</p>
    </div>
    
    <script>
        // Tab switching
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
            
            // Trigger resize for Plotly charts
            window.dispatchEvent(new Event('resize'));
        }}
        
        // Render charts
        const config = {{responsive: true, displayModeBar: true, displaylogo: false}};
'''
    
    # Add chart data
    if 'grace' in figures:
        html_content += f'''
        Plotly.newPlot('grace-chart', {figures['grace'].to_json()}.data, {figures['grace'].to_json()}.layout, config);
'''
    
    if 'trinity' in figures:
        html_content += f'''
        Plotly.newPlot('trinity-chart', {figures['trinity'].to_json()}.data, {figures['trinity'].to_json()}.layout, config);
'''
    
    if 'coherence' in figures:
        html_content += f'''
        Plotly.newPlot('coherence-chart', {figures['coherence'].to_json()}.data, {figures['coherence'].to_json()}.layout, config);
'''
    
    if 'laws' in figures:
        html_content += f'''
        Plotly.newPlot('laws-chart', {figures['laws'].to_json()}.data, {figures['laws'].to_json()}.layout, config);
'''
    
    if 'concepts' in figures:
        html_content += f'''
        Plotly.newPlot('concepts-chart', {figures['concepts'].to_json()}.data, {figures['concepts'].to_json()}.layout, config);
'''
    
    if 'heatmap' in figures:
        html_content += f'''
        Plotly.newPlot('heatmap-chart', {figures['heatmap'].to_json()}.data, {figures['heatmap'].to_json()}.layout, config);
'''
    
    if 'comparison' in figures:
        html_content += f'''
        Plotly.newPlot('comparison-chart', {figures['comparison'].to_json()}.data, {figures['comparison'].to_json()}.layout, config);
'''
    
    html_content += '''
    </script>
</body>
</html>
'''
    
    output_file = output_path / "analytics_dashboard.html"
    output_file.write_text(html_content, encoding='utf-8')
    
    return output_file


if __name__ == "__main__":
    # Test HTML generation
    test_output = Path("./test_html")
    
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
    
    test_concepts = {"quantum": 86, "consciousness": 55, "information": 102, "observer": 45}
    
    test_metrics = {
        'overall_coherence': 0.841,
        'grade': 'A-',
        'law_coverage': 0.99,
        'trinity_balance': 0.883,
        'grace_entropy': 0.5,
        'papers_analyzed': 4
    }
    
    # Test with external theories
    external = [
        {'name': 'String Theory', 'coherence': 0.65, 'law_coverage': 0.4, 'trinity_balance': 0.3, 'grace_entropy': 0.2},
        {'name': 'IIT (Tononi)', 'coherence': 0.72, 'law_coverage': 0.5, 'trinity_balance': 0.4, 'grace_entropy': 0.3},
    ]
    
    output = generate_full_html_dashboard(
        paper_data=test_papers,
        law_scores=test_laws,
        trinity=(38.1, 28.6, 33.3),
        grace_ratio=0.5,
        concepts=test_concepts,
        global_metrics=test_metrics,
        external_theories=external,
        output_path=test_output
    )
    
    print(f"Generated: {output}")
