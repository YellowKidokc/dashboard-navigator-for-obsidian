"""
THEOPHYSICS AUTO-LINKER v2.0
Enhanced with Source Priority + Kill/Skip Toggle Logic
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class ToggleAction(Enum):
    """Two kinds of disable actions"""
    SKIP = "skip"      # Session only
    KILL = "kill"      # Permanent blacklist


@dataclass
class SourceConfig:
    """Single source configuration"""
    rank: int
    name: str
    url_pattern: str
    enabled: bool
    category: str
    note: Optional[str] = None


@dataclass
class LinkState:
    """Tracks state of a discovered key term"""
    key_term: str
    found_count: int
    target_link: str
    source_rank: int  # Which source found it (lower = higher priority)
    source_name: str
    action: Optional[ToggleAction] = None
    action_timestamp: Optional[str] = None
    reason: Optional[str] = None


class AutoLinkerStateManager:
    """Manages Kill list, Skip list, and session state"""
    
    def __init__(self, vault_path):
        self.vault_path = vault_path
        self.kill_list_file = os.path.join(vault_path, ".theophysics_kill_list.json")
        self.skip_list_file = os.path.join(vault_path, ".theophysics_skip_list.json")
        
        self.kill_list = self._load_kill_list()
        self.skip_list = self._load_skip_list()
        self.session_skips = set()  # Current session only
    
    def _load_kill_list(self) -> Dict:
        """Load permanent blacklist"""
        if os.path.exists(self.kill_list_file):
            with open(self.kill_list_file, 'r') as f:
                return json.load(f)
        return {"killed_terms": {}}
    
    def _load_skip_list(self) -> Dict:
        """Load session skip list"""
        if os.path.exists(self.skip_list_file):
            with open(self.skip_list_file, 'r') as f:
                return json.load(f)
        return {"session_skips": {}}
    
    def save_kill_list(self):
        """Persist permanent blacklist"""
        with open(self.kill_list_file, 'w') as f:
            json.dump(self.kill_list, f, indent=2)
    
    def save_skip_list(self):
        """Persist session skip list"""
        with open(self.skip_list_file, 'w') as f:
            json.dump(self.skip_list, f, indent=2)
    
    def kill_term(self, key_term: str, reason: str = ""):
        """Permanently blacklist a key term"""
        self.kill_list["killed_terms"][key_term] = {
            "killed_at": datetime.now().isoformat(),
            "reason": reason
        }
        self.save_kill_list()
        print(f"🚫 KILLED: '{key_term}' (permanent)")
    
    def skip_term(self, key_term: str, reason: str = ""):
        """Skip term for this session only"""
        self.skip_list["session_skips"][key_term] = {
            "skipped_at": datetime.now().isoformat(),
            "reason": reason
        }
        self.session_skips.add(key_term)
        self.save_skip_list()
        print(f"⏸️  SKIPPED: '{key_term}' (this session)")
    
    def is_killed(self, key_term: str) -> bool:
        """Check if term is permanently blacklisted"""
        return key_term in self.kill_list.get("killed_terms", {})
    
    def is_skipped(self, key_term: str) -> bool:
        """Check if term is skipped"""
        return key_term in self.session_skips or key_term in self.skip_list.get("session_skips", {})
    
    def should_process(self, key_term: str) -> bool:
        """Main decision: should linker process this term?"""
        if self.is_killed(key_term):
            return False
        if self.is_skipped(key_term):
            return False
        return True
    
    def remove_skip(self, key_term: str):
        """Re-enable a skipped term"""
        if key_term in self.skip_list.get("session_skips", {}):
            del self.skip_list["session_skips"][key_term]
            self.save_skip_list()
        if key_term in self.session_skips:
            self.session_skips.discard(key_term)
        print(f"✅ RE-ENABLED: '{key_term}'")


class SourcePriorityManager:
    """Manages source hierarchy and selection"""
    
    def __init__(self, config_file: str):
        self.config_file = config_file
        self.sources = self._load_sources()
    
    def _load_sources(self) -> List[SourceConfig]:
        """Load source priority config"""
        with open(self.config_file, 'r') as f:
            data = json.load(f)
        
        sources = []
        for item in data["source_priority"]:
            sources.append(SourceConfig(**item))
        
        # Sort by rank
        sources.sort(key=lambda x: x.rank)
        return sources
    
    def get_enabled_sources(self) -> List[SourceConfig]:
        """Get all currently enabled sources in priority order"""
        return [s for s in self.sources if s.enabled]
    
    def disable_source(self, rank: int):
        """Disable a source"""
        for s in self.sources:
            if s.rank == rank:
                s.enabled = False
                self._persist()
                break
    
    def enable_source(self, rank: int):
        """Re-enable a source"""
        for s in self.sources:
            if s.rank == rank:
                s.enabled = True
                self._persist()
                break
    
    def reorder_sources(self, source_ranks: List[int]):
        """Reorder source priority"""
        rank_map = {old_rank: new_rank for new_rank, old_rank in enumerate(source_ranks, 1)}
        for s in self.sources:
            if s.rank in rank_map:
                s.rank = rank_map[s.rank]
        self.sources.sort(key=lambda x: x.rank)
        self._persist()
    
    def _persist(self):
        """Save source config back to file"""
        data = {
            "source_priority": [asdict(s) for s in self.sources]
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2)


class AutoLinkerEngine:
    """Core linking logic with source priority cascade"""
    
    def __init__(self, sources_config_file: str, vault_path: str):
        self.source_mgr = SourcePriorityManager(sources_config_file)
        self.state_mgr = AutoLinkerStateManager(vault_path)
    
    def find_link_for_term(self, key_term: str) -> Optional[LinkState]:
        """
        CASCADE through sources in priority order.
        Return FIRST successful match OR None.
        """
        
        # FILTER 1: Is it killed?
        if self.state_mgr.is_killed(key_term):
            print(f"  ⛔ {key_term} is KILLED (blacklist)")
            return None
        
        # FILTER 2: Is it skipped?
        if self.state_mgr.is_skipped(key_term):
            print(f"  ⏸️  {key_term} is SKIPPED (session)")
            return None
        
        # CASCADE through enabled sources
        enabled_sources = self.source_mgr.get_enabled_sources()
        
        for source in enabled_sources:
            print(f"  🔍 Checking {source.name}...")
            result = self._search_source(key_term, source)
            
            if result:
                link_state = LinkState(
                    key_term=key_term,
                    found_count=result.get("count", 0),
                    target_link=result.get("url", ""),
                    source_rank=source.rank,
                    source_name=source.name
                )
                print(f"    ✅ Found in {source.name} (rank {source.rank})")
                return link_state
        
        # No source found it
        print(f"  ❌ {key_term} not found in any enabled source")
        return None
    
    def _search_source(self, key_term: str, source: SourceConfig) -> Optional[Dict]:
        """
        Placeholder for actual source search logic.
        In real implementation, this would:
        - Query Stanford Encyclopedia API
        - Scrape IEP
        - Call PhilPapers API
        - etc.
        """
        # Stub: would call actual search
        return None


# ============================================================================
# GUI STATE & TOGGLE LOGIC
# ============================================================================

class LinkDiscoveryUI:
    """Manages UI state for discovered links"""
    
    def __init__(self, linker_engine: AutoLinkerEngine):
        self.engine = linker_engine
        self.discovered_links: List[LinkState] = []
        self.review_mode = False
    
    def process_candidates(self, key_terms: List[str]) -> List[LinkState]:
        """Find links for all key terms"""
        self.discovered_links = []
        
        for term in key_terms:
            result = self.engine.find_link_for_term(term)
            if result:
                self.discovered_links.append(result)
        
        return self.discovered_links
    
    def toggle_action(self, key_term: str, action: ToggleAction, reason: str = ""):
        """
        Handle toggle from GUI.
        
        User clicks checkbox/toggle:
        - KILL (X icon) → permanent blacklist
        - SKIP (toggle off) → session only
        """
        if action == ToggleAction.KILL:
            self.engine.state_mgr.kill_term(key_term, reason)
        elif action == ToggleAction.SKIP:
            self.engine.state_mgr.skip_term(key_term, reason)
    
    def undo_toggle(self, key_term: str):
        """Re-enable a previously skipped term"""
        self.engine.state_mgr.remove_skip(key_term)
    
    def get_source_priority_display(self) -> List[Dict]:
        """Return source list for GUI dropdown/selector"""
        sources = self.engine.source_mgr.get_enabled_sources()
        return [
            {
                "rank": s.rank,
                "name": s.name,
                "enabled": s.enabled,
                "category": s.category
            }
            for s in sources
        ]


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize
    config_file = r"C:\Users\lowes\OneDrive\Desktop\Theophysics Obsidian\Theophysics_Backend\Backend Python\sources_config.json"
    vault_path = r"C:\Users\lowes\OneDrive\Desktop\Theophysics Obsidian\Theophysics_Master"
    
    linker = AutoLinkerEngine(config_file, vault_path)
    ui = LinkDiscoveryUI(linker)
    
    # Example: Show source priority
    print("📋 SOURCE PRIORITY ORDER:")
    for src in ui.get_source_priority_display():
        print(f"  {src['rank']}. {src['name']} ({src['category']})")
    
    # Example: Process some terms
    test_terms = ["Measurement Problem", "Phase Transitions", "Born Rule"]
    print("\n🔗 FINDING LINKS:")
    results = ui.process_candidates(test_terms)
    
    # Example: User toggles on one
    print("\n🎛️  USER ACTIONS:")
    ui.toggle_action("Measurement Problem", ToggleAction.KILL, "Using internal source instead")
    ui.toggle_action("Phase Transitions", ToggleAction.SKIP, "Need to verify this one")
    
    # Try again
    print("\n🔗 RE-SCANNING:")
    results = ui.process_candidates(test_terms)
