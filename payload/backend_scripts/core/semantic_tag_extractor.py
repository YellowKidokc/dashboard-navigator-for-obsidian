"""
Semantic Tag Extractor
Parses %%tag:: format from obsidian-semantic-ai plugin and exports to PostgreSQL.

Tag format: %%tag::TYPE::UUID::"LABEL"::PARENT_UUID%%

Author: David Lowe / Theophysics
"""

import re
import json
import uuid as uuid_lib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict


@dataclass
class SemanticTag:
    """Represents a parsed semantic tag."""
    tag_type: str
    uuid: str
    label: str
    parent_uuid: Optional[str]
    file_path: str
    line_number: int
    custom_type: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class TagStats:
    """Statistics about extracted tags."""
    total_tags: int
    by_type: Dict[str, int]
    files_processed: int
    duplicates_found: int
    orphaned_tags: int  # Tags with parent_uuid that doesn't exist


class SemanticTagExtractor:
    """
    Extracts semantic tags from Obsidian vault files.
    Handles deduplication and relationship mapping.
    """
    
    # Regex pattern for tag format: %%tag::TYPE::UUID::"LABEL"::PARENT%%
    TAG_PATTERN = re.compile(
        r'%%tag::([^:]+)::([a-f0-9\-]+)::"([^"]+)"::([^%]*)%%',
        re.IGNORECASE
    )
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.tags: List[SemanticTag] = []
        self.tags_by_uuid: Dict[str, SemanticTag] = {}
        self.tags_by_content: Dict[str, List[SemanticTag]] = defaultdict(list)
        self.stats = TagStats(0, {}, 0, 0, 0)
        
    def extract_from_file(self, file_path: Path) -> List[SemanticTag]:
        """Extract all semantic tags from a single file."""
        tags = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for match in self.TAG_PATTERN.finditer(line):
                    tag_type = match.group(1)
                    tag_uuid = match.group(2)
                    label = match.group(3)
                    parent_uuid = match.group(4).strip()
                    
                    # Handle "null" string as None
                    if parent_uuid.lower() == 'null' or parent_uuid == '':
                        parent_uuid = None
                    
                    # Handle custom types (Custom:TypeName)
                    custom_type = None
                    if tag_type.startswith('Custom:'):
                        custom_type = tag_type.replace('Custom:', '')
                        tag_type = 'Custom'
                    
                    tag = SemanticTag(
                        tag_type=tag_type,
                        uuid=tag_uuid,
                        label=label,
                        parent_uuid=parent_uuid,
                        file_path=str(file_path.relative_to(self.vault_path)),
                        line_number=line_num,
                        custom_type=custom_type
                    )
                    tags.append(tag)
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
        return tags
    
    def extract_from_folder(self, folder_path: Optional[str] = None, 
                           recursive: bool = True) -> List[SemanticTag]:
        """Extract tags from all markdown files in a folder."""
        search_path = Path(folder_path) if folder_path else self.vault_path
        
        if recursive:
            md_files = list(search_path.rglob('*.md'))
        else:
            md_files = list(search_path.glob('*.md'))
        
        all_tags = []
        for file_path in md_files:
            file_tags = self.extract_from_file(file_path)
            all_tags.extend(file_tags)
            
        self.stats.files_processed = len(md_files)
        return all_tags
    
    def deduplicate_by_content(self, tags: List[SemanticTag]) -> List[SemanticTag]:
        """
        Deduplicate tags that have the same content but different UUIDs.
        Keeps the first occurrence, tracks duplicates.
        """
        seen_content: Dict[Tuple[str, str], SemanticTag] = {}
        unique_tags = []
        duplicates = 0
        
        for tag in tags:
            # Create content key: (type, label)
            content_key = (tag.tag_type, tag.label.lower().strip())
            
            if content_key not in seen_content:
                seen_content[content_key] = tag
                unique_tags.append(tag)
            else:
                duplicates += 1
                # Track that this is a duplicate
                self.tags_by_content[content_key].append(tag)
        
        self.stats.duplicates_found = duplicates
        return unique_tags
    
    def build_hierarchy(self, tags: List[SemanticTag]) -> Dict[str, List[SemanticTag]]:
        """
        Build parent-child hierarchy from tags.
        Returns dict mapping parent_uuid -> list of child tags.
        """
        # First, index all tags by UUID
        uuid_index = {tag.uuid: tag for tag in tags}
        
        # Build hierarchy
        hierarchy = defaultdict(list)
        orphaned = 0
        
        for tag in tags:
            if tag.parent_uuid:
                if tag.parent_uuid in uuid_index:
                    hierarchy[tag.parent_uuid].append(tag)
                else:
                    orphaned += 1
                    hierarchy['_orphaned'].append(tag)
            else:
                hierarchy['_root'].append(tag)
        
        self.stats.orphaned_tags = orphaned
        return dict(hierarchy)
    
    def extract_and_process(self, folder_path: Optional[str] = None,
                           deduplicate: bool = True) -> Dict:
        """
        Full extraction pipeline: extract, deduplicate, build hierarchy.
        Returns processed data ready for export.
        """
        # Extract all tags
        raw_tags = self.extract_from_folder(folder_path)
        
        # Deduplicate if requested
        if deduplicate:
            tags = self.deduplicate_by_content(raw_tags)
        else:
            tags = raw_tags
        
        # Build hierarchy
        hierarchy = self.build_hierarchy(tags)
        
        # Calculate stats
        type_counts = defaultdict(int)
        for tag in tags:
            type_counts[tag.tag_type] += 1
        
        self.stats.total_tags = len(tags)
        self.stats.by_type = dict(type_counts)
        
        # Store for later use
        self.tags = tags
        self.tags_by_uuid = {tag.uuid: tag for tag in tags}
        
        return {
            'tags': [tag.to_dict() for tag in tags],
            'hierarchy': {k: [t.to_dict() for t in v] for k, v in hierarchy.items()},
            'stats': asdict(self.stats),
            'extracted_at': datetime.now().isoformat()
        }
    
    def export_to_json(self, output_path: str, data: Optional[Dict] = None) -> Path:
        """Export processed data to JSON file."""
        if data is None:
            data = self.extract_and_process()
        
        output_file = Path(output_path)
        output_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        return output_file
    
    def export_to_postgres_tables(self, data: Optional[Dict] = None) -> Dict[str, List[Dict]]:
        """
        Convert extracted data to PostgreSQL table format.
        Returns dict with table_name -> list of row dicts.
        """
        if data is None:
            data = self.extract_and_process()
        
        tables = {
            'semantic_axioms': [],
            'semantic_claims': [],
            'semantic_evidence': [],
            'semantic_relationships': [],
            'semantic_tags_all': []
        }
        
        for tag_dict in data['tags']:
            # All tags go to the master table
            tables['semantic_tags_all'].append({
                'uuid': tag_dict['uuid'],
                'tag_type': tag_dict['tag_type'],
                'label': tag_dict['label'],
                'parent_uuid': tag_dict['parent_uuid'],
                'file_path': tag_dict['file_path'],
                'line_number': tag_dict['line_number'],
                'custom_type': tag_dict.get('custom_type'),
                'created_at': datetime.now().isoformat()
            })
            
            # Route to type-specific tables
            tag_type = tag_dict['tag_type']
            if tag_type == 'Axiom':
                tables['semantic_axioms'].append(tag_dict)
            elif tag_type == 'Claim':
                tables['semantic_claims'].append(tag_dict)
            elif tag_type == 'EvidenceBundle':
                tables['semantic_evidence'].append(tag_dict)
            elif tag_type == 'Relationship':
                tables['semantic_relationships'].append(tag_dict)
        
        return tables
    
    def get_evidence_for_axiom(self, axiom_uuid: str) -> List[SemanticTag]:
        """Get all evidence that supports a specific axiom."""
        # First find claims that reference this axiom
        supporting_claims = [
            tag for tag in self.tags 
            if tag.tag_type == 'Claim' and tag.parent_uuid == axiom_uuid
        ]
        
        # Then find evidence that supports those claims
        claim_uuids = {c.uuid for c in supporting_claims}
        evidence = [
            tag for tag in self.tags
            if tag.tag_type == 'EvidenceBundle' and tag.parent_uuid in claim_uuids
        ]
        
        # Also get direct evidence for the axiom
        direct_evidence = [
            tag for tag in self.tags
            if tag.tag_type == 'EvidenceBundle' and tag.parent_uuid == axiom_uuid
        ]
        
        return direct_evidence + evidence
    
    def find_by_label(self, search_term: str, tag_type: Optional[str] = None) -> List[SemanticTag]:
        """Search tags by label content."""
        results = []
        search_lower = search_term.lower()
        
        for tag in self.tags:
            if search_lower in tag.label.lower():
                if tag_type is None or tag.tag_type == tag_type:
                    results.append(tag)
        
        return results


# Convenience function for quick extraction
def extract_vault_tags(vault_path: str, output_json: Optional[str] = None) -> Dict:
    """
    Quick extraction of all semantic tags from a vault.
    
    Args:
        vault_path: Path to Obsidian vault
        output_json: Optional path to save JSON output
        
    Returns:
        Processed tag data with hierarchy and stats
    """
    extractor = SemanticTagExtractor(vault_path)
    data = extractor.extract_and_process()
    
    if output_json:
        extractor.export_to_json(output_json, data)
        print(f"Exported to {output_json}")
    
    print(f"Extracted {data['stats']['total_tags']} tags from {data['stats']['files_processed']} files")
    print(f"By type: {data['stats']['by_type']}")
    print(f"Duplicates removed: {data['stats']['duplicates_found']}")
    
    return data


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python semantic_tag_extractor.py <vault_path> [output.json]")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else None
    
    extract_vault_tags(vault_path, output_json)
