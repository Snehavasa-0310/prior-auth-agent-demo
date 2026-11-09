"""FastAPI application for Prior Authorization Copilot Service."""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agent.state_machine import PriorAuthStateMachineAgent
from src.agent.tools import PriorAuthTools
from src.core.phi import PHIGuard
from src.policy.loader import load_and_index_policies
from src.policy.schemas import StructuredPolicy
from src.retrieval.hybrid import HybridPolicyRetriever
from src.storage.repository import CaseRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("prior-auth-api")

# Global instances initialized on startup
repository: CaseRepository | None = None
retriever: HybridPolicyRetriever | None = None
policies_cache: list[StructuredPolicy] = []
agent: PriorAuthStateMachineAgent | None = None
phi_guard = PHIGuard()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global repository, retriever, policies_cache, agent
    logger.info("Initializing Prior Auth Service resources...")
    repository = CaseRepository()
    policies_dir = Path(os.getenv("POLICIES_DIR", "data/policies"))
    retriever, policies_cache, _ = load_and_index_policies(policies_dir)
    tools = PriorAuthTools(retriever=retriever)
    agent = PriorAuthStateMachineAgent(tools=tools)
    logger.info(f"Loaded and indexed {len(policies_cache)} coverage policies.")
    yield
    logger.info("Shutting down Prior Auth Service.")


app = FastAPI(
    title="Prior Authorization Agent API",
    version="1.0.0",
    description="Safety-guarded, deterministic Prior Authorization copilot agent with exact substring citation verification.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID & Logging Middleware
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


# Auth dependency
def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    expected_key = os.getenv("API_KEY", "dev-prior-auth-key")
    if os.getenv("REQUIRE_API_KEY", "false").lower() == "true":
        if not x_api_key or x_api_key != expected_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key header.",
            )
    return x_api_key or "anonymous"


# --- Request & Response Models ---
class SubmitCaseRequest(BaseModel):
    patient_id: str = Field(default="SYNTH-PATIENT", description="Synthetic patient identifier")
    procedure_name: str = Field(..., description="e.g. Lumbar Spine MRI without Contrast")
    procedure_code: str = Field(..., description="CPT or HCPCS code, e.g. 72148")
    payer: str = Field(default="Medicare (CMS)", description="Target insurance payer")
    clinical_note: str = Field(..., min_length=10, description="Raw clinical text")


class ReviewCaseRequest(BaseModel):
    action: str = Field(..., pattern="^(APPROVE|REJECT|REQUEST_INFO)$")
    reviewer_notes: str = Field(..., description="Mandatory clinician review rationale")
    edited_letter: str | None = None


# --- Endpoints ---
@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "prior-auth-agent",
        "version": "1.0.0",
        "policies_indexed": len(policies_cache),
        "disclaimer": "Demo only. Not medical or coverage advice.",
    }


@app.get("/policies", tags=["Policies"])
def list_policies(_: str = Depends(verify_api_key)):
    return [
        {
            "id": p.id,
            "title": p.title,
            "payer": p.payer,
            "policy_type": p.policy_type,
            "procedure_name": p.procedure_name,
            "cpt_codes": p.cpt_codes,
            "effective_date": p.effective_date,
            "source_url": p.source_url,
            "criteria_count": len(p.criteria),
        }
        for p in policies_cache
    ]


@app.post("/cases", status_code=status.HTTP_201_CREATED, tags=["Cases"])
def submit_case(req: SubmitCaseRequest, _: str = Depends(verify_api_key)):
    assert repository is not None
    assert agent is not None

    # Step 1: PHI Guard Check
    phi_check = phi_guard.scan(req.clinical_note)
    if not phi_check.is_safe:
        logger.warning(f"Submission rejected due to PHI detection: {phi_check.summary}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "PHI_DETECTED",
                "message": "Potential real Protected Health Information (PHI) detected in clinical note. Ingestion blocked.",
                "details": phi_check.summary,
            },
        )

    # Step 2: Create initial case record
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    repository.create_case(
        case_id=case_id,
        procedure_name=req.procedure_name,
        procedure_code=req.procedure_code,
        payer=req.payer,
        raw_clinical_note=req.clinical_note,
        patient_id=req.patient_id,
    )

    # Step 3: Run Prior Auth Agent State Machine
    decision = agent.run(
        clinical_note=req.clinical_note,
        procedure_name=req.procedure_name,
        procedure_code=req.procedure_code,
        payer=req.payer,
    )

    # Step 4: Persist decision & return case
    repository.save_decision(case_id, decision)
    case_data = repository.get_case(case_id)
    return case_data


@app.get("/cases", tags=["Cases"])
def list_cases(limit: int = 50, _: str = Depends(verify_api_key)):
    assert repository is not None
    return repository.list_cases(limit=limit)


@app.get("/cases/{case_id}", tags=["Cases"])
def get_case(case_id: str, _: str = Depends(verify_api_key)):
    assert repository is not None
    case_data = repository.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")
    return case_data


@app.post("/cases/{case_id}/review", tags=["Human-in-the-Loop Review"])
def review_case(case_id: str, req: ReviewCaseRequest, _: str = Depends(verify_api_key)):
    assert repository is not None
    case_data = repository.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found.")

    updated = repository.update_reviewer_action(
        case_id=case_id,
        action=req.action,
        reviewer_notes=req.reviewer_notes,
        edited_letter=req.edited_letter,
    )
    return updated
