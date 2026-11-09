"""Pydantic v2 schemas for agent state, criteria evaluation, decisions, and audit events."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CriterionStatus(str, Enum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    INSUFFICIENT_INFO = "INSUFFICIENT_INFO"


class OverallRecommendation(str, Enum):
    LIKELY_APPROVABLE = "LIKELY_APPROVABLE"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    LIKELY_DENIED = "LIKELY_DENIED"


class CaseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED_BY_REVIEWER = "APPROVED_BY_REVIEWER"
    REJECTED = "REJECTED"


class CriterionEvaluation(BaseModel):
    criterion_id: str
    criterion_title: str
    status: CriterionStatus
    evidence_quote: str = Field(default="", description="Exact substring from original note")
    char_start: int | None = None
    char_end: int | None = None
    is_verified_substring: bool = False
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    missing_elements: str | None = None


class AuditEvent(BaseModel):
    step_name: str
    tool_name: str | None = None
    input_summary: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float
    model_name: str
    timestamp: str


class PriorAuthDecision(BaseModel):
    policy_id: str
    procedure_name: str
    procedure_code: str
    payer: str
    overall_recommendation: OverallRecommendation
    confidence_score: float = Field(ge=0.0, le=1.0)
    criteria_results: list[CriterionEvaluation] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    draft_letter: str = ""
    audit_trail: list[AuditEvent] = Field(default_factory=list)
