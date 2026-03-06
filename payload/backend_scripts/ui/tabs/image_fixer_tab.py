"""
Image Link Fixer Tab
UI for scanning and fixing broken image links in papers
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QCheckBox, QProgressBar, QFileDialog, QMessageBox,
    QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap


class ImageScanWorker(QThread):
    """Background worker for scanning papers."""
    progress = Signal(int, int)  # current, total
    log = Signal(str)
    finished = Signal(dict)  # scan_results
    
    def __init__(self, fixer, folder_path, recursive):
        super().__init__()
        self.fixer = fixer
        self.folder_path = folder_path
        self.recursive = recursive
        self._stop = False
    
    def run(self):
        try:
            self.log.emit(f"Scanning folder: {self.folder_path}")
            results = self.fixer.scan_folder(Path(self.folder_path), self.recursive)
            
            if not self._stop:
                stats = self.fixer.get_statistics(results)
                self.log.emit(f"\n✓ Scan complete!")
                self.log.emit(f"  Papers with images: {stats['total_papers']}")
                self.log.emit(f"  Total images: {stats['total_images']}")
                self.log.emit(f"  Broken links: {stats['broken_images']}")
                self.log.emit(f"  Fixable: {stats['fixable_images']}")
                self.finished.emit(results)
        except Exception as e:
            self.log.emit(f"Error: {e}")
    
    def stop(self):
        self._stop = True


class ImageFixWorker(QThread):
    """Background worker for fixing images."""
    progress = Signal(int, int)
    log = Signal(str)
    finished = Signal(int, int)  # total_fixed, total_papers
    
    def __init__(self, fixer, fixes_by_paper):
        super().__init__()
        self.fixer = fixer
        self.fixes_by_paper = fixes_by_paper
        self._stop = False
    
    def run(self):
        try:
            total_fixed = 0
            total_papers = len(self.fixes_by_paper)
            
            for i, (paper_path, fixes) in enumerate(self.fixes_by_paper.items(), 1):
                if self._stop:
                    break
                
                self.progress.emit(i, total_papers)
                self.log.emit(f"Fixing: {paper_path.name}")
                
                num_fixed, new_content = self.fixer.fix_paper_images(paper_path, fixes)
                
                if num_fixed > 0:
                    # Write the fixed content
                    paper_path.write_text(new_content, encoding='utf-8')
                    total_fixed += num_fixed
                    self.log.emit(f"  ✓ Fixed {num_fixed} images")
            
            if not self._stop:
                self.finished.emit(total_fixed, total_papers)
        except Exception as e:
            self.log.emit(f"Error: {e}")
    
    def stop(self):
        self._stop = True


def create_image_fixer_tab(parent, colors):
    """Create the image link fixer tab."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(12, 12, 12, 12)
    
    # Header
    header = QLabel("🖼️ Image Link Fixer")
    header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {colors['accent_cyan']};")
    layout.addWidget(header)
    
    desc = QLabel("Scan papers for broken image links and fix them by finding images in canonical media folder.")
    desc.setWordWrap(True)
    desc.setStyleSheet(f"color: {colors['text_dim']}; margin-bottom: 10px;")
    layout.addWidget(desc)
    
    # Configuration
    config_group = QGroupBox("Configuration")
    config_layout = QVBoxLayout(config_group)
    
    # Canonical media path
    media_row = QHBoxLayout()
    media_row.addWidget(QLabel("Canonical Media:"))
    parent.image_fixer_media_path = QLineEdit()
    parent.image_fixer_media_path.setPlaceholderText("Path to 00_canonical_media folder...")
    parent.image_fixer_media_path.setText("O:/Theophysics_Backend/00_canonical_media")
    media_row.addWidget(parent.image_fixer_media_path, 1)
    
    browse_media_btn = QPushButton("📁")
    browse_media_btn.setMaximumWidth(40)
    browse_media_btn.clicked.connect(lambda: parent._browse_image_media_folder())
    media_row.addWidget(browse_media_btn)
    config_layout.addLayout(media_row)
    
    # Papers folder
    papers_row = QHBoxLayout()
    papers_row.addWidget(QLabel("Papers Folder:"))
    parent.image_fixer_papers_path = QLineEdit()
    parent.image_fixer_papers_path.setPlaceholderText("Path to papers folder...")
    papers_row.addWidget(parent.image_fixer_papers_path, 1)
    
    browse_papers_btn = QPushButton("📁")
    browse_papers_btn.setMaximumWidth(40)
    browse_papers_btn.clicked.connect(lambda: parent._browse_image_papers_folder())
    papers_row.addWidget(browse_papers_btn)
    config_layout.addLayout(papers_row)
    
    # Options
    options_row = QHBoxLayout()
    parent.image_fixer_recursive = QCheckBox("Recursive scan")
    parent.image_fixer_recursive.setChecked(True)
    options_row.addWidget(parent.image_fixer_recursive)
    options_row.addStretch()
    
    parent.image_fixer_scan_btn = QPushButton("🔍 Scan for Broken Images")
    parent.image_fixer_scan_btn.setProperty("class", "primary")
    parent.image_fixer_scan_btn.clicked.connect(parent._scan_image_links)
    options_row.addWidget(parent.image_fixer_scan_btn)
    
    config_layout.addLayout(options_row)
    layout.addWidget(config_group)
    
    # Results section with splitter
    results_splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Left: Table of broken images
    table_widget = QWidget()
    table_layout = QVBoxLayout(table_widget)
    table_layout.setContentsMargins(0, 0, 0, 0)
    
    table_header = QLabel("Broken Image Links")
    table_header.setStyleSheet("font-weight: bold;")
    table_layout.addWidget(table_header)
    
    parent.image_fixer_table = QTableWidget()
    parent.image_fixer_table.setColumnCount(6)
    parent.image_fixer_table.setHorizontalHeaderLabels([
        "Paper", "Line", "Image Name", "Status", "Fix Available", "Apply?"
    ])
    parent.image_fixer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    parent.image_fixer_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    parent.image_fixer_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    parent.image_fixer_table.itemSelectionChanged.connect(parent._on_image_selection_changed)
    table_layout.addWidget(parent.image_fixer_table)
    
    # Table controls
    table_ctrl_row = QHBoxLayout()
    
    select_all_btn = QPushButton("Select All Fixable")
    select_all_btn.clicked.connect(parent._select_all_fixable_images)
    table_ctrl_row.addWidget(select_all_btn)
    
    deselect_all_btn = QPushButton("Deselect All")
    deselect_all_btn.clicked.connect(parent._deselect_all_images)
    table_ctrl_row.addWidget(deselect_all_btn)
    
    table_ctrl_row.addStretch()
    
    parent.image_fixer_apply_btn = QPushButton("✅ Apply Selected Fixes")
    parent.image_fixer_apply_btn.setProperty("class", "success")
    parent.image_fixer_apply_btn.setEnabled(False)
    parent.image_fixer_apply_btn.clicked.connect(parent._apply_image_fixes)
    table_ctrl_row.addWidget(parent.image_fixer_apply_btn)
    
    table_layout.addLayout(table_ctrl_row)
    results_splitter.addWidget(table_widget)
    
    # Right: Image preview
    preview_widget = QWidget()
    preview_layout = QVBoxLayout(preview_widget)
    preview_layout.setContentsMargins(0, 0, 0, 0)
    
    preview_header = QLabel("Image Preview")
    preview_header.setStyleSheet("font-weight: bold;")
    preview_layout.addWidget(preview_header)
    
    parent.image_fixer_preview = QLabel("Select an image to preview")
    parent.image_fixer_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
    parent.image_fixer_preview.setStyleSheet(f"background-color: {colors['bg_dark']}; padding: 20px; border: 1px solid {colors['border_dark']};")
    parent.image_fixer_preview.setMinimumHeight(300)
    parent.image_fixer_preview.setScaledContents(False)
    preview_layout.addWidget(parent.image_fixer_preview)
    
    parent.image_fixer_preview_info = QLabel("")
    parent.image_fixer_preview_info.setWordWrap(True)
    parent.image_fixer_preview_info.setStyleSheet(f"color: {colors['text_dim']}; font-size: 10pt;")
    preview_layout.addWidget(parent.image_fixer_preview_info)
    
    results_splitter.addWidget(preview_widget)
    results_splitter.setStretchFactor(0, 2)
    results_splitter.setStretchFactor(1, 1)
    
    layout.addWidget(results_splitter, 1)
    
    # Progress and log
    parent.image_fixer_progress = QProgressBar()
    parent.image_fixer_progress.setVisible(False)
    layout.addWidget(parent.image_fixer_progress)
    
    log_group = QGroupBox("Log")
    log_layout = QVBoxLayout(log_group)
    
    parent.image_fixer_log = QTextEdit()
    parent.image_fixer_log.setReadOnly(True)
    parent.image_fixer_log.setMaximumHeight(120)
    parent.image_fixer_log.setStyleSheet(f"""
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
        font-family: 'Consolas', monospace;
        font-size: 9pt;
    """)
    log_layout.addWidget(parent.image_fixer_log)
    layout.addWidget(log_group)
    
    # Initialize
    parent._image_fixer = None
    parent._image_scan_results = {}
    parent._image_scan_worker = None
    parent._image_fix_worker = None
    
    return page
