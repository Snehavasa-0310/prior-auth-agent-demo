"""Cross-Encoder / Reranking module."""

from __future__ import annotations

import re


class FastClinicalReranker:
    """Lightweight clinical cross-scoring reranker.

    Computes fine-grained lexical and semantic alignment between the user's query
    and candidate policy chunks (e.g. CPT code exact match bonus, clinical term density).
    """

    def rerank(self, query: str, candidates: list[tuple[str, str, float]]) -> list[tuple[str, float]]:
        """Rerank candidates based on joint interaction scoring.

        Parameters
        ----------
        query:
            The input query (procedure name, code, or clinical note excerpt).
        candidates:
            List of tuples: (doc_id, doc_text, initial_score).

        Returns
        -------
        Reranked list of (doc_id, reranked_score) sorted descending.
        """
        q_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", query.lower()))
        reranked: list[tuple[str, float]] = []

        for doc_id, text, base_score in candidates:
            doc_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower()))
            overlap = len(q_tokens.intersection(doc_tokens))
            jaccard = overlap / max(len(q_tokens.union(doc_tokens)), 1)

            # Check for exact code match (e.g. 72148, 29881, E0601)
            code_boost = 0.0
            for qt in q_tokens:
                if re.match(r"^\d{4,5}$|^[a-zA-Z]\d{4}$", qt) and qt in doc_tokens:
                    code_boost += 0.5

            final_score = base_score * 0.5 + jaccard * 0.3 + code_boost
            reranked.append((doc_id, float(final_score)))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
