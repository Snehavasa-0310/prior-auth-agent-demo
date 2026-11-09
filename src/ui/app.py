"""Streamlit Reviewer Dashboard for Prior Authorization Agent."""

import html
import os

import requests
import streamlit as st

st.set_page_config(
    page_title="Prior Authorization Copilot - Reviewer Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# API Configuration
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-prior-auth-key")
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Top Disclaimer
st.warning("⚠️ **DEMO ONLY. Not medical or coverage advice. Use strictly synthetic data.**")

# Sidebar
st.sidebar.title("🩺 Prior Auth Copilot")
st.sidebar.markdown(
    "Human-in-the-Loop Clinical Reviewer Workspace.\n"
    "Deterministic policy retrieval & verifiable exact-substring citation checking."
)

PROCEDURE_PRESETS = [
    {
        "name": "Lumbar Spine MRI without Contrast",
        "code": "72148",
        "payer": "Medicare (CMS)",
        "sample": (
            "CLINICAL ENCOUNTER NOTE - SPINE CLINIC\n"
            "Patient: Robert Johnson | Age: 52 | Sex: Male\n"
            "Date of Service: 2024-03-12\n\n"
            "SUBJECTIVE:\n"
            "Pt is a 52yo M with persistent low back pain radiating down the left leg into the lateral calf and great toe for 10 weeks.\n"
            "Pain is sharp, burning, 8/10 severity. Has completed 8 weeks of formal physical therapy with no relief. "
            "Also took meloxicam 15mg daily for 6 weeks with minimal benefit.\n\n"
            "PHYSICAL EXAMINATION:\n"
            "Lumbar Spine: Tenderness at L4-L5 interspace. Decreased sensation along left L5 dermatome. "
            "Positive straight leg raise on the left at 40 degrees. Lower extremity motor strength 4/5 left extensor hallucis longus.\n"
            "No saddle anesthesia. Normal rectal tone.\n\n"
            "ASSESSMENT & PLAN:\n"
            "Left L5 radiculopathy secondary to suspected herniated nucleus pulposus. Failed conservative therapy > 6 weeks. "
            "Order Lumbar spine MRI without contrast (CPT 72148)."
        ),
    },
    {
        "name": "Arthroscopy, knee, surgical; with meniscectomy",
        "code": "29881",
        "payer": "Anthem / Commercial Payer",
        "sample": (
            "ORTHOPEDIC CLINIC CONSULTATION\n"
            "Patient: Sarah Connor | Age: 44 | Sex: Female\n"
            "HPI: Patient reports persistent right knee pain with episodic true mechanical locking and catching when descending stairs. "
            "Symptoms ongoing for 4 months. Completed 8 weeks of supervised physical therapy focusing on quadriceps strengthening without resolution. "
            "Received right knee intra-articular cortisone injection 6 weeks ago with only transient 3-day relief.\n"
            "PHYSICAL EXAM:\n"
            "Right knee demonstrates joint effusion, medial joint line tenderness, and positive McMurray click with pain.\n"
            "IMAGING:\n"
            "Right knee MRI: Demonstrates complex tear of posterior horn of medial meniscus with no significant osteoarthritis.\n"
            "PLAN: Right knee arthroscopy with partial medial meniscectomy (CPT 29881)."
        ),
    },
    {
        "name": "Semaglutide / Dulaglutide / Tirzepatide (GLP-1)",
        "code": "J3490",
        "payer": "UnitedHealthcare / Commercial",
        "sample": (
            "ENDOCRINOLOGY CLINIC VISIT\n"
            "Patient: Marcus Vance | Age: 58 | Sex: Male\n"
            "DIAGNOSIS: Type 2 Diabetes Mellitus without acute complications (E11.9).\n"
            "HPI: Patient has a 5-year history of T2D. Currently prescribed Metformin 1000mg BID for the past 6 months, "
            "but experiences persistent gastrointestinal distress and unable to achieve glycemic goal.\n"
            "LABS (Dated 2 weeks ago):\n"
            "HbA1c: 8.6% (baseline elevated). eGFR: 78 mL/min/1.73m2. Fasting glucose: 174 mg/dL.\n"
            "MEDICATIONS: Metformin 1000mg BID. No DPP-4 inhibitors prescribed or taken.\n"
            "PLAN: Prescribe Semaglutide (Ozempic) 0.5mg subcutaneous weekly injection."
        ),
    },
]

preset_idx = st.sidebar.selectbox(
    "Load Preset Clinical Archetype",
    range(len(PROCEDURE_PRESETS)),
    format_func=lambda i: PROCEDURE_PRESETS[i]["name"],
)
selected_preset = PROCEDURE_PRESETS[preset_idx]

st.sidebar.divider()
st.sidebar.markdown("### Service Health")
try:
    health_resp = requests.get(f"{API_URL}/health", timeout=2)
    if health_resp.status_code == 200:
        st.sidebar.success(f"API Online (v{health_resp.json().get('version')})")
        st.sidebar.caption(f"Policies Indexed: {health_resp.json().get('policies_indexed')}")
    else:
        st.sidebar.error("API returned non-200")
except Exception:
    st.sidebar.warning("API offline. Start with `make run` or uvicorn.")


# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Submit & Analyze Case", "🔍 Reviewer Workspace", "📋 Policy Knowledge Base"])

with tab1:
    st.header("Submit Clinical Encounter for Prior Auth Analysis")

    col_meta1, col_meta2, col_meta3 = st.columns(3)
    with col_meta1:
        procedure_name = st.text_input("Procedure / Medication Name", value=selected_preset["name"])
    with col_meta2:
        procedure_code = st.text_input("CPT / HCPCS Code", value=selected_preset["code"])
    with col_meta3:
        payer = st.text_input("Target Payer", value=selected_preset["payer"])

    clinical_note = st.text_area(
        "Clinical Note (Paste or edit synthetic documentation)",
        value=selected_preset["sample"],
        height=280,
    )

    if st.button("🚀 Run Prior Auth Analysis Agent", type="primary"):
        with st.spinner("Executing PHI Guard, Hybrid Policy Retrieval, Fact Extraction & Verification..."):
            try:
                resp = requests.post(
                    f"{API_URL}/cases",
                    headers=HEADERS,
                    json={
                        "procedure_name": procedure_name,
                        "procedure_code": procedure_code,
                        "payer": payer,
                        "clinical_note": clinical_note,
                    },
                    timeout=10,
                )
                if resp.status_code == 201:
                    case_data = resp.json()
                    st.session_state["active_case"] = case_data
                    st.success(f"Case {case_data['id']} analyzed successfully! Switch to 'Reviewer Workspace'.")
                elif resp.status_code == 422:
                    st.error(f"🛑 Submission Blocked by PHI Guard:\n{resp.json().get('detail')}")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")

with tab2:
    st.header("Clinical Reviewer Workspace")
    case = st.session_state.get("active_case")

    if not case:
        st.info("No active case analyzed yet. Submit a case in Tab 1 or select a recent case below.")
        try:
            list_resp = requests.get(f"{API_URL}/cases", headers=HEADERS, timeout=2)
            if list_resp.status_code == 200 and list_resp.json():
                cases_list = list_resp.json()
                chosen_id = st.selectbox("Select existing case", [c["id"] for c in cases_list])
                if st.button("Load Selected Case"):
                    c_resp = requests.get(f"{API_URL}/cases/{chosen_id}", headers=HEADERS)
                    if c_resp.status_code == 200:
                        st.session_state["active_case"] = c_resp.json()
                        st.rerun()
        except Exception:
            pass
    else:
        # Display Recommendation Pill
        rec = case.get("overall_recommendation")
        status_col, id_col, conf_col = st.columns([2, 2, 1])

        with status_col:
            if rec == "LIKELY_APPROVABLE":
                st.success(f"### Recommendation: ✅ {rec}")
            elif rec == "NEEDS_MORE_INFO":
                st.warning(f"### Recommendation: ⚠️ {rec}")
            else:
                st.error(f"### Recommendation: ❌ {rec}")

        with id_col:
            st.markdown(f"**Case ID:** `{case.get('id')}`")
            st.markdown(f"**Workflow Status:** `{case.get('status')}`")

        with conf_col:
            st.metric("Confidence", f"{case.get('confidence_score', 0.0) * 100:.0f}%")

        st.divider()

        # Two-Column Layout: Left = Criteria Checklist, Right = Note with Verified Spans
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("Policy Criteria Checklist")
            for crit in case.get("criteria_results", []):
                crit_status = crit["status"]
                with st.expander(
                    f"{'✅' if crit_status == 'MET' else '❌' if crit_status == 'NOT_MET' else '⚠️'} [{crit_status}] {crit['criterion_title']}",
                    expanded=(crit_status != "MET"),
                ):
                    st.markdown(f"**Criterion ID:** `{crit['criterion_id']}`")
                    st.markdown(f"**Reasoning:** {crit['reasoning']}")
                    if crit.get("evidence_quote"):
                        verified_badge = "🛡️ **Exact Substring Verified**" if crit.get("is_verified_substring") else "❌ Unverified"
                        st.markdown(f"**Evidence Citation:** {verified_badge}")
                        st.info(f"\"{crit['evidence_quote']}\"")
                        if crit.get("char_start") is not None:
                            st.caption(f"Offsets in Note: Chars [{crit['char_start']}:{crit['char_end']}]")
                    else:
                        st.caption("No verifiable evidence quote present in note.")

        with col_right:
            st.subheader("Note Inspector & Verified Citations")
            raw_note = case.get("raw_clinical_note", "")

            # Render HTML highlighted note
            highlighted = html.escape(raw_note)
            for crit in case.get("criteria_results", []):
                quote = crit.get("evidence_quote")
                if quote and crit.get("is_verified_substring") and quote in raw_note:
                    escaped_quote = html.escape(quote)
                    color = "#c8e6c9" if crit["status"] == "MET" else "#ffcdd2" if crit["status"] == "NOT_MET" else "#fff9c4"
                    replacement = f'<span style="background-color: {color}; padding: 2px 4px; border-radius: 4px; border: 1px solid #888;" title="{crit["criterion_title"]}">{escaped_quote}</span>'
                    highlighted = highlighted.replace(escaped_quote, replacement, 1)

            st.markdown(
                f'<div style="border: 1px solid #ccc; padding: 12px; border-radius: 6px; max-height: 400px; overflow-y: scroll; white-space: pre-wrap; font-family: monospace; font-size: 13px; background-color: #fafafa;">{highlighted}</div>',
                unsafe_allow_html=True,
            )

        st.divider()

        # Prior Auth Request Letter & Reviewer Decision
        st.subheader("Prior Authorization Request Letter")
        edited_letter = st.text_area("Edit Draft Request Letter", value=case.get("draft_letter", ""), height=250)

        st.subheader("Human-in-the-Loop Reviewer Sign-Off")
        reviewer_notes = st.text_input("Reviewer Clinical Rationale / Notes", value="Clinically reviewed and verified against policy.")

        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("✅ Approve Request", type="primary", use_container_width=True):
                resp = requests.post(
                    f"{API_URL}/cases/{case['id']}/review",
                    headers=HEADERS,
                    json={"action": "APPROVE", "reviewer_notes": reviewer_notes, "edited_letter": edited_letter},
                )
                if resp.status_code == 200:
                    st.session_state["active_case"] = resp.json()
                    st.success("Case Approved by Reviewer!")
                    st.rerun()

        with action_col2:
            if st.button("❌ Reject Request", use_container_width=True):
                resp = requests.post(
                    f"{API_URL}/cases/{case['id']}/review",
                    headers=HEADERS,
                    json={"action": "REJECT", "reviewer_notes": reviewer_notes, "edited_letter": edited_letter},
                )
                if resp.status_code == 200:
                    st.session_state["active_case"] = resp.json()
                    st.warning("Case Rejected by Reviewer.")
                    st.rerun()

        with action_col3:
            if st.button("📝 Request Additional Clinicals", use_container_width=True):
                resp = requests.post(
                    f"{API_URL}/cases/{case['id']}/review",
                    headers=HEADERS,
                    json={"action": "REQUEST_INFO", "reviewer_notes": reviewer_notes, "edited_letter": edited_letter},
                )
                if resp.status_code == 200:
                    st.session_state["active_case"] = resp.json()
                    st.info("Additional information requested.")
                    st.rerun()

with tab3:
    st.header("Authoritative Payer Coverage Policies")
    try:
        p_resp = requests.get(f"{API_URL}/policies", headers=HEADERS, timeout=2)
        if p_resp.status_code == 200:
            policies_list = p_resp.json()
            st.dataframe(policies_list, use_container_width=True)
    except Exception:
        st.info("Start API server to browse active policies.")
