# core/api_manager.py
"""
API Manager - Handles API calls, caching, and file tracking
Part of Theophysics Backend
"""

import json
import hashlib
import requests
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import sqlite3


def generate_api_uuid() -> str:
    """Generate UUID for API calls/jobs"""
    return str(uuid.uuid4())


class APIManager:
    """
    Manages API endpoints, calls, caching, and file tracking.
    """
    
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path("O:/Theophysics_Backend/Backend Python")
        self.config_path = self.base_path / "config"
        self.cache_path = self.base_path / "data" / "api_cache"
        self.db_path = self.base_path / "data" / "api_tracking.db"
        
        # Ensure directories exist
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # Load configs
        self.endpoints = self._load_endpoints()
        self.jobs = self._load_jobs()
        
        # Initialize tracking database
        self._init_tracking_db()
    
    # =========================================
    # ENDPOINT MANAGEMENT
    # =========================================
    
    def _load_endpoints(self) -> Dict[str, Any]:
        """Load saved API endpoints"""
        endpoint_file = self.config_path / "api_endpoints.json"
        if endpoint_file.exists():
            with open(endpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"endpoints": []}
    
    def save_endpoints(self):
        """Save endpoints to config"""
        endpoint_file = self.config_path / "api_endpoints.json"
        with open(endpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.endpoints, f, indent=2)
    
    def add_endpoint(self, name: str, url: str, method: str = "GET",
                     headers: Dict = None, params: Dict = None,
                     description: str = "") -> str:
        """Add a new API endpoint"""
        endpoint_id = generate_api_uuid()
        endpoint = {
            "id": endpoint_id,
            "name": name,
            "url": url,
            "method": method.upper(),
            "headers": headers or {},
            "default_params": params or {},
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        self.endpoints["endpoints"].append(endpoint)
        self.save_endpoints()
        return endpoint_id
    
    def get_endpoint(self, endpoint_id: str) -> Optional[Dict]:
        """Get endpoint by ID"""
        for ep in self.endpoints["endpoints"]:
            if ep["id"] == endpoint_id:
                return ep
        return None
    
    def update_endpoint(self, endpoint_id: str, **kwargs):
        """Update endpoint properties"""
        for ep in self.endpoints["endpoints"]:
            if ep["id"] == endpoint_id:
                ep.update(kwargs)
                self.save_endpoints()
                return True
        return False
    
    def delete_endpoint(self, endpoint_id: str):
        """Delete an endpoint"""
        self.endpoints["endpoints"] = [
            ep for ep in self.endpoints["endpoints"] 
            if ep["id"] != endpoint_id
        ]
        self.save_endpoints()
    
    def list_endpoints(self) -> List[Dict]:
        """List all endpoints"""
        return self.endpoints["endpoints"]
    
    # =========================================
    # JOB MANAGEMENT
    # =========================================
    
    def _load_jobs(self) -> Dict[str, Any]:
        """Load saved jobs"""
        jobs_file = self.config_path / "api_jobs.json"
        if jobs_file.exists():
            with open(jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"jobs": []}
    
    def save_jobs(self):
        """Save jobs to config"""
        jobs_file = self.config_path / "api_jobs.json"
        with open(jobs_file, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2)
    
    def create_job(self, name: str, endpoint_id: str, 
                   params: Dict = None, param_variants: Dict = None,
                   description: str = "") -> str:
        """
        Create a new job with optional parameter variants.
        
        param_variants example:
        {
            "years": [1, 5, 10, 20],
            "state": ["CA", "TX", "NY"]
        }
        """
        job_id = generate_api_uuid()
        job_folder = self.cache_path / name.replace(" ", "_")
        job_folder.mkdir(exist_ok=True)
        
        job = {
            "id": job_id,
            "name": name,
            "endpoint_id": endpoint_id,
            "params": params or {},
            "param_variants": param_variants or {},
            "output_folder": str(job_folder),
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "run_count": 0,
            "runs": []
        }
        self.jobs["jobs"].append(job)
        self.save_jobs()
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job by ID"""
        for job in self.jobs["jobs"]:
            if job["id"] == job_id:
                return job
        return None
    
    def list_jobs(self) -> List[Dict]:
        """List all jobs"""
        return self.jobs["jobs"]
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        self.jobs["jobs"] = [j for j in self.jobs["jobs"] if j["id"] != job_id]
        self.save_jobs()
    
    # =========================================
    # API CALLING
    # =========================================
    
    def call_api(self, endpoint_id: str, params: Dict = None,
                 save_to_job: str = None) -> Dict:
        """
        Make an API call.
        
        Returns:
            {
                "success": bool,
                "data": response data,
                "status_code": int,
                "file_path": str (if saved),
                "call_id": str
            }
        """
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return {"success": False, "error": "Endpoint not found"}
        
        # Merge default params with provided params
        merged_params = {**endpoint.get("default_params", {}), **(params or {})}
        
        call_id = generate_api_uuid()
        start_time = time.time()
        
        try:
            if endpoint["method"] == "GET":
                response = requests.get(
                    endpoint["url"],
                    params=merged_params,
                    headers=endpoint.get("headers", {}),
                    timeout=30
                )
            elif endpoint["method"] == "POST":
                response = requests.post(
                    endpoint["url"],
                    json=merged_params,
                    headers=endpoint.get("headers", {}),
                    timeout=30
                )
            else:
                return {"success": False, "error": f"Unsupported method: {endpoint['method']}"}
            
            elapsed = time.time() - start_time
            
            # Try to parse JSON
            try:
                data = response.json()
            except:
                data = response.text
            
            result = {
                "success": response.ok,
                "status_code": response.status_code,
                "data": data,
                "call_id": call_id,
                "elapsed_seconds": round(elapsed, 2)
            }
            
            # Save if job specified
            if save_to_job and response.ok:
                file_path = self._save_response(save_to_job, call_id, data, params)
                result["file_path"] = file_path
            
            # Update endpoint stats
            endpoint["last_used"] = datetime.now().isoformat()
            endpoint["use_count"] = endpoint.get("use_count", 0) + 1
            self.save_endpoints()
            
            # Track the call
            self._track_call(call_id, endpoint_id, params, result)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "call_id": call_id
            }
    
    def run_job(self, job_id: str, variant_params: Dict = None) -> List[Dict]:
        """
        Run a job, optionally with specific variant parameters.
        Returns list of results for each call.
        """
        job = self.get_job(job_id)
        if not job:
            return [{"success": False, "error": "Job not found"}]
        
        results = []
        params = {**job.get("params", {}), **(variant_params or {})}
        
        result = self.call_api(job["endpoint_id"], params, save_to_job=job_id)
        results.append(result)
        
        # Update job stats
        job["last_run"] = datetime.now().isoformat()
        job["run_count"] = job.get("run_count", 0) + 1
        job["runs"].append({
            "timestamp": datetime.now().isoformat(),
            "params": params,
            "success": result.get("success", False),
            "call_id": result.get("call_id")
        })
        self.save_jobs()
        
        return results
    
    def run_job_all_variants(self, job_id: str) -> List[Dict]:
        """
        Run job with ALL variant combinations.
        E.g., if years=[1,5,10] and states=["CA","TX"],
        runs 6 times with all combinations.
        """
        job = self.get_job(job_id)
        if not job:
            return [{"success": False, "error": "Job not found"}]
        
        variants = job.get("param_variants", {})
        if not variants:
            return self.run_job(job_id)
        
        # Generate all combinations
        import itertools
        keys = list(variants.keys())
        values = [variants[k] for k in keys]
        combinations = list(itertools.product(*values))
        
        results = []
        for combo in combinations:
            variant_params = dict(zip(keys, combo))
            result = self.run_job(job_id, variant_params)
            results.extend(result)
        
        return results
    
    # =========================================
    # FILE TRACKING
    # =========================================
    
    def _save_response(self, job_id: str, call_id: str, 
                       data: Any, params: Dict) -> str:
        """Save API response to job folder"""
        job = self.get_job(job_id)
        if not job:
            return None
        
        folder = Path(job["output_folder"])
        folder.mkdir(exist_ok=True)
        
        # Generate filename with timestamp and params hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
        filename = f"{timestamp}_{params_hash}.json"
        
        file_path = folder / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            output = {
                "call_id": call_id,
                "job_id": job_id,
                "params": params,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            json.dump(output, f, indent=2)
        
        # Track the file
        self._track_file(call_id, str(file_path))
        
        return str(file_path)
    
    def _init_tracking_db(self):
        """Initialize SQLite tracking database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT UNIQUE,
            endpoint_id TEXT,
            params TEXT,
            result TEXT,
            success INTEGER,
            timestamp TEXT
        )
        """)
        
        c.execute("""
        CREATE TABLE IF NOT EXISTS file_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT,
            original_path TEXT,
            current_path TEXT,
            file_hash TEXT,
            created_at TEXT,
            last_verified TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def _track_call(self, call_id: str, endpoint_id: str, 
                    params: Dict, result: Dict):
        """Track API call in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
        INSERT INTO api_calls (call_id, endpoint_id, params, result, success, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            endpoint_id,
            json.dumps(params),
            json.dumps(result),
            1 if result.get("success") else 0,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _track_file(self, call_id: str, file_path: str):
        """Track file location in database"""
        # Calculate file hash
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
        INSERT INTO file_tracking (call_id, original_path, current_path, file_hash, created_at, last_verified)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            call_id,
            file_path,
            file_path,
            file_hash,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def find_file(self, call_id: str) -> Optional[str]:
        """Find file by call_id, verifying it still exists"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
        SELECT current_path, file_hash FROM file_tracking WHERE call_id = ?
        """, (call_id,))
        
        row = c.fetchone()
        conn.close()
        
        if row:
            path, expected_hash = row
            if os.path.exists(path):
                return path
            # TODO: Could search for file by hash if moved
        
        return None
    
    def get_call_history(self, limit: int = 50) -> List[Dict]:
        """Get recent API call history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
        SELECT call_id, endpoint_id, params, success, timestamp
        FROM api_calls ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        rows = c.fetchall()
        conn.close()
        
        return [
            {
                "call_id": row[0],
                "endpoint_id": row[1],
                "params": json.loads(row[2]) if row[2] else {},
                "success": bool(row[3]),
                "timestamp": row[4]
            }
            for row in rows
        ]


# =========================================
# BUILT-IN API TEMPLATES
# =========================================

BUILTIN_APIS = {
    # === ACADEMIC RESEARCH ===
    "semantic_scholar": {
        "name": "📚 Semantic Scholar",
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "method": "GET",
        "description": "Academic paper search - great for research",
        "default_params": {"fields": "title,abstract,authors,year,citationCount,venue", "limit": 20}
    },
    "semantic_scholar_hrv": {
        "name": "❤️ HeartMath/HRV Research",
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "method": "GET",
        "description": "Search HeartMath & HRV coherence papers",
        "default_params": {
            "query": "HeartMath HRV coherence",
            "fields": "title,abstract,authors,year,citationCount,venue",
            "limit": 25
        }
    },
    "semantic_scholar_nde": {
        "name": "👁️ NDE Research",
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "method": "GET",
        "description": "Near-death experience research papers",
        "default_params": {
            "query": "near death experience consciousness",
            "fields": "title,abstract,authors,year,citationCount,venue",
            "limit": 25
        }
    },
    "semantic_scholar_moral": {
        "name": "⚖️ Moral Psychology Research",
        "url": "https://api.semanticscholar.org/graph/v1/paper/search",
        "method": "GET",
        "description": "Moral behavior and psychology papers",
        "default_params": {
            "query": "moral behavior neuroscience physiology",
            "fields": "title,abstract,authors,year,citationCount,venue",
            "limit": 25
        }
    },
    "pubmed": {
        "name": "🏥 PubMed Search",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "method": "GET",
        "description": "NCBI PubMed medical literature",
        "default_params": {"db": "pubmed", "retmode": "json", "retmax": 20}
    },
    "pubmed_hrv": {
        "name": "❤️ PubMed HRV Studies",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        "method": "GET",
        "description": "Heart rate variability medical studies",
        "default_params": {
            "db": "pubmed", 
            "retmode": "json", 
            "retmax": 30,
            "term": "heart rate variability coherence emotional regulation"
        }
    },
    "arxiv": {
        "name": "📄 arXiv Preprints",
        "url": "http://export.arxiv.org/api/query",
        "method": "GET",
        "description": "arXiv preprint search",
        "default_params": {"max_results": 10}
    },
    "crossref": {
        "name": "🔗 CrossRef DOI",
        "url": "https://api.crossref.org/works",
        "method": "GET",
        "description": "DOI and citation lookup",
        "default_params": {"rows": 20}
    },
    "openalex": {
        "name": "📖 OpenAlex",
        "url": "https://api.openalex.org/works",
        "method": "GET",
        "description": "Open catalog of scholarly works",
        "default_params": {"per_page": 25}
    },
    
    # === GOVERNMENT DATA ===
    "census_acs": {
        "name": "🇺🇸 US Census ACS",
        "url": "https://api.census.gov/data/2022/acs/acs5",
        "method": "GET",
        "description": "American Community Survey 5-year estimates",
        "default_params": {"get": "NAME", "for": "state:*"}
    },
    "world_bank": {
        "name": "🌍 World Bank Indicators",
        "url": "https://api.worldbank.org/v2/country/all/indicator/",
        "method": "GET",
        "description": "World Bank development indicators",
        "default_params": {"format": "json", "per_page": 100}
    },
    "cdc_data": {
        "name": "🏥 CDC Data",
        "url": "https://data.cdc.gov/resource/",
        "method": "GET",
        "description": "CDC health statistics",
        "default_params": {"$limit": 50}
    },
    
    # === THEOPHYSICS SPECIFIC ===
    "gcp_data": {
        "name": "🌐 Global Consciousness Project",
        "url": "https://noosphere.princeton.edu/data/",
        "method": "GET",
        "description": "Random event generator correlations",
        "default_params": {}
    }
}
