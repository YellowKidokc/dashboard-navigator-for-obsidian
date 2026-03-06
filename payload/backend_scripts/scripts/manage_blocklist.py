"""
Tag Blocklist Manager
Add, remove, or view blocked tags that won't be regenerated.
"""

import sys
from pathlib import Path

VAULT_PATH = r"C:\Users\Yellowkid\Documents\Theophysics Master SYNC"
BLOCKLIST_PATH = Path(VAULT_PATH) / "_TAG_NOTES" / "_BLOCKLIST.txt"


def load_blocklist() -> set:
    """Load current blocklist."""
    blocked = set()
    if BLOCKLIST_PATH.exists():
        content = BLOCKLIST_PATH.read_text(encoding='utf-8')
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                blocked.add(line.lower())
    return blocked


def save_blocklist(blocked: set, header: str = None):
    """Save blocklist to file."""
    if header is None:
        header = """# TAG BLOCKLIST
# Add tags here (one per line) that you DON'T want generated
# Lines starting with # are comments
# Run the tag generator again after editing this file.

"""
    content = header + "\n".join(sorted(blocked))
    BLOCKLIST_PATH.write_text(content, encoding='utf-8')


def add_tags(tags: list):
    """Add tags to blocklist."""
    blocked = load_blocklist()
    added = []
    for tag in tags:
        tag = tag.lower().strip().lstrip('#')
        if tag and tag not in blocked:
            blocked.add(tag)
            added.append(tag)
    save_blocklist(blocked)
    print(f"Added {len(added)} tags to blocklist: {added}")
    print(f"Total blocked: {len(blocked)}")


def remove_tags(tags: list):
    """Remove tags from blocklist."""
    blocked = load_blocklist()
    removed = []
    for tag in tags:
        tag = tag.lower().strip().lstrip('#')
        if tag in blocked:
            blocked.remove(tag)
            removed.append(tag)
    save_blocklist(blocked)
    print(f"Removed {len(removed)} tags from blocklist: {removed}")
    print(f"Total blocked: {len(blocked)}")


def list_blocked():
    """List all blocked tags."""
    blocked = load_blocklist()
    print(f"\n=== BLOCKED TAGS ({len(blocked)}) ===\n")
    for tag in sorted(blocked):
        print(f"  - {tag}")
    print()


def auto_block_junk():
    """Auto-detect and block junk tags (short, numeric, etc.)."""
    tag_notes_dir = Path(VAULT_PATH) / "_TAG_NOTES"
    blocked = load_blocklist()
    
    junk_patterns = []
    
    for md_file in tag_notes_dir.glob("*.md"):
        if md_file.name.startswith("_"):
            continue
        
        tag_name = md_file.stem.lower()
        
        # Detect junk patterns
        is_junk = False
        reason = ""
        
        # Too short (1-2 chars)
        if len(tag_name) <= 2:
            is_junk = True
            reason = "too short"
        
        # Mostly numbers
        elif sum(c.isdigit() for c in tag_name) > len(tag_name) * 0.5:
            is_junk = True
            reason = "mostly numbers"
        
        # Random hex-like strings
        elif len(tag_name) >= 6 and all(c in '0123456789abcdef-' for c in tag_name):
            is_junk = True
            reason = "hex string"
        
        # Single letters with numbers (like 9fb, a1, etc.)
        elif len(tag_name) <= 4 and any(c.isdigit() for c in tag_name):
            is_junk = True
            reason = "short alphanumeric"
        
        if is_junk and tag_name not in blocked:
            junk_patterns.append((tag_name, reason))
            blocked.add(tag_name)
    
    if junk_patterns:
        save_blocklist(blocked)
        print(f"\n=== AUTO-BLOCKED {len(junk_patterns)} JUNK TAGS ===\n")
        for tag, reason in junk_patterns[:30]:
            print(f"  - {tag} ({reason})")
        if len(junk_patterns) > 30:
            print(f"  ... and {len(junk_patterns) - 30} more")
    else:
        print("No junk tags detected.")
    
    print(f"\nTotal blocked: {len(blocked)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
Tag Blocklist Manager
=====================

Usage:
  python manage_blocklist.py list              - Show all blocked tags
  python manage_blocklist.py add tag1 tag2     - Add tags to blocklist
  python manage_blocklist.py remove tag1 tag2  - Remove tags from blocklist
  python manage_blocklist.py auto              - Auto-detect and block junk tags

After modifying the blocklist, run generate_filtered_tags.py to regenerate.
        """)
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_blocked()
    elif command == "add" and len(sys.argv) > 2:
        add_tags(sys.argv[2:])
    elif command == "remove" and len(sys.argv) > 2:
        remove_tags(sys.argv[2:])
    elif command == "auto":
        auto_block_junk()
    else:
        print("Unknown command. Run without arguments for help.")
