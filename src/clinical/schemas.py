"""Pydantic v2 schemas for clinical fact extraction and terminology mapping."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ClinicalFactCategory(str, Enum):
    DIAGNOSIS = "DIAGNOSIS"
    SYMPTOM = "SYMPTOM"
    DURATION = "DURATION"
    PRIOR_TREATMENT = "PRIOR_TREATMENT"
    MEDICATION = "MEDICATION"
    IMAGING = "IMAGING"
    LAB_VALUE = "LAB_VALUE"
    PHYSICAL_EXAM = "PHYSICAL_EXAM"
    DATE = "DATE"


class NormalizedConcept(BaseModel):
    code: str
    code_system: str = Field(description="e.g. ICD-10-CM, RxNorm, CPT, LOINC")
    display_name: str
    confidence: float = 1.0


class ClinicalFact(BaseModel):
    fact_id: str
    category: ClinicalFactCategory
    raw_text: str = Field(description="Exact substring from the original note")
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    normalized: NormalizedConcept | None = None
    value: str | None = None
    unit: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClinicalNoteAnalysis(BaseModel):
    note_length: int
    facts: list[ClinicalFact] = Field(default_factory=list)

    @property
    def diagnoses(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.DIAGNOSIS]

    @property
    def treatments(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.PRIOR_TREATMENT]

    @property
    def medications(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.MEDICATION]

    @property
    def labs(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.LAB_VALUE]

    @property
    def imaging(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.IMAGING]

    @property
    def durations(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.DURATION]

    @property
    def physical_exam(self) -> list[ClinicalFact]:
        return [f for f in self.facts if f.category == ClinicalFactCategory.PHYSICAL_EXAM]
