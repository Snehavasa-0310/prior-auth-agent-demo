"""Interactive terminal demo for Prior Authorization Copilot Agent.

Provides a fast, visual, colorized demonstration of:
1. Automated PHI scanning
2. Hybrid policy retrieval (Vector + BM25 + RRF)
3. Deterministic state-machine criterion evaluation
4. Programmatic exact-substring verification
5. Prior authorization letter drafting and audit logging
"""

import sys
import time
from pathlib import Path

# Ensure root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ANSI colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{CYAN}{BOLD}{'=' * 80}")
    print("      PRIOR AUTHORIZATION COPILOT: CLINICAL AGENT DEMO & VERIFICATION")
    print(f"{'=' * 80}{RESET}")
    print(f"{YELLOW}DISCLAIMER: Demo only. Not medical or coverage advice. All patient data is synthetic.{RESET}\n")


def run_demo():
    print_banner()

    # Step 1: Initialize System
    print(f"{BOLD}[1/5] Loading Authoritative Payer Coverage Policies...{RESET}")
    from src.policy.loader import load_and_index_policies
    from src.core.phi import PHIGuard
    from src.agent.tools import PriorAuthTools
    from src.agent.state_machine import PriorAuthStateMachineAgent

    policies_dir = Path("data/policies")
    retriever, policies, chunks = load_and_index_policies(policies_dir)
    print(f"  {GREEN}✓{RESET} Loaded {len(policies)} clinical coverage policies into Vector & BM25 indices.")

    tools = PriorAuthTools(retriever=retriever)
    agent = PriorAuthStateMachineAgent(tools=tools)
    phi_guard = PHIGuard()

    # Step 2: Sample Clinical Encounter
    sample_note = (
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
    )

    proc_name = "Lumbar Spine MRI without Contrast"
    proc_code = "72148"
    payer = "Medicare (CMS)"

    print(f"\n{BOLD}[2/5] Patient Encounter & Safety Guard Scanner...{RESET}")
    print(f"  Requested Procedure: {CYAN}{proc_name}{RESET} (Code: {CYAN}{proc_code}{RESET})")
    print(f"  Target Payer:        {CYAN}{payer}{RESET}")

    phi_res = phi_guard.scan(sample_note)
    if phi_res.is_safe:
        print(f"  {GREEN}✓ PHI Guard Status: SAFE (Zero real patient identifiers detected){RESET}")
    else:
        print(f"  {RED}✗ PHI Guard Alert: {phi_res.summary}{RESET}")
        sys.exit(1)

    # Step 3: Run Agent State Machine
    print(f"\n{BOLD}[3/5] Executing State-Machine Agent...{RESET}")
    t0 = time.time()
    decision = agent.run(
        clinical_note=sample_note,
        procedure_name=proc_name,
        procedure_code=proc_code,
        payer=payer,
    )
    elapsed_ms = (time.time() - t0) * 1000

    print(f"  Matched Policy:   {CYAN}{decision.policy_id}{RESET}")
    rec_color = GREEN if decision.overall_recommendation.value == "LIKELY_APPROVABLE" else RED
    print(f"  Overall Outcome:  {rec_color}{BOLD}{decision.overall_recommendation.value}{RESET} (Confidence: {decision.confidence_score * 100:.0f}%)")
    print(f"  Execution Time:   {DIM}{elapsed_ms:.1f}ms{RESET}")

    # Step 4: Display Criteria Checklist with Verified Offsets
    print(f"\n{BOLD}[4/5] Discrete Criteria Evaluation & Quote Verification:{RESET}")
    print(f"{'-' * 80}")
    for idx, crit in enumerate(decision.criteria_results, 1):
        status_str = f"{GREEN}[MET]{RESET}" if crit.status.value == "MET" else f"{RED}[NOT MET]{RESET}" if crit.status.value == "NOT_MET" else f"{YELLOW}[INSUFFICIENT INFO]{RESET}"
        print(f"{idx}. {status_str} {BOLD}{crit.criterion_title}{RESET} ({crit.criterion_id})")
        if crit.evidence_quote:
            offset_str = f" [Chars: {crit.char_start}:{crit.char_end}]" if crit.char_start is not None else ""
            verified_badge = f"{GREEN}✓ Exact Substring Verified{RESET}" if crit.is_verified_substring else f"{RED}✗ Unverified{RESET}"
            print(f"   Evidence Quote:{offset_str} \"{CYAN}{crit.evidence_quote}{RESET}\"")
            print(f"   Verification:   {verified_badge}")
        else:
            print(f"   Evidence Quote: {DIM}[None documented in encounter note]{RESET}")
        print(f"   Rationale:      {DIM}{crit.reasoning}{RESET}\n")

    # Step 5: Draft Request Letter
    print(f"{BOLD}[5/5] Synthesized Prior Authorization Request Packet Preview:{RESET}")
    print(f"{'-' * 80}")
    preview_lines = decision.draft_letter.split("\n")[:18]
    for line in preview_lines:
        print(f"  {line}")
    print(f"  {DIM}... [remainder of packet truncated for preview] ...{RESET}")
    print(f"{'-' * 80}")

    print(f"\n{GREEN}{BOLD}✓ Demo execution completed successfully.{RESET}")
    print(f"{CYAN}Launch the full Reviewer Workspace UI anytime with:{RESET} {BOLD}make run-ui{RESET}\n")


if __name__ == "__main__":
    run_demo()
