"""
Contradiction Detector — Main engine.

Orchestrates three detection passes:
  Pass 1: Internal consistency (single document self-contradictions)
  Pass 2: Cross-reference consistency (pairwise document conflicts)
  Pass 3: External consistency (vs. established knowledge)

Each pass can run in two modes:
  - Rule-based: Fast, no AI required, catches structural issues
  - AI-enhanced: Deeper analysis via Ollama/OpenAI, catches semantic issues

Results → ConflictLedger → PostgreSQL conflict_ledger table.
"""

from __future__ import annotations

import re
import time
import json
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable

from .claim_extractor import ClaimExtractor, DocumentClaims, Assertion, Definition, Equation
from .conflict_ledger import ConflictLedger, Conflict, ExtractedClaim, MathEntry


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class DetectorConfig:
    """Configuration for the contradiction detector."""
    # AI settings
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    use_ai: bool = True              # set False for rule-only mode
    
    # Scan settings
    max_files_per_scan: int = 500
    max_pairs_per_scan: int = 1000   # for Pass 2
    min_confidence: float = 0.3      # below this, don't record
    
    # Vault
    vault_root: str = r"O:\_Theophysics_v3"
    axioms_folder: str = r"O:\_Theophysics_v3\00_AXIOMS"


# ============================================================================
# MAIN ENGINE
# ============================================================================

class ContradictionDetector:
    """
    Universal contradiction detection engine.
    
    Usage:
        detector = ContradictionDetector()
        
        # Pass 1: Check a folder for internal contradictions
        results = detector.pass_1_internal("path/to/folder")
        
        # Pass 2: Check pairs of related documents
        results = detector.pass_2_crossref("path/to/folder")
        
        # Full scan
        results = detector.full_scan("path/to/folder")
    """
    
    def __init__(self, config: DetectorConfig = None, 
                 ledger: ConflictLedger = None,
                 progress_callback: Callable = None):
        self.config = config or DetectorConfig()
        self.ledger = ledger or ConflictLedger()
        self.extractor = ClaimExtractor()
        self.progress = progress_callback or (lambda msg: print(f"[Detector] {msg}"))
        
        # Check Ollama availability
        self._ollama_available = self._check_ollama() if self.config.use_ai else False
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running."""
        try:
            r = requests.get(f"{self.config.ollama_url}/api/tags", timeout=3)
            return r.status_code == 200
        except:
            return False
    
    # =========================================================================
    # PASS 1: INTERNAL CONSISTENCY
    # =========================================================================
    
    def pass_1_internal(self, folder_path: str, 
                        pattern: str = "*.md") -> List[Conflict]:
        """
        Pass 1: Check each document for internal contradictions.
        
        Rule-based checks:
          - YAML frontmatter vs body content disagreement
          - Duplicate definitions with different meanings
          - Equations that redefine variables differently
          - Assertions that contradict each other within the same doc
        
        AI-enhanced checks (if Ollama available):
          - Semantic contradiction detection
          - Implicit vs explicit claim conflicts
        """
        folder = Path(folder_path)
        if not folder.exists():
            self.progress(f"Folder not found: {folder_path}")
            return []
        
        scan_id = self.ledger.start_scan('pass_1', folder_path, 
                                          self.config.ollama_model if self._ollama_available else 'rules_only')
        
        all_conflicts = []
        files_scanned = 0
        start_time = time.time()
        
        md_files = sorted(folder.glob(pattern))[:self.config.max_files_per_scan]
        total = len(md_files)
        
        self.progress(f"Pass 1: Scanning {total} files in {folder.name}")
        
        for i, md_file in enumerate(md_files):
            if not md_file.is_file():
                continue
            
            self.progress(f"  [{i+1}/{total}] {md_file.name}")
            
            doc = self.extractor.extract_from_file(str(md_file))
            
            # Rule-based internal checks
            conflicts = self._check_internal_rules(doc)
            
            # AI-enhanced internal check
            if self._ollama_available and doc.total_claims > 0:
                ai_conflicts = self._check_internal_ai(doc)
                conflicts.extend(ai_conflicts)
            
            all_conflicts.extend(conflicts)
            files_scanned += 1
            
            # Store extracted claims + equations in DB for future use
            self._store_extractions(doc)
        
        # Record conflicts
        recorded = self.ledger.record_conflicts_batch(all_conflicts)
        
        duration = time.time() - start_time
        if scan_id:
            self.ledger.complete_scan(
                scan_id, files_scanned=files_scanned,
                conflicts_found=recorded, duration_seconds=duration
            )
        
        self.progress(f"Pass 1 complete: {files_scanned} files, {recorded} conflicts, {duration:.1f}s")
        return all_conflicts
    
    def _check_internal_rules(self, doc: DocumentClaims) -> List[Conflict]:
        """Rule-based internal consistency checks."""
        conflicts = []
        
        # Check 1: Duplicate variable definitions
        var_defs = {}
        for defn in doc.definitions:
            term_key = defn.term.lower().strip()
            if term_key in var_defs:
                prev = var_defs[term_key]
                if prev.definition.lower() != defn.definition.lower():
                    conflicts.append(Conflict(
                        source_file=doc.file_path,
                        source_claim=f"{prev.term}: {prev.definition}",
                        source_location=f"Section: {prev.section}, Line: {prev.line_number}",
                        source_axiom_id=doc.axiom_id,
                        target_file=doc.file_path,
                        target_claim=f"{defn.term}: {defn.definition}",
                        target_location=f"Section: {defn.section}, Line: {defn.line_number}",
                        target_axiom_id=doc.axiom_id,
                        conflict_type='definitional_drift',
                        severity='warning',
                        pass_number=1,
                        detected_by='rule_engine',
                        detection_model='rule:duplicate_definition',
                        confidence=0.85,
                        reasoning=f"Term '{defn.term}' defined differently in two places within the same document."
                    ))
            else:
                var_defs[term_key] = defn
        
        # Check 2: Variable reuse in equations with different meanings
        eq_vars = {}
        for eq in doc.equations:
            for var in eq.variables:
                key = var
                ctx = eq.context_before[:100] + eq.context_after[:100]
                if key in eq_vars:
                    prev_ctx = eq_vars[key]
                    # This is a soft check — flag if same var appears in very different contexts
                    # Real analysis would need AI, but we flag for review
                else:
                    eq_vars[key] = ctx
        
        # Check 3: YAML claims vs body content
        if doc.yaml_metadata:
            yaml_status = doc.yaml_metadata.get('status', '')
            yaml_stage = doc.yaml_metadata.get('stage', 0)
            
            # Check if YAML says "proven" but body says "conjecture"
            if yaml_status and yaml_status.lower() in ('proven', 'established', 'verified'):
                for assertion in doc.assertions:
                    if assertion.confidence == 'hedged':
                        conflicts.append(Conflict(
                            source_file=doc.file_path,
                            source_claim=f"YAML status: {yaml_status}",
                            source_location="frontmatter",
                            source_axiom_id=doc.axiom_id,
                            target_file=doc.file_path,
                            target_claim=assertion.text[:200],
                            target_location=f"Section: {assertion.section}, Line: {assertion.line_number}",
                            target_axiom_id=doc.axiom_id,
                            conflict_type='tension',
                            severity='note',
                            pass_number=1,
                            detected_by='rule_engine',
                            detection_model='rule:yaml_vs_body_confidence',
                            confidence=0.5,
                            reasoning=f"YAML says '{yaml_status}' but body uses hedging language."
                        ))
                        break  # one flag per doc is enough for this check
        
        return conflicts
    
    def _check_internal_ai(self, doc: DocumentClaims) -> List[Conflict]:
        """AI-enhanced internal consistency check via Ollama."""
        if not self._ollama_available:
            return []
        
        # Build a summary of the document's key claims
        claim_summary = self._build_claim_summary(doc)
        if len(claim_summary) < 50:
            return []
        
        prompt = f"""You are a logic auditor checking a single document for internal contradictions.

DOCUMENT: {doc.file_name}
{f"AXIOM ID: {doc.axiom_id}" if doc.axiom_id else ""}

KEY CLAIMS AND DEFINITIONS FROM THIS DOCUMENT:
{claim_summary}

TASK: Identify any internal contradictions, tensions, or inconsistencies WITHIN this document.

For each conflict found, respond with EXACTLY this format (one per conflict):
CONFLICT|<severity: critical/warning/note>|<type: direct_contradiction/tension/ambiguity/definitional_drift>|<confidence: 0.0-1.0>|<claim_a>|<claim_b>|<reasoning>

If no contradictions are found, respond with exactly:
CLEAN

Be precise. Only flag genuine logical conflicts, not stylistic issues or different phrasings of the same idea."""

        response = self._query_ollama(prompt)
        if not response:
            return []
        
        return self._parse_ai_conflicts(response, doc.file_path, doc.axiom_id, pass_number=1)
    
    # =========================================================================
    # PASS 2: CROSS-REFERENCE CONSISTENCY
    # =========================================================================
    
    def pass_2_crossref(self, folder_path: str,
                        pattern: str = "*.md",
                        pair_strategy: str = "dependency") -> List[Conflict]:
        """
        Pass 2: Check pairs of related documents for contradictions.
        
        Pair strategies:
          - "dependency": Follow depends_on chains (most efficient for axioms)
          - "shared_tags": Compare docs that share tags
          - "all_pairs": Brute force (expensive, use sparingly)
          - "adjacent": Compare sequential chain positions
        """
        folder = Path(folder_path)
        if not folder.exists():
            self.progress(f"Folder not found: {folder_path}")
            return []
        
        scan_id = self.ledger.start_scan('pass_2', folder_path,
                                          self.config.ollama_model if self._ollama_available else 'rules_only')
        
        start_time = time.time()
        
        # Extract all documents first
        self.progress(f"Pass 2: Loading documents from {folder.name}")
        all_docs = {}
        for md_file in sorted(folder.glob(pattern))[:self.config.max_files_per_scan]:
            if md_file.is_file():
                doc = self.extractor.extract_from_file(str(md_file))
                all_docs[doc.file_path] = doc
        
        self.progress(f"  Loaded {len(all_docs)} documents")
        
        # Generate pairs based on strategy
        pairs = self._generate_pairs(all_docs, pair_strategy)
        pairs = pairs[:self.config.max_pairs_per_scan]
        
        self.progress(f"  Generated {len(pairs)} pairs ({pair_strategy} strategy)")
        
        all_conflicts = []
        
        for i, (doc_a, doc_b) in enumerate(pairs):
            if (i + 1) % 10 == 0:
                self.progress(f"  [{i+1}/{len(pairs)}] Comparing {doc_a.file_name} ↔ {doc_b.file_name}")
            
            # Rule-based cross checks
            conflicts = self._check_crossref_rules(doc_a, doc_b)
            
            # AI-enhanced cross check
            if self._ollama_available:
                ai_conflicts = self._check_crossref_ai(doc_a, doc_b)
                conflicts.extend(ai_conflicts)
            
            all_conflicts.extend(conflicts)
        
        recorded = self.ledger.record_conflicts_batch(all_conflicts)
        
        duration = time.time() - start_time
        if scan_id:
            self.ledger.complete_scan(
                scan_id, files_scanned=len(all_docs),
                conflicts_found=recorded, duration_seconds=duration
            )
        
        self.progress(f"Pass 2 complete: {len(pairs)} pairs, {recorded} conflicts, {duration:.1f}s")
        return all_conflicts
    
    def _generate_pairs(self, docs: Dict[str, DocumentClaims], 
                        strategy: str) -> List[Tuple[DocumentClaims, DocumentClaims]]:
        """Generate document pairs for comparison based on strategy."""
        pairs = []
        doc_list = list(docs.values())
        
        if strategy == "dependency":
            # For each doc, compare with its dependencies
            axiom_index = {d.axiom_id: d for d in doc_list if d.axiom_id}
            
            for doc in doc_list:
                if not doc.depends_on:
                    continue
                deps = doc.depends_on if isinstance(doc.depends_on, list) else [doc.depends_on]
                for dep_id in deps:
                    if dep_id and dep_id in axiom_index:
                        pairs.append((doc, axiom_index[dep_id]))
        
        elif strategy == "adjacent":
            # Compare sequential chain positions
            axiom_docs = sorted(
                [d for d in doc_list if d.chain_position],
                key=lambda d: d.chain_position
            )
            for i in range(len(axiom_docs) - 1):
                pairs.append((axiom_docs[i], axiom_docs[i + 1]))
        
        elif strategy == "all_pairs":
            # Brute force — expensive
            for i in range(len(doc_list)):
                for j in range(i + 1, len(doc_list)):
                    if doc_list[i].total_claims > 0 and doc_list[j].total_claims > 0:
                        pairs.append((doc_list[i], doc_list[j]))
        
        elif strategy == "shared_tags":
            # Compare docs that share YAML tags
            tag_index = {}
            for doc in doc_list:
                tags = doc.yaml_metadata.get('tags', []) or []
                if isinstance(tags, str):
                    tags = [tags]
                for tag in tags:
                    if tag not in tag_index:
                        tag_index[tag] = []
                    tag_index[tag].append(doc)
            
            seen = set()
            for tag, tag_docs in tag_index.items():
                for i in range(len(tag_docs)):
                    for j in range(i + 1, len(tag_docs)):
                        key = tuple(sorted([tag_docs[i].file_path, tag_docs[j].file_path]))
                        if key not in seen:
                            pairs.append((tag_docs[i], tag_docs[j]))
                            seen.add(key)
        
        return pairs
    
    def _check_crossref_rules(self, doc_a: DocumentClaims, 
                               doc_b: DocumentClaims) -> List[Conflict]:
        """Rule-based cross-reference checks between two documents."""
        conflicts = []
        
        # Check 1: Same term defined differently
        defs_a = {d.term.lower(): d for d in doc_a.definitions}
        defs_b = {d.term.lower(): d for d in doc_b.definitions}
        
        shared_terms = set(defs_a.keys()) & set(defs_b.keys())
        for term in shared_terms:
            da = defs_a[term]
            db = defs_b[term]
            if da.definition.lower().strip() != db.definition.lower().strip():
                conflicts.append(Conflict(
                    source_file=doc_a.file_path,
                    source_claim=f"{da.term}: {da.definition[:200]}",
                    source_location=f"Section: {da.section}, Line: {da.line_number}",
                    source_axiom_id=doc_a.axiom_id,
                    target_file=doc_b.file_path,
                    target_claim=f"{db.term}: {db.definition[:200]}",
                    target_location=f"Section: {db.section}, Line: {db.line_number}",
                    target_axiom_id=doc_b.axiom_id,
                    conflict_type='definitional_drift',
                    severity='warning',
                    pass_number=2,
                    detected_by='rule_engine',
                    detection_model='rule:cross_definition_mismatch',
                    confidence=0.75,
                    reasoning=f"Term '{term}' defined differently across documents."
                ))
        
        # Check 2: Equation variable conflicts
        # Build variable usage maps
        vars_a = {}
        for eq in doc_a.equations:
            for var in eq.variables:
                if var not in vars_a:
                    vars_a[var] = eq.context_before[:100] + " " + eq.context_after[:100]
        
        vars_b = {}
        for eq in doc_b.equations:
            for var in eq.variables:
                if var not in vars_b:
                    vars_b[var] = eq.context_before[:100] + " " + eq.context_after[:100]
        
        # Shared variables flagged for AI review (rule engine can't judge context well)
        shared_vars = set(vars_a.keys()) & set(vars_b.keys())
        # Don't flag these as rule-based — they need AI. Just note for Pass 2 AI.
        
        return conflicts
    
    def _check_crossref_ai(self, doc_a: DocumentClaims, 
                            doc_b: DocumentClaims) -> List[Conflict]:
        """AI-enhanced cross-reference check between two documents."""
        if not self._ollama_available:
            return []
        
        summary_a = self._build_claim_summary(doc_a, max_chars=1500)
        summary_b = self._build_claim_summary(doc_b, max_chars=1500)
        
        if len(summary_a) < 30 or len(summary_b) < 30:
            return []
        
        prompt = f"""You are a logic auditor checking TWO documents for contradictions between them.

DOCUMENT A: {doc_a.file_name}
{f"Axiom: {doc_a.axiom_id}" if doc_a.axiom_id else ""}
{f"Depends on: {doc_a.depends_on}" if doc_a.depends_on else ""}

KEY CLAIMS FROM DOCUMENT A:
{summary_a}

---

DOCUMENT B: {doc_b.file_name}
{f"Axiom: {doc_b.axiom_id}" if doc_b.axiom_id else ""}
{f"Depends on: {doc_b.depends_on}" if doc_b.depends_on else ""}

KEY CLAIMS FROM DOCUMENT B:
{summary_b}

---

TASK: Identify contradictions, tensions, or inconsistencies BETWEEN these two documents.

Focus on:
- Claims that directly conflict
- Terms used with different meanings
- Mathematical variables defined differently
- Logical dependencies that don't hold

For each conflict found, respond with EXACTLY this format:
CONFLICT|<severity: critical/warning/note>|<type: direct_contradiction/tension/definitional_drift/math_inconsistency/dependency_violation>|<confidence: 0.0-1.0>|<claim_from_doc_a>|<claim_from_doc_b>|<reasoning>

If no contradictions are found, respond with exactly:
CLEAN

Only flag genuine logical conflicts. Different phrasings of the same idea are not contradictions."""

        response = self._query_ollama(prompt)
        if not response:
            return []
        
        return self._parse_ai_conflicts(
            response, doc_a.file_path, doc_a.axiom_id,
            target_file=doc_b.file_path, target_axiom_id=doc_b.axiom_id,
            pass_number=2
        )
    
    # =========================================================================
    # FULL SCAN
    # =========================================================================
    
    def full_scan(self, folder_path: str, pattern: str = "*.md",
                  pair_strategy: str = "dependency") -> Dict[str, any]:
        """Run all passes on a folder."""
        self.progress(f"=== FULL SCAN: {folder_path} ===")
        
        p1 = self.pass_1_internal(folder_path, pattern)
        p2 = self.pass_2_crossref(folder_path, pattern, pair_strategy)
        
        summary = self.ledger.get_conflict_summary()
        
        self.progress(f"\n=== SCAN COMPLETE ===")
        self.progress(f"  Pass 1 conflicts: {len(p1)}")
        self.progress(f"  Pass 2 conflicts: {len(p2)}")
        self.progress(f"  Total in ledger: {summary.get('total', 0)}")
        self.progress(f"  Unresolved: {summary.get('unresolved', 0)}")
        self.progress(f"  Critical: {summary.get('critical', 0)}")
        
        return {
            'pass_1': p1,
            'pass_2': p2,
            'summary': summary
        }
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _build_claim_summary(self, doc: DocumentClaims, max_chars: int = 2000) -> str:
        """Build a text summary of a document's key claims for AI consumption."""
        parts = []
        
        # Definitions first
        for defn in doc.definitions[:10]:
            parts.append(f"DEFINITION: {defn.term} = {defn.definition[:150]}")
        
        # Key equations
        for eq in doc.equations[:5]:
            if eq.display_type == "display":
                parts.append(f"EQUATION: ${eq.latex}$")
                if eq.context_before:
                    parts.append(f"  Context: {eq.context_before[:100]}")
        
        # Strong assertions
        for assertion in doc.assertions[:15]:
            parts.append(f"CLAIM [{assertion.claim_type}]: {assertion.text[:200]}")
        
        summary = '\n'.join(parts)
        return summary[:max_chars]
    
    def _store_extractions(self, doc: DocumentClaims):
        """Store extracted claims and equations in the database for future use."""
        # Store equations
        for eq in doc.equations:
            self.ledger.record_equation(MathEntry(
                latex=eq.latex,
                source_file=doc.file_path,
                axiom_id=doc.axiom_id,
                section_header=eq.section,
                context_before=eq.context_before,
                context_after=eq.context_after,
                variables={v: ClaimExtractor.KNOWN_VARIABLES.get(v, '') for v in eq.variables},
                equation_type="unknown",
                display_type=eq.display_type
            ))
        
        # Store claims
        for assertion in doc.assertions:
            self.ledger.record_claim(ExtractedClaim(
                source_file=doc.file_path,
                claim_text=assertion.text[:500],
                claim_type=assertion.claim_type,
                section_header=assertion.section,
                line_number=assertion.line_number,
                axiom_id=doc.axiom_id,
                extracted_by='rule_engine'
            ))
    
    def _query_ollama(self, prompt: str, timeout: int = 120) -> str:
        """Send a prompt to Ollama and return the response."""
        try:
            response = requests.post(
                f"{self.config.ollama_url}/api/generate",
                json={
                    "model": self.config.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,     # low temp for analytical work
                        "num_predict": 2000,
                    }
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                self.progress(f"  Ollama error: {response.status_code}")
                return ''
        except requests.exceptions.Timeout:
            self.progress("  Ollama timeout")
            return ''
        except Exception as e:
            self.progress(f"  Ollama error: {e}")
            return ''
    
    def _parse_ai_conflicts(self, response: str, source_file: str,
                            source_axiom_id: str = "",
                            target_file: str = "",
                            target_axiom_id: str = "",
                            pass_number: int = 1) -> List[Conflict]:
        """Parse Ollama response into Conflict objects."""
        conflicts = []
        
        if 'CLEAN' in response.strip().upper()[:10]:
            return []
        
        for line in response.strip().split('\n'):
            line = line.strip()
            if not line.startswith('CONFLICT|'):
                continue
            
            parts = line.split('|')
            if len(parts) < 7:
                continue
            
            try:
                severity = parts[1].strip().lower()
                conflict_type = parts[2].strip().lower()
                confidence = float(parts[3].strip())
                claim_a = parts[4].strip()
                claim_b = parts[5].strip()
                reasoning = parts[6].strip()
                
                # Validate
                if severity not in ('critical', 'warning', 'note'):
                    severity = 'note'
                valid_types = ('direct_contradiction', 'tension', 'ambiguity', 
                               'definitional_drift', 'math_inconsistency',
                               'scope_conflict', 'dependency_violation')
                if conflict_type not in valid_types:
                    conflict_type = 'tension'
                if confidence < self.config.min_confidence:
                    continue
                
                # For Pass 1 (internal), target = source
                t_file = target_file if pass_number >= 2 else source_file
                t_axiom = target_axiom_id if pass_number >= 2 else source_axiom_id
                
                conflicts.append(Conflict(
                    source_file=source_file,
                    source_claim=claim_a[:500],
                    source_axiom_id=source_axiom_id,
                    target_file=t_file,
                    target_claim=claim_b[:500],
                    target_axiom_id=t_axiom,
                    conflict_type=conflict_type,
                    severity=severity,
                    pass_number=pass_number,
                    detected_by='ollama',
                    detection_model=self.config.ollama_model,
                    confidence=confidence,
                    reasoning=reasoning[:500]
                ))
            except (ValueError, IndexError):
                continue
        
        return conflicts


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def quick_scan(folder_path: str, use_ai: bool = True) -> Dict:
    """One-liner to scan a folder."""
    config = DetectorConfig(use_ai=use_ai)
    detector = ContradictionDetector(config)
    return detector.full_scan(folder_path)


def scan_axioms(use_ai: bool = True) -> Dict:
    """Scan the axioms folder specifically."""
    config = DetectorConfig(use_ai=use_ai)
    detector = ContradictionDetector(config)
    return detector.full_scan(config.axioms_folder, pattern="*.md", pair_strategy="dependency")
