"""
AUTO-APPLY: Mermaid Scanner Integration
Adds Mermaid diagram scanning and rendering to Semantic Dashboard
"""

from pathlib import Path
import shutil
from datetime import datetime

def apply_mermaid_integration():
    """Apply Mermaid integration to main_window_v2.py"""
    
    main_window_path = Path(__file__).parent / "ui" / "main_window_v2.py"
    
    print("=" * 70)
    print("MERMAID SCANNER INTEGRATION")
    print("=" * 70)
    
    # Backup
    backup_path = main_window_path.parent / f"{main_window_path.stem}_backup_mermaid_{datetime.now().strftime('%Y%m%d_%H%M%S')}{main_window_path.suffix}"
    shutil.copy2(main_window_path, backup_path)
    print(f"[OK] Backup: {backup_path.name}")
    
    # Read file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = content.count('\n')
    print(f"[READING] {original_lines} lines")
    
    # ==================================================================
    # PATCH 1: Replace "Sync to Database" with "Scan for Mermaids"
    # ==================================================================
    print("\n[1/3] Replacing 'Sync to Database' button...")
    
    old_sync_btn = '''        self.sync_semantic_db_btn = QPushButton("🗄️ Sync to Database")
        self.sync_semantic_db_btn.clicked.connect(self._sync_semantic_to_db)
        btn_row.addWidget(self.sync_semantic_db_btn)'''
    
    new_scan_btn = '''        self.scan_mermaids_btn = QPushButton("🎨 Scan for Mermaids")
        self.scan_mermaids_btn.clicked.connect(self._scan_mermaid_diagrams)
        btn_row.addWidget(self.scan_mermaids_btn)'''
    
    if old_sync_btn in content:
        content = content.replace(old_sync_btn, new_scan_btn)
        print("      [OK] Button replaced")
    else:
        print("      [WARNING] Could not find 'Sync to Database' button (may already be replaced)")
    
    # ==================================================================
    # PATCH 2: Add Mermaid section before table
    # ==================================================================
    print("\n[2/3] Adding Mermaid diagram viewer section...")
    
    # Find where to insert (before "layout.addWidget(table_group)")
    marker = "        layout.addWidget(table_group)"
    
    if marker in content:
        mermaid_section = '''
        # ==========================================
        # SECTION 5: Mermaid Diagrams Viewer
        # ==========================================
        mermaid_group = QGroupBox("🎨 Mermaid Diagrams from Papers")
        mermaid_layout = QVBoxLayout(mermaid_group)
        
        # Control buttons
        mermaid_btn_row = QHBoxLayout()
        
        self.refresh_mermaids_btn = QPushButton("🔄 Refresh Diagrams")
        self.refresh_mermaids_btn.clicked.connect(self._scan_mermaid_diagrams)
        mermaid_btn_row.addWidget(self.refresh_mermaids_btn)
        
        self.combine_axioms_btn = QPushButton("🔗 Combine All Axioms")
        self.combine_axioms_btn.setProperty("class", "success")
        self.combine_axioms_btn.clicked.connect(self._combine_axiom_diagrams)
        self.combine_axioms_btn.setToolTip("Merge all axiom Mermaid diagrams into one master diagram")
        mermaid_btn_row.addWidget(self.combine_axioms_btn)
        
        mermaid_btn_row.addStretch()
        
        self.mermaid_count_label = QLabel("0 diagrams found")
        self.mermaid_count_label.setStyleSheet("color: #6b7280;")
        mermaid_btn_row.addWidget(self.mermaid_count_label)
        
        mermaid_layout.addLayout(mermaid_btn_row)
        
        # Scrollable container for diagrams
        self.mermaid_scroll = QScrollArea()
        self.mermaid_scroll.setWidgetResizable(True)
        self.mermaid_scroll.setMinimumHeight(300)
        self.mermaid_scroll.setMaximumHeight(600)
        
        self.mermaid_container = QWidget()
        self.mermaid_container_layout = QVBoxLayout(self.mermaid_container)
        self.mermaid_container_layout.setSpacing(20)
        
        self.mermaid_scroll.setWidget(self.mermaid_container)
        mermaid_layout.addWidget(self.mermaid_scroll)
        
        layout.addWidget(mermaid_group)
        
'''
        content = content.replace(marker, mermaid_section + marker)
        print("      [OK] Mermaid section added")
    else:
        print("      [WARNING] Could not find insertion point for Mermaid section")
    
    # ==================================================================
    # PATCH 3: Update data storage init
    # ==================================================================
    print("\n[3/3] Adding Mermaid data storage...")
    
    old_storage = '''        # Store extracted data
        self._semantic_data = None
        self._semantic_extractor = None'''
    
    new_storage = '''        # Store extracted data
        self._semantic_data = None
        self._semantic_extractor = None
        self._mermaid_diagrams = []  # Mermaid diagram storage'''
    
    if old_storage in content:
        content = content.replace(old_storage, new_storage)
        print("      [OK] Data storage updated")
    else:
        print("      [WARNING] Could not find data storage init")
    
    # Write patched file
    print(f"\n[SAVING] Writing patched file...")
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    new_lines = content.count('\n')
    added_lines = new_lines - original_lines
    
    print(f"         Original: {original_lines} lines")
    print(f"         Patched:  {new_lines} lines")
    print(f"         Added:    +{added_lines} lines")
    
    print("\n" + "=" * 70)
    print("[COMPLETE] Mermaid integration applied!")
    print("=" * 70)
    print("\nNOTE: Methods still need to be added!")
    print("      Run APPLY_MERMAID_METHODS.py next")
    
    return True

if __name__ == "__main__":
    try:
        success = apply_mermaid_integration()
        if not success:
            print("\n[ERROR] Integration failed - restore from backup")
        input("\nPress Enter to close...")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
