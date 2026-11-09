"""Integration tests for FastAPI endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    with TestClient(app) as c:
        response = c.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["policies_indexed"] >= 8


def test_list_policies():
    with TestClient(app) as c:
        response = c.get("/policies")
        assert response.status_code == 200
        policies = response.json()
        assert len(policies) >= 8


def test_submit_case_and_review_workflow():
    with TestClient(app) as c:
        note = (
            "SUBJECTIVE:\n"
            "Pt is a 52yo M with persistent low back pain radiating down the left leg into the lateral calf for 10 weeks.\n"
            "Has completed 8 weeks of formal physical therapy with no relief. Also took meloxicam 15mg daily for 6 weeks with minimal benefit.\n"
            "PHYSICAL EXAMINATION:\n"
            "Positive straight leg raise on the left at 40 degrees. Lower extremity motor strength 4/5 left extensor hallucis longus.\n"
            "No saddle anesthesia. Normal rectal tone.\n"
            "PLAN: Order Lumbar spine MRI without contrast (CPT 72148)."
        )

        # 1. Submit Case
        submit_resp = c.post(
            "/cases",
            json={
                "procedure_name": "Lumbar Spine MRI without Contrast",
                "procedure_code": "72148",
                "payer": "Medicare (CMS)",
                "clinical_note": note,
            },
        )
        assert submit_resp.status_code == 201
        case_data = submit_resp.json()
        case_id = case_data["id"]
        assert case_data["status"] == "ANALYZED"
        assert case_data["overall_recommendation"] == "LIKELY_APPROVABLE"
        assert len(case_data["criteria_results"]) >= 4

        # 2. Get Case
        get_resp = c.get(f"/cases/{case_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == case_id

        # 3. Human Reviewer Action: APPROVE
        review_resp = c.post(
            f"/cases/{case_id}/review",
            json={
                "action": "APPROVE",
                "reviewer_notes": "All conservative therapy criteria clinically verified.",
                "edited_letter": case_data["draft_letter"] + "\n[Reviewed and Approved by Medical Director]",
            },
        )
        assert review_resp.status_code == 200
        updated_data = review_resp.json()
        assert updated_data["status"] == "APPROVED_BY_REVIEWER"
        assert "Reviewed and Approved by Medical Director" in updated_data["draft_letter"]


def test_submit_case_blocked_by_phi_guard():
    with TestClient(app) as c:
        phi_note = "Patient SSN is 000-12-3456 and phone is (555) 839-2001. Complains of knee pain."
        response = c.post(
            "/cases",
            json={
                "procedure_name": "Knee Arthroscopy",
                "procedure_code": "29881",
                "payer": "Medicare",
                "clinical_note": phi_note,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "PHI_DETECTED"
