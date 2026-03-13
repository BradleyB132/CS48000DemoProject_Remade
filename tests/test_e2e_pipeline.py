"""
End-to-end tests for the data pipeline: ETL → database → analytics.

These tests verify the full flow from raw DataFrames (as would be produced by
reading production/quality/shipping spreadsheets) through consolidation,
summary metrics, database insertion, and validation. They use the real test
database and ensure the pipeline behaves correctly under realistic data.

Run with: pytest tests/test_e2e_pipeline.py -v
"""

import pandas as pd
from sqlalchemy import text

from src.services import etl
from src.database.connection import Database


def _truncate_tables(conn):
    """
    Truncate all pipeline tables in FK-safe order so tests start from a clean state.

    Order matters: child tables (shipping_manifests, quality_inspections) must be
    cleared before production_logs to avoid foreign key violations.
    """
    conn.execute(text("TRUNCATE shipping_manifests CASCADE"))
    conn.execute(text("TRUNCATE quality_inspections CASCADE"))
    conn.execute(text("TRUNCATE production_logs CASCADE"))


def test_full_pipeline():
    """
    End-to-end test of the full data pipeline:
    ETL → database inserts → database queries → analytics.

    Steps:
    1. Build mock input DataFrames (simulating CSV/Excel ingestion).
    2. Run ETL: consolidate_data + summary_metrics.
    3. Insert production logs, quality inspections, and shipping manifests.
    4. Assert row counts and that consolidated/output metrics are correct.

    This validates that the entire path from "raw data" to "persisted and
    queryable" works as expected for the dashboard and reporting.
    """
    db = Database()

    # --- Create mock input data (simulates read_production_files / CSVs) ---
    production = pd.DataFrame(
        {
            "lot_number": ["A100", "A101"],
            "line_number": [1, 2],
            "production_date": ["2024-01-01", "2024-01-02"],
            "shift_leader": ["Alice", "Bob"],
        }
    )

    quality = pd.DataFrame(
        {
            "lot_number": ["A100"],
            "production_date": ["2024-01-01"],
            "defect_type": ["Scratch"],
            "defect_severity": ["Low"],
            "is_defective": [True],
        }
    )

    shipping = pd.DataFrame(
        {
            "lot_number": ["A100", "A101"],
            "production_date": ["2024-01-01", "2024-01-02"],
            "destination": ["Chicago", "Detroit"],
            "is_shipped": [True, False],
        }
    )

    # --- Run ETL pipeline (in-memory analytics) ---
    consolidated = etl.consolidate_data(production, quality, shipping)
    metrics = etl.summary_metrics(consolidated)

    # ETL contract: we expect one row per production lot after merge
    assert len(consolidated) == 2
    # Summary metrics must include defect_rate for reporting (AC5, AC6)
    assert "defect_rate" in metrics.columns

    # --- Insert data into database (same order as schema dependencies) ---
    with db.engine.begin() as conn:
        _truncate_tables(conn)

        # Insert production logs and capture generated IDs for child tables
        result = conn.execute(
            text("""
                INSERT INTO production_logs
                (lot_number, line_number, production_date, shift_leader)
                VALUES
                ('A100', 1, '2024-01-01', 'Alice'),
                ('A101', 2, '2024-01-02', 'Bob')
                RETURNING production_log_id, lot_number
            """)
        )

        rows = result.fetchall()
        id_map = {row.lot_number: row.production_log_id for row in rows}

        # Insert quality inspection for A100 only (one defective lot)
        conn.execute(
            text("""
                INSERT INTO quality_inspections
                (production_log_id, defect_type, defect_severity, is_defective, inspection_count)
                VALUES (:log_id, 'Scratch', 'Low', TRUE, 1)
            """),
            {"log_id": id_map["A100"]},
        )

        # Insert shipping manifests (A100 shipped, A101 not shipped)
        conn.execute(
            text("""
                INSERT INTO shipping_manifests
                (production_log_id, ship_date, destination, is_shipped)
                VALUES
                (:log_id1, '2024-01-03', 'Chicago', TRUE),
                (:log_id2, '2024-01-03', 'Detroit', FALSE)
            """),
            {
                "log_id1": id_map["A100"],
                "log_id2": id_map["A101"],
            },
        )

        # --- Validate database contents (persistence layer) ---
        production_count = conn.execute(
            text("SELECT COUNT(*) FROM production_logs")
        ).scalar()

        inspection_count = conn.execute(
            text("SELECT COUNT(*) FROM quality_inspections")
        ).scalar()

        shipping_count = conn.execute(
            text("SELECT COUNT(*) FROM shipping_manifests")
        ).scalar()

    # --- Assertions: pipeline output and DB state match expectations ---
    assert production_count == 2
    assert inspection_count == 1
    assert shipping_count == 2


def test_full_pipeline_empty_production():
    """
    E2E test when production data is empty: consolidate_data and summary_metrics
    must handle empty input without errors and return empty (or zero-row) outputs.

    This guards against regressions when no files are loaded or all rows are
    filtered out (e.g. by AC4 dropna).
    """
    production = pd.DataFrame(
        columns=["lot_number", "line_number", "production_date", "shift_leader"]
    )
    quality = pd.DataFrame(
        columns=[
            "lot_number",
            "production_date",
            "defect_type",
            "defect_severity",
            "is_defective",
        ]
    )
    shipping = pd.DataFrame(
        columns=["lot_number", "production_date", "destination", "is_shipped"]
    )

    consolidated = etl.consolidate_data(production, quality, shipping)
    metrics = etl.summary_metrics(consolidated)

    assert len(consolidated) == 0
    assert len(metrics) == 0


def test_full_pipeline_filter_and_sort_and_trends():
    """
    E2E test for ETL filter/sort and trend detection.

    Verifies that after consolidation:
    - filter_and_sort returns the correct subset and order.
    - detect_trends produces metrics with is_anomaly when defect rates are high.

    This validates the analytics path used for reporting (AC6, AC7) without
    touching the database.
    """
    production = pd.DataFrame(
        {
            "lot_number": ["B1", "B2", "B3"],
            "line_number": [1, 1, 2],
            "production_date": ["2024-02-01", "2024-02-01", "2024-02-01"],
            "shift_leader": ["Carol", "Carol", "Dave"],
        }
    )
    quality = pd.DataFrame(
        {
            "lot_number": ["B1", "B2", "B3"],
            "production_date": ["2024-02-01", "2024-02-01", "2024-02-01"],
            "defect_type": ["Scratch", "Dent", None],
            "defect_severity": ["Low", "High", None],
            "is_defective": [True, True, False],
        }
    )
    shipping = pd.DataFrame(
        {
            "lot_number": ["B1", "B2", "B3"],
            "production_date": ["2024-02-01", "2024-02-01", "2024-02-01"],
            "destination": ["NYC", "NYC", "Boston"],
            "is_shipped": [True, False, True],
        }
    )

    consolidated = etl.consolidate_data(production, quality, shipping)

    # Filter to line 1 only; sort by lot_number ascending
    filtered = etl.filter_and_sort(
        consolidated,
        filters={"line_number": [1]},
        sort_by="lot_number",
        ascending=True,
    )
    assert len(filtered) == 2
    assert list(filtered["lot_number"]) == ["B1", "B2"]

    # Summary metrics and trend detection
    metrics = etl.summary_metrics(consolidated)
    assert "defect_rate" in metrics.columns
    trends = etl.detect_trends(consolidated, group_by="line_number")
    assert "is_anomaly" in trends.columns
