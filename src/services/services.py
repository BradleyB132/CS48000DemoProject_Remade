"""Service layer providing business logic and CRUD operations.

This module implements functions that operate on the ORM models using the
`Database` connection. All functions use the `Database.get_session()` context
manager to ensure sessions are cleaned up and to prevent connection leaks.

The service layer decouples UI code from direct database access, which helps
unit testing and maintains the project's layered architecture.

Time and space complexity notes are provided per function.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.database.connection import default_db
from src.models.models import ProductionLog, QualityInspection

logger = logging.getLogger(__name__)


def list_production_logs(limit: int = 100) -> List[ProductionLog]:
    """Return up to `limit` production logs ordered by production_date desc.

    Time complexity: O(n) where n is `limit` (due to fetching rows).
    Space complexity: O(n) to hold returned ORM objects.
    """
    with default_db.get_session() as session:
        # Eager-load related objects to avoid DetachedInstanceError when the
        # session is closed. `selectinload` performs a second query to fetch
        # relationships efficiently for multiple parent rows.
        stmt = (
            select(ProductionLog)
            .options(
                selectinload(ProductionLog.shipping_manifest),
                selectinload(ProductionLog.inspections),
            )
            .order_by(ProductionLog.production_date.desc())
            .limit(limit)
        )
        result = session.execute(stmt).scalars().all()
        logger.debug(
            "list_production_logs: limit=%d, returned %d rows", limit, len(result)
        )
        return result


def get_production_log_by_id(production_log_id: int) -> Optional[ProductionLog]:
    """Fetch a single ProductionLog by its primary key.

    Time complexity: O(1) for the indexed primary key lookup.
    Space complexity: O(1).
    """
    with default_db.get_session() as session:
        # Use a select with eager loading to fetch related objects while the
        # session is open. This prevents later attribute access from trying to
        # lazy-load on a closed session.
        stmt = (
            select(ProductionLog)
            .options(
                selectinload(ProductionLog.shipping_manifest),
                selectinload(ProductionLog.inspections),
            )
            .where(ProductionLog.production_log_id == production_log_id)
        )
        log = session.execute(stmt).scalars().one_or_none()
        logger.debug(
            "get_production_log_by_id: id=%s, found=%s",
            production_log_id,
            log is not None,
        )
        return log


def create_production_log(
    lot_number: str, line_number: int, production_date, shift_leader: str
) -> ProductionLog:
    """Create and persist a new ProductionLog.

    Time complexity: O(1).
    Space complexity: O(1).
    """
    new_log = ProductionLog(
        lot_number=lot_number,
        line_number=line_number,
        production_date=production_date,
        shift_leader=shift_leader,
        created_at=None,  # rely on DB default if available
    )
    with default_db.get_session() as session:
        session.add(new_log)
        # flush to populate PK without committing if the database assigns it
        session.flush()
        session.refresh(new_log)
        logger.info(
            "create_production_log: created lot_number=%s, production_log_id=%s",
            lot_number,
            new_log.production_log_id,
        )
        return new_log


def list_inspections_for_log(production_log_id: int) -> List[QualityInspection]:
    """List inspections associated with a production log.

    Time complexity: O(m) where m is number of inspections for the log.
    Space complexity: O(m).
    """
    with default_db.get_session() as session:
        stmt = select(QualityInspection).where(
            QualityInspection.production_log_id == production_log_id
        )
        result = session.execute(stmt).scalars().all()
        logger.debug(
            "list_inspections_for_log: production_log_id=%s, count=%d",
            production_log_id,
            len(result),
        )
        return result
