"""
Theophysics Article Converter — Callouts to Footnotes
=====================================================
Converts inline structural callouts ([!establish], [!derive], [!challenge],
[!anchor], [!bridge]) into numbered footnotes while preserving:
- Structural Index at top (> [!abstract]-)
- Media block (> [!info]-)
- Regular callouts ([!note], [!important], [!warning], [!quote], [!cite])
- Ring 2 / Ring 3 sections
- Audit section
- Images and all other content

Usage:
    python callout_to_footnote.py <input.md> [output.md]
    
If output is omitted, writes to <input>_published.md

Author: Opus (Claude) for David Lowe / POF 2828
Date: 2026-03-05
"""

import re
import sys
import yaml
from pathlib import Path
from typing import Optional

# Callout types that get converted to footnotes
STRUCTURAL_CALLOUTS = {'establish', 'derive', 'challenge', 'anchor', 'bridge'}

# Callout types that STAY as callouts (not converted)
KEEP_CALLOUTS = {'abstract', 'info', 'note', 'important', 'warning', 'quote', 'cite'}

# Ring explanation link
RING_EXPLANATION = '> *Every claim is grounded two ways: established science we built on ([[00_Canonical/_Documentation/RING_2_AND_RING_3_EXPLAINED|Ring 2]]) and our own framework connections ([[00_Canonical/_Documentation/RING_2_AND_RING_3_EXPLAINED|Ring 3]]). [[00_Canonical/_Documentation/RING_2_AND_RING_3_EXPLAINED|Learn how this works.]]*'


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (metadata, remaining_text)."""
    if text.startswith('---\n'):
        m = re.match(r'^---\n(.*?)\n---\n?', text, flags=re.DOTALL)
        if m:
            yaml_str = m.group(1).strip()
            try:
                metadata = yaml.safe_load(yaml_str) or {}
            except Exception:
                metadata = {}
            body = text[m.end():].lstrip('\n')
            return metadata, body
    return {}, text


def extract_structural_callouts(text: str) -> tuple[str, list[dict]]:
    """
    Find all structural callout blocks, extract them, and leave markers.
    Returns (modified_text, list_of_callout_dicts).
    """
    callouts = []
    footnote_num = 1
    
    # Pattern matches multi-line callout blocks like:
    # > [!establish] **A1 — Axiom: ...**
    # > content...
    # > content...
    # 
    # ^A1  (optional block ID)
    
    lines = text.split('\n')
    result_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a structural callout
        callout_match = re.match(r'^>\s*\[!(establish|derive|challenge|anchor|bridge)\]\s*(.*)', line)
        
        if callout_match:
            callout_type = callout_match.group(1)
            first_line_content = callout_match.group(2).strip()
            
            # Collect all continuation lines (starting with >)
            callout_lines = [first_line_content]
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                content = lines[i][1:].strip()  # Remove '>' prefix
                if content:  # Skip empty continuation lines
                    callout_lines.append(content)
                i += 1
            
            # Check for block ID on next line (^A1, ^C1, etc.)
            block_id = ''
            if i < len(lines) and re.match(r'^\^[A-Z]\d+', lines[i].strip()):
                block_id = lines[i].strip()
                i += 1
            
            # Extract the label (e.g., "A1 — Axiom: Five Properties...")
            label_match = re.match(r'\*\*([^*]+)\*\*', first_line_content)
            label = label_match.group(1) if label_match else f"{callout_type.title()} {footnote_num}"
            
            # Build footnote content — extract key info
            full_content = '\n'.join(callout_lines)
            
            # Create a concise footnote from the callout
            footnote_text = _build_footnote_text(callout_type, label, full_content)
            
            callouts.append({
                'num': footnote_num,
                'type': callout_type,
                'label': label,
                'block_id': block_id,
                'full_content': full_content,
                'footnote_text': footnote_text
            })
            
            # Insert footnote reference where the callout was
            result_lines.append(f'[^{footnote_num}]')
            result_lines.append('')  # blank line after
            
            footnote_num += 1
            continue
        
        result_lines.append(line)
        i += 1
    
    return '\n'.join(result_lines), callouts


def _build_footnote_text(callout_type: str, label: str, content: str) -> str:
    """Build a concise, readable footnote from a structural callout."""
    
    # Extract key fields from the callout content
    vulnerability = _extract_field(content, 'Vulnerability')
    weakest_link = _extract_field(content, 'Weakest link')
    what_kills = _extract_field(content, 'What should kill it')
    chain = _extract_field(content, 'Chain')
    data_cited = _extract_field(content, 'Data cited')
    strongest_attack = _extract_field(content, 'Strongest attack')
    survived = _extract_field(content, 'Survived')
    
    type_labels = {
        'establish': 'Axiom',
        'derive': 'Claim', 
        'challenge': 'Challenge',
        'anchor': 'Evidence',
        'bridge': 'Bridge'
    }
    
    type_label = type_labels.get(callout_type, callout_type.title())
    
    parts = [f'**{label}** ({type_label})']
    
    if chain:
        parts.append(f'Chain: {chain}')
    if data_cited:
        parts.append(f'Data: {data_cited}')
    if strongest_attack:
        parts.append(f'Strongest attack: {strongest_attack}')
    if survived:
        parts.append(f'Result: {survived}')
    if vulnerability or weakest_link:
        v = vulnerability or weakest_link
        parts.append(f'Vulnerability: {v}')
    if what_kills:
        parts.append(f'Falsification: {what_kills}')
    
    return ' | '.join(parts)


def _extract_field(content: str, field_name: str) -> Optional[str]:
    """Extract a named field value from callout content."""
    pattern = rf'\*\*{field_name}:?\*\*\s*(.*?)(?=\n\*\*|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        value = match.group(1).strip()
        # Clean up and truncate if needed
        value = re.sub(r'\s+', ' ', value)
        if len(value) > 200:
            value = value[:197] + '...'
        return value
    return None


def add_ring_intro(text: str) -> str:
    """Add explanation link before Ring 2 section."""
    ring2_pattern = r'(## Ring 2 — Canonical Grounding)'
    replacement = RING_EXPLANATION + '\n\n\\1'
    return re.sub(ring2_pattern, replacement, text, count=1)


def generate_media_block(metadata: dict) -> str:
    """Generate media callout from YAML media fields."""
    media = metadata.get('media', {})
    if not media or all(v == '' or v is None for v in media.values()):
        # Return placeholder block
        return '''> [!info]- 🎧 Listen, Watch & Download
>
> **Podcasts**
> - 🎙️ Debate Format: *Coming soon*
> - 🎙️ Deep Dive: *Coming soon*
>
> **Audio**
> - 🔊 Article Narration: *Coming soon*
>
> **Downloads**
> - 📁 Downloads: *Coming soon*
>
> *Items marked "Coming soon" are in production. Subscribe for updates.*'''
    
    lines = ['> [!info]- 🎧 Listen, Watch & Download', '>']
    
    lines.append('> **Podcasts**')
    if media.get('podcast_debate'):
        lines.append(f'> - 🎙️ [Debate Format]({media["podcast_debate"]}) *(stress test)*')
    else:
        lines.append('> - 🎙️ Debate Format: *Coming soon*')
    
    if media.get('podcast_deepdive'):
        lines.append(f'> - 🎙️ [Deep Dive]({media["podcast_deepdive"]}) *(full episode)*')
    else:
        lines.append('> - 🎙️ Deep Dive: *Coming soon*')
    
    lines.append('>')
    lines.append('> **Audio**')
    if media.get('audio_narration'):
        dur = media.get('audio_duration', '')
        dur_str = f' ({dur})' if dur else ''
        lines.append(f'> - 🔊 [Article Narration{dur_str}]({media["audio_narration"]})')
    else:
        lines.append('> - 🔊 Article Narration: *Coming soon*')
    
    lines.append('>')
    lines.append('> **Downloads**')
    has_download = False
    if media.get('slides'):
        lines.append(f'> - 📊 [Presentation Slides]({media["slides"]})')
        has_download = True
    if media.get('gdrive_folder'):
        lines.append(f'> - 📁 [Download All Files]({media["gdrive_folder"]})')
        has_download = True
    if not has_download:
        lines.append('> - 📁 Downloads: *Coming soon*')
    
    lines.append('>')
    lines.append('> *Items marked "Coming soon" are in production.*')
    
    return '\n'.join(lines)


def insert_media_block(text: str, media_block: str) -> str:
    """Insert media block after the structural index (> [!abstract]-) block."""
    # Avoid duplicate insertion on repeated runs.
    if 'MEDIA_CALLOUT_START' in text:
        return text
    if re.search(r'>\s*\[!info\]-\s*.*Listen,\s*Watch', text, flags=re.IGNORECASE):
        return text

    # Find the end of the abstract callout block
    lines = text.split('\n')
    insert_after = -1
    in_abstract = False
    
    for i, line in enumerate(lines):
        if '> [!abstract]' in line:
            in_abstract = True
            continue
        if in_abstract:
            if not line.startswith('>') and line.strip() != '':
                insert_after = i
                in_abstract = False
                break
            elif not line.startswith('>') and line.strip() == '':
                continue
    
    if insert_after == -1:
        # No abstract block found, insert at beginning after first ---
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:
                insert_after = i + 1
                break
    
    if insert_after > 0:
        lines.insert(insert_after, '\n' + media_block + '\n')
    
    return '\n'.join(lines)


def build_footnotes_section(callouts: list[dict]) -> str:
    """Build the footnotes section to append at the end."""
    if not callouts:
        return ''
    
    lines = ['\n---\n', '## Structural Notes\n']
    lines.append('*These notes contain the formal scaffolding behind the claims above. The article is the argument; these are the load-bearing specs.*\n')
    
    for c in callouts:
        lines.append(f'[^{c["num"]}]: {c["footnote_text"]}\n')
    
    return '\n'.join(lines)


def convert_article(input_path: str, output_path: Optional[str] = None):
    """Main conversion function."""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return
    
    if output_path is None:
        output_file = input_file.with_name(input_file.stem + '_published.md')
    else:
        output_file = Path(output_path)
    
    # Read source
    text = input_file.read_text(encoding='utf-8')
    
    # Parse frontmatter
    metadata, body = parse_frontmatter(text)
    
    # Generate media block
    media_block = generate_media_block(metadata)
    
    # Insert media block after structural index
    body = insert_media_block(body, media_block)
    
    # Extract structural callouts and convert to footnotes
    body, callouts = extract_structural_callouts(body)
    
    # Add Ring explanation intro
    body = add_ring_intro(body)
    
    # Build footnotes section
    footnotes = build_footnotes_section(callouts)
    
    # Reconstruct frontmatter
    if metadata:
        frontmatter = '---\n' + yaml.dump(metadata, default_flow_style=False, allow_unicode=True) + '---\n\n'
    else:
        frontmatter = ''
    
    # Combine
    output = frontmatter + body + footnotes
    
    # Clean up excessive blank lines
    output = re.sub(r'\n{4,}', '\n\n\n', output)
    
    # Write output
    output_file.write_text(output, encoding='utf-8')
    
    print(f"Converted: {input_file.name}")
    print(f"Output:    {output_file}")
    print(f"Callouts converted to footnotes: {len(callouts)}")
    for c in callouts:
        print(f"  [^{c['num']}] {c['label'][:60]}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python callout_to_footnote.py <input.md> [output.md]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    convert_article(input_path, output_path)
