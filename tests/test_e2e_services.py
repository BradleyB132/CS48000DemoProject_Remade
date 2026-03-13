"""
End-to-end tests for the service layer: database → services → API used by the dashboard.

These tests verify that the application’s service layer (list_production_logs,
get_production_log_by_id, list_inspections_for_log, create_production_log) works
correctly against the real test database. They seed the DB, call the services,
and assert on returned ORM objects and relationships.

This is the E2E path that the Streamlit dashboard uses: no UI, but full stack
from DB to in-memory objects the UI consumes.

Run with: pytest tests/test_e2e_services.py -v
"""

from datetime import date
from sqlalchemy import text

from src.database.connection import Database
from src.services import services


def _truncate_tables(conn):
    """
    Truncate all tables in FK-safe order so tests start from a clean state.
    """
    conn.execute(text("TRUNCATE shipping_manifests CASCADE"))
    conn.execute(text("TRUNCATE quality_inspections CASCADE"))
    conn.execute(text("TRUNCATE production_logs CASCADE"))


def _seed_production_and_related(db, id_map):
    """
    Insert one production log, one quality inspection, and one shipping manifest.

    Uses raw SQL to control exact IDs and avoid ORM side effects. Populates
    id_map with lot_number -> production_log_id for use in assertions.
    """
    with db.engine.begin() as conn:
        _truncate_tables(conn)
        result = conn.execute(
            text("""
                INSERT INTO production_logs
                (lot_number, line_number, production_date, shift_leader, created_at)
                VALUES
                ('LOT-E2E-1', 1, '2024-03-01', 'Leader A', NOW())
                RETURNING production_log_id, lot_number
            """)
        )
        row = result.fetchone()
        log_id = row.production_log_id
        id_map[row.lot_number] = log_id

        conn.execute(
            text("""
                INSERT INTO quality_inspections
                (production_log_id, defect_type, defect_severity, is_defective, inspection_count, inspected_at)
                VALUES (:log_id, 'Scratch', 'Medium', TRUE, 1, NOW())
            """),
            {"log_id": log_id},
        )
        conn.execute(
            text("""
                INSERT INTO shipping_manifests
                (production_log_id, ship_date, destination, is_shipped, is_cancelled)
                VALUES (:log_id, '2024-03-02', 'Chicago', TRUE, FALSE)
            """),
            {"log_id": log_id},
        )


def test_e2e_list_production_logs_returns_eager_loaded_relations():
    """
    E2E: list_production_logs returns logs with shipping_manifest and inspections
    eager-loaded so the dashboard can render without extra queries.

    We seed one log with one inspection and one shipping manifest, then call
    list_production_logs and assert on counts and attribute access. Detached
    session access (after the context manager exits) must not raise because
    relationships were selectinload-ed.
    """
    db = Database()
    id_map = {}
    _seed_production_and_related(db, id_map)

    logs = services.list_production_logs(limit=100)

    assert len(logs) >= 1
    log = next(log_ for log_ in logs if log_.lot_number == "LOT-E2E-1")
    assert log.line_number == 1
    assert log.shift_leader == "Leader A"
    assert log.production_date == date(2024, 3, 1)

    # Eager-loaded: no DetachedInstanceError when session is closed
    assert log.shipping_manifest is not None
    assert log.shipping_manifest.destination == "Chicago"
    assert log.shipping_manifest.is_shipped is True

    assert log.inspections is not None
    assert len(log.inspections) == 1
    assert log.inspections[0].defect_type == "Scratch"
    assert log.inspections[0].is_defective is True


def test_e2e_get_production_log_by_id_and_list_inspections():
    """
    E2E: get_production_log_by_id returns a single log with relations;
    list_inspections_for_log returns that log’s inspections.

    This mirrors the dashboard flow when the user selects a row and we show
    detail (production log + shipping) and then list inspections for that log.
    """
    db = Database()
    id_map = {}
    _seed_production_and_related(db, id_map)
    log_id = id_map["LOT-E2E-1"]

    detail = services.get_production_log_by_id(log_id)

    assert detail is not None
    assert detail.lot_number == "LOT-E2E-1"
    assert detail.shipping_manifest is not None
    assert detail.shipping_manifest.destination == "Chicago"

    inspections = services.list_inspections_for_log(log_id)
    assert len(inspections) == 1
    assert inspections[0].defect_type == "Scratch"
    assert inspections[0].defect_severity == "Medium"


def test_e2e_get_production_log_by_id_missing_returns_none():
    """
    E2E: get_production_log_by_id returns None when the ID does not exist.

    Ensures the service layer does not raise and the dashboard can handle
    “row not found” (e.g. deleted or invalid selection).
    """
    result = services.get_production_log_by_id(999999)
    assert result is None


def test_e2e_create_production_log_persists_and_is_listed():
    """
    E2E: create_production_log persists a new log and it appears in list_production_logs.

    Creates a log via the service, then fetches the list and verifies the new
    lot_number and attributes are present. Table is truncated first so we can
    rely on a small result set.
    """
    db = Database()
    with db.engine.begin() as conn:
        _truncate_tables(conn)

    new_log = services.create_production_log(
        lot_number="LOT-CREATE-E2E",
        line_number=2,
        production_date=date(2024, 3, 10),
        shift_leader="Leader B",
    )

    assert new_log is not None
    assert new_log.production_log_id is not None
    assert new_log.lot_number == "LOT-CREATE-E2E"

    logs = services.list_production_logs(limit=100)
    found = next((log_ for log_ in logs if log_.lot_number == "LOT-CREATE-E2E"), None)
    assert found is not None
    assert found.production_log_id == new_log.production_log_id
    assert found.line_number == 2
