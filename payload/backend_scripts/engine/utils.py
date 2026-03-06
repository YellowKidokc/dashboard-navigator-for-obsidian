# engine/utils.py

import re
import yaml

# YAML front matter pattern - handles various edge cases
YAML_PATTERN = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

# Tag pattern - Obsidian style tags
TAG_PATTERN = re.compile(r"(?<!\w)#([A-Za-z][A-Za-z0-9/_-]*)")

# Wikilink pattern - [[link]] or [[link|alias]]
LINK_PATTERN = re.compile(r"\[\[([^\]\|]+)(?:\|[^\]]+)?\]\]")


def parse_yaml_block(text: str) -> dict:
    """
    Parse YAML front matter from text.
    
    Returns empty dict if no valid YAML found or parsing fails.
    """
    if not text or not text.strip().startswith('---'):
        return {}
    
    m = YAML_PATTERN.search(text)
    if not m:
        return {}
    
    try:
        yaml_content = m.group(1)
        
        # Fix common YAML issues
        # Replace tabs with spaces
        yaml_content = yaml_content.replace('\t', '  ')
        
        # Try to parse
        block = yaml.safe_load(yaml_content)
        
        if block is None:
            return {}
        
        if not isinstance(block, dict):
            return {}
        
        return block
        
    except yaml.YAMLError:
        return {}
    except Exception:
        return {}


def strip_yaml_block(text: str) -> str:
    """Remove YAML front matter from text."""
    if not text:
        return ""
    return YAML_PATTERN.sub("", text, count=1).lstrip()


def extract_tags(text: str) -> list[str]:
    """
    Extract Obsidian-style tags from text.
    
    Returns unique tags without the # prefix.
    """
    if not text:
        return []
    
    # Remove code blocks first to avoid false positives
    text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text_no_code = re.sub(r"`[^`]+`", "", text_no_code)
    
    # Remove YAML block (tags in YAML should be handled separately)
    text_no_yaml = strip_yaml_block(text_no_code)
    
    # Find all tags
    tags = TAG_PATTERN.findall(text_no_yaml)
    
    # Return unique tags
    return list(set(tags))


def extract_links(text: str) -> list[str]:
    """
    Extract wikilinks from text.
    
    Returns unique link targets (without aliases).
    """
    if not text:
        return []
    
    # Remove code blocks
    text_no_code = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text_no_code = re.sub(r"`[^`]+`", "", text_no_code)
    
    # Find all links
    links = LINK_PATTERN.findall(text_no_code)
    
    # Clean up links (remove any heading references like Note#heading)
    cleaned = []
    for link in links:
        # Take only the note name part (before any #)
        note_name = link.split('#')[0].strip()
        if note_name:
            cleaned.append(note_name)
    
    return list(set(cleaned))


def extract_yaml_tags(yaml_block: dict) -> list[str]:
    """
    Extract tags from YAML front matter.
    
    Handles both:
    - tags: [tag1, tag2]
    - tags:
        - tag1
        - tag2
    """
    if not yaml_block:
        return []
    
    tags = yaml_block.get('tags', [])
    
    if isinstance(tags, str):
        # Single tag as string
        return [tags.strip()] if tags.strip() else []
    
    if isinstance(tags, list):
        # List of tags
        return [str(t).strip() for t in tags if t]
    
    return []


def normalize_link(link: str) -> str:
    """Normalize a link for comparison."""
    return link.lower().strip()


def extract_all_tags(text: str, yaml_block: dict = None) -> list[str]:
    """Extract tags from both text and YAML front matter."""
    text_tags = extract_tags(text)
    yaml_tags = extract_yaml_tags(yaml_block) if yaml_block else []
    
    # Combine and deduplicate
    all_tags = set(text_tags)
    all_tags.update(yaml_tags)
    
    return list(all_tags)
