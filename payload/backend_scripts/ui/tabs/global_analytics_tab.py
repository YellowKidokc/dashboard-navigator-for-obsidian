"""
Global Analytics Tab
Dense data visualization and analytics dashboard
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QGridLayout, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PySide6.QtGui import QPainter
import sqlite3
import json
from datetime import datetime


class AnalyticsWorker(QThread):
    """Background worker for analytics extraction."""
    progress = Signal(str)
    finished = Signal(dict, str)  # metrics, output_folder
    
    def __init__(self, backend_root, output_path, batch_size=12):
        super().__init__()
        self.backend_root = backend_root
        self.output_path = output_path
        self.batch_size = batch_size
        self._stop = False
    
    def run(self):
        try:
            from engine.global_analytics_engine import GlobalAnalyticsEngine
            from engine.analytics_dashboard_generator import AnalyticsDashboardGenerator
            
            self.progress.emit("Initializing analytics engine...")
            engine = GlobalAnalyticsEngine(self.backend_root, self.output_path)
            
            self.progress.emit("Extracting all data points...")
            engine.extract_all_data()
            
            self.progress.emit("Exporting dense data...")
            engine.export_dense_data()
            
            if not self._stop:
                self.progress.emit("Generating visual dashboards...")
                db_path = self.output_path / "analytics.db"
                generator = AnalyticsDashboardGenerator(db_path, self.output_path)
                output_folder = generator.generate_all_outputs(self.batch_size)
                
                self.progress.emit(f"✅ Complete! Output: {output_folder}")
                self.finished.emit(engine.data_points['metrics'], str(output_folder))
        except Exception as e:
            self.progress.emit(f"Error: {e}")
            import traceback
            self.progress.emit(traceback.format_exc())
    
    def stop(self):
        self._stop = True


def create_global_analytics_tab(parent, colors):
    """Create the global analytics dashboard."""
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(12, 12, 12, 12)
    
    # Header
    header = QLabel("📊 Global Analytics Dashboard")
    header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {colors['accent_cyan']};")
    layout.addWidget(header)
    
    desc = QLabel("Dense data extraction and visualization across the entire Theophysics ecosystem.")
    desc.setWordWrap(True)
    desc.setStyleSheet(f"color: {colors['text_dim']}; margin-bottom: 10px;")
    layout.addWidget(desc)
    
    # Control panel
    control_group = QGroupBox("Control Panel")
    control_layout = QVBoxLayout(control_group)
    
    # Top row: batch size
    batch_row = QHBoxLayout()
    batch_row.addWidget(QLabel("Papers per batch:"))
    parent.analytics_batch_size = QSpinBox()
    parent.analytics_batch_size.setMinimum(1)
    parent.analytics_batch_size.setMaximum(100)
    parent.analytics_batch_size.setValue(12)
    parent.analytics_batch_size.setToolTip("Group papers into batches (e.g., 12 papers per dashboard)")
    batch_row.addWidget(parent.analytics_batch_size)
    batch_row.addStretch()
    control_layout.addLayout(batch_row)
    
    # Bottom row: buttons
    btn_row = QHBoxLayout()
    
    parent.analytics_extract_btn = QPushButton("🔍 Extract & Generate Dashboards")
    parent.analytics_extract_btn.setProperty("class", "primary")
    parent.analytics_extract_btn.setMinimumHeight(40)
    parent.analytics_extract_btn.clicked.connect(parent._extract_analytics_data)
    btn_row.addWidget(parent.analytics_extract_btn)
    
    parent.analytics_refresh_btn = QPushButton("🔄 Refresh")
    parent.analytics_refresh_btn.clicked.connect(parent._refresh_analytics_dashboard)
    btn_row.addWidget(parent.analytics_refresh_btn)
    
    parent.analytics_export_btn = QPushButton("💾 Export")
    parent.analytics_export_btn.clicked.connect(parent._export_analytics_data)
    btn_row.addWidget(parent.analytics_export_btn)
    
    parent.analytics_open_folder_btn = QPushButton("📁 Open Output")
    parent.analytics_open_folder_btn.setEnabled(False)
    parent.analytics_open_folder_btn.clicked.connect(parent._open_analytics_output)
    btn_row.addWidget(parent.analytics_open_folder_btn)
    
    control_layout.addLayout(btn_row)
    layout.addWidget(control_group)
    
    # Progress
    parent.analytics_progress = QProgressBar()
    parent.analytics_progress.setVisible(False)
    layout.addWidget(parent.analytics_progress)
    
    # Main content splitter
    splitter = QSplitter(Qt.Orientation.Horizontal)
    
    # Left: Metrics and charts
    left_widget = QWidget()
    left_layout = QVBoxLayout(left_widget)
    left_layout.setContentsMargins(0, 0, 0, 0)
    
    # Key metrics grid
    metrics_group = QGroupBox("📈 Key Metrics")
    metrics_layout = QGridLayout(metrics_group)
    
    parent.analytics_metrics = {}
    metric_labels = [
        ("total_papers", "Total Papers", "📄"),
        ("total_words", "Total Words", "📝"),
        ("total_tags", "Unique Tags", "🏷️"),
        ("total_links", "Total Links", "🔗"),
        ("total_concepts", "Tracked Concepts", "💡"),
        ("total_relationships", "Relationships", "🕸️"),
        ("avg_words_per_paper", "Avg Words/Paper", "📊"),
        ("avg_relationship_strength", "Avg Relationship", "🔬")
    ]
    
    for i, (key, label, icon) in enumerate(metric_labels):
        row = i // 2
        col = (i % 2) * 2
        
        lbl = QLabel(f"{icon} {label}:")
        lbl.setStyleSheet("font-weight: bold; font-size: 10pt;")
        metrics_layout.addWidget(lbl, row, col)
        
        value_lbl = QLabel("0")
        value_lbl.setStyleSheet(f"font-size: 16px; color: {colors['accent_green']};")
        parent.analytics_metrics[key] = value_lbl
        metrics_layout.addWidget(value_lbl, row, col + 1)
    
    left_layout.addWidget(metrics_group)
    
    # Charts
    charts_group = QGroupBox("📊 Visualizations")
    charts_layout = QVBoxLayout(charts_group)
    
    # Tag distribution chart
    parent.analytics_tag_chart = QChartView()
    parent.analytics_tag_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
    parent.analytics_tag_chart.setMinimumHeight(250)
    charts_layout.addWidget(QLabel("Top Tags Distribution"))
    charts_layout.addWidget(parent.analytics_tag_chart)
    
    # Concept frequency chart
    parent.analytics_concept_chart = QChartView()
    parent.analytics_concept_chart.setRenderHint(QPainter.RenderHint.Antialiasing)
    parent.analytics_concept_chart.setMinimumHeight(250)
    charts_layout.addWidget(QLabel("Concept Frequency"))
    charts_layout.addWidget(parent.analytics_concept_chart)
    
    left_layout.addWidget(charts_group)
    splitter.addWidget(left_widget)
    
    # Right: Data tables
    right_widget = QWidget()
    right_layout = QVBoxLayout(right_widget)
    right_layout.setContentsMargins(0, 0, 0, 0)
    
    # Data view selector
    view_row = QHBoxLayout()
    view_row.addWidget(QLabel("View:"))
    parent.analytics_view_combo = QComboBox()
    parent.analytics_view_combo.addItems([
        "Papers", "Tags", "Concepts", "Relationships", "Definitions", "Links"
    ])
    parent.analytics_view_combo.currentTextChanged.connect(parent._change_analytics_view)
    view_row.addWidget(parent.analytics_view_combo, 1)
    right_layout.addLayout(view_row)
    
    # Data table
    parent.analytics_table = QTableWidget()
    parent.analytics_table.setAlternatingRowColors(True)
    parent.analytics_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    right_layout.addWidget(parent.analytics_table)
    
    # Table stats
    parent.analytics_table_stats = QLabel("No data loaded")
    parent.analytics_table_stats.setStyleSheet(f"color: {colors['text_dim']}; font-size: 9pt;")
    right_layout.addWidget(parent.analytics_table_stats)
    
    splitter.addWidget(right_widget)
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 1)
    
    layout.addWidget(splitter, 1)
    
    # Log
    log_group = QGroupBox("📋 Activity Log")
    log_layout = QVBoxLayout(log_group)
    
    parent.analytics_log = QTextEdit()
    parent.analytics_log.setReadOnly(True)
    parent.analytics_log.setMaximumHeight(120)
    parent.analytics_log.setStyleSheet(f"""
        background-color: {colors['bg_dark']};
        color: {colors['text_primary']};
        font-family: 'Consolas', monospace;
        font-size: 9pt;
    """)
    log_layout.addWidget(parent.analytics_log)
    layout.addWidget(log_group)
    
    # Initialize
    parent._analytics_worker = None
    parent._analytics_db_path = Path("O:/Theophysics_Backend/Global_Analytics/analytics.db")
    parent._analytics_output_folder = None
    
    # Auto-load if database exists
    if parent._analytics_db_path.exists():
        parent._refresh_analytics_dashboard()
    
    return page


def create_pie_chart(data_dict, title, colors):
    """Create a pie chart from data."""
    series = QPieSeries()
    
    # Sort and take top 10
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for label, value in sorted_data:
        slice = series.append(label, value)
        slice.setLabelVisible(True)
    
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.legend().setVisible(True)
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
    
    return chart


def create_bar_chart(data_dict, title, colors):
    """Create a bar chart from data."""
    # Sort and take top 10
    sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:10]
    
    bar_set = QBarSet("Frequency")
    categories = []
    
    for label, value in sorted_data:
        bar_set.append(value)
        categories.append(label[:15])  # Truncate long labels
    
    series = QBarSeries()
    series.append(bar_set)
    
    chart = QChart()
    chart.addSeries(series)
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
    
    # Axes
    axis_x = QBarCategoryAxis()
    axis_x.append(categories)
    chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
    series.attachAxis(axis_x)
    
    axis_y = QValueAxis()
    chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
    series.attachAxis(axis_y)
    
    chart.legend().setVisible(False)
    
    return chart
