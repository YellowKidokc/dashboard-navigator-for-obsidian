# engine/database_engine.py

import sqlite3
import uuid
from pathlib import Path
import json
import time
from typing import Iterable, Dict, Any

try:
    import psycopg
except ImportError:
    psycopg = None  # optional


def generate_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class DatabaseEngine:
    def __init__(self, settings):
        self.settings = settings
        self.db_path = self._resolve_db_path()
        self._ensure_schema()

    def _resolve_db_path(self) -> Path:
        if self.settings.sqlite_path:
            return self.settings.sqlite_path
        if self.settings.vault_path and self.settings.vault_path.exists():
            return self.settings.vault_path / "theophysics.db"
        # Default to current directory
        return Path(__file__).parent.parent / "theophysics.db"

    def update_db_path(self, p: Path):
        self.db_path = p
        self._ensure_schema()

    def _ensure_schema(self):
        # Ensure parent directory exists (only if not root/system dir)
        try:
            if self.db_path.parent != self.db_path.parent.parent:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            # If we can't create parent, use current directory
            self.db_path = Path(__file__).parent.parent / "theophysics.db"
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # ===========================================
        # CORE TABLES - Mirror of Vault Structure
        # ===========================================
        
        # All markdown files in the vault
        c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            path TEXT UNIQUE,
            title TEXT,
            folder TEXT,
            note_type TEXT,
            yaml TEXT,
            tags TEXT,
            links TEXT,
            content TEXT,
            word_count INTEGER,
            hash TEXT,
            created_at INTEGER,
            modified_at INTEGER,
            updated_at INTEGER
        )
        """)
        
        # Papers (subset of notes with paper-specific metadata)
        c.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            note_uuid TEXT REFERENCES notes(uuid),
            paper_id TEXT UNIQUE,
            title TEXT,
            authors TEXT,
            abstract TEXT,
            status TEXT,
            domain TEXT,
            keywords TEXT,
            citations TEXT,
            file_path TEXT,
            updated_at INTEGER
        )
        """)

        # Definitions with full structure
        c.execute("""
        CREATE TABLE IF NOT EXISTS definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            term TEXT UNIQUE,
            symbol TEXT,
            aliases TEXT,
            classification TEXT,
            canonical_definition TEXT,
            canonical_formula TEXT,
            body TEXT,
            status TEXT,
            completeness_score REAL,
            file_path TEXT,
            updated_at INTEGER
        )
        """)

        # ===========================================
        # SEMANTIC ELEMENTS - Extracted from Notes
        # ===========================================
        
        # Axioms extracted from definitions/papers
        c.execute("""
        CREATE TABLE IF NOT EXISTS axioms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            axiom_id TEXT UNIQUE,
            name TEXT,
            statement TEXT,
            equation TEXT,
            category TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            source_term TEXT,
            updated_at INTEGER
        )
        """)
        
        # Theorems and proofs
        c.execute("""
        CREATE TABLE IF NOT EXISTS theorems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            theorem_id TEXT UNIQUE,
            name TEXT,
            statement TEXT,
            equation TEXT,
            proof_reference TEXT,
            implications TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER
        )
        """)
        
        # Mathematical structures and equations
        c.execute("""
        CREATE TABLE IF NOT EXISTS equations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            equation_id TEXT UNIQUE,
            label TEXT,
            latex TEXT,
            description TEXT,
            variables TEXT,
            domain TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            source_section TEXT,
            updated_at INTEGER
        )
        """)
        
        # Evidence bundles - causal claims with supporting evidence
        c.execute("""
        CREATE TABLE IF NOT EXISTS evidence_bundles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            bundle_id TEXT UNIQUE,
            claim TEXT,
            evidence_type TEXT,
            supporting_sentences TEXT,
            source_citations TEXT,
            confidence REAL,
            domain TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER
        )
        """)
        
        # Domain interpretations for terms
        c.execute("""
        CREATE TABLE IF NOT EXISTS domain_interpretations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            term TEXT,
            domain TEXT,
            interpretation TEXT,
            equation TEXT,
            phenomena TEXT,
            measurement TEXT,
            scale TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER,
            UNIQUE(term, domain)
        )
        """)

        # ===========================================
        # RELATIONSHIP TABLES - Ontology & Links
        # ===========================================
        
        # Ontology nodes (concepts and their relationships)
        c.execute("""
        CREATE TABLE IF NOT EXISTS ontology_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            term TEXT UNIQUE,
            node_type TEXT,
            classification TEXT,
            parents TEXT,
            children TEXT,
            related TEXT,
            properties TEXT,
            updated_at INTEGER
        )
        """)
        
        # Explicit relationships between concepts
        c.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            source_term TEXT,
            target_term TEXT,
            relationship_type TEXT,
            strength REAL,
            evidence TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER,
            UNIQUE(source_term, target_term, relationship_type)
        )
        """)

        # ===========================================
        # REFERENCE TABLES - External Sources
        # ===========================================
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS research_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            term TEXT,
            source TEXT,
            url TEXT,
            title TEXT,
            snippet TEXT,
            retrieved_at INTEGER
        )
        """)
        
        # Citations found in papers
        c.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            citation_key TEXT,
            authors TEXT,
            year INTEGER,
            title TEXT,
            source TEXT,
            url TEXT,
            found_in_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER
        )
        """)

        # ===========================================
        # TRACKING TABLES - Drift, Changes, Cache
        # ===========================================
        
        # Usage drift log for definitions
        c.execute("""
        CREATE TABLE IF NOT EXISTS drift_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            term TEXT,
            date TEXT,
            context TEXT,
            observation TEXT,
            resolution TEXT,
            severity TEXT,
            source_note_id INTEGER REFERENCES notes(id),
            updated_at INTEGER
        )
        """)
        
        # Cache for expensive computations
        c.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            cache_key TEXT UNIQUE,
            cache_type TEXT,
            data TEXT,
            expires_at INTEGER,
            created_at INTEGER
        )
        """)
        
        # Sync status for PostgreSQL
        c.execute("""
        CREATE TABLE IF NOT EXISTS sync_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            table_name TEXT UNIQUE,
            last_sync_at INTEGER,
            records_synced INTEGER,
            status TEXT
        )
        """)

        # ===========================================
        # ANALYTICS TABLES - Paper & Insight Results
        # ===========================================
        
        # Paper analytics (coherence scores, metrics per paper)
        c.execute("""
        CREATE TABLE IF NOT EXISTS paper_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            paper_id TEXT UNIQUE,
            paper_name TEXT,
            coherence_score REAL,
            grade TEXT,
            concept_count INTEGER,
            equation_count INTEGER,
            tag_count INTEGER,
            word_count INTEGER,
            cross_ref_density REAL,
            term_consistency REAL,
            domains TEXT,
            top_concepts TEXT,
            scan_timestamp INTEGER,
            updated_at INTEGER
        )
        """)
        
        # Breakout detections
        c.execute("""
        CREATE TABLE IF NOT EXISTS breakouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            title TEXT,
            description TEXT,
            papers_involved TEXT,
            domains_bridged TEXT,
            novelty_score REAL,
            integration_order INTEGER,
            evidence TEXT,
            implications TEXT,
            scan_timestamp INTEGER,
            updated_at INTEGER
        )
        """)
        
        # Coherence points (Lagrangian mappings)
        c.execute("""
        CREATE TABLE IF NOT EXISTS coherence_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            physical_law TEXT,
            spiritual_principle TEXT,
            mapping_strength REAL,
            papers_supporting TEXT,
            key_equations TEXT,
            explanation TEXT,
            lagrangian_term TEXT,
            scan_timestamp INTEGER,
            updated_at INTEGER,
            UNIQUE(physical_law, spiritual_principle)
        )
        """)
        
        # Hidden correlations
        c.execute("""
        CREATE TABLE IF NOT EXISTS hidden_correlations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            concept_a TEXT,
            concept_b TEXT,
            correlation_type TEXT,
            surprise_score REAL,
            explanation TEXT,
            papers_found_in TEXT,
            why_unexpected TEXT,
            scan_timestamp INTEGER,
            updated_at INTEGER,
            UNIQUE(concept_a, concept_b)
        )
        """)
        
        # Global analytics summary
        c.execute("""
        CREATE TABLE IF NOT EXISTS global_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT UNIQUE NOT NULL,
            overall_coherence REAL,
            grade TEXT,
            law_coverage REAL,
            trinity_balance REAL,
            grace_entropy REAL,
            papers_analyzed INTEGER,
            total_breakouts INTEGER,
            total_coherence_points INTEGER,
            total_hidden_correlations INTEGER,
            scan_timestamp INTEGER,
            updated_at INTEGER
        )
        """)

        # ===========================================
        # INDEXES for performance
        # ===========================================
        
        c.execute("CREATE INDEX IF NOT EXISTS idx_notes_uuid ON notes(uuid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(note_type)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notes_hash ON notes(hash)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_definitions_term ON definitions(term)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_axioms_category ON axioms(category)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_equations_domain ON equations(domain)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_evidence_domain ON evidence_bundles(domain)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_term)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_term)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache(cache_key)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")

        conn.commit()
        conn.close()

    # -------- Notes --------

    def store_notes(self, notes: Iterable[Dict[str, Any]], replace: bool = False):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if replace:
            c.execute("DELETE FROM notes")
        now = int(time.time())
        for n in notes:
            # Check if note already exists to preserve UUID
            c.execute("SELECT uuid FROM notes WHERE path = ?", (n["path"],))
            existing = c.fetchone()
            note_uuid = existing[0] if existing else n.get("uuid") or generate_uuid()
            
            c.execute("""
            INSERT OR REPLACE INTO notes (uuid, path, title, folder, note_type, yaml, tags, links, content, word_count, hash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                note_uuid,
                n["path"],
                n["title"],
                n.get("folder"),
                n.get("note_type"),
                json.dumps(n.get("yaml", {})),
                json.dumps(n.get("tags", [])),
                json.dumps(n.get("links", [])),
                n.get("content"),
                n.get("word_count"),
                n["hash"],
                now
            ))
        conn.commit()
        conn.close()

    def get_metrics(self) -> dict:
        """Get vault metrics with ACTUAL counts (not string lengths)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Count notes
        c.execute("SELECT COUNT(*) FROM notes")
        notes_count = c.fetchone()[0]

        # Count actual tags and links by parsing the JSON
        c.execute("SELECT tags, links FROM notes")
        rows = c.fetchall()
        
        total_tags = 0
        unique_tags = set()
        total_links = 0
        unique_links = set()
        
        for tags_json, links_json in rows:
            try:
                tags = json.loads(tags_json) if tags_json else []
                links = json.loads(links_json) if links_json else []
                
                total_tags += len(tags)
                unique_tags.update(tags)
                
                total_links += len(links)
                unique_links.update(links)
            except (json.JSONDecodeError, TypeError):
                pass

        # Count definitions
        c.execute("SELECT COUNT(*) FROM definitions")
        defs_count = c.fetchone()[0]

        conn.close()

        return {
            "notes": notes_count,
            "tags": len(unique_tags),  # Unique tag count
            "tags_total": total_tags,   # Total tag occurrences
            "links": len(unique_links), # Unique link count
            "links_total": total_links, # Total link occurrences
            "definitions": defs_count,
            "errors": 0,
        }

    # -------- Definitions --------

    def upsert_definition(self, data: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if definition exists to preserve UUID
        c.execute("SELECT uuid FROM definitions WHERE term = ?", (data["term"],))
        existing = c.fetchone()
        def_uuid = existing[0] if existing else data.get("uuid") or generate_uuid()
        
        c.execute("""
        INSERT INTO definitions (uuid, term, symbol, aliases, classification, canonical_definition, canonical_formula, body, status, completeness_score, file_path, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(term) DO UPDATE SET
            symbol = excluded.symbol,
            aliases = excluded.aliases,
            classification = excluded.classification,
            canonical_definition = excluded.canonical_definition,
            canonical_formula = excluded.canonical_formula,
            body = excluded.body,
            status = excluded.status,
            completeness_score = excluded.completeness_score,
            file_path = excluded.file_path,
            updated_at = excluded.updated_at
        """, (
            def_uuid,
            data["term"],
            data.get("symbol"),
            json.dumps(data.get("aliases", [])),
            data.get("classification"),
            data.get("canonical_definition"),
            data.get("canonical_formula"),
            data.get("body"),
            data.get("status", "draft"),
            data.get("completeness_score"),
            data.get("file_path"),
            now
        ))
        conn.commit()
        conn.close()

    def list_definitions(self) -> list[dict]:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT term, status, file_path FROM definitions ORDER BY term")
        rows = c.fetchall()
        conn.close()
        return [{"term": r[0], "status": r[1] or "", "file_path": r[2] or ""} for r in rows]

    def get_definition(self, term: str) -> dict | None:
        """Get full definition by term."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT term, aliases, classification, body, status, file_path
        FROM definitions WHERE term = ?
        """, (term,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "term": row[0],
            "aliases": json.loads(row[1]) if row[1] else [],
            "classification": row[2],
            "body": row[3],
            "status": row[4],
            "file_path": row[5],
        }

    # -------- Research links --------

    def add_research_link(self, term: str, source: str, url: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        link_uuid = generate_uuid()
        c.execute("INSERT INTO research_links (uuid, term, source, url) VALUES (?, ?, ?, ?)",
                  (link_uuid, term, source, url))
        conn.commit()
        conn.close()

    def get_research_links(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT term, source, url FROM research_links")
        rows = c.fetchall()
        conn.close()

        result: dict[str, list[dict]] = {}
        for term, source, url in rows:
            result.setdefault(term.lower(), []).append({"source": source, "url": url})
        return result

    # -------- Query helpers --------

    def get_all_notes(self) -> list[dict]:
        """Get all notes from database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT path, title, yaml, tags, links, hash FROM notes")
        rows = c.fetchall()
        conn.close()
        
        return [{
            "path": r[0],
            "title": r[1],
            "yaml": json.loads(r[2]) if r[2] else {},
            "tags": json.loads(r[3]) if r[3] else [],
            "links": json.loads(r[4]) if r[4] else [],
            "hash": r[5],
        } for r in rows]

    def get_note_by_path(self, path: str) -> dict | None:
        """Get single note by path."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT path, title, yaml, tags, links, hash FROM notes WHERE path = ?", (path,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "path": row[0],
            "title": row[1],
            "yaml": json.loads(row[2]) if row[2] else {},
            "tags": json.loads(row[3]) if row[3] else [],
            "links": json.loads(row[4]) if row[4] else [],
            "hash": row[5],
        }

    # -------- Papers --------
    
    def upsert_paper(self, data: Dict[str, Any]):
        """Insert or update a paper record."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if paper exists to preserve UUID
        c.execute("SELECT uuid FROM papers WHERE paper_id = ?", (data["paper_id"],))
        existing = c.fetchone()
        paper_uuid = existing[0] if existing else data.get("uuid") or generate_uuid()
        
        c.execute("""
        INSERT INTO papers (uuid, paper_id, note_uuid, title, authors, abstract, status, domain, keywords, citations, file_path, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(paper_id) DO UPDATE SET
            note_uuid = excluded.note_uuid,
            title = excluded.title,
            authors = excluded.authors,
            abstract = excluded.abstract,
            status = excluded.status,
            domain = excluded.domain,
            keywords = excluded.keywords,
            citations = excluded.citations,
            file_path = excluded.file_path,
            updated_at = excluded.updated_at
        """, (
            paper_uuid,
            data["paper_id"],
            data.get("note_uuid"),
            data.get("title"),
            json.dumps(data.get("authors", [])),
            data.get("abstract"),
            data.get("status", "draft"),
            data.get("domain"),
            json.dumps(data.get("keywords", [])),
            json.dumps(data.get("citations", [])),
            data.get("file_path"),
            now
        ))
        conn.commit()
        conn.close()
    
    def get_all_papers(self) -> list[dict]:
        """Get all papers."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT paper_id, title, authors, status, domain, file_path FROM papers ORDER BY title")
        rows = c.fetchall()
        conn.close()
        return [{
            "paper_id": r[0],
            "title": r[1],
            "authors": json.loads(r[2]) if r[2] else [],
            "status": r[3],
            "domain": r[4],
            "file_path": r[5],
        } for r in rows]

    # -------- Axioms --------
    
    def upsert_axiom(self, data: Dict[str, Any]):
        """Insert or update an axiom."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if axiom exists to preserve UUID
        c.execute("SELECT uuid FROM axioms WHERE axiom_id = ?", (data["axiom_id"],))
        existing = c.fetchone()
        axiom_uuid = existing[0] if existing else data.get("uuid") or generate_uuid()
        
        c.execute("""
        INSERT INTO axioms (uuid, axiom_id, name, statement, equation, category, source_note_id, source_term, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(axiom_id) DO UPDATE SET
            name = excluded.name,
            statement = excluded.statement,
            equation = excluded.equation,
            category = excluded.category,
            source_note_id = excluded.source_note_id,
            source_term = excluded.source_term,
            updated_at = excluded.updated_at
        """, (
            axiom_uuid,
            data["axiom_id"],
            data.get("name"),
            data.get("statement"),
            data.get("equation"),
            data.get("category", "general"),
            data.get("source_note_id"),
            data.get("source_term"),
            now
        ))
        conn.commit()
        conn.close()
    
    def get_all_axioms(self) -> list[dict]:
        """Get all axioms."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT axiom_id, name, statement, equation, category, source_term FROM axioms ORDER BY axiom_id")
        rows = c.fetchall()
        conn.close()
        return [{
            "axiom_id": r[0],
            "name": r[1],
            "statement": r[2],
            "equation": r[3],
            "category": r[4],
            "source_term": r[5],
        } for r in rows]

    # -------- Theorems --------
    
    def upsert_theorem(self, data: Dict[str, Any]):
        """Insert or update a theorem."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO theorems (theorem_id, name, statement, equation, proof_reference, implications, source_note_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(theorem_id) DO UPDATE SET
            name = excluded.name,
            statement = excluded.statement,
            equation = excluded.equation,
            proof_reference = excluded.proof_reference,
            implications = excluded.implications,
            source_note_id = excluded.source_note_id,
            updated_at = excluded.updated_at
        """, (
            data["theorem_id"],
            data.get("name"),
            data.get("statement"),
            data.get("equation"),
            data.get("proof_reference"),
            json.dumps(data.get("implications", [])),
            data.get("source_note_id"),
            now
        ))
        conn.commit()
        conn.close()

    # -------- Equations --------
    
    def upsert_equation(self, data: Dict[str, Any]):
        """Insert or update an equation."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO equations (equation_id, label, latex, description, variables, domain, source_note_id, source_section, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(equation_id) DO UPDATE SET
            label = excluded.label,
            latex = excluded.latex,
            description = excluded.description,
            variables = excluded.variables,
            domain = excluded.domain,
            source_note_id = excluded.source_note_id,
            source_section = excluded.source_section,
            updated_at = excluded.updated_at
        """, (
            data["equation_id"],
            data.get("label"),
            data.get("latex"),
            data.get("description"),
            json.dumps(data.get("variables", [])),
            data.get("domain"),
            data.get("source_note_id"),
            data.get("source_section"),
            now
        ))
        conn.commit()
        conn.close()
    
    def get_all_equations(self) -> list[dict]:
        """Get all equations."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT equation_id, label, latex, description, domain FROM equations ORDER BY equation_id")
        rows = c.fetchall()
        conn.close()
        return [{
            "equation_id": r[0],
            "label": r[1],
            "latex": r[2],
            "description": r[3],
            "domain": r[4],
        } for r in rows]

    # -------- Evidence Bundles --------
    
    def upsert_evidence_bundle(self, data: Dict[str, Any]):
        """Insert or update an evidence bundle."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO evidence_bundles (bundle_id, claim, evidence_type, supporting_sentences, source_citations, confidence, domain, source_note_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(bundle_id) DO UPDATE SET
            claim = excluded.claim,
            evidence_type = excluded.evidence_type,
            supporting_sentences = excluded.supporting_sentences,
            source_citations = excluded.source_citations,
            confidence = excluded.confidence,
            domain = excluded.domain,
            source_note_id = excluded.source_note_id,
            updated_at = excluded.updated_at
        """, (
            data["bundle_id"],
            data.get("claim"),
            data.get("evidence_type"),
            json.dumps(data.get("supporting_sentences", [])),
            json.dumps(data.get("source_citations", [])),
            data.get("confidence", 0.0),
            data.get("domain"),
            data.get("source_note_id"),
            now
        ))
        conn.commit()
        conn.close()
    
    def get_all_evidence_bundles(self) -> list[dict]:
        """Get all evidence bundles."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT bundle_id, claim, evidence_type, confidence, domain FROM evidence_bundles ORDER BY confidence DESC")
        rows = c.fetchall()
        conn.close()
        return [{
            "bundle_id": r[0],
            "claim": r[1],
            "evidence_type": r[2],
            "confidence": r[3],
            "domain": r[4],
        } for r in rows]

    # -------- Domain Interpretations --------
    
    def upsert_domain_interpretation(self, data: Dict[str, Any]):
        """Insert or update a domain interpretation."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO domain_interpretations (term, domain, interpretation, equation, phenomena, measurement, scale, source_note_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(term, domain) DO UPDATE SET
            interpretation = excluded.interpretation,
            equation = excluded.equation,
            phenomena = excluded.phenomena,
            measurement = excluded.measurement,
            scale = excluded.scale,
            source_note_id = excluded.source_note_id,
            updated_at = excluded.updated_at
        """, (
            data["term"],
            data["domain"],
            data.get("interpretation"),
            data.get("equation"),
            json.dumps(data.get("phenomena", [])),
            data.get("measurement"),
            data.get("scale"),
            data.get("source_note_id"),
            now
        ))
        conn.commit()
        conn.close()

    # -------- Ontology --------
    
    def upsert_ontology_node(self, data: Dict[str, Any]):
        """Insert or update an ontology node."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO ontology_nodes (term, node_type, classification, parents, children, related, properties, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(term) DO UPDATE SET
            node_type = excluded.node_type,
            classification = excluded.classification,
            parents = excluded.parents,
            children = excluded.children,
            related = excluded.related,
            properties = excluded.properties,
            updated_at = excluded.updated_at
        """, (
            data["term"],
            data.get("node_type"),
            data.get("classification"),
            json.dumps(data.get("parents", [])),
            json.dumps(data.get("children", [])),
            json.dumps(data.get("related", [])),
            json.dumps(data.get("properties", {})),
            now
        ))
        conn.commit()
        conn.close()

    # -------- Relationships --------
    
    def upsert_relationship(self, data: Dict[str, Any]):
        """Insert or update a relationship between terms."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("""
        INSERT INTO relationships (source_term, target_term, relationship_type, strength, evidence, source_note_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_term, target_term, relationship_type) DO UPDATE SET
            strength = excluded.strength,
            evidence = excluded.evidence,
            source_note_id = excluded.source_note_id,
            updated_at = excluded.updated_at
        """, (
            data["source_term"],
            data["target_term"],
            data["relationship_type"],
            data.get("strength", 1.0),
            data.get("evidence"),
            data.get("source_note_id"),
            now
        ))
        conn.commit()
        conn.close()

    # -------- Cache --------
    
    def cache_set(self, key: str, cache_type: str, data: Any, ttl_seconds: int = 3600):
        """Set a cache entry."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        expires = now + ttl_seconds
        c.execute("""
        INSERT INTO cache (cache_key, cache_type, data, expires_at, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(cache_key) DO UPDATE SET
            cache_type = excluded.cache_type,
            data = excluded.data,
            expires_at = excluded.expires_at,
            created_at = excluded.created_at
        """, (key, cache_type, json.dumps(data), expires, now))
        conn.commit()
        conn.close()
    
    def cache_get(self, key: str) -> Any | None:
        """Get a cache entry if not expired."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("SELECT data FROM cache WHERE cache_key = ? AND expires_at > ?", (key, now))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        return None
    
    def cache_clear_expired(self):
        """Clear expired cache entries."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        c.execute("DELETE FROM cache WHERE expires_at < ?", (now,))
        conn.commit()
        conn.close()

    # -------- Comprehensive Metrics --------
    
    def get_full_metrics(self) -> dict:
        """Get comprehensive metrics for all tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        metrics = {}
        tables = ['notes', 'papers', 'definitions', 'axioms', 'theorems', 
                  'equations', 'evidence_bundles', 'domain_interpretations',
                  'ontology_nodes', 'relationships', 'citations', 'research_links']
        
        for table in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                metrics[table] = c.fetchone()[0]
            except:
                metrics[table] = 0
        
        conn.close()
        return metrics

    # -------- Aggregation / Maintenance --------

    def aggregate_data(self):
        # Placeholder for future aggregation logic
        return True

    def vacuum_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("VACUUM")
        conn.close()
        return True

    # -------- Postgres export --------

    def export_to_postgres(self) -> tuple[bool, str]:
        if not self.settings.postgres_conn_str:
            return False, "Postgres connection string not set."

        if psycopg is None:
            return False, "psycopg is not installed. Run: pip install psycopg[binary]"

        try:
            with psycopg.connect(self.settings.postgres_conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS notes (
                        path TEXT PRIMARY KEY,
                        title TEXT,
                        yaml JSONB,
                        tags JSONB,
                        links JSONB,
                        hash TEXT,
                        updated_at BIGINT
                    )
                    """)
                    cur.execute("""
                    CREATE TABLE IF NOT EXISTS definitions (
                        term TEXT PRIMARY KEY,
                        aliases JSONB,
                        classification TEXT,
                        body TEXT,
                        status TEXT,
                        file_path TEXT,
                        updated_at BIGINT
                    )
                    """)

                    # export Notes
                    sconn = sqlite3.connect(self.db_path)
                    sc = sconn.cursor()
                    sc.execute("SELECT path, title, yaml, tags, links, hash, updated_at FROM notes")
                    
                    note_count = 0
                    for row in sc.fetchall():
                        cur.execute("""
                        INSERT INTO notes (path, title, yaml, tags, links, hash, updated_at)
                        VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                        ON CONFLICT(path) DO UPDATE SET
                            title = EXCLUDED.title,
                            yaml = EXCLUDED.yaml,
                            tags = EXCLUDED.tags,
                            links = EXCLUDED.links,
                            hash = EXCLUDED.hash,
                            updated_at = EXCLUDED.updated_at
                        """, row)
                        note_count += 1

                    # export Definitions
                    sc.execute("SELECT term, aliases, classification, body, status, file_path, updated_at FROM definitions")
                    
                    def_count = 0
                    for row in sc.fetchall():
                        cur.execute("""
                        INSERT INTO definitions (term, aliases, classification, body, status, file_path, updated_at)
                        VALUES (%s, %s::jsonb, %s, %s, %s, %s, %s)
                        ON CONFLICT(term) DO UPDATE SET
                            aliases = EXCLUDED.aliases,
                            classification = EXCLUDED.classification,
                            body = EXCLUDED.body,
                            status = EXCLUDED.status,
                            file_path = EXCLUDED.file_path,
                            updated_at = EXCLUDED.updated_at
                        """, row)
                        def_count += 1

                    sconn.close()

            return True, f"Export complete: {note_count} notes, {def_count} definitions"
        except Exception as e:
            return False, f"Postgres export error: {e}"

    # -------- Paper Analytics Storage --------
    
    def store_paper_analytics(self, paper_data: Dict[str, Any]):
        """Store analytics for a single paper."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        paper_id = paper_data.get("paper_id") or paper_data.get("name", "").replace(" ", "_")[:20]
        
        # Check if exists to preserve UUID
        c.execute("SELECT uuid FROM paper_analytics WHERE paper_id = ?", (paper_id,))
        existing = c.fetchone()
        analytics_uuid = existing[0] if existing else generate_uuid()
        
        c.execute("""
        INSERT INTO paper_analytics (uuid, paper_id, paper_name, coherence_score, grade, 
            concept_count, equation_count, tag_count, word_count, cross_ref_density, 
            term_consistency, domains, top_concepts, scan_timestamp, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(paper_id) DO UPDATE SET
            paper_name = excluded.paper_name,
            coherence_score = excluded.coherence_score,
            grade = excluded.grade,
            concept_count = excluded.concept_count,
            equation_count = excluded.equation_count,
            tag_count = excluded.tag_count,
            word_count = excluded.word_count,
            cross_ref_density = excluded.cross_ref_density,
            term_consistency = excluded.term_consistency,
            domains = excluded.domains,
            top_concepts = excluded.top_concepts,
            scan_timestamp = excluded.scan_timestamp,
            updated_at = excluded.updated_at
        """, (
            analytics_uuid,
            paper_id,
            paper_data.get("name"),
            paper_data.get("coherence", 0),
            paper_data.get("grade", ""),
            paper_data.get("concepts", 0),
            paper_data.get("equations", 0),
            paper_data.get("tags", 0),
            paper_data.get("words", 0),
            paper_data.get("cross_ref_density", 0),
            paper_data.get("term_consistency", 0),
            json.dumps(paper_data.get("domains", [])),
            json.dumps(paper_data.get("top_concepts", {})),
            now,
            now
        ))
        conn.commit()
        conn.close()
    
    def store_all_paper_analytics(self, papers: list[Dict[str, Any]]):
        """Store analytics for multiple papers."""
        for paper in papers:
            self.store_paper_analytics(paper)
    
    def get_all_paper_analytics(self) -> list[dict]:
        """Get all stored paper analytics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT paper_id, paper_name, coherence_score, grade, concept_count, 
               equation_count, tag_count, word_count, scan_timestamp
        FROM paper_analytics ORDER BY paper_name
        """)
        rows = c.fetchall()
        conn.close()
        return [{
            "paper_id": r[0],
            "name": r[1],
            "coherence": r[2],
            "grade": r[3],
            "concepts": r[4],
            "equations": r[5],
            "tags": r[6],
            "words": r[7],
            "scan_timestamp": r[8],
        } for r in rows]

    # -------- Insight Results Storage --------
    
    def store_breakout(self, breakout: Dict[str, Any]):
        """Store a breakout detection result."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        breakout_uuid = generate_uuid()
        
        c.execute("""
        INSERT INTO breakouts (uuid, title, description, papers_involved, domains_bridged,
            novelty_score, integration_order, evidence, implications, scan_timestamp, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            breakout_uuid,
            breakout.get("title"),
            breakout.get("description"),
            json.dumps(breakout.get("papers_involved", [])),
            json.dumps(breakout.get("domains_bridged", [])),
            breakout.get("novelty_score", 0),
            breakout.get("integration_order", 1),
            json.dumps(breakout.get("evidence", [])),
            json.dumps(breakout.get("implications", [])),
            now,
            now
        ))
        conn.commit()
        conn.close()
    
    def store_coherence_point(self, point: Dict[str, Any]):
        """Store a coherence point (Lagrangian mapping)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if exists
        c.execute("SELECT uuid FROM coherence_points WHERE physical_law = ? AND spiritual_principle = ?",
                  (point.get("physical_law"), point.get("spiritual_principle")))
        existing = c.fetchone()
        point_uuid = existing[0] if existing else generate_uuid()
        
        c.execute("""
        INSERT INTO coherence_points (uuid, physical_law, spiritual_principle, mapping_strength,
            papers_supporting, key_equations, explanation, lagrangian_term, scan_timestamp, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(physical_law, spiritual_principle) DO UPDATE SET
            mapping_strength = excluded.mapping_strength,
            papers_supporting = excluded.papers_supporting,
            key_equations = excluded.key_equations,
            explanation = excluded.explanation,
            lagrangian_term = excluded.lagrangian_term,
            scan_timestamp = excluded.scan_timestamp,
            updated_at = excluded.updated_at
        """, (
            point_uuid,
            point.get("physical_law"),
            point.get("spiritual_principle"),
            point.get("mapping_strength", 0),
            json.dumps(point.get("papers_supporting", [])),
            json.dumps(point.get("key_equations", [])),
            point.get("explanation"),
            point.get("lagrangian_term"),
            now,
            now
        ))
        conn.commit()
        conn.close()
    
    def store_hidden_correlation(self, correlation: Dict[str, Any]):
        """Store a hidden correlation."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Check if exists
        c.execute("SELECT uuid FROM hidden_correlations WHERE concept_a = ? AND concept_b = ?",
                  (correlation.get("concept_a"), correlation.get("concept_b")))
        existing = c.fetchone()
        corr_uuid = existing[0] if existing else generate_uuid()
        
        c.execute("""
        INSERT INTO hidden_correlations (uuid, concept_a, concept_b, correlation_type,
            surprise_score, explanation, papers_found_in, why_unexpected, scan_timestamp, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(concept_a, concept_b) DO UPDATE SET
            correlation_type = excluded.correlation_type,
            surprise_score = excluded.surprise_score,
            explanation = excluded.explanation,
            papers_found_in = excluded.papers_found_in,
            why_unexpected = excluded.why_unexpected,
            scan_timestamp = excluded.scan_timestamp,
            updated_at = excluded.updated_at
        """, (
            corr_uuid,
            correlation.get("concept_a"),
            correlation.get("concept_b"),
            correlation.get("correlation_type"),
            correlation.get("surprise_score", 0),
            correlation.get("explanation"),
            json.dumps(correlation.get("papers_found_in", [])),
            correlation.get("why_unexpected"),
            now,
            now
        ))
        conn.commit()
        conn.close()
    
    def store_insight_results(self, result: Dict[str, Any]):
        """Store complete insight analysis results."""
        # Clear old results first
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM breakouts")
        c.execute("DELETE FROM coherence_points")
        c.execute("DELETE FROM hidden_correlations")
        conn.commit()
        conn.close()
        
        # Store breakouts
        for b in result.get("breakouts", []):
            self.store_breakout(b)
        
        # Store coherence points
        for cp in result.get("coherence_points", []):
            self.store_coherence_point(cp)
        
        # Store hidden correlations
        for hc in result.get("hidden_correlations", []):
            self.store_hidden_correlation(hc)
    
    def store_global_analytics(self, metrics: Dict[str, Any]):
        """Store global analytics summary."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = int(time.time())
        
        # Always replace the single global record
        c.execute("DELETE FROM global_analytics")
        
        global_uuid = generate_uuid()
        
        c.execute("""
        INSERT INTO global_analytics (uuid, overall_coherence, grade, law_coverage, 
            trinity_balance, grace_entropy, papers_analyzed, total_breakouts, 
            total_coherence_points, total_hidden_correlations, scan_timestamp, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            global_uuid,
            metrics.get("overall_coherence", 0),
            metrics.get("grade", ""),
            metrics.get("law_coverage", 0),
            metrics.get("trinity_balance", 0),
            metrics.get("grace_entropy", 0),
            metrics.get("papers_analyzed", 0),
            metrics.get("total_breakouts", 0),
            metrics.get("total_coherence_points", 0),
            metrics.get("total_hidden_correlations", 0),
            now,
            now
        ))
        conn.commit()
        conn.close()
    
    def get_global_analytics(self) -> dict | None:
        """Get the latest global analytics summary."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT overall_coherence, grade, law_coverage, trinity_balance, grace_entropy,
               papers_analyzed, total_breakouts, total_coherence_points, 
               total_hidden_correlations, scan_timestamp
        FROM global_analytics ORDER BY scan_timestamp DESC LIMIT 1
        """)
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "overall_coherence": row[0],
            "grade": row[1],
            "law_coverage": row[2],
            "trinity_balance": row[3],
            "grace_entropy": row[4],
            "papers_analyzed": row[5],
            "total_breakouts": row[6],
            "total_coherence_points": row[7],
            "total_hidden_correlations": row[8],
            "scan_timestamp": row[9],
        }
    
    def get_all_breakouts(self) -> list[dict]:
        """Get all stored breakouts."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT title, description, papers_involved, domains_bridged, novelty_score, 
               integration_order, evidence, implications
        FROM breakouts ORDER BY novelty_score DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [{
            "title": r[0],
            "description": r[1],
            "papers_involved": json.loads(r[2]) if r[2] else [],
            "domains_bridged": json.loads(r[3]) if r[3] else [],
            "novelty_score": r[4],
            "integration_order": r[5],
            "evidence": json.loads(r[6]) if r[6] else [],
            "implications": json.loads(r[7]) if r[7] else [],
        } for r in rows]
    
    def get_all_coherence_points(self) -> list[dict]:
        """Get all stored coherence points."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT physical_law, spiritual_principle, mapping_strength, papers_supporting,
               key_equations, explanation, lagrangian_term
        FROM coherence_points ORDER BY mapping_strength DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [{
            "physical_law": r[0],
            "spiritual_principle": r[1],
            "mapping_strength": r[2],
            "papers_supporting": json.loads(r[3]) if r[3] else [],
            "key_equations": json.loads(r[4]) if r[4] else [],
            "explanation": r[5],
            "lagrangian_term": r[6],
        } for r in rows]
    
    def get_all_hidden_correlations(self) -> list[dict]:
        """Get all stored hidden correlations."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
        SELECT concept_a, concept_b, correlation_type, surprise_score, 
               explanation, papers_found_in, why_unexpected
        FROM hidden_correlations ORDER BY surprise_score DESC
        """)
        rows = c.fetchall()
        conn.close()
        return [{
            "concept_a": r[0],
            "concept_b": r[1],
            "correlation_type": r[2],
            "surprise_score": r[3],
            "explanation": r[4],
            "papers_found_in": json.loads(r[5]) if r[5] else [],
            "why_unexpected": r[6],
        } for r in rows]
    
    def get_analytics_metrics(self) -> dict:
        """Get counts for all analytics tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        metrics = {}
        tables = ['paper_analytics', 'breakouts', 'coherence_points', 'hidden_correlations', 'global_analytics']
        
        for table in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                metrics[table] = c.fetchone()[0]
            except:
                metrics[table] = 0
        
        conn.close()
        return metrics
