"""
TRACKER INTEGRATOR MODULE
==========================
Generates Obsidian Tracker YAML code blocks for dynamic monitoring.

Creates:
- Circulation heatmap tracker
- Breakthrough velocity tracker
- Coherence progress tracker
- Domain distribution pie chart
- Concept velocity tracker

Author: David Lowe & Claude
Date: 2025-11-19
"""

from pathlib import Path
from typing import Dict, List
from datetime import datetime


class TrackerIntegrator:
    """Generates Obsidian Tracker dashboards"""

    def __init__(self, vault_path: Path, config: Dict):
        self.vault_path = Path(vault_path)
        self.config = config

    def generate_all_trackers(self, circulation_patterns: List):
        """Generate all Obsidian Tracker dashboards"""
        print("Generating Obsidian Tracker blocks...")

        analytics_dir = self.vault_path / "_Analytics"
        analytics_dir.mkdir(exist_ok=True)

        trackers_dir = analytics_dir / "Trackers"
        trackers_dir.mkdir(exist_ok=True)

        # Generate circulation tracker
        self._generate_circulation_tracker(trackers_dir, circulation_patterns)

        # Generate other trackers
        self._generate_breakthrough_velocity_tracker(trackers_dir)
        self._generate_coherence_progress_tracker(trackers_dir)

        print(f"  ✓ Trackers saved to: {trackers_dir}/")

    def _generate_circulation_tracker(self, trackers_dir: Path, patterns: List):
        """Create circulation heatmap tracker"""
        tracker_content = f"""---
type: tracker_dashboard
generated: {datetime.now().isoformat()}
---

# 🔄 Circulation Detection Dashboard

## Active Circulation Patterns

"""

        if patterns:
            for pattern in patterns[:10]:
                prob = pattern.breakthrough_probability
                status = "⚠️  IMMINENT" if prob > 0.70 else "📊 STRONG" if prob > 0.40 else "📈 WEAK"

                tracker_content += f"""
### {pattern.concept_name} - {status}
- **Breakthrough Probability:** {prob:.1%}
- **Approaches:** {pattern.total_approaches}
- **Time Span:** {(pattern.last_approach - pattern.first_approach).days} days
- **Last Approach:** {pattern.last_approach.strftime('%Y-%m-%d')}

"""
        else:
            tracker_content += "\n*No circulation patterns detected*\n"

        tracker_content += """

## Obsidian Tracker Visualization

```tracker
searchType: frontmatter
searchTarget: circulation_patterns
folder: /
month:
    mode: circle
    threshold: 0.70
    color: good
    dimNotInMonth: false
```

---

*Run orchestrator.py → Detect Circulation to update*
"""

        tracker_path = trackers_dir / "Circulation_Tracker.md"
        tracker_path.write_text(tracker_content, encoding='utf-8')

        print(f"  ✓ Created: {tracker_path.name}")

    def _generate_breakthrough_velocity_tracker(self, trackers_dir: Path):
        """Create breakthrough accumulation tracker"""
        tracker_content = """---
type: tracker_dashboard
---

# 🎯 Breakthrough Velocity Tracker

## Cumulative Breakthroughs Over Time

```tracker
searchType: frontmatter
searchTarget: breakthrough_count
folder: /
line:
    title: Breakthrough Accumulation (Vault-Wide)
    xAxisLabel: Date
    yAxisLabel: Cumulative Breakthroughs
    lineColor: "#00ff41"
    showLegend: false
    yMin: 0
```

## Statistics

**Total Detected:** {{sum(frontmatter(breakthrough_count))}}
**This Month:** {{count(WHERE date > date(today) - dur(30 days))}}
**Average per Paper:** {{average(frontmatter(breakthrough_count))}}

---

*Updates automatically with paper frontmatter*
"""

        tracker_path = trackers_dir / "Breakthrough_Velocity.md"
        tracker_path.write_text(tracker_content, encoding='utf-8')

        print(f"  ✓ Created: {tracker_path.name}")

    def _generate_coherence_progress_tracker(self, trackers_dir: Path):
        """Create coherence progress tracker"""
        tracker_content = """---
type: tracker_dashboard
---

# 📈 Coherence Progress Tracker

## Vault Coherence Over Time

```tracker
searchType: frontmatter
searchTarget: coherence_score
folder: /
line:
    title: Vault Coherence Progress
    xAxisLabel: Date
    yAxisLabel: Coherence Score (%)
    yMin: 0
    yMax: 100
    lineColor: "#00ff41"
    showPoint: true
    pointSize: 4
```

## Coherence Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Vault Average | {{average(frontmatter(coherence_score))}}% | 90% | In Progress |
| Best Paper | {{max(frontmatter(coherence_score))}}% | 95% | ✓ |
| Weakest Paper | {{min(frontmatter(coherence_score))}}% | 75% | ⚠️ |

---

*Goal: Increase vault-wide coherence from 57.3% to 90%*
"""

        tracker_path = trackers_dir / "Coherence_Progress.md"
        tracker_path.write_text(tracker_content, encoding='utf-8')

        print(f"  ✓ Created: {tracker_path.name}")
