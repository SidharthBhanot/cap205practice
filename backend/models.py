from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey,
    Integer, JSON, String, Table, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base, utcnow


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    code = Column(String(30), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    obligations = relationship("Obligation", back_populates="course", passive_deletes=True)


class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    source_type = Column(String(30), nullable=False)
    description = Column(Text, default="", nullable=False)
    reference_url = Column(String(2048))
    recorded_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    last_checked_at = Column(DateTime)
    obligations = relationship("Obligation", back_populates="source", passive_deletes=True)
    __table_args__ = {"sqlite_autoincrement": True}


class Obligation(Base):
    __tablename__ = "obligations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="RESTRICT"), index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(240), default="", nullable=False)
    description = Column(Text, default="", nullable=False)
    obligation_type = Column(String(30))
    deadline = Column(Date, index=True)
    status = Column(String(30), default="Planned", nullable=False, index=True)
    reference_url = Column(String(2048))
    recorded_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    course = relationship("Course", back_populates="obligations")
    source = relationship("Source", back_populates="obligations")
    __table_args__ = {"sqlite_autoincrement": True}


conflict_obligations = Table(
    "conflict_obligations", Base.metadata,
    Column("conflict_id", ForeignKey("conflicts.id", ondelete="CASCADE"), primary_key=True),
    Column("obligation_id", ForeignKey("obligations.id", ondelete="CASCADE"), primary_key=True),
)


class Conflict(Base):
    __tablename__ = "conflicts"
    id = Column(Integer, primary_key=True)
    fingerprint = Column(String(180), nullable=False, unique=True)
    conflict_type = Column(String(40), nullable=False, index=True)
    explanation = Column(Text, nullable=False)
    record_ids = Column(JSON, nullable=False)
    source_records = Column(JSON, nullable=False)
    evidence_hash = Column(String(64), nullable=False)
    detected_at = Column(DateTime, default=utcnow, nullable=False)
    last_detected_at = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String(30), default="Needs Verification", nullable=False, index=True)
    resolution_notes = Column(Text, default="", nullable=False)
    reviewed_at = Column(DateTime)
    reviewed_evidence_hash = Column(String(64))
    evidence_changed = Column(Boolean, default=False, nullable=False)
    is_current = Column(Boolean, default=True, nullable=False)
    obligations = relationship("Obligation", secondary=conflict_obligations)
    __table_args__ = (
        CheckConstraint("status IN ('Needs Verification','Under Review','Resolved','Dismissed')"),
    )


class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"
    id = Column(Integer, primary_key=True)
    obligation_a_id = Column(Integer, ForeignKey("obligations.id", ondelete="SET NULL"))
    obligation_b_id = Column(Integer, ForeignKey("obligations.id", ondelete="SET NULL"))
    pair_key = Column(String(80), unique=True, nullable=False)
    classification = Column(String(30), nullable=False, index=True)
    title_similarity = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    source_records = Column(JSON, nullable=False)
    conflict_ids = Column(JSON, default=list, nullable=False)
    compared_at = Column(DateTime, default=utcnow, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="SET NULL"), index=True)
    __table_args__ = (UniqueConstraint("obligation_a_id", "obligation_b_id"),)


class AppState(Base):
    __tablename__ = "app_state"
    id = Column(Integer, primary_key=True)
    data_revision = Column(Integer, default=0, nullable=False)
    reconciled_revision = Column(Integer, default=-1, nullable=False)
    last_reconciled_at = Column(DateTime)
    last_config = Column(JSON)
    run_summary = Column(JSON, default=dict, nullable=False)
    synthetic_data = Column(Boolean, default=False, nullable=False)
