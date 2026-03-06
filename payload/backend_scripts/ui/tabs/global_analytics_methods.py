"""
Global Analytics Methods
Helper methods for the global analytics dashboard
"""

from pathlib import Path
from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtCore import Qt
import sqlite3
import json
from datetime import datetime


def extract_analytics_data(self):
    """Start extracting analytics data."""
    backend_root = Path("O:/Theophysics_Backend")
    output_path = Path("O:/Theophysics_Backend/Global_Analytics")
    
    # Get batch size from UI (default 12)
    batch_size = getattr(self, 'analytics_batch_size', None)
    if batch_size:
        batch_size = batch_size.value()
    else:
        batch_size = 12
    
    self.analytics_log.clear()
    self.analytics_log.append("Starting comprehensive data extraction...")
    self.analytics_log.append(f"Batch size: {batch_size} papers per group")
    
    self.analytics_extract_btn.setEnabled(False)
    self.analytics_progress.setVisible(True)
    self.analytics_progress.setRange(0, 0)  # Indeterminate
    
    from ui.tabs.global_analytics_tab import AnalyticsWorker
    self._analytics_worker = AnalyticsWorker(backend_root, output_path, batch_size)
    
    self._analytics_worker.progress.connect(lambda msg: self.analytics_log.append(msg))
    self._analytics_worker.finished.connect(self._on_analytics_extraction_finished)
    self._analytics_worker.start()


def on_analytics_extraction_finished(self, metrics, output_folder):
    """Handle extraction completion."""
    self.analytics_extract_btn.setEnabled(True)
    self.analytics_progress.setVisible(False)
    
    # Store output folder
    self._analytics_output_folder = output_folder
    self.analytics_open_folder_btn.setEnabled(True)
    
    self.analytics_log.append("\n✅ Data extraction complete!")
    self.analytics_log.append(f"Extracted {metrics.get('total_papers', 0)} papers")
    self.analytics_log.append(f"Found {metrics.get('total_tags', 0)} unique tags")
    self.analytics_log.append(f"Tracked {metrics.get('total_concepts', 0)} concepts")
    self.analytics_log.append(f"\n📁 Output folder: {output_folder}")
    
    # Refresh dashboard
    self._refresh_analytics_dashboard()
    
    QMessageBox.information(
        self, "Extraction Complete",
        f"Successfully extracted analytics data!\n\n"
        f"Papers: {metrics.get('total_papers', 0)}\n"
        f"Tags: {metrics.get('total_tags', 0)}\n"
        f"Concepts: {metrics.get('total_concepts', 0)}\n\n"
        f"Output: {output_folder}"
    )


def open_analytics_output(self):
    """Open the analytics output folder."""
    if not self._analytics_output_folder:
        QMessageBox.warning(self, "No Output", "No analytics output folder available.")
        return
    
    import os
    import subprocess
    
    folder_path = Path(self._analytics_output_folder)
    if not folder_path.exists():
        QMessageBox.warning(self, "Folder Not Found", f"Output folder not found:\n{folder_path}")
        return
    
    try:
        # Open folder in file explorer
        if os.name == 'nt':  # Windows
            os.startfile(folder_path)
        elif os.name == 'posix':  # macOS/Linux
            subprocess.run(['open' if 'darwin' in os.sys.platform else 'xdg-open', folder_path])
        
        self.analytics_log.append(f"📁 Opened folder: {folder_path}")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to open folder:\n{e}")


def refresh_analytics_dashboard(self):
    """Refresh the analytics dashboard from database."""
    if not self._analytics_db_path.exists():
        self.analytics_log.append("No analytics database found. Run extraction first.")
        return
    
    try:
        conn = sqlite3.connect(self._analytics_db_path)
        cursor = conn.cursor()
        
        # Load latest snapshot
        cursor.execute("""
            SELECT total_papers, total_words, total_tags, total_links,
                   total_concepts, metrics_json
            FROM snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        if row:
            total_papers, total_words, total_tags, total_links, total_concepts, metrics_json = row
            metrics = json.loads(metrics_json)
            
            # Update metric labels
            self.analytics_metrics['total_papers'].setText(str(total_papers))
            self.analytics_metrics['total_words'].setText(f"{total_words:,}")
            self.analytics_metrics['total_tags'].setText(str(total_tags))
            self.analytics_metrics['total_links'].setText(str(total_links))
            self.analytics_metrics['total_concepts'].setText(str(total_concepts))
            self.analytics_metrics['total_relationships'].setText(str(metrics.get('total_relationships', 0)))
            self.analytics_metrics['avg_words_per_paper'].setText(f"{metrics.get('avg_words_per_paper', 0):.0f}")
            self.analytics_metrics['avg_relationship_strength'].setText(f"{metrics.get('avg_relationship_strength', 0):.2f}")
            
            # Update charts
            self._update_analytics_charts(cursor)
            
            # Update current table view
            self._change_analytics_view(self.analytics_view_combo.currentText())
            
            self.analytics_log.append(f"Dashboard refreshed at {datetime.now().strftime('%H:%M:%S')}")
        
        conn.close()
    
    except Exception as e:
        self.analytics_log.append(f"Error refreshing dashboard: {e}")


def update_analytics_charts(self, cursor):
    """Update the visualization charts."""
    try:
        from ui.tabs.global_analytics_tab import create_pie_chart, create_bar_chart
        from ui.styles_v2 import COLORS
        
        # Tag distribution chart
        cursor.execute("SELECT tag, count FROM tags ORDER BY count DESC LIMIT 10")
        tag_data = {row[0]: row[1] for row in cursor.fetchall()}
        
        if tag_data:
            tag_chart = create_pie_chart(tag_data, "Top 10 Tags", COLORS)
            self.analytics_tag_chart.setChart(tag_chart)
        
        # Concept frequency chart
        cursor.execute("SELECT concept, frequency FROM concepts ORDER BY frequency DESC LIMIT 10")
        concept_data = {row[0]: row[1] for row in cursor.fetchall()}
        
        if concept_data:
            concept_chart = create_bar_chart(concept_data, "Top 10 Concepts", COLORS)
            self.analytics_concept_chart.setChart(concept_chart)
    
    except Exception as e:
        self.analytics_log.append(f"Error updating charts: {e}")


def change_analytics_view(self, view_name):
    """Change the data table view."""
    if not self._analytics_db_path.exists():
        return
    
    try:
        conn = sqlite3.connect(self._analytics_db_path)
        cursor = conn.cursor()
        
        self.analytics_table.clear()
        
        if view_name == "Papers":
            self.analytics_table.setColumnCount(6)
            self.analytics_table.setHorizontalHeaderLabels([
                "Filename", "Title", "Words", "Tags", "Links", "Modified"
            ])
            
            cursor.execute("""
                SELECT filename, title, word_count, tags_json, links_json, modified_date
                FROM papers
                ORDER BY word_count DESC
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                filename, title, word_count, tags_json, links_json, modified = row
                tags = json.loads(tags_json) if tags_json else []
                links = json.loads(links_json) if links_json else []
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(filename))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(title[:50]))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(str(word_count)))
                self.analytics_table.setItem(i, 3, QTableWidgetItem(str(len(tags))))
                self.analytics_table.setItem(i, 4, QTableWidgetItem(str(len(links))))
                self.analytics_table.setItem(i, 5, QTableWidgetItem(modified[:10]))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} papers")
        
        elif view_name == "Tags":
            self.analytics_table.setColumnCount(3)
            self.analytics_table.setHorizontalHeaderLabels(["Tag", "Count", "Papers"])
            
            cursor.execute("""
                SELECT tag, count, papers_json
                FROM tags
                ORDER BY count DESC
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                tag, count, papers_json = row
                papers = json.loads(papers_json) if papers_json else []
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(tag))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(str(count)))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(str(len(papers))))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} tags")
        
        elif view_name == "Concepts":
            self.analytics_table.setColumnCount(3)
            self.analytics_table.setHorizontalHeaderLabels(["Concept", "Frequency", "Papers"])
            
            cursor.execute("""
                SELECT concept, frequency, papers_json
                FROM concepts
                ORDER BY frequency DESC
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                concept, frequency, papers_json = row
                papers = json.loads(papers_json) if papers_json else []
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(concept))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(str(frequency)))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(str(len(papers))))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} concepts")
        
        elif view_name == "Relationships":
            self.analytics_table.setColumnCount(4)
            self.analytics_table.setHorizontalHeaderLabels([
                "Concept A", "Concept B", "Strength", "Common Papers"
            ])
            
            cursor.execute("""
                SELECT concept_a, concept_b, strength, papers_json
                FROM relationships
                ORDER BY strength DESC
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                concept_a, concept_b, strength, papers_json = row
                papers = json.loads(papers_json) if papers_json else []
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(concept_a))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(concept_b))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(f"{strength:.3f}"))
                self.analytics_table.setItem(i, 3, QTableWidgetItem(str(len(papers))))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} relationships")
        
        elif view_name == "Definitions":
            self.analytics_table.setColumnCount(3)
            self.analytics_table.setHorizontalHeaderLabels(["Term", "Definition", "Source"])
            
            cursor.execute("""
                SELECT term, definition, source_paper
                FROM definitions
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                term, definition, source = row
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(term))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(definition[:100]))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(Path(source).name if source else ""))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} definitions")
        
        elif view_name == "Links":
            self.analytics_table.setColumnCount(3)
            self.analytics_table.setHorizontalHeaderLabels(["Source", "Target", "Type"])
            
            cursor.execute("""
                SELECT source_paper, target, link_type
                FROM links
                LIMIT 100
            """)
            
            rows = cursor.fetchall()
            self.analytics_table.setRowCount(len(rows))
            
            for i, row in enumerate(rows):
                source, target, link_type = row
                
                self.analytics_table.setItem(i, 0, QTableWidgetItem(Path(source).name if source else ""))
                self.analytics_table.setItem(i, 1, QTableWidgetItem(target))
                self.analytics_table.setItem(i, 2, QTableWidgetItem(link_type))
            
            self.analytics_table_stats.setText(f"Showing {len(rows)} links")
        
        conn.close()
    
    except Exception as e:
        self.analytics_log.append(f"Error loading {view_name} view: {e}")


def export_analytics_data(self):
    """Export analytics data to JSON."""
    if not self._analytics_db_path.exists():
        QMessageBox.warning(self, "No Data", "No analytics data available. Run extraction first.")
        return
    
    file_path, _ = QFileDialog.getSaveFileName(
        self, "Export Analytics Data",
        f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        "JSON Files (*.json)"
    )
    
    if not file_path:
        return
    
    try:
        conn = sqlite3.connect(self._analytics_db_path)
        cursor = conn.cursor()
        
        # Export all data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'papers': [],
            'tags': [],
            'concepts': [],
            'relationships': [],
            'metrics': {}
        }
        
        # Papers
        cursor.execute("SELECT * FROM papers")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export_data['papers'].append(dict(zip(columns, row)))
        
        # Tags
        cursor.execute("SELECT * FROM tags")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export_data['tags'].append(dict(zip(columns, row)))
        
        # Concepts
        cursor.execute("SELECT * FROM concepts")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export_data['concepts'].append(dict(zip(columns, row)))
        
        # Relationships
        cursor.execute("SELECT * FROM relationships")
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            export_data['relationships'].append(dict(zip(columns, row)))
        
        # Latest metrics
        cursor.execute("SELECT metrics_json FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            export_data['metrics'] = json.loads(row[0])
        
        conn.close()
        
        # Write to file
        Path(file_path).write_text(json.dumps(export_data, indent=2), encoding='utf-8')
        
        self.analytics_log.append(f"✓ Exported to {file_path}")
        QMessageBox.information(self, "Export Complete", f"Analytics data exported to:\n{file_path}")
    
    except Exception as e:
        QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{e}")
