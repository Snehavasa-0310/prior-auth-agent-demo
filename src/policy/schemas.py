"""Pydantic v2 schemas for policy representation, chunking, and criteria extraction."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import AliasChoices, BaseModel, Field


class CriterionType(str, Enum):
    INCLUSION = "INCLUSION"
    EXCLUSION = "EXCLUSION"
    CONSERVATIVE_THERAPY = "CONSERVATIVE_THERAPY"
    DIAGNOSTIC = "DIAGNOSTIC"


class CriterionDefinition(BaseModel):
    id: str = Field(description="Unique criterion identifier, e.g. CRIT-LUMBAR-01")
    title: str = Field(description="Short human-readable title of the criterion")
    criterion_type: CriterionType = Field(description="Category of coverage criterion")
    description: str = Field(description="Clinical condition or rule required by the policy")
    required_evidence_description: str = Field(
        default="",
        validation_alias=AliasChoices("required_evidence_description", "required_evidence"),
        description="Type of documentation expected in clinical notes to satisfy this criterion",
    )
    is_mandatory: bool = Field(
        default=True, description="Whether this criterion must be satisfied for approval"
    )

    class Config:
        populate_by_name = True


class PolicySection(BaseModel):
    title: str
    content: str


class StructuredPolicy(BaseModel):
    id: str
    title: str
    payer: str
    policy_type: str
    policy_number: str | None = None
    procedure_name: str
    cpt_codes: list[str] = Field(default_factory=list)
    icd10_codes: list[str] = Field(default_factory=list)
    effective_date: str
    source_url: str
    summary: str
    sections: list[PolicySection] = Field(default_factory=list)
    criteria: list[CriterionDefinition] = Field(default_factory=list)


class PolicyChunk(BaseModel):
    chunk_id: str
    policy_id: str
    procedure_name: str
    payer: str
    section_title: str
    cpt_codes: list[str] = Field(default_factory=list)
    content: str
    chunk_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class CriteriaExtractionResult(BaseModel):
    policy_id: str
    procedure_name: str
    criteria: list[CriterionDefinition] = Field(min_length=1)
    extracted_at: str
    version: str = "1.0"
