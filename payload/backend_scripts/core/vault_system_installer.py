"""
Vault Analytics System Installer
Portable, duplicatable system that can be deployed anywhere
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .settings_manager import SettingsManager


@dataclass
class VaultInstance:
    """Represents a vault analytics instance."""
    instance_id: str
    vault_name: str
    vault_path: Path
    installed_date: str
    version: str
    features_enabled: List[str]
    global_analytics_enabled: bool
    master_sheets_path: Path
    data_analytics_path: Path


class VaultSystemInstaller:
    """
    Installs and manages portable vault analytics systems.
    Can duplicate the entire system structure anywhere.
    """

    # System version
    SYSTEM_VERSION = "1.0.0"

    # Template structure (relative paths from vault root)
    TEMPLATE_STRUCTURE = {
        "00_VAULT_SYSTEM": {
            "01_Admin": {},
            "02_Config": {
                "Plugin_Configs": {}
            },
            "03_Docs": {
                "01_Templates": {},
                "02_Wizards": {},
                "03_Concepts": {},
                "04_Prompts": {},
                "05_Technical_Docs": {},
                "06_Dashboards": {},
                "07_Indices": {},
                "08_Papers": {},
                "Concept_Hubs": {}
            },
            "04_Analysis": {
                "00_CURRENT": {},
                "01_Scripts": {
                    "analysis": {},
                    "utilities": {},
                    "docker": {}
                },
                "02_Foundations": {},
                "02_System": {},
                "03_Templates": {},
                "04_Dashboards": {},
                "04_Integration": {},
                "05_Doctrine": {},
                "05_Hubs": {},
                "06_Wizards": {},
                "07_Data": {
                    "correlations": {},
                    "master_sheets": {},
                    "profiles": {}
                },
                "08_Tags": {
                    "Information": {},
                    "Philosophy": {},
                    "Physics": {},
                    "Theology": {},
                    "Theophysics": {}
                },
                "09_MOCs": {},
                "Data Analytics": {
                    "Dashboards": {},
                    "Exports": {},
                    "Master Sheets": {
                        "Axioms": {},
                        "Breakthroughs": {},
                        "Claims": {},
                        "Definitions": {},
                        "Evidence": {},
                        "Mathematics": {},
                        "References": {},
                        "Tags": {},
                        "Timeline": {},
                        "Verified Links": {}
                    },
                    "Reports": {}
                },
                "GLOBAL": {
                    "Breakthrough_Maps": {},
                    "Coherence_Reports": {},
                    "Concept_Networks": {},
                    "Evolution_Tracking": {}
                },
                "LOCAL_PAPERS": {},
                "Master Sheets": {}
            },
            "05_Workflow": {},
            "06_Assets": {
                "Images": {},
                "Prompts": {}
            },
            "07_Data": {},
            "08_Database": {},
            "09_Paper_Configs": {},
            "09_Templates": {},
            "10_Scripts": {},
            "11_MOCs": {
                "MOCs": {},
                "Topics": {},
                "Characters": {}
            },
            "12_Plugins": {},
            "AI Chat": {}
        }
    }

    # Template files to create
    TEMPLATE_FILES = {
        "00_VAULT_SYSTEM/README.md": """# Vault Analytics System

This vault uses the Theophysics Vault Analytics System.

## Features

- 📊 Data Analytics
- 📚 Paper Management
- 🏷️ Tag System
- 🔗 Link Analysis
- 📈 Dashboards
- 🤖 AI Integration

## Structure

- `04_Analysis/` - Analytics and scripts
- `Data Analytics/` - Analysis outputs
- `Master Sheets/` - Centralized data
- `09_Paper_Configs/` - Paper configurations

## Global Analytics

This instance is registered for global analytics aggregation.

**Instance ID:** {instance_id}
**Vault Name:** {vault_name}
**Installed:** {installed_date}
""",
        "00_VAULT_SYSTEM/04_Analysis/README.md": """# Theophysics Analysis System

A comprehensive analysis toolkit for the Theophysics vault.

## Quick Start

1. **Start the API server:**
   ```bash
   python 01_Scripts/api_server.py
   ```

2. **Run full vault analysis:**
   ```bash
   python 01_Scripts/grace_vault_manager.py --cli --vault /path/to/vault --auto
   ```

## Folder Structure

- `01_Scripts/` - Python scripts and automation
- `04_Dashboards/` - Dataview-powered dashboards
- `07_Data/` - Analysis output, databases, JSON
- `Data Analytics/` - Paper-specific analytics
- `GLOBAL/` - Global analytics aggregation
""",
        "00_VAULT_SYSTEM/04_Analysis/Data Analytics/README.md": """# Data Analytics

This folder contains the output of individual analysis runs. Each file in this directory represents a specific analysis scope (e.g., a single paper, a combination of papers, or the entire vault).

## Master Sheets

Centralized tracking to avoid duplicates:
- Axioms
- Breakthroughs
- Claims
- Definitions
- Evidence
- Mathematics
- References
- Tags
- Timeline
- Verified Links

## Global Analytics

This instance contributes to global analytics. See `GLOBAL/` folder for aggregated results.
""",
        "00_VAULT_SYSTEM/04_Analysis/Master Sheets/MASTER_ANALYTICS_SHEET.md": """# Master Analytics Sheet

This sheet contains the master aggregated data from all analysis runs. It is automatically updated by the analytics script.

## Master Tag Index

*This section will be populated with a master list of all tags in the vault.*

## Master Link Index

*This section will be populated with a master list of all links in the vault.*

## Master Math Index

*This section will be populated with a master list of all mathematical equations in the vault.*

## Script Action Log

*This section will log the actions taken by the analytics script.*

## Instance Information

**Instance ID:** {instance_id}
**Vault Name:** {vault_name}
**Last Updated:** {installed_date}
""",
        "00_VAULT_SYSTEM/04_Analysis/Data Analytics/Master Sheets/README.md": """# Master Sheets

Centralized tracking system to prevent duplicates and maintain consistency across papers.

## Structure

- **Axioms/** - All axioms from all papers
- **Breakthroughs/** - Key breakthroughs and insights
- **Claims/** - All claims made in papers
- **Definitions/** - All definitions (synced with Obsidian Definitions Manager)
- **Evidence/** - Supporting evidence
- **Mathematics/** - Mathematical equations and formulas
- **References/** - Citations and references
- **Tags/** - Tag master index
- **Timeline/** - Chronological events
- **Verified Links/** - Verified cross-references

## Global Integration

These master sheets are aggregated into global analytics when enabled.
"""
    }

    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.instances_file = Path(__file__).parent.parent.parent / "config" / "vault_instances.json"
        self.instances_file.parent.mkdir(exist_ok=True)
        self.instances: Dict[str, VaultInstance] = {}
        self._load_instances()

    def _load_instances(self) -> None:
        """Load registered instances."""
        if self.instances_file.exists():
            try:
                data = json.loads(self.instances_file.read_text(encoding="utf-8"))
                for inst_data in data.get("instances", []):
                    inst = VaultInstance(
                        instance_id=inst_data["instance_id"],
                        vault_name=inst_data["vault_name"],
                        vault_path=Path(inst_data["vault_path"]),
                        installed_date=inst_data["installed_date"],
                        version=inst_data["version"],
                        features_enabled=inst_data["features_enabled"],
                        global_analytics_enabled=inst_data["global_analytics_enabled"],
                        master_sheets_path=Path(inst_data["master_sheets_path"]),
                        data_analytics_path=Path(inst_data["data_analytics_path"])
                    )
                    self.instances[inst.instance_id] = inst
            except Exception as e:
                print(f"Error loading instances: {e}")

    def _save_instances(self) -> None:
        """Save registered instances."""
        data = {
            "version": self.SYSTEM_VERSION,
            "last_updated": datetime.now().isoformat(),
            "instances": [asdict(inst) for inst in self.instances.values()]
        }
        # Convert Path objects to strings
        for inst_dict in data["instances"]:
            inst_dict["vault_path"] = str(inst_dict["vault_path"])
            inst_dict["master_sheets_path"] = str(inst_dict["master_sheets_path"])
            inst_dict["data_analytics_path"] = str(inst_dict["data_analytics_path"])
        
        self.instances_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def install_system(
        self,
        vault_path: Path,
        vault_name: Optional[str] = None,
        features: Optional[List[str]] = None,
        enable_global_analytics: bool = True
    ) -> VaultInstance:
        """
        Install the complete vault analytics system to a vault.
        
        Args:
            vault_path: Path to the vault root
            vault_name: Name for this vault (defaults to folder name)
            features: List of features to enable (None = all)
            enable_global_analytics: Whether to register for global analytics
        
        Returns:
            VaultInstance object
        """
        vault_path = Path(vault_path).resolve()
        
        if not vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")
        
        if vault_name is None:
            vault_name = vault_path.name
        
        # Generate instance ID
        instance_id = f"{vault_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create directory structure
        system_root = vault_path / "00_VAULT_SYSTEM"
        self._create_structure(system_root, self.TEMPLATE_STRUCTURE["00_VAULT_SYSTEM"])
        
        # Create template files
        self._create_template_files(system_root, instance_id, vault_name)
        
        # Create instance record
        instance = VaultInstance(
            instance_id=instance_id,
            vault_name=vault_name,
            vault_path=vault_path,
            installed_date=datetime.now().isoformat(),
            version=self.SYSTEM_VERSION,
            features_enabled=features or ["all"],
            global_analytics_enabled=enable_global_analytics,
            master_sheets_path=system_root / "04_Analysis" / "Master Sheets",
            data_analytics_path=system_root / "04_Analysis" / "Data Analytics"
        )
        
        # Register instance
        self.instances[instance_id] = instance
        self._save_instances()
        
        # Create instance registry file in vault
        registry_file = system_root / "INSTANCE_REGISTRY.json"
        registry_file.write_text(json.dumps(asdict(instance), indent=2, default=str), encoding="utf-8")
        
        return instance

    def _create_structure(self, root: Path, structure: Dict) -> None:
        """Recursively create directory structure."""
        for name, children in structure.items():
            dir_path = root / name
            dir_path.mkdir(parents=True, exist_ok=True)
            if children:
                self._create_structure(dir_path, children)

    def _create_template_files(self, system_root: Path, instance_id: str, vault_name: str) -> None:
        """Create template files with variable substitution."""
        for rel_path, template_content in self.TEMPLATE_FILES.items():
            file_path = system_root / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = template_content.format(
                instance_id=instance_id,
                vault_name=vault_name,
                installed_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            file_path.write_text(content, encoding="utf-8")

    def list_instances(self) -> List[VaultInstance]:
        """List all registered instances."""
        return list(self.instances.values())

    def get_instance(self, instance_id: str) -> Optional[VaultInstance]:
        """Get a specific instance by ID."""
        return self.instances.get(instance_id)

    def unregister_instance(self, instance_id: str) -> bool:
        """Unregister an instance (doesn't delete files)."""
        if instance_id in self.instances:
            del self.instances[instance_id]
            self._save_instances()
            return True
        return False

    def update_instance(self, instance_id: str, **kwargs) -> bool:
        """Update instance properties."""
        if instance_id not in self.instances:
            return False
        
        instance = self.instances[instance_id]
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self._save_instances()
        return True

