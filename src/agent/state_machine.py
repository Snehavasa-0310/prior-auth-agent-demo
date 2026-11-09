"""State machine agent orchestrating prior authorization evaluation."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime

from src.agent.schemas import (
    AuditEvent,
    CriterionEvaluation,
    CriterionStatus,
    OverallRecommendation,
    PriorAuthDecision,
)
from src.agent.tools import PriorAuthTools
from src.policy.schemas import StructuredPolicy

logger = logging.getLogger(__name__)


class PriorAuthStateMachineAgent:
    """Deterministic, transparent Prior Authorization State Machine Agent."""

    def __init__(self, tools: PriorAuthTools, model_name: str = "prior-auth-agent-v1"):
        self.tools = tools
        self.model_name = model_name

    def run(
        self,
        clinical_note: str,
        procedure_name: str,
        procedure_code: str,
        payer: str = "Standard Payer",
        policy_override: StructuredPolicy | None = None,
        use_hybrid_retrieval: bool = True,
        use_reranker: bool = False,
    ) -> PriorAuthDecision:
        audit_trail: list[AuditEvent] = []

        # Step 1: SEARCH_POLICY
        step_start = time.time()
        policy: StructuredPolicy | None = policy_override
        if not policy:
            policy = self.tools.search_policy(
                procedure_name_or_code=f"{procedure_name} {procedure_code}",
                payer=payer,
                use_hybrid=use_hybrid_retrieval,
                use_reranker=use_reranker,
            )

        step_latency = (time.time() - step_start) * 1000
        audit_trail.append(
            AuditEvent(
                step_name="SEARCH_POLICY",
                tool_name="search_policy",
                input_summary={"procedure_name": procedure_name, "procedure_code": procedure_code},
                output_summary={"found_policy_id": policy.id if policy else None},
                latency_ms=step_latency,
                model_name=self.model_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

        if not policy:
            # Fallback if no matching policy exists
            return PriorAuthDecision(
                policy_id="POLICY_NOT_FOUND",
                procedure_name=procedure_name,
                procedure_code=procedure_code,
                payer=payer,
                overall_recommendation=OverallRecommendation.NEEDS_MORE_INFO,
                confidence_score=0.0,
                criteria_results=[],
                missing_information=["Unable to locate a matching payer coverage policy."],
                draft_letter="Prior authorization could not be determined because no matching coverage policy was found.",
                audit_trail=audit_trail,
            )

        # Step 2: EXTRACT_FACTS
        step_start = time.time()
        facts = self.tools.extract_note_facts(clinical_note)
        step_latency = (time.time() - step_start) * 1000
        audit_trail.append(
            AuditEvent(
                step_name="EXTRACT_FACTS",
                tool_name="extract_note_facts",
                input_summary={"note_length": len(clinical_note)},
                output_summary={"fact_count": len(facts.facts)},
                latency_ms=step_latency,
                model_name=self.model_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

        # Step 3: EVALUATE_CRITERIA
        step_start = time.time()
        criteria_evals: list[CriterionEvaluation] = []
        for crit in policy.criteria:
            crit_eval = self.tools.check_criterion(crit, clinical_note, facts)
            criteria_evals.append(crit_eval)

        step_latency = (time.time() - step_start) * 1000
        audit_trail.append(
            AuditEvent(
                step_name="EVALUATE_CRITERIA",
                tool_name="check_criterion",
                input_summary={"criteria_count": len(policy.criteria)},
                output_summary={"evaluated_count": len(criteria_evals)},
                latency_ms=step_latency,
                model_name=self.model_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

        # Step 4: AGGREGATE_DECISION
        step_start = time.time()
        missing_info: list[str] = []
        has_hard_denial = False
        has_incomplete_or_insufficient = False

        # Build map of criterion id to definition
        crit_def_map = {c.id: c for c in policy.criteria}

        for eval_res in criteria_evals:
            crit_def = crit_def_map.get(eval_res.criterion_id)
            is_mandatory = crit_def.is_mandatory if crit_def else True
            crit_type = crit_def.criterion_type.value if crit_def else "INCLUSION"

            if eval_res.status == CriterionStatus.NOT_MET:
                # Distinguish between hard medical denials vs conservative therapy pends
                if crit_type in ("EXCLUSION", "DIAGNOSTIC") or "exclusion" in eval_res.reasoning.lower() or "denies" in eval_res.reasoning.lower():
                    has_hard_denial = True
                else:
                    # Incomplete conservative trial (e.g. 3-4 weeks done out of 6) pends for additional clinicals
                    has_incomplete_or_insufficient = True
                    missing_info.append(f"{eval_res.criterion_title}: {eval_res.reasoning}")
            elif eval_res.status == CriterionStatus.INSUFFICIENT_INFO:
                if is_mandatory:
                    has_incomplete_or_insufficient = True
                    missing_info.append(f"{eval_res.criterion_title}: {eval_res.reasoning}")

        if has_hard_denial:
            overall_rec = OverallRecommendation.LIKELY_DENIED
            confidence = 0.95
        elif has_incomplete_or_insufficient:
            overall_rec = OverallRecommendation.NEEDS_MORE_INFO
            confidence = 0.88
        else:
            overall_rec = OverallRecommendation.LIKELY_APPROVABLE
            confidence = 0.98

        step_latency = (time.time() - step_start) * 1000
        audit_trail.append(
            AuditEvent(
                step_name="AGGREGATE_DECISION",
                tool_name="aggregate_decision",
                input_summary={"criteria_results": [e.status.value for e in criteria_evals]},
                output_summary={"recommendation": overall_rec.value, "missing_gaps": len(missing_info)},
                latency_ms=step_latency,
                model_name=self.model_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

        # Step 5: DRAFT_LETTER
        step_start = time.time()
        letter = self.tools.draft_letter(
            procedure_name=procedure_name,
            procedure_code=procedure_code,
            payer=payer,
            policy=policy,
            criteria_evaluations=criteria_evals,
            recommendation=overall_rec,
        )
        step_latency = (time.time() - step_start) * 1000
        audit_trail.append(
            AuditEvent(
                step_name="DRAFT_LETTER",
                tool_name="draft_letter",
                input_summary={"recommendation": overall_rec.value},
                output_summary={"letter_length": len(letter)},
                latency_ms=step_latency,
                model_name=self.model_name,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )

        return PriorAuthDecision(
            policy_id=policy.id,
            procedure_name=procedure_name,
            procedure_code=procedure_code,
            payer=payer,
            overall_recommendation=overall_rec,
            confidence_score=confidence,
            criteria_results=criteria_evals,
            missing_information=missing_info,
            draft_letter=letter,
            audit_trail=audit_trail,
        )
