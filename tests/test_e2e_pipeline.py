import pandas as pd
from sqlalchemy import text

from src.services import etl
from src.database.connection import Database


def test_full_pipeline():
    """
    End-to-end test of the full data pipeline:
    ETL → database inserts → database queries → analytics.
    """

    db = Database()

    # --- Create mock input data ---
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

    # --- Run ETL pipeline ---
    consolidated = etl.consolidate_data(production, quality, shipping)
    metrics = etl.summary_metrics(consolidated)

    assert len(consolidated) == 2
    assert "defect_rate" in metrics.columns

    # --- Insert data into database ---
    with db.engine.begin() as conn:
        # Reset tables so test runs are repeatable
        conn.execute(text("TRUNCATE shipping_manifests CASCADE"))
        conn.execute(text("TRUNCATE quality_inspections CASCADE"))
        conn.execute(text("TRUNCATE production_logs CASCADE"))

        # Insert production logs
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

        # Insert quality inspection
        conn.execute(
            text("""
                INSERT INTO quality_inspections
                (production_log_id, defect_type, defect_severity, is_defective, inspection_count)
                VALUES (:log_id, 'Scratch', 'Low', TRUE, 1)
            """),
            {"log_id": id_map["A100"]},
        )

        # Insert shipping manifests
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

        # --- Validate database contents ---
        production_count = conn.execute(
            text("SELECT COUNT(*) FROM production_logs")
        ).scalar()

        inspection_count = conn.execute(
            text("SELECT COUNT(*) FROM quality_inspections")
        ).scalar()

        shipping_count = conn.execute(
            text("SELECT COUNT(*) FROM shipping_manifests")
        ).scalar()

    # --- Assertions ---
    assert production_count == 2
    assert inspection_count == 1
    assert shipping_count == 2
