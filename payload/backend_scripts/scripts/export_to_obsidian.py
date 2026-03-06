"""
Export to Obsidian - Bridge Python cache to Obsidian markdown dashboards

This script reads cached data from SQLite and generates markdown files
that Obsidian dashboards can display.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stats_cache import StatsCache, VaultStats


class ObsidianExporter:
    """
    Exports cached analytics data to Obsidian-readable markdown files.
    """

    def __init__(self, vault_path: str, obsidian_output_path: str):
        self.vault_path = Path(vault_path)
        self.output_path = Path(obsidian_output_path)
        self.cache = StatsCache(vault_path)

        # Ensure output directories exist
        self.reports_path = self.output_path / "02_Python_Engine" / "reports"
        self.cache_path = self.reports_path / "cache"
        self.charts_path = self.reports_path / "charts"

        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.charts_path.mkdir(parents=True, exist_ok=True)

    def export_all(self):
        """Export all cached data to Obsidian markdown."""
        print("=" * 50)
        print("EXPORTING CACHE TO OBSIDIAN")
        print("=" * 50)

        # Export vault stats
        self.export_vault_stats()

        # Export definition health
        self.export_definition_health()

        # Export tag stats
        self.export_tag_stats()

        # Export paper stats
        self.export_paper_stats()

        # Export cache summary
        self.export_cache_summary()

        # Update timestamp
        self.update_timestamp()

        print("\n✓ Export complete!")
        print(f"  Output: {self.output_path}")

    def export_vault_stats(self):
        """Export vault statistics."""
        print("\n→ Exporting vault stats...")

        stats = self.cache.get_vault_stats()

        if stats:
            content = f"""---
type: cache_data
source: python_backend
updated: {stats.last_updated}
---

# Vault Statistics

| Metric | Value |
|--------|-------|
| Total Notes | {stats.total_notes} |
| Total Definitions | {stats.total_definitions} |
| Total Papers | {stats.total_papers} |
| Total Tags | {stats.total_tags} |
| Total Words | {stats.total_words:,} |
| Total Links | {stats.total_links} |
| Incomplete Definitions | {stats.incomplete_definitions} |
| Missing Definitions | {stats.missing_definitions} |

## Papers by Status

| Status | Count |
|--------|-------|
"""
            for status, count in stats.papers_by_status.items():
                content += f"| {status} | {count} |\n"

            content += """
## Tags by Type

| Type | Count |
|------|-------|
"""
            for tag_type, count in stats.tags_by_type.items():
                content += f"| {tag_type} | {count} |\n"

            output_file = self.cache_path / "vault_stats.md"
            output_file.write_text(content, encoding="utf-8")
            print(f"  ✓ {output_file.name}")
        else:
            print("  ⚠ No vault stats in cache")

    def export_definition_health(self):
        """Export definition health data."""
        print("\n→ Exporting definition health...")

        health = self.cache.get_definition_health()

        content = f"""---
type: cache_data
source: python_backend
---

# Definition Health

| Metric | Count |
|--------|-------|
| Incomplete Definitions | {health['incomplete_count']} |
| Missing Definitions | {health['missing_count']} |
| Cache Age (seconds) | {health['age'] or 'N/A'} |

## Incomplete Definitions

"""
        for item in health['incomplete'][:20]:
            if isinstance(item, dict):
                content += f"- {item.get('name', item.get('file', str(item)))}\n"
            else:
                content += f"- {item}\n"

        if len(health['incomplete']) > 20:
            content += f"\n*...and {len(health['incomplete']) - 20} more*\n"

        content += """
## Missing Definitions

"""
        for item in health['missing'][:20]:
            if isinstance(item, dict):
                content += f"- {item.get('term', item.get('file', str(item)))}\n"
            else:
                content += f"- {item}\n"

        if len(health['missing']) > 20:
            content += f"\n*...and {len(health['missing']) - 20} more*\n"

        output_file = self.cache_path / "definition_health.md"
        output_file.write_text(content, encoding="utf-8")
        print(f"  ✓ {output_file.name}")

    def export_tag_stats(self):
        """Export tag statistics."""
        print("\n→ Exporting tag stats...")

        stats = self.cache.get_tag_stats()

        if stats:
            content = f"""---
type: cache_data
source: python_backend
---

# Tag Statistics

"""
            if isinstance(stats, dict):
                content += "| Metric | Value |\n|--------|-------|\n"
                for key, value in stats.items():
                    if isinstance(value, (int, float, str)):
                        content += f"| {key} | {value} |\n"

                # Handle nested structures
                for key, value in stats.items():
                    if isinstance(value, dict):
                        content += f"\n## {key}\n\n"
                        content += "| Item | Count |\n|------|-------|\n"
                        for k, v in list(value.items())[:30]:
                            content += f"| {k} | {v} |\n"
                    elif isinstance(value, list):
                        content += f"\n## {key}\n\n"
                        for item in value[:30]:
                            content += f"- {item}\n"

            output_file = self.cache_path / "tag_stats.md"
            output_file.write_text(content, encoding="utf-8")
            print(f"  ✓ {output_file.name}")
        else:
            print("  ⚠ No tag stats in cache")

    def export_paper_stats(self):
        """Export paper statistics."""
        print("\n→ Exporting paper stats...")

        stats = self.cache.get_paper_stats()

        if stats:
            content = f"""---
type: cache_data
source: python_backend
---

# Paper Statistics

"""
            if isinstance(stats, dict):
                content += "| Metric | Value |\n|--------|-------|\n"
                for key, value in stats.items():
                    if isinstance(value, (int, float, str)):
                        content += f"| {key} | {value} |\n"

            output_file = self.cache_path / "paper_stats.md"
            output_file.write_text(content, encoding="utf-8")
            print(f"  ✓ {output_file.name}")
        else:
            print("  ⚠ No paper stats in cache")

    def export_cache_summary(self):
        """Export cache summary."""
        print("\n→ Exporting cache summary...")

        summary = self.cache.get_cache_summary()

        content = f"""---
type: cache_data
source: python_backend
generated: {datetime.now().isoformat()}
---

# Cache Summary

**Key-Value Entries:** {summary['kv_count']}

## Cached Items

| Type | Key | Updated |
|------|-----|---------|
"""
        for item in summary['items']:
            count_str = f" ({item.get('count', '')} items)" if 'count' in item else ""
            content += f"| {item['type']} | {item['key']}{count_str} | {item['updated']} |\n"

        output_file = self.cache_path / "cache_summary.md"
        output_file.write_text(content, encoding="utf-8")
        print(f"  ✓ {output_file.name}")

    def update_timestamp(self):
        """Update the timestamp file."""
        content = f"""---
type: timestamp
---

**Last Export:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Run `python scripts/export_to_obsidian.py` to refresh*
"""
        output_file = self.cache_path / "cache_timestamp.md"
        output_file.write_text(content, encoding="utf-8")


def main():
    """Main entry point."""
    # Default paths
    backend_path = Path(__file__).parent.parent

    # Try to find vault path from config
    config_file = backend_path / "theophysics_config.json"
    if config_file.exists():
        config = json.loads(config_file.read_text())
        vault_path = config.get("vault_path", str(backend_path))
    else:
        vault_path = str(backend_path)

    # Default Obsidian output path
    # Adjust this to match your vault structure
    obsidian_output = Path(vault_path).parent / "Theophysics_Master" / "Theophysics Master" / "01_CANONICAL" / "_GLOBAL_ANALYTICS" / "Global_Analytics"

    # Allow override via command line
    if len(sys.argv) > 1:
        obsidian_output = Path(sys.argv[1])

    print(f"Vault Path: {vault_path}")
    print(f"Output Path: {obsidian_output}")

    if not obsidian_output.exists():
        print(f"\n⚠ Output path doesn't exist. Creating...")
        obsidian_output.mkdir(parents=True, exist_ok=True)

    exporter = ObsidianExporter(vault_path, str(obsidian_output))
    exporter.export_all()


if __name__ == "__main__":
    main()
