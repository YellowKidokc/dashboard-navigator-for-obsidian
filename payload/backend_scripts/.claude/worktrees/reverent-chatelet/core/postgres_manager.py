"""
PostgreSQL Manager - Stores definitions, footnotes, research links, and memories.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
from dataclasses import dataclass, asdict
import json
from datetime import datetime


@dataclass
class DatabaseConfig:
    """PostgreSQL connection configuration."""
    host: str = "192.168.1.177"
    port: int = 2665
    database: str = "Theophysics"
    user: str = "Yellowkid"
    password: str = "Moss9pep28$"


class PostgresManager:
    """Manages PostgreSQL database for Theophysics Research Manager."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """Initialize PostgreSQL manager."""
        self.config = config or DatabaseConfig()
        self.conn = None
        self._ensure_schema()
    
    def connect(self) -> bool:
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            return True
        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _ensure_schema(self) -> None:
        """Create database schema if it doesn't exist."""
        if not self.connect():
            return
        
        try:
            with self.conn.cursor() as cur:
                # Definitions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS definitions (
                        id SERIAL PRIMARY KEY,
                        phrase TEXT NOT NULL UNIQUE,
                        aliases JSONB DEFAULT '[]',
                        definition TEXT NOT NULL,
                        classification TEXT,
                        folder TEXT,
                        vault_link TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Footnotes table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS footnotes (
                        id SERIAL PRIMARY KEY,
                        marker INTEGER NOT NULL,
                        term TEXT NOT NULL,
                        vault_link TEXT,
                        academic_links JSONB DEFAULT '{}',
                        explanation TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Research links table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS research_links (
                        id SERIAL PRIMARY KEY,
                        term TEXT NOT NULL,
                        source TEXT NOT NULL,
                        url TEXT NOT NULL,
                        priority INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(term, source)
                    )
                """)
                
                # Memories table (for AI context)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id SERIAL PRIMARY KEY,
                        category TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cur.execute("CREATE INDEX IF NOT EXISTS idx_definitions_phrase ON definitions(phrase)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_footnotes_term ON footnotes(term)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_research_links_term ON research_links(term)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)")
                
                self.conn.commit()
        except Exception as e:
            print(f"Schema creation error: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            self.disconnect()
    
    # Definitions methods
    def save_definition(
        self,
        phrase: str,
        definition: str,
        aliases: List[str] = None,
        classification: str = "",
        folder: str = "",
        vault_link: str = ""
    ) -> bool:
        """Save a definition to the database."""
        if not self.connect():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO definitions (phrase, aliases, definition, classification, folder, vault_link)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (phrase) 
                    DO UPDATE SET
                        aliases = EXCLUDED.aliases,
                        definition = EXCLUDED.definition,
                        classification = EXCLUDED.classification,
                        folder = EXCLUDED.folder,
                        vault_link = EXCLUDED.vault_link,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    phrase,
                    json.dumps(aliases or []),
                    definition,
                    classification or None,
                    folder or None,
                    vault_link or None
                ))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error saving definition: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def get_all_definitions(self) -> List[Dict[str, Any]]:
        """Get all definitions from database."""
        if not self.connect():
            return []
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM definitions ORDER BY phrase")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching definitions: {e}")
            return []
        finally:
            self.disconnect()
    
    # Footnotes methods
    def save_footnote(
        self,
        marker: int,
        term: str,
        vault_link: str = "",
        academic_links: Dict[str, str] = None,
        explanation: str = ""
    ) -> bool:
        """Save a footnote to the database."""
        if not self.connect():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO footnotes (marker, term, vault_link, academic_links, explanation)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    marker,
                    term,
                    vault_link or None,
                    json.dumps(academic_links or {}),
                    explanation or None
                ))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error saving footnote: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    # Research links methods
    def save_research_link(
        self,
        term: str,
        source: str,
        url: str,
        priority: int = 0
    ) -> bool:
        """Save a research link to the database."""
        if not self.connect():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO research_links (term, source, url, priority)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (term, source)
                    DO UPDATE SET url = EXCLUDED.url, priority = EXCLUDED.priority
                """, (term, source, url, priority))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error saving research link: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    # Memories methods (for AI context)
    def save_memory(
        self,
        category: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Save a memory for AI context."""
        if not self.connect():
            return False
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories (category, content, metadata)
                    VALUES (%s, %s, %s)
                """, (
                    category,
                    content,
                    json.dumps(metadata or {})
                ))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error saving memory: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def get_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get memories, optionally filtered by category."""
        if not self.connect():
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                if category:
                    cur.execute("SELECT * FROM memories WHERE category = %s ORDER BY created_at DESC", (category,))
                else:
                    cur.execute("SELECT * FROM memories ORDER BY created_at DESC")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching memories: {e}")
            return []
        finally:
            self.disconnect()

    # =========================================================================
    # TWO-WAY SYNC - READ METHODS (Added for bidirectional sync)
    # =========================================================================

    def get_all_footnotes(self) -> List[Dict[str, Any]]:
        """Get all footnotes from database."""
        if not self.connect():
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM footnotes ORDER BY marker")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching footnotes: {e}")
            return []
        finally:
            self.disconnect()

    def get_footnotes_by_term(self, term: str) -> List[Dict[str, Any]]:
        """Get footnotes for a specific term."""
        if not self.connect():
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM footnotes WHERE term = %s ORDER BY marker", (term,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching footnotes for term: {e}")
            return []
        finally:
            self.disconnect()

    def get_all_research_links(self) -> List[Dict[str, Any]]:
        """Get all research links from database."""
        if not self.connect():
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM research_links ORDER BY term, priority DESC")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching research links: {e}")
            return []
        finally:
            self.disconnect()

    def get_research_links_by_term(self, term: str) -> List[Dict[str, Any]]:
        """Get research links for a specific term."""
        if not self.connect():
            return []

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM research_links WHERE term = %s ORDER BY priority DESC", (term,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching research links for term: {e}")
            return []
        finally:
            self.disconnect()

    def get_definition_by_phrase(self, phrase: str) -> Optional[Dict[str, Any]]:
        """Get a single definition by phrase."""
        if not self.connect():
            return None

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM definitions WHERE phrase = %s", (phrase,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error fetching definition: {e}")
            return None
        finally:
            self.disconnect()

    def delete_definition(self, phrase: str) -> bool:
        """Delete a definition by phrase."""
        if not self.connect():
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM definitions WHERE phrase = %s", (phrase,))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting definition: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def delete_footnote(self, footnote_id: int) -> bool:
        """Delete a footnote by ID."""
        if not self.connect():
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM footnotes WHERE id = %s", (footnote_id,))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting footnote: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def delete_research_link(self, term: str, source: str) -> bool:
        """Delete a research link by term and source."""
        if not self.connect():
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM research_links WHERE term = %s AND source = %s", (term, source))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"Error deleting research link: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()

    # =========================================================================
    # TWO-WAY SYNC - Vault <-> Database synchronization
    # =========================================================================

    def sync_definitions_to_vault(self, vault_path: str) -> Dict[str, int]:
        """Sync definitions from database to vault (DB -> Vault).

        Returns dict with counts: {'created': n, 'updated': n, 'skipped': n}
        """
        from pathlib import Path
        import json as json_mod

        definitions = self.get_all_definitions()
        glossary_path = Path(vault_path) / "02_LIBRARY" / "Glossary"
        glossary_path.mkdir(parents=True, exist_ok=True)

        stats = {'created': 0, 'updated': 0, 'skipped': 0}

        for defn in definitions:
            phrase = defn.get('phrase', '')
            if not phrase:
                continue

            # Create safe filename
            safe_name = phrase.replace('/', '-').replace('\\', '-').replace(':', '-')
            file_path = glossary_path / f"{safe_name}.md"

            # Build 7-layer definition content
            aliases = defn.get('aliases', [])
            if isinstance(aliases, str):
                aliases = json_mod.loads(aliases) if aliases else []

            content = f"""---
aliases: {json_mod.dumps(aliases)}
tags: ["glossary", "theophysics", "db-synced"]
def-type: {defn.get('classification', 'general')}
category: {defn.get('folder', 'theophysics-general')}
db-id: {defn.get('id', '')}
synced-at: {datetime.now().isoformat()}
---

# {phrase}

## Core Definition

{defn.get('definition', 'Definition to be determined.')}

## Operational Definition

{phrase} functions within the Theophysics framework as...

## Ontological Context

General Ontology / Logos Framework

## Cross-References

{defn.get('vault_link', '')}

## Textbook Definition



## Narrative Definition


"""
            try:
                if file_path.exists():
                    # Check if DB is newer (update)
                    file_path.write_text(content, encoding='utf-8')
                    stats['updated'] += 1
                else:
                    file_path.write_text(content, encoding='utf-8')
                    stats['created'] += 1
            except Exception as e:
                print(f"Error syncing {phrase}: {e}")
                stats['skipped'] += 1

        return stats

    def sync_definitions_from_vault(self, vault_path: str) -> Dict[str, int]:
        """Sync definitions from vault to database (Vault -> DB).

        Returns dict with counts: {'created': n, 'updated': n, 'skipped': n}
        """
        from pathlib import Path
        import re

        glossary_path = Path(vault_path) / "02_LIBRARY" / "Glossary"
        if not glossary_path.exists():
            return {'created': 0, 'updated': 0, 'skipped': 0, 'error': 'Glossary not found'}

        stats = {'created': 0, 'updated': 0, 'skipped': 0}

        for md_file in glossary_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                phrase = md_file.stem

                # Skip garbage files
                if phrase.startswith('#') or phrase.startswith('$'):
                    stats['skipped'] += 1
                    continue

                # Extract definition from Core Definition section
                core_match = re.search(r'## Core Definition\s*\n(.*?)(?=\n##|\Z)', content, re.DOTALL)
                definition = core_match.group(1).strip() if core_match else ""

                # Extract aliases from frontmatter
                aliases_match = re.search(r'aliases:\s*\[(.*?)\]', content)
                aliases = []
                if aliases_match:
                    aliases_str = aliases_match.group(1)
                    aliases = [a.strip().strip('"\'') for a in aliases_str.split(',') if a.strip()]

                # Extract classification
                class_match = re.search(r'def-type:\s*(.+)', content)
                classification = class_match.group(1).strip() if class_match else ""

                # Extract folder/category
                cat_match = re.search(r'category:\s*(.+)', content)
                folder = cat_match.group(1).strip() if cat_match else ""

                # Check if exists in DB
                existing = self.get_definition_by_phrase(phrase)

                success = self.save_definition(
                    phrase=phrase,
                    definition=definition or "Definition to be determined.",
                    aliases=aliases,
                    classification=classification,
                    folder=folder,
                    vault_link=str(md_file)
                )

                if success:
                    if existing:
                        stats['updated'] += 1
                    else:
                        stats['created'] += 1
                else:
                    stats['skipped'] += 1

            except Exception as e:
                print(f"Error syncing {md_file}: {e}")
                stats['skipped'] += 1

        return stats

    def test_connection(self) -> bool:
        """Test database connection."""
        return self.connect()

