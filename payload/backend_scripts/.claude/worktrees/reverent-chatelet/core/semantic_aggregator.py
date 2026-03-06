"""
Semantic Aggregator for Theophysics Vault
=========================================
Extracts semantic tags (Axiom, Claim, Concept, Evidence, etc.) from papers
and aggregates them to 07_MASTER_TRUTH/ folders.

Supports:
- LOCAL mode: Per-paper or per-folder analysis
- GLOBAL mode: Vault-wide aggregation with deduplication

Author: David Lowe / Theophysics
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict
import hashlib


@dataclass
class SemanticItem:
    """A semantic tag extracted from the vault."""
    item_type: str  # Axiom, Claim, Concept, Evidence, Relationship, etc.
    uuid: str
    label: str
    parent_uuid: Optional[str]
    source_file: str
    line_number: int
    context: str = ""  # Surrounding text for context
    custom_type: Optional[str] = None
    
    def content_hash(self) -> str:
        """Hash for deduplication by content."""
        return hashlib.md5(f"{self.item_type}:{self.label}".encode()).hexdigest()[:12]


@dataclass
class AggregationResult:
    """Results from semantic aggregation."""
    items_by_type: Dict[str, List[SemanticItem]] = field(default_factory=dict)
    duplicates: List[Tuple[SemanticItem, SemanticItem]] = field(default_factory=list)
    contradictions: List[Tuple[SemanticItem, SemanticItem]] = field(default_factory=list)
    orphaned: List[SemanticItem] = field(default_factory=list)  # Parent UUID not found
    stats: Dict[str, int] = field(default_factory=dict)


class SemanticAggregator:
    """
    Aggregates semantic tags from Obsidian vault files.
    """
    
    # Tag pattern: %%tag::TYPE::UUID::"LABEL"::PARENT%%
    TAG_PATTERN = re.compile(
        r'%%tag::([^:]+)::([a-f0-9\-]+)::"([^"]+)"::([^%]*)%%',
        re.IGNORECASE
    )
    
    # Map tag types to 07_MASTER_TRUTH folders
    TYPE_TO_FOLDER = {
        'Axiom': 'axioms',
        'Claim': 'claims',
        'Concept': 'concepts',
        'Evidence': 'evidence',
        'EvidenceBundle': 'evidence',
        'Relationship': 'coherence',
        'Theory': 'theories',
        'Breakthrough': 'breakthroughs',
        'Timeline': 'timeline',
        'Math': 'math',
        'Progression': 'progression',
    }
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.master_truth_path = self.vault_path / "07_MASTER_TRUTH"
        self.items: List[SemanticItem] = []
        self.items_by_uuid: Dict[str, SemanticItem] = {}
        
    def scan_folder(self, folder_path: Path, recursive: bool = True) -> List[SemanticItem]:
        """Scan a folder for semantic tags."""
        items = []
        pattern = "**/*.md" if recursive else "*.md"
        
        for md_file in folder_path.glob(pattern):
            file_items = self._extract_from_file(md_file)
            items.extend(file_items)
            
        return items
    
    def _extract_from_file(self, file_path: Path) -> List[SemanticItem]:
        """Extract semantic tags from a single file."""
        items = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for match in self.TAG_PATTERN.finditer(line):
                    tag_type = match.group(1)
                    uuid = match.group(2)
                    label = match.group(3)
                    parent_uuid = match.group(4).strip()
                    
                    if parent_uuid.lower() == 'null' or parent_uuid == '':
                        parent_uuid = None
                    
                    # Handle custom types
                    custom_type = None
                    if ':' in tag_type:
                        parts = tag_type.split(':', 1)
                        tag_type = parts[0]
                        custom_type = parts[1]
                    
                    # Get context (surrounding lines)
                    context_start = max(0, line_num - 3)
                    context_end = min(len(lines), line_num + 2)
                    context = '\n'.join(lines[context_start:context_end])
                    
                    try:
                        rel_path = str(file_path.relative_to(self.vault_path))
                    except ValueError:
                        rel_path = str(file_path)
                    
                    item = SemanticItem(
                        item_type=tag_type,
                        uuid=uuid,
                        label=label,
                        parent_uuid=parent_uuid,
                        source_file=rel_path,
                        line_number=line_num,
                        context=context,
                        custom_type=custom_type
                    )
                    items.append(item)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return items
    
    def aggregate_local(self, folder_path: str, output_folder: str = None) -> AggregationResult:
        """
        LOCAL mode: Scan a specific folder and output analytics there.
        Good for per-paper analysis.
        """
        folder = Path(folder_path)
        items = self.scan_folder(folder)
        
        result = self._analyze_items(items)
        
        # Output to _Data_Analytics subfolder or specified output
        if output_folder:
            out_path = Path(output_folder)
        else:
            out_path = folder / "_Data_Analytics"
        
        self._write_local_report(result, out_path, folder.name)
        
        return result
    
    def aggregate_global(self) -> AggregationResult:
        """
        GLOBAL mode: Scan entire vault and aggregate to 07_MASTER_TRUTH.
        Deduplicates across all papers.
        """
        # Scan key folders
        scan_paths = [
            self.vault_path / "03_PUBLICATIONS",
            self.vault_path / "Glossary",
            self.vault_path / "Notes",
        ]
        
        all_items = []
        for scan_path in scan_paths:
            if scan_path.exists():
                items = self.scan_folder(scan_path)
                all_items.extend(items)
                print(f"  Scanned {scan_path.name}: {len(items)} tags")
        
        result = self._analyze_items(all_items)
        
        # Write to 07_MASTER_TRUTH folders
        self._write_global_output(result)
        
        return result
    
    def _analyze_items(self, items: List[SemanticItem]) -> AggregationResult:
        """Analyze items for duplicates, contradictions, orphans."""
        result = AggregationResult()
        
        # Group by type
        by_type: Dict[str, List[SemanticItem]] = defaultdict(list)
        by_uuid: Dict[str, SemanticItem] = {}
        by_label: Dict[str, List[SemanticItem]] = defaultdict(list)
        
        for item in items:
            by_type[item.item_type].append(item)
            by_label[f"{item.item_type}:{item.label}"].append(item)
            
            # Check for UUID duplicates
            if item.uuid in by_uuid:
                existing = by_uuid[item.uuid]
                if existing.label != item.label:
                    # Same UUID, different label = contradiction
                    result.contradictions.append((existing, item))
                else:
                    # Same UUID, same label = duplicate reference
                    result.duplicates.append((existing, item))
            else:
                by_uuid[item.uuid] = item
        
        # Check for orphaned items (parent UUID doesn't exist)
        all_uuids = set(by_uuid.keys())
        for item in items:
            if item.parent_uuid and item.parent_uuid not in all_uuids:
                result.orphaned.append(item)
        
        result.items_by_type = dict(by_type)
        result.stats = {
            'total_items': len(items),
            'unique_items': len(by_uuid),
            'duplicates': len(result.duplicates),
            'contradictions': len(result.contradictions),
            'orphaned': len(result.orphaned),
            **{f'{k}_count': len(v) for k, v in by_type.items()}
        }
        
        return result
    
    def _write_local_report(self, result: AggregationResult, output_path: Path, source_name: str):
        """Write local analytics report."""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Summary markdown
        summary = f"""# Semantic Analysis: {source_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics
| Metric | Count |
|--------|-------|
| Total Tags | {result.stats.get('total_items', 0)} |
| Unique Items | {result.stats.get('unique_items', 0)} |
| Duplicates | {result.stats.get('duplicates', 0)} |
| Contradictions | {result.stats.get('contradictions', 0)} |
| Orphaned | {result.stats.get('orphaned', 0)} |

## By Type
"""
        for item_type, items in result.items_by_type.items():
            summary += f"- **{item_type}**: {len(items)}\n"
        
        # List items by type
        for item_type, items in result.items_by_type.items():
            summary += f"\n## {item_type}s\n"
            for item in items[:50]:  # Limit to 50 per type
                summary += f"- `{item.uuid[:8]}` {item.label}\n"
                if item.parent_uuid:
                    summary += f"  - Parent: `{item.parent_uuid[:8]}`\n"
        
        # Contradictions
        if result.contradictions:
            summary += "\n## ⚠️ Contradictions\n"
            for item1, item2 in result.contradictions:
                summary += f"- UUID `{item1.uuid[:8]}`: \"{item1.label}\" vs \"{item2.label}\"\n"
        
        (output_path / "SEMANTIC_ANALYSIS.md").write_text(summary, encoding='utf-8')
        
        # JSON export
        json_data = {
            'source': source_name,
            'generated': datetime.now().isoformat(),
            'stats': result.stats,
            'items': {
                item_type: [asdict(i) for i in items]
                for item_type, items in result.items_by_type.items()
            }
        }
        (output_path / "semantic_tags.json").write_text(
            json.dumps(json_data, indent=2), encoding='utf-8'
        )
        
        print(f"  Wrote local report to {output_path}")
    
    def _write_global_output(self, result: AggregationResult):
        """Write aggregated items to 07_MASTER_TRUTH folders."""
        self.master_truth_path.mkdir(parents=True, exist_ok=True)
        
        for item_type, items in result.items_by_type.items():
            folder_name = self.TYPE_TO_FOLDER.get(item_type, item_type.lower())
            folder_path = self.master_truth_path / folder_name
            folder_path.mkdir(parents=True, exist_ok=True)
            
            # Deduplicate by UUID
            unique_items = {}
            for item in items:
                if item.uuid not in unique_items:
                    unique_items[item.uuid] = item
            
            # Write registry markdown
            registry_content = f"""# {item_type} Registry
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total: {len(unique_items)} unique items

| UUID | Label | Source | Parent |
|------|-------|--------|--------|
"""
            for item in unique_items.values():
                parent = item.parent_uuid[:8] if item.parent_uuid else "-"
                source = Path(item.source_file).stem[:30]
                registry_content += f"| `{item.uuid[:8]}` | {item.label[:50]} | {source} | {parent} |\n"
            
            (folder_path / f"{folder_name}-registry.md").write_text(
                registry_content, encoding='utf-8'
            )
            
            # Write individual item files for important types
            if item_type in ['Axiom', 'Claim', 'Theory']:
                items_folder = folder_path / "items"
                items_folder.mkdir(exist_ok=True)
                
                for item in list(unique_items.values())[:100]:  # Limit to 100
                    safe_name = re.sub(r'[^\w\s-]', '', item.label)[:40]
                    item_file = items_folder / f"{safe_name}.md"
                    
                    item_content = f"""# {item.label}

**Type**: {item.item_type}
**UUID**: `{item.uuid}`
**Source**: [[{item.source_file}]]
**Parent**: {f'`{item.parent_uuid}`' if item.parent_uuid else 'None'}

## Context
```
{item.context}
```

---
*Auto-generated by Semantic Aggregator*
"""
                    item_file.write_text(item_content, encoding='utf-8')
        
        # Write global summary
        summary = f"""# Global Semantic Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Statistics
| Metric | Count |
|--------|-------|
| Total Tags | {result.stats.get('total_items', 0)} |
| Unique Items | {result.stats.get('unique_items', 0)} |
| Contradictions | {result.stats.get('contradictions', 0)} |
| Orphaned References | {result.stats.get('orphaned', 0)} |

## By Type
"""
        for item_type, items in result.items_by_type.items():
            folder_name = self.TYPE_TO_FOLDER.get(item_type, item_type.lower())
            summary += f"- **{item_type}**: {len(items)} → [[07_MASTER_TRUTH/{folder_name}/]]\n"
        
        if result.contradictions:
            summary += "\n## ⚠️ Contradictions Found\n"
            for item1, item2 in result.contradictions[:20]:
                summary += f"- `{item1.uuid[:8]}`: \"{item1.label}\" ≠ \"{item2.label}\"\n"
        
        (self.master_truth_path / "GLOBAL_SEMANTIC_SUMMARY.md").write_text(
            summary, encoding='utf-8'
        )
        
        print(f"  Wrote global output to {self.master_truth_path}")


def run_local_aggregation(vault_path: str, target_folder: str, output_folder: str = None):
    """Run LOCAL semantic aggregation on a specific folder."""
    agg = SemanticAggregator(vault_path)
    result = agg.aggregate_local(target_folder, output_folder)
    return result


def run_global_aggregation(vault_path: str):
    """Run GLOBAL semantic aggregation across the vault."""
    agg = SemanticAggregator(vault_path)
    result = agg.aggregate_global()
    return result


if __name__ == "__main__":
    # Example usage
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    
    print("Running GLOBAL semantic aggregation...")
    result = run_global_aggregation(vault)
    
    print(f"\nResults:")
    print(f"  Total items: {result.stats.get('total_items', 0)}")
    print(f"  Unique items: {result.stats.get('unique_items', 0)}")
    print(f"  Contradictions: {result.stats.get('contradictions', 0)}")
    
    for item_type, count in result.stats.items():
        if item_type.endswith('_count'):
            print(f"  {item_type}: {count}")
