"""Hybrid retrieval engine combining Dense Vector search, BM25 keyword search, and RRF."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.policy.schemas import PolicyChunk, StructuredPolicy
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.embeddings import BaseEmbedder, FastClinicalEmbedder, cosine_similarity
from src.retrieval.reranker import FastClinicalReranker
from src.retrieval.rrf import reciprocal_rank_fusion


@dataclass
class SearchResult:
    policy_id: str
    procedure_name: str
    score: float
    matched_chunk_id: str | None
    matched_chunk_text: str
    policy: StructuredPolicy | None = None


class HybridPolicyRetriever:
    """Enterprise hybrid policy retrieval system."""

    def __init__(
        self,
        embedder: BaseEmbedder | None = None,
        bm25: BM25Retriever | None = None,
        reranker: FastClinicalReranker | None = None,
    ):
        self.embedder = embedder or FastClinicalEmbedder()
        self.bm25 = bm25 or BM25Retriever()
        self.reranker = reranker or FastClinicalReranker()

        self.policies: dict[str, StructuredPolicy] = {}
        self.chunks: list[PolicyChunk] = []
        self.chunk_map: dict[str, PolicyChunk] = {}
        self.chunk_embeddings: np.ndarray | None = None
        self._is_indexed = False

    def index(self, policies: list[StructuredPolicy], chunks: list[PolicyChunk]) -> None:
        """Index policies and their constituent chunks into vector and BM25 stores."""
        self.policies = {p.id: p for p in policies}
        self.chunks = chunks
        self.chunk_map = {c.chunk_id: c for c in chunks}

        # 1. Fit BM25
        chunk_ids = [c.chunk_id for c in chunks]
        chunk_texts = [c.content for c in chunks]
        self.bm25.fit(chunk_ids, chunk_texts)

        # 2. Compute Dense Embeddings
        self.chunk_embeddings = self.embedder.embed_texts(chunk_texts)
        self._is_indexed = True

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        use_vector_only: bool = False,
        use_bm25_only: bool = False,
        use_reranker: bool = False,
    ) -> list[SearchResult]:
        """Search policy chunks and aggregate at policy level."""
        if not self._is_indexed or not self.chunks:
            return []

        # 1. Dense Vector Retrieval
        query_vec = self.embedder.embed_query(query)
        assert self.chunk_embeddings is not None
        vector_sims = cosine_similarity(query_vec, self.chunk_embeddings)
        vector_ranked = [
            (self.chunks[i].chunk_id, float(vector_sims[i])) for i in range(len(self.chunks))
        ]
        vector_ranked.sort(key=lambda x: x[1], reverse=True)

        # 2. BM25 Keyword Retrieval
        bm25_ranked = self.bm25.score(query)

        # 3. Stream Merging / Ablation Logic
        if use_vector_only:
            combined_chunk_ranks = vector_ranked[: top_k * 4]
        elif use_bm25_only:
            combined_chunk_ranks = bm25_ranked[: top_k * 4]
        elif use_hybrid:
            combined_chunk_ranks = reciprocal_rank_fusion([vector_ranked, bm25_ranked], k=60)
        else:
            combined_chunk_ranks = vector_ranked[: top_k * 4]

        # 4. Optional Cross-Encoder Reranker
        if use_reranker:
            candidates = [
                (chunk_id, self.chunk_map[chunk_id].content, score)
                for chunk_id, score in combined_chunk_ranks[:15]
                if chunk_id in self.chunk_map
            ]
            reranked_chunks = self.reranker.rerank(query, candidates)
            final_ranked_chunks = reranked_chunks
        else:
            final_ranked_chunks = combined_chunk_ranks

        # 5. Aggregate to Policy Level (taking highest scoring chunk per policy)
        policy_scores: dict[str, tuple[float, str]] = {}
        for chunk_id, score in final_ranked_chunks:
            chunk = self.chunk_map.get(chunk_id)
            if not chunk:
                continue
            pol_id = chunk.policy_id
            if pol_id not in policy_scores or score > policy_scores[pol_id][0]:
                policy_scores[pol_id] = (score, chunk_id)

        sorted_policies = sorted(policy_scores.items(), key=lambda x: x[1][0], reverse=True)

        results: list[SearchResult] = []
        for pol_id, (best_score, best_chunk_id) in sorted_policies[:top_k]:
            policy_obj = self.policies.get(pol_id)
            best_chunk = self.chunk_map[best_chunk_id]
            results.append(
                SearchResult(
                    policy_id=pol_id,
                    procedure_name=policy_obj.procedure_name if policy_obj else best_chunk.procedure_name,
                    score=best_score,
                    matched_chunk_id=best_chunk_id,
                    matched_chunk_text=best_chunk.content,
                    policy=policy_obj,
                )
            )

        return results
