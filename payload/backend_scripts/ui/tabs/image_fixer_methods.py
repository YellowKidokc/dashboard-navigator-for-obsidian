"""
Image Fixer Methods
Helper methods for the image link fixer tab
"""

from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox, QCheckBox, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from engine.image_link_fixer import ImageLinkFixer


def browse_image_media_folder(self):
    """Browse for canonical media folder."""
    folder = QFileDialog.getExistingDirectory(self, "Select Canonical Media Folder")
    if folder:
        self.image_fixer_media_path.setText(folder)


def browse_image_papers_folder(self):
    """Browse for papers folder."""
    folder = QFileDialog.getExistingDirectory(self, "Select Papers Folder")
    if folder:
        self.image_fixer_papers_path.setText(folder)


def scan_image_links(self):
    """Start scanning for broken image links."""
    media_path = self.image_fixer_media_path.text()
    papers_path = self.image_fixer_papers_path.text()
    
    if not media_path or not Path(media_path).exists():
        QMessageBox.warning(self, "Invalid Path", "Please select a valid canonical media folder.")
        return
    
    if not papers_path or not Path(papers_path).exists():
        QMessageBox.warning(self, "Invalid Path", "Please select a valid papers folder.")
        return
    
    # Initialize fixer
    self.image_fixer_log.clear()
    self.image_fixer_log.append(f"Initializing image fixer...")
    self.image_fixer_log.append(f"Canonical media: {media_path}")
    
    from engine.image_link_fixer import ImageLinkFixer
    self._image_fixer = ImageLinkFixer(media_path)
    
    # Start scan
    self.image_fixer_scan_btn.setEnabled(False)
    self.image_fixer_progress.setVisible(True)
    self.image_fixer_progress.setRange(0, 0)  # Indeterminate
    
    from ui.tabs.image_fixer_tab import ImageScanWorker
    self._image_scan_worker = ImageScanWorker(
        self._image_fixer,
        papers_path,
        self.image_fixer_recursive.isChecked()
    )
    
    self._image_scan_worker.log.connect(lambda msg: self.image_fixer_log.append(msg))
    self._image_scan_worker.finished.connect(self._on_image_scan_finished)
    self._image_scan_worker.start()


def on_image_scan_finished(self, results):
    """Handle scan completion."""
    self.image_fixer_scan_btn.setEnabled(True)
    self.image_fixer_progress.setVisible(False)
    
    self._image_scan_results = results
    
    # Populate table
    self.image_fixer_table.setRowCount(0)
    
    row = 0
    for paper_path, issues in results.items():
        for issue in issues:
            if not issue['exists']:  # Only show broken links
                self.image_fixer_table.insertRow(row)
                
                # Paper name
                self.image_fixer_table.setItem(row, 0, QTableWidgetItem(paper_path.name))
                
                # Line number
                self.image_fixer_table.setItem(row, 1, QTableWidgetItem(str(issue['line_num'])))
                
                # Image name
                self.image_fixer_table.setItem(row, 2, QTableWidgetItem(issue['image_name']))
                
                # Status
                status = "❌ Broken"
                self.image_fixer_table.setItem(row, 3, QTableWidgetItem(status))
                
                # Fix available
                fix_status = "✓ Yes" if issue['suggested_fix'] else "✗ No"
                self.image_fixer_table.setItem(row, 4, QTableWidgetItem(fix_status))
                
                # Apply checkbox
                if issue['suggested_fix']:
                    chk = QCheckBox()
                    chk.setChecked(True)
                    container = QWidget()
                    layout = QHBoxLayout(container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(chk)
                    self.image_fixer_table.setCellWidget(row, 5, container)
                    
                    # Store data for later
                    self.image_fixer_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, {
                        'paper_path': paper_path,
                        'issue': issue
                    })
                
                row += 1
    
    if row > 0:
        self.image_fixer_apply_btn.setEnabled(True)
        self.image_fixer_log.append(f"\n✓ Found {row} broken image links")
    else:
        self.image_fixer_log.append(f"\n✓ No broken image links found!")


def select_all_fixable_images(self):
    """Select all fixable images."""
    for row in range(self.image_fixer_table.rowCount()):
        widget = self.image_fixer_table.cellWidget(row, 5)
        if widget:
            chk = widget.findChild(QCheckBox)
            if chk:
                chk.setChecked(True)


def deselect_all_images(self):
    """Deselect all images."""
    for row in range(self.image_fixer_table.rowCount()):
        widget = self.image_fixer_table.cellWidget(row, 5)
        if widget:
            chk = widget.findChild(QCheckBox)
            if chk:
                chk.setChecked(False)


def on_image_selection_changed(self):
    """Handle image selection change - show preview."""
    selected_rows = self.image_fixer_table.selectedIndexes()
    if not selected_rows:
        self.image_fixer_preview.setText("Select an image to preview")
        self.image_fixer_preview_info.setText("")
        return
    
    row = selected_rows[0].row()
    item = self.image_fixer_table.item(row, 0)
    if not item:
        return
    
    data = item.data(Qt.ItemDataRole.UserRole)
    if not data:
        return
    
    issue = data['issue']
    suggested_fix = issue.get('suggested_fix')
    
    if suggested_fix and Path(suggested_fix).exists():
        # Load and display image
        pixmap = QPixmap(str(suggested_fix))
        if not pixmap.isNull():
            # Scale to fit preview area
            scaled_pixmap = pixmap.scaled(
                self.image_fixer_preview.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_fixer_preview.setPixmap(scaled_pixmap)
            
            # Show info
            info = f"Image: {issue['image_name']}\n"
            info += f"Found at: {suggested_fix}\n"
            info += f"Size: {pixmap.width()}x{pixmap.height()}"
            self.image_fixer_preview_info.setText(info)
        else:
            self.image_fixer_preview.setText("Failed to load image")
            self.image_fixer_preview_info.setText("")
    else:
        self.image_fixer_preview.setText("No fix available for this image")
        self.image_fixer_preview_info.setText(f"Image not found: {issue['image_name']}")


def apply_image_fixes(self):
    """Apply selected image fixes."""
    # Collect selected fixes
    fixes_by_paper = {}
    
    for row in range(self.image_fixer_table.rowCount()):
        widget = self.image_fixer_table.cellWidget(row, 5)
        if not widget:
            continue
        
        chk = widget.findChild(QCheckBox)
        if not chk or not chk.isChecked():
            continue
        
        item = self.image_fixer_table.item(row, 0)
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            continue
        
        paper_path = data['paper_path']
        issue = data['issue']
        issue['apply'] = True
        
        if paper_path not in fixes_by_paper:
            fixes_by_paper[paper_path] = []
        fixes_by_paper[paper_path].append(issue)
    
    if not fixes_by_paper:
        QMessageBox.warning(self, "No Fixes Selected", "Please select at least one fix to apply.")
        return
    
    # Confirm
    total_fixes = sum(len(fixes) for fixes in fixes_by_paper.values())
    confirm = QMessageBox.question(
        self, "Apply Fixes",
        f"Apply {total_fixes} fixes to {len(fixes_by_paper)} papers?\n\nThis will modify the paper files.",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if confirm != QMessageBox.StandardButton.Yes:
        return
    
    # Start fixing
    self.image_fixer_apply_btn.setEnabled(False)
    self.image_fixer_scan_btn.setEnabled(False)
    self.image_fixer_progress.setVisible(True)
    self.image_fixer_progress.setRange(0, len(fixes_by_paper))
    self.image_fixer_log.append(f"\nApplying fixes to {len(fixes_by_paper)} papers...")
    
    from ui.tabs.image_fixer_tab import ImageFixWorker
    self._image_fix_worker = ImageFixWorker(self._image_fixer, fixes_by_paper)
    
    self._image_fix_worker.progress.connect(lambda cur, tot: self.image_fixer_progress.setValue(cur))
    self._image_fix_worker.log.connect(lambda msg: self.image_fixer_log.append(msg))
    self._image_fix_worker.finished.connect(self._on_image_fix_finished)
    self._image_fix_worker.start()


def on_image_fix_finished(self, total_fixed, total_papers):
    """Handle fix completion."""
    self.image_fixer_apply_btn.setEnabled(True)
    self.image_fixer_scan_btn.setEnabled(True)
    self.image_fixer_progress.setVisible(False)
    
    self.image_fixer_log.append(f"\n✅ Complete! Fixed {total_fixed} images in {total_papers} papers.")
    
    QMessageBox.information(
        self, "Fixes Applied",
        f"Successfully fixed {total_fixed} image links in {total_papers} papers."
    )
    
    # Clear table
    self.image_fixer_table.setRowCount(0)
    self._image_scan_results = {}
