"""
Manifests - Run manifests and hashes for reproducibility

Responsibilities:
- Generate deterministic hashes of scripts, configs, and data
- Create run manifests that capture full execution context
- Enable reproducibility verification months later
"""

import hashlib
import json
import logging
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RunManifest:
    """Complete manifest of a script run for reproducibility."""

    run_id: str
    script_name: str
    script_version: str
    script_hash: str
    config: dict[str, Any]
    config_hash: str
    target_db: str
    data_snapshot_hash: str | None
    dependencies: dict[str, str]
    environment: dict[str, str]
    created_at: datetime = field(default_factory=datetime.now)
    manifest_hash: str = ""

    def __post_init__(self):
        if not self.manifest_hash:
            self.manifest_hash = self._compute_manifest_hash()

    def _compute_manifest_hash(self) -> str:
        """Compute hash of the entire manifest."""
        data = {
            "run_id": self.run_id,
            "script_hash": self.script_hash,
            "config_hash": self.config_hash,
            "data_snapshot_hash": self.data_snapshot_hash,
        }
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "run_id": self.run_id,
            "script_name": self.script_name,
            "script_version": self.script_version,
            "script_hash": self.script_hash,
            "config": self.config,
            "config_hash": self.config_hash,
            "target_db": self.target_db,
            "data_snapshot_hash": self.data_snapshot_hash,
            "dependencies": self.dependencies,
            "environment": self.environment,
            "created_at": self.created_at.isoformat(),
            "manifest_hash": self.manifest_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunManifest":
        """Create from dictionary."""
        return cls(
            run_id=data["run_id"],
            script_name=data["script_name"],
            script_version=data["script_version"],
            script_hash=data["script_hash"],
            config=data["config"],
            config_hash=data["config_hash"],
            target_db=data["target_db"],
            data_snapshot_hash=data.get("data_snapshot_hash"),
            dependencies=data.get("dependencies", {}),
            environment=data.get("environment", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            manifest_hash=data.get("manifest_hash", ""),
        )


class ManifestGenerator:
    """Generates run manifests for reproducibility tracking."""

    def __init__(self, manifests_dir: Path):
        self.manifests_dir = Path(manifests_dir)
        self.manifests_dir.mkdir(parents=True, exist_ok=True)

    def create_manifest(
        self,
        run_id: str,
        script_path: Path,
        script_name: str,
        script_version: str,
        config: dict[str, Any],
        target_db: str,
        data_files: list[Path] | None = None,
    ) -> RunManifest:
        """
        Create a complete run manifest.

        Args:
            run_id: Unique run identifier.
            script_path: Path to the script file.
            script_name: Name of the script.
            script_version: Version of the script.
            config: Configuration used for the run.
            target_db: Target database name.
            data_files: Optional list of input data files.

        Returns:
            Complete RunManifest.
        """
        manifest = RunManifest(
            run_id=run_id,
            script_name=script_name,
            script_version=script_version,
            script_hash=self.hash_file(script_path),
            config=config,
            config_hash=self.hash_config(config),
            target_db=target_db,
            data_snapshot_hash=self._hash_data_files(data_files),
            dependencies=self._capture_dependencies(),
            environment=self._capture_environment(),
        )

        # Save manifest to file
        self._save_manifest(manifest)

        return manifest

    def hash_file(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        if not path.exists():
            return ""

        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def hash_config(self, config: dict[str, Any]) -> str:
        """Compute deterministic hash of configuration."""
        content = json.dumps(config, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _hash_data_files(self, files: list[Path] | None) -> str | None:
        """Compute combined hash of data files."""
        if not files:
            return None

        combined = hashlib.sha256()
        for path in sorted(files):
            if path.exists():
                file_hash = self.hash_file(path)
                combined.update(file_hash.encode())
        return combined.hexdigest()

    def _capture_dependencies(self) -> dict[str, str]:
        """Capture versions of key dependencies."""
        deps = {
            "python": platform.python_version(),
        }

        # Try to get versions of key packages
        packages = ["pandas", "numpy", "psycopg2", "customtkinter", "pyyaml"]
        for pkg in packages:
            try:
                import importlib.metadata
                deps[pkg] = importlib.metadata.version(pkg)
            except Exception:
                pass

        return deps

    def _capture_environment(self) -> dict[str, str]:
        """Capture environment information."""
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "architecture": platform.machine(),
        }

    def _save_manifest(self, manifest: RunManifest) -> Path:
        """Save manifest to JSON file."""
        path = self.manifests_dir / f"{manifest.run_id}_manifest.json"
        with open(path, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        logger.info(f"Saved manifest: {path}")
        return path

    def load_manifest(self, run_id: str) -> RunManifest | None:
        """Load a manifest by run ID."""
        path = self.manifests_dir / f"{run_id}_manifest.json"
        if not path.exists():
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return RunManifest.from_dict(data)

    def verify_manifest(
        self,
        manifest: RunManifest,
        script_path: Path,
    ) -> dict[str, bool]:
        """
        Verify that current state matches a saved manifest.

        Returns:
            Dictionary of verification results.
        """
        results = {}

        # Verify script hash
        current_script_hash = self.hash_file(script_path)
        results["script_unchanged"] = current_script_hash == manifest.script_hash

        # Verify manifest hash integrity
        recomputed_hash = manifest._compute_manifest_hash()
        results["manifest_valid"] = recomputed_hash == manifest.manifest_hash

        # Check Python version
        results["python_version_match"] = (
            manifest.environment.get("python_version") == platform.python_version()
        )

        return results


class EvidenceRegistry:
    """
    Registry for academic evidence claims.

    Links analytical claims to their source runs for reproducibility.
    """

    def __init__(self, db):
        self.db = db
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure evidence table exists."""
        cursor = self.db.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta.evidence (
                id SERIAL PRIMARY KEY,
                paper_id TEXT,
                claim TEXT NOT NULL,
                source_dataset TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                query_text TEXT,
                result_value NUMERIC,
                ci_low NUMERIC,
                ci_high NUMERIC,
                result_context JSONB,
                computed_at TIMESTAMP NOT NULL,
                script_version TEXT NOT NULL,
                run_id TEXT,
                verified_at TIMESTAMP,
                verification_status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.db.commit()
        cursor.close()

    def register_claim(
        self,
        claim: str,
        source_dataset: str,
        query_text: str,
        result_value: float,
        script_version: str,
        run_id: str | None = None,
        paper_id: str | None = None,
        ci_low: float | None = None,
        ci_high: float | None = None,
        context: dict[str, Any] | None = None,
    ) -> int:
        """
        Register an analytical claim for a paper.

        Args:
            claim: Description of the claim (e.g., "Treatment A reduces X by 15%")
            source_dataset: Name of the dataset used.
            query_text: SQL or code that produced the result.
            result_value: The numeric result value.
            script_version: Version of the analysis script.
            run_id: Optional link to a specific run.
            paper_id: Optional paper identifier.
            ci_low: Lower bound of confidence interval.
            ci_high: Upper bound of confidence interval.
            context: Additional context (sample size, etc.)

        Returns:
            ID of the registered evidence.
        """
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]

        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO meta.evidence
            (paper_id, claim, source_dataset, query_hash, query_text,
             result_value, ci_low, ci_high, result_context,
             computed_at, script_version, run_id, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id;
        """, (
            paper_id,
            claim,
            source_dataset,
            query_hash,
            query_text,
            result_value,
            ci_low,
            ci_high,
            json.dumps(context) if context else None,
            datetime.now(),
            script_version,
            run_id,
        ))

        evidence_id = cursor.fetchone()[0]
        self.db.commit()
        cursor.close()

        logger.info(f"Registered evidence claim: {evidence_id}")
        return evidence_id

    def verify_claim(self, evidence_id: int) -> dict[str, Any]:
        """
        Verify an evidence claim by re-running its query.

        Returns verification status and any discrepancies.
        """
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT query_text, result_value, source_dataset
            FROM meta.evidence WHERE id = %s;
        """, (evidence_id,))

        row = cursor.fetchone()
        if not row:
            return {"error": "Evidence not found"}

        query_text, original_value, source_dataset = row

        try:
            # Re-run the query
            cursor.execute(query_text)
            new_result = cursor.fetchone()
            new_value = new_result[0] if new_result else None

            # Compare values
            if new_value is not None and original_value is not None:
                match = abs(float(new_value) - float(original_value)) < 0.0001
                status = "verified" if match else "failed"
            else:
                status = "failed"

            # Update verification status
            cursor.execute("""
                UPDATE meta.evidence
                SET verified_at = %s, verification_status = %s
                WHERE id = %s;
            """, (datetime.now(), status, evidence_id))

            self.db.commit()
            cursor.close()

            return {
                "status": status,
                "original_value": original_value,
                "new_value": new_value,
                "verified_at": datetime.now().isoformat(),
            }

        except Exception as e:
            cursor.close()
            return {"error": str(e), "status": "failed"}

    def get_claims_for_paper(self, paper_id: str) -> list[dict]:
        """Get all evidence claims for a paper."""
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT id, claim, source_dataset, result_value, ci_low, ci_high,
                   verification_status, computed_at
            FROM meta.evidence
            WHERE paper_id = %s
            ORDER BY id;
        """, (paper_id,))

        columns = ["id", "claim", "source_dataset", "result_value",
                   "ci_low", "ci_high", "verification_status", "computed_at"]
        rows = cursor.fetchall()
        cursor.close()

        return [dict(zip(columns, row)) for row in rows]
