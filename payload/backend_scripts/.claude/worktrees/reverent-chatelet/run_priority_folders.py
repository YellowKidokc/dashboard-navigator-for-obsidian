"""
Priority folder processor - runs in background
Processes the 3 priority folders with low CPU settings
"""

import sys
import os
import re
import yaml
import time
import uuid
import requests
from pathlib import Path
from datetime import datetime

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"
DELAY_BETWEEN_FILES = 3.0  # seconds
SKIP_EXISTING = True

# Priority folders
FOLDERS = [
    r"O:\Theophysics_Master\TM SUBSTACK\03_PUBLICATIONS\COMPLETE_LOGOS_PAPERS_FINAL",
    r"O:\Theophysics_Master\TM SUBSTACK\03_PUBLICATIONS\Logos Papers Axiom",
    r"O:\Theophysics_Master\TM SUBSTACK\03_PUBLICATIONS\Logos_Papers",
]

# Skip patterns
SKIP_PATTERNS = ['04_The_Axioms', '00_CANONICAL', '01_CANONICAL', '_TEMPLATE', '.obsidian', '__pycache__']

YAML_PROMPT = """You are a YAML frontmatter generator for the Theophysics academic framework.
Analyze this note and generate YAML frontmatter.

REQUIRED FIELDS:
- title: Extract from first heading or generate
- uuid: Generate UUID format xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- type: One of [axiom, theorem, definition, stage, paper, evidence, claim, note]
- status: draft
- tier: One of [primordial, ontological, physical, consciousness, agency, relational, eschatological]

OPTIONAL:
- axiom_refs: List referenced axioms [A1.1, T1, etc]
- domains: [physics, theology, information-theory, consciousness, mathematics, ethics]
- tags: Relevant tags
- summary: One sentence

Return ONLY valid YAML, no code blocks.

Note content:
{content}

YAML:"""

AXIOM_PATTERN = re.compile(
    r'\[\[([ATLMPC]\d+(?:\.\d+)*)\]\]|'
    r'(?<!\w)([ATLM]\d+\.\d+)(?!\w)',
    re.IGNORECASE
)

stats = {'processed': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
log_file = Path(__file__).parent / "ollama_run.log"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def generate(prompt, timeout=180):
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_ctx": 2048,
                    "num_thread": 2,
                }
            },
            timeout=timeout
        )
        if r.status_code == 200:
            return r.json().get("response", "").strip()
    except Exception as e:
        log(f"  ERROR: {e}")
    return None


def extract_frontmatter(content):
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[1].strip(), parts[2].strip()
    return None, content


def extract_axiom_refs(content):
    refs = set()
    for match in AXIOM_PATTERN.finditer(content):
        ref = match.group(1) or match.group(2)
        if ref:
            refs.add(ref.upper())
    return sorted(refs)


def parse_yaml(yaml_str):
    try:
        yaml_str = yaml_str.strip()
        if yaml_str.startswith('```'):
            lines = yaml_str.split('\n')
            yaml_str = '\n'.join(l for l in lines if not l.startswith('```'))
        return yaml.safe_load(yaml_str)
    except:
        return None


def process_file(filepath):
    global stats

    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        log(f"  ERROR reading: {e}")
        stats['errors'] += 1
        return

    existing_fm, body = extract_frontmatter(content)

    if existing_fm and SKIP_EXISTING:
        stats['skipped'] += 1
        return

    axioms = extract_axiom_refs(content)
    prompt = YAML_PROMPT.format(content=content[:1500])

    response = generate(prompt)
    if not response:
        stats['errors'] += 1
        return

    new_fm = parse_yaml(response)
    if not new_fm:
        log(f"  ERROR: Invalid YAML")
        stats['errors'] += 1
        return

    if axioms:
        new_fm['axiom_refs'] = axioms

    if 'uuid' not in new_fm:
        new_fm['uuid'] = str(uuid.uuid4())

    # Write
    try:
        new_content = f"---\n{yaml.dump(new_fm, default_flow_style=False, allow_unicode=True)}---\n\n{body}"
        filepath.write_text(new_content, encoding='utf-8')
        stats['updated'] += 1
        log(f"  UPDATED")
    except Exception as e:
        log(f"  ERROR writing: {e}")
        stats['errors'] += 1

    stats['processed'] += 1


def process_folder(folder_path):
    folder = Path(folder_path)
    if not folder.exists():
        log(f"FOLDER NOT FOUND: {folder_path}")
        return

    md_files = list(folder.rglob("*.md"))
    md_files = [f for f in md_files if not any(p in str(f) for p in SKIP_PATTERNS)]

    log(f"\n{'='*60}")
    log(f"PROCESSING: {folder_path}")
    log(f"Found {len(md_files)} markdown files")
    log(f"{'='*60}")

    for i, filepath in enumerate(md_files, 1):
        log(f"[{i}/{len(md_files)}] {filepath.name[:50]}")
        process_file(filepath)
        time.sleep(DELAY_BETWEEN_FILES)


def main():
    log("\n" + "="*60)
    log("  OLLAMA YAML PROCESSOR - PRIORITY FOLDERS")
    log("  Low CPU mode: 2 threads, 3s delay")
    log("="*60)

    # Check Ollama
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code != 200:
            log("ERROR: Ollama not responding")
            return
        log(f"Ollama ready: {MODEL}")
    except:
        log("ERROR: Ollama not running! Start with: ollama serve")
        return

    start_time = datetime.now()

    for folder in FOLDERS:
        process_folder(folder)

    elapsed = (datetime.now() - start_time).total_seconds()

    log("\n" + "="*60)
    log("  COMPLETE")
    log("="*60)
    log(f"  Processed: {stats['processed']}")
    log(f"  Updated:   {stats['updated']}")
    log(f"  Skipped:   {stats['skipped']}")
    log(f"  Errors:    {stats['errors']}")
    log(f"  Time:      {elapsed:.1f}s")
    log("="*60)


if __name__ == '__main__':
    main()
