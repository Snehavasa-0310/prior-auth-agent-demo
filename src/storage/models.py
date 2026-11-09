"""SQLAlchemy database models for cases, criteria evaluations, and audit logs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CaseModel(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id: Mapped[str] = mapped_column(String(64), default="SYNTH-UNKNOWN")
    procedure_name: Mapped[str] = mapped_column(String(255))
    procedure_code: Mapped[str] = mapped_column(String(32))
    payer: Mapped[str] = mapped_column(String(128))
    policy_id: Mapped[str] = mapped_column(String(128), default="")
    raw_clinical_note: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="SUBMITTED")
    overall_recommendation: Mapped[str] = mapped_column(String(32), default="NEEDS_MORE_INFO")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    draft_letter: Mapped[str] = mapped_column(Text, default="")
    reviewer_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    criteria_results = relationship("CaseCriterionResultModel", back_populates="case", cascade="all, delete-orphan")
    audit_events = relationship("AuditEventModel", back_populates="case", cascade="all, delete-orphan")


class CaseCriterionResultModel(Base):
    __tablename__ = "case_criterion_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.id"), nullable=False)
    criterion_id: Mapped[str] = mapped_column(String(64))
    criterion_title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32))
    evidence_quote: Mapped[str] = mapped_column(Text, default="")
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified_substring: Mapped[bool] = mapped_column(Boolean, default=False)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    case = relationship("CaseModel", back_populates="criteria_results")


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.id"), nullable=False)
    step_name: Mapped[str] = mapped_column(String(64))
    tool_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    input_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    output_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    model_name: Mapped[str] = mapped_column(String(64), default="agent-v1")
    timestamp: Mapped[str] = mapped_column(String(64))

    case = relationship("CaseModel", back_populates="audit_events")
