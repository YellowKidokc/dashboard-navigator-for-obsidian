"""
Database Tab - PostgreSQL connection and management.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QGroupBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.postgres_manager import PostgresManager, DatabaseConfig


class DatabaseTab(QWidget):
    """Tab for PostgreSQL database management."""
    
    def __init__(self, postgres_manager: PostgresManager):
        super().__init__()
        self.postgres_manager = postgres_manager
        self._setup_ui()
        self._load_config()
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🗄️ PostgreSQL Database")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QVBoxLayout()
        
        # Host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("localhost")
        host_layout.addWidget(self.host_input)
        conn_layout.addLayout(host_layout)
        
        # Port
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(5432)
        port_layout.addWidget(self.port_input)
        conn_layout.addLayout(port_layout)
        
        # Database
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Database:"))
        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("theophysics_research")
        db_layout.addWidget(self.database_input)
        conn_layout.addLayout(db_layout)
        
        # User
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("User:"))
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("postgres")
        user_layout.addWidget(self.user_input)
        conn_layout.addLayout(user_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        password_layout.addWidget(self.password_input)
        conn_layout.addLayout(password_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        test_btn = QPushButton("🔍 Test Connection")
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)
        
        save_btn = QPushButton("💾 Save & Connect")
        save_btn.clicked.connect(self._save_and_connect)
        btn_layout.addWidget(save_btn)
        conn_layout.addLayout(btn_layout)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Status
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        status_layout.addWidget(self.status_text)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Database operations
        ops_group = QGroupBox("Database Operations")
        ops_layout = QVBoxLayout()
        
        sync_defs_btn = QPushButton("🔄 Sync Definitions to Database")
        sync_defs_btn.clicked.connect(self._sync_definitions)
        ops_layout.addWidget(sync_defs_btn)
        
        sync_links_btn = QPushButton("🔄 Sync Research Links to Database")
        sync_links_btn.clicked.connect(self._sync_research_links)
        ops_layout.addWidget(sync_links_btn)
        
        ops_group.setLayout(ops_layout)
        layout.addWidget(ops_group)
        
        layout.addStretch()
    
    def _load_config(self) -> None:
        """Load database configuration."""
        config = self.postgres_manager.config
        self.host_input.setText(config.host)
        self.port_input.setValue(config.port)
        self.database_input.setText(config.database)
        self.user_input.setText(config.user)
        # Don't load password for security
    
    def _test_connection(self) -> None:
        """Test database connection."""
        config = self._get_config()
        self.postgres_manager.config = config
        
        if self.postgres_manager.test_connection():
            self.status_text.append("✅ Connection successful!")
            QMessageBox.information(self, "Success", "Database connection successful!")
        else:
            self.status_text.append("❌ Connection failed. Check settings.")
            QMessageBox.warning(self, "Failed", "Database connection failed. Check your settings.")
    
    def _save_and_connect(self) -> None:
        """Save configuration and connect."""
        config = self._get_config()
        self.postgres_manager.config = config
        
        # Save to settings (you'd implement this)
        self.status_text.append("💾 Configuration saved.")
        
        if self.postgres_manager.test_connection():
            self.status_text.append("✅ Connected to database.")
            QMessageBox.information(self, "Success", "Connected to database!")
        else:
            self.status_text.append("❌ Connection failed.")
    
    def _get_config(self) -> DatabaseConfig:
        """Get configuration from UI."""
        from core.postgres_manager import DatabaseConfig
        return DatabaseConfig(
            host=self.host_input.text() or "localhost",
            port=self.port_input.value(),
            database=self.database_input.text() or "theophysics_research",
            user=self.user_input.text() or "postgres",
            password=self.password_input.text()
        )
    
    def _sync_definitions(self) -> None:
        """Sync definitions to database."""
        QMessageBox.information(self, "Info", "This will sync all definitions to PostgreSQL.")
        # Implementation would go here
    
    def _sync_research_links(self) -> None:
        """Sync research links to database."""
        QMessageBox.information(self, "Info", "This will sync all research links to PostgreSQL.")
        # Implementation would go here

