"""
THEOPHYSICS VAULT ORCHESTRATOR
================================
Comprehensive research intelligence system for breakthrough detection,
semantic analysis, and cross-platform integration.

Architecture Philosophy:
- Modular design (5 core systems working together)
- UUID-based cross-platform identity
- Circulation detection for breakthrough prediction
- PostgreSQL integration for persistence
- Obsidian Tracker dashboards for monitoring

Author: David Lowe & Claude
Date: 2025-11-19
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add current directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

# Import modular systems
from modules.infrastructure_manager import InfrastructureManager
from modules.uuid_semantic_manager import UUIDSemanticManager
from modules.circulation_detector import CirculationDetector
from modules.dashboard_generator import DashboardGenerator
from modules.tracker_integrator import TrackerIntegrator


class TheophysicsOrchestrator:
    """
    Master controller coordinating all vault intelligence systems.
    
    Systems:
    1. Infrastructure Manager - Structural maintenance & organization
    2. UUID/Semantic Manager - Cross-platform identity & tagging
    3. Circulation Detector - Breakthrough prediction
    4. Dashboard Generator - Analytics & statistics
    5. Tracker Integrator - Obsidian Tracker dashboards
    """
    
    def __init__(self, vault_root: Optional[Path] = None):
        """Initialize orchestrator with vault root detection"""
        
        # Auto-detect vault root if not provided
        if vault_root is None:
            vault_root = self._detect_vault_root()
        
        self.vault_root = Path(vault_root)
        self.config_path = self.vault_root / "00_VAULT_SYSTEM" / "orchestrator_config.yaml"
        
        print(f"🧬 THEOPHYSICS VAULT ORCHESTRATOR")
        print(f"=" * 70)
        print(f"Vault Root: {self.vault_root}")
        print(f"=" * 70)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize subsystems
        self.infrastructure = InfrastructureManager(self.vault_root, self.config)
        self.uuid_manager = UUIDSemanticManager(self.vault_root, self.config)
        self.circulation = CirculationDetector(self.vault_root, self.config)
        self.dashboard = DashboardGenerator(self.vault_root, self.config)
        self.tracker = TrackerIntegrator(self.vault_root, self.config)
        
        # Detect user experience level
        self.user_level = self._detect_user_level()
    
    def _detect_vault_root(self) -> Path:
        """Auto-detect vault root from script location"""
        # Assume: orchestrator.py is in P##/_LOCAL/_LOCAL_ANALYSIS/
        # So vault root is 3 levels up
        current = Path(__file__).resolve().parent
        
        # Navigate up: _LOCAL_ANALYSIS -> _LOCAL -> P## -> COMPLETE_LOGOS_PAPERS_FINAL
        vault_root = current.parent.parent.parent
        
        # Validate by checking for expected structure
        if (vault_root / "00_VAULT_SYSTEM").exists():
            return vault_root
        
        # Fallback: prompt user
        print("⚠️  Could not auto-detect vault root.")
        vault_input = input("Enter vault root path: ")
        return Path(vault_input)
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML or use defaults"""
        if self.config_path.exists():
            import yaml
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Return default configuration
        return {
            'vault': {
                'postgres_connection': None,  # Set if available
                'git_enabled': False
            },
            'user': {
                'experience_level': 2,  # 1=first-time, 2=regular, 3=advanced
                'default_operations': [
                    'assign_uuids',
                    'generate_tags',
                    'detect_circulation',
                    'update_analytics'
                ]
            },
            'infrastructure': {
                'auto_clean': True,
                'clean_schedule': 'weekly',
                'deduplication': {
                    'enabled': True,
                    'similarity_threshold': 0.92
                }
            },
            'semantic': {
                'auto_tag': True,
                'tag_threshold': 5,
                'auto_link': True,
                'ontology_validation': {
                    'enabled': True,
                    'min_similarity': 0.70,
                    'max_similarity': 0.90
                }
            },
            'analytics': {
                'breakthrough_detection': True,
                'coherence_calculation': True,
                'circulation_detection': True
            }
        }
    
    def _detect_user_level(self) -> int:
        """Determine user experience level (1=first-time, 2=regular, 3=advanced)"""
        saved_level = self.config.get('user', {}).get('experience_level', 2)
        
        print(f"\n🎓 Current Experience Level: {saved_level}")
        print("   1. First-Time User (guided setup)")
        print("   2. Regular Researcher (standard operations)")
        print("   3. Academic/Developer (full control)")
        
        change = input("\nChange level? (y/N): ").lower()
        
        if change == 'y':
            level = int(input("Select level (1-3): "))
            return level
        
        return saved_level
    
    def main_menu(self):
        """Display adaptive menu based on user experience level"""
        
        if self.user_level == 1:
            self._guided_setup()
        elif self.user_level == 2:
            self._research_menu()
        else:
            self._advanced_menu()
    
    def _guided_setup(self):
        """First-time user: guided setup workflow"""
        print("\n🌟 THEOPHYSICS VAULT: GUIDED SETUP")
        print("=" * 70)
        print("This will set up your vault with:")
        print("  • UUIDs for all papers")
        print("  • Auto-generated semantic tags")
        print("  • Breakthrough detection")
        print("  • Analytics dashboards")
        print("  • Obsidian Tracker integration")
        print("=" * 70)
        
        input("\nPress Enter to begin...")
        
        # Step 1: Validate structure
        print("\n[1/6] Validating vault structure...")
        self.infrastructure.validate_folders()
        
        # Step 2: Assign UUIDs
        print("\n[2/6] Assigning unique identifiers...")
        self.uuid_manager.assign_uuids_all_papers()
        
        # Step 3: Generate tags
        print("\n[3/6] Auto-generating semantic tags...")
        self.uuid_manager.generate_tags_all_papers()
        
        # Step 4: Initial circulation scan
        print("\n[4/6] Scanning for circulation patterns...")
        self.circulation.scan_vault_for_approaches()
        patterns = self.circulation.detect_circulation_patterns()
        
        # Step 5: Run analytics
        print("\n[5/6] Generating analytics...")
        self.dashboard.generate_vault_analytics()
        
        # Step 6: Create trackers
        print("\n[6/6] Setting up Obsidian Tracker dashboards...")
        self.tracker.generate_all_trackers(patterns)
        
        print("\n✅ Setup complete! Check:")
        print("   • _Analytics/ folder for dashboards")
        print("   • Each paper's _LOCAL/ folder for individual stats")
        print("   • Obsidian Tracker blocks in dashboards")
    
    def _research_menu(self):
        """Regular researcher: common operations"""
        while True:
            print("\n📊 THEOPHYSICS ORCHESTRATOR")
            print("=" * 70)
            print("1. Create New Paper")
            print("2. Clean Vault (remove duplicates, fix links)")
            print("3. Update Analytics")
            print("4. Detect Circulation Patterns")
            print("5. Sync to PostgreSQL")
            print("6. View Dashboard")
            print("7. Generate Statistics Report")
            print("8. Exit")
            print("=" * 70)
            
            choice = input("\nSelect operation (1-8): ")
            
            if choice == "1":
                self._create_new_paper()
            elif choice == "2":
                self._clean_vault()
            elif choice == "3":
                self._update_analytics()
            elif choice == "4":
                self._detect_circulation()
            elif choice == "5":
                self._sync_postgres()
            elif choice == "6":
                self._view_dashboard()
            elif choice == "7":
                self._generate_statistics_report()
            elif choice == "8":
                break
    
    def _advanced_menu(self):
        """Academic/developer: full system access"""
        while True:
            print("\n⚙️ THEOPHYSICS ORCHESTRATOR: ADVANCED MODE")
            print("=" * 70)
            print("\n🏗️  Infrastructure")
            print("  1. Scaffold New Paper")
            print("  2. Deep Clean (duplicates, orphans, broken links)")
            print("  3. Batch Folder Operations")
            
            print("\n🔬 Semantic Analysis")
            print("  4. Assign/Update UUIDs")
            print("  5. Auto-Generate Tags")
            print("  6. Build Semantic Network")
            print("  7. Validate Ontology (70-90% rule)")
            
            print("\n📊 Analytics")
            print("  8. Calculate Coherence Scores")
            print("  9. Detect Breakthroughs")
            print("  10. Detect Circulation Patterns")
            print("  11. Generate All Dashboards")
            print("  12. Export Statistics (JSON)")
            
            print("\n🔄 Integration")
            print("  13. Sync to PostgreSQL")
            print("  14. Create Obsidian Tracker Blocks")
            print("  15. Generate Citation Registry")
            
            print("\n🎯 Utilities")
            print("  16. Custom Query")
            print("  17. Batch Operations")
            print("  18. Exit")
            print("=" * 70)
            
            choice = input("\nSelect operation (1-18): ")
            
            if choice == "1":
                self._scaffold_new_paper()
            elif choice == "2":
                self._deep_clean()
            elif choice == "4":
                self._assign_update_uuids()
            elif choice == "5":
                self._auto_generate_tags()
            elif choice == "6":
                self._build_semantic_network()
            elif choice == "8":
                self._calculate_coherence()
            elif choice == "9":
                self._detect_breakthroughs()
            elif choice == "10":
                self._detect_circulation()
            elif choice == "11":
                self._generate_all_dashboards()
            elif choice == "12":
                self._export_statistics_json()
            elif choice == "13":
                self._sync_postgres()
            elif choice == "14":
                self._create_tracker_blocks()
            elif choice == "18":
                break
    
    # ===================================================================
    # OPERATION IMPLEMENTATIONS
    # ===================================================================
    
    def _create_new_paper(self):
        """Interactive paper creation wizard"""
        print("\n📄 CREATE NEW PAPER")
        print("=" * 70)
        
        paper_number = int(input("Paper number (e.g., 13): "))
        title = input("Paper title (e.g., 'Quantum Grace Field'): ")
        
        print(f"\nCreating P{paper_number:02d}-{title.replace(' ', '-')}...")
        
        self.infrastructure.scaffold_paper(paper_number, title)
        
        print(f"✅ Paper P{paper_number:02d} created!")
        print(f"   Location: {self.vault_root / f'P{paper_number:02d}-{title.replace(' ', '-')}'}")
    
    def _clean_vault(self):
        """Run vault cleaning operations"""
        print("\n🧹 CLEANING VAULT")
        print("=" * 70)
        
        self.infrastructure.clean_vault()
        
        print("\n✅ Vault cleaned!")
    
    def _update_analytics(self):
        """Update all analytics dashboards"""
        print("\n📊 UPDATING ANALYTICS")
        print("=" * 70)
        
        self.dashboard.generate_vault_analytics()
        
        print("\n✅ Analytics updated!")
        print("   Check: _Analytics/ folder")
    
    def _detect_circulation(self):
        """Scan for circulation patterns"""
        print("\n🔄 DETECTING CIRCULATION PATTERNS")
        print("=" * 70)
        
        self.circulation.scan_vault_for_approaches()
        patterns = self.circulation.detect_circulation_patterns()
        
        if patterns:
            print(f"\n✅ Found {len(patterns)} circulation patterns!")
            print("\n🔥 TOP PATTERNS (Breakthrough Imminent):")
            
            for i, pattern in enumerate(patterns[:5], 1):
                prob = pattern.breakthrough_probability
                status = "⚠️  IMMINENT" if prob > 0.70 else "📊 STRONG" if prob > 0.40 else "📈 WEAK"
                
                print(f"\n{i}. {pattern.concept_name} - {status}")
                print(f"   Probability: {prob:.1%}")
                print(f"   Approaches: {pattern.total_approaches}")
                print(f"   Time span: {(pattern.last_approach - pattern.first_approach).days} days")
        else:
            print("\n✓ No circulation patterns detected")
    
    def _sync_postgres(self):
        """Sync vault to PostgreSQL database"""
        print("\n🗄️  SYNCING TO POSTGRESQL")
        print("=" * 70)
        
        if not self.config['vault'].get('postgres_connection'):
            print("⚠️  PostgreSQL not configured")
            print("   Set 'postgres_connection' in config")
            return
        
        self.uuid_manager.sync_to_postgres()
        
        print("\n✅ Synced to PostgreSQL!")
    
    def _view_dashboard(self):
        """Open analytics dashboard"""
        print("\n📊 OPENING DASHBOARD")
        print("=" * 70)
        
        dashboard_path = self.vault_root / "_Analytics" / "Vault_Dashboard.md"
        
        if dashboard_path.exists():
            os.startfile(dashboard_path)  # Windows
            print(f"✅ Opened: {dashboard_path}")
        else:
            print("⚠️  Dashboard not found. Run 'Update Analytics' first.")
    
    def _generate_statistics_report(self):
        """Generate comprehensive statistics report"""
        print("\n📈 GENERATING STATISTICS REPORT")
        print("=" * 70)
        
        stats = self.dashboard.calculate_vault_statistics()
        
        # Display key stats
        print(f"\n📊 VAULT STATISTICS")
        print(f"=" * 70)
        print(f"Total Papers: {stats['total_papers']}")
        print(f"Total Words: {stats['total_words']:,}")
        print(f"Total Concepts: {stats['total_concepts']:,}")
        print(f"Total Breakthroughs: {stats['total_breakthroughs']}")
        print(f"Average Coherence: {stats['avg_coherence']:.1f}/100")
        print(f"\n💎 ATOMS: {stats['atoms_count']}")
        print(f"🧬 MOLECULES: {stats['molecules_count']}")
        print(f"🌉 BRIDGES: {stats['bridges_count']}")
        print(f"\n🎯 INTEGRATION ORDERS:")
        print(f"   Order 4: {stats['order_4_count']} breakthroughs")
        print(f"   Order 3: {stats['order_3_count']} breakthroughs")
        print(f"   Order 2: {stats['order_2_count']} breakthroughs")
        
        # Save to file
        report_path = self.vault_root / "_Analytics" / "Statistics_Report.md"
        self.dashboard.generate_statistics_report(report_path, stats)
        
        print(f"\n✅ Report saved: {report_path}")
    
    # Additional operation stubs (implement as needed)
    
    def _scaffold_new_paper(self):
        """Advanced paper scaffolding"""
        self._create_new_paper()
    
    def _deep_clean(self):
        """Deep cleaning with advanced options"""
        self._clean_vault()
    
    def _assign_update_uuids(self):
        """UUID assignment"""
        self.uuid_manager.assign_uuids_all_papers()
    
    def _auto_generate_tags(self):
        """Tag generation"""
        self.uuid_manager.generate_tags_all_papers()
    
    def _build_semantic_network(self):
        """Build semantic network graph"""
        print("Building semantic network...")
        self.dashboard.build_semantic_network()
    
    def _calculate_coherence(self):
        """Calculate coherence scores"""
        print("Calculating coherence...")
        self.dashboard.calculate_all_coherence()
    
    def _detect_breakthroughs(self):
        """Detect breakthroughs across vault"""
        print("Detecting breakthroughs...")
        self.dashboard.detect_all_breakthroughs()
    
    def _generate_all_dashboards(self):
        """Generate all analytics dashboards"""
        self._update_analytics()
    
    def _export_statistics_json(self):
        """Export stats to JSON"""
        stats = self.dashboard.calculate_vault_statistics()
        output_path = self.vault_root / "_Analytics" / "vault_statistics.json"
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ Exported: {output_path}")
    
    def _create_tracker_blocks(self):
        """Generate Obsidian Tracker blocks"""
        print("Creating tracker blocks...")
        self.tracker.generate_all_trackers([])


def main():
    """Main entry point"""
    import sys
    
    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print("THEOPHYSICS Vault Orchestrator")
            print("Usage:")
            print("  python orchestrator.py          # Interactive mode")
            print("  python orchestrator.py --init   # Guided setup")
            return 0
        
        elif sys.argv[1] == '--init':
            orchestrator = TheophysicsOrchestrator()
            orchestrator._guided_setup()
            return 0
    
    # Interactive mode
    orchestrator = TheophysicsOrchestrator()
    orchestrator.main_menu()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
