"""
format_conversation.py
Reformats a Claude.ai exported conversation transcript.
Removes artifacts, adds speaker labels, cleans up structure.

Usage: python format_conversation.py <input_file> <output_file>
"""
import sys
import io
import re
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --- Config ---
INPUT  = r"O:\_Theophysics_v3\Prompt 1\The evidence 1.md"
OUTPUT = r"O:\_Theophysics_v3\Prompt 1\The evidence 1 - FORMATTED.md"

MONTH_MAP = {
    'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
    'May': 'May',     'Jun': 'June',     'Jul': 'July',  'Aug': 'August',
    'Sep': 'September','Oct': 'October', 'Nov': 'November','Dec': 'December'
}

DATE_RE    = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$')
DOCTYPE_RE = re.compile(r'^(Document|Code|Text|Image)\s*[·•]\s*(MD|JSX|TXT|py|PNG|JPG)$', re.IGNORECASE)

# Lines that are almost certainly Claude UI artifacts (action summaries)
ARTIFACT_PHRASES = [
    'Architected', 'Synthesized', 'Recognized', 'Prepared', 'Contemplated',
    'Deliberated', 'Validated', 'Diagnosed', 'Verified', 'Deciphered',
    'Orchestrated', 'Aggregated', 'Examined', 'Organized',
]

def is_artifact(line):
    s = line.strip()
    for phrase in ARTIFACT_PHRASES:
        if s.startswith(phrase) and len(s) < 120:
            return True
    return False

def is_markdown_heavy(line):
    """Lines that are clearly Claude formatting."""
    s = line.strip()
    return (s.startswith(('#', '-', '*', '>', '|', '```', '$$', '!'))
            or re.match(r'^\d+[.)]', s)
            or re.match(r'^\*\*', s)
            or '→' in s
            or len(s) > 200)

def looks_like_david(line):
    """Heuristic: short, informal, no markdown."""
    s = line.strip()
    if not s:
        return False
    if is_markdown_heavy(line):
        return False
    # Very short lines OR lines with voice-transcription feel
    if len(s) < 120:
        lower = s.lower()
        informal_starts = ('i ', 'you ', 'we ', 'this ', 'so ', 'okay', 'ok ',
                           'yeah', 'hey', 'love', 'the problem', 'look ',
                           'let me', "let's", 'but ', 'and ', 'now ', 'holy')
        for start in informal_starts:
            if lower.startswith(start):
                return True
    return False

# --- Read ---
with open(INPUT, 'r', encoding='utf-8', errors='replace') as f:
    raw = f.readlines()
lines = [l.rstrip('\n') for l in raw]

# --- Pass 1: Remove consecutive duplicates (metadata artifacts) ---
deduped = []
i = 0
while i < len(lines):
    if (i + 1 < len(lines)
            and lines[i].strip()
            and lines[i] == lines[i+1]):
        i += 2  # skip both
    else:
        deduped.append(lines[i])
        i += 1
lines = deduped

# --- Pass 2: Remove single-instance artifacts and "Show more" ---
cleaned = []
skip_next = False
for idx, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    s = line.strip()
    if s == 'Show more':
        continue
    if is_artifact(s):
        continue
    # Document reference pairs: "Name\nDocument · MD" → single ref line
    if (idx + 1 < len(lines)
            and DOCTYPE_RE.match(lines[idx+1].strip())):
        doc_type = lines[idx+1].strip()
        if 'Document' in doc_type or 'MD' in doc_type:
            type_label = 'document'
        elif 'Code' in doc_type or 'JSX' in doc_type:
            type_label = 'code'
        else:
            type_label = 'file'
        cleaned.append(f'> 📎 *{s} ({type_label})*')
        skip_next = True
        continue
    cleaned.append(line)
lines = cleaned

# --- Pass 3: Parse into speaker blocks ---
# Structure after cleanup:
#   [CLAUDE content]
#   [DAVID content]    ← before each date line
#   [DATE LINE]
#   [CLAUDE content]
#   ...
# We'll walk the lines and use the DATE LINE as the primary delimiter.
# Within a section, we use heuristics to split Claude→David.

class Block:
    def __init__(self, speaker, date_header=None):
        self.speaker = speaker  # 'claude', 'david', 'date', 'ref'
        self.date_header = date_header
        self.lines = []

blocks = []
current = Block('claude')  # file starts with Claude

for line in lines:
    s = line.strip()

    # Date line → boundary
    m = DATE_RE.match(s)
    if m:
        # Flush current block
        if current.lines:
            # If current block is 'claude', check if tail is David's voice
            # Split claude block: structured content = claude, trailing informal = david
            if current.speaker == 'claude':
                # Find split point: last stretch of structured content
                split_idx = len(current.lines)
                for j in range(len(current.lines) - 1, -1, -1):
                    l = current.lines[j]
                    if l.strip() == '':
                        continue
                    if looks_like_david(l):
                        split_idx = j
                    else:
                        break
                if split_idx < len(current.lines):
                    # Split into claude + david
                    claude_part = current.lines[:split_idx]
                    david_part  = current.lines[split_idx:]
                    if claude_part:
                        b = Block('claude')
                        b.lines = claude_part
                        blocks.append(b)
                    if david_part:
                        b = Block('david')
                        b.lines = david_part
                        blocks.append(b)
                else:
                    blocks.append(current)
            else:
                blocks.append(current)

        # Add date block
        month = MONTH_MAP.get(m.group(1), m.group(1))
        day = s.split()[1]
        db = Block('date')
        db.date_header = f'{month} {day}'
        blocks.append(db)

        # Next content is Claude's
        current = Block('claude')
        continue

    current.lines.append(line)

# Flush last block
if current.lines:
    blocks.append(current)

# --- Pass 4: Render ---
out = []
out.append('---')
out.append('title: "The Evidence 1 — Conversation Transcript"')
out.append('date_reformatted: "2026-03-05"')
out.append('original: "Prompt 1/The evidence 1.md"')
out.append('---')
out.append('')
out.append('# The Evidence 1')
out.append('')
out.append('*Conversation transcript — reformatted for readability.*')
out.append('*Original: [[Prompt 1/The evidence 1]]*')
out.append('')
out.append('---')
out.append('')

for block in blocks:
    if block.speaker == 'date':
        out.append('')
        out.append(f'## {block.date_header}')
        out.append('')
        out.append('---')
        continue

    content = '\n'.join(block.lines).strip()
    if not content:
        continue

    if block.speaker == 'claude':
        out.append('')
        out.append('**Claude:**')
        out.append('')
        out.append(content)
        out.append('')
    elif block.speaker == 'david':
        out.append('')
        out.append('**David:**')
        out.append('')
        out.append(content)
        out.append('')

# --- Write ---
result = '\n'.join(out)
with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(result)

size_in = os.path.getsize(INPUT)
size_out = os.path.getsize(OUTPUT)
print(f"Done.")
print(f"Input:  {INPUT} ({size_in:,} bytes)")
print(f"Output: {OUTPUT} ({size_out:,} bytes)")
print(f"Blocks written: {len(blocks)}")
