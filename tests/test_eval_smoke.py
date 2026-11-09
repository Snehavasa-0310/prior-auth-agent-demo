"""CI Regression Gate: Evaluates model metrics against strict production safety thresholds."""

from eval.runner import run_evaluation


def test_ci_evaluation_safety_gates(tmp_path):
    """Regression gate: Fails build if critical error rate, faithfulness, or recall violates bounds."""
    results = run_evaluation(output_dir=tmp_path / "ci_results")

    # Gate 1: Zero Critical Error Rate Tolerance
    assert results.critical_error_rate == 0.0, (
        f"CRITICAL SAFETY VIOLATION: Critical Error Rate was {results.critical_error_rate * 100:.2f}%. "
        f"Expected 0.00% (zero unauthorized false approvals)."
    )

    # Gate 2: Exact Substring Evidence Faithfulness
    assert results.exact_substring_faithfulness >= 0.99, (
        f"FAITHFULNESS VIOLATION: Evidence Substring Faithfulness was {results.exact_substring_faithfulness * 100:.2f}%. "
        f"Expected >= 99.0%."
    )

    # Gate 3: Policy Retrieval Recall
    assert results.retrieval_recall_at_1 >= 0.95, (
        f"RETRIEVAL VIOLATION: Retrieval Recall@1 was {results.retrieval_recall_at_1 * 100:.2f}%. "
        f"Expected >= 95.0%."
    )

    # Gate 4: Abstention Recall (correctly identifying missing information)
    assert results.abstention_recall >= 0.85, (
        f"ABSTENTION VIOLATION: Abstention recall was {results.abstention_recall * 100:.2f}%. "
        f"Expected >= 85.0%."
    )
