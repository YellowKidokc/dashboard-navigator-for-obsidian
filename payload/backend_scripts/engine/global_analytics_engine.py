"""
Global Analytics Engine
Dense data extraction and aggregation system for Theophysics
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
from collections import Counter, defaultdict


class GlobalAnalyticsEngine:
    """Extract and aggregate dense data points from the entire Theophysics ecosystem."""
    
    def __init__(self, backend_root: Path, output_path: Path):
        self.backend_root = Path(backend_root)
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data storage
        self.db_path = self.output_path / "analytics.db"
        self._init_database()
        
        # Data collectors
        self.data_points = {
            'papers': [],
            'definitions': [],
            'tags': [],
            'links': [],
            'images': [],
            'equations': [],
            'citations': [],
            'concepts': [],
            'relationships': [],
            'temporal': [],
            'metrics': {}
        }
    
    def _init_database(self):
        """Initialize SQLite database for dense data storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Papers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                filename TEXT,
                title TEXT,
                word_count INTEGER,
                char_count INTEGER,
                line_count INTEGER,
                created_date TEXT,
                modified_date TEXT,
                has_frontmatter BOOLEAN,
                has_equations BOOLEAN,
                has_images BOOLEAN,
                has_citations BOOLEAN,
                category TEXT,
                status TEXT,
                author TEXT,
                tags_json TEXT,
                links_json TEXT,
                metadata_json TEXT
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT UNIQUE,
                count INTEGER,
                papers_json TEXT,
                first_seen TEXT,
                last_seen TEXT,
                category TEXT
            )
        """)
        
        # Links table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_paper TEXT,
                target TEXT,
                link_type TEXT,
                context TEXT,
                line_number INTEGER
            )
        """)
        
        # Definitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT,
                definition TEXT,
                source_paper TEXT,
                category TEXT,
                related_terms_json TEXT,
                usage_count INTEGER
            )
        """)
        
        # Equations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS equations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equation TEXT,
                paper TEXT,
                line_number INTEGER,
                context TEXT,
                has_translation BOOLEAN,
                translation TEXT
            )
        """)
        
        # Concepts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT UNIQUE,
                frequency INTEGER,
                papers_json TEXT,
                related_concepts_json TEXT,
                category TEXT
            )
        """)
        
        # Relationships table (concept co-occurrence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_a TEXT,
                concept_b TEXT,
                strength REAL,
                papers_json TEXT,
                relationship_type TEXT
            )
        """)
        
        # Temporal data (track changes over time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS temporal_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                metric_name TEXT,
                metric_value REAL,
                metadata_json TEXT
            )
        """)
        
        # Analytics snapshots
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                total_papers INTEGER,
                total_words INTEGER,
                total_tags INTEGER,
                total_links INTEGER,
                total_definitions INTEGER,
                total_equations INTEGER,
                total_concepts INTEGER,
                metrics_json TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def extract_all_data(self):
        """Extract all data points from the ecosystem."""
        print("🔍 Starting comprehensive data extraction...")
        
        # Extract from different sources
        self._extract_papers_data()
        self._extract_tags_data()
        self._extract_definitions_data()
        self._extract_links_data()
        self._extract_concepts_data()
        self._extract_relationships()
        self._calculate_metrics()
        
        # Create snapshot
        self._create_snapshot()
        
        print("✅ Data extraction complete!")
    
    def _extract_papers_data(self):
        """Extract dense data from all markdown papers."""
        print("📄 Extracting paper data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Search for markdown files
        search_paths = [
            self.backend_root / "Edge TTS" / "PROCESSED",
            self.backend_root / "TTS_Pipeline",
            self.backend_root / "00_VAULT_SYSTEM"
        ]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
            
            for md_file in search_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    
                    # Extract metadata
                    title = self._extract_title(content)
                    word_count = len(content.split())
                    char_count = len(content)
                    line_count = len(content.split('\n'))
                    
                    # Check for features
                    has_frontmatter = content.strip().startswith('---')
                    has_equations = bool(re.search(r'\$\$.*?\$\$|\$.*?\$', content))
                    has_images = bool(re.search(r'!\[.*?\]\(.*?\)|!\[\[.*?\]\]', content))
                    has_citations = bool(re.search(r'\[@.*?\]|\[\^.*?\]', content))
                    
                    # Extract tags
                    tags = self._extract_tags(content)
                    
                    # Extract links
                    links = self._extract_links(content)
                    
                    # File metadata
                    stat = md_file.stat()
                    created = datetime.fromtimestamp(stat.st_ctime).isoformat()
                    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
                    
                    # Insert into database
                    cursor.execute("""
                        INSERT OR REPLACE INTO papers 
                        (path, filename, title, word_count, char_count, line_count,
                         created_date, modified_date, has_frontmatter, has_equations,
                         has_images, has_citations, tags_json, links_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(md_file), md_file.name, title, word_count, char_count, line_count,
                        created, modified, has_frontmatter, has_equations, has_images,
                        has_citations, json.dumps(tags), json.dumps(links)
                    ))
                    
                    self.data_points['papers'].append({
                        'path': str(md_file),
                        'title': title,
                        'word_count': word_count,
                        'tags': tags,
                        'links': links
                    })
                
                except Exception as e:
                    print(f"Error processing {md_file}: {e}")
        
        conn.commit()
        conn.close()
        print(f"  ✓ Processed {len(self.data_points['papers'])} papers")
    
    def _extract_tags_data(self):
        """Extract and aggregate tag data."""
        print("🏷️  Extracting tag data...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Aggregate tags from papers
        tag_counter = Counter()
        tag_papers = defaultdict(list)
        
        cursor.execute("SELECT path, tags_json FROM papers WHERE tags_json IS NOT NULL")
        for path, tags_json in cursor.fetchall():
            tags = json.loads(tags_json)
            for tag in tags:
                tag_counter[tag] += 1
                tag_papers[tag].append(path)
        
        # Insert tag data
        for tag, count in tag_counter.items():
            cursor.execute("""
                INSERT OR REPLACE INTO tags (tag, count, papers_json, last_seen)
                VALUES (?, ?, ?, ?)
            """, (tag, count, json.dumps(tag_papers[tag]), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        print(f"  ✓ Processed {len(tag_counter)} unique tags")
    
    def _extract_definitions_data(self):
        """Extract definition data."""
        print("📚 Extracting definitions...")
        
        # Look for definition patterns in papers
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT path FROM papers")
        for (path,) in cursor.fetchall():
            try:
                content = Path(path).read_text(encoding='utf-8')
                
                # Pattern: **Term**: Definition or ## Term followed by definition
                definitions = re.findall(r'\*\*([^*]+)\*\*:\s*([^\n]+)', content)
                
                for term, definition in definitions:
                    cursor.execute("""
                        INSERT INTO definitions (term, definition, source_paper)
                        VALUES (?, ?, ?)
                    """, (term.strip(), definition.strip(), path))
            
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
    
    def _extract_links_data(self):
        """Extract link data."""
        print("🔗 Extracting links...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT path, links_json FROM papers WHERE links_json IS NOT NULL")
        for path, links_json in cursor.fetchall():
            links = json.loads(links_json)
            for link in links:
                cursor.execute("""
                    INSERT INTO links (source_paper, target, link_type)
                    VALUES (?, ?, ?)
                """, (path, link, 'internal'))
        
        conn.commit()
        conn.close()
    
    def _extract_concepts_data(self):
        """Extract key concepts from papers."""
        print("💡 Extracting concepts...")
        
        # Key Theophysics concepts to track
        key_concepts = [
            'grace', 'trinity', 'resurrection', 'entropy', 'coherence',
            'axiom', 'theorem', 'consciousness', 'quantum', 'divine',
            'logos', 'pneuma', 'christology', 'eschatology', 'soteriology'
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        concept_counter = Counter()
        concept_papers = defaultdict(list)
        
        cursor.execute("SELECT path FROM papers")
        for (path,) in cursor.fetchall():
            try:
                content = Path(path).read_text(encoding='utf-8').lower()
                
                for concept in key_concepts:
                    count = content.count(concept.lower())
                    if count > 0:
                        concept_counter[concept] += count
                        concept_papers[concept].append(path)
            
            except Exception as e:
                continue
        
        # Insert concept data
        for concept, frequency in concept_counter.items():
            cursor.execute("""
                INSERT OR REPLACE INTO concepts (concept, frequency, papers_json)
                VALUES (?, ?, ?)
            """, (concept, frequency, json.dumps(concept_papers[concept])))
        
        conn.commit()
        conn.close()
        print(f"  ✓ Tracked {len(concept_counter)} concepts")
    
    def _extract_relationships(self):
        """Extract concept co-occurrence relationships."""
        print("🕸️  Extracting relationships...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all concepts
        cursor.execute("SELECT concept FROM concepts")
        concepts = [row[0] for row in cursor.fetchall()]
        
        # Calculate co-occurrence
        for i, concept_a in enumerate(concepts):
            for concept_b in concepts[i+1:]:
                # Find papers containing both
                cursor.execute("""
                    SELECT papers_json FROM concepts WHERE concept = ?
                """, (concept_a,))
                papers_a = set(json.loads(cursor.fetchone()[0]))
                
                cursor.execute("""
                    SELECT papers_json FROM concepts WHERE concept = ?
                """, (concept_b,))
                papers_b = set(json.loads(cursor.fetchone()[0]))
                
                common_papers = papers_a & papers_b
                if common_papers:
                    strength = len(common_papers) / max(len(papers_a), len(papers_b))
                    
                    cursor.execute("""
                        INSERT INTO relationships 
                        (concept_a, concept_b, strength, papers_json, relationship_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (concept_a, concept_b, strength, json.dumps(list(common_papers)), 'co-occurrence'))
        
        conn.commit()
        conn.close()
    
    def _calculate_metrics(self):
        """Calculate aggregate metrics."""
        print("📊 Calculating metrics...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics = {}
        
        # Paper metrics
        cursor.execute("SELECT COUNT(*), SUM(word_count), AVG(word_count) FROM papers")
        total_papers, total_words, avg_words = cursor.fetchone()
        metrics['total_papers'] = total_papers
        metrics['total_words'] = total_words or 0
        metrics['avg_words_per_paper'] = avg_words or 0
        
        # Tag metrics
        cursor.execute("SELECT COUNT(*), AVG(count) FROM tags")
        total_tags, avg_tag_usage = cursor.fetchone()
        metrics['total_tags'] = total_tags
        metrics['avg_tag_usage'] = avg_tag_usage or 0
        
        # Link metrics
        cursor.execute("SELECT COUNT(*) FROM links")
        metrics['total_links'] = cursor.fetchone()[0]
        
        # Concept metrics
        cursor.execute("SELECT COUNT(*), SUM(frequency) FROM concepts")
        total_concepts, total_concept_mentions = cursor.fetchone()
        metrics['total_concepts'] = total_concepts
        metrics['total_concept_mentions'] = total_concept_mentions or 0
        
        # Relationship metrics
        cursor.execute("SELECT COUNT(*), AVG(strength) FROM relationships")
        total_relationships, avg_strength = cursor.fetchone()
        metrics['total_relationships'] = total_relationships
        metrics['avg_relationship_strength'] = avg_strength or 0
        
        self.data_points['metrics'] = metrics
        
        conn.close()
        print(f"  ✓ Calculated {len(metrics)} metrics")
    
    def _create_snapshot(self):
        """Create a snapshot of current analytics state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metrics = self.data_points['metrics']
        
        cursor.execute("""
            INSERT INTO snapshots 
            (timestamp, total_papers, total_words, total_tags, total_links,
             total_concepts, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            metrics.get('total_papers', 0),
            metrics.get('total_words', 0),
            metrics.get('total_tags', 0),
            metrics.get('total_links', 0),
            metrics.get('total_concepts', 0),
            json.dumps(metrics)
        ))
        
        conn.commit()
        conn.close()
    
    def export_dense_data(self):
        """Export all data to JSON files for analysis."""
        print("💾 Exporting dense data...")
        
        # Export to JSON
        data_export = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.data_points['metrics'],
            'papers': self.data_points['papers']
        }
        
        export_file = self.output_path / f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_file.write_text(json.dumps(data_export, indent=2), encoding='utf-8')
        
        print(f"  ✓ Exported to {export_file}")
    
    def _extract_title(self, content: str) -> str:
        """Extract title from content."""
        # Try frontmatter first
        if content.strip().startswith('---'):
            match = re.search(r'title:\s*(.+)', content)
            if match:
                return match.group(1).strip()
        
        # Try first heading
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        return "Untitled"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content."""
        tags = []
        
        # Frontmatter tags
        if content.strip().startswith('---'):
            match = re.search(r'tags:\s*\[(.*?)\]', content, re.DOTALL)
            if match:
                tags.extend([t.strip().strip('"\'') for t in match.group(1).split(',')])
        
        # Inline tags
        tags.extend(re.findall(r'#(\w+)', content))
        
        return list(set(tags))
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract internal links from content."""
        # Wiki-style links
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        
        # Markdown links to .md files
        md_links = re.findall(r'\[([^\]]+)\]\(([^\)]+\.md)\)', content)
        
        return wiki_links + [link[1] for link in md_links]
