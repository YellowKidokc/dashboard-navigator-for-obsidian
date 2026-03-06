"""
HTML Report Generator for Document Evaluator
Beautiful interactive reports with Fruits/Chi visualizations
"""

from datetime import datetime
from typing import Dict


def generate_html_report(results: Dict) -> str:
    """Generate an interactive HTML report with visualizations."""
    
    agg = results["aggregate"]
    docs = results["documents"]
    
    # Calculate fruit averages for radar chart
    fruits_avg = agg.get("fruits_totals", {})
    anti_fruits_avg = agg.get("anti_fruits_totals", {})
    
    # Sort documents by chi score
    docs_sorted = sorted(docs, key=lambda x: x.get("chi", 0), reverse=True)
    top_5 = docs_sorted[:5]
    bottom_5 = docs_sorted[-5:]
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Evaluation Report - {datetime.now().strftime("%Y-%m-%d")}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #2d3748;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f7fafc;
        }}
        
        .metric-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }}
        
        .metric-value {{
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .metric-label {{
            font-size: 0.9em;
            color: #718096;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            padding: 40px;
        }}
        
        .chart-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-card h2 {{
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 1.5em;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
        }}
        
        .tables {{
            padding: 40px;
        }}
        
        .table-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .table-card h2 {{
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 1.5em;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        tr:hover {{
            background: #f7fafc;
        }}
        
        .grade {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .grade-a {{ background: #48bb78; color: white; }}
        .grade-b {{ background: #4299e1; color: white; }}
        .grade-c {{ background: #ed8936; color: white; }}
        .grade-d {{ background: #f56565; color: white; }}
        .grade-f {{ background: #e53e3e; color: white; }}
        
        .footer {{
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .footer p {{
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍇 Document Evaluation Report</h1>
            <p>Universal Coherence Assessment Framework</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{agg['total_docs']}</div>
                <div class="metric-label">Documents Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{agg['avg_chi']:.3f}</div>
                <div class="metric-label">Average χ Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{_calculate_avg_grade(docs)}</div>
                <div class="metric-label">Average Grade</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{len([d for d in docs if d.get('chi', 0) >= 0.80])}</div>
                <div class="metric-label">High Performers (B+)</div>
            </div>
        </div>
        
        <div class="charts">
            <div class="chart-card">
                <h2>🍇 Fruits Profile (Positive Markers)</h2>
                <div class="chart-container">
                    <canvas id="fruitsChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h2>⚠️ Anti-Fruits Profile (Decoherence Signatures)</h2>
                <div class="chart-container">
                    <canvas id="antiFruitsChart"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h2>📊 χ Score Distribution</h2>
                <div class="chart-container">
                    <canvas id="chiDistribution"></canvas>
                </div>
            </div>
            
            <div class="chart-card">
                <h2>🎯 Grade Distribution</h2>
                <div class="chart-container">
                    <canvas id="gradeDistribution"></canvas>
                </div>
            </div>
        </div>
        
        <div class="tables">
            <div class="table-card">
                <h2>🏆 Top 5 Performers</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Document</th>
                            <th>χ Score</th>
                            <th>Grade</th>
                            <th>Top Fruit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_generate_table_rows(top_5, start_rank=1)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-card">
                <h2>📉 Bottom 5 Performers</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Document</th>
                            <th>χ Score</th>
                            <th>Grade</th>
                            <th>Top Anti-Fruit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_generate_table_rows(bottom_5, start_rank=len(docs)-4, show_anti=True)}
                    </tbody>
                </table>
            </div>
            
            <div class="table-card">
                <h2>📋 All Documents</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Document</th>
                            <th>Word Count</th>
                            <th>χ Score</th>
                            <th>Grade</th>
                            <th>Top Fruit</th>
                        </tr>
                    </thead>
                    <tbody>
                        {_generate_all_docs_rows(docs_sorted)}
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Evaluation Framework:</strong> Universal Document Evaluator v1.0 (Theophysics)</p>
            <p style="margin-top: 10px;">Three-dimensional coherence assessment: Fruits + Anti-Fruits + χ</p>
        </div>
    </div>
    
    <script>
        // Fruits Radar Chart
        const fruitsCtx = document.getElementById('fruitsChart').getContext('2d');
        new Chart(fruitsCtx, {{
            type: 'radar',
            data: {{
                labels: {list(fruits_avg.keys())},
                datasets: [{{
                    label: 'Average Score',
                    data: {list(fruits_avg.values())},
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20
                        }}
                    }}
                }}
            }}
        }});
        
        // Anti-Fruits Radar Chart
        const antiFruitsCtx = document.getElementById('antiFruitsChart').getContext('2d');
        new Chart(antiFruitsCtx, {{
            type: 'radar',
            data: {{
                labels: {list(anti_fruits_avg.keys())},
                datasets: [{{
                    label: 'Average Score',
                    data: {list(anti_fruits_avg.values())},
                    backgroundColor: 'rgba(245, 101, 101, 0.2)',
                    borderColor: 'rgba(245, 101, 101, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(245, 101, 101, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(245, 101, 101, 1)'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20
                        }}
                    }}
                }}
            }}
        }});
        
        // Chi Distribution Histogram
        const chiCtx = document.getElementById('chiDistribution').getContext('2d');
        const chiScores = {[doc.get('chi', 0) for doc in docs]};
        const chiBins = _create_histogram_bins(chiScores, 10);
        
        new Chart(chiCtx, {{
            type: 'bar',
            data: {{
                labels: chiBins.labels,
                datasets: [{{
                    label: 'Number of Documents',
                    data: chiBins.counts,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        
        // Grade Distribution Pie Chart
        const gradeCtx = document.getElementById('gradeDistribution').getContext('2d');
        const gradeCounts = _count_grades({[doc.get('grade', 'F') for doc in docs]});
        
        new Chart(gradeCtx, {{
            type: 'doughnut',
            data: {{
                labels: Object.keys(gradeCounts),
                datasets: [{{
                    data: Object.values(gradeCounts),
                    backgroundColor: [
                        'rgba(72, 187, 120, 0.8)',
                        'rgba(66, 153, 225, 0.8)',
                        'rgba(237, 137, 54, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(229, 62, 62, 0.8)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // Helper function for histogram bins
        function _create_histogram_bins(scores, numBins) {{
            const bins = Array(numBins).fill(0);
            const labels = [];
            const binSize = 1.0 / numBins;
            
            for (let i = 0; i < numBins; i++) {{
                labels.push((i * binSize).toFixed(2) + '-' + ((i + 1) * binSize).toFixed(2));
            }}
            
            scores.forEach(score => {{
                const binIndex = Math.min(Math.floor(score / binSize), numBins - 1);
                bins[binIndex]++;
            }});
            
            return {{ labels, counts: bins }};
        }}
        
        // Helper function for grade counts
        function _count_grades(grades) {{
            const counts = {{}};
            grades.forEach(grade => {{
                const letter = grade.charAt(0);
                counts[letter] = (counts[letter] || 0) + 1;
            }});
            return counts;
        }}
    </script>
</body>
</html>"""
    
    return html


def _calculate_avg_grade(docs):
    """Calculate average letter grade."""
    if not docs:
        return "-"
    
    grade_values = {
        'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0
    }
    
    total = 0
    count = 0
    for doc in docs:
        grade = doc.get('grade', 'F')
        letter = grade[0] if grade else 'F'
        total += grade_values.get(letter, 0)
        count += 1
    
    avg = total / count if count > 0 else 0
    
    if avg >= 3.5: return "A"
    elif avg >= 2.5: return "B"
    elif avg >= 1.5: return "C"
    elif avg >= 0.5: return "D"
    else: return "F"


def _generate_table_rows(docs, start_rank=1, show_anti=False):
    """Generate HTML table rows for documents."""
    rows = []
    for i, doc in enumerate(docs):
        rank = start_rank + i
        filename = doc.get('filename', 'Unknown')
        chi = doc.get('chi', 0)
        grade = doc.get('grade', 'F')
        grade_class = f"grade-{grade[0].lower()}"
        
        if show_anti:
            anti_fruits = doc.get('anti_fruits', {})
            top_item = max(anti_fruits.items(), key=lambda x: x[1]) if anti_fruits else ('N/A', 0)
            top_display = f"{top_item[0]} ({top_item[1]})"
        else:
            fruits = doc.get('fruits', {})
            top_item = max(fruits.items(), key=lambda x: x[1]) if fruits else ('N/A', 0)
            top_display = f"{top_item[0]} ({top_item[1]})"
        
        rows.append(f"""
                        <tr>
                            <td><strong>#{rank}</strong></td>
                            <td>{filename}</td>
                            <td><strong>{chi:.3f}</strong></td>
                            <td><span class="grade {grade_class}">{grade}</span></td>
                            <td>{top_display}</td>
                        </tr>""")
    
    return ''.join(rows)


def _generate_all_docs_rows(docs):
    """Generate HTML table rows for all documents."""
    rows = []
    for doc in docs:
        filename = doc.get('filename', 'Unknown')
        word_count = doc.get('word_count', 0)
        chi = doc.get('chi', 0)
        grade = doc.get('grade', 'F')
        grade_class = f"grade-{grade[0].lower()}"
        
        fruits = doc.get('fruits', {})
        top_fruit = max(fruits.items(), key=lambda x: x[1]) if fruits else ('N/A', 0)
        
        rows.append(f"""
                        <tr>
                            <td>{filename}</td>
                            <td>{word_count:,}</td>
                            <td><strong>{chi:.3f}</strong></td>
                            <td><span class="grade {grade_class}">{grade}</span></td>
                            <td>{top_fruit[0]} ({top_fruit[1]})</td>
                        </tr>""")
    
    return ''.join(rows)
