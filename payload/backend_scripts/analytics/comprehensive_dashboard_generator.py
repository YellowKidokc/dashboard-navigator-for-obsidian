"""
Comprehensive Theophysics Dashboard Generator
==============================================
Creates interactive HTML dashboard with:
- 40+ baseline metrics per paper
- Trend charts (up/down/left/right)
- Individual paper analysis
- Subset comparisons
- Full corpus aggregation
- Wisdom vs Knowledge scoring
- Fruits of the Spirit metrics
- Master Equation variables

This is the UNIFIED dashboard for the complete Theophysics package.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analytics.paper_metrics_engine import PaperMetricsEngine
from analytics.paper_comparison_engine import PaperComparisonEngine

import plotly.graph_objects as go
from plotly.subplots import make_subplots


class ComprehensiveDashboardGenerator:
    """Generate comprehensive Theophysics dashboard."""
    
    DARK_THEME = {
        'bg': '#0d0d0d',
        'surface': '#1a1a1a',
        'panel': '#242424',
        'text': '#ffffff',
        'text_dim': '#b0b0b0',
        'grid': '#2a2a2a',
        'accent_cyan': '#00d9ff',
        'accent_green': '#4ec9b0',
        'accent_orange': '#ce9178',
        'accent_purple': '#c586c0',
        'accent_yellow': '#dcdcaa',
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.metrics_engine = PaperMetricsEngine()
        self.comparison_engine = PaperComparisonEngine()
        self.output_dir = output_dir or Path(__file__).parent.parent.parent / "Global_Analytics"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_trend_chart(self, paper_names: List[str], values: List[float], 
                          title: str, ylabel: str) -> go.Figure:
        """Create trend line chart."""
        fig = go.Figure()
        
        # Detect trend
        if len(values) >= 2:
            if values[-1] > values[0] * 1.1:
                color = self.DARK_THEME['accent_green']
                trend = '↗ Trending Up'
            elif values[-1] < values[0] * 0.9:
                color = self.DARK_THEME['accent_orange']
                trend = '↘ Trending Down'
            else:
                color = self.DARK_THEME['accent_cyan']
                trend = '→ Stable'
        else:
            color = self.DARK_THEME['accent_cyan']
            trend = '→'
        
        fig.add_trace(go.Scatter(
            x=paper_names,
            y=values,
            mode='lines+markers',
            name=ylabel,
            line=dict(color=color, width=3),
            marker=dict(size=10, color=color),
            hovertemplate='<b>%{x}</b><br>%{y:.2f}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'{title} {trend}',
            xaxis_title='Papers',
            yaxis_title=ylabel,
            paper_bgcolor=self.DARK_THEME['bg'],
            plot_bgcolor=self.DARK_THEME['surface'],
            font=dict(color=self.DARK_THEME['text'], family='Segoe UI'),
            xaxis=dict(gridcolor=self.DARK_THEME['grid'], tickangle=-45),
            yaxis=dict(gridcolor=self.DARK_THEME['grid']),
            height=400,
        )
        
        return fig
    
    def create_metric_bars(self, paper_names: List[str], metric_dict: Dict[str, List[float]], 
                          title: str) -> go.Figure:
        """Create grouped bar chart for multiple metrics."""
        fig = go.Figure()
        
        colors = [
            self.DARK_THEME['accent_cyan'],
            self.DARK_THEME['accent_green'],
            self.DARK_THEME['accent_purple'],
            self.DARK_THEME['accent_orange'],
            self.DARK_THEME['accent_yellow'],
        ]
        
        for i, (metric_name, values) in enumerate(metric_dict.items()):
            fig.add_trace(go.Bar(
                name=metric_name,
                x=paper_names,
                y=values,
                marker_color=colors[i % len(colors)],
                hovertemplate=f'<b>{metric_name}</b><br>%{{x}}: %{{y:.2f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            barmode='group',
            paper_bgcolor=self.DARK_THEME['bg'],
            plot_bgcolor=self.DARK_THEME['surface'],
            font=dict(color=self.DARK_THEME['text']),
            xaxis=dict(gridcolor=self.DARK_THEME['grid'], tickangle=-45),
            yaxis=dict(gridcolor=self.DARK_THEME['grid']),
            height=500,
        )
        
        return fig
    
    def create_fruits_radar(self, fruits_dict: Dict[str, float], paper_name: str) -> go.Figure:
        """Create radar chart for Fruits of the Spirit."""
        fruits = list(fruits_dict.keys())
        values = list(fruits_dict.values())
        
        # Close the radar
        fruits_closed = fruits + [fruits[0]]
        values_closed = values + [values[0]]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=fruits_closed,
            fill='toself',
            fillcolor=f'rgba(0, 217, 255, 0.2)',
            line_color=self.DARK_THEME['accent_cyan'],
            name='Fruits',
        ))
        
        fig.update_layout(
            title=f'Fruits of the Spirit - {paper_name}',
            polar=dict(
                bgcolor=self.DARK_THEME['surface'],
                radialaxis=dict(
                    visible=True,
                    range=[0, 10],
                    gridcolor=self.DARK_THEME['grid'],
                ),
                angularaxis=dict(gridcolor=self.DARK_THEME['grid']),
            ),
            paper_bgcolor=self.DARK_THEME['bg'],
            font=dict(color=self.DARK_THEME['text']),
            height=500,
        )
        
        return fig
    
    def create_wisdom_knowledge_scatter(self, papers_data: List[Dict]) -> go.Figure:
        """Create scatter plot of Wisdom vs Knowledge."""
        fig = go.Figure()
        
        paper_names = [p['name'] for p in papers_data]
        wisdom = [p['wisdom'] for p in papers_data]
        knowledge = [p['knowledge'] for p in papers_data]
        ratios = [p['ratio'] for p in papers_data]
        
        # Color by ratio
        colors = []
        for ratio in ratios:
            if ratio > 1.5:
                colors.append(self.DARK_THEME['accent_green'])  # Wisdom dominant
            elif ratio > 1.0:
                colors.append(self.DARK_THEME['accent_cyan'])  # Balanced
            else:
                colors.append(self.DARK_THEME['accent_orange'])  # Knowledge dominant
        
        fig.add_trace(go.Scatter(
            x=knowledge,
            y=wisdom,
            mode='markers+text',
            marker=dict(size=15, color=colors),
            text=[p[:10] for p in paper_names],
            textposition='top center',
            hovertemplate='<b>%{text}</b><br>Wisdom: %{y:.2f}<br>Knowledge: %{x:.2f}<extra></extra>'
        ))
        
        # Add diagonal line (W=K)
        max_val = max(max(wisdom), max(knowledge))
        fig.add_trace(go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(dash='dash', color=self.DARK_THEME['text_dim']),
            name='W=K Line',
            showlegend=False,
        ))
        
        fig.update_layout(
            title='Wisdom vs Knowledge Scores',
            xaxis_title='Knowledge Score',
            yaxis_title='Wisdom Score',
            paper_bgcolor=self.DARK_THEME['bg'],
            plot_bgcolor=self.DARK_THEME['surface'],
            font=dict(color=self.DARK_THEME['text']),
            xaxis=dict(gridcolor=self.DARK_THEME['grid']),
            yaxis=dict(gridcolor=self.DARK_THEME['grid']),
            height=600,
        )
        
        return fig
    
    def generate_html_dashboard(self, paper_paths: List[Path]) -> Path:
        """Generate complete HTML dashboard."""
        print("\n" + "=" * 80)
        print("GENERATING COMPREHENSIVE THEOPHYSICS DASHBOARD")
        print("=" * 80 + "\n")
        
        # Analyze all papers
        print("Analyzing papers...")
        metrics_list = self.comparison_engine.analyze_paper_set(paper_paths)
        
        # Aggregate
        print("Calculating aggregates...")
        aggregate = self.comparison_engine.aggregate_corpus(metrics_list)
        
        # Generate trends
        print("Analyzing trends...")
        trends = self.comparison_engine.generate_trend_report(metrics_list)
        
        # Create visualizations
        print("Creating visualizations...")
        
        paper_names = [m.paper_id for m in metrics_list]
        
        # 1. CHI Score Trend
        chi_chart = self.create_trend_chart(
            paper_names,
            [m.chi_score for m in metrics_list],
            'Coherence (CHI) Score',
            'CHI Score (0-10)'
        )
        
        # 2. Wisdom/Knowledge Ratio Trend
        wk_chart = self.create_trend_chart(
            paper_names,
            [m.wisdom_knowledge_ratio for m in metrics_list],
            'Wisdom/Knowledge Ratio',
            'W/K Ratio'
        )
        
        # 3. Fruits composite trend
        fruits_chart = self.create_trend_chart(
            paper_names,
            [m.get_composite_scores()['fruits_composite'] for m in metrics_list],
            'Fruits of the Spirit Score',
            'Fruits Score (0-10)'
        )
        
        # 4. Master Equation trend
        master_eq_chart = self.create_trend_chart(
            paper_names,
            [m.get_composite_scores()['master_equation_composite'] for m in metrics_list],
            'Master Equation Variables',
            'Master Eq Score (0-10)'
        )
        
        # 5. Multi-metric comparison
        multi_metric_chart = self.create_metric_bars(
            paper_names,
            {
                'CHI Score': [m.chi_score for m in metrics_list],
                'Wisdom Score': [m.wisdom_score for m in metrics_list],
                'Fruits Score': [m.get_composite_scores()['fruits_composite'] for m in metrics_list],
            },
            'Key Metrics Comparison'
        )
        
        # 6. Wisdom vs Knowledge scatter
        wk_scatter = self.create_wisdom_knowledge_scatter([
            {
                'name': m.paper_id,
                'wisdom': m.wisdom_score,
                'knowledge': m.knowledge_score,
                'ratio': m.wisdom_knowledge_ratio,
            }
            for m in metrics_list
        ])
        
        # 7. Fruits radar for best paper
        best_fruits = max(metrics_list, key=lambda m: m.get_composite_scores()['fruits_composite'])
        fruits_radar = self.create_fruits_radar(
            {
                'Love': best_fruits.fruit_love,
                'Joy': best_fruits.fruit_joy,
                'Peace': best_fruits.fruit_peace,
                'Patience': best_fruits.fruit_patience,
                'Kindness': best_fruits.fruit_kindness,
                'Goodness': best_fruits.fruit_goodness,
                'Faithfulness': best_fruits.fruit_faithfulness,
                'Gentleness': best_fruits.fruit_gentleness,
                'Self-Control': best_fruits.fruit_self_control,
                'Grace': best_fruits.fruit_grace,
                'Hope': best_fruits.fruit_hope,
                'Humility': best_fruits.fruit_humility,
            },
            best_fruits.paper_id
        )
        
        # Build HTML
        print("Building HTML...")
        html_content = self._build_html(
            aggregate, metrics_list, trends,
            [chi_chart, wk_chart, fruits_chart, master_eq_chart, 
             multi_metric_chart, wk_scatter, fruits_radar]
        )
        
        # Save
        output_file = self.output_dir / "theophysics_comprehensive_dashboard.html"
        output_file.write_text(html_content, encoding='utf-8')
        
        print(f"\n✅ Dashboard generated: {output_file}")
        return output_file
    
    def _build_html(self, aggregate, metrics_list, trends, charts) -> str:
        """Build complete HTML document."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert charts to JSON
        chart_jsons = [fig.to_json() for fig in charts]
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Theophysics Comprehensive Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', sans-serif;
            background: {self.DARK_THEME['bg']};
            color: {self.DARK_THEME['text']};
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
            padding: 40px;
            border-bottom: 3px solid {self.DARK_THEME['accent_cyan']};
        }}
        .header h1 {{
            color: {self.DARK_THEME['accent_cyan']};
            font-size: 36px;
            margin-bottom: 10px;
        }}
        .subtitle {{ color: {self.DARK_THEME['text_dim']}; }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            max-width: 1800px;
            margin: 0 auto;
        }}
        .metric-card {{
            background: {self.DARK_THEME['surface']};
            border: 1px solid {self.DARK_THEME['grid']};
            border-radius: 12px;
            padding: 20px;
        }}
        .metric-label {{
            color: {self.DARK_THEME['text_dim']};
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .metric-value {{
            color: {self.DARK_THEME['accent_cyan']};
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .metric-trend {{
            font-size: 14px;
            color: {self.DARK_THEME['accent_green']};
        }}
        
        .charts-container {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 30px;
        }}
        .chart-card {{
            background: {self.DARK_THEME['surface']};
            border: 1px solid {self.DARK_THEME['grid']};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
        }}
        
        .insights {{
            max-width: 1800px;
            margin: 0 auto;
            padding: 30px;
        }}
        .insight-card {{
            background: {self.DARK_THEME['surface']};
            border-left: 4px solid {self.DARK_THEME['accent_cyan']};
            padding: 20px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚛️ Theophysics Comprehensive Dashboard</h1>
        <div class="subtitle">
            Complete Analytics Package | 50+ Baseline Metrics | Generated: {timestamp}
        </div>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Papers Analyzed</div>
            <div class="metric-value">{aggregate.paper_count}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Words</div>
            <div class="metric-value">{aggregate.total_words:,}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Axioms</div>
            <div class="metric-value">{aggregate.total_axioms}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg CHI Score</div>
            <div class="metric-value">{aggregate.avg_chi_score:.2f}</div>
            <div class="metric-trend">{aggregate.trend_chi}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Wisdom Score</div>
            <div class="metric-value">{aggregate.avg_wisdom_score:.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">W/K Ratio</div>
            <div class="metric-value">{aggregate.avg_wisdom_knowledge_ratio:.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Avg Fruits Score</div>
            <div class="metric-value">{aggregate.avg_fruits_score:.2f}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Master Eq Score</div>
            <div class="metric-value">{aggregate.avg_master_equation_score:.2f}</div>
        </div>
    </div>
    
    <div class="charts-container">
        <div class="chart-card"><div id="chart0"></div></div>
        <div class="chart-card"><div id="chart1"></div></div>
        <div class="chart-card"><div id="chart2"></div></div>
        <div class="chart-card"><div id="chart3"></div></div>
        <div class="chart-card"><div id="chart4"></div></div>
        <div class="chart-card"><div id="chart5"></div></div>
        <div class="chart-card"><div id="chart6"></div></div>
    </div>
    
    <script>
        const config = {{responsive: true, displayModeBar: true, displaylogo: false}};
'''
        
        for i, chart_json in enumerate(chart_jsons):
            html += f'''
        Plotly.newPlot('chart{i}', {chart_json}.data, {chart_json}.layout, config);
'''
        
        html += '''
    </script>
</body>
</html>
'''
        
        return html


def main():
    """Main entry point."""
    generator = ComprehensiveDashboardGenerator()
    
    # Find papers to analyze
    base_path = Path(os.environ.get('THEOPHYSICS_VAULT', r'O:\_Theophysics_v3'))
    paper_folders = [
        'V3_P01-Logos-Principle', 'V3_P02-Quantum-Bridge', 'V3_P03-Algorithm-Reality',
        'V3_P04-Hard-Problem', 'V3_P05-Soul-Observer', 'V3_P06-Physics-Principalities',
        'V3_P07-Grace-Function',
    ]
    
    papers_to_analyze = []
    for folder in paper_folders:
        folder_path = base_path / folder
        if folder_path.exists():
            canonicals = list(folder_path.glob("*canonical*.md"))
            if canonicals:
                papers_to_analyze.append(canonicals[0])
    
    if papers_to_analyze:
        generator.generate_html_dashboard(papers_to_analyze)
    else:
        print("No papers found")


if __name__ == "__main__":
    main()
