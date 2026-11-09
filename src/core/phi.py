"""PHI Guard module.

Scans clinical text for direct Protected Health Information (PHI) identifiers
(e.g., Social Security Numbers, direct phone numbers, email addresses, MRNs)
to ensure real identifiers are strictly blocked from ingestion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PHIViolation:
    entity_type: str
    matched_text: str
    char_start: int
    char_end: int
    message: str


@dataclass
class PHICheckResult:
    is_safe: bool
    violations: list[PHIViolation] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if self.is_safe:
            return "No obvious direct PHI detected."
        items = [f"{v.entity_type} ('{v.matched_text}') at [{v.char_start}:{v.char_end}]" for v in self.violations]
        return f"Blocked {len(self.violations)} potential PHI entity(ies): " + ", ".join(items)


class PHIGuard:
    """Deterministic, high-precision PHI regex scanner."""

    # SSN pattern: 000-00-0000 or unhyphenated 9 digits marked as SSN
    SSN_PATTERN = re.compile(r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b")
    SSN_EXPLICIT_PATTERN = re.compile(r"(?i)\bssn[:\s#]+(\d{3}-\d{2}-\d{4}|\d{9})\b")

    # US Phone Numbers
    PHONE_PATTERN = re.compile(
        r"(?i)(?:phone|tel|cell|fax|call)?[:\s]*(\+?1[-. ]?)?\(?([2-9]\d{2})\)?[-. ]?([2-9]\d{2})[-. ]?(\d{4})\b"
    )

    # Email addresses
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # High-confidence Real MRN pattern (e.g. MRN: 12345678, Medical Record #: 87654321)
    MRN_PATTERN = re.compile(r"(?i)\b(?:mrn|med(?:ical)?\s*rec(?:ord)?(?:\s*#|\s*num|\s*no)?[:\s#]+)([A-Z0-9]{6,12})\b")

    # Credit card / Financial numbers
    FINANCIAL_PATTERN = re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b")

    def scan(self, text: str) -> PHICheckResult:
        """Scan text and return PHICheckResult with any detected direct identifiers."""
        violations: list[PHIViolation] = []

        # 1. SSN
        for match in self.SSN_PATTERN.finditer(text):
            violations.append(
                PHIViolation(
                    entity_type="SSN",
                    matched_text=match.group(0),
                    char_start=match.start(),
                    char_end=match.end(),
                    message="Standard Social Security Number pattern detected.",
                )
            )

        for match in self.SSN_EXPLICIT_PATTERN.finditer(text):
            # Only add if not already caught
            if not any(v.char_start == match.start(1) for v in violations if v.entity_type == "SSN"):
                violations.append(
                    PHIViolation(
                        entity_type="SSN",
                        matched_text=match.group(1),
                        char_start=match.start(1),
                        char_end=match.end(1),
                        message="Explicit SSN label with identifier detected.",
                    )
                )

        # 2. Email
        for match in self.EMAIL_PATTERN.finditer(text):
            violations.append(
                PHIViolation(
                    entity_type="EMAIL",
                    matched_text=match.group(0),
                    char_start=match.start(),
                    char_end=match.end(),
                    message="Email address detected.",
                )
            )

        # 3. Direct Phone Numbers
        for match in self.PHONE_PATTERN.finditer(text):
            full_match = match.group(0).strip()
            # Verify minimum digits to avoid date false positives
            digits = re.sub(r"\D", "", full_match)
            if len(digits) >= 10:
                violations.append(
                    PHIViolation(
                        entity_type="PHONE",
                        matched_text=full_match,
                        char_start=match.start(),
                        char_end=match.end(),
                        message="Direct telephone/fax number pattern detected.",
                    )
                )

        # 4. Explicit MRN
        for match in self.MRN_PATTERN.finditer(text):
            violations.append(
                PHIViolation(
                    entity_type="MRN",
                    matched_text=match.group(0),
                    char_start=match.start(),
                    char_end=match.end(),
                    message="Explicit Medical Record Number pattern detected.",
                )
            )

        # 5. Financial / Credit card
        for match in self.FINANCIAL_PATTERN.finditer(text):
            violations.append(
                PHIViolation(
                    entity_type="FINANCIAL_ID",
                    matched_text=match.group(0),
                    char_start=match.start(),
                    char_end=match.end(),
                    message="Credit card / financial identifier pattern detected.",
                )
            )

        is_safe = len(violations) == 0
        return PHICheckResult(is_safe=is_safe, violations=violations)

    def redact(self, text: str) -> str:
        """Sanitize text by replacing detected PHI with redaction placeholders."""
        result = self.scan(text)
        if result.is_safe:
            return text

        # Sort violations in reverse order of char_start to replace safely
        sorted_violations = sorted(result.violations, key=lambda v: v.char_start, reverse=True)
        sanitized = text
        for v in sorted_violations:
            replacement = f"[REDACTED_{v.entity_type}]"
            sanitized = sanitized[: v.char_start] + replacement + sanitized[v.char_end :]
        return sanitized
