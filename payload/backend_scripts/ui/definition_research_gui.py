"""
Definition & Research Links GUI
Comprehensive interface for managing definitions, research links, and exclusions
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QListWidgetItem,
    QTabWidget, QGroupBox, QCheckBox, QSpinBox, QComboBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QSplitter, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent / "analytics"))
sys.path.append(str(Path(__file__).parent.parent / "core"))

from definition_manager import DefinitionManager
from research_linker import ResearchLinker


class DefinitionWorker(QThread):
    """Background worker for definition processing"""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(dict)  # results
    
    def __init__(self, manager, term, options):
        super().__init__()
        self.manager = manager
        self.term = term
        self.options = options
    
    def run(self):
        try:
            defn = self.manager.create_or_update_definition(
                term=self.term,
                fetch_wikipedia=self.options.get('fetch_wikipedia', True),
                generate_examples=self.options.get('generate_examples', True),
                find_related=self.options.get('find_related', True)
            )
            
            if defn:
                self.finished.emit({
                    'success': True,
                    'definition': defn,
                    'message': f"Successfully processed '{self.term}'"
                })
            else:
                self.finished.emit({
                    'success': False,
                    'message': f"Term '{self.term}' is excluded"
                })
        except Exception as e:
            self.finished.emit({
                'success': False,
                'error': str(e),
                'message': f"Error processing '{self.term}': {e}"
            })


class DefinitionResearchGUI(QMainWindow):
    """Main GUI for Definition & Research Links Management"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Theophysics Definition & Research Manager")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize managers
        definitions_dir = Path(__file__).parent.parent / "analytics" / "definitions"
        self.def_manager = DefinitionManager(definitions_dir)
        self.res_linker = ResearchLinker()
        
        self.worker = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("📚 Theophysics Definition & Research Manager")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Tab widget
        tabs = QTabWidget()
        tabs.addTab(self._create_definition_tab(), "📖 Definitions")
        tabs.addTab(self._create_research_tab(), "🔗 Research Links")
        tabs.addTab(self._create_exclusion_tab(), "⊘ Exclusions")
        tabs.addTab(self._create_batch_tab(), "⚡ Batch Processing")
        tabs.addTab(self._create_settings_tab(), "⚙️ Settings")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
    
    def _create_definition_tab(self):
        """Create definition management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input section
        input_group = QGroupBox("Create/Update Definition")
        input_layout = QVBoxLayout(input_group)
        
        # Term input
        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel("Term:"))
        self.term_input = QLineEdit()
        self.term_input.setPlaceholderText("Enter term (e.g., 'Entropy', 'Coherence')")
        term_layout.addWidget(self.term_input)
        input_layout.addLayout(term_layout)
        
        # Aliases
        aliases_layout = QHBoxLayout()
        aliases_layout.addWidget(QLabel("Aliases:"))
        self.aliases_input = QLineEdit()
        self.aliases_input.setPlaceholderText("Comma-separated (e.g., 'thermodynamic entropy, disorder')")
        aliases_layout.addWidget(self.aliases_input)
        input_layout.addLayout(aliases_layout)
        
        # User definition
        input_layout.addWidget(QLabel("Your Definition (optional):"))
        self.user_def_input = QTextEdit()
        self.user_def_input.setPlaceholderText("Enter your custom definition...")
        self.user_def_input.setMaximumHeight(80)
        input_layout.addWidget(self.user_def_input)
        
        # Options
        options_layout = QHBoxLayout()
        self.fetch_wiki_check = QCheckBox("Fetch Wikipedia")
        self.fetch_wiki_check.setChecked(True)
        self.gen_examples_check = QCheckBox("Generate Examples")
        self.gen_examples_check.setChecked(True)
        self.find_related_check = QCheckBox("Find Related Terms")
        self.find_related_check.setChecked(True)
        
        options_layout.addWidget(self.fetch_wiki_check)
        options_layout.addWidget(self.gen_examples_check)
        options_layout.addWidget(self.find_related_check)
        options_layout.addStretch()
        input_layout.addLayout(options_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        create_btn = QPushButton("✓ Create/Update Definition")
        create_btn.clicked.connect(self._create_definition)
        create_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_definition_form)
        
        button_layout.addWidget(create_btn)
        button_layout.addWidget(clear_btn)
        input_layout.addLayout(button_layout)
        
        layout.addWidget(input_group)
        
        # Results section
        results_group = QGroupBox("Definition Preview")
        results_layout = QVBoxLayout(results_group)
        
        self.definition_preview = QTextEdit()
        self.definition_preview.setReadOnly(True)
        results_layout.addWidget(self.definition_preview)
        
        layout.addWidget(results_group)
        
        # Progress bar
        self.def_progress = QProgressBar()
        self.def_progress.setVisible(False)
        layout.addWidget(self.def_progress)
        
        return widget
    
    def _create_research_tab(self):
        """Create research links tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input section
        input_group = QGroupBox("Generate Research Links")
        input_layout = QVBoxLayout(input_group)
        
        # Term input
        term_layout = QHBoxLayout()
        term_layout.addWidget(QLabel("Term:"))
        self.research_term_input = QLineEdit()
        self.research_term_input.setPlaceholderText("Enter term to research")
        term_layout.addWidget(self.research_term_input)
        
        generate_btn = QPushButton("🔍 Generate Links")
        generate_btn.clicked.connect(self._generate_research_links)
        generate_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        term_layout.addWidget(generate_btn)
        
        input_layout.addLayout(term_layout)
        
        # Link count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Max Links:"))
        self.link_count_spin = QSpinBox()
        self.link_count_spin.setMinimum(1)
        self.link_count_spin.setMaximum(12)
        self.link_count_spin.setValue(5)
        count_layout.addWidget(self.link_count_spin)
        count_layout.addStretch()
        input_layout.addLayout(count_layout)
        
        layout.addWidget(input_group)
        
        # Priority order
        priority_group = QGroupBox("Source Priority Order")
        priority_layout = QVBoxLayout(priority_group)
        
        priority_layout.addWidget(QLabel("Current priority (drag to reorder):"))
        self.priority_list = QListWidget()
        self.priority_list.setDragDropMode(QListWidget.InternalMove)
        priority_layout.addWidget(self.priority_list)
        
        save_priority_btn = QPushButton("💾 Save Priority Order")
        save_priority_btn.clicked.connect(self._save_priority_order)
        priority_layout.addWidget(save_priority_btn)
        
        layout.addWidget(priority_group)
        
        # Results
        results_group = QGroupBox("Generated Links")
        results_layout = QVBoxLayout(results_group)
        
        self.research_results = QTextEdit()
        self.research_results.setReadOnly(True)
        results_layout.addWidget(self.research_results)
        
        layout.addWidget(results_group)
        
        return widget
    
    def _create_exclusion_tab(self):
        """Create exclusion management tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Add exclusion
        add_group = QGroupBox("Add Exclusion")
        add_layout = QHBoxLayout(add_group)
        
        add_layout.addWidget(QLabel("Term to Exclude:"))
        self.exclude_input = QLineEdit()
        self.exclude_input.setPlaceholderText("Enter term to permanently exclude")
        add_layout.addWidget(self.exclude_input)
        
        add_btn = QPushButton("⊘ Add to Exclusion List")
        add_btn.clicked.connect(self._add_exclusion)
        add_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        add_layout.addWidget(add_btn)
        
        layout.addWidget(add_group)
        
        # Bulk add
        bulk_group = QGroupBox("Bulk Add Exclusions")
        bulk_layout = QVBoxLayout(bulk_group)
        
        bulk_layout.addWidget(QLabel("Enter multiple terms (comma-separated):"))
        self.bulk_exclude_input = QTextEdit()
        self.bulk_exclude_input.setPlaceholderText("John, Smith, MyName, CommonWord, ...")
        self.bulk_exclude_input.setMaximumHeight(80)
        bulk_layout.addWidget(self.bulk_exclude_input)
        
        bulk_btn = QPushButton("⊘ Bulk Add")
        bulk_btn.clicked.connect(self._bulk_add_exclusions)
        bulk_layout.addWidget(bulk_btn)
        
        layout.addWidget(bulk_group)
        
        # Excluded terms list
        list_group = QGroupBox("Currently Excluded Terms")
        list_layout = QVBoxLayout(list_group)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.exclusion_search = QLineEdit()
        self.exclusion_search.setPlaceholderText("Filter exclusions...")
        self.exclusion_search.textChanged.connect(self._filter_exclusions)
        search_layout.addWidget(self.exclusion_search)
        list_layout.addLayout(search_layout)
        
        self.exclusion_list = QListWidget()
        list_layout.addWidget(self.exclusion_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("✓ Remove Selected")
        remove_btn.clicked.connect(self._remove_exclusion)
        
        clear_all_btn = QPushButton("🗑️ Clear All")
        clear_all_btn.clicked.connect(self._clear_all_exclusions)
        clear_all_btn.setStyleSheet("background-color: #9E9E9E;")
        
        sync_btn = QPushButton("🔄 Sync Lists")
        sync_btn.clicked.connect(self._sync_exclusions)
        
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(clear_all_btn)
        btn_layout.addWidget(sync_btn)
        list_layout.addLayout(btn_layout)
        
        layout.addWidget(list_group)
        
        return widget
    
    def _create_batch_tab(self):
        """Create batch processing tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Input
        input_group = QGroupBox("Batch Process Terms")
        input_layout = QVBoxLayout(input_group)
        
        input_layout.addWidget(QLabel("Enter terms to process (one per line):"))
        self.batch_input = QTextEdit()
        self.batch_input.setPlaceholderText("Entropy\nCoherence\nGrace\nQuantum Mechanics\n...")
        input_layout.addWidget(self.batch_input)
        
        # Options
        options_layout = QHBoxLayout()
        self.batch_wiki = QCheckBox("Fetch Wikipedia")
        self.batch_wiki.setChecked(True)
        self.batch_examples = QCheckBox("Generate Examples")
        self.batch_examples.setChecked(False)
        self.batch_related = QCheckBox("Find Related")
        self.batch_related.setChecked(False)
        
        options_layout.addWidget(self.batch_wiki)
        options_layout.addWidget(self.batch_examples)
        options_layout.addWidget(self.batch_related)
        options_layout.addStretch()
        input_layout.addLayout(options_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        process_btn = QPushButton("⚡ Process All")
        process_btn.clicked.connect(self._batch_process)
        process_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 10px;")
        
        stop_btn = QPushButton("⏹ Stop")
        stop_btn.clicked.connect(self._stop_batch)
        
        btn_layout.addWidget(process_btn)
        btn_layout.addWidget(stop_btn)
        input_layout.addLayout(btn_layout)
        
        layout.addWidget(input_group)
        
        # Progress
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.batch_progress = QProgressBar()
        progress_layout.addWidget(self.batch_progress)
        
        self.batch_status = QLabel("Ready")
        progress_layout.addWidget(self.batch_status)
        
        layout.addWidget(progress_group)
        
        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)
        
        self.batch_results = QTextEdit()
        self.batch_results.setReadOnly(True)
        results_layout.addWidget(self.batch_results)
        
        layout.addWidget(results_group)
        
        return widget
    
    def _create_settings_tab(self):
        """Create settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Paths
        paths_group = QGroupBox("Paths")
        paths_layout = QVBoxLayout(paths_group)
        
        # Definitions directory
        def_path_layout = QHBoxLayout()
        def_path_layout.addWidget(QLabel("Definitions Directory:"))
        self.def_path_label = QLabel(str(self.def_manager.definitions_dir))
        self.def_path_label.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        def_path_layout.addWidget(self.def_path_label)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_definitions_dir)
        def_path_layout.addWidget(browse_btn)
        
        paths_layout.addLayout(def_path_layout)
        layout.addWidget(paths_group)
        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel()
        stats_layout.addWidget(self.stats_label)
        
        refresh_btn = QPushButton("🔄 Refresh Stats")
        refresh_btn.clicked.connect(self._update_stats)
        stats_layout.addWidget(refresh_btn)
        
        layout.addWidget(stats_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        export_btn = QPushButton("📤 Export All Definitions")
        export_btn.clicked.connect(self._export_definitions)
        
        generate_files_btn = QPushButton("📝 Generate All Obsidian Files")
        generate_files_btn.clicked.connect(self._generate_all_obsidian_files)
        
        actions_layout.addWidget(export_btn)
        actions_layout.addWidget(generate_files_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        return widget
    
    def _load_data(self):
        """Load initial data"""
        self._load_priority_list()
        self._load_exclusion_list()
        self._update_stats()
    
    def _load_priority_list(self):
        """Load research link priority order"""
        self.priority_list.clear()
        for source in self.res_linker.get_priority_order():
            display_name = self.res_linker.LINK_TEMPLATES[source]['display_name']
            item = QListWidgetItem(f"{source} - {display_name}")
            item.setData(Qt.UserRole, source)
            self.priority_list.addItem(item)
    
    def _load_exclusion_list(self):
        """Load excluded terms"""
        self.exclusion_list.clear()
        excluded = sorted(set(
            self.def_manager.get_excluded_terms() + 
            self.res_linker.get_excluded_terms()
        ))
        
        for term in excluded:
            self.exclusion_list.addItem(term)
    
    def _filter_exclusions(self, text):
        """Filter exclusion list"""
        for i in range(self.exclusion_list.count()):
            item = self.exclusion_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def _create_definition(self):
        """Create or update a definition"""
        term = self.term_input.text().strip()
        if not term:
            QMessageBox.warning(self, "No Term", "Please enter a term")
            return
        
        # Check if excluded
        if self.def_manager.is_excluded(term):
            reply = QMessageBox.question(
                self, "Term Excluded",
                f"'{term}' is in the exclusion list. Remove it and proceed?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.def_manager.remove_from_exclusion_list(term)
                self.res_linker.remove_from_exclusion_list(term)
                self._load_exclusion_list()
            else:
                return
        
        # Get options
        aliases = [a.strip() for a in self.aliases_input.text().split(',') if a.strip()]
        user_def = self.user_def_input.toPlainText().strip() or None
        
        options = {
            'fetch_wikipedia': self.fetch_wiki_check.isChecked(),
            'generate_examples': self.gen_examples_check.isChecked(),
            'find_related': self.find_related_check.isChecked()
        }
        
        # Show progress
        self.def_progress.setVisible(True)
        self.def_progress.setRange(0, 0)  # Indeterminate
        self.status_label.setText(f"Processing '{term}'...")
        
        # Create worker
        self.worker = DefinitionWorker(self.def_manager, term, options)
        self.worker.finished.connect(self._on_definition_complete)
        self.worker.start()
    
    def _on_definition_complete(self, result):
        """Handle definition completion"""
        self.def_progress.setVisible(False)
        
        if result['success']:
            defn = result['definition']
            
            # Show preview
            preview = f"# {defn.term}\n\n"
            if defn.aliases:
                preview += f"**Aliases:** {', '.join(defn.aliases)}\n\n"
            if defn.definition_user:
                preview += f"**Your Definition:**\n{defn.definition_user}\n\n"
            if defn.definition_wikipedia:
                preview += f"**Wikipedia:**\n{defn.definition_wikipedia[:200]}...\n\n"
            if defn.research_links:
                preview += f"**Research Links ({len(defn.research_links)}):**\n"
                for source, url in list(defn.research_links.items())[:5]:
                    preview += f"- [{source}]({url})\n"
            if defn.related_terms:
                preview += f"\n**Related Terms:** {', '.join(defn.related_terms[:10])}"
            
            self.definition_preview.setText(preview)
            self.status_label.setText(result['message'])
            
            QMessageBox.information(self, "Success", result['message'])
        else:
            self.status_label.setText(result['message'])
            QMessageBox.warning(self, "Error", result['message'])
    
    def _clear_definition_form(self):
        """Clear the definition form"""
        self.term_input.clear()
        self.aliases_input.clear()
        self.user_def_input.clear()
        self.definition_preview.clear()
    
    def _generate_research_links(self):
        """Generate research links for a term"""
        term = self.research_term_input.text().strip()
        if not term:
            QMessageBox.warning(self, "No Term", "Please enter a term")
            return
        
        count = self.link_count_spin.value()
        links = self.res_linker.get_top_quality_links(term, count=count)
        
        if links:
            result = f"# Research Links for '{term}'\n\n"
            result += f"Generated {len(links)} high-quality links:\n\n"
            
            for i, (source, url) in enumerate(links.items(), 1):
                display = self.res_linker.LINK_TEMPLATES[source]['display_name']
                result += f"{i}. **{source}** - {display}\n"
                result += f"   {url}\n\n"
            
            self.research_results.setText(result)
            self.status_label.setText(f"Generated {len(links)} links for '{term}'")
        else:
            self.research_results.setText(f"No research links found for '{term}'")
            self.status_label.setText("No links generated")
    
    def _save_priority_order(self):
        """Save the priority order"""
        new_priority = []
        for i in range(self.priority_list.count()):
            item = self.priority_list.item(i)
            source = item.data(Qt.UserRole)
            new_priority.append(source)
        
        self.res_linker.set_priority_order(new_priority)
        QMessageBox.information(self, "Saved", "Priority order saved successfully")
        self.status_label.setText("Priority order updated")
    
    def _add_exclusion(self):
        """Add a term to exclusion list"""
        term = self.exclude_input.text().strip()
        if not term:
            return
        
        self.def_manager.add_to_exclusion_list(term)
        self.res_linker.add_to_exclusion_list(term)
        
        self.exclude_input.clear()
        self._load_exclusion_list()
        self.status_label.setText(f"Excluded '{term}'")
    
    def _bulk_add_exclusions(self):
        """Bulk add exclusions"""
        text = self.bulk_exclude_input.toPlainText().strip()
        if not text:
            return
        
        terms = [t.strip() for t in text.replace('\n', ',').split(',') if t.strip()]
        
        for term in terms:
            self.def_manager.add_to_exclusion_list(term)
            self.res_linker.add_to_exclusion_list(term)
        
        self.bulk_exclude_input.clear()
        self._load_exclusion_list()
        self.status_label.setText(f"Excluded {len(terms)} terms")
        QMessageBox.information(self, "Success", f"Added {len(terms)} terms to exclusion list")
    
    def _remove_exclusion(self):
        """Remove selected exclusion"""
        current = self.exclusion_list.currentItem()
        if not current:
            return
        
        term = current.text()
        self.def_manager.remove_from_exclusion_list(term)
        self.res_linker.remove_from_exclusion_list(term)
        
        self._load_exclusion_list()
        self.status_label.setText(f"Removed '{term}' from exclusions")
    
    def _clear_all_exclusions(self):
        """Clear all exclusions"""
        reply = QMessageBox.question(
            self, "Clear All",
            "Are you sure you want to clear ALL exclusions?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.def_manager.clear_exclusion_list()
            self.res_linker.clear_exclusion_list()
            self._load_exclusion_list()
            self.status_label.setText("All exclusions cleared")
    
    def _sync_exclusions(self):
        """Sync exclusion lists"""
        def_excluded = set(self.def_manager.get_excluded_terms())
        res_excluded = set(self.res_linker.get_excluded_terms())
        
        # Sync
        for term in def_excluded:
            self.res_linker.add_to_exclusion_list(term)
        for term in res_excluded:
            self.def_manager.add_to_exclusion_list(term)
        
        self._load_exclusion_list()
        self.status_label.setText("Exclusion lists synced")
        QMessageBox.information(self, "Synced", "Exclusion lists synchronized")
    
    def _batch_process(self):
        """Batch process terms"""
        text = self.batch_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Terms", "Please enter terms to process")
            return
        
        terms = [t.strip() for t in text.split('\n') if t.strip()]
        
        self.batch_progress.setMaximum(len(terms))
        self.batch_progress.setValue(0)
        self.batch_results.clear()
        
        results = []
        for i, term in enumerate(terms, 1):
            self.batch_status.setText(f"Processing {i}/{len(terms)}: {term}")
            self.batch_progress.setValue(i)
            QApplication.processEvents()
            
            try:
                defn = self.def_manager.create_or_update_definition(
                    term=term,
                    fetch_wikipedia=self.batch_wiki.isChecked(),
                    generate_examples=self.batch_examples.isChecked(),
                    find_related=self.batch_related.isChecked()
                )
                
                if defn:
                    results.append(f"✓ {term} - Success ({len(defn.research_links)} links)")
                else:
                    results.append(f"⊘ {term} - Excluded")
            except Exception as e:
                results.append(f"✗ {term} - Error: {e}")
        
        self.batch_results.setText('\n'.join(results))
        self.batch_status.setText(f"Complete: {len(terms)} terms processed")
        self.status_label.setText("Batch processing complete")
        
        QMessageBox.information(self, "Complete", f"Processed {len(terms)} terms")
    
    def _stop_batch(self):
        """Stop batch processing"""
        # Placeholder for stop functionality
        self.batch_status.setText("Stopped")
    
    def _browse_definitions_dir(self):
        """Browse for definitions directory"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Definitions Directory")
        if dir_path:
            self.def_manager = DefinitionManager(Path(dir_path))
            self.def_path_label.setText(dir_path)
            self._update_stats()
    
    def _update_stats(self):
        """Update statistics"""
        total_defs = len(self.def_manager.definitions)
        total_excluded = len(self.def_manager.get_excluded_terms())
        
        stats_text = f"""
Total Definitions: {total_defs}
Excluded Terms: {total_excluded}
Research Link Sources: {len(self.res_linker.LINK_TEMPLATES)}
        """
        
        self.stats_label.setText(stats_text.strip())
    
    def _export_definitions(self):
        """Export all definitions"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Definitions", "", "JSON Files (*.json)"
        )
        
        if file_path:
            import json
            from dataclasses import asdict
            
            data = {term: asdict(defn) for term, defn in self.def_manager.definitions.items()}
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "Exported", f"Exported {len(data)} definitions")
            self.status_label.setText(f"Exported to {file_path}")
    
    def _generate_all_obsidian_files(self):
        """Generate all Obsidian files"""
        reply = QMessageBox.question(
            self, "Generate Files",
            f"Generate Obsidian files for {len(self.def_manager.definitions)} definitions?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            output_dir = self.def_manager.definitions_dir / "obsidian_definitions"
            self.def_manager.generate_all_obsidian_files(output_dir)
            
            QMessageBox.information(
                self, "Complete",
                f"Generated {len(self.def_manager.definitions)} Obsidian files in:\n{output_dir}"
            )
            self.status_label.setText(f"Generated {len(self.def_manager.definitions)} files")


def main():
    """Run the GUI application"""
    app = QApplication(sys.argv)
    
    # Set dark theme
    app.setStyle("Fusion")
    
    window = DefinitionResearchGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
