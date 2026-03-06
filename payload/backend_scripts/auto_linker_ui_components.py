"""
THEOPHYSICS AUTO-LINKER UI COMPONENT
Integrates Kill/Skip toggles + Source Priority Selector
For use in Qt Designer or web interface
"""

from dataclasses import dataclass
from typing import List, Callable, Dict
import json

@dataclass
class ToggleState:
    """UI state for a single link candidate"""
    key_term: str
    found_count: int
    source_name: str
    source_rank: int
    
    # Toggle states
    is_killed: bool = False
    is_skipped: bool = False
    was_applied: bool = False
    
    # Callbacks
    on_kill: Callable = None
    on_skip: Callable = None


class SourcePrioritySelector:
    """
    UI Component: Source Priority Reorderer
    
    Shows current cascade order with drag-to-reorder ability
    """
    
    def __init__(self, sources: List[Dict]):
        self.sources = sorted(sources, key=lambda x: x['rank'])
        self.reorder_callbacks = []
    
    def render_html(self) -> str:
        """Generate HTML for source selector"""
        html = '''
        <div class="source-priority-panel">
            <h3>📚 Source Priority (Cascade Order)</h3>
            <p style="font-size: 0.9em; color: #888;">
                Links checked in this order. First match wins.
            </p>
            
            <div class="source-list" id="sourcePriorityList">
        '''
        
        for src in self.sources:
            status = "🟢 Enabled" if src['enabled'] else "⚫ Disabled"
            html += f'''
            <div class="source-item" draggable="true" data-rank="{src['rank']}">
                <span class="rank-badge">{src['rank']}</span>
                <span class="source-name">{src['name']}</span>
                <span class="status-badge">{status}</span>
                <button class="toggle-btn" onclick="toggleSource({src['rank']})">
                    {'Disable' if src['enabled'] else 'Enable'}
                </button>
            </div>
            '''
        
        html += '''
            </div>
            
            <style>
                .source-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 12px;
                    border: 1px solid #444;
                    border-radius: 4px;
                    margin: 8px 0;
                    background: #1a1a1a;
                    cursor: move;
                    transition: all 0.2s;
                }
                
                .source-item:hover {
                    background: #252525;
                    border-color: #00d4ff;
                }
                
                .rank-badge {
                    font-weight: bold;
                    color: #00d4ff;
                    min-width: 30px;
                    text-align: center;
                }
                
                .source-name {
                    flex: 1;
                    font-size: 0.95em;
                }
                
                .status-badge {
                    font-size: 0.85em;
                    padding: 4px 8px;
                    border-radius: 3px;
                    background: #333;
                }
                
                .toggle-btn {
                    padding: 4px 12px;
                    background: #0066cc;
                    border: none;
                    border-radius: 3px;
                    color: white;
                    cursor: pointer;
                    font-size: 0.85em;
                }
                
                .toggle-btn:hover {
                    background: #0052a3;
                }
            </style>
        </div>
        '''
        return html
    
    def register_reorder_callback(self, callback: Callable):
        """Register function to call when user reorders"""
        self.reorder_callbacks.append(callback)
    
    def on_reorder(self, new_ranks: List[int]):
        """Called when user finishes drag-reorder"""
        for callback in self.reorder_callbacks:
            callback(new_ranks)


class LinkReviewPanel:
    """
    UI Component: Link Review/Apply
    
    Shows discovered links with Kill/Skip toggles
    """
    
    def __init__(self, discovered_links: List[ToggleState]):
        self.links = discovered_links
        self.kill_callbacks = []
        self.skip_callbacks = []
        self.apply_callbacks = []
    
    def render_html(self) -> str:
        """Generate HTML for link review table"""
        html = '''
        <div class="link-review-panel">
            <h3>🔗 Discovered Links - Review & Apply</h3>
            
            <table class="link-table">
                <thead>
                    <tr>
                        <th>Key Term</th>
                        <th>Found Count</th>
                        <th>Source</th>
                        <th>Action</th>
                        <th>Apply</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for link in self.links:
            # Determine button state
            kill_class = "btn-danger" if link.is_killed else ""
            skip_class = "btn-warning" if link.is_skipped else ""
            apply_class = "btn-success" if not (link.is_killed or link.is_skipped) else "btn-disabled"
            
            html += f'''
            <tr class="link-row" data-term="{link.key_term}">
                <td class="term-name">{link.key_term}</td>
                <td class="count">{link.found_count}</td>
                <td class="source">
                    {link.source_name}
                    <span class="rank-badge">#{link.source_rank}</span>
                </td>
                <td class="action-buttons">
                    <button class="action-btn {kill_class}" 
                            onclick="toggleKill('{link.key_term}')"
                            title="Permanent blacklist - never suggest again">
                        ❌ KILL
                    </button>
                    <button class="action-btn {skip_class}" 
                            onclick="toggleSkip('{link.key_term}')"
                            title="Skip for this session only">
                        ⏸️ SKIP
                    </button>
                </td>
                <td class="apply-btn">
                    <button class="apply-btn {apply_class}" 
                            onclick="applyLink('{link.key_term}')"
                            disabled={link.is_killed or link.is_skipped}>
                        Apply Link
                    </button>
                </td>
            </tr>
            '''
        
        html += '''
                </tbody>
            </table>
            
            <style>
                .link-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 12px;
                }
                
                .link-table th {
                    background: #0d47a1;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: bold;
                }
                
                .link-table td {
                    padding: 12px;
                    border-bottom: 1px solid #333;
                }
                
                .link-row:hover {
                    background: #1a1a1a;
                }
                
                .action-buttons {
                    display: flex;
                    gap: 8px;
                }
                
                .action-btn {
                    padding: 6px 10px;
                    border: 1px solid #666;
                    background: #222;
                    color: #ccc;
                    border-radius: 3px;
                    cursor: pointer;
                    font-size: 0.85em;
                    transition: all 0.2s;
                }
                
                .action-btn:hover {
                    border-color: #00d4ff;
                    color: #00d4ff;
                }
                
                .action-btn.btn-danger {
                    border-color: #d32f2f;
                    color: #ff6b6b;
                    background: #3c0000;
                }
                
                .action-btn.btn-warning {
                    border-color: #f57c00;
                    color: #ffb74d;
                    background: #3c2c00;
                }
                
                .apply-btn {
                    padding: 8px 16px;
                    background: #1976d2;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: all 0.2s;
                }
                
                .apply-btn:hover:not(:disabled) {
                    background: #1565c0;
                }
                
                .apply-btn:disabled,
                .apply-btn.btn-disabled {
                    background: #666;
                    cursor: not-allowed;
                    opacity: 0.5;
                }
                
                .rank-badge {
                    display: inline-block;
                    margin-left: 8px;
                    padding: 2px 6px;
                    background: #333;
                    border-radius: 2px;
                    font-size: 0.8em;
                    color: #888;
                }
            </style>
        </div>
        '''
        return html
    
    def register_kill_callback(self, callback: Callable):
        """Register kill action callback"""
        self.kill_callbacks.append(callback)
    
    def register_skip_callback(self, callback: Callable):
        """Register skip action callback"""
        self.skip_callbacks.append(callback)
    
    def register_apply_callback(self, callback: Callable):
        """Register apply action callback"""
        self.apply_callbacks.append(callback)
    
    def on_kill(self, key_term: str):
        """User clicked KILL button"""
        # Find link and toggle
        for link in self.links:
            if link.key_term == key_term:
                link.is_killed = True
                link.is_skipped = False
                for callback in self.kill_callbacks:
                    callback(key_term)
    
    def on_skip(self, key_term: str):
        """User clicked SKIP button"""
        for link in self.links:
            if link.key_term == key_term:
                link.is_skipped = not link.is_skipped  # Toggle
                link.is_killed = False
                for callback in self.skip_callbacks:
                    callback(key_term, link.is_skipped)
    
    def on_apply(self, key_term: str):
        """User clicked APPLY LINK button"""
        for link in self.links:
            if link.key_term == key_term and not (link.is_killed or link.is_skipped):
                link.was_applied = True
                for callback in self.apply_callbacks:
                    callback(key_term)


# ============================================================================
# CONFIGURATION PANEL
# ============================================================================

class LinkerConfigPanel:
    """
    Settings panel for Auto-Linker configuration
    Allows user to set:
    - Min occurrence threshold
    - Wikipedia fallback behavior
    - Dual link mode (glossary + Wikipedia)
    """
    
    def __init__(self):
        self.min_occurrences = 4
        self.wikipedia_fallback = True
        self.dual_link_mode = True
    
    def render_html(self) -> str:
        html = '''
        <div class="linker-config-panel">
            <h3>⚙️ Auto-Linker Configuration</h3>
            
            <div class="config-group">
                <label>Minimum Occurrences:</label>
                <input type="number" id="minOccurrences" value="4" min="1" max="20">
                <span class="help">Only suggest links for terms found this many times</span>
            </div>
            
            <div class="config-group">
                <label>Wikipedia Fallback:</label>
                <input type="checkbox" id="wikipediaFallback" checked>
                <span class="help">Use Wikipedia only if no academic source found</span>
            </div>
            
            <div class="config-group">
                <label>Dual Link Mode:</label>
                <input type="checkbox" id="dualLinkMode" checked>
                <span class="help">Add both glossary AND Wikipedia links when available</span>
            </div>
            
            <div class="config-group">
                <label>Academic Source Priority:</label>
                <select id="academicPriority">
                    <option value="stanford">Stanford Encyclopedia (Primary)</option>
                    <option value="iep">Internet Encyclopedia (Secondary)</option>
                    <option value="philpapers">PhilPapers (Tertiary)</option>
                </select>
            </div>
            
            <style>
                .linker-config-panel {
                    background: #0d47a1;
                    padding: 16px;
                    border-radius: 4px;
                    margin: 12px 0;
                }
                
                .config-group {
                    margin: 12px 0;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                
                .config-group label {
                    font-weight: bold;
                    min-width: 180px;
                }
                
                .config-group input[type="checkbox"],
                .config-group input[type="number"],
                .config-group select {
                    padding: 6px;
                    border: 1px solid #444;
                    background: #1a1a1a;
                    color: white;
                    border-radius: 3px;
                }
                
                .help {
                    font-size: 0.85em;
                    color: #aaa;
                    font-style: italic;
                }
            </style>
        </div>
        '''
        return html


# ============================================================================
# INTEGRATION EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example UI state
    test_links = [
        ToggleState("Measurement Problem", 8, "Stanford Encyclopedia", 1),
        ToggleState("Monte Carlo", 8, "Stanford Encyclopedia", 1),
        ToggleState("Phase Transitions", 8, "Stanford Encyclopedia", 1),
    ]
    
    # Create components
    selector = SourcePrioritySelector([
        {"rank": 1, "name": "Stanford Encyclopedia", "enabled": True},
        {"rank": 2, "name": "IEP", "enabled": True},
        {"rank": 3, "name": "PhilPapers", "enabled": True},
        {"rank": 99, "name": "Wikipedia", "enabled": True}
    ])
    
    review = LinkReviewPanel(test_links)
    config = LinkerConfigPanel()
    
    # Generate HTML
    print("=== SOURCE PRIORITY SELECTOR ===")
    print(selector.render_html())
    
    print("\n=== LINK REVIEW PANEL ===")
    print(review.render_html())
    
    print("\n=== CONFIG PANEL ===")
    print(config.render_html())
