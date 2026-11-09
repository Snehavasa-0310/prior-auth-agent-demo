"""BM25 (Best Matching 25) Keyword Retrieval Engine."""

from __future__ import annotations

import math
import re


class BM25Retriever:
    """Okapi BM25 implementation optimized for clinical keywords and CPT codes."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: list[str] = []
        self.doc_ids: list[str] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.term_freqs: list[dict[str, int]] = []

    def _tokenize(self, text: str) -> list[str]:
        # Keep words and alphanumeric codes (e.g. 72148, e0601, l34220)
        return re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text.lower())

    def fit(self, doc_ids: list[str], texts: list[str]) -> None:
        self.doc_ids = doc_ids
        self.corpus = texts
        self.doc_lengths = []
        self.term_freqs = []
        self.doc_freqs = {}

        total_len = 0
        for text in texts:
            tokens = self._tokenize(text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for unique_token in tf.keys():
                self.doc_freqs[unique_token] = self.doc_freqs.get(unique_token, 0) + 1

        self.avg_doc_len = total_len / max(len(texts), 1)

    def score(self, query: str) -> list[tuple[str, float]]:
        """Calculate BM25 score for all indexed documents given a query string."""
        q_tokens = self._tokenize(query)
        num_docs = len(self.corpus)
        scores: list[float] = [0.0] * num_docs

        for token in q_tokens:
            if token not in self.doc_freqs:
                continue
            df = self.doc_freqs[token]
            idf = math.log(1.0 + (num_docs - df + 0.5) / (df + 0.5))

            for i, tf_dict in enumerate(self.term_freqs):
                tf = tf_dict.get(token, 0)
                if tf > 0:
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lengths[i] / max(self.avg_doc_len, 1e-6)))
                    scores[i] += idf * (numerator / denominator)

        ranked = [(self.doc_ids[i], scores[i]) for i in range(num_docs)]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked
