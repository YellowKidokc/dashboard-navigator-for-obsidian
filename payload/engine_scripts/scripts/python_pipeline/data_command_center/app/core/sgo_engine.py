"""
S/G/O Computation Engine

Centralized computation of standardized thermodynamic variables:
- S (Entropy): Disorder/chaos indicators
- G (Grace): Support/protective factors
- O (Observer): Engagement/awareness measures

Computes derived metric: OG/S = (O * G) / (S + ε)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Default epsilon to prevent division by zero
DEFAULT_EPSILON = 0.0001


@dataclass
class SGOResult:
    """Result of S/G/O computation for a subject."""

    subject_id: str
    s_entropy: float
    g_grace: float
    o_observer: float
    og_over_s: float
    component_values: dict[str, float]
    computed_at: datetime
    source_dataset: str
    script_version: str


class SGOEngine:
    """
    Computes S/G/O variables from staging data.

    S/G/O Framework:
    - S (Entropy): Measures disorder, chaos, severity - higher = worse
    - G (Grace): Measures support, resources, protection - higher = better
    - O (Observer): Measures engagement, readiness, awareness - higher = better
    - OG/S: Combined metric where higher = better prognosis
    """

    def __init__(self, epsilon: float = DEFAULT_EPSILON):
        self.epsilon = epsilon

    def compute(
        self,
        subject_id: str,
        variable_mapping: dict[str, Any],
        data: dict[str, Any],
        source_dataset: str,
        script_version: str,
    ) -> SGOResult:
        """
        Compute S/G/O variables for a subject.

        Args:
            subject_id: Unique identifier for the subject.
            variable_mapping: Mapping from SCRIPT_SPEC defining which
                              data columns map to S, G, O components.
            data: Raw data dictionary with column values.
            source_dataset: Name of the source dataset.
            script_version: Version of the ingestion script.

        Returns:
            SGOResult with computed values.
        """
        component_values = {}

        # Compute S (Entropy)
        s_columns = variable_mapping.get("s_entropy", [])
        s_values = self._extract_values(data, s_columns)
        s_entropy = self._compute_component(s_values, "entropy")
        component_values["s_raw"] = s_values

        # Compute G (Grace)
        g_columns = variable_mapping.get("g_grace", [])
        g_values = self._extract_values(data, g_columns)
        g_grace = self._compute_component(g_values, "grace")
        component_values["g_raw"] = g_values

        # Compute O (Observer)
        o_columns = variable_mapping.get("o_observer", [])
        o_values = self._extract_values(data, o_columns)
        o_observer = self._compute_component(o_values, "observer")
        component_values["o_raw"] = o_values

        # Compute OG/S
        og_over_s = (o_observer * g_grace) / (s_entropy + self.epsilon)

        return SGOResult(
            subject_id=subject_id,
            s_entropy=s_entropy,
            g_grace=g_grace,
            o_observer=o_observer,
            og_over_s=og_over_s,
            component_values=component_values,
            computed_at=datetime.now(),
            source_dataset=source_dataset,
            script_version=script_version,
        )

    def compute_batch(
        self,
        records: list[dict[str, Any]],
        variable_mapping: dict[str, Any],
        id_column: str,
        source_dataset: str,
        script_version: str,
    ) -> list[SGOResult]:
        """
        Compute S/G/O variables for a batch of records.

        Args:
            records: List of data dictionaries.
            variable_mapping: Mapping from SCRIPT_SPEC.
            id_column: Column name to use as subject_id.
            source_dataset: Name of the source dataset.
            script_version: Version of the ingestion script.

        Returns:
            List of SGOResult objects.
        """
        results = []

        for record in records:
            subject_id = str(record.get(id_column, "unknown"))
            try:
                result = self.compute(
                    subject_id=subject_id,
                    variable_mapping=variable_mapping,
                    data=record,
                    source_dataset=source_dataset,
                    script_version=script_version,
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to compute SGO for {subject_id}: {e}")

        return results

    def _extract_values(
        self,
        data: dict[str, Any],
        columns: list[str],
    ) -> list[float]:
        """Extract numeric values from data for specified columns."""
        values = []
        for col in columns:
            val = data.get(col)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        return values

    def _compute_component(
        self,
        values: list[float],
        component_type: str,
    ) -> float:
        """
        Compute a single S/G/O component from raw values.

        Default implementation uses normalized mean.
        Can be extended with component-specific logic.
        """
        if not values:
            return 0.0

        arr = np.array(values)

        # Normalize to 0-1 range (assuming values are on similar scales)
        # In production, normalization parameters would be dataset-specific
        normalized = self._normalize(arr)

        # Return mean of normalized values
        return float(np.mean(normalized))

    def _normalize(self, values: np.ndarray) -> np.ndarray:
        """Normalize values to 0-1 range."""
        if len(values) == 0:
            return values

        min_val = np.min(values)
        max_val = np.max(values)

        if max_val == min_val:
            return np.zeros_like(values)

        return (values - min_val) / (max_val - min_val)

    def save_results(
        self,
        db,
        results: list[SGOResult],
    ) -> int:
        """
        Save computed S/G/O results to the database.

        Writes to: analysis.subject_variables

        Args:
            db: Database connection.
            results: List of SGOResult objects to save.

        Returns:
            Number of records saved.
        """
        cursor = db.cursor()

        # Ensure schema and table exist
        cursor.execute("CREATE SCHEMA IF NOT EXISTS analysis;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis.subject_variables (
                id SERIAL PRIMARY KEY,
                subject_id TEXT NOT NULL,
                s_entropy NUMERIC,
                g_grace NUMERIC,
                o_observer NUMERIC,
                og_over_s NUMERIC,
                component_values JSONB,
                computed_at TIMESTAMP,
                source_dataset TEXT,
                script_version TEXT,
                UNIQUE(subject_id, source_dataset, computed_at)
            );
        """)

        saved_count = 0
        for result in results:
            try:
                import json
                cursor.execute("""
                    INSERT INTO analysis.subject_variables
                    (subject_id, s_entropy, g_grace, o_observer, og_over_s,
                     component_values, computed_at, source_dataset, script_version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (subject_id, source_dataset, computed_at)
                    DO UPDATE SET
                        s_entropy = EXCLUDED.s_entropy,
                        g_grace = EXCLUDED.g_grace,
                        o_observer = EXCLUDED.o_observer,
                        og_over_s = EXCLUDED.og_over_s,
                        component_values = EXCLUDED.component_values,
                        script_version = EXCLUDED.script_version;
                """, (
                    result.subject_id,
                    result.s_entropy,
                    result.g_grace,
                    result.o_observer,
                    result.og_over_s,
                    json.dumps(result.component_values),
                    result.computed_at,
                    result.source_dataset,
                    result.script_version,
                ))
                saved_count += 1
            except Exception as e:
                logger.warning(f"Failed to save SGO for {result.subject_id}: {e}")

        cursor.close()
        db.commit()

        logger.info(f"Saved {saved_count} S/G/O results to database")
        return saved_count


def compute_sgo_from_staging(
    db,
    script_info,
    staging_table: str,
    id_column: str,
    epsilon: float = DEFAULT_EPSILON,
) -> list[SGOResult]:
    """
    Convenience function to compute S/G/O from a staging table.

    Args:
        db: Database connection.
        script_info: ScriptInfo object with variable_mapping.
        staging_table: Name of the staging table (schema.table).
        id_column: Column to use as subject identifier.
        epsilon: Small value for OG/S computation.

    Returns:
        List of computed SGOResult objects.
    """
    cursor = db.cursor()

    # Fetch all records from staging
    cursor.execute(f"SELECT * FROM {staging_table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()

    # Convert to list of dicts
    records = [dict(zip(columns, row)) for row in rows]

    # Compute S/G/O
    engine = SGOEngine(epsilon=epsilon)
    results = engine.compute_batch(
        records=records,
        variable_mapping=script_info.variable_mapping,
        id_column=id_column,
        source_dataset=script_info.name,
        script_version=script_info.version,
    )

    # Save to database
    engine.save_results(db, results)

    return results
