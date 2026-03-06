"""
Tag Analytics Engine
Transforms tags from labels into dynamic state variables.

Components:
1. Tag Engine - frequency, co-occurrence, velocity
2. Law Engine - constraint checking, missing operators
3. Narrative Engine - phase detection, storyline summaries
4. Diagnostics - system state reports

Author: David Lowe / Theophysics
"""

import re
import json
import itertools
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
import os


@dataclass
class Note:
    """Represents a vault note with temporal and semantic data."""
    path: str
    tags: List[str]
    links: List[str]
    created: Optional[datetime]
    modified: Optional[datetime]
    text: str
    word_count: int = 0
    
    def __post_init__(self):
        self.word_count = len(self.text.split())


@dataclass
class TagMetrics:
    """Metrics for a single tag."""
    name: str
    frequency: int = 0
    velocity: float = 0.0  # appearances per day (recent)
    acceleration: float = 0.0  # change in velocity
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    co_occurs_with: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass 
class SystemState:
    """Current state of the vault system."""
    timestamp: datetime
    total_notes: int
    total_tags: int
    dominant_tags: List[Tuple[str, int]]  # top tags
    emerging_tags: List[Tuple[str, float]]  # high velocity
    fading_tags: List[Tuple[str, float]]  # negative velocity
    regime: str  # detected phase
    coherence_score: float
    law_violations: List[dict]


# ============================================================
# TEN LAWS - Tag Constraints
# ============================================================

TEN_LAWS = {
    "Law1_Gravity_Sin": {
        "triggers": ["#sin", "#fall", "#gravity", "#downward"],
        "requires": ["#entropy", "#disorder"],
        "forbids": [],
        "description": "Sin operates like gravity - always pulling toward disorder"
    },
    "Law2_Motion_Momentum": {
        "triggers": ["#momentum", "#motion", "#spiritual-momentum"],
        "requires": ["#force", "#direction"],
        "forbids": [],
        "description": "Spiritual momentum follows laws of motion"
    },
    "Law3_Conservation_Transformation": {
        "triggers": ["#transformation", "#conservation", "#eternal"],
        "requires": ["#energy", "#form-change"],
        "forbids": ["#destruction", "#annihilation"],
        "description": "Nothing is destroyed, only transformed"
    },
    "Law4_Entropy_Renewal": {
        "triggers": ["#entropy", "#decay", "#corruption"],
        "requires": [],
        "forbids": [],
        "description": "Entropy increases without external intervention"
    },
    "Law5_Light_Truth": {
        "triggers": ["#truth", "#light", "#revelation"],
        "requires": ["#visibility", "#clarity"],
        "forbids": ["#darkness", "#deception"],
        "description": "Truth operates like light - reveals and exposes"
    },
    "Law6_Cause_Effect": {
        "triggers": ["#sowing", "#reaping", "#causality"],
        "requires": ["#action", "#consequence"],
        "forbids": [],
        "description": "Every action has proportional consequences"
    },
    "Law7_Grace_Negentropy": {
        "triggers": ["#grace", "#miracle", "#resurrection", "#negentropy"],
        "requires": ["#open-system", "#external-input", "#external-operator"],
        "forbids": ["#closed-system"],
        "description": "Grace requires open system with external operator"
    },
    "Law8_Quantum_Faith": {
        "triggers": ["#faith", "#belief", "#observer"],
        "requires": ["#measurement", "#collapse"],
        "forbids": [],
        "description": "Faith operates like quantum observation"
    },
    "Law9_Relativity_Perspective": {
        "triggers": ["#perspective", "#relativity", "#frame"],
        "requires": ["#observer", "#reference"],
        "forbids": [],
        "description": "Truth is absolute but perception is relative"
    },
    "Law10_Consciousness_Soul": {
        "triggers": ["#consciousness", "#soul", "#awareness"],
        "requires": ["#observer", "#witness"],
        "forbids": [],
        "description": "Consciousness is fundamental, not emergent"
    }
}


class TagAnalyticsEngine:
    """
    Main engine for tag analytics.
    Treats tags as state variables, not labels.
    """
    
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
    YAML_TAGS_PATTERN = re.compile(r'^tags:\s*\[([^\]]+)\]', re.MULTILINE)
    YAML_TAGS_LIST_PATTERN = re.compile(r'^tags:\s*\n((?:\s*-\s*.+\n?)+)', re.MULTILINE)
    INLINE_TAG_PATTERN = re.compile(r'#([A-Za-z][A-Za-z0-9_\-/]+)')
    WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')
    DATE_PATTERNS = [
        re.compile(r'created:\s*["\']?(\d{4}-\d{2}-\d{2})["\']?'),
        re.compile(r'date:\s*["\']?(\d{4}-\d{2}-\d{2})["\']?'),
    ]
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.notes: List[Note] = []
        self.tag_metrics: Dict[str, TagMetrics] = {}
        self.cooccurrence: Counter = Counter()
        self.phases: List[dict] = []
        self.system_states: List[SystemState] = []
        
    # ============================================================
    # PARSING
    # ============================================================
    
    def _parse_date(self, content: str, file_path: Path) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Extract created/modified dates."""
        created = None
        modified = None
        
        # Try YAML frontmatter
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(content)
            if match:
                try:
                    created = datetime.fromisoformat(match.group(1))
                    break
                except:
                    pass
        
        # Fall back to file stats
        try:
            stat = file_path.stat()
            if not created:
                created = datetime.fromtimestamp(stat.st_ctime)
            modified = datetime.fromtimestamp(stat.st_mtime)
        except:
            pass
        
        return created, modified
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract all tags from content."""
        tags = []
        
        # YAML frontmatter tags
        fm_match = self.FRONTMATTER_PATTERN.match(content)
        if fm_match:
            frontmatter = fm_match.group(1)
            
            # Inline format
            inline_match = self.YAML_TAGS_PATTERN.search(frontmatter)
            if inline_match:
                tag_str = inline_match.group(1)
                tags.extend([t.strip().strip('"\'') for t in tag_str.split(',') if t.strip()])
            
            # List format
            list_match = self.YAML_TAGS_LIST_PATTERN.search(frontmatter)
            if list_match:
                for line in list_match.group(1).split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        tag = line[1:].strip().strip('"\'')
                        if tag:
                            tags.append(tag)
        
        # Inline #tags (outside code blocks)
        body = self.FRONTMATTER_PATTERN.sub('', content)
        body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
        tags.extend(self.INLINE_TAG_PATTERN.findall(body))
        
        # Normalize
        return [f"#{t.lower().strip('#')}" for t in tags if t]
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract wikilinks."""
        return self.WIKILINK_PATTERN.findall(content)
    
    def load_vault(self, exclude_folders: List[str] = None, max_notes: int = 1000, 
                   priority_folders: List[str] = None):
        """
        Load notes from vault with filtering.
        Prioritizes certain folders and limits total notes.
        """
        exclude = exclude_folders or [
            '.obsidian', '.git', 'venv', '__pycache__', 'node_modules', '_TAG_NOTES',
            'ARCHIVE', '_gsdata_', 'Data_Analytics', 'Theophysics_Analytics'
        ]
        
        # Priority folders to include first
        priority = priority_folders or [
            '03_PUBLICATIONS', '04_CANONICAL', '02_LIBRARY/4_LEXICON',
            'COMPLETE_LOGOS_PAPERS', '10-Laws'
        ]
        
        print(f"Loading vault from {self.vault_path} (max {max_notes} notes)...")
        md_files = list(self.vault_path.rglob('*.md'))
        
        # Separate priority and regular files
        priority_files = []
        regular_files = []
        
        for file_path in md_files:
            rel_path = file_path.relative_to(self.vault_path)
            rel_str = str(rel_path)
            
            # Skip excluded
            if any(part in exclude for part in rel_path.parts):
                continue
            
            # Check if priority
            is_priority = any(p in rel_str for p in priority)
            if is_priority:
                priority_files.append(file_path)
            else:
                regular_files.append(file_path)
        
        # Process priority first, then fill with regular up to max
        files_to_process = priority_files[:max_notes]
        remaining = max_notes - len(files_to_process)
        if remaining > 0:
            files_to_process.extend(regular_files[:remaining])
        
        print(f"Processing {len(files_to_process)} files ({len(priority_files)} priority, {len(regular_files)} regular)")
        
        for file_path in files_to_process:
            rel_path = file_path.relative_to(self.vault_path)
            
            try:
                content = file_path.read_text(encoding='utf-8')
                tags = self._extract_tags(content)
                
                # Skip notes with no tags
                if not tags:
                    continue
                    
                links = self._extract_links(content)
                created, modified = self._parse_date(content, file_path)
                
                note = Note(
                    path=str(rel_path),
                    tags=tags,
                    links=links,
                    created=created,
                    modified=modified,
                    text=content
                )
                self.notes.append(note)
                
            except Exception as e:
                pass
        
        # Sort by creation date
        self.notes.sort(key=lambda n: n.created or datetime.min)
        print(f"Loaded {len(self.notes)} notes with tags")
    
    # ============================================================
    # TAG ENGINE - Frequency, Co-occurrence, Velocity
    # ============================================================
    
    def compute_tag_frequency(self, window: int = None) -> Counter:
        """
        Compute tag frequency.
        If window specified, only last N notes.
        """
        notes = self.notes[-window:] if window else self.notes
        tags = []
        for note in notes:
            tags.extend(note.tags)
        return Counter(tags)
    
    def compute_cooccurrence(self) -> Counter:
        """Compute tag co-occurrence matrix."""
        pairs = Counter()
        for note in self.notes:
            unique_tags = set(note.tags)
            for a, b in itertools.combinations(sorted(unique_tags), 2):
                pairs[(a, b)] += 1
        self.cooccurrence = pairs
        return pairs
    
    def compute_tag_velocity(self, days: int = 30) -> Dict[str, float]:
        """
        Compute tag velocity (appearances per day).
        Compares recent period to historical average.
        """
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        
        recent_tags = Counter()
        recent_days = 0
        historical_tags = Counter()
        historical_days = 0
        
        for note in self.notes:
            if note.created and note.created >= cutoff:
                recent_tags.update(note.tags)
                recent_days = max(recent_days, (now - note.created).days + 1)
            elif note.created:
                historical_tags.update(note.tags)
                historical_days = max(historical_days, (cutoff - note.created).days + 1)
        
        velocity = {}
        all_tags = set(recent_tags.keys()) | set(historical_tags.keys())
        
        for tag in all_tags:
            recent_rate = recent_tags[tag] / max(recent_days, 1)
            historical_rate = historical_tags[tag] / max(historical_days, 1)
            velocity[tag] = recent_rate - historical_rate  # positive = emerging
        
        return velocity
    
    def build_tag_metrics(self):
        """Build comprehensive metrics for all tags."""
        print("Building tag metrics...")
        
        freq = self.compute_tag_frequency()
        velocity = self.compute_tag_velocity()
        cooc = self.compute_cooccurrence()
        
        for tag, count in freq.items():
            metrics = TagMetrics(name=tag, frequency=count)
            metrics.velocity = velocity.get(tag, 0.0)
            
            # Find first/last seen
            for note in self.notes:
                if tag in note.tags:
                    if note.created:
                        if not metrics.first_seen or note.created < metrics.first_seen:
                            metrics.first_seen = note.created
                        if not metrics.last_seen or note.created > metrics.last_seen:
                            metrics.last_seen = note.created
                    metrics.notes.append(note.path)
            
            # Co-occurrence
            for (a, b), count in cooc.items():
                if a == tag:
                    metrics.co_occurs_with[b] = count
                elif b == tag:
                    metrics.co_occurs_with[a] = count
            
            self.tag_metrics[tag] = metrics
        
        print(f"Built metrics for {len(self.tag_metrics)} tags")
    
    # ============================================================
    # LAW ENGINE - Constraint Checking
    # ============================================================
    
    def check_law_violations(self) -> List[dict]:
        """Check all notes for Ten Laws violations."""
        violations = []
        
        for note in self.notes:
            note_tags = set(note.tags)
            
            for law_name, law in TEN_LAWS.items():
                # Check if any trigger tags are present
                triggers = set(f"#{t.strip('#')}" for t in law["triggers"])
                if not triggers.intersection(note_tags):
                    continue
                
                # Check required tags
                required = set(f"#{t.strip('#')}" for t in law["requires"])
                missing = required - note_tags
                
                # Check forbidden tags
                forbidden = set(f"#{t.strip('#')}" for t in law["forbids"])
                present_forbidden = forbidden.intersection(note_tags)
                
                if missing or present_forbidden:
                    violations.append({
                        "note": note.path,
                        "law": law_name,
                        "description": law["description"],
                        "missing_required": list(missing),
                        "forbidden_present": list(present_forbidden),
                        "triggers_found": list(triggers.intersection(note_tags))
                    })
        
        return violations
    
    # ============================================================
    # NARRATIVE ENGINE - Phase Detection, Story Extraction
    # ============================================================
    
    def detect_phases(self, window: int = 20) -> List[dict]:
        """
        Detect regime changes / phases in the vault.
        Uses sliding window to find tag distribution shifts.
        """
        if len(self.notes) < window * 2:
            return []
        
        phases = []
        prev_dominant = None
        
        for i in range(window, len(self.notes), window // 2):
            window_notes = self.notes[i-window:i]
            tags = Counter()
            for note in window_notes:
                tags.update(note.tags)
            
            # Get dominant tags (top 5)
            dominant = [t for t, _ in tags.most_common(5)]
            
            if prev_dominant and set(dominant) != set(prev_dominant):
                # Phase transition detected
                start_note = window_notes[0]
                end_note = window_notes[-1]
                
                phases.append({
                    "start": start_note.created.isoformat() if start_note.created else None,
                    "end": end_note.created.isoformat() if end_note.created else None,
                    "from_tags": prev_dominant,
                    "to_tags": dominant,
                    "notes_in_window": len(window_notes)
                })
            
            prev_dominant = dominant
        
        self.phases = phases
        return phases
    
    def extract_narrative_summary(self, window: int = 30) -> str:
        """
        Generate a narrative summary of recent tag evolution.
        """
        recent = self.notes[-window:] if len(self.notes) >= window else self.notes
        
        if not recent:
            return "No notes to analyze."
        
        # Tag frequency in window
        freq = Counter()
        for note in recent:
            freq.update(note.tags)
        
        top_tags = freq.most_common(10)
        
        # Velocity
        velocity = self.compute_tag_velocity(days=30)
        emerging = [(t, v) for t, v in velocity.items() if v > 0.1]
        emerging.sort(key=lambda x: x[1], reverse=True)
        
        fading = [(t, v) for t, v in velocity.items() if v < -0.1]
        fading.sort(key=lambda x: x[1])
        
        # Build narrative
        lines = [
            f"## System State Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Notes Analyzed:** {len(recent)} (last {window})",
            "",
            "### Dominant Concepts",
        ]
        
        for tag, count in top_tags[:5]:
            lines.append(f"- **{tag}**: {count} occurrences")
        
        if emerging[:3]:
            lines.append("")
            lines.append("### Emerging Concepts (rising velocity)")
            for tag, vel in emerging[:3]:
                lines.append(f"- **{tag}**: +{vel:.2f}/day")
        
        if fading[:3]:
            lines.append("")
            lines.append("### Fading Concepts (declining velocity)")
            for tag, vel in fading[:3]:
                lines.append(f"- **{tag}**: {vel:.2f}/day")
        
        # Co-occurrence insights
        if self.cooccurrence:
            lines.append("")
            lines.append("### Strongest Tag Pairs")
            top_pairs = self.cooccurrence.most_common(5)
            for (a, b), count in top_pairs:
                lines.append(f"- {a} ↔ {b}: {count} co-occurrences")
        
        return "\n".join(lines)
    
    # ============================================================
    # SYSTEM STATE
    # ============================================================
    
    def compute_coherence_score(self) -> float:
        """
        Compute overall coherence score (0-1).
        Based on tag consistency, law compliance, and structure.
        """
        if not self.notes:
            return 0.0
        
        # Factor 1: Tag concentration (fewer dominant tags = more coherent)
        freq = self.compute_tag_frequency()
        if freq:
            total = sum(freq.values())
            top_5_share = sum(c for _, c in freq.most_common(5)) / total
        else:
            top_5_share = 0
        
        # Factor 2: Law compliance
        violations = self.check_law_violations()
        violation_rate = len(violations) / max(len(self.notes), 1)
        compliance = max(0, 1 - violation_rate)
        
        # Factor 3: Co-occurrence density (more connections = more coherent)
        if self.cooccurrence:
            avg_cooc = sum(self.cooccurrence.values()) / len(self.cooccurrence)
            cooc_score = min(avg_cooc / 10, 1.0)  # normalize
        else:
            cooc_score = 0
        
        # Weighted average
        score = (top_5_share * 0.3) + (compliance * 0.5) + (cooc_score * 0.2)
        return round(score, 3)
    
    def get_system_state(self) -> SystemState:
        """Get current system state snapshot."""
        freq = self.compute_tag_frequency()
        velocity = self.compute_tag_velocity()
        violations = self.check_law_violations()
        
        emerging = [(t, v) for t, v in velocity.items() if v > 0.05]
        emerging.sort(key=lambda x: x[1], reverse=True)
        
        fading = [(t, v) for t, v in velocity.items() if v < -0.05]
        fading.sort(key=lambda x: x[1])
        
        # Detect current regime
        top_tags = [t for t, _ in freq.most_common(3)]
        if any("grace" in t or "negentropy" in t for t in top_tags):
            regime = "Restoration"
        elif any("entropy" in t or "chaos" in t for t in top_tags):
            regime = "Decay"
        elif any("coherence" in t or "order" in t for t in top_tags):
            regime = "Coherence"
        else:
            regime = "Exploration"
        
        return SystemState(
            timestamp=datetime.now(),
            total_notes=len(self.notes),
            total_tags=len(freq),
            dominant_tags=freq.most_common(10),
            emerging_tags=emerging[:5],
            fading_tags=fading[:5],
            regime=regime,
            coherence_score=self.compute_coherence_score(),
            law_violations=violations[:10]  # top 10
        )
    
    # ============================================================
    # REPORTS
    # ============================================================
    
    def generate_daily_report(self, output_path: str = None) -> str:
        """Generate daily system state report."""
        self.build_tag_metrics()
        self.compute_cooccurrence()
        
        state = self.get_system_state()
        narrative = self.extract_narrative_summary()
        phases = self.detect_phases()
        
        report = f"""---
type: system-report
generated: "{state.timestamp.isoformat()}"
regime: "{state.regime}"
coherence: {state.coherence_score}
---

# Daily System State Report

**Generated:** {state.timestamp.strftime('%Y-%m-%d %H:%M')}
**Regime:** {state.regime}
**Coherence Score:** {state.coherence_score:.1%}

## Overview
- **Total Notes:** {state.total_notes}
- **Unique Tags:** {state.total_tags}
- **Law Violations:** {len(state.law_violations)}

{narrative}

## Recent Phase Transitions
"""
        if phases:
            for phase in phases[-3:]:
                report += f"\n### {phase.get('start', 'Unknown')} → {phase.get('end', 'Unknown')}\n"
                report += f"- From: {', '.join(phase['from_tags'][:3])}\n"
                report += f"- To: {', '.join(phase['to_tags'][:3])}\n"
        else:
            report += "\n_No significant phase transitions detected._\n"
        
        if state.law_violations:
            report += "\n## Law Violations (Top 10)\n"
            for v in state.law_violations[:10]:
                report += f"\n### {v['law']}\n"
                report += f"- **Note:** [[{v['note']}]]\n"
                if v['missing_required']:
                    report += f"- **Missing:** {', '.join(v['missing_required'])}\n"
                if v['forbidden_present']:
                    report += f"- **Forbidden:** {', '.join(v['forbidden_present'])}\n"
        
        report += "\n---\n*Auto-generated by Tag Analytics Engine*\n"
        
        if output_path:
            Path(output_path).write_text(report, encoding='utf-8')
            print(f"Report saved to {output_path}")
        
        return report
    
    def export_metrics_json(self, output_path: str):
        """Export all metrics to JSON."""
        data = {
            "generated": datetime.now().isoformat(),
            "total_notes": len(self.notes),
            "tag_count": len(self.tag_metrics),
            "tags": {},
            "cooccurrence": [],
            "phases": self.phases
        }
        
        for tag, metrics in self.tag_metrics.items():
            data["tags"][tag] = {
                "frequency": metrics.frequency,
                "velocity": metrics.velocity,
                "first_seen": metrics.first_seen.isoformat() if metrics.first_seen else None,
                "last_seen": metrics.last_seen.isoformat() if metrics.last_seen else None,
                "top_cooccurs": dict(sorted(metrics.co_occurs_with.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        
        for (a, b), count in self.cooccurrence.most_common(100):
            data["cooccurrence"].append({"tag_a": a, "tag_b": b, "count": count})
        
        Path(output_path).write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f"Metrics exported to {output_path}")


def run_daily_analysis(vault_path: str):
    """Run complete daily analysis."""
    engine = TagAnalyticsEngine(vault_path)
    engine.load_vault()
    
    # Generate report
    report_path = Path(vault_path) / "_TAG_NOTES" / f"SYSTEM_STATE_{datetime.now().strftime('%Y-%m-%d')}.md"
    report_path.parent.mkdir(exist_ok=True)
    engine.generate_daily_report(str(report_path))
    
    # Export metrics
    metrics_path = Path(vault_path) / "_TAG_NOTES" / "tag_metrics.json"
    engine.export_metrics_json(str(metrics_path))
    
    return engine


if __name__ == "__main__":
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    engine = run_daily_analysis(vault)
    
    print("\n" + "="*60)
    print("TAG ANALYTICS COMPLETE")
    print("="*60)
    state = engine.get_system_state()
    print(f"Regime: {state.regime}")
    print(f"Coherence: {state.coherence_score:.1%}")
    print(f"Violations: {len(state.law_violations)}")
