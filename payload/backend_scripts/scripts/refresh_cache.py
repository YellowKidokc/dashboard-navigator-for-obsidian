"""
Refresh Cache - Scan vault and update SQLite cache

This script scans the vault and populates the cache with fresh statistics.
"""

import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json
import re

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stats_cache import StatsCache, VaultStats


class VaultScanner:
    """
    Scans the vault and collects statistics.
    """

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.cache = StatsCache(vault_path)

        # Patterns to identify content types
        self.paper_patterns = [r'P\d{2}', r'Paper', r'paper']
        self.definition_patterns = [r'::definition::', r'Definition:', r'DEF-']
        self.tag_pattern = re.compile(r'#[\w/-]+')
        self.link_pattern = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')

    def refresh_all(self):
        """Refresh all cached statistics."""
        print("=" * 50)
        print("REFRESHING VAULT CACHE")
        print("=" * 50)
        print(f"Vault: {self.vault_path}")

        # Clear old cache
        print("\n→ Clearing old cache...")
        self.cache.clear_all()

        # Scan vault
        print("\n→ Scanning vault...")
        stats = self.scan_vault()

        # Save to cache
        print("\n→ Saving to cache...")
        self.cache.save_vault_stats(stats)

        # Scan for definitions
        print("\n→ Scanning definitions...")
        self.scan_definitions()

        # Scan tags
        print("\n→ Scanning tags...")
        self.scan_tags()

        # Scan papers
        print("\n→ Scanning papers...")
        self.scan_papers()

        print("\n" + "=" * 50)
        print("CACHE REFRESH COMPLETE")
        print("=" * 50)
        self.print_summary(stats)

    def scan_vault(self) -> VaultStats:
        """Scan entire vault and return statistics."""
        stats = VaultStats()

        total_words = 0
        total_links = 0
        papers_found = 0
        definitions_found = 0
        tags_found = set()

        # Scan all markdown files
        md_files = list(self.vault_path.rglob("*.md"))
        stats.total_notes = len(md_files)

        for file_path in md_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Count words
                words = len(content.split())
                total_words += words

                # Count links
                links = self.link_pattern.findall(content)
                total_links += len(links)

                # Check if paper
                file_name = file_path.name
                for pattern in self.paper_patterns:
                    if re.search(pattern, file_name):
                        papers_found += 1
                        break

                # Check for definitions
                for pattern in self.definition_patterns:
                    if re.search(pattern, content):
                        definitions_found += 1
                        break

                # Extract tags
                file_tags = self.tag_pattern.findall(content)
                tags_found.update(file_tags)

            except Exception as e:
                print(f"  ⚠ Error reading {file_path.name}: {e}")

        stats.total_words = total_words
        stats.total_links = total_links
        stats.total_papers = papers_found
        stats.total_definitions = definitions_found
        stats.total_tags = len(tags_found)

        return stats

    def scan_definitions(self):
        """Scan for definition health."""
        incomplete = []
        missing = []

        # Look for definition files
        for file_path in self.vault_path.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")

                # Check if it's a definition file
                is_definition = any(re.search(p, content) for p in self.definition_patterns)

                if is_definition:
                    # Check completeness (simple heuristic: look for key sections)
                    has_description = "description" in content.lower() or "##" in content
                    has_content = len(content) > 200

                    if not (has_description and has_content):
                        incomplete.append({
                            "file": file_path.name,
                            "path": str(file_path.relative_to(self.vault_path)),
                            "size": len(content)
                        })

            except Exception:
                pass

        # Cache the results
        self.cache.cache_definition_health(incomplete, missing)
        print(f"  Found {len(incomplete)} incomplete definitions")

    def scan_tags(self):
        """Scan and categorize all tags."""
        tag_counts = defaultdict(int)
        tag_types = defaultdict(int)

        for file_path in self.vault_path.rglob("*.md"):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                tags = self.tag_pattern.findall(content)

                for tag in tags:
                    tag_counts[tag] += 1

                    # Categorize by prefix
                    if "/" in tag:
                        prefix = tag.split("/")[0]
                        tag_types[prefix] += 1
                    else:
                        tag_types["simple"] += 1

            except Exception:
                pass

        # Get top tags
        top_tags = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:50])

        stats = {
            "total_unique": len(tag_counts),
            "total_usage": sum(tag_counts.values()),
            "top_tags": top_tags,
            "by_type": dict(tag_types)
        }

        self.cache.cache_tag_stats(stats)
        print(f"  Found {len(tag_counts)} unique tags")

    def scan_papers(self):
        """Scan paper files and their status."""
        papers = []
        status_counts = defaultdict(int)

        for file_path in self.vault_path.rglob("*.md"):
            file_name = file_path.name

            # Check if it's a paper
            for pattern in self.paper_patterns:
                if re.search(pattern, file_name):
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")

                        # Determine status from frontmatter or content
                        status = "unknown"
                        if "status:" in content.lower():
                            match = re.search(r'status:\s*(\w+)', content, re.IGNORECASE)
                            if match:
                                status = match.group(1).lower()
                        elif "draft" in content.lower():
                            status = "draft"
                        elif "complete" in content.lower() or "final" in content.lower():
                            status = "complete"
                        else:
                            status = "in_progress"

                        status_counts[status] += 1
                        papers.append({
                            "file": file_name,
                            "status": status,
                            "size": len(content)
                        })

                    except Exception:
                        pass
                    break

        stats = {
            "total": len(papers),
            "by_status": dict(status_counts),
            "papers": papers
        }

        self.cache.cache_paper_stats(stats)
        print(f"  Found {len(papers)} papers")

    def print_summary(self, stats: VaultStats):
        """Print summary of cached data."""
        print(f"""
CACHE SUMMARY:
--------------
Total Notes:       {stats.total_notes}
Total Words:       {stats.total_words:,}
Total Links:       {stats.total_links}
Total Papers:      {stats.total_papers}
Total Definitions: {stats.total_definitions}
Total Tags:        {stats.total_tags}

Last Updated: {stats.last_updated}

Run 'python scripts/export_to_obsidian.py' to export to Obsidian.
""")


def main():
    """Main entry point."""
    backend_path = Path(__file__).parent.parent

    # Try to find vault path from config
    config_file = backend_path / "theophysics_config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        vault_path = config.get("vault_path", str(backend_path.parent.parent / "Theophysics_Master"))
    else:
        # Default: look for Theophysics_Master sibling
        vault_path = str(backend_path.parent.parent / "Theophysics_Master")

    # Allow override via command line
    if len(sys.argv) > 1:
        vault_path = sys.argv[1]

    if not Path(vault_path).exists():
        print(f"⚠ Vault path not found: {vault_path}")
        print("Usage: python refresh_cache.py [vault_path]")
        sys.exit(1)

    scanner = VaultScanner(vault_path)
    scanner.refresh_all()


if __name__ == "__main__":
    main()
