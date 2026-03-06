"""
STATS HUB TAB
=============
Grid of small, focused statistics widgets.
Each one does ONE thing and does it well.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QPushButton, QLabel, QFrame, QScrollArea, QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont


class StatCard(QFrame):
    """A single stat card widget."""
    
    def __init__(self, title: str, icon: str = "📊"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            StatCard {
                background-color: #1e2a3a;
                border: 1px solid #2d4a6f;
                border-radius: 8px;
                padding: 12px;
            }
            StatCard:hover {
                border-color: #00d9ff;
            }
        """)
        self.setMinimumSize(200, 120)
        self.setMaximumHeight(150)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header = QLabel(f"{icon} {title}")
        header.setStyleSheet("font-size: 11px; color: #8899aa; font-weight: bold;")
        layout.addWidget(header)
        
        # Value (big number)
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #00d9ff;")
        layout.addWidget(self.value_label)
        
        # Subtitle (details)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("font-size: 10px; color: #667788;")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)
        
        layout.addStretch()
    
    def set_value(self, value: str, subtitle: str = "", color: str = "#00d9ff"):
        self.value_label.setText(str(value))
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        self.subtitle_label.setText(subtitle)
    
    def set_loading(self):
        self.value_label.setText("...")
        self.value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #667788;")
        self.subtitle_label.setText("Loading...")


class StatsWorker(QThread):
    """Background worker to gather all stats."""
    progress = Signal(str)  # status message
    stat_ready = Signal(str, str, str, str)  # card_id, value, subtitle, color
    finished = Signal()
    
    def __init__(self, papers_folder: str, vault_folder: str = ""):
        super().__init__()
        self.papers_folder = Path(papers_folder) if papers_folder else None
        self.vault_folder = Path(vault_folder) if vault_folder else None
    
    def run(self):
        if not self.papers_folder or not self.papers_folder.exists():
            self.stat_ready.emit("papers", "⚠️", "No papers folder", "#ff6b6b")
            self.finished.emit()
            return
        
        # Gather all markdown files
        md_files = list(self.papers_folder.rglob("*.md"))
        
        # === STAT 1: Total Papers ===
        self.progress.emit("Counting papers...")
        paper_count = len([f for f in md_files if not f.name.startswith('_')])
        self.stat_ready.emit("papers", str(paper_count), f"in {self.papers_folder.name}", "#00d9ff")
        
        # === STAT 2: Total Words ===
        self.progress.emit("Counting words...")
        total_words = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                total_words += len(content.split())
            except:
                pass
        
        if total_words > 1000000:
            word_str = f"{total_words/1000000:.1f}M"
        elif total_words > 1000:
            word_str = f"{total_words/1000:.1f}K"
        else:
            word_str = str(total_words)
        self.stat_ready.emit("words", word_str, f"~{total_words//paper_count if paper_count else 0} per paper", "#4ecdc4")
        
        # === STAT 3: Semantic Tags ===
        self.progress.emit("Counting semantic tags...")
        tag_pattern = re.compile(r'%%tag::(\w+)::([a-f0-9-]+)::"([^"]+)"::([a-f0-9-]*)%%')
        tag_counts = Counter()
        total_tags = 0
        
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                matches = tag_pattern.findall(content)
                for match in matches:
                    tag_counts[match[0]] += 1
                    total_tags += 1
            except:
                pass
        
        top_types = ", ".join([f"{t}:{c}" for t, c in tag_counts.most_common(3)])
        self.stat_ready.emit("tags", str(total_tags), top_types or "No tags found", "#f9ca24")
        
        # === STAT 4: Axioms ===
        axiom_count = tag_counts.get('Axiom', 0)
        self.stat_ready.emit("axioms", str(axiom_count), "Foundational axioms", "#e056fd")
        
        # === STAT 5: Theorems ===
        theorem_count = tag_counts.get('Theorem', 0)
        self.stat_ready.emit("theorems", str(theorem_count), "Derived theorems", "#686de0")
        
        # === STAT 6: Equations ===
        self.progress.emit("Counting equations...")
        equation_pattern = re.compile(r'\$\$.*?\$\$|\$[^$]+\$', re.DOTALL)
        total_equations = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                total_equations += len(equation_pattern.findall(content))
            except:
                pass
        self.stat_ready.emit("equations", str(total_equations), "LaTeX equations", "#ff7979")
        
        # === STAT 7: Internal Links ===
        self.progress.emit("Counting links...")
        link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        total_links = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                total_links += len(link_pattern.findall(content))
            except:
                pass
        self.stat_ready.emit("links", str(total_links), "[[Internal links]]", "#7ed6df")
        
        # === STAT 8: UUIDs ===
        self.progress.emit("Checking UUIDs...")
        uuid_pattern = re.compile(r'uuid:\s*([a-f0-9-]{36})', re.IGNORECASE)
        papers_with_uuid = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                if uuid_pattern.search(content):
                    papers_with_uuid += 1
            except:
                pass
        
        pct = int((papers_with_uuid / paper_count * 100)) if paper_count else 0
        color = "#2ecc71" if pct >= 90 else "#f39c12" if pct >= 50 else "#e74c3c"
        self.stat_ready.emit("uuids", f"{pct}%", f"{papers_with_uuid}/{paper_count} have UUIDs", color)
        
        # === STAT 9: YAML Frontmatter ===
        self.progress.emit("Checking frontmatter...")
        papers_with_yaml = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                if content.strip().startswith('---'):
                    papers_with_yaml += 1
            except:
                pass
        
        pct = int((papers_with_yaml / paper_count * 100)) if paper_count else 0
        color = "#2ecc71" if pct >= 90 else "#f39c12" if pct >= 50 else "#e74c3c"
        self.stat_ready.emit("yaml", f"{pct}%", f"{papers_with_yaml}/{paper_count} have YAML", color)
        
        # === STAT 10: Recently Modified ===
        self.progress.emit("Checking file ages...")
        now = datetime.now()
        recent_24h = 0
        recent_7d = 0
        for f in md_files:
            try:
                mtime = datetime.fromtimestamp(f.stat().st_mtime)
                if now - mtime < timedelta(hours=24):
                    recent_24h += 1
                if now - mtime < timedelta(days=7):
                    recent_7d += 1
            except:
                pass
        self.stat_ready.emit("recent", str(recent_7d), f"{recent_24h} in last 24h", "#1abc9c")
        
        # === STAT 11: Evidence Bundles ===
        eb_pattern = re.compile(r'%%tag::EvidenceBundle', re.IGNORECASE)
        eb_count = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                eb_count += len(eb_pattern.findall(content))
            except:
                pass
        self.stat_ready.emit("evidence", str(eb_count), "Evidence bundles", "#e17055")
        
        # === STAT 12: Bible References ===
        self.progress.emit("Finding Bible refs...")
        bible_pattern = re.compile(r'\b(Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|Proverbs|Ecclesiastes|Song|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|Titus|Philemon|Hebrews|James|Peter|Jude|Revelation)\s+\d+[:\d]*', re.IGNORECASE)
        bible_refs = 0
        for f in md_files:
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
                bible_refs += len(bible_pattern.findall(content))
            except:
                pass
        self.stat_ready.emit("bible", str(bible_refs), "Scripture references", "#fdcb6e")
        
        self.finished.emit()


class StatsHubTab(QWidget):
    """Stats Hub - Grid of quick stat widgets."""
    
    def __init__(self, settings_mgr):
        super().__init__()
        self.settings_mgr = settings_mgr
        self.worker = None
        self.cards: Dict[str, StatCard] = {}
        self._current_stats: Dict[str, Dict[str, str]] = {}
        self._current_scan_path: str = ""
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_row = QHBoxLayout()
        
        header = QLabel("📊 Stats Hub")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #00d9ff;")
        header_row.addWidget(header)
        
        header_row.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Refresh All")
        self.refresh_btn.clicked.connect(self._refresh_stats)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d4a6f;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d5a7f;
            }
        """)
        header_row.addWidget(self.refresh_btn)

        self.copy_btn = QPushButton("📋 Copy All Stats")
        self.copy_btn.clicked.connect(self._copy_all_stats)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #345b3a;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d6b45;
            }
        """)
        header_row.addWidget(self.copy_btn)
        
        layout.addLayout(header_row)
        
        # Status
        self.status_label = QLabel("Click Refresh to load stats")
        self.status_label.setStyleSheet("color: #667788; font-size: 11px;")
        layout.addWidget(self.status_label)
        
        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        container = QWidget()
        self.grid = QGridLayout(container)
        self.grid.setSpacing(16)
        
        # Create stat cards
        card_defs = [
            ("papers", "📄 Papers", 0, 0),
            ("words", "📝 Words", 0, 1),
            ("tags", "🏷️ Semantic Tags", 0, 2),
            ("axioms", "⚛️ Axioms", 0, 3),
            ("theorems", "📐 Theorems", 1, 0),
            ("equations", "🔢 Equations", 1, 1),
            ("links", "🔗 Internal Links", 1, 2),
            ("uuids", "🆔 UUID Coverage", 1, 3),
            ("yaml", "📋 YAML Coverage", 2, 0),
            ("recent", "📅 Active (7d)", 2, 1),
            ("evidence", "📦 Evidence", 2, 2),
            ("bible", "✝️ Bible Refs", 2, 3),
        ]
        
        for card_id, title, row, col in card_defs:
            card = StatCard(title)
            self.cards[card_id] = card
            self.grid.addWidget(card, row, col)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        self._load_cached_stats()

    def _cache_path(self) -> Path:
        root = Path(__file__).resolve().parents[2]
        return root / "config" / "ui_cache" / "stats_hub.json"

    def _save_cached_stats(self):
        if not self._current_stats:
            return
        try:
            cache_path = self._cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "scan_path": self._current_scan_path,
                "stats": self._current_stats,
            }
            cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_cached_stats(self):
        cache_path = self._cache_path()
        if not cache_path.exists():
            return
        try:
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
            stats = payload.get("stats", {})
            if not isinstance(stats, dict):
                return

            for card_id, stat in stats.items():
                if card_id in self.cards and isinstance(stat, dict):
                    self.cards[card_id].set_value(
                        stat.get("value", "--"),
                        stat.get("subtitle", ""),
                        stat.get("color", "#00d9ff"),
                    )

            generated_at = payload.get("generated_at", "")
            if generated_at:
                pretty = generated_at.replace("T", " ")
                self.status_label.setText(f"Loaded cached stats ({pretty})")
                self.status_label.setStyleSheet("color: #8899aa;")
            self._current_stats = stats
            self._current_scan_path = payload.get("scan_path", "")
        except Exception:
            pass
    
    def _refresh_stats(self):
        # Get papers folder - try multiple sources
        papers_folder = ""
        
        # Try settings
        if hasattr(self.settings_mgr, 'get'):
            papers_folder = self.settings_mgr.get('folders', 'logos_papers', '')
        
        # Fallback to default
        if not papers_folder:
            default = r"O:\Theophysics_Master\TM SUBSTACK\03_PUBLICATIONS\Logos Papers Axiom"
            if Path(default).exists():
                papers_folder = default
        
        if not papers_folder:
            # Try vault root
            if hasattr(self.settings_mgr, 'get'):
                papers_folder = self.settings_mgr.get('obsidian', 'vault_path', '')
        
        if not papers_folder or not Path(papers_folder).exists():
            self.status_label.setText("⚠️ No valid papers folder found. Check Settings.")
            self.status_label.setStyleSheet("color: #e74c3c;")
            return
        
        # Set all cards to loading
        for card in self.cards.values():
            card.set_loading()
        
        self._current_scan_path = str(papers_folder)
        self._current_stats = {}
        self.refresh_btn.setEnabled(False)
        self.status_label.setText(f"Scanning {papers_folder}...")
        self.status_label.setStyleSheet("color: #00d9ff;")
        
        # Start worker
        self.worker = StatsWorker(papers_folder)
        self.worker.progress.connect(self._on_progress)
        self.worker.stat_ready.connect(self._on_stat_ready)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()
    
    def _on_progress(self, msg: str):
        self.status_label.setText(msg)
    
    def _on_stat_ready(self, card_id: str, value: str, subtitle: str, color: str):
        if card_id in self.cards:
            self.cards[card_id].set_value(value, subtitle, color)
            self._current_stats[card_id] = {
                "value": str(value),
                "subtitle": str(subtitle),
                "color": str(color),
            }
    
    def _on_finished(self):
        self.refresh_btn.setEnabled(True)
        now = datetime.now()
        self.status_label.setText(f"✅ Stats refreshed at {now.strftime('%H:%M:%S')}")
        self.status_label.setStyleSheet("color: #2ecc71;")
        self._save_cached_stats()

    def _build_stats_export_text(self) -> str:
        lines: List[str] = []
        lines.append("Stats Hub Export")
        lines.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
        lines.append(f"Scan Path: {self._current_scan_path}")
        lines.append(f"Status: {self.status_label.text()}")
        lines.append("")
        lines.append("Metrics:")

        if self._current_stats:
            for card_id in sorted(self._current_stats.keys()):
                stat = self._current_stats.get(card_id, {})
                value = str(stat.get("value", "--"))
                subtitle = str(stat.get("subtitle", ""))
                lines.append(f"- {card_id}: {value} ({subtitle})")
        else:
            for card_id, card in sorted(self.cards.items()):
                value = card.value_label.text()
                subtitle = card.subtitle_label.text()
                lines.append(f"- {card_id}: {value} ({subtitle})")

        return "\n".join(lines)

    def _copy_all_stats(self):
        text = self._build_stats_export_text()
        QApplication.clipboard().setText(text)
        self.status_label.setText("Copied all Stats Hub metrics to clipboard.")
        self.status_label.setStyleSheet("color: #2ecc71;")
