"""
Plugin Data Aggregator
Aggregates data from all Obsidian plugins and prepares for PostgreSQL export.

Plugins:
- Word-ontology: Classifications, semantic blocks
- Obsidian-Plugin-Module-Notes: Axioms, Evidence, Claims, Timeline, etc.
- Obsidian-link-tag-plugin: Classifications, PostgreSQL sync
- Obsidian-Tags-Data-Analytics: Tag analytics, definitions
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import re


@dataclass
class PluginDataSource:
    """Represents a plugin data source."""
    name: str
    path: Path
    enabled: bool = True
    last_synced: Optional[str] = None


class PluginDataAggregator:
    """Aggregates data from all Obsidian plugins."""
    
    def __init__(self, aggregation_target: Path):
        """
        Initialize aggregator.
        
        Args:
            aggregation_target: Path to Obsidian-Theophysics-research folder
        """
        self.aggregation_target = Path(aggregation_target)
        self.aggregation_target.mkdir(parents=True, exist_ok=True)
        
        # Plugin paths (on D: drive root)
        self.plugins = {
            "word_ontology": PluginDataSource(
                "Word Ontology",
                Path(r"D:\Word-ontology")
            ),
            "module_notes": PluginDataSource(
                "Module Notes",
                Path(r"D:\Obsidian-Plugin-Module-Notes")
            ),
            "link_tag": PluginDataSource(
                "Link Tag Plugin",
                Path(r"D:\Obsidian-link-tag-plugin")
            ),
            "tags_analytics": PluginDataSource(
                "Tags Analytics",
                Path(r"D:\Obsidian-Tags-Data-Analytics")
            )
        }
        
        # Output structure
        self.output_structure = {
            "axioms": [],
            "claims": [],
            "evidence": [],
            "definitions": [],
            "classifications": [],
            "tags": [],
            "timeline_events": [],
            "semantic_blocks": [],
            "math_equations": [],
            "theories": [],
            "coherence_scores": []
        }
    
    def scan_all_plugins(self) -> Dict[str, Any]:
        """Scan all enabled plugins and extract data."""
        results = {
            "scan_date": datetime.now().isoformat(),
            "plugins": {},
            "aggregated": self.output_structure.copy()
        }
        
        for plugin_id, plugin in self.plugins.items():
            if not plugin.enabled:
                continue
            
            if not plugin.path.exists():
                results["plugins"][plugin_id] = {
                    "status": "not_found",
                    "path": str(plugin.path)
                }
                continue
            
            try:
                plugin_data = self._scan_plugin(plugin_id, plugin.path)
                results["plugins"][plugin_id] = {
                    "status": "success",
                    "data_count": sum(len(v) if isinstance(v, list) else 1 for v in plugin_data.values()),
                    "last_synced": datetime.now().isoformat()
                }
                
                # Merge into aggregated data
                for key, value in plugin_data.items():
                    if key in results["aggregated"]:
                        if isinstance(value, list):
                            results["aggregated"][key].extend(value)
                        else:
                            results["aggregated"][key].append(value)
            
            except Exception as e:
                results["plugins"][plugin_id] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results
    
    def _scan_plugin(self, plugin_id: str, plugin_path: Path) -> Dict[str, Any]:
        """Scan a specific plugin for data."""
        data = {}
        
        if plugin_id == "word_ontology":
            data = self._scan_word_ontology(plugin_path)
        elif plugin_id == "module_notes":
            data = self._scan_module_notes(plugin_path)
        elif plugin_id == "link_tag":
            data = self._scan_link_tag(plugin_path)
        elif plugin_id == "tags_analytics":
            data = self._scan_tags_analytics(plugin_path)
        
        return data
    
    def _scan_word_ontology(self, plugin_path: Path) -> Dict[str, Any]:
        """Scan Word Ontology plugin."""
        data = {
            "classifications": [],
            "semantic_blocks": []
        }
        
        # Check for data.json
        data_json = plugin_path / "data.json"
        if data_json.exists():
            try:
                with open(data_json, 'r', encoding='utf-8') as f:
                    ontology_data = json.load(f)
                    # Extract classifications if present
                    if isinstance(ontology_data, dict):
                        data["classifications"].append(ontology_data)
            except Exception as e:
                print(f"Error reading Word Ontology data.json: {e}")
        
        return data
    
    def _scan_module_notes(self, plugin_path: Path) -> Dict[str, Any]:
        """Scan Module Notes plugin."""
        data = {
            "axioms": [],
            "claims": [],
            "evidence": [],
            "timeline_events": [],
            "theories": []
        }
        
        # Look for master truth or data files
        master_truth = plugin_path / "03_MASTER_TRUTH"
        if master_truth.exists():
            # Scan for markdown files with structured data
            for md_file in master_truth.rglob("*.md"):
                content = md_file.read_text(encoding='utf-8')
                # Extract semantic blocks
                semantic_blocks = self._extract_semantic_blocks(content)
                if semantic_blocks:
                    data["semantic_blocks"].extend(semantic_blocks)
        
        return data
    
    def _scan_link_tag(self, plugin_path: Path) -> Dict[str, Any]:
        """Scan Link Tag plugin."""
        data = {
            "classifications": [],
            "definitions": []
        }
        
        # Check for glossary manager
        glossary_file = plugin_path / "glossary-manager.js"
        if glossary_file.exists():
            # Could parse JavaScript for definitions, but better to read from vault
            pass
        
        return data
    
    def _scan_tags_analytics(self, plugin_path: Path) -> Dict[str, Any]:
        """Scan Tags Analytics plugin."""
        data = {
            "tags": [],
            "definitions": []
        }
        
        # Check Python extraction script output
        python_dir = plugin_path / "python"
        if python_dir.exists():
            # Look for output JSON files
            for json_file in python_dir.rglob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        tag_data = json.load(f)
                        if isinstance(tag_data, list):
                            data["tags"].extend(tag_data)
                        elif isinstance(tag_data, dict):
                            data["tags"].append(tag_data)
                except Exception as e:
                    print(f"Error reading {json_file}: {e}")
        
        return data
    
    def _extract_semantic_blocks(self, content: str) -> List[Dict]:
        """Extract semantic blocks from markdown content."""
        blocks = []
        pattern = r'%%semantic\s+(.*?)\s+%%'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            try:
                block_data = json.loads(match.group(1))
                blocks.append(block_data)
            except json.JSONDecodeError:
                # Try YAML
                try:
                    block_data = yaml.safe_load(match.group(1))
                    if block_data:
                        blocks.append(block_data)
                except Exception:
                    pass
        
        return blocks
    
    def aggregate_to_postgres_format(self, aggregated_data: Dict) -> Dict:
        """Convert aggregated data to PostgreSQL-compatible format."""
        postgres_data = {
            "notes": [],
            "classifications": [],
            "tag_nodes": [],
            "tag_statistics": [],
            "tag_definitions": [],
            "timeline_events": []
        }
        
        # Convert classifications
        for classification in aggregated_data.get("classifications", []):
            postgres_data["classifications"].append({
                "id": self._generate_uuid(),
                "content": classification.get("content", ""),
                "type": classification.get("type", "unknown"),
                "file": classification.get("file", ""),
                "timestamp": datetime.now().isoformat()
            })
        
        # Convert definitions
        for definition in aggregated_data.get("definitions", []):
            postgres_data["tag_definitions"].append({
                "id": self._generate_uuid(),
                "tag": definition.get("tag", ""),
                "definition_text": definition.get("text", ""),
                "source": definition.get("source", "user"),
                "file": definition.get("file", "")
            })
        
        # Convert tags
        for tag in aggregated_data.get("tags", []):
            postgres_data["tag_nodes"].append({
                "id": self._generate_uuid(),
                "tag": tag.get("tag", ""),
                "content": tag.get("content", ""),
                "file": tag.get("file", ""),
                "occurrence_count": tag.get("count", 1)
            })
        
        return postgres_data
    
    def _generate_uuid(self) -> str:
        """Generate a simple UUID-like string."""
        import uuid
        return str(uuid.uuid4())
    
    def save_aggregated_data(self, data: Dict, format: str = "json") -> Path:
        """Save aggregated data to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            output_file = self.aggregation_target / f"aggregated_data_{timestamp}.json"
            output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        elif format == "yaml":
            output_file = self.aggregation_target / f"aggregated_data_{timestamp}.yaml"
            output_file.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        
        return output_file
    
    def export_to_postgres(self, postgres_data: Dict, connection_string: str) -> bool:
        """Export data to PostgreSQL database."""
        try:
            import psycopg2
            from psycopg2.extras import execute_batch
            
            # Parse connection string
            # Format: postgresql://user:password@host:port/database
            conn_str = connection_string.replace("postgresql://", "")
            user_pass, host_db = conn_str.split("@")
            user, password = user_pass.split(":")
            host, port_db = host_db.split(":")
            port, database = port_db.split("/")
            
            # Connect
            conn = psycopg2.connect(
                host=host,
                port=int(port),
                database=database,
                user=user,
                password=password
            )
            cur = conn.cursor()
            
            # Insert classifications
            if postgres_data.get("classifications"):
                insert_class = """
                    INSERT INTO theophysics.classifications 
                    (id, content, type_id, note_id, start_offset, end_offset, tagged_at)
                    VALUES (%s, %s, 
                        (SELECT id FROM theophysics.epistemic_types WHERE name = %s),
                        (SELECT id FROM theophysics.notes WHERE file_path = %s),
                        %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
                # Would need to prepare data properly
                # execute_batch(cur, insert_class, classifications_data)
            
            # Insert tag definitions
            if postgres_data.get("tag_definitions"):
                insert_def = """
                    INSERT INTO tag_definitions 
                    (id, tag, definition_text, source, file, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """
                def_data = [
                    (d["id"], d["tag"], d["definition_text"], d["source"], d.get("file", ""), datetime.now())
                    for d in postgres_data["tag_definitions"]
                ]
                execute_batch(cur, insert_def, def_data)
            
            conn.commit()
            cur.close()
            conn.close()
            
            return True
        
        except ImportError:
            print("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            print(f"Error exporting to PostgreSQL: {e}")
            return False

