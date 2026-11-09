"""Tests for QuoteVerifier and Hard Substring Invariant."""

from src.agent.schemas import CriterionEvaluation, CriterionStatus
from src.agent.verifier import QuoteVerifier


def test_quote_verifier_exact_substring():
    note = (
        "Patient completed 8 weeks of formal physical therapy with no relief. "
        "Exam reveals positive straight leg raise on left at 40 degrees."
    )
    quote = "positive straight leg raise on left at 40 degrees."

    raw_eval = CriterionEvaluation(
        criterion_id="CRIT-01",
        criterion_title="Radiculopathy Exam Sign",
        status=CriterionStatus.MET,
        evidence_quote=quote,
        reasoning="Physical exam demonstrates positive SLR.",
    )

    verified = QuoteVerifier.verify_and_align(raw_eval, note)
    assert verified.is_verified_substring is True
    assert verified.status == CriterionStatus.MET
    assert verified.char_start is not None
    assert verified.char_end is not None
    assert note[verified.char_start : verified.char_end] == quote


def test_quote_verifier_coerces_hallucination_to_insufficient_info():
    note = "Patient has back pain radiating down leg for 6 weeks."
    # Hallucinated quote that is NOT an exact substring
    hallucinated_quote = "Patient attended eight weeks of intense aquatic therapy with great success."

    raw_eval = CriterionEvaluation(
        criterion_id="CRIT-02",
        criterion_title="Conservative Therapy Requirement",
        status=CriterionStatus.MET,
        evidence_quote=hallucinated_quote,
        reasoning="Patient completed therapy.",
    )

    verified = QuoteVerifier.verify_and_align(raw_eval, note)
    # HARD INVARIANT: Must be coerced to INSUFFICIENT_INFO, never MET!
    assert verified.status == CriterionStatus.INSUFFICIENT_INFO
    assert verified.is_verified_substring is False
    assert verified.char_start is None
    assert "[SAFETY ENFORCEMENT" in verified.reasoning


def test_quote_verifier_empty_quote_coerced():
    note = "Patient presents with knee pain."
    raw_eval = CriterionEvaluation(
        criterion_id="CRIT-03",
        criterion_title="MRI Tear",
        status=CriterionStatus.MET,
        evidence_quote="",
        reasoning="Believed to have tear.",
    )

    verified = QuoteVerifier.verify_and_align(raw_eval, note)
    assert verified.status == CriterionStatus.INSUFFICIENT_INFO
    assert verified.is_verified_substring is False

