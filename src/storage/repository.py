"""Database repository handling cases, evaluations, and audit logs."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from src.agent.schemas import CaseStatus, PriorAuthDecision
from src.storage.models import AuditEventModel, Base, CaseCriterionResultModel, CaseModel


class CaseRepository:
    """Repository managing persistence of Prior Authorization cases and audit logs."""

    def __init__(self, db_url: str | None = None):
        self.db_url: str = db_url or os.getenv("DATABASE_URL") or "sqlite:///prior_auth.db"
        # Ensure SQLite works smoothly in multithreaded / FastAPI contexts
        connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.db_url, connect_args=connect_args)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()

    def init_db(self) -> None:
        """Create tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)

    def create_case(
        self,
        case_id: str,
        procedure_name: str,
        procedure_code: str,
        payer: str,
        raw_clinical_note: str,
        patient_id: str = "SYNTH-PATIENT",
    ) -> CaseModel:
        with self.SessionLocal() as session:
            case = CaseModel(
                id=case_id,
                patient_id=patient_id,
                procedure_name=procedure_name,
                procedure_code=procedure_code,
                payer=payer,
                raw_clinical_note=raw_clinical_note,
                status=CaseStatus.SUBMITTED.value,
            )
            session.add(case)
            session.commit()
            session.refresh(case)
            return case

    def save_decision(self, case_id: str, decision: PriorAuthDecision) -> CaseModel:
        with self.SessionLocal() as session:
            case = session.execute(select(CaseModel).where(CaseModel.id == case_id)).scalar_one_or_none()
            if not case:
                raise ValueError(f"Case with ID {case_id} not found.")

            case.policy_id = decision.policy_id
            case.status = CaseStatus.ANALYZED.value
            case.overall_recommendation = decision.overall_recommendation.value
            case.confidence_score = decision.confidence_score
            case.draft_letter = decision.draft_letter
            case.updated_at = datetime.now(UTC)

            # Store Criteria Evaluations
            for crit in decision.criteria_results:
                crit_row = CaseCriterionResultModel(
                    case_id=case_id,
                    criterion_id=crit.criterion_id,
                    criterion_title=crit.criterion_title,
                    status=crit.status.value,
                    evidence_quote=crit.evidence_quote,
                    char_start=crit.char_start,
                    char_end=crit.char_end,
                    is_verified_substring=crit.is_verified_substring,
                    reasoning=crit.reasoning,
                    confidence=crit.confidence,
                )
                session.add(crit_row)

            # Store Audit Events
            for event in decision.audit_trail:
                audit_row = AuditEventModel(
                    case_id=case_id,
                    step_name=event.step_name,
                    tool_name=event.tool_name,
                    input_summary=event.input_summary,
                    output_summary=event.output_summary,
                    latency_ms=event.latency_ms,
                    model_name=event.model_name,
                    timestamp=event.timestamp,
                )
                session.add(audit_row)

            session.commit()
            session.refresh(case)
            return case

    def get_case(self, case_id: str) -> dict[str, Any] | None:
        with self.SessionLocal() as session:
            case = session.execute(select(CaseModel).where(CaseModel.id == case_id)).scalar_one_or_none()
            if not case:
                return None

            crit_rows = session.execute(
                select(CaseCriterionResultModel).where(CaseCriterionResultModel.case_id == case_id)
            ).scalars().all()

            audit_rows = session.execute(
                select(AuditEventModel).where(AuditEventModel.case_id == case_id)
            ).scalars().all()

            return {
                "id": case.id,
                "patient_id": case.patient_id,
                "procedure_name": case.procedure_name,
                "procedure_code": case.procedure_code,
                "payer": case.payer,
                "policy_id": case.policy_id,
                "raw_clinical_note": case.raw_clinical_note,
                "status": case.status,
                "overall_recommendation": case.overall_recommendation,
                "confidence_score": case.confidence_score,
                "draft_letter": case.draft_letter,
                "reviewer_notes": case.reviewer_notes,
                "created_at": case.created_at.isoformat() if case.created_at else None,
                "criteria_results": [
                    {
                        "criterion_id": c.criterion_id,
                        "criterion_title": c.criterion_title,
                        "status": c.status,
                        "evidence_quote": c.evidence_quote,
                        "char_start": c.char_start,
                        "char_end": c.char_end,
                        "is_verified_substring": c.is_verified_substring,
                        "reasoning": c.reasoning,
                        "confidence": c.confidence,
                    }
                    for c in crit_rows
                ],
                "audit_trail": [
                    {
                        "step_name": a.step_name,
                        "tool_name": a.tool_name,
                        "input_summary": a.input_summary,
                        "output_summary": a.output_summary,
                        "latency_ms": a.latency_ms,
                        "model_name": a.model_name,
                        "timestamp": a.timestamp,
                    }
                    for a in audit_rows
                ],
            }

    def list_cases(self, limit: int = 50) -> list[dict[str, Any]]:
        with self.SessionLocal() as session:
            cases = session.execute(
                select(CaseModel).order_by(CaseModel.created_at.desc()).limit(limit)
            ).scalars().all()

            return [
                {
                    "id": c.id,
                    "patient_id": c.patient_id,
                    "procedure_name": c.procedure_name,
                    "procedure_code": c.procedure_code,
                    "payer": c.payer,
                    "status": c.status,
                    "overall_recommendation": c.overall_recommendation,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in cases
            ]

    def update_reviewer_action(
        self,
        case_id: str,
        action: str,  # "APPROVE", "REJECT", "REQUEST_INFO"
        reviewer_notes: str,
        edited_letter: str | None = None,
    ) -> dict[str, Any]:
        with self.SessionLocal() as session:
            case = session.execute(select(CaseModel).where(CaseModel.id == case_id)).scalar_one_or_none()
            if not case:
                raise ValueError(f"Case {case_id} not found.")

            if action == "APPROVE":
                case.status = CaseStatus.APPROVED_BY_REVIEWER.value
            elif action == "REJECT":
                case.status = CaseStatus.REJECTED.value
            else:
                case.status = CaseStatus.UNDER_REVIEW.value

            case.reviewer_notes = reviewer_notes
            if edited_letter:
                case.draft_letter = edited_letter

            # Add human review audit event
            audit_row = AuditEventModel(
                case_id=case_id,
                step_name="HUMAN_REVIEW",
                tool_name="reviewer_action",
                input_summary={"action": action},
                output_summary={"final_status": case.status, "has_notes": bool(reviewer_notes)},
                latency_ms=0.0,
                model_name="human-reviewer",
                timestamp=datetime.now(UTC).isoformat(),
            )
            session.add(audit_row)

            session.commit()
            return self.get_case(case_id)  # type: ignore
