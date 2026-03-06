"""
Modern Dark Theme V2 - Deeper blacks with cyan accents
Sidebar-optimized styling
"""

# Color palette
COLORS = {
    'bg_darkest': '#0d0d0d',      # Deepest black
    'bg_dark': '#141414',          # Main background
    'bg_medium': '#1a1a1a',        # Card/panel background
    'bg_light': '#242424',         # Elevated elements
    'bg_hover': '#2a2a2a',         # Hover state
    'bg_selected': '#0f3460',      # Selected item
    
    'border_dark': '#2a2a2a',      # Subtle borders
    'border_medium': '#3a3a3a',    # Normal borders
    'border_light': '#4a4a4a',     # Prominent borders
    
    'text_primary': '#ffffff',     # Primary text
    'text_secondary': '#b0b0b0',   # Secondary text
    'text_muted': '#707070',       # Muted text
    'text_dim': '#707070',         # Dim text (alias for muted)
    
    'accent_cyan': '#00d9ff',      # Primary accent
    'accent_blue': '#007acc',      # Secondary accent
    'accent_green': '#4ec9b0',     # Success
    'accent_orange': '#ce9178',    # Warning
    'accent_red': '#f44747',       # Error/danger
    'accent_purple': '#c586c0',    # Special
    'accent_yellow': '#dcdcaa',    # Highlight
}

DARK_THEME_V2 = f"""
/* ============================================
   GLOBAL STYLES
   ============================================ */

QMainWindow {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', Arial, sans-serif;
}}

QWidget {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-size: 10pt;
}}

/* ============================================
   SIDEBAR NAVIGATION
   ============================================ */

QListWidget#sidebar {{
    background-color: {COLORS['bg_dark']};
    border: none;
    border-right: 1px solid {COLORS['border_dark']};
    outline: none;
    padding: 8px 4px;
}}

QListWidget#sidebar::item {{
    color: {COLORS['text_secondary']};
    padding: 12px 16px;
    margin: 2px 4px;
    border-radius: 6px;
    border: none;
}}

QListWidget#sidebar::item:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

QListWidget#sidebar::item:selected {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['accent_cyan']};
    font-weight: 600;
}}

/* ============================================
   CONTENT AREA
   ============================================ */

QStackedWidget {{
    background-color: {COLORS['bg_darkest']};
}}

QScrollArea {{
    background-color: {COLORS['bg_darkest']};
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background-color: {COLORS['bg_darkest']};
}}

/* ============================================
   GROUP BOXES (Cards)
   ============================================ */

QGroupBox {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    padding: 0 8px;
    color: {COLORS['accent_cyan']};
    font-size: 11pt;
    font-weight: 600;
}}

/* ============================================
   BUTTONS
   ============================================ */

QPushButton {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['text_primary']};
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-weight: 500;
    min-width: 100px;
}}

QPushButton:hover {{
    background-color: #1a8cd8;
}}

QPushButton:pressed {{
    background-color: #005a9e;
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}

/* Primary action button */
QPushButton[class="primary"] {{
    background-color: {COLORS['accent_cyan']};
    color: {COLORS['bg_darkest']};
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background-color: #33e0ff;
}}

/* Success button */
QPushButton[class="success"] {{
    background-color: {COLORS['accent_green']};
    color: {COLORS['bg_darkest']};
}}

/* Danger button */
QPushButton[class="danger"] {{
    background-color: {COLORS['accent_red']};
    color: {COLORS['text_primary']};
}}

/* Warning/Orange button */
QPushButton[class="warning"] {{
    background-color: {COLORS['accent_orange']};
    color: {COLORS['bg_darkest']};
}}

/* Purple button */
QPushButton[class="purple"] {{
    background-color: {COLORS['accent_purple']};
    color: {COLORS['text_primary']};
}}

/* ============================================
   INPUT FIELDS
   ============================================ */

QLineEdit {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    padding: 10px 12px;
    selection-background-color: {COLORS['bg_selected']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_cyan']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}

QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    padding: 10px;
    selection-background-color: {COLORS['bg_selected']};
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_cyan']};
}}

/* ============================================
   COMBO BOXES
   ============================================ */

QComboBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 150px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent_cyan']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    selection-background-color: {COLORS['bg_selected']};
    outline: none;
}}

/* ============================================
   CHECKBOXES
   ============================================ */

QCheckBox {{
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border_medium']};
    background-color: {COLORS['bg_dark']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_cyan']};
    border-color: {COLORS['accent_cyan']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['accent_cyan']};
}}

/* ============================================
   TABLES
   ============================================ */

QTableWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    gridline-color: {COLORS['border_dark']};
    selection-background-color: {COLORS['bg_selected']};
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border_dark']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['bg_selected']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['accent_cyan']};
    padding: 10px;
    border: none;
    border-bottom: 2px solid {COLORS['accent_cyan']};
    font-weight: 600;
}}

/* ============================================
   LIST WIDGETS
   ============================================ */

QListWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
    border-bottom: 1px solid {COLORS['border_dark']};
}}

QListWidget::item:selected {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['accent_cyan']};
}}

QListWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* ============================================
   PROGRESS BARS
   ============================================ */

QProgressBar {{
    background-color: {COLORS['bg_dark']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent_cyan']};
    border-radius: 4px;
}}

/* ============================================
   SCROLL BARS
   ============================================ */

QScrollBar:vertical {{
    background-color: {COLORS['bg_dark']};
    width: 12px;
    border-radius: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['border_medium']};
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border_light']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_dark']};
    height: 12px;
    border-radius: 6px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['border_medium']};
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

/* ============================================
   LABELS
   ============================================ */

QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel[class="header"] {{
    font-size: 18pt;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

QLabel[class="subheader"] {{
    font-size: 14pt;
    font-weight: 600;
    color: {COLORS['accent_cyan']};
}}

QLabel[class="muted"] {{
    color: {COLORS['text_muted']};
    font-size: 9pt;
}}

QLabel[class="success"] {{
    color: {COLORS['accent_green']};
}}

QLabel[class="error"] {{
    color: {COLORS['accent_red']};
}}

/* ============================================
   LINKS - No underlines, color only
   ============================================ */

QLabel a {{
    color: {COLORS['accent_cyan']};
    text-decoration: none;
}}

QTextEdit a, QPlainTextEdit a {{
    color: {COLORS['accent_cyan']};
    text-decoration: none;
}}

/* For QTextBrowser if used */
QTextBrowser a {{
    color: {COLORS['accent_cyan']};
    text-decoration: none;
}}

QTextBrowser a:hover {{
    color: {COLORS['accent_blue']};
}}

/* ============================================
   SPLITTERS
   ============================================ */

QSplitter::handle {{
    background-color: {COLORS['border_dark']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* ============================================
   TAB WIDGETS (for internal tabs if needed)
   ============================================ */

QTabWidget::pane {{
    border: 1px solid {COLORS['border_dark']};
    border-radius: 6px;
    background-color: {COLORS['bg_medium']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['accent_cyan']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

/* ============================================
   STATUS BAR
   ============================================ */

QStatusBar {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border_dark']};
    padding: 4px 12px;
}}

/* ============================================
   TOOLTIPS
   ============================================ */

QToolTip {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ============================================
   MENU BAR
   ============================================ */

QMenuBar {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border_dark']};
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenu {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
}}

QMenu::item:selected {{
    background-color: {COLORS['bg_selected']};
}}
"""

# Export both for compatibility
DARK_THEME_STYLESHEET = DARK_THEME_V2
