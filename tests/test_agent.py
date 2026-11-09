"""Tests for Prior Authorization State Machine Agent and Repository."""

from pathlib import Path

from src.agent.schemas import CaseStatus, CriterionStatus, OverallRecommendation
from src.agent.state_machine import PriorAuthStateMachineAgent
from src.agent.tools import PriorAuthTools
from src.policy.loader import load_and_index_policies
from src.storage.repository import CaseRepository


def test_prior_auth_agent_end_to_end(tmp_path):
    retriever, policies, chunks = load_and_index_policies(Path("data/policies"))
    tools = PriorAuthTools(retriever=retriever)
    agent = PriorAuthStateMachineAgent(tools=tools)

    db_path = tmp_path / "test_agent.db"
    repo = CaseRepository(db_url=f"sqlite:///{db_path}")

    # Test Case 1: Approvable Lumbar Spine MRI
    note = (
        "SUBJECTIVE:\n"
        "Pt is a 52yo M with persistent low back pain radiating down the left leg into the lateral calf and great toe for 10 weeks.\n"
        "Has completed 8 weeks of formal physical therapy with no relief. Also took meloxicam 15mg daily for 6 weeks with minimal benefit.\n"
        "PHYSICAL EXAMINATION:\n"
        "Positive straight leg raise on the left at 40 degrees. Lower extremity motor strength 4/5 left extensor hallucis longus.\n"
        "No saddle anesthesia. Normal rectal tone.\n"
        "PLAN: Order Lumbar spine MRI without contrast (CPT 72148)."
    )

    case = repo.create_case(
        case_id="TEST-CASE-001",
        procedure_name="Lumbar Spine MRI without Contrast",
        procedure_code="72148",
        payer="Medicare (CMS)",
        raw_clinical_note=note,
    )
    assert case.status == CaseStatus.SUBMITTED.value

    decision = agent.run(
        clinical_note=note,
        procedure_name="Lumbar Spine MRI without Contrast",
        procedure_code="72148",
        payer="Medicare (CMS)",
    )

    assert decision.policy_id == "POL-CMS-L34220-LUMBAR-MRI"
    assert decision.overall_recommendation == OverallRecommendation.LIKELY_APPROVABLE
    assert len(decision.criteria_results) >= 4

    # Verify that all MET criteria have verified substring quotes
    for cr in decision.criteria_results:
        if cr.status == CriterionStatus.MET:
            assert cr.is_verified_substring is True
            assert cr.char_start is not None
            assert cr.char_end is not None
            assert note[cr.char_start : cr.char_end] == cr.evidence_quote

    # Verify letter drafting
    assert "PRIOR AUTHORIZATION REQUEST PACKET" in decision.draft_letter
    assert "POL-CMS-L34220-LUMBAR-MRI" in decision.draft_letter

    # Verify audit trail
    assert len(decision.audit_trail) >= 4
    step_names = [e.step_name for e in decision.audit_trail]
    assert "SEARCH_POLICY" in step_names
    assert "EXTRACT_FACTS" in step_names
    assert "EVALUATE_CRITERIA" in step_names
    assert "AGGREGATE_DECISION" in step_names

    # Persist decision and check retrieval
    saved_case = repo.save_decision("TEST-CASE-001", decision)
    assert saved_case.status == CaseStatus.ANALYZED.value

    fetched = repo.get_case("TEST-CASE-001")
    assert fetched is not None
    assert fetched["status"] == "ANALYZED"
    assert fetched["overall_recommendation"] == "LIKELY_APPROVABLE"
    assert len(fetched["criteria_results"]) >= 4

    # Test Human Reviewer Action
    updated = repo.update_reviewer_action(
        case_id="TEST-CASE-001",
        action="APPROVE",
        reviewer_notes="Approved following clinical review of 8 weeks of PT documentation.",
        edited_letter=decision.draft_letter + "\n[Clinically Approved by MD]",
    )
    assert updated["status"] == CaseStatus.APPROVED_BY_REVIEWER.value
    assert "Clinically Approved by MD" in updated["draft_letter"]
