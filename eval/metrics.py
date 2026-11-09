"""Evaluation metrics engine for Prior Authorization Copilot."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ClassificationMetrics:
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvaluationSuiteResult:
    total_cases: int
    tricky_cases_count: int

    # Retrieval Metrics
    retrieval_recall_at_1: float
    retrieval_recall_at_3: float
    retrieval_mrr: float

    # Criterion Metrics
    criterion_accuracy: float
    criterion_macro_f1: float
    criterion_per_class: dict[str, ClassificationMetrics]
    confusion_matrix: dict[str, dict[str, int]]  # truth -> pred -> count

    # Overall Decision Metrics
    overall_accuracy: float
    critical_error_rate: float  # Predicted LIKELY_APPROVABLE when truth is NOT approvable
    critical_error_count: int
    non_approvable_ground_truth_total: int

    # Safety, Faithfulness & Hallucination
    exact_substring_faithfulness: float  # % of quotes that are exact substrings
    evidence_support_score: float  # Rubric alignment
    hallucination_rate: float
    abstention_precision: float
    abstention_recall: float

    # Latency & Cost
    latency_p50_ms: float
    latency_p95_ms: float
    cost_per_case_usd: float

    # Ablation comparisons
    ablations: dict[str, dict[str, float]] = field(default_factory=dict)


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str],
) -> tuple[float, float, dict[str, ClassificationMetrics], dict[str, dict[str, int]]]:
    """Compute accuracy, macro F1, per-class metrics, and confusion matrix."""
    assert len(y_true) == len(y_pred)
    total = len(y_true)
    if total == 0:
        return 0.0, 0.0, {}, {}

    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total

    # Confusion matrix
    matrix: dict[str, dict[str, int]] = {lbl: {l2: 0 for l2 in labels} for lbl in labels}
    for t, p in zip(y_true, y_pred):
        if t in matrix and p in matrix[t]:
            matrix[t][p] += 1

    per_class: dict[str, ClassificationMetrics] = {}
    f1_list: list[float] = []

    for lbl in labels:
        tp = matrix[lbl][lbl]
        fp = sum(matrix[other][lbl] for other in labels if other != lbl)
        fn = sum(matrix[lbl][other] for other in labels if other != lbl)
        support = sum(matrix[lbl].values())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[lbl] = ClassificationMetrics(precision=prec, recall=rec, f1=f1, support=support)
        f1_list.append(f1)

    macro_f1 = float(np.mean(f1_list))
    return accuracy, macro_f1, per_class, matrix


def compute_critical_error_rate(
    ground_truth_recs: list[str],
    predicted_recs: list[str],
) -> tuple[float, int, int]:
    """Calculate the Critical Error Rate.

    A critical error occurs when the system predicts 'LIKELY_APPROVABLE' for a case
    where the true clinical outcome is NOT approvable ('NEEDS_MORE_INFO' or 'LIKELY_DENIED').
    Such errors create high legal and clinical liability in production prior authorization.
    """
    assert len(ground_truth_recs) == len(predicted_recs)

    non_approvable_total = 0
    critical_errors = 0

    for truth, pred in zip(ground_truth_recs, predicted_recs):
        if truth in ("NEEDS_MORE_INFO", "LIKELY_DENIED"):
            non_approvable_total += 1
            if pred == "LIKELY_APPROVABLE":
                critical_errors += 1

    rate = (critical_errors / non_approvable_total) if non_approvable_total > 0 else 0.0
    return rate, critical_errors, non_approvable_total
