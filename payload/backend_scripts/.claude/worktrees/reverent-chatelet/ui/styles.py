"""
Modern Dark Theme Styles - Same as Stratum
"""

DARK_THEME_STYLESHEET = """
/* Main Application Styles */
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-size: 10pt;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    background-color: #252526;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 8px 16px;
    margin-right: 2px;
    border: 1px solid #3a3a3a;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    font-weight: 500;
}

QTabBar::tab:selected {
    background-color: #37373d;
    color: #ffffff;
    border: 2px solid #007acc;
    border-bottom: 2px solid #37373d;
}

QTabBar::tab:hover {
    background-color: #3c3c42;
    color: #ffffff;
}

/* Buttons */
QPushButton {
    background-color: #0e639c;
    color: white;
    border: 1px solid #007acc;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 500;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1177bb;
    border-color: #4f9fd1;
}

QPushButton:pressed {
    background-color: #0a4f7a;
    border-color: #005a9e;
}

QPushButton:disabled {
    background-color: #3c3c42;
    color: #cccccc;
    border-color: #555555;
}

/* Text Areas */
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 8px;
    selection-background-color: #264f78;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #007acc;
}

/* Labels */
QLabel {
    color: #ffffff;
    background-color: transparent;
}

/* List Widgets */
QListWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    selection-background-color: #264f78;
}

QListWidget::item {
    padding: 4px;
    border-bottom: 1px solid #3a3a3a;
}

QListWidget::item:selected {
    background-color: #264f78;
    color: #ffffff;
}

QListWidget::item:hover {
    background-color: #2a2d2e;
}

/* Table Widgets */
QTableWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    gridline-color: #3a3a3a;
}

QTableWidget::item {
    padding: 4px;
}

QTableWidget::item:selected {
    background-color: #264f78;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #2d2d30;
    color: #ffffff;
    padding: 6px;
    border: 1px solid #3a3a3a;
}

/* Line Edits */
QLineEdit {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 6px;
    selection-background-color: #264f78;
}

QLineEdit:focus {
    border-color: #007acc;
}

/* Combo Boxes */
QComboBox {
    background-color: #3c3c42;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 120px;
}

QComboBox:hover {
    border-color: #007acc;
}

QComboBox::drop-down {
    border: none;
    background-color: #3c3c42;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    selection-background-color: #264f78;
}

/* Group Boxes */
QGroupBox {
    font-weight: bold;
    border: 2px solid #3a3a3a;
    border-radius: 5px;
    margin-top: 1ex;
    background-color: #252526;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 10px 0 10px;
    color: #ffffff;
    font-weight: bold;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 14px;
    border-radius: 7px;
}

QScrollBar::handle:vertical {
    background-color: #3a3a3a;
    border-radius: 7px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    background-color: transparent;
    border: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background-color: transparent;
}
"""

