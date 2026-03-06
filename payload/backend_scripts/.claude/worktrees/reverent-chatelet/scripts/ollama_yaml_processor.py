"""
Ollama YAML Processor - Overnight batch processing for Theophysics vault
Reads papers, generates/enriches YAML frontmatter using local Ollama

Usage:
    python ollama_yaml_processor.py                    # Process all papers
    python ollama_yaml_processor.py --dry-run          # Preview without writing
    python ollama_yaml_processor.py --limit 10         # Process first 10 only
    python ollama_yaml_processor.py --model llama3.2   # Use specific model
"""

import sys
import os
import re
import json
import yaml
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Default paths
VAULT_PATH = Path(r"O:/Theophysics_Master/TM SUBSTACK/03_PUBLICATIONS/Logos Papers Axiom")
OUTPUT_PATH = Path(r"O:/Theophysics_Master/TM/00_VAULT_OS/Reports")
OLLAMA_URL = "http://localhost:11434/api/generate"

# Theophysics-specific prompt
YAML_PROMPT = """You are a YAML frontmatter generator for the Theophysics academic framework.
Analyze this note and generate YAML frontmatter following these rules:

REQUIRED FIELDS:
- title: Extract from first heading or generate from content
- uuid: Generate new UUID if none exists
- type: One of [axiom, theorem, definition, stage, paper, evidence, claim, note]
- status: One of [draft, review, canonical, deprecated]
- tier: One of [primordial, ontological, physical, consciousness, agency, relational, eschatological]

OPTIONAL FIELDS:
- axiom_refs: List axioms referenced (e.g., [A1.1, A2.2, T1])
- domains: List domains [physics, theology, information-theory, consciousness, mathematics, ethics]
- tags: List relevant tags
- depends_on: List dependencies
- created: ISO date
- summary: One sentence summary

Return ONLY valid YAML, no code blocks, no explanation.

Note content:
{content}

YAML:"""

# Axiom extraction pattern
AXIOM_PATTERN = re.compile(
    r'\[\[([ATLMPC]\d+(?:\.\d+)*)\]\]|'
    r'(?<!\w)([ATLM]\d+\.\d+)(?!\w)',
    re.IGNORECASE
)


class OllamaProcessor:
    def __init__(self, model: str = "llama3.2", dry_run: bool = False):
        self.model = model
        self.dry_run = dry_run
        self.stats = {
            'processed': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        self.results = []

    def check_ollama(self) -> bool:
        """Verify Ollama is running."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            if r.status_code == 200:
                models = [m['name'] for m in r.json().get('models', [])]
                if self.model not in models and f"{self.model}:latest" not in models:
                    print(f"Warning: Model '{self.model}' not found. Available: {models}")
                return True
        except Exception as e:
            print(f"Ollama not available: {e}")
        return False

    def generate(self, prompt: str, timeout: int = 120) -> Optional[str]:
        """Call Ollama API."""
        try:
            r = requests.post(
                OLLAMA_URL,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=timeout
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception as e:
            print(f"  Error: {e}")
        return None

    def extract_frontmatter(self, content: str) -> tuple:
        """Extract existing YAML frontmatter and body."""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[1].strip(), parts[2].strip()
        return None, content

    def extract_axiom_refs(self, content: str) -> List[str]:
        """Extract axiom references from content."""
        refs = set()
        for match in AXIOM_PATTERN.finditer(content):
            ref = match.group(1) or match.group(2)
            if ref:
                refs.add(ref.upper())
        return sorted(refs)

    def parse_yaml(self, yaml_str: str) -> Optional[Dict]:
        """Safely parse YAML."""
        try:
            # Clean up common LLM output issues
            yaml_str = yaml_str.strip()
            if yaml_str.startswith('```'):
                lines = yaml_str.split('\n')
                yaml_str = '\n'.join(l for l in lines if not l.startswith('```'))
            return yaml.safe_load(yaml_str)
        except:
            return None

    def process_file(self, filepath: Path, vault_root: Path) -> Dict:
        """Process a single markdown file."""
        result = {
            'path': str(filepath.relative_to(vault_root)),
            'status': 'skipped',
            'existing_fm': False,
            'axioms': []
        }

        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            self.stats['errors'] += 1
            return result

        # Extract existing frontmatter
        existing_fm, body = self.extract_frontmatter(content)
        result['existing_fm'] = existing_fm is not None

        # Extract axiom refs
        axioms = self.extract_axiom_refs(content)
        result['axioms'] = axioms

        # Generate new YAML with Ollama
        prompt = YAML_PROMPT.format(content=content[:2000])
        print(f"  Generating YAML for: {filepath.name[:40]}...")

        response = self.generate(prompt)
        if not response:
            result['status'] = 'error'
            result['error'] = 'No response from Ollama'
            self.stats['errors'] += 1
            return result

        # Parse the generated YAML
        new_fm = self.parse_yaml(response)
        if not new_fm:
            result['status'] = 'error'
            result['error'] = 'Invalid YAML response'
            result['raw_response'] = response[:200]
            self.stats['errors'] += 1
            return result

        # Ensure axiom_refs are included
        if axioms and 'axiom_refs' not in new_fm:
            new_fm['axiom_refs'] = axioms

        # Ensure UUID
        if 'uuid' not in new_fm or not new_fm['uuid']:
            new_fm['uuid'] = str(uuid.uuid4())

        result['generated_fm'] = new_fm
        result['status'] = 'generated'

        # Write back if not dry run
        if not self.dry_run:
            try:
                new_content = f"---\n{yaml.dump(new_fm, default_flow_style=False, allow_unicode=True)}---\n\n{body}"
                filepath.write_text(new_content, encoding='utf-8')
                result['status'] = 'updated'
                self.stats['updated'] += 1
            except Exception as e:
                result['status'] = 'error'
                result['error'] = f"Write failed: {e}"
                self.stats['errors'] += 1
        else:
            self.stats['updated'] += 1  # Count as would-update

        self.stats['processed'] += 1
        return result

    def process_folder(self, folder: Path, limit: int = 0, skip_with_fm: bool = False):
        """Process all markdown files in folder."""
        if not folder.exists():
            print(f"Folder not found: {folder}")
            return

        md_files = list(folder.rglob("*.md"))
        print(f"\nFound {len(md_files)} markdown files")

        # Skip canonical axiom definition files
        skip_patterns = ['04_The_Axioms', '00_CANONICAL', '01_CANONICAL']
        md_files = [f for f in md_files if not any(p in str(f) for p in skip_patterns)]
        print(f"After filtering canonical: {len(md_files)} files")

        if limit > 0:
            md_files = md_files[:limit]
            print(f"Limited to: {limit} files")

        for i, filepath in enumerate(md_files, 1):
            print(f"\n[{i}/{len(md_files)}] Processing: {filepath.name}")

            # Check if should skip files with existing frontmatter
            if skip_with_fm:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
                if content.startswith('---'):
                    print("  Skipping - has frontmatter")
                    self.stats['skipped'] += 1
                    continue

            result = self.process_file(filepath, folder)
            self.results.append(result)

            # Brief pause to not hammer Ollama
            time.sleep(0.5)

    def save_report(self, output_path: Path):
        """Save processing report."""
        output_path.mkdir(parents=True, exist_ok=True)

        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()

        report = {
            'generated': datetime.now().isoformat(),
            'model': self.model,
            'dry_run': self.dry_run,
            'stats': {
                'processed': self.stats['processed'],
                'updated': self.stats['updated'],
                'skipped': self.stats['skipped'],
                'errors': self.stats['errors'],
                'elapsed_seconds': round(elapsed, 1),
                'avg_seconds_per_file': round(elapsed / max(1, self.stats['processed']), 2)
            },
            'results': self.results
        }

        report_file = output_path / f"ollama_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
        report_file.write_text(yaml.dump(report, default_flow_style=False, allow_unicode=True), encoding='utf-8')
        print(f"\nReport saved to: {report_file}")

        return report


def main():
    parser = argparse.ArgumentParser(description='Process vault with Ollama for YAML generation')
    parser.add_argument('--folder', '-f', default=str(VAULT_PATH), help='Folder to process')
    parser.add_argument('--model', '-m', default='llama3.2', help='Ollama model to use')
    parser.add_argument('--limit', '-l', type=int, default=0, help='Limit number of files (0=all)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without writing')
    parser.add_argument('--skip-existing', '-s', action='store_true', help='Skip files with frontmatter')
    parser.add_argument('--output', '-o', default=str(OUTPUT_PATH), help='Report output folder')
    args = parser.parse_args()

    print("="*60)
    print("  OLLAMA YAML PROCESSOR")
    print("  Overnight batch processing for Theophysics vault")
    print("="*60)
    print(f"\nModel: {args.model}")
    print(f"Folder: {args.folder}")
    print(f"Dry run: {args.dry_run}")
    if args.limit:
        print(f"Limit: {args.limit} files")

    processor = OllamaProcessor(model=args.model, dry_run=args.dry_run)

    if not processor.check_ollama():
        print("\nERROR: Ollama not running. Start it with: ollama serve")
        sys.exit(1)

    print("\nOllama ready. Starting processing...")
    processor.process_folder(
        Path(args.folder),
        limit=args.limit,
        skip_with_fm=args.skip_existing
    )

    report = processor.save_report(Path(args.output))

    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)
    print(f"  Processed: {report['stats']['processed']}")
    print(f"  Updated:   {report['stats']['updated']}")
    print(f"  Skipped:   {report['stats']['skipped']}")
    print(f"  Errors:    {report['stats']['errors']}")
    print(f"  Time:      {report['stats']['elapsed_seconds']}s")
    print("="*60)


if __name__ == '__main__':
    main()
