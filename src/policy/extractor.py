"""LLM-based policy criteria extractor with disk caching and Pydantic validation."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from src.core.llm import BaseLLMClient, get_llm_client
from src.policy.schemas import (
    CriteriaExtractionResult,
    CriterionDefinition,
    CriterionType,
    StructuredPolicy,
)

logger = logging.getLogger(__name__)


class CriteriaExtractor:
    """Extracts discrete clinical criteria from policy documents with caching."""

    def __init__(
        self,
        llm_client: BaseLLMClient | None = None,
        cache_dir: Path | None = None,
    ):
        self.llm_client = llm_client or get_llm_client()
        self.cache_dir = cache_dir or Path("data/cache/criteria")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, policy: StructuredPolicy, force_refresh: bool = False) -> CriteriaExtractionResult:
        cache_file = self.cache_dir / f"{policy.id}.json"

        # 1. Check cache
        if not force_refresh and cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    data = json.load(f)
                return CriteriaExtractionResult.model_validate(data)
            except Exception as e:
                logger.warning(f"Error loading cached criteria for {policy.id}: {e}")

        # 2. If policy already has pre-curated structured criteria (from policy source), use as gold standard
        if policy.criteria and len(policy.criteria) > 0:
            result = CriteriaExtractionResult(
                policy_id=policy.id,
                procedure_name=policy.procedure_name,
                criteria=policy.criteria,
                extracted_at=datetime.now(UTC).isoformat(),
                version="1.0",
            )
            # Write cache
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2)
            return result

        # 3. Otherwise, invoke LLM extractor
        prompt = (
            f"You are an expert healthcare prior authorization criteria extractor.\n"
            f"Convert this medical coverage policy into a structured checklist of discrete criteria.\n\n"
            f"Policy: {policy.title} ({policy.id})\n"
            f"Procedure: {policy.procedure_name}\n"
            f"Payer: {policy.payer}\n"
            f"Summary: {policy.summary}\n\n"
            f"Policy Content:\n"
        )
        for s in policy.sections:
            prompt += f"--- Section: {s.title} ---\n{s.content}\n\n"

        prompt += (
            "Extract discrete criteria. Each criterion must specify:\n"
            "- id: unique ID (e.g. CRIT-01)\n"
            "- title: concise title\n"
            "- criterion_type: INCLUSION, EXCLUSION, CONSERVATIVE_THERAPY, or DIAGNOSTIC\n"
            "- description: clinical rule\n"
            "- required_evidence_description: what documentation in note would prove it\n"
            "- is_mandatory: boolean\n"
        )

        try:
            res = self.llm_client.complete_structured(
                prompt=prompt,
                response_model=CriteriaExtractionResult,
                system_prompt="Extract clinical prior auth criteria in strict accordance with the requested schema.",
            )
        except Exception:
            # Fallback to default policy criteria
            res = CriteriaExtractionResult(
                policy_id=policy.id,
                procedure_name=policy.procedure_name,
                criteria=[
                    CriterionDefinition(
                        id=f"{policy.id}-CRIT-01",
                        title="Documented Clinical Indication",
                        criterion_type=CriterionType.INCLUSION,
                        description=policy.summary,
                        required_evidence_description="Relevant clinical notes and physical exam.",
                        is_mandatory=True,
                    )
                ],
                extracted_at=datetime.now(UTC).isoformat(),
                version="1.0",
            )

        # Write cache
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(res.model_dump(), f, indent=2)

        return res
