"""
Global Analytics Aggregator
Pulls data from all registered vault instances and creates master analytics
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from collections import defaultdict
from datetime import datetime

from .vault_system_installer import VaultSystemInstaller, VaultInstance


class GlobalAnalyticsAggregator:
    """
    Aggregates analytics from all registered vault instances.
    Creates master sheets that combine data from all instances.
    """

    def __init__(self, installer: VaultSystemInstaller, global_output_path: Optional[Path] = None):
        self.installer = installer
        self.global_output_path = global_output_path or Path(__file__).parent.parent.parent / "Global_Analytics"
        self.global_output_path.mkdir(exist_ok=True)

    def aggregate_all(self) -> Dict:
        """
        Aggregate all analytics from all registered instances.
        
        Returns:
            Dictionary with aggregated data
        """
        instances = self.installer.list_instances()
        enabled_instances = [inst for inst in instances if inst.global_analytics_enabled]
        
        if not enabled_instances:
            return {"error": "No instances enabled for global analytics"}
        
        aggregated = {
            "aggregation_date": datetime.now().isoformat(),
            "instances_count": len(enabled_instances),
            "instances": [inst.vault_name for inst in enabled_instances],
            "master_sheets": {}
        }
        
        # Aggregate each master sheet type
        master_sheet_types = [
            "Axioms", "Breakthroughs", "Claims", "Definitions",
            "Evidence", "Mathematics", "References", "Tags",
            "Timeline", "Verified Links"
        ]
        
        for sheet_type in master_sheet_types:
            aggregated["master_sheets"][sheet_type] = self._aggregate_master_sheet(
                enabled_instances, sheet_type
            )
        
        # Save aggregated data
        output_file = self.global_output_path / "MASTER_AGGREGATED_ANALYTICS.json"
        output_file.write_text(json.dumps(aggregated, indent=2), encoding="utf-8")
        
        # Generate markdown reports
        self._generate_markdown_reports(aggregated, enabled_instances)
        
        return aggregated

    def _aggregate_master_sheet(
        self,
        instances: List[VaultInstance],
        sheet_type: str
    ) -> Dict:
        """Aggregate a specific master sheet type from all instances."""
        all_items = []
        item_sources = defaultdict(list)  # Track which instances have each item
        seen_items = set()  # Track unique items to avoid duplicates
        
        for instance in instances:
            master_sheets_path = instance.data_analytics_path / "Master Sheets" / sheet_type
            
            if not master_sheets_path.exists():
                continue
            
            # Read all files in this master sheet folder
            for file_path in master_sheets_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in [".md", ".json", ".yaml", ".yml"]:
                    try:
                        if file_path.suffix == ".json":
                            data = json.loads(file_path.read_text(encoding="utf-8"))
                            items = self._extract_items_from_json(data, sheet_type)
                        else:
                            # For markdown, extract structured data
                            items = self._extract_items_from_markdown(file_path, sheet_type)
                        
                        for item in items:
                            # Create unique identifier
                            item_id = self._create_item_id(item, sheet_type)
                            
                            if item_id not in seen_items:
                                seen_items.add(item_id)
                                item["source_instance"] = instance.vault_name
                                item["source_path"] = str(file_path.relative_to(instance.vault_path))
                                all_items.append(item)
                            else:
                                # Item already exists, just track source
                                item_sources[item_id].append(instance.vault_name)
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        return {
            "total_unique_items": len(all_items),
            "items": all_items,
            "duplicate_sources": dict(item_sources)
        }

    def _extract_items_from_json(self, data: Dict, sheet_type: str) -> List[Dict]:
        """Extract items from JSON data."""
        items = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Try common keys
            for key in ["items", "data", "definitions", "axioms", "claims", "tags"]:
                if key in data:
                    if isinstance(data[key], list):
                        items = data[key]
                        break
            if not items:
                items = [data]  # Single item
        
        return items

    def _extract_items_from_markdown(self, file_path: Path, sheet_type: str) -> List[Dict]:
        """Extract structured items from markdown files."""
        content = file_path.read_text(encoding="utf-8")
        items = []
        
        # Try to parse frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                # Has frontmatter
                frontmatter = parts[1]
                body = parts[2]
                
                # Parse YAML frontmatter
                try:
                    try:
                        import yaml
                        metadata = yaml.safe_load(frontmatter)
                    except ImportError:
                        # YAML not installed, parse manually
                        metadata = self._parse_yaml_manual(frontmatter)
                    
                    if metadata:
                        items.append({
                            "metadata": metadata,
                            "content": body.strip(),
                            "file": file_path.name
                        })
                except:
                    pass
        
        # If no frontmatter or parsing failed, treat entire file as one item
        if not items:
            items.append({
                "content": content.strip(),
                "file": file_path.name
            })
        
        return items

    def _parse_yaml_manual(self, yaml_text: str) -> Dict:
        """Simple YAML parser for basic key: value pairs."""
        result = {}
        for line in yaml_text.split('\n'):
            if ':' in line and not line.strip().startswith('#'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip().strip('"\'')
                    result[key] = value
        return result

    def _create_item_id(self, item: Dict, sheet_type: str) -> str:
        """Create a unique identifier for an item."""
        # Try different strategies based on item structure
        if "id" in item:
            return f"{sheet_type}_{item['id']}"
        elif "name" in item:
            return f"{sheet_type}_{item['name']}"
        elif "title" in item:
            return f"{sheet_type}_{item['title']}"
        elif "phrase" in item:
            return f"{sheet_type}_{item['phrase']}"
        elif "content" in item:
            # Use hash of content
            import hashlib
            content_hash = hashlib.md5(str(item["content"]).encode()).hexdigest()[:8]
            return f"{sheet_type}_{content_hash}"
        else:
            # Fallback: hash entire item
            import hashlib
            item_str = json.dumps(item, sort_keys=True)
            item_hash = hashlib.md5(item_str.encode()).hexdigest()[:8]
            return f"{sheet_type}_{item_hash}"

    def _generate_markdown_reports(self, aggregated: Dict, instances: List[VaultInstance]) -> None:
        """Generate markdown reports from aggregated data."""
        reports_dir = self.global_output_path / "Reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Master Summary Report
        summary_file = reports_dir / "GLOBAL_ANALYTICS_SUMMARY.md"
        summary_content = f"""# Global Analytics Summary

**Generated:** {aggregated['aggregation_date']}
**Instances:** {aggregated['instances_count']}
**Vaults:** {', '.join(aggregated['instances'])}

## Master Sheets Overview

"""
        
        for sheet_type, data in aggregated["master_sheets"].items():
            summary_content += f"### {sheet_type}\n"
            summary_content += f"- **Total Unique Items:** {data['total_unique_items']}\n"
            if data.get("duplicate_sources"):
                summary_content += f"- **Items in Multiple Vaults:** {len(data['duplicate_sources'])}\n"
            summary_content += "\n"
        
        summary_file.write_text(summary_content, encoding="utf-8")
        
        # Detailed reports for each master sheet type
        for sheet_type, data in aggregated["master_sheets"].items():
            if data["total_unique_items"] > 0:
                detail_file = reports_dir / f"GLOBAL_{sheet_type.upper()}.md"
                detail_content = f"""# Global {sheet_type}

**Total Items:** {data['total_unique_items']}
**Generated:** {aggregated['aggregation_date']}

## Items

"""
                for item in data["items"][:100]:  # Limit to first 100 for readability
                    detail_content += f"### Item from {item.get('source_instance', 'Unknown')}\n\n"
                    if "content" in item:
                        detail_content += f"{item['content'][:500]}...\n\n"
                    elif "metadata" in item:
                        detail_content += f"```yaml\n{item['metadata']}\n```\n\n"
                    detail_content += "---\n\n"
                
                detail_file.write_text(detail_content, encoding="utf-8")

