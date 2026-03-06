"""
Filtered Tag Notes Generator
Only creates tag notes for tags with 10+ uses
Links to glossary/lexicon entries and pulls descriptions
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
from collections import defaultdict


class FilteredTagGenerator:
    """Generate tag notes with minimum usage filter, glossary linking, and blocklist."""
    
    YAML_TAGS_PATTERN = re.compile(r'^tags:\s*\[([^\]]+)\]', re.MULTILINE)
    YAML_TAGS_LIST_PATTERN = re.compile(r'^tags:\s*\n((?:\s*-\s*.+\n?)+)', re.MULTILINE)
    INLINE_TAG_PATTERN = re.compile(r'#([A-Za-z][A-Za-z0-9_\-/]+)')
    FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)
    
    # Glossary/Lexicon paths
    LEXICON_PATHS = [
        "02_LIBRARY/4_LEXICON",
        "02_LIBRARY/9_ARCHIVE/_OLD_STRUCTURE/Glossary",
    ]
    
    def __init__(self, vault_path: str, output_folder: str = "_TAG_NOTES", min_uses: int = 10):
        self.vault_path = Path(vault_path)
        self.output_folder = self.vault_path / output_folder
        self.min_uses = min_uses
        self.tags: Dict[str, dict] = {}
        self.glossary: Dict[str, dict] = {}  # normalized name -> {path, description, title}
        self.blocklist: Set[str] = set()  # tags to never generate
        self._load_blocklist()
    
    def _load_blocklist(self):
        """Load blocklist from _BLOCKLIST.txt file."""
        blocklist_path = self.output_folder / "_BLOCKLIST.txt"
        print(f"Looking for blocklist at: {blocklist_path}")
        print(f"Exists: {blocklist_path.exists()}")
        if blocklist_path.exists():
            try:
                content = blocklist_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Add both raw and normalized versions
                        self.blocklist.add(line.lower())
                        norm = self._normalize_simple(line)
                        if norm:
                            self.blocklist.add(norm)
                print(f"Loaded {len(self.blocklist)} blocked tags from {len(lines)} lines")
            except Exception as e:
                print(f"Warning: Could not load blocklist: {e}")
    
    def _normalize_simple(self, tag: str) -> str:
        """Simple normalize without regex (for blocklist loading)."""
        tag = tag.lstrip('#').lower().strip()
        result = ""
        for c in tag:
            if c.isalnum() or c == '-':
                result += c
            else:
                result += '-'
        return result.strip('-')
        
    def _normalize(self, tag: str) -> str:
        tag = tag.lstrip('#').lower()
        return re.sub(r'[^a-z0-9\-]', '-', tag).strip('-')
    
    def _extract_yaml_tags(self, content: str) -> List[str]:
        tags = []
        fm_match = self.FRONTMATTER_PATTERN.match(content)
        if not fm_match:
            return tags
        frontmatter = fm_match.group(1)
        
        inline_match = self.YAML_TAGS_PATTERN.search(frontmatter)
        if inline_match:
            tag_str = inline_match.group(1)
            tags.extend([t.strip().strip('"\'') for t in tag_str.split(',') if t.strip()])
        
        list_match = self.YAML_TAGS_LIST_PATTERN.search(frontmatter)
        if list_match:
            for line in list_match.group(1).split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    tag = line[1:].strip().strip('"\'')
                    if tag:
                        tags.append(tag)
        return tags
    
    def _extract_inline_tags(self, content: str) -> List[str]:
        content = self.FRONTMATTER_PATTERN.sub('', content)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        return self.INLINE_TAG_PATTERN.findall(content)
    
    def _extract_description(self, content: str) -> str:
        """Extract a short description from glossary content."""
        # Try to find "Simplified Definition" section
        match = re.search(r'## Simplified Definition\s*\n+(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            # Take first 2-3 sentences
            sentences = re.split(r'(?<=[.!?])\s+', desc)
            return ' '.join(sentences[:2]).strip()
        
        # Try "Core Definition"
        match = re.search(r'## (?:\d+\.\s*)?Core Definition\s*\n+(.+?)(?=\n##|\n---|\Z)', content, re.DOTALL)
        if match:
            desc = match.group(1).strip()
            if desc and not desc.startswith('<!--'):
                sentences = re.split(r'(?<=[.!?])\s+', desc)
                return ' '.join(sentences[:2]).strip()
        
        # Try first paragraph after title
        match = re.search(r'^# .+?\n\n(.+?)(?=\n\n|\n##|\Z)', content, re.MULTILINE | re.DOTALL)
        if match:
            desc = match.group(1).strip()
            if desc and not desc.startswith('<!--') and not desc.startswith('|'):
                sentences = re.split(r'(?<=[.!?])\s+', desc)
                return ' '.join(sentences[:2]).strip()
        
        return ""
    
    def load_glossary(self):
        """Load glossary/lexicon entries."""
        print("Loading glossary entries...")
        
        for rel_path in self.LEXICON_PATHS:
            lexicon_dir = self.vault_path / rel_path
            if not lexicon_dir.exists():
                continue
            
            for md_file in lexicon_dir.glob('*.md'):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    title = md_file.stem
                    norm = self._normalize(title)
                    
                    # Extract description
                    desc = self._extract_description(content)
                    
                    # Get relative path for linking
                    rel_file = md_file.relative_to(self.vault_path)
                    
                    self.glossary[norm] = {
                        'title': title,
                        'path': str(rel_file),
                        'description': desc,
                        'link': str(rel_file).replace('\\', '/').replace('.md', '')
                    }
                    
                    # Also index by variations
                    title_lower = title.lower().replace(' ', '-')
                    if title_lower != norm:
                        self.glossary[title_lower] = self.glossary[norm]
                    
                except Exception as e:
                    pass
        
        print(f"Loaded {len(self.glossary)} glossary entries")
    
    def scan_vault(self):
        """Scan vault and collect tag usage."""
        exclude = ['_TAG_NOTES', '.obsidian', '.git', 'venv', '__pycache__', 'node_modules']
        md_files = list(self.vault_path.rglob('*.md'))
        
        for file_path in md_files:
            rel_path = file_path.relative_to(self.vault_path)
            if any(part in exclude for part in rel_path.parts):
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8')
            except:
                continue
            
            # Get all tags from this file
            all_tags = self._extract_yaml_tags(content) + self._extract_inline_tags(content)
            rel_str = str(rel_path)
            
            for tag in all_tags:
                norm = self._normalize(tag)
                if not norm or len(norm) < 2:
                    continue
                    
                if norm not in self.tags:
                    self.tags[norm] = {
                        'name': tag,
                        'count': 0,
                        'files': set(),
                        'aliases': set()
                    }
                
                self.tags[norm]['count'] += 1
                self.tags[norm]['files'].add(rel_str)
                if tag != self.tags[norm]['name']:
                    self.tags[norm]['aliases'].add(tag)
        
        print(f"Scanned {len(md_files)} files, found {len(self.tags)} unique tags")
    
    def generate_notes(self):
        """Generate notes only for tags with min_uses or more, excluding blocklisted tags."""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        # Filter tags by min uses AND not in blocklist
        filtered = {k: v for k, v in self.tags.items() 
                    if v['count'] >= self.min_uses and k not in self.blocklist}
        
        blocked_count = sum(1 for k in self.tags if k in self.blocklist)
        print(f"Filtered to {len(filtered)} tags with {self.min_uses}+ uses")
        print(f"Blocked {blocked_count} tags from blocklist")
        
        count = 0
        skipped = 0
        for norm, data in filtered.items():
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', data['name'])
            if len(safe_name) > 80:
                safe_name = safe_name[:80]
            
            file_path = self.output_folder / f"{safe_name}.md"
            
            # Build content
            files_list = sorted(data['files'])[:50]
            files_md = "\n".join([f"- [[{f}]]" for f in files_list])
            if len(data['files']) > 50:
                files_md += f"\n- ... and {len(data['files']) - 50} more"
            
            aliases = ", ".join(sorted(data['aliases']))
            
            content = f"""---
tag_name: "{data['name']}"
usage_count: {data['count']}
aliases: [{aliases}]
updated: "{datetime.now().isoformat()}"
---

# {data['name']}

## Description
_Add your description here (2-30 words recommended)_

## Usage Statistics
- **Total Uses:** {data['count']}
- **Files Linked:** {len(data['files'])}

## Linked Files
{files_md}

---
*Auto-generated. Edit description as needed.*
"""
            file_path.write_text(content, encoding='utf-8')
            count += 1
        
        print(f"Generated {count} tag notes in {self.output_folder}")
        return count


def main():
    vault = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
    gen = FilteredTagGenerator(vault, "_TAG_NOTES", min_uses=10)
    gen.scan_vault()
    gen.generate_notes()


if __name__ == "__main__":
    main()
