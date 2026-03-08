"""ORM models for the production quality system.

This module defines SQLAlchemy ORM models that mirror the database schema in
`db/schema.sql`. Each model class is documented with its purpose and
important invariants.

Time complexity for model definitions: O(1). These are static class
definitions and do not allocate significant runtime resources beyond class
objects.
Space complexity: O(1) per model class.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class ProductionLog(Base):
    """Represents a manufacturing production log (lot).

    Attributes map to the `production_logs` table.

    Notes:
        - `production_log_id` is the surrogate primary key.
        - `lot_number` is a unique business identifier.
    """

    __tablename__ = "production_logs"

    production_log_id = Column(Integer, primary_key=True, index=True)
    lot_number = Column(String(50), nullable=False, unique=True)
    line_number = Column(Integer, nullable=False)
    production_date = Column(Date, nullable=False, default=datetime.utcnow)
    shift_leader = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Relationship references: one ProductionLog can have many QualityInspections
    # and one ShippingManifest (1:1). Using `relationship` allows SQLAlchemy to
    # load related objects conveniently when needed.
    inspections = relationship("QualityInspection", back_populates="production_log", cascade="all, delete-orphan")
    shipping_manifest = relationship("ShippingManifest", back_populates="production_log", uselist=False, cascade="all, delete-orphan")


class QualityInspection(Base):
    """Represents individual quality inspections related to a production log.

    Columns and constraints are designed to follow `db/schema.sql`. The
    `production_log_id` foreign key enforces referential integrity.
    """

    __tablename__ = "quality_inspections"

    quality_inspection_id = Column(Integer, primary_key=True, index=True)
    production_log_id = Column(Integer, ForeignKey("production_logs.production_log_id", ondelete="CASCADE"), nullable=False)
    defect_type = Column(String(100), nullable=True)
    defect_severity = Column(String(20), nullable=True)
    is_defective = Column(Boolean, nullable=False, default=False)
    inspection_count = Column(Integer, nullable=False, default=0)
    inspected_at = Column(TIMESTAMP(timezone=True), nullable=False)

    # Relationship back to production log for convenient access.
    production_log = relationship("ProductionLog", back_populates="inspections")


class ShippingManifest(Base):
    """Represents shipping information for a production log (1:1 relation).

    The `production_log_id` column is unique to ensure one shipping manifest
    per production log.
    """

    __tablename__ = "shipping_manifests"

    shipping_manifest_id = Column(Integer, primary_key=True, index=True)
    production_log_id = Column(Integer, ForeignKey("production_logs.production_log_id", ondelete="CASCADE"), nullable=False, unique=True)
    ship_date = Column(Date, nullable=True)
    destination = Column(String(255), nullable=False)
    is_shipped = Column(Boolean, nullable=False, default=False)
    is_cancelled = Column(Boolean, nullable=False, default=False)

    production_log = relationship("ProductionLog", back_populates="shipping_manifest")
