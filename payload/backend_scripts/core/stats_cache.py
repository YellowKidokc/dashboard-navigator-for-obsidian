"""
Stats Cache - Persistent caching for vault statistics

Stores computed statistics in SQLite so they're available immediately
on app startup without needing to rescan the vault.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class VaultStats:
    """Cached vault statistics."""
    total_notes: int = 0
    total_definitions: int = 0
    total_papers: int = 0
    total_tags: int = 0
    total_words: int = 0
    total_links: int = 0
    incomplete_definitions: int = 0
    missing_definitions: int = 0
    papers_by_status: Dict[str, int] = None
    tags_by_type: Dict[str, int] = None
    last_updated: str = ""
    
    def __post_init__(self):
        if self.papers_by_status is None:
            self.papers_by_status = {}
        if self.tags_by_type is None:
            self.tags_by_type = {}
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


class StatsCache:
    """
    SQLite-backed cache for vault statistics.
    
    Stores:
    - Vault-wide statistics (note count, word count, etc.)
    - Definition health metrics
    - Paper status breakdown
    - Tag usage stats
    - Any other computed values that are expensive to calculate
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.db_path = self.vault_path / "theophysics_cache.db"
        self._ensure_schema()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _ensure_schema(self):
        """Create cache tables if they don't exist."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Key-value cache for simple values
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cache_kv (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Structured stats cache
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cache_stats (
            stat_type TEXT PRIMARY KEY,
            data TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Scan results cache (for expensive operations)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cache_scans (
            scan_type TEXT PRIMARY KEY,
            results TEXT,
            item_count INTEGER,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
    
    # ==========================================
    # VAULT STATS
    # ==========================================
    
    def save_vault_stats(self, stats: VaultStats):
        """Save vault statistics to cache."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        stats.last_updated = datetime.now().isoformat()
        data = json.dumps(asdict(stats))
        
        cur.execute("""
        INSERT OR REPLACE INTO cache_stats (stat_type, data, updated_at)
        VALUES ('vault_stats', ?, CURRENT_TIMESTAMP)
        """, (data,))
        
        conn.commit()
        conn.close()
    
    def get_vault_stats(self) -> Optional[VaultStats]:
        """Get cached vault statistics."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT data FROM cache_stats WHERE stat_type = 'vault_stats'")
        row = cur.fetchone()
        conn.close()
        
        if row:
            data = json.loads(row['data'])
            return VaultStats(**data)
        return None
    
    # ==========================================
    # KEY-VALUE CACHE
    # ==========================================
    
    def set(self, key: str, value: Any):
        """Set a cached value."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT OR REPLACE INTO cache_kv (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, json.dumps(value)))
        
        conn.commit()
        conn.close()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a cached value."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT value FROM cache_kv WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['value'])
        return default
    
    def get_with_age(self, key: str) -> tuple:
        """Get a cached value with its age in seconds."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT value, updated_at FROM cache_kv WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            value = json.loads(row['value'])
            updated = datetime.fromisoformat(row['updated_at'])
            age = (datetime.now() - updated).total_seconds()
            return value, age
        return None, None
    
    # ==========================================
    # SCAN RESULTS CACHE
    # ==========================================
    
    def save_scan_results(self, scan_type: str, results: list):
        """Cache results from an expensive scan operation."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("""
        INSERT OR REPLACE INTO cache_scans (scan_type, results, item_count, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (scan_type, json.dumps(results), len(results)))
        
        conn.commit()
        conn.close()
    
    def get_scan_results(self, scan_type: str) -> Optional[list]:
        """Get cached scan results."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT results FROM cache_scans WHERE scan_type = ?", (scan_type,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return json.loads(row['results'])
        return None
    
    def get_scan_age(self, scan_type: str) -> Optional[float]:
        """Get age of cached scan in seconds."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT updated_at FROM cache_scans WHERE scan_type = ?", (scan_type,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            updated = datetime.fromisoformat(row['updated_at'])
            return (datetime.now() - updated).total_seconds()
        return None
    
    # ==========================================
    # CONVENIENCE METHODS
    # ==========================================
    
    def cache_definition_health(self, incomplete: list, missing: list):
        """Cache definition health scan results."""
        self.save_scan_results('incomplete_definitions', incomplete)
        self.save_scan_results('missing_definitions', missing)
        self.set('incomplete_count', len(incomplete))
        self.set('missing_count', len(missing))
    
    def get_definition_health(self) -> Dict[str, Any]:
        """Get cached definition health data."""
        return {
            'incomplete': self.get_scan_results('incomplete_definitions') or [],
            'missing': self.get_scan_results('missing_definitions') or [],
            'incomplete_count': self.get('incomplete_count', 0),
            'missing_count': self.get('missing_count', 0),
            'age': self.get_scan_age('incomplete_definitions')
        }
    
    def cache_tag_stats(self, stats: Dict[str, Any]):
        """Cache tag statistics."""
        self.set('tag_stats', stats)
    
    def get_tag_stats(self) -> Dict[str, Any]:
        """Get cached tag statistics."""
        return self.get('tag_stats', {})
    
    def cache_paper_stats(self, stats: Dict[str, Any]):
        """Cache paper statistics."""
        self.set('paper_stats', stats)
    
    def get_paper_stats(self) -> Dict[str, Any]:
        """Get cached paper statistics."""
        return self.get('paper_stats', {})
    
    def clear_all(self):
        """Clear all cached data."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM cache_kv")
        cur.execute("DELETE FROM cache_stats")
        cur.execute("DELETE FROM cache_scans")
        conn.commit()
        conn.close()
    
    def get_cache_summary(self) -> Dict[str, Any]:
        """Get summary of what's cached and when."""
        conn = self._get_conn()
        cur = conn.cursor()
        
        summary = {'items': []}
        
        # Stats
        cur.execute("SELECT stat_type, updated_at FROM cache_stats")
        for row in cur.fetchall():
            summary['items'].append({
                'type': 'stats',
                'key': row['stat_type'],
                'updated': row['updated_at']
            })
        
        # Scans
        cur.execute("SELECT scan_type, item_count, updated_at FROM cache_scans")
        for row in cur.fetchall():
            summary['items'].append({
                'type': 'scan',
                'key': row['scan_type'],
                'count': row['item_count'],
                'updated': row['updated_at']
            })
        
        # KV count
        cur.execute("SELECT COUNT(*) as cnt FROM cache_kv")
        summary['kv_count'] = cur.fetchone()['cnt']
        
        conn.close()
        return summary
