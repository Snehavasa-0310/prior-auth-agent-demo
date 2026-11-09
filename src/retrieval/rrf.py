"""Reciprocal Rank Fusion (RRF) algorithm for merging hybrid retrieval streams."""

from __future__ import annotations


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[str, float]]],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Merge multiple ranked lists using Reciprocal Rank Fusion.

    Parameters
    ----------
    ranked_lists:
        List of ranked candidate lists, each as [(doc_id, original_score), ...] sorted descending.
    k:
        Smoothing parameter (typically 60 in standard information retrieval literature).

    Returns
    -------
    Merged list of (doc_id, rrf_score) sorted by rrf_score descending.
    """
    rrf_scores: dict[str, float] = {}

    for r_list in ranked_lists:
        for rank, (doc_id, _) in enumerate(r_list):
            # rank is 0-indexed, so 1-based rank is rank + 1
            rank_score = 1.0 / (k + (rank + 1))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rank_score

    sorted_results = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_results
