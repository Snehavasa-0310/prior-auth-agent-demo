"""Public terminology normalizer for ICD-10-CM and RxNorm."""

from __future__ import annotations

import re

from src.clinical.schemas import NormalizedConcept

# Public ICD-10-CM reference mapping
ICD10_MAP: dict[str, NormalizedConcept] = {
    "lumbar radiculopathy": NormalizedConcept(code="M54.16", code_system="ICD-10-CM", display_name="Radiculopathy, lumbar region"),
    "radiculopathy": NormalizedConcept(code="M54.16", code_system="ICD-10-CM", display_name="Radiculopathy, lumbar region"),
    "low back pain": NormalizedConcept(code="M54.50", code_system="ICD-10-CM", display_name="Low back pain, unspecified"),
    "lumbago": NormalizedConcept(code="M54.50", code_system="ICD-10-CM", display_name="Low back pain, unspecified"),
    "lbp": NormalizedConcept(code="M54.50", code_system="ICD-10-CM", display_name="Low back pain, unspecified"),
    "cauda equina": NormalizedConcept(code="G83.4", code_system="ICD-10-CM", display_name="Cauda equina syndrome"),
    "cauda equina syndrome": NormalizedConcept(code="G83.4", code_system="ICD-10-CM", display_name="Cauda equina syndrome"),
    "meniscal tear": NormalizedConcept(code="M23.22", code_system="ICD-10-CM", display_name="Derangement of meniscus due to old tear, medial meniscus"),
    "meniscus tear": NormalizedConcept(code="M23.22", code_system="ICD-10-CM", display_name="Derangement of meniscus due to old tear, medial meniscus"),
    "type 2 diabetes": NormalizedConcept(code="E11.9", code_system="ICD-10-CM", display_name="Type 2 diabetes mellitus without complications"),
    "t2d": NormalizedConcept(code="E11.9", code_system="ICD-10-CM", display_name="Type 2 diabetes mellitus without complications"),
    "t2dm": NormalizedConcept(code="E11.9", code_system="ICD-10-CM", display_name="Type 2 diabetes mellitus without complications"),
    "obstructive sleep apnea": NormalizedConcept(code="G47.33", code_system="ICD-10-CM", display_name="Obstructive sleep apnea (adult)"),
    "osa": NormalizedConcept(code="G47.33", code_system="ICD-10-CM", display_name="Obstructive sleep apnea (adult)"),
    "rheumatoid arthritis": NormalizedConcept(code="M05.79", code_system="ICD-10-CM", display_name="Rheumatoid arthritis with rheumatoid factor, multiple sites"),
    "ra": NormalizedConcept(code="M06.9", code_system="ICD-10-CM", display_name="Rheumatoid arthritis, unspecified"),
    "morbid obesity": NormalizedConcept(code="E66.01", code_system="ICD-10-CM", display_name="Morbid (severe) obesity due to excess calories"),
    "obesity": NormalizedConcept(code="E66.9", code_system="ICD-10-CM", display_name="Obesity, unspecified"),
}

# Public RxNorm reference mapping
RXNORM_MAP: dict[str, NormalizedConcept] = {
    "metformin": NormalizedConcept(code="6809", code_system="RxNorm", display_name="Metformin"),
    "semaglutide": NormalizedConcept(code="1999557", code_system="RxNorm", display_name="Semaglutide"),
    "ozempic": NormalizedConcept(code="1999557", code_system="RxNorm", display_name="Semaglutide (Ozempic)"),
    "wegovy": NormalizedConcept(code="1999557", code_system="RxNorm", display_name="Semaglutide (Wegovy)"),
    "dulaglutide": NormalizedConcept(code="1551291", code_system="RxNorm", display_name="Dulaglutide"),
    "trulicity": NormalizedConcept(code="1551291", code_system="RxNorm", display_name="Dulaglutide (Trulicity)"),
    "methotrexate": NormalizedConcept(code="6851", code_system="RxNorm", display_name="Methotrexate"),
    "mtx": NormalizedConcept(code="6851", code_system="RxNorm", display_name="Methotrexate"),
    "adalimumab": NormalizedConcept(code="327361", code_system="RxNorm", display_name="Adalimumab"),
    "humira": NormalizedConcept(code="327361", code_system="RxNorm", display_name="Adalimumab (Humira)"),
    "meloxicam": NormalizedConcept(code="214199", code_system="RxNorm", display_name="Meloxicam"),
    "naproxen": NormalizedConcept(code="7258", code_system="RxNorm", display_name="Naproxen"),
    "ibuprofen": NormalizedConcept(code="5640", code_system="RxNorm", display_name="Ibuprofen"),
    "leflunomide": NormalizedConcept(code="236780", code_system="RxNorm", display_name="Leflunomide"),
    "sitagliptin": NormalizedConcept(code="593411", code_system="RxNorm", display_name="Sitagliptin"),
    "linagliptin": NormalizedConcept(code="1114195", code_system="RxNorm", display_name="Linagliptin"),
}


class TerminologyNormalizer:
    """Normalizes clinical terms, medications, and diagnoses to standard code systems."""

    def normalize(self, term: str) -> NormalizedConcept | None:
        cleaned = re.sub(r"[^\w\s-]", "", term.strip().lower())

        # Exact match
        if cleaned in ICD10_MAP:
            return ICD10_MAP[cleaned]
        if cleaned in RXNORM_MAP:
            return RXNORM_MAP[cleaned]

        # Substring search
        for key, concept in RXNORM_MAP.items():
            if re.search(rf"\b{re.escape(key)}\b", cleaned):
                return concept

        for key, concept in ICD10_MAP.items():
            if re.search(rf"\b{re.escape(key)}\b", cleaned):
                return concept

        return None
