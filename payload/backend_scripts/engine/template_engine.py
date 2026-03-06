# engine/template_engine.py
"""
Template Engine for Theophysics Research
========================================
Handles folder structure mimicking and analytics replication.
"""

import shutil
import os
from pathlib import Path
from typing import Optional, List, Dict
import yaml

class TemplateEngine:
    """
    Manages creation of folder structures and copying of analytics tools.
    """

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.templates_dir = self.vault_path / "00_VAULT_SYSTEM" / "09_Templates"
        self.global_analytics_dir = self.vault_path / "00_VAULT_SYSTEM" / "Global_Analytics"

    def list_templates(self) -> List[str]:
        """List available folder templates."""
        if not self.templates_dir.exists():
            return []
        return [d.name for d in self.templates_dir.iterdir() if d.is_dir()]

    def create_from_template(self, template_name: str, target_name: str, target_parent: Path = None) -> Path:
        """
        Create a new folder structure based on a template.
        
        Args:
            template_name: Name of the template (subfolder in 09_Templates) OR absolute path to a folder to mimic.
            target_name: Name of the new folder to create.
            target_parent: Where to create the new folder. Defaults to vault root.
        
        Returns:
            Path to the created folder.
        """
        if target_parent is None:
            target_parent = self.vault_path

        target_path = target_parent / target_name
        
        # Check if template_name is a name in templates_dir or a path
        source_path = self.templates_dir / template_name
        if not source_path.exists():
            # Try as absolute path
            source_path = Path(template_name)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found.")

        if target_path.exists():
            raise FileExistsError(f"Target '{target_path}' already exists.")

        # Copy the structure
        shutil.copytree(source_path, target_path)
        
        return target_path

    def replicate_analytics(self, target_folder: Path):
        """
        Copy Global Analytics tools to a local target folder.
        
        Args:
            target_folder: The folder where analytics should be enabled (e.g. a paper folder).
        """
        if not self.global_analytics_dir.exists():
            # Try alternative location
            alt_loc = self.vault_path / "Global OR LOCAL" / "Global_Analytics"
            if alt_loc.exists():
                self.global_analytics_dir = alt_loc
            else:
                raise FileNotFoundError("Global Analytics directory not found.")

        if not target_folder.exists():
            raise FileNotFoundError(f"Target folder '{target_folder}' does not exist.")

        local_analytics_path = target_folder / "Local_Analytics"
        
        if local_analytics_path.exists():
             print(f"Local Analytics already exists in {target_folder}")
             # Optional: update files? For now, skip to avoid overwrite data
             return local_analytics_path

        shutil.copytree(self.global_analytics_dir, local_analytics_path)
        
        # Create a config file indicating this is a local instance
        config_path = local_analytics_path / "analytics_config.yaml"
        config = {
            "mode": "local",
            "scope": str(target_folder.relative_to(self.vault_path) if target_folder.is_relative_to(self.vault_path) else target_folder.name),
            "origin": "Global_Analytics",
            "created_at": str(os.path.getctime(str(local_analytics_path)))
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
            
        return local_analytics_path

    def create_analytics_sandbox(self, name: str) -> Path:
        """Create a new folder with Local Analytics pre-installed."""
        # Create folder
        path = self.vault_path / name
        path.mkdir(exist_ok=True)
        
        # Install analytics
        self.replicate_analytics(path)
        
        return path
