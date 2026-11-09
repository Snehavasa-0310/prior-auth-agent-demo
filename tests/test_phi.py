"""Tests for PHI Guard."""

from src.core.phi import PHIGuard


def test_phi_guard_clean_synthetic_text():
    guard = PHIGuard()
    text = (
        "Patient is a 54yo male presenting with progressive lower back pain radiating "
        "to left L5 dermatome. Conservative therapy attempted for 8 weeks without relief."
    )
    result = guard.scan(text)
    assert result.is_safe
    assert len(result.violations) == 0


def test_phi_guard_blocks_ssn():
    guard = PHIGuard()
    text = "Patient SSN is 123-45-6789. Referred by Dr. Smith."
    result = guard.scan(text)
    assert not result.is_safe
    assert any(v.entity_type == "SSN" for v in result.violations)


def test_phi_guard_blocks_email_and_phone():
    guard = PHIGuard()
    text = "Contact patient at john.doe@example.com or phone (555) 234-5678."
    result = guard.scan(text)
    assert not result.is_safe
    types = {v.entity_type for v in result.violations}
    assert "EMAIL" in types
    assert "PHONE" in types


def test_phi_guard_redaction():
    guard = PHIGuard()
    text = "Call 555-839-2001 or email test@health.org immediately."
    redacted = guard.redact(text)
    assert "555-839-2001" not in redacted
    assert "test@health.org" not in redacted
    assert "[REDACTED_PHONE]" in redacted or "[REDACTED_EMAIL]" in redacted

