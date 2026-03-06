"""
Conflict Ledger — PostgreSQL interface for the contradiction detection system.
Handles all CRUD operations on the conflict_ledger, math_index, extracted_claims,
and scan_history tables.

Follows existing postgres_manager.py patterns (connect/disconnect per operation).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor


@dataclass
class Conflict:
    """A single detected conflict/contradiction."""
    source_file: str
    conflict_type: str
    severity: str
    pass_number: int
    source_claim: str = ""
    source_location: str = ""
    source_axiom_id: str = ""
    target_file: str = ""
    target_claim: str = ""
    target_location: str = ""
    target_axiom_id: str = ""
    detected_by: str = "ollama"
    detection_model: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    status: str = "unresolved"
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass 
class ExtractedClaim:
    """A claim parsed from a document."""
    source_file: str
    claim_text: str
    claim_type: str = "assertion"
    section_header: str = ""
    line_number: int = 0
    axiom_id: str = ""
    variables_referenced: list = field(default_factory=list)
    extracted_by: str = "ollama"


@dataclass
class MathEntry:
    """An equation extracted from the vault."""
    latex: str
    source_file: str
    axiom_id: str = ""
    section_header: str = ""
    context_before: str = ""
    context_after: str = ""
    variables: dict = field(default_factory=dict)
    equation_type: str = "unknown"
    display_type: str = "display"


class ConflictLedger:
    """PostgreSQL interface for the contradiction detection system."""
    
    def __init__(self, host="192.168.1.177", port=2665, 
                 database="Theophysics", user="Yellowkid", password="Moss9pep2828"):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.conn = None
        self._ensure_schema()
    
    # =========================================================================
    # CONNECTION
    # =========================================================================
    
    def connect(self) -> bool:
        """Connect to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(
                host=self.host, port=self.port,
                database=self.database, user=self.user,
                password=self.password
            )
            return True
        except psycopg2.OperationalError as e:
            print(f"[ConflictLedger] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from PostgreSQL."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _ensure_schema(self):
        """Create tables if they don't exist."""
        if not self.connect():
            print("[ConflictLedger] Cannot create schema — DB unavailable")
            return
        
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            print(f"[ConflictLedger] Schema file not found: {schema_path}")
            self.disconnect()
            return
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            with self.conn.cursor() as cur:
                cur.execute(sql)
            self.conn.commit()
            print("[ConflictLedger] Schema verified/created")
        except Exception as e:
            print(f"[ConflictLedger] Schema error: {e}")
            if self.conn:
                self.conn.rollback()
        finally:
            self.disconnect()
    
    # =========================================================================
    # CONFLICT LEDGER — WRITE
    # =========================================================================
    
    def record_conflict(self, conflict: Conflict) -> Optional[int]:
        """Record a conflict. Returns the new conflict ID, or None on failure."""
        if not self.connect():
            return None
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conflict_ledger (
                        source_file, source_claim, source_location, source_axiom_id,
                        target_file, target_claim, target_location, target_axiom_id,
                        conflict_type, severity, status,
                        pass_number, detected_by, detection_model, confidence, reasoning
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s, %s
                    ) RETURNING id
                """, (
                    conflict.source_file, conflict.source_claim or None,
                    conflict.source_location or None, conflict.source_axiom_id or None,
                    conflict.target_file or None, conflict.target_claim or None,
                    conflict.target_location or None, conflict.target_axiom_id or None,
                    conflict.conflict_type, conflict.severity, conflict.status,
                    conflict.pass_number, conflict.detected_by,
                    conflict.detection_model or None,
                    conflict.confidence if conflict.confidence else None,
                    conflict.reasoning or None
                ))
                result = cur.fetchone()
                self.conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"[ConflictLedger] Error recording conflict: {e}")
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            self.disconnect()
    
    def record_conflicts_batch(self, conflicts: List[Conflict]) -> int:
        """Record multiple conflicts in one transaction. Returns count inserted."""
        if not conflicts:
            return 0
        if not self.connect():
            return 0
        
        count = 0
        try:
            with self.conn.cursor() as cur:
                for c in conflicts:
                    cur.execute("""
                        INSERT INTO conflict_ledger (
                            source_file, source_claim, source_location, source_axiom_id,
                            target_file, target_claim, target_location, target_axiom_id,
                            conflict_type, severity, status,
                            pass_number, detected_by, detection_model, confidence, reasoning
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        c.source_file, c.source_claim or None,
                        c.source_location or None, c.source_axiom_id or None,
                        c.target_file or None, c.target_claim or None,
                        c.target_location or None, c.target_axiom_id or None,
                        c.conflict_type, c.severity, c.status,
                        c.pass_number, c.detected_by,
                        c.detection_model or None,
                        c.confidence if c.confidence else None,
                        c.reasoning or None
                    ))
                    count += 1
            self.conn.commit()
            return count
        except Exception as e:
            print(f"[ConflictLedger] Batch error: {e}")
            if self.conn:
                self.conn.rollback()
            return 0
        finally:
            self.disconnect()
    
    def update_conflict_status(self, conflict_id: int, status: str, 
                                resolution_notes: str = "", resolved_by: str = "") -> bool:
        """Update the status of a conflict."""
        if not self.connect():
            return False
        
        try:
            with self.conn.cursor() as cur:
                if status in ('resolved', 'accepted_tension', 'false_positive', 'duplicate'):
                    cur.execute("""
                        UPDATE conflict_ledger 
                        SET status = %s, resolution_notes = %s, resolved_by = %s,
                            resolved_at = CURRENT_TIMESTAMP, reviewed_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (status, resolution_notes or None, resolved_by or None, conflict_id))
                else:
                    cur.execute("""
                        UPDATE conflict_ledger 
                        SET status = %s, reviewed_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (status, conflict_id))
                self.conn.commit()
                return cur.rowcount > 0
        except Exception as e:
            print(f"[ConflictLedger] Update error: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    # =========================================================================
    # CONFLICT LEDGER — READ
    # =========================================================================
    
    def get_conflicts(self, status: str = None, severity: str = None,
                      pass_number: int = None, source_file: str = None,
                      conflict_type: str = None, limit: int = 100) -> List[Dict]:
        """Query conflicts with optional filters."""
        if not self.connect():
            return []
        
        try:
            conditions = []
            params = []
            
            if status:
                conditions.append("status = %s")
                params.append(status)
            if severity:
                conditions.append("severity = %s")
                params.append(severity)
            if pass_number:
                conditions.append("pass_number = %s")
                params.append(pass_number)
            if source_file:
                conditions.append("(source_file = %s OR target_file = %s)")
                params.extend([source_file, source_file])
            if conflict_type:
                conditions.append("conflict_type = %s")
                params.append(conflict_type)
            
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM conflict_ledger 
                    {where}
                    ORDER BY 
                        CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                        detected_at DESC
                    LIMIT %s
                """, params + [limit])
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"[ConflictLedger] Query error: {e}")
            return []
        finally:
            self.disconnect()
    
    def get_conflict_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the conflict ledger."""
        if not self.connect():
            return {}
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE status = 'unresolved') as unresolved,
                        COUNT(*) FILTER (WHERE status = 'resolved') as resolved,
                        COUNT(*) FILTER (WHERE status = 'accepted_tension') as accepted,
                        COUNT(*) FILTER (WHERE status = 'false_positive') as false_positives,
                        COUNT(*) FILTER (WHERE severity = 'critical') as critical,
                        COUNT(*) FILTER (WHERE severity = 'warning') as warnings,
                        COUNT(*) FILTER (WHERE severity = 'note') as notes,
                        COUNT(*) FILTER (WHERE pass_number = 1) as pass_1,
                        COUNT(*) FILTER (WHERE pass_number = 2) as pass_2,
                        COUNT(*) FILTER (WHERE pass_number = 3) as pass_3
                    FROM conflict_ledger
                """)
                row = cur.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            print(f"[ConflictLedger] Summary error: {e}")
            return {}
        finally:
            self.disconnect()
    
    # =========================================================================
    # MATH INDEX
    # =========================================================================
    
    def record_equation(self, entry: MathEntry) -> Optional[int]:
        """Record an equation. Deduplicates by hash + source_file."""
        if not self.connect():
            return None
        
        normalized = ' '.join(entry.latex.split())
        latex_hash = hashlib.sha256(normalized.encode()).hexdigest()
        
        try:
            with self.conn.cursor() as cur:
                # Check if this exact equation from this file already exists
                cur.execute("""
                    SELECT id, occurrence_count FROM math_index 
                    WHERE latex_hash = %s AND source_file = %s
                """, (latex_hash, entry.source_file))
                existing = cur.fetchone()
                
                if existing:
                    cur.execute("""
                        UPDATE math_index 
                        SET occurrence_count = occurrence_count + 1,
                            last_seen = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (existing[0],))
                    self.conn.commit()
                    return existing[0]
                else:
                    cur.execute("""
                        INSERT INTO math_index (
                            latex, latex_normalized, latex_hash,
                            source_file, axiom_id, section_header,
                            context_before, context_after,
                            variables, equation_type, display_type
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        entry.latex, normalized, latex_hash,
                        entry.source_file, entry.axiom_id or None,
                        entry.section_header or None,
                        entry.context_before or None, entry.context_after or None,
                        json.dumps(entry.variables),
                        entry.equation_type, entry.display_type
                    ))
                    result = cur.fetchone()
                    self.conn.commit()
                    return result[0] if result else None
        except Exception as e:
            print(f"[ConflictLedger] Equation error: {e}")
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            self.disconnect()
    
    def get_equations(self, source_file: str = None, axiom_id: str = None,
                      equation_type: str = None) -> List[Dict]:
        """Query math index with optional filters."""
        if not self.connect():
            return []
        
        try:
            conditions = []
            params = []
            
            if source_file:
                conditions.append("source_file = %s")
                params.append(source_file)
            if axiom_id:
                conditions.append("axiom_id = %s")
                params.append(axiom_id)
            if equation_type:
                conditions.append("equation_type = %s")
                params.append(equation_type)
            
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT * FROM math_index {where}
                    ORDER BY source_file, id
                """, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"[ConflictLedger] Equation query error: {e}")
            return []
        finally:
            self.disconnect()
    
    # =========================================================================
    # CLAIMS
    # =========================================================================
    
    def record_claim(self, claim: ExtractedClaim) -> Optional[int]:
        """Record an extracted claim."""
        if not self.connect():
            return None
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO extracted_claims (
                        source_file, claim_text, claim_type, section_header,
                        line_number, axiom_id, variables_referenced, extracted_by
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    claim.source_file, claim.claim_text,
                    claim.claim_type, claim.section_header or None,
                    claim.line_number or None, claim.axiom_id or None,
                    json.dumps(claim.variables_referenced),
                    claim.extracted_by
                ))
                result = cur.fetchone()
                self.conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"[ConflictLedger] Claim error: {e}")
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            self.disconnect()
    
    def get_claims(self, source_file: str = None, axiom_id: str = None,
                   claim_type: str = None) -> List[Dict]:
        """Query extracted claims."""
        if not self.connect():
            return []
        
        try:
            conditions = []
            params = []
            
            if source_file:
                conditions.append("source_file = %s")
                params.append(source_file)
            if axiom_id:
                conditions.append("axiom_id = %s")
                params.append(axiom_id)
            if claim_type:
                conditions.append("claim_type = %s")
                params.append(claim_type)
            
            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f"SELECT * FROM extracted_claims {where} ORDER BY source_file, line_number", params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"[ConflictLedger] Claims query error: {e}")
            return []
        finally:
            self.disconnect()
    
    # =========================================================================
    # SCAN HISTORY
    # =========================================================================
    
    def start_scan(self, scan_type: str, target_path: str, model_used: str = "") -> Optional[int]:
        """Record the start of a scan. Returns scan ID."""
        if not self.connect():
            return None
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO scan_history (scan_type, target_path, model_used, status)
                    VALUES (%s, %s, %s, 'running')
                    RETURNING id
                """, (scan_type, target_path, model_used or None))
                result = cur.fetchone()
                self.conn.commit()
                return result[0] if result else None
        except Exception as e:
            print(f"[ConflictLedger] Scan start error: {e}")
            if self.conn:
                self.conn.rollback()
            return None
        finally:
            self.disconnect()
    
    def complete_scan(self, scan_id: int, files_scanned: int = 0,
                      conflicts_found: int = 0, claims_extracted: int = 0,
                      equations_found: int = 0, duration_seconds: float = 0,
                      error_message: str = None) -> bool:
        """Record scan completion."""
        if not self.connect():
            return False
        
        status = 'failed' if error_message else 'completed'
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE scan_history SET
                        files_scanned = %s, conflicts_found = %s,
                        claims_extracted = %s, equations_found = %s,
                        duration_seconds = %s, status = %s,
                        error_message = %s, completed_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    files_scanned, conflicts_found, claims_extracted,
                    equations_found, duration_seconds, status,
                    error_message, scan_id
                ))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"[ConflictLedger] Scan complete error: {e}")
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            self.disconnect()
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        result = self.connect()
        if result:
            self.disconnect()
        return result
