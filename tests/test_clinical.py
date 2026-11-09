"""Tests for Clinical Fact Extraction and Terminology Normalization."""

from src.clinical.extractor import ClinicalFactExtractor
from src.clinical.terminology import TerminologyNormalizer


def test_terminology_normalizer():
    norm = TerminologyNormalizer()

    c1 = norm.normalize("lumbar radiculopathy")
    assert c1 is not None
    assert c1.code == "M54.16"
    assert c1.code_system == "ICD-10-CM"

    c2 = norm.normalize("metformin 1000mg")
    assert c2 is not None
    assert c2.code == "6809"
    assert c2.code_system == "RxNorm"

    c3 = norm.normalize("Humira 40mg injection")
    assert c3 is not None
    assert c3.code == "327361"
    assert c3.code_system == "RxNorm"


def test_clinical_fact_extractor_offsets():
    extractor = ClinicalFactExtractor()
    note = (
        "Patient is a 54yo M with severe lumbar radiculopathy lasting 8 weeks. "
        "Completed 6 weeks of physical therapy and took meloxicam 15mg daily without relief. "
        "Exam shows positive straight leg raise at 35 degrees. Lab: HbA1c: 8.6%."
    )

    analysis = extractor.analyze_note(note)
    assert analysis.note_length == len(note)
    assert len(analysis.facts) >= 6

    # Verify character offsets
    for fact in analysis.facts:
        assert note[fact.char_start : fact.char_end] == fact.raw_text

    # Verify categories
    durations = [f.raw_text for f in analysis.durations]
    assert any("8 weeks" in d for d in durations)
    assert any("6 weeks" in d for d in durations)

    labs = analysis.labs
    assert len(labs) >= 1
    assert labs[0].value == "8.6"

    pe = analysis.physical_exam
    assert any("straight leg raise" in p.raw_text for p in pe)
