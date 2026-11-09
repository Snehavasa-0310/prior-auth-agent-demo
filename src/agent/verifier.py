"""Deterministic quote verification engine enforcing exact substring integrity."""

from __future__ import annotations

import logging

from src.agent.schemas import CriterionEvaluation, CriterionStatus

logger = logging.getLogger(__name__)


class QuoteVerifier:
    """Enforces the fundamental safety invariant:

    A criterion can NEVER be marked MET unless supported by an exact,
    character-verifiable substring of the input clinical note.
    """

    @staticmethod
    def verify_and_align(
        evaluation: CriterionEvaluation,
        clinical_note: str,
    ) -> CriterionEvaluation:
        quote = evaluation.evidence_quote.strip() if evaluation.evidence_quote else ""

        if not quote:
            # Empty quote
            if evaluation.status == CriterionStatus.MET:
                logger.warning(
                    f"Violation in {evaluation.criterion_id}: status was MET but evidence_quote is empty. "
                    "Enforcing INSUFFICIENT_INFO."
                )
                return evaluation.model_copy(
                    update={
                        "status": CriterionStatus.INSUFFICIENT_INFO,
                        "is_verified_substring": False,
                        "char_start": None,
                        "char_end": None,
                        "reasoning": (
                            f"[SAFETY ENFORCEMENT: No evidence quote provided. Coerced from MET to INSUFFICIENT_INFO] "
                            f"{evaluation.reasoning}"
                        ),
                    }
                )
            return evaluation.model_copy(
                update={
                    "is_verified_substring": False,
                    "char_start": None,
                    "char_end": None,
                }
            )

        # Check if quote exists in clinical note
        char_start = clinical_note.find(quote)
        if char_start != -1:
            char_end = char_start + len(quote)
            # Double check exact match
            assert clinical_note[char_start:char_end] == quote
            return evaluation.model_copy(
                update={
                    "is_verified_substring": True,
                    "char_start": char_start,
                    "char_end": char_end,
                }
            )

        # Quote was NOT found as an exact substring
        if evaluation.status == CriterionStatus.MET:
            logger.warning(
                f"Violation in {evaluation.criterion_id}: Evidence quote '{quote}' was NOT found in note! "
                "Enforcing INSUFFICIENT_INFO."
            )
            return evaluation.model_copy(
                update={
                    "status": CriterionStatus.INSUFFICIENT_INFO,
                    "is_verified_substring": False,
                    "char_start": None,
                    "char_end": None,
                    "reasoning": (
                        f"[SAFETY ENFORCEMENT: Hallucinated or non-exact evidence quote '{quote}' rejected. "
                        f"Coerced from MET to INSUFFICIENT_INFO] {evaluation.reasoning}"
                    ),
                }
            )

        return evaluation.model_copy(
            update={
                "is_verified_substring": False,
                "char_start": None,
                "char_end": None,
            }
        )
