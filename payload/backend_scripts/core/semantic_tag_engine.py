"""
Semantic Tag Engine - Reader-Facing Tag System with Database Sync

Phase 2: Tags with UUID tracking, SQLite storage, and PostgreSQL sync.

Tag Axes:
1. Epistemic Mode - How strong is the claim?
2. Function - What role does this note play?
3. Domain - Which language/lens is being used?
4. Path - Where does this sit in the reader's journey?
"""

import sqlite3
import uuid
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime


def generate_uuid() -> str:
    return str(uuid.uuid4())


# =============================================================================
# TAG TAXONOMY - The 4 Axes
# =============================================================================

TAG_TAXONOMY = {
    "epistemic": {
        "description": "How strong is this claim?",
        "required": True,
        "max_per_note": 1,
        "values": {
            "established": "Accepted science/scholarship",
            "inferential": "Logical derivation from established premises",
            "speculative": "Hypothesis, conjecture, exploration",
            "metaphorical": "Analogy, illustration, not literal claim",
        }
    },
    "function": {
        "description": "What role does this note play?",
        "required": False,
        "max_per_note": 2,
        "values": {
            "definition": "Defines a term or concept",
            "bridge": "Connects two domains or ideas",
            "constraint": "Sets boundaries, limits, conditions",
            "synthesis": "Integrates multiple threads",
            "example": "Illustrates with concrete case",
            "objection": "Raises a counterargument",
            "response": "Answers an objection",
            "derivation": "Step-by-step logical/mathematical work",
        }
    },
    "domain": {
        "description": "Which language/lens is being used?",
        "required": False,
        "max_per_note": None,  # Multiple allowed
        "values": {
            "physics": "Physical sciences",
            "information": "Information theory",
            "philosophy": "Philosophical analysis",
            "theology": "Theological perspective",
            "cognition": "Cognitive science",
            "mathematics": "Mathematical formalism",
            "history": "Historical context",
        }
    },
    "path": {
        "description": "Where does this sit in the reader's journey?",
        "required": False,
        "max_per_note": 1,
        "values": {
            "entry": "Start here, overview, accessible",
            "core": "Central argument, essential reading",
            "deep": "Advanced, assumes prior context",
            "appendix": "Reference, supplementary, technical",
        }
    }
}


@dataclass
class SemanticTag:
    """A semantic tag with UUID tracking."""
    uuid: str
    axis: str           # epistemic, function, domain, path
    value: str          # established, bridge, physics, etc.
    note_path: str      # Path to the note this tag is on
    note_uuid: str      # UUID of the note
    created_at: int
    updated_at: int
    
    @property
    def full_tag(self) -> str:
        """Return the full tag string like #epistemic/established"""
        return f"#{self.axis}/{self.value}"


class SemanticTagEngine:
    """
    Engine for managing reader-facing semantic tags with database persistence.
    """
    
    def __init__(self, vault_path: str, db_path: Optional[str] = None):
        self.vault_path = Path(vault_path)
        self.db_path = Path(db_path) if db_path else self.vault_path / "semantic_tags.db"
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Create database schema for semantic tags."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Main semantic tags table
        c.execute("""
        CREATE TABLE IF NOT EXISTS semantic_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            axis TEXT NOT NULL,
            value TEXT NOT NULL,
            note_path TEXT NOT NULL,
            note_uuid TEXT,
            created_at INTEGER,
            updated_at INTEGER,
            UNIQUE(axis, value, note_path)
        )
        """)
        
        # Notes table for tracking which notes have been tagged
        c.execute("""
        CREATE TABLE IF NOT EXISTS tagged_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            path TEXT UNIQUE NOT NULL,
            title TEXT,
            epistemic_tag TEXT,
            function_tags TEXT,
            domain_tags TEXT,
            path_tag TEXT,
            is_complete INTEGER DEFAULT 0,
            created_at INTEGER,
            updated_at INTEGER
        )
        """)
        
        # Tag usage statistics
        c.execute("""
        CREATE TABLE IF NOT EXISTS tag_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            axis TEXT NOT NULL,
            value TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            last_used_at INTEGER,
            UNIQUE(axis, value)
        )
        """)
        
        # Sync status for PostgreSQL
        c.execute("""
        CREATE TABLE IF NOT EXISTS tag_sync_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            table_name TEXT UNIQUE,
            last_sync_at INTEGER,
            records_synced INTEGER,
            status TEXT
        )
        """)
        
        # Indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_tags_axis ON semantic_tags(axis)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tags_value ON semantic_tags(value)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tags_note ON semantic_tags(note_path)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notes_path ON tagged_notes(path)")
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # TAG OPERATIONS
    # =========================================================================
    
    def add_tag(self, note_path: str, axis: str, value: str, note_uuid: Optional[str] = None) -> str:
        """Add a semantic tag to a note. Returns the tag UUID."""
        # Validate axis and value
        if axis not in TAG_TAXONOMY:
            raise ValueError(f"Invalid axis: {axis}. Must be one of {list(TAG_TAXONOMY.keys())}")
        
        if value not in TAG_TAXONOMY[axis]["values"]:
            raise ValueError(f"Invalid value '{value}' for axis '{axis}'. Must be one of {list(TAG_TAXONOMY[axis]['values'].keys())}")
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if tag already exists
        c.execute("SELECT uuid FROM semantic_tags WHERE axis = ? AND value = ? AND note_path = ?",
                  (axis, value, note_path))
        existing = c.fetchone()
        
        if existing:
            tag_uuid = existing[0]
            c.execute("UPDATE semantic_tags SET updated_at = ? WHERE uuid = ?", (now, tag_uuid))
        else:
            tag_uuid = generate_uuid()
            c.execute("""
            INSERT INTO semantic_tags (uuid, axis, value, note_path, note_uuid, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (tag_uuid, axis, value, note_path, note_uuid or generate_uuid(), now, now))
        
        # Update tag stats
        c.execute("""
        INSERT INTO tag_stats (uuid, axis, value, usage_count, last_used_at)
        VALUES (?, ?, ?, 1, ?)
        ON CONFLICT(axis, value) DO UPDATE SET
            usage_count = usage_count + 1,
            last_used_at = ?
        """, (generate_uuid(), axis, value, now, now))
        
        conn.commit()
        conn.close()
        
        return tag_uuid
    
    def remove_tag(self, note_path: str, axis: str, value: str) -> bool:
        """Remove a semantic tag from a note."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM semantic_tags WHERE axis = ? AND value = ? AND note_path = ?",
                  (axis, value, note_path))
        deleted = c.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
    
    def get_note_tags(self, note_path: str) -> Dict[str, List[str]]:
        """Get all semantic tags for a note, organized by axis."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT axis, value FROM semantic_tags WHERE note_path = ?", (note_path,))
        rows = c.fetchall()
        conn.close()
        
        result = {axis: [] for axis in TAG_TAXONOMY.keys()}
        for axis, value in rows:
            result[axis].append(value)
        return result
    
    def get_notes_by_tag(self, axis: str, value: str) -> List[str]:
        """Get all note paths that have a specific tag."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT note_path FROM semantic_tags WHERE axis = ? AND value = ?", (axis, value))
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    def get_tag_stats(self) -> Dict[str, Dict[str, int]]:
        """Get usage statistics for all tags."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT axis, value, usage_count FROM tag_stats ORDER BY axis, usage_count DESC")
        rows = c.fetchall()
        conn.close()
        
        result = {axis: {} for axis in TAG_TAXONOMY.keys()}
        for axis, value, count in rows:
            result[axis][value] = count
        return result
    
    # =========================================================================
    # NOTE TAGGING
    # =========================================================================
    
    def tag_note(self, note_path: str, tags: Dict[str, List[str]], note_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        Tag a note with semantic tags.
        
        Args:
            note_path: Path to the note
            tags: Dict like {"epistemic": ["established"], "domain": ["physics", "theology"]}
            note_uuid: Optional UUID for the note
        
        Returns:
            Dict with status and any validation warnings
        """
        warnings = []
        added_tags = []
        
        # Validate tag constraints
        for axis, values in tags.items():
            if axis not in TAG_TAXONOMY:
                warnings.append(f"Unknown axis: {axis}")
                continue
            
            max_allowed = TAG_TAXONOMY[axis]["max_per_note"]
            if max_allowed and len(values) > max_allowed:
                warnings.append(f"Too many {axis} tags: {len(values)} (max {max_allowed})")
                values = values[:max_allowed]
            
            for value in values:
                try:
                    tag_uuid = self.add_tag(note_path, axis, value, note_uuid)
                    added_tags.append(f"#{axis}/{value}")
                except ValueError as e:
                    warnings.append(str(e))
        
        # Check if epistemic tag is present (required)
        if "epistemic" not in tags or not tags["epistemic"]:
            warnings.append("Missing required epistemic tag")
        
        # Update tagged_notes table
        self._update_tagged_note(note_path, tags, note_uuid)
        
        return {
            "success": len(added_tags) > 0,
            "tags_added": added_tags,
            "warnings": warnings
        }
    
    def _update_tagged_note(self, note_path: str, tags: Dict[str, List[str]], note_uuid: Optional[str] = None):
        """Update the tagged_notes tracking table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Extract title from path
        title = Path(note_path).stem
        
        # Check completeness
        is_complete = 1 if tags.get("epistemic") else 0
        
        c.execute("""
        INSERT INTO tagged_notes (uuid, path, title, epistemic_tag, function_tags, domain_tags, path_tag, is_complete, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            title = excluded.title,
            epistemic_tag = excluded.epistemic_tag,
            function_tags = excluded.function_tags,
            domain_tags = excluded.domain_tags,
            path_tag = excluded.path_tag,
            is_complete = excluded.is_complete,
            updated_at = excluded.updated_at
        """, (
            note_uuid or generate_uuid(),
            note_path,
            title,
            tags.get("epistemic", [None])[0] if tags.get("epistemic") else None,
            json.dumps(tags.get("function", [])),
            json.dumps(tags.get("domain", [])),
            tags.get("path", [None])[0] if tags.get("path") else None,
            is_complete,
            now,
            now
        ))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # VAULT SCANNING
    # =========================================================================
    
    def scan_vault_for_tags(self) -> Dict[str, Any]:
        """Scan vault for existing semantic tags in frontmatter."""
        stats = {
            "files_scanned": 0,
            "files_with_tags": 0,
            "tags_found": {axis: {} for axis in TAG_TAXONOMY.keys()},
            "incomplete_notes": [],
        }
        
        for md_file in self.vault_path.rglob("*.md"):
            # Skip system folders
            if any(skip in str(md_file) for skip in [".obsidian", "_TAG_NOTES", "node_modules"]):
                continue
            
            stats["files_scanned"] += 1
            
            try:
                content = md_file.read_text(encoding='utf-8')
                tags = self._extract_semantic_tags(content)
                
                if any(tags.values()):
                    stats["files_with_tags"] += 1
                    rel_path = str(md_file.relative_to(self.vault_path))
                    
                    # Store in database
                    self.tag_note(rel_path, tags)
                    
                    # Update stats
                    for axis, values in tags.items():
                        for value in values:
                            stats["tags_found"][axis][value] = stats["tags_found"][axis].get(value, 0) + 1
                    
                    # Check completeness
                    if not tags.get("epistemic"):
                        stats["incomplete_notes"].append(rel_path)
                        
            except Exception as e:
                pass  # Skip files that can't be read
        
        return stats
    
    def _extract_semantic_tags(self, content: str) -> Dict[str, List[str]]:
        """Extract semantic tags from note content."""
        tags = {axis: [] for axis in TAG_TAXONOMY.keys()}
        
        # Look for tags in frontmatter
        fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if fm_match:
            frontmatter = fm_match.group(1)
            
            # Look for tags array
            tags_match = re.search(r'tags:\s*\[([^\]]+)\]', frontmatter)
            if tags_match:
                tag_list = [t.strip().strip('"\'') for t in tags_match.group(1).split(',')]
                for tag in tag_list:
                    self._parse_semantic_tag(tag, tags)
            
            # Look for tags list format
            tags_list_match = re.search(r'tags:\s*\n((?:\s*-\s*.+\n?)+)', frontmatter)
            if tags_list_match:
                for line in tags_list_match.group(1).split('\n'):
                    tag = line.strip().lstrip('-').strip().strip('"\'')
                    if tag:
                        self._parse_semantic_tag(tag, tags)
        
        # Also look for inline tags
        inline_tags = re.findall(r'#(epistemic|function|domain|path)/(\w+)', content)
        for axis, value in inline_tags:
            if value not in tags[axis]:
                tags[axis].append(value)
        
        return tags
    
    def _parse_semantic_tag(self, tag: str, tags: Dict[str, List[str]]):
        """Parse a single tag string and add to tags dict."""
        tag = tag.lstrip('#')
        
        for axis in TAG_TAXONOMY.keys():
            if tag.startswith(f"{axis}/"):
                value = tag.split('/')[1]
                if value in TAG_TAXONOMY[axis]["values"] and value not in tags[axis]:
                    tags[axis].append(value)
                return
    
    # =========================================================================
    # POSTGRESQL SYNC
    # =========================================================================
    
    def export_to_postgres(self, conn_str: str) -> tuple[bool, str]:
        """Export semantic tags to PostgreSQL."""
        try:
            import psycopg2
        except ImportError:
            return False, "psycopg2 not installed"
        
        try:
            pg_conn = psycopg2.connect(conn_str)
            pg_cur = pg_conn.cursor()
            
            # Create tables in PostgreSQL
            pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS semantic_tags (
                id SERIAL PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                axis TEXT NOT NULL,
                value TEXT NOT NULL,
                note_path TEXT NOT NULL,
                note_uuid TEXT,
                created_at INTEGER,
                updated_at INTEGER,
                UNIQUE(axis, value, note_path)
            )
            """)
            
            pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS tagged_notes (
                id SERIAL PRIMARY KEY,
                uuid TEXT UNIQUE NOT NULL,
                path TEXT UNIQUE NOT NULL,
                title TEXT,
                epistemic_tag TEXT,
                function_tags JSONB,
                domain_tags JSONB,
                path_tag TEXT,
                is_complete INTEGER DEFAULT 0,
                created_at INTEGER,
                updated_at INTEGER
            )
            """)
            
            # Get all tags from SQLite
            sqlite_conn = sqlite3.connect(self.db_path)
            sqlite_cur = sqlite_conn.cursor()
            
            # Sync semantic_tags
            sqlite_cur.execute("SELECT uuid, axis, value, note_path, note_uuid, created_at, updated_at FROM semantic_tags")
            tags = sqlite_cur.fetchall()
            
            synced = 0
            for tag in tags:
                pg_cur.execute("""
                INSERT INTO semantic_tags (uuid, axis, value, note_path, note_uuid, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uuid) DO UPDATE SET
                    axis = EXCLUDED.axis,
                    value = EXCLUDED.value,
                    note_path = EXCLUDED.note_path,
                    note_uuid = EXCLUDED.note_uuid,
                    updated_at = EXCLUDED.updated_at
                """, tag)
                synced += 1
            
            # Sync tagged_notes
            sqlite_cur.execute("SELECT uuid, path, title, epistemic_tag, function_tags, domain_tags, path_tag, is_complete, created_at, updated_at FROM tagged_notes")
            notes = sqlite_cur.fetchall()
            
            for note in notes:
                pg_cur.execute("""
                INSERT INTO tagged_notes (uuid, path, title, epistemic_tag, function_tags, domain_tags, path_tag, is_complete, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (uuid) DO UPDATE SET
                    path = EXCLUDED.path,
                    title = EXCLUDED.title,
                    epistemic_tag = EXCLUDED.epistemic_tag,
                    function_tags = EXCLUDED.function_tags,
                    domain_tags = EXCLUDED.domain_tags,
                    path_tag = EXCLUDED.path_tag,
                    is_complete = EXCLUDED.is_complete,
                    updated_at = EXCLUDED.updated_at
                """, note)
            
            pg_conn.commit()
            pg_cur.close()
            pg_conn.close()
            sqlite_conn.close()
            
            # Update sync status
            self._update_sync_status("semantic_tags", synced)
            
            return True, f"Synced {synced} tags to PostgreSQL"
            
        except Exception as e:
            return False, str(e)
    
    def _update_sync_status(self, table_name: str, records: int):
        """Update sync status in SQLite."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        c.execute("""
        INSERT INTO tag_sync_status (uuid, table_name, last_sync_at, records_synced, status)
        VALUES (?, ?, ?, ?, 'success')
        ON CONFLICT(table_name) DO UPDATE SET
            last_sync_at = ?,
            records_synced = ?,
            status = 'success'
        """, (generate_uuid(), table_name, now, records, now, records))
        
        conn.commit()
        conn.close()
    
    # =========================================================================
    # REPORTS
    # =========================================================================
    
    def generate_taxonomy_report(self) -> str:
        """Generate a markdown report of the tag taxonomy and usage."""
        stats = self.get_tag_stats()
        
        report = """# Semantic Tag Taxonomy

> **Links tell the reader what something means.**
> **Tags tell the reader how to read it.**

---

"""
        for axis, config in TAG_TAXONOMY.items():
            report += f"## {axis.title()} Tags\n\n"
            report += f"*{config['description']}*\n\n"
            report += f"- **Required:** {'Yes' if config['required'] else 'No'}\n"
            report += f"- **Max per note:** {config['max_per_note'] or 'Unlimited'}\n\n"
            
            report += "| Tag | Description | Usage |\n"
            report += "|-----|-------------|-------|\n"
            
            for value, desc in config["values"].items():
                usage = stats.get(axis, {}).get(value, 0)
                report += f"| `#{axis}/{value}` | {desc} | {usage} |\n"
            
            report += "\n"
        
        return report
    
    def get_incomplete_notes(self) -> List[Dict[str, Any]]:
        """Get notes that are missing required tags."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT path, title, epistemic_tag, function_tags, domain_tags, path_tag
        FROM tagged_notes
        WHERE is_complete = 0
        ORDER BY path
        """)
        rows = c.fetchall()
        conn.close()
        
        return [{
            "path": r[0],
            "title": r[1],
            "epistemic": r[2],
            "function": json.loads(r[3]) if r[3] else [],
            "domain": json.loads(r[4]) if r[4] else [],
            "path": r[5],
        } for r in rows]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_taxonomy() -> Dict[str, Any]:
    """Get the full tag taxonomy."""
    return TAG_TAXONOMY


def validate_tags(tags: Dict[str, List[str]]) -> List[str]:
    """Validate a set of tags against the taxonomy. Returns list of errors."""
    errors = []
    
    for axis, values in tags.items():
        if axis not in TAG_TAXONOMY:
            errors.append(f"Unknown axis: {axis}")
            continue
        
        config = TAG_TAXONOMY[axis]
        
        # Check max per note
        if config["max_per_note"] and len(values) > config["max_per_note"]:
            errors.append(f"Too many {axis} tags: {len(values)} (max {config['max_per_note']})")
        
        # Check valid values
        for value in values:
            if value not in config["values"]:
                errors.append(f"Invalid {axis} value: {value}")
    
    # Check required axes
    for axis, config in TAG_TAXONOMY.items():
        if config["required"] and axis not in tags:
            errors.append(f"Missing required axis: {axis}")
    
    return errors
