"""Policy loader and indexing coordinator."""

from __future__ import annotations

import json
from pathlib import Path

from src.policy.chunker import PolicyChunker
from src.policy.schemas import PolicyChunk, StructuredPolicy
from src.retrieval.hybrid import HybridPolicyRetriever


def load_policies_from_dir(policies_dir: Path) -> list[StructuredPolicy]:
    """Load all JSON policies from a directory."""
    policies: list[StructuredPolicy] = []
    for f in sorted(policies_dir.glob("*.json")):
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
            policies.append(StructuredPolicy.model_validate(data))
    return policies


def load_and_index_policies(
    policies_dir: Path,
    chunker: PolicyChunker | None = None,
) -> tuple[HybridPolicyRetriever, list[StructuredPolicy], list[PolicyChunk]]:
    """Load policies, split into chunks, and index into the hybrid retriever."""
    chunker = chunker or PolicyChunker()
    policies = load_policies_from_dir(policies_dir)
    all_chunks: list[PolicyChunk] = []

    for policy in policies:
        chunks = chunker.chunk_policy(policy)
        all_chunks.extend(chunks)

    retriever = HybridPolicyRetriever()
    retriever.index(policies, all_chunks)
    return retriever, policies, all_chunks
