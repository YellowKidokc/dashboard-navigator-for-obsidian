# engine/api_query_engine.py
"""
API Query Engine - Template building and parameter management
Part of Theophysics Backend
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
import threading
import time


class QueryTemplate:
    """
    Represents a parameterized query template.
    
    Example:
        template = QueryTemplate(
            name="Divorce Rate by Year",
            base_params={"indicator": "divorce_rate"},
            variables={
                "years": {
                    "type": "dropdown",
                    "options": [1, 5, 10, 20],
                    "default": 5,
                    "label": "Years of Data"
                },
                "state": {
                    "type": "dropdown", 
                    "options": ["CA", "TX", "NY", "FL"],
                    "default": "CA",
                    "label": "State"
                }
            }
        )
    """
    
    def __init__(self, name: str, base_params: Dict = None, 
                 variables: Dict = None, description: str = ""):
        self.name = name
        self.base_params = base_params or {}
        self.variables = variables or {}
        self.description = description
    
    def get_variable_options(self, var_name: str) -> List:
        """Get dropdown options for a variable"""
        if var_name in self.variables:
            return self.variables[var_name].get("options", [])
        return []
    
    def get_default_value(self, var_name: str) -> Any:
        """Get default value for a variable"""
        if var_name in self.variables:
            return self.variables[var_name].get("default")
        return None
    
    def build_params(self, variable_values: Dict = None) -> Dict:
        """Build final params by merging base + variable values"""
        params = self.base_params.copy()
        
        # Apply variable values (or defaults)
        for var_name, var_config in self.variables.items():
            if variable_values and var_name in variable_values:
                params[var_name] = variable_values[var_name]
            else:
                params[var_name] = var_config.get("default")
        
        return params
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for saving"""
        return {
            "name": self.name,
            "base_params": self.base_params,
            "variables": self.variables,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QueryTemplate':
        """Create from dictionary"""
        return cls(
            name=data.get("name", "Unnamed"),
            base_params=data.get("base_params", {}),
            variables=data.get("variables", {}),
            description=data.get("description", "")
        )


class APIQueryEngine:
    """
    Engine for building and managing API queries.
    """
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.templates: Dict[str, QueryTemplate] = {}
        self.scheduled_jobs: List[Dict] = []
        self._scheduler_thread = None
        self._scheduler_running = False
        
        self._load_templates()
    
    def _load_templates(self):
        """Load saved templates"""
        template_file = self.api_manager.config_path / "api_templates.json"
        if template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for name, tpl_data in data.get("templates", {}).items():
                    self.templates[name] = QueryTemplate.from_dict(tpl_data)
    
    def save_templates(self):
        """Save templates to config"""
        template_file = self.api_manager.config_path / "api_templates.json"
        data = {
            "templates": {
                name: tpl.to_dict() 
                for name, tpl in self.templates.items()
            }
        }
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def create_template(self, name: str, base_params: Dict = None,
                        variables: Dict = None, description: str = "") -> QueryTemplate:
        """Create and save a new template"""
        template = QueryTemplate(name, base_params, variables, description)
        self.templates[name] = template
        self.save_templates()
        return template
    
    def get_template(self, name: str) -> Optional[QueryTemplate]:
        """Get template by name"""
        return self.templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all template names"""
        return list(self.templates.keys())
    
    def delete_template(self, name: str):
        """Delete a template"""
        if name in self.templates:
            del self.templates[name]
            self.save_templates()
    
    # =========================================
    # QUICK QUERY BUILDERS
    # =========================================
    
    def build_year_range_query(self, base_params: Dict, 
                               year_options: List[int] = None) -> QueryTemplate:
        """
        Quick builder for year-based queries.
        E.g., "last N years" queries
        """
        if year_options is None:
            year_options = [1, 2, 5, 10, 15, 20, 25, 50]
        
        return QueryTemplate(
            name="Year Range Query",
            base_params=base_params,
            variables={
                "years": {
                    "type": "dropdown",
                    "options": year_options,
                    "default": year_options[2] if len(year_options) > 2 else year_options[0],
                    "label": "Years of Data"
                }
            }
        )
    
    def build_state_query(self, base_params: Dict,
                          states: List[str] = None) -> QueryTemplate:
        """Quick builder for state-based queries"""
        if states is None:
            states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                      "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                      "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                      "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                      "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
        
        return QueryTemplate(
            name="State Query",
            base_params=base_params,
            variables={
                "state": {
                    "type": "dropdown",
                    "options": states,
                    "default": "CA",
                    "label": "State"
                }
            }
        )
    
    def build_combo_query(self, name: str, base_params: Dict,
                          variables: Dict) -> QueryTemplate:
        """Build a custom query with multiple dropdowns"""
        return self.create_template(name, base_params, variables)
    
    # =========================================
    # BATCH EXECUTION
    # =========================================
    
    def run_all_options(self, template: QueryTemplate, 
                        endpoint_id: str, job_id: str = None,
                        callback: Callable = None) -> List[Dict]:
        """
        Run query for ALL combinations of variable options.
        
        callback(current, total, result) - optional progress callback
        """
        import itertools
        
        var_names = list(template.variables.keys())
        var_options = [template.variables[v]["options"] for v in var_names]
        
        if not var_options:
            # No variables, just run once
            params = template.build_params()
            return [self.api_manager.call_api(endpoint_id, params, job_id)]
        
        combinations = list(itertools.product(*var_options))
        results = []
        
        for i, combo in enumerate(combinations):
            var_values = dict(zip(var_names, combo))
            params = template.build_params(var_values)
            
            result = self.api_manager.call_api(endpoint_id, params, job_id)
            result["variable_values"] = var_values
            results.append(result)
            
            if callback:
                callback(i + 1, len(combinations), result)
        
        return results
    
    def run_selected_options(self, template: QueryTemplate,
                             endpoint_id: str, 
                             selected_values: Dict[str, List],
                             job_id: str = None) -> List[Dict]:
        """
        Run query for selected combinations only.
        
        selected_values example:
            {"years": [1, 5, 10], "state": ["CA"]}
        """
        import itertools
        
        var_names = list(selected_values.keys())
        var_options = [selected_values[v] for v in var_names]
        
        combinations = list(itertools.product(*var_options))
        results = []
        
        for combo in combinations:
            var_values = dict(zip(var_names, combo))
            params = template.build_params(var_values)
            
            result = self.api_manager.call_api(endpoint_id, params, job_id)
            result["variable_values"] = var_values
            results.append(result)
        
        return results
    
    # =========================================
    # SCHEDULING
    # =========================================
    
    def schedule_job(self, job_id: str, interval_hours: float = 24,
                     start_time: datetime = None) -> str:
        """
        Schedule a job to run periodically.
        Returns schedule ID.
        """
        from uuid import uuid4
        schedule_id = str(uuid4())
        
        schedule = {
            "schedule_id": schedule_id,
            "job_id": job_id,
            "interval_hours": interval_hours,
            "start_time": (start_time or datetime.now()).isoformat(),
            "next_run": (start_time or datetime.now()).isoformat(),
            "last_run": None,
            "enabled": True
        }
        
        self.scheduled_jobs.append(schedule)
        self._save_schedules()
        
        return schedule_id
    
    def _save_schedules(self):
        """Save schedules to config"""
        schedule_file = self.api_manager.config_path / "api_schedules.json"
        with open(schedule_file, 'w', encoding='utf-8') as f:
            json.dump({"schedules": self.scheduled_jobs}, f, indent=2)
    
    def _load_schedules(self):
        """Load schedules from config"""
        schedule_file = self.api_manager.config_path / "api_schedules.json"
        if schedule_file.exists():
            with open(schedule_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scheduled_jobs = data.get("schedules", [])
    
    def start_scheduler(self):
        """Start the background scheduler thread"""
        if self._scheduler_running:
            return
        
        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self._scheduler_running = False
    
    def _scheduler_loop(self):
        """Background scheduler loop"""
        while self._scheduler_running:
            now = datetime.now()
            
            for schedule in self.scheduled_jobs:
                if not schedule.get("enabled"):
                    continue
                
                next_run = datetime.fromisoformat(schedule["next_run"])
                
                if now >= next_run:
                    # Run the job
                    job_id = schedule["job_id"]
                    self.api_manager.run_job(job_id)
                    
                    # Update schedule
                    schedule["last_run"] = now.isoformat()
                    interval = timedelta(hours=schedule["interval_hours"])
                    schedule["next_run"] = (now + interval).isoformat()
                    self._save_schedules()
            
            # Check every minute
            time.sleep(60)
    
    def cancel_schedule(self, schedule_id: str):
        """Cancel a scheduled job"""
        self.scheduled_jobs = [
            s for s in self.scheduled_jobs 
            if s["schedule_id"] != schedule_id
        ]
        self._save_schedules()
    
    def list_schedules(self) -> List[Dict]:
        """List all scheduled jobs"""
        return self.scheduled_jobs


# =========================================
# PRESET QUERY TEMPLATES
# =========================================

PRESET_TEMPLATES = {
    "divorce_rate": QueryTemplate(
        name="US Divorce Rate by Year",
        base_params={"indicator": "divorce_rate", "country": "USA"},
        variables={
            "years": {
                "type": "dropdown",
                "options": [1, 2, 5, 10, 15, 20, 25, 30],
                "default": 5,
                "label": "Years of Data"
            }
        },
        description="Query divorce rate trends over specified years"
    ),
    "academic_search": QueryTemplate(
        name="Academic Paper Search",
        base_params={"fields": "title,abstract,authors,year"},
        variables={
            "query": {
                "type": "text",
                "default": "",
                "label": "Search Query"
            },
            "limit": {
                "type": "dropdown",
                "options": [10, 25, 50, 100],
                "default": 25,
                "label": "Max Results"
            },
            "year_from": {
                "type": "dropdown",
                "options": list(range(2024, 1990, -1)),
                "default": 2020,
                "label": "From Year"
            }
        },
        description="Search academic papers with filters"
    ),
    "heartmath_hrv": QueryTemplate(
        name="HeartMath HRV Research",
        base_params={
            "fields": "title,abstract,authors,year,venue",
            "query": "HeartMath HRV coherence"
        },
        variables={
            "topic": {
                "type": "dropdown",
                "options": [
                    "HRV coherence meditation",
                    "HRV moral behavior",
                    "cardiac coherence emotion",
                    "heart brain interaction",
                    "psychophysiological coherence"
                ],
                "default": "HRV coherence meditation",
                "label": "Research Topic"
            },
            "limit": {
                "type": "dropdown",
                "options": [10, 25, 50],
                "default": 25,
                "label": "Max Results"
            }
        },
        description="Search HeartMath-related HRV research for P8/P9"
    )
}
