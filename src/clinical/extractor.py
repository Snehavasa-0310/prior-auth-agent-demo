"""Clinical fact extractor preserving verified character offsets."""

from __future__ import annotations

import re

from src.clinical.schemas import (
    ClinicalFact,
    ClinicalFactCategory,
    ClinicalNoteAnalysis,
)
from src.clinical.terminology import TerminologyNormalizer


class ClinicalFactExtractor:
    """Extracts structured clinical facts from raw clinical notes while maintaining offset integrity."""

    def __init__(self, normalizer: TerminologyNormalizer | None = None):
        self.normalizer = normalizer or TerminologyNormalizer()

    def analyze_note(self, text: str) -> ClinicalNoteAnalysis:
        facts: list[ClinicalFact] = []
        fact_idx = 1

        # 1. Durations (e.g. "6 weeks", "8 weeks of formal physical therapy", "10 days", "5 months")
        duration_pattern = re.compile(
            r"\b(\d{1,2}\s+(?:weeks?|wks?|months?|mos?|days?|years?|yrs?))\b", re.IGNORECASE
        )
        for match in duration_pattern.finditer(text):
            start, end = match.span()
            raw_val = text[start:end]
            facts.append(
                ClinicalFact(
                    fact_id=f"FACT-{fact_idx:04d}",
                    category=ClinicalFactCategory.DURATION,
                    raw_text=raw_val,
                    char_start=start,
                    char_end=end,
                    value=match.group(1),
                )
            )
            fact_idx += 1

        # 2. Diagnoses & Clinical Entities
        diag_patterns = [
            (r"(?i)\b(?:radiculopathy|lumbar radiculopathy)\b", "radiculopathy"),
            (r"(?i)\b(?:cauda equina(?:\s+syndrome)?)\b", "cauda equina syndrome"),
            (r"(?i)\b(?:low(?:er)? back pain|lbp)\b", "low back pain"),
            (r"(?i)\b(?:menisc(?:al|us)\s+tear)\b", "meniscal tear"),
            (r"(?i)\b(?:type 2 diabetes(?: mellitus)?|t2d|t2dm)\b", "type 2 diabetes"),
            (r"(?i)\b(?:obstructive sleep apnea|osa)\b", "obstructive sleep apnea"),
            (r"(?i)\b(?:rheumatoid arthritis|ra)\b", "rheumatoid arthritis"),
            (r"(?i)\b(?:morbid obesity|obesity)\b", "morbid obesity"),
        ]
        for pattern, norm_key in diag_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                raw_val = text[start:end]
                norm = self.normalizer.normalize(norm_key)
                facts.append(
                    ClinicalFact(
                        fact_id=f"FACT-{fact_idx:04d}",
                        category=ClinicalFactCategory.DIAGNOSIS,
                        raw_text=raw_val,
                        char_start=start,
                        char_end=end,
                        normalized=norm,
                    )
                )
                fact_idx += 1

        # 3. Medications & Prior Treatments
        med_patterns = [
            (r"(?i)\b(?:metformin(?:\s+\d+\s*mg)?(?:\s+(?:bid|tid|daily))?)\b", "metformin"),
            (r"(?i)\b(?:semaglutide|ozempic|wegovy)\b", "semaglutide"),
            (r"(?i)\b(?:dulaglutide|trulicity)\b", "dulaglutide"),
            (r"(?i)\b(?:methotrexate|mtx)\b", "methotrexate"),
            (r"(?i)\b(?:adalimumab|humira)\b", "adalimumab"),
            (r"(?i)\b(?:meloxicam|naproxen|ibuprofen|celecoxib|nsaids?)\b", "nsaids"),
            (r"(?i)\b(?:leflunomide|sulfasalazine)\b", "csdmard"),
            (r"(?i)\b(?:physical therapy|pt(?:\s+sessions?)?|physiotherapy)\b", "physical therapy"),
            (r"(?i)\b(?:intra-articular (?:cortisone|steroid) injection|cortisone injection)\b", "steroid injection"),
            (r"(?i)\b(?:weight management program|medical weight loss)\b", "medical weight loss"),
        ]
        for pattern, norm_key in med_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                raw_val = text[start:end]
                norm = self.normalizer.normalize(norm_key)
                cat = ClinicalFactCategory.MEDICATION if norm and norm.code_system == "RxNorm" else ClinicalFactCategory.PRIOR_TREATMENT
                facts.append(
                    ClinicalFact(
                        fact_id=f"FACT-{fact_idx:04d}",
                        category=cat,
                        raw_text=raw_val,
                        char_start=start,
                        char_end=end,
                        normalized=norm,
                    )
                )
                fact_idx += 1

        # 4. Lab Values & Diagnostic Metrics
        lab_patterns = [
            (r"(?i)\b(?:hba1c|a1c)[:\s]*(\d{1,2}(?:\.\d{1,2})?)\s*%", "HbA1c", "%"),
            (r"(?i)\b(?:ahi|apnea-hypopnea index)[:\s]*(\d{1,2}(?:\.\d{1,2})?)\s*(?:events?/hr|events?/hour)?\b", "AHI", "events/hr"),
            (r"(?i)\b(?:bmi|body mass index)[:\s]*(\d{1,2}(?:\.\d{1,2})?)\s*(?:kg/m2)?\b", "BMI", "kg/m2"),
            (r"(?i)\b(?:epworth sleepiness scale|ess)(?:[:\s]*score)?[:\s]*(\d{1,2})\s*(?:/\s*24)?\b", "ESS", "score"),
            (r"(?i)\b(?:crp)[:\s]*(\d{1,2}(?:\.\d{1,2})?)\s*(?:mg/l)?\b", "CRP", "mg/L"),
            (r"(?i)\b(?:quantiferon(?:-tb)? gold|ppd)[:\s]*(?:was\s+)?(negative|positive)\b", "TB_SCREENING", "status"),
        ]
        for pattern, metric_name, unit in lab_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                raw_val = text[start:end]
                val = match.group(1)
                facts.append(
                    ClinicalFact(
                        fact_id=f"FACT-{fact_idx:04d}",
                        category=ClinicalFactCategory.LAB_VALUE,
                        raw_text=raw_val,
                        char_start=start,
                        char_end=end,
                        value=val,
                        unit=unit,
                        metadata={"metric": metric_name},
                    )
                )
                fact_idx += 1

        # 5. Physical Exam Findings
        pe_patterns = [
            r"(?i)\b(?:straight leg raise|slr(?:\s*\+)?)",
            r"(?i)\b(?:saddle anesthesia)",
            r"(?i)\b(?:mcmurray(?:\s+(?:click|sign|test))?)",
            r"(?i)\b(?:joint line tenderness|jlt)",
            r"(?i)\b(?:foot drop)",
            r"(?i)\b(?:urinary incontinence|bowel/bladder)",
            r"(?i)\b(?:locking|catching|giving way)",
        ]
        for pattern in pe_patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                raw_val = text[start:end]
                facts.append(
                    ClinicalFact(
                        fact_id=f"FACT-{fact_idx:04d}",
                        category=ClinicalFactCategory.PHYSICAL_EXAM,
                        raw_text=raw_val,
                        char_start=start,
                        char_end=end,
                    )
                )
                fact_idx += 1

        # 6. Verify Substring Invariant for EVERY fact extracted
        for f in facts:
            assert text[f.char_start : f.char_end] == f.raw_text, (
                f"Offset mismatch for {f.fact_id}: '{text[f.char_start:f.char_end]}' != '{f.raw_text}'"
            )

        return ClinicalNoteAnalysis(note_length=len(text), facts=facts)
