"""
Image Link Fixer Engine
Scans papers for broken image links and fixes them by finding images in canonical media folder
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class ImageLinkFixer:
    """Fix broken image links in markdown papers."""
    
    def __init__(self, canonical_media_path: str):
        self.canonical_media_path = Path(canonical_media_path)
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
        self.image_cache = {}
        self._build_image_cache()
    
    def _build_image_cache(self):
        """Build a cache of all images in canonical media folder."""
        if not self.canonical_media_path.exists():
            print(f"Warning: Canonical media path does not exist: {self.canonical_media_path}")
            return
        
        print(f"Building image cache from: {self.canonical_media_path}")
        for img_file in self.canonical_media_path.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in self.image_extensions:
                # Store by filename (case-insensitive)
                key = img_file.name.lower()
                if key not in self.image_cache:
                    self.image_cache[key] = []
                self.image_cache[key].append(img_file)
        
        print(f"Found {len(self.image_cache)} unique image filenames in canonical media")
    
    def scan_paper(self, paper_path: Path) -> List[Dict]:
        """
        Scan a paper for image references.
        Returns list of dicts with: line_num, original_link, image_name, exists, suggested_fix
        """
        if not paper_path.exists():
            return []
        
        results = []
        content = paper_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        
        # Regex patterns for markdown images
        # ![alt](path) or ![[wikilink]]
        md_image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
        wiki_image_pattern = r'!\[\[([^\]]+)\]\]'
        
        for line_num, line in enumerate(lines, 1):
            # Check markdown style images
            for match in re.finditer(md_image_pattern, line):
                alt_text = match.group(1)
                image_path = match.group(2)
                
                # Extract just the filename
                image_name = Path(image_path).name
                
                # Check if image exists at specified path
                full_path = paper_path.parent / image_path
                exists = full_path.exists()
                
                # Try to find in canonical media
                suggested_fix = None
                if not exists:
                    suggested_fix = self._find_image_in_canonical(image_name)
                
                results.append({
                    'line_num': line_num,
                    'line_text': line.strip(),
                    'original_link': image_path,
                    'image_name': image_name,
                    'exists': exists,
                    'suggested_fix': suggested_fix,
                    'alt_text': alt_text,
                    'match_type': 'markdown'
                })
            
            # Check wiki-style images
            for match in re.finditer(wiki_image_pattern, line):
                image_name = match.group(1)
                
                # Check if it's a path or just filename
                if '/' in image_name or '\\' in image_name:
                    image_filename = Path(image_name).name
                else:
                    image_filename = image_name
                
                # Try to find in canonical media
                suggested_fix = self._find_image_in_canonical(image_filename)
                exists = suggested_fix is not None
                
                results.append({
                    'line_num': line_num,
                    'line_text': line.strip(),
                    'original_link': image_name,
                    'image_name': image_filename,
                    'exists': exists,
                    'suggested_fix': suggested_fix,
                    'alt_text': '',
                    'match_type': 'wikilink'
                })
        
        return results
    
    def _find_image_in_canonical(self, image_name: str) -> Optional[Path]:
        """Find an image in the canonical media folder."""
        key = image_name.lower()
        
        # Exact match
        if key in self.image_cache:
            return self.image_cache[key][0]  # Return first match
        
        # Try without extension
        name_without_ext = Path(image_name).stem.lower()
        for cached_key, paths in self.image_cache.items():
            if Path(cached_key).stem.lower() == name_without_ext:
                return paths[0]
        
        return None
    
    def fix_paper_images(self, paper_path: Path, fixes: List[Dict]) -> Tuple[int, str]:
        """
        Apply fixes to a paper.
        Returns (num_fixed, new_content)
        """
        if not paper_path.exists():
            return 0, ""
        
        content = paper_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        num_fixed = 0
        
        # Sort fixes by line number (descending) to avoid line number shifts
        fixes_sorted = sorted(fixes, key=lambda x: x['line_num'], reverse=True)
        
        for fix in fixes_sorted:
            if not fix.get('apply', False):
                continue
            
            line_num = fix['line_num'] - 1  # Convert to 0-indexed
            if line_num >= len(lines):
                continue
            
            line = lines[line_num]
            original_link = fix['original_link']
            suggested_fix = fix['suggested_fix']
            
            if not suggested_fix:
                continue
            
            # Calculate relative path from paper to image
            try:
                relative_path = suggested_fix.relative_to(paper_path.parent)
                new_link = str(relative_path).replace('\\', '/')
            except ValueError:
                # If relative path fails, use absolute path
                new_link = str(suggested_fix).replace('\\', '/')
            
            # Replace the link in the line
            if fix['match_type'] == 'markdown':
                # Replace ![alt](old_path) with ![alt](new_path)
                new_line = line.replace(f']({original_link})', f']({new_link})')
            else:  # wikilink
                # Replace ![[old_path]] with ![](new_path)
                new_line = line.replace(f'![[{original_link}]]', f'![]({new_link})')
            
            if new_line != line:
                lines[line_num] = new_line
                num_fixed += 1
        
        new_content = '\n'.join(lines)
        return num_fixed, new_content
    
    def scan_folder(self, folder_path: Path, recursive: bool = True) -> Dict[Path, List[Dict]]:
        """
        Scan all markdown files in a folder.
        Returns dict mapping paper_path -> list of image issues
        """
        results = {}
        
        if not folder_path.exists():
            return results
        
        pattern = "**/*.md" if recursive else "*.md"
        for paper_path in folder_path.glob(pattern):
            issues = self.scan_paper(paper_path)
            if issues:
                results[paper_path] = issues
        
        return results
    
    def get_statistics(self, scan_results: Dict[Path, List[Dict]]) -> Dict:
        """Get statistics from scan results."""
        total_images = 0
        broken_images = 0
        fixable_images = 0
        
        for paper_path, issues in scan_results.items():
            for issue in issues:
                total_images += 1
                if not issue['exists']:
                    broken_images += 1
                    if issue['suggested_fix']:
                        fixable_images += 1
        
        return {
            'total_papers': len(scan_results),
            'total_images': total_images,
            'broken_images': broken_images,
            'fixable_images': fixable_images,
            'unfixable_images': broken_images - fixable_images
        }
