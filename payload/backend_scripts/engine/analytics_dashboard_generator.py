"""
Analytics Dashboard Generator
Creates organized output folders with visual dashboards and reports
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import seaborn as sns
from collections import Counter, defaultdict

# Set style
sns.set_style("darkgrid")
plt.rcParams['figure.facecolor'] = '#1e1e1e'
plt.rcParams['axes.facecolor'] = '#2d2d2d'
plt.rcParams['text.color'] = '#e0e0e0'
plt.rcParams['axes.labelcolor'] = '#e0e0e0'
plt.rcParams['xtick.color'] = '#e0e0e0'
plt.rcParams['ytick.color'] = '#e0e0e0'


class AnalyticsDashboardGenerator:
    """Generate organized output folders with visual dashboards."""
    
    def __init__(self, db_path: Path, output_root: Path):
        self.db_path = Path(db_path)
        self.output_root = Path(output_root)
        self.output_root.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped run folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.run_folder = self.output_root / f"analytics_run_{timestamp}"
        self.run_folder.mkdir(parents=True, exist_ok=True)
        
        # Create subfolders
        self.dashboards_folder = self.run_folder / "dashboards"
        self.charts_folder = self.run_folder / "charts"
        self.reports_folder = self.run_folder / "reports"
        self.data_folder = self.run_folder / "data"
        
        for folder in [self.dashboards_folder, self.charts_folder, self.reports_folder, self.data_folder]:
            folder.mkdir(exist_ok=True)
    
    def generate_all_outputs(self, batch_size: int = 12):
        """Generate all dashboards, charts, and reports."""
        print(f"📊 Generating outputs in: {self.run_folder}")
        
        # Generate visual charts
        self._generate_charts()
        
        # Generate markdown dashboards
        self._generate_main_dashboard()
        self._generate_papers_dashboard(batch_size)
        self._generate_concepts_dashboard()
        self._generate_tags_dashboard()
        self._generate_relationships_dashboard()
        
        # Generate reports
        self._generate_summary_report()
        self._generate_detailed_report()
        
        # Export data
        self._export_data_files()
        
        # Create index
        self._create_index()
        
        print(f"✅ All outputs generated in: {self.run_folder}")
        return self.run_folder
    
    def _generate_charts(self):
        """Generate all visual charts."""
        print("📈 Generating visual charts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Tags distribution pie chart
        cursor.execute("SELECT tag, count FROM tags ORDER BY count DESC LIMIT 10")
        tags_data = cursor.fetchall()
        if tags_data:
            self._create_pie_chart(
                dict(tags_data),
                "Top 10 Tags Distribution",
                self.charts_folder / "tags_distribution.png"
            )
        
        # 2. Concepts frequency bar chart
        cursor.execute("SELECT concept, frequency FROM concepts ORDER BY frequency DESC LIMIT 15")
        concepts_data = cursor.fetchall()
        if concepts_data:
            self._create_bar_chart(
                dict(concepts_data),
                "Top 15 Concepts Frequency",
                self.charts_folder / "concepts_frequency.png"
            )
        
        # 3. Papers word count distribution
        cursor.execute("SELECT filename, word_count FROM papers ORDER BY word_count DESC LIMIT 20")
        papers_data = cursor.fetchall()
        if papers_data:
            self._create_horizontal_bar_chart(
                dict(papers_data),
                "Top 20 Papers by Word Count",
                self.charts_folder / "papers_wordcount.png"
            )
        
        # 4. Relationship network heatmap
        cursor.execute("""
            SELECT concept_a, concept_b, strength 
            FROM relationships 
            ORDER BY strength DESC 
            LIMIT 50
        """)
        relationships_data = cursor.fetchall()
        if relationships_data:
            self._create_relationship_heatmap(
                relationships_data,
                self.charts_folder / "relationships_heatmap.png"
            )
        
        # 5. Timeline chart (papers by modification date)
        cursor.execute("""
            SELECT modified_date, COUNT(*) 
            FROM papers 
            GROUP BY DATE(modified_date)
            ORDER BY modified_date DESC
            LIMIT 30
        """)
        timeline_data = cursor.fetchall()
        if timeline_data:
            self._create_timeline_chart(
                timeline_data,
                "Papers Modified Over Time (Last 30 Days)",
                self.charts_folder / "papers_timeline.png"
            )
        
        conn.close()
        print(f"  ✓ Generated {len(list(self.charts_folder.glob('*.png')))} charts")
    
    def _create_pie_chart(self, data: Dict, title: str, output_path: Path):
        """Create a pie chart."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = list(data.keys())
        sizes = list(data.values())
        colors = sns.color_palette("husl", len(labels))
        
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=colors, startangle=90
        )
        
        for text in texts:
            text.set_color('#e0e0e0')
        for autotext in autotexts:
            autotext.set_color('#1e1e1e')
            autotext.set_weight('bold')
        
        ax.set_title(title, color='#e0e0e0', fontsize=16, pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#1e1e1e')
        plt.close()
    
    def _create_bar_chart(self, data: Dict, title: str, output_path: Path):
        """Create a bar chart."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        labels = list(data.keys())
        values = list(data.values())
        colors = sns.color_palette("viridis", len(labels))
        
        bars = ax.bar(labels, values, color=colors)
        
        ax.set_title(title, color='#e0e0e0', fontsize=16, pad=20)
        ax.set_xlabel('Concept', color='#e0e0e0', fontsize=12)
        ax.set_ylabel('Frequency', color='#e0e0e0', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#1e1e1e')
        plt.close()
    
    def _create_horizontal_bar_chart(self, data: Dict, title: str, output_path: Path):
        """Create a horizontal bar chart."""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Truncate long labels
        labels = [str(k)[:30] + '...' if len(str(k)) > 30 else str(k) for k in data.keys()]
        values = list(data.values())
        colors = sns.color_palette("coolwarm", len(labels))
        
        y_pos = range(len(labels))
        bars = ax.barh(y_pos, values, color=colors)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_title(title, color='#e0e0e0', fontsize=16, pad=20)
        ax.set_xlabel('Word Count', color='#e0e0e0', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#1e1e1e')
        plt.close()
    
    def _create_relationship_heatmap(self, relationships: List, output_path: Path):
        """Create a relationship heatmap."""
        # Build matrix
        concepts = set()
        for a, b, _ in relationships:
            concepts.add(a)
            concepts.add(b)
        
        concepts = sorted(list(concepts))[:15]  # Limit to 15 for readability
        matrix = [[0.0] * len(concepts) for _ in range(len(concepts))]
        
        concept_idx = {c: i for i, c in enumerate(concepts)}
        
        for a, b, strength in relationships:
            if a in concept_idx and b in concept_idx:
                i, j = concept_idx[a], concept_idx[b]
                matrix[i][j] = strength
                matrix[j][i] = strength
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        sns.heatmap(
            matrix, 
            xticklabels=concepts, 
            yticklabels=concepts,
            cmap='YlOrRd',
            annot=True,
            fmt='.2f',
            cbar_kws={'label': 'Relationship Strength'},
            ax=ax
        )
        
        ax.set_title('Concept Relationship Heatmap', color='#e0e0e0', fontsize=16, pad=20)
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#1e1e1e')
        plt.close()
    
    def _create_timeline_chart(self, timeline_data: List, title: str, output_path: Path):
        """Create a timeline chart."""
        fig, ax = plt.subplots(figsize=(14, 6))
        
        dates = [d[0][:10] for d in timeline_data]  # Extract date part
        counts = [d[1] for d in timeline_data]
        
        ax.plot(dates, counts, marker='o', linewidth=2, markersize=8, color='#00d4ff')
        ax.fill_between(range(len(dates)), counts, alpha=0.3, color='#00d4ff')
        
        ax.set_title(title, color='#e0e0e0', fontsize=16, pad=20)
        ax.set_xlabel('Date', color='#e0e0e0', fontsize=12)
        ax.set_ylabel('Papers Modified', color='#e0e0e0', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, facecolor='#1e1e1e')
        plt.close()
    
    def _generate_main_dashboard(self):
        """Generate main analytics dashboard."""
        print("📄 Generating main dashboard...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get latest snapshot
        cursor.execute("""
            SELECT total_papers, total_words, total_tags, total_links,
                   total_concepts, metrics_json
            FROM snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        total_papers, total_words, total_tags, total_links, total_concepts, metrics_json = row
        metrics = json.loads(metrics_json)
        
        dashboard = f"""# 📊 Global Analytics Dashboard
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## 🎯 Executive Summary

### Key Metrics

| Metric | Value |
|--------|-------|
| 📄 Total Papers | {total_papers:,} |
| 📝 Total Words | {total_words:,} |
| 🏷️ Unique Tags | {total_tags} |
| 🔗 Total Links | {total_links} |
| 💡 Tracked Concepts | {total_concepts} |
| 🕸️ Relationships | {metrics.get('total_relationships', 0)} |
| 📊 Avg Words/Paper | {metrics.get('avg_words_per_paper', 0):.0f} |
| 🔬 Avg Relationship Strength | {metrics.get('avg_relationship_strength', 0):.3f} |

---

## 📈 Visual Analytics

### Charts
- [Tags Distribution](../charts/tags_distribution.png)
- [Concepts Frequency](../charts/concepts_frequency.png)
- [Papers Word Count](../charts/papers_wordcount.png)
- [Relationship Heatmap](../charts/relationships_heatmap.png)
- [Papers Timeline](../charts/papers_timeline.png)

---

## 📚 Detailed Dashboards

- [[Papers Dashboard]] - Grouped by batches of 12
- [[Concepts Dashboard]] - Key Theophysics concepts
- [[Tags Dashboard]] - Tag distribution and usage
- [[Relationships Dashboard]] - Concept co-occurrence

---

## 📋 Reports

- [[Summary Report]] - High-level overview
- [[Detailed Report]] - Comprehensive analysis

---

## 💾 Data Exports

- `data/papers.json` - All paper metadata
- `data/tags.json` - Tag aggregation
- `data/concepts.json` - Concept tracking
- `data/relationships.json` - Relationship matrix
- `data/full_export.json` - Complete database export

---

*This dashboard was automatically generated by the Global Analytics Engine*
"""
        
        output_path = self.dashboards_folder / "Main_Dashboard.md"
        output_path.write_text(dashboard, encoding='utf-8')
        
        conn.close()
        print(f"  ✓ Generated main dashboard")
    
    def _generate_papers_dashboard(self, batch_size: int):
        """Generate papers dashboard with batching."""
        print(f"📄 Generating papers dashboard (batch size: {batch_size})...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT filename, title, word_count, tags_json, links_json, modified_date
            FROM papers
            ORDER BY word_count DESC
        """)
        
        papers = cursor.fetchall()
        conn.close()
        
        if not papers:
            return
        
        # Create batches
        batches = [papers[i:i + batch_size] for i in range(0, len(papers), batch_size)]
        
        # Main papers dashboard
        dashboard = f"""# 📄 Papers Dashboard
*Total Papers: {len(papers)}*
*Batches: {len(batches)} (size: {batch_size})*

---

## 📦 Paper Batches

"""
        
        for i, batch in enumerate(batches, 1):
            batch_name = f"Batch_{i:02d}"
            dashboard += f"### [[{batch_name}]] - Papers {(i-1)*batch_size + 1} to {min(i*batch_size, len(papers))}\n\n"
            
            # Create individual batch dashboard
            self._create_batch_dashboard(batch, batch_name, i)
        
        dashboard += "\n---\n\n## 📊 Statistics\n\n"
        dashboard += f"- **Total Papers**: {len(papers)}\n"
        dashboard += f"- **Total Words**: {sum(p[2] for p in papers):,}\n"
        dashboard += f"- **Average Words/Paper**: {sum(p[2] for p in papers) / len(papers):.0f}\n"
        
        output_path = self.dashboards_folder / "Papers_Dashboard.md"
        output_path.write_text(dashboard, encoding='utf-8')
        
        print(f"  ✓ Generated papers dashboard with {len(batches)} batches")
    
    def _create_batch_dashboard(self, papers: List, batch_name: str, batch_num: int):
        """Create a dashboard for a batch of papers."""
        dashboard = f"""# 📦 {batch_name}
*Batch {batch_num}*

---

## Papers in This Batch

| # | Filename | Title | Words | Tags | Links |
|---|----------|-------|-------|------|-------|
"""
        
        for i, paper in enumerate(papers, 1):
            filename, title, word_count, tags_json, links_json, modified = paper
            tags = json.loads(tags_json) if tags_json else []
            links = json.loads(links_json) if links_json else []
            
            title_short = title[:40] + '...' if len(title) > 40 else title
            dashboard += f"| {i} | `{filename}` | {title_short} | {word_count:,} | {len(tags)} | {len(links)} |\n"
        
        dashboard += f"\n---\n\n## Batch Statistics\n\n"
        dashboard += f"- **Papers in Batch**: {len(papers)}\n"
        dashboard += f"- **Total Words**: {sum(p[2] for p in papers):,}\n"
        dashboard += f"- **Average Words**: {sum(p[2] for p in papers) / len(papers):.0f}\n"
        
        output_path = self.dashboards_folder / f"{batch_name}.md"
        output_path.write_text(dashboard, encoding='utf-8')
    
    def _generate_concepts_dashboard(self):
        """Generate concepts dashboard."""
        print("💡 Generating concepts dashboard...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT concept, frequency, papers_json
            FROM concepts
            ORDER BY frequency DESC
        """)
        
        concepts = cursor.fetchall()
        conn.close()
        
        if not concepts:
            return
        
        dashboard = f"""# 💡 Concepts Dashboard
*Total Concepts: {len(concepts)}*

---

## Top Concepts

| Rank | Concept | Frequency | Papers |
|------|---------|-----------|--------|
"""
        
        for i, (concept, frequency, papers_json) in enumerate(concepts, 1):
            papers = json.loads(papers_json) if papers_json else []
            dashboard += f"| {i} | **{concept}** | {frequency:,} | {len(papers)} |\n"
        
        dashboard += f"\n---\n\n![Concepts Chart](../charts/concepts_frequency.png)\n"
        
        output_path = self.dashboards_folder / "Concepts_Dashboard.md"
        output_path.write_text(dashboard, encoding='utf-8')
        
        print(f"  ✓ Generated concepts dashboard")
    
    def _generate_tags_dashboard(self):
        """Generate tags dashboard."""
        print("🏷️  Generating tags dashboard...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tag, count, papers_json
            FROM tags
            ORDER BY count DESC
        """)
        
        tags = cursor.fetchall()
        conn.close()
        
        if not tags:
            return
        
        dashboard = f"""# 🏷️ Tags Dashboard
*Total Tags: {len(tags)}*

---

## Tag Distribution

| Rank | Tag | Count | Papers |
|------|-----|-------|--------|
"""
        
        for i, (tag, count, papers_json) in enumerate(tags[:50], 1):  # Top 50
            papers = json.loads(papers_json) if papers_json else []
            dashboard += f"| {i} | `{tag}` | {count} | {len(papers)} |\n"
        
        dashboard += f"\n---\n\n![Tags Chart](../charts/tags_distribution.png)\n"
        
        output_path = self.dashboards_folder / "Tags_Dashboard.md"
        output_path.write_text(dashboard, encoding='utf-8')
        
        print(f"  ✓ Generated tags dashboard")
    
    def _generate_relationships_dashboard(self):
        """Generate relationships dashboard."""
        print("🕸️  Generating relationships dashboard...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT concept_a, concept_b, strength, papers_json
            FROM relationships
            ORDER BY strength DESC
            LIMIT 100
        """)
        
        relationships = cursor.fetchall()
        conn.close()
        
        if not relationships:
            return
        
        dashboard = f"""# 🕸️ Relationships Dashboard
*Total Relationships: {len(relationships)}*

---

## Top Concept Relationships

| Rank | Concept A | Concept B | Strength | Common Papers |
|------|-----------|-----------|----------|---------------|
"""
        
        for i, (concept_a, concept_b, strength, papers_json) in enumerate(relationships, 1):
            papers = json.loads(papers_json) if papers_json else []
            dashboard += f"| {i} | **{concept_a}** | **{concept_b}** | {strength:.3f} | {len(papers)} |\n"
        
        dashboard += f"\n---\n\n![Relationship Heatmap](../charts/relationships_heatmap.png)\n"
        
        output_path = self.dashboards_folder / "Relationships_Dashboard.md"
        output_path.write_text(dashboard, encoding='utf-8')
        
        print(f"  ✓ Generated relationships dashboard")
    
    def _generate_summary_report(self):
        """Generate summary report."""
        print("📋 Generating summary report...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT metrics_json FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
        
        metrics = json.loads(row[0])
        
        report = f"""# 📋 Analytics Summary Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## Executive Summary

This report provides a high-level overview of the Theophysics research ecosystem analytics.

### Key Findings

- **Total Papers**: {metrics.get('total_papers', 0):,}
- **Total Words**: {metrics.get('total_words', 0):,}
- **Unique Tags**: {metrics.get('total_tags', 0)}
- **Total Links**: {metrics.get('total_links', 0)}
- **Tracked Concepts**: {metrics.get('total_concepts', 0)}
- **Concept Relationships**: {metrics.get('total_relationships', 0)}

### Averages

- **Words per Paper**: {metrics.get('avg_words_per_paper', 0):.0f}
- **Tag Usage**: {metrics.get('avg_tag_usage', 0):.1f}
- **Relationship Strength**: {metrics.get('avg_relationship_strength', 0):.3f}

---

## Recommendations

1. **Content Density**: Papers average {metrics.get('avg_words_per_paper', 0):.0f} words - consider expanding shorter papers
2. **Tagging**: {metrics.get('total_tags', 0)} unique tags provide good categorization
3. **Linking**: {metrics.get('total_links', 0)} links create a connected knowledge graph
4. **Concepts**: {metrics.get('total_concepts', 0)} key concepts tracked across papers

---

*For detailed analysis, see the [[Detailed Report]]*
"""
        
        output_path = self.reports_folder / "Summary_Report.md"
        output_path.write_text(report, encoding='utf-8')
        
        conn.close()
        print(f"  ✓ Generated summary report")
    
    def _generate_detailed_report(self):
        """Generate detailed analysis report."""
        print("📋 Generating detailed report...")
        
        # This would contain much more detailed analysis
        report = f"""# 📋 Detailed Analytics Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

---

## Comprehensive Analysis

This report contains detailed analysis of all data points in the Theophysics research ecosystem.

### Sections

1. [[#Paper Analysis]]
2. [[#Tag Analysis]]
3. [[#Concept Analysis]]
4. [[#Relationship Analysis]]
5. [[#Temporal Analysis]]

---

## Paper Analysis

See [[Papers_Dashboard]] for complete paper listings grouped into batches of 12.

## Tag Analysis

See [[Tags_Dashboard]] for tag distribution and usage patterns.

## Concept Analysis

See [[Concepts_Dashboard]] for key concept tracking and frequency.

## Relationship Analysis

See [[Relationships_Dashboard]] for concept co-occurrence matrix.

---

*This is a comprehensive report. Refer to individual dashboards for specific details.*
"""
        
        output_path = self.reports_folder / "Detailed_Report.md"
        output_path.write_text(report, encoding='utf-8')
        
        print(f"  ✓ Generated detailed report")
    
    def _export_data_files(self):
        """Export data to JSON files."""
        print("💾 Exporting data files...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Export papers
        cursor.execute("SELECT * FROM papers")
        columns = [desc[0] for desc in cursor.description]
        papers = [dict(zip(columns, row)) for row in cursor.fetchall()]
        (self.data_folder / "papers.json").write_text(json.dumps(papers, indent=2), encoding='utf-8')
        
        # Export tags
        cursor.execute("SELECT * FROM tags")
        columns = [desc[0] for desc in cursor.description]
        tags = [dict(zip(columns, row)) for row in cursor.fetchall()]
        (self.data_folder / "tags.json").write_text(json.dumps(tags, indent=2), encoding='utf-8')
        
        # Export concepts
        cursor.execute("SELECT * FROM concepts")
        columns = [desc[0] for desc in cursor.description]
        concepts = [dict(zip(columns, row)) for row in cursor.fetchall()]
        (self.data_folder / "concepts.json").write_text(json.dumps(concepts, indent=2), encoding='utf-8')
        
        # Export relationships
        cursor.execute("SELECT * FROM relationships")
        columns = [desc[0] for desc in cursor.description]
        relationships = [dict(zip(columns, row)) for row in cursor.fetchall()]
        (self.data_folder / "relationships.json").write_text(json.dumps(relationships, indent=2), encoding='utf-8')
        
        conn.close()
        print(f"  ✓ Exported 4 data files")
    
    def _create_index(self):
        """Create index file for the run."""
        index = f"""# 📊 Analytics Run Index
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Location: `{self.run_folder}`*

---

## 📂 Folder Structure

```
{self.run_folder.name}/
├── dashboards/          # Markdown dashboards
│   ├── Main_Dashboard.md
│   ├── Papers_Dashboard.md
│   ├── Concepts_Dashboard.md
│   ├── Tags_Dashboard.md
│   └── Relationships_Dashboard.md
├── charts/              # Visual charts (PNG)
│   ├── tags_distribution.png
│   ├── concepts_frequency.png
│   ├── papers_wordcount.png
│   ├── relationships_heatmap.png
│   └── papers_timeline.png
├── reports/             # Analysis reports
│   ├── Summary_Report.md
│   └── Detailed_Report.md
└── data/                # JSON exports
    ├── papers.json
    ├── tags.json
    ├── concepts.json
    └── relationships.json
```

---

## 🚀 Quick Start

1. Open [[dashboards/Main_Dashboard.md]] for overview
2. Browse [[dashboards/Papers_Dashboard.md]] for paper batches
3. View charts in `charts/` folder
4. Read reports in `reports/` folder

---

*This analytics run contains complete data extraction and visualization*
"""
        
        output_path = self.run_folder / "INDEX.md"
        output_path.write_text(index, encoding='utf-8')
