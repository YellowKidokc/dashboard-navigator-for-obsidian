"""
Web Weaver - Automated Wiki-Link Generator for Obsidian Axiom Files

Scans axiom files and converts plain-text references to [[wiki-links]].
Creates a tangled web of interconnected notes.
"""

from __future__ import annotations

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
import json


@dataclass
class AxiomFile:
    """Represents an axiom file with its metadata."""
    path: Path
    filename: str
    id: str  # e.g., "A1.1", "O2.3", "BC7.1"
    title: str  # e.g., "Existence", "Self-Grounding"
    content: str
    existing_links: Set[str] = field(default_factory=set)


@dataclass
class LinkSuggestion:
    """A suggested link to add."""
    file_path: Path
    line_number: int
    original_text: str
    suggested_link: str
    target_file: str
    context: str  # surrounding text for preview


class WebWeaver:
    """Engine for weaving wiki-links between axiom files."""

    # Patterns for axiom IDs (e.g., A1.1, O2.3, BC7.1, HC.10, etc.)
    AXIOM_ID_PATTERNS = [
        r'\b(A\d+\.\d+)',           # A1.1, A2.2, A5.1
        r'\b(O\d+\.\d+)',           # O1.1, O2.3, O3.1
        r'\b(BC\d+\.\d+)',          # BC7.1
        r'\b(D\d+\.\d+)',           # D2.1
        r'\b(G\d+\.\d+)',           # G0.1, G1.2
        r'\b(GA\.\d+)',             # GA.1, GA.5
        r'\b(GI\.\d+)',             # GI.1, GI.2
        r'\b(H\d+\.\d+)',           # H0.1
        r'\b(HB\.\d+)',             # HB.1, HB.3
        r'\b(HC\.\d+)',             # HC.1, HC.10
        r'\b(HF\.\d+)',             # HF.1, HF.10
        r'\b(HM\.\d+)',             # HM.1, HM.4
        r'\b(HP\.\d+)',             # HP.1
        r'\b(HS\.\d+)',             # HS.1
        r'\b(HO\.\d+)',             # HO.1
        r'\b(M\d+\.\d+)',           # M0.1
        r'\b(ME\.\d+)',             # ME.1
        r'\b(MG\.\d+)',             # MG.1
        r'\b(MQ\.\d+)',             # MQ.1
        r'\b(MS\.\d+)',             # MS.1
        r'\b(R\d+\.\d+)',           # R1.1
        r'\b(S\d+\.\d+)',           # S0.1
        r'\b(SA\.\d+)',             # SA.1
        r'\b(SD\.\d+)',             # SD.1
        r'\b(SP\.\d+)',             # SP.1
        r'\b(T\d+\.\d+)',           # T0.0, T1.1
        r'\b(L\d+\.\d+)',           # L2.0, L4.1
        r'\b(AX-\d+)',              # AX-128, AX-138
        r'\b(P\d+\.\d+)',           # P0.1
    ]

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path
        self.axiom_files: Dict[str, AxiomFile] = {}  # id -> AxiomFile
        self.filename_map: Dict[str, str] = {}  # filename (no ext) -> id
        self.suggestions: List[LinkSuggestion] = []

    def set_vault_path(self, path: Path) -> None:
        """Set the vault path and scan for axiom files."""
        self.vault_path = path
        self.scan_axiom_files()

    def scan_axiom_files(self) -> int:
        """Scan vault for axiom files and build the index."""
        if not self.vault_path or not self.vault_path.exists():
            return 0

        self.axiom_files.clear()
        self.filename_map.clear()

        # Find all markdown files
        md_files = list(self.vault_path.glob("*.md"))

        for md_file in md_files:
            axiom = self._parse_axiom_file(md_file)
            if axiom and axiom.id:
                self.axiom_files[axiom.id] = axiom
                self.filename_map[axiom.filename] = axiom.id

        return len(self.axiom_files)

    def _parse_axiom_file(self, file_path: Path) -> Optional[AxiomFile]:
        """Parse an axiom file and extract metadata."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return None

        filename = file_path.stem  # filename without extension

        # Extract ID from frontmatter or filename
        axiom_id = self._extract_id(content, filename)
        title = self._extract_title(content, filename)
        existing_links = self._find_existing_links(content)

        return AxiomFile(
            path=file_path,
            filename=filename,
            id=axiom_id,
            title=title,
            content=content,
            existing_links=existing_links
        )

    def _extract_id(self, content: str, filename: str) -> str:
        """Extract axiom ID from frontmatter or filename."""
        # Try frontmatter first
        id_match = re.search(r'^id:\s*([A-Z0-9\.\-]+)', content, re.MULTILINE | re.IGNORECASE)
        if id_match:
            return id_match.group(1)

        # Try filename patterns
        for pattern in self.AXIOM_ID_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)

        # Return filename as fallback
        return filename

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract title from frontmatter or filename."""
        # Try frontmatter
        title_match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # Try first H1 heading
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        # Parse from filename (e.g., "A1.1-Existence" -> "Existence")
        parts = filename.split('-', 1)
        if len(parts) > 1:
            return parts[1].replace('-', ' ').replace('_', ' ')

        return filename

    def _find_existing_links(self, content: str) -> Set[str]:
        """Find all existing [[wiki-links]] in content."""
        links = set()
        # Match [[link]] and [[link|alias]]
        for match in re.finditer(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content):
            links.add(match.group(1))
        return links

    def find_link_opportunities(self, file_path: Optional[Path] = None) -> List[LinkSuggestion]:
        """Find opportunities to add links in files."""
        self.suggestions.clear()

        files_to_scan = []
        if file_path:
            files_to_scan = [file_path]
        else:
            files_to_scan = [af.path for af in self.axiom_files.values()]

        for fp in files_to_scan:
            self._scan_file_for_opportunities(fp)

        return self.suggestions

    def _scan_file_for_opportunities(self, file_path: Path) -> None:
        """Scan a single file for linking opportunities."""
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception:
            return

        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Skip frontmatter
            if line.startswith('---'):
                continue
            # Skip lines that are already links
            if '[[' in line and ']]' in line:
                # Still check for unlinked references on same line
                pass

            # Find axiom ID references that aren't already linked
            for pattern in self.AXIOM_ID_PATTERNS:
                for match in re.finditer(pattern, line):
                    axiom_id = match.group(1)

                    # Check if this ID exists in our index
                    if axiom_id not in self.axiom_files:
                        continue

                    # Check if it's already a wiki-link
                    # Look for [[axiom_id or [[filename containing axiom_id
                    start_pos = match.start()

                    # Check if preceded by [[ within 50 chars
                    preceding = line[max(0, start_pos-50):start_pos]
                    if '[[' in preceding and ']]' not in preceding:
                        continue  # Already inside a link

                    # Check if this exact match is inside [[...]]
                    check_start = max(0, start_pos - 2)
                    check_end = min(len(line), match.end() + 2)
                    surrounding = line[check_start:check_end]
                    if surrounding.startswith('[[') or '[[' in line[max(0,start_pos-30):start_pos]:
                        # Check if there's a ]] before us
                        before = line[max(0,start_pos-50):start_pos]
                        if '[[' in before:
                            last_open = before.rfind('[[')
                            last_close = before.rfind(']]')
                            if last_open > last_close:
                                continue  # We're inside a link

                    # Get target filename
                    target = self.axiom_files[axiom_id]
                    target_filename = target.filename

                    # Don't suggest linking to self
                    if file_path.stem == target_filename:
                        continue

                    # Create suggestion
                    context_start = max(0, start_pos - 30)
                    context_end = min(len(line), match.end() + 30)
                    context = line[context_start:context_end]
                    if context_start > 0:
                        context = "..." + context
                    if context_end < len(line):
                        context = context + "..."

                    suggestion = LinkSuggestion(
                        file_path=file_path,
                        line_number=line_num,
                        original_text=axiom_id,
                        suggested_link=f"[[{target_filename}|{axiom_id}]]",
                        target_file=target_filename,
                        context=context
                    )
                    self.suggestions.append(suggestion)

    def apply_suggestions(self, suggestions: List[LinkSuggestion]) -> Dict[Path, int]:
        """Apply selected suggestions to files."""
        changes_per_file: Dict[Path, int] = {}

        # Group suggestions by file
        by_file: Dict[Path, List[LinkSuggestion]] = {}
        for s in suggestions:
            if s.file_path not in by_file:
                by_file[s.file_path] = []
            by_file[s.file_path].append(s)

        for file_path, file_suggestions in by_file.items():
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content

                # Sort by line number descending to avoid offset issues
                file_suggestions.sort(key=lambda x: x.line_number, reverse=True)

                lines = content.split('\n')

                for suggestion in file_suggestions:
                    line_idx = suggestion.line_number - 1
                    if 0 <= line_idx < len(lines):
                        line = lines[line_idx]
                        # Replace the first occurrence of the original text that isn't already linked
                        # Be careful to not break existing links
                        new_line = self._safe_replace(line, suggestion.original_text, suggestion.suggested_link)
                        lines[line_idx] = new_line

                new_content = '\n'.join(lines)

                if new_content != original_content:
                    file_path.write_text(new_content, encoding='utf-8')
                    changes_per_file[file_path] = len(file_suggestions)

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return changes_per_file

    def _safe_replace(self, line: str, original: str, replacement: str) -> str:
        """Safely replace text without breaking existing links."""
        # Find all positions of original text
        result = line
        pos = 0

        while True:
            idx = result.find(original, pos)
            if idx == -1:
                break

            # Check if this occurrence is already inside a link
            before = result[:idx]
            after = result[idx + len(original):]

            # Count [[ and ]] before this position
            open_count = before.count('[[')
            close_count = before.count(']]')

            if open_count > close_count:
                # We're inside a link, skip this occurrence
                pos = idx + len(original)
                continue

            # Check if immediately preceded by [[
            if idx >= 2 and result[idx-2:idx] == '[[':
                pos = idx + len(original)
                continue

            # Safe to replace
            result = result[:idx] + replacement + result[idx + len(original):]
            break  # Only replace first safe occurrence

        return result

    def get_link_stats(self) -> Dict:
        """Get statistics about linking in the vault."""
        total_files = len(self.axiom_files)
        total_links = 0
        unlinked_references = 0

        for axiom in self.axiom_files.values():
            total_links += len(axiom.existing_links)

        # Count potential links
        self.find_link_opportunities()
        unlinked_references = len(self.suggestions)

        return {
            'total_files': total_files,
            'total_existing_links': total_links,
            'unlinked_references': unlinked_references,
            'axiom_ids': list(self.axiom_files.keys())
        }

    def get_connection_map(self) -> Dict[str, List[str]]:
        """Get a map of which files link to which."""
        connections: Dict[str, List[str]] = {}

        for axiom_id, axiom in self.axiom_files.items():
            connections[axiom_id] = []
            for link in axiom.existing_links:
                # Try to match link to an axiom ID
                if link in self.filename_map:
                    target_id = self.filename_map[link]
                    connections[axiom_id].append(target_id)
                elif link in self.axiom_files:
                    connections[axiom_id].append(link)

        return connections

    def generate_mermaid_graph(self, max_nodes: int = 50) -> str:
        """Generate a Mermaid diagram of the link structure."""
        connections = self.get_connection_map()

        lines = ["```mermaid", "graph TD"]

        # Limit nodes for readability
        nodes_shown = set()
        edges_added = 0

        for source, targets in connections.items():
            if len(nodes_shown) >= max_nodes:
                break
            nodes_shown.add(source)

            for target in targets[:5]:  # Limit edges per node
                if target in self.axiom_files:
                    nodes_shown.add(target)
                    # Sanitize IDs for Mermaid (replace dots with underscores)
                    src_safe = source.replace('.', '_').replace('-', '_')
                    tgt_safe = target.replace('.', '_').replace('-', '_')
                    lines.append(f"    {src_safe}[{source}] --> {tgt_safe}[{target}]")
                    edges_added += 1

        lines.append("```")

        if edges_added == 0:
            return "No connections found yet."

        return '\n'.join(lines)
