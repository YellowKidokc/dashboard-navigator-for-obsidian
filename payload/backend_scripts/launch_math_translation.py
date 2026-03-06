"""
Quick launcher for Math Translation feature
Bypasses full app initialization to just show the Math Translation tab
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt

# Add engine path
sys.path.insert(0, str(Path(__file__).parent))

from engine.settings import SettingsManager
from engine.database_engine import DatabaseEngine
from engine.math_translation_engine import MathTranslationEngine

# Import just the math translation page builder from main
from main import TheophysicsManager

class MathTranslationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Math Translation Layer")
        self.resize(1200, 800)
        self.setStyleSheet(self._get_stylesheet())
        
        # Minimal initialization
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()
        
        # Create database with fallback
        try:
            self.db_engine = DatabaseEngine(self.settings_mgr)
        except Exception as e:
            print(f"[WARN] Database init failed: {e}")
            # Create minimal mock
            class MockDB:
                def __init__(self):
                    pass
            self.db_engine = MockDB()
        
        self.math_engine = MathTranslationEngine(self.settings_mgr, self.db_engine)
        
        # Build UI
        self._init_ui()
    
    def _get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #1a1a2e;
        }
        QWidget {
            background-color: #1a1a2e;
            color: #eaeaea;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            background-color: #16213e;
            border: 1px solid #0f3460;
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: #00d9ff;
        }
        QPushButton {
            background-color: #0f3460;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            color: #eaeaea;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #1f4068;
        }
        QPushButton#primaryBtn {
            background-color: #00d9ff;
            color: #1a1a2e;
        }
        QPushButton#primaryBtn:hover {
            background-color: #00b8d4;
        }
        QLineEdit, QTextEdit {
            background-color: #0f3460;
            border: 1px solid #1f4068;
            border-radius: 6px;
            padding: 8px;
            color: #eaeaea;
        }
        QProgressBar {
            background-color: #0f3460;
            border-radius: 4px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #00d9ff;
            border-radius: 4px;
        }
        QLabel#metricsLabel {
            background-color: #0f3460;
            border-radius: 6px;
            padding: 12px;
            font-family: 'Consolas', monospace;
        }
        """
    
    def _init_ui(self):
        # Use the math translation page builder from main.py
        manager = TheophysicsManager.__new__(TheophysicsManager)
        manager.math_engine = self.math_engine
        manager.settings_mgr = self.settings_mgr
        
        # Build the page
        page = manager._build_math_translation_page()
        
        self.setCentralWidget(page)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MathTranslationApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
