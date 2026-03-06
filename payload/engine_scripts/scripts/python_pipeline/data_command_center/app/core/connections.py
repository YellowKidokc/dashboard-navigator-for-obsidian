"""
Connection Resolver - Manages database connections

Responsibilities:
- Load connection configurations from YAML
- Resolve credentials from environment variables or keyring
- Provide database handles to scripts
"""

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import keyring
import yaml

logger = logging.getLogger(__name__)

# Pattern to match ${ENV_VAR_NAME}
ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")
# Pattern to match keyring:service_name
KEYRING_PATTERN = re.compile(r"^keyring:(.+)$")


@dataclass
class ConnectionConfig:
    """Database connection configuration."""

    name: str
    type: str
    config: dict[str, Any]


class ConnectionResolver:
    """Resolves and manages database connections."""

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._connections: dict[str, ConnectionConfig] = {}
        self._default: str | None = None
        self._load_config()

    def _load_config(self) -> None:
        """Load connections from YAML configuration."""
        if not self.config_path.exists():
            logger.warning(f"Connections config not found: {self.config_path}")
            return

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        self._default = config.get("default")
        databases = config.get("databases", {})

        for name, db_config in databases.items():
            db_type = db_config.pop("type", "postgresql")
            self._connections[name] = ConnectionConfig(
                name=name,
                type=db_type,
                config=db_config,
            )

    def _resolve_value(self, value: Any) -> Any:
        """Resolve environment variables and keyring references in a value."""
        if not isinstance(value, str):
            return value

        # Check for keyring reference
        keyring_match = KEYRING_PATTERN.match(value)
        if keyring_match:
            service_name = keyring_match.group(1)
            password = keyring.get_password(service_name, "default")
            if password is None:
                logger.warning(f"No keyring entry found for service: {service_name}")
                return None
            return password

        # Check for environment variable references
        def replace_env_var(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                logger.warning(f"Environment variable not set: {var_name}")
                return ""
            return env_value

        return ENV_VAR_PATTERN.sub(replace_env_var, value)

    def _resolve_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Resolve all credential references in a config dictionary."""
        resolved = {}
        for key, value in config.items():
            resolved[key] = self._resolve_value(value)
        return resolved

    def get_connection(self, name: str | None = None):
        """
        Get a database connection by name.

        Args:
            name: Connection name. Uses default if None.

        Returns:
            Database connection object.
        """
        conn_name = name or self._default
        if conn_name is None:
            raise ValueError("No connection name specified and no default set")

        if conn_name not in self._connections:
            raise ValueError(f"Unknown connection: {conn_name}")

        conn_config = self._connections[conn_name]
        resolved_config = self._resolve_config(conn_config.config)

        return self._create_connection(conn_config.type, resolved_config)

    def _create_connection(self, db_type: str, config: dict[str, Any]):
        """Create a database connection based on type."""
        if db_type == "postgresql":
            return self._create_postgres_connection(config)
        elif db_type == "cloudflare_d1":
            return self._create_d1_connection(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    def _create_postgres_connection(self, config: dict[str, Any]):
        """Create a PostgreSQL connection."""
        import psycopg2

        return psycopg2.connect(
            host=config.get("host", "localhost"),
            port=config.get("port", 5432),
            database=config.get("database"),
            user=config.get("user"),
            password=config.get("password"),
        )

    def _create_d1_connection(self, config: dict[str, Any]):
        """Create a Cloudflare D1 connection wrapper."""
        return D1Connection(
            account_id=config.get("account_id"),
            database_id=config.get("database_id"),
            api_token=config.get("api_token"),
        )

    def list_connections(self) -> list[str]:
        """List all available connection names."""
        return list(self._connections.keys())

    def get_default(self) -> str | None:
        """Get the default connection name."""
        return self._default


class D1Connection:
    """
    Wrapper for Cloudflare D1 database operations.

    Provides a similar interface to psycopg2 for basic operations.
    """

    def __init__(self, account_id: str, database_id: str, api_token: str):
        self.account_id = account_id
        self.database_id = database_id
        self.api_token = api_token
        self._base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}"

    def execute(self, sql: str, params: list | None = None) -> dict:
        """Execute a SQL statement."""
        import httpx

        response = httpx.post(
            f"{self._base_url}/query",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            json={
                "sql": sql,
                "params": params or [],
            },
        )
        response.raise_for_status()
        return response.json()

    def cursor(self):
        """Return a cursor-like object for compatibility."""
        return D1Cursor(self)

    def commit(self):
        """D1 auto-commits, so this is a no-op."""
        pass

    def close(self):
        """Close the connection (no-op for HTTP-based connection)."""
        pass


class D1Cursor:
    """Cursor-like wrapper for D1 operations."""

    def __init__(self, connection: D1Connection):
        self.connection = connection
        self._results: list = []
        self._index = 0

    def execute(self, sql: str, params: list | None = None):
        """Execute a SQL statement."""
        result = self.connection.execute(sql, params)
        if result.get("success") and result.get("result"):
            self._results = result["result"][0].get("results", [])
        else:
            self._results = []
        self._index = 0

    def fetchone(self):
        """Fetch one result row."""
        if self._index < len(self._results):
            row = self._results[self._index]
            self._index += 1
            return tuple(row.values())
        return None

    def fetchall(self):
        """Fetch all result rows."""
        rows = self._results[self._index:]
        self._index = len(self._results)
        return [tuple(row.values()) for row in rows]

    def close(self):
        """Close the cursor."""
        self._results = []
        self._index = 0
