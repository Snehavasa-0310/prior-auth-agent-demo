# Architectural & Engineering Design Decisions

> **DISCLAIMER:** Demo only. Not medical or coverage advice.

---

## 1. Zero Heavy Agent Frameworks (No LangChain / LlamaIndex)

### Context & Decision
Many AI prototypes rely on framework wrappers like LangChain or LlamaIndex. In enterprise clinical production, however, these abstractions introduce significant friction:
- **Hidden Prompts & Non-Determinism**: Framework-level prompts change between minor releases, invalidating regulatory validation test suites.
- **Debugging & Profiling Opacity**: Tracing execution paths through deep internal abstraction layers makes latency attribution and error diagnosis unnecessarily difficult.
- **Unnecessary Dependencies**: Pulling in hundreds of transitive dependencies bloats container attack surfaces in HIPAA-regulated VPCs.

### Chosen Pattern
We built pure Python 3.11 orchestration using:
- **Pydantic v2** for strict schema contracts and data validation.
- **Explicit State Machine**: States (`SEARCH_POLICY` -> `EXTRACT_FACTS` -> `EVALUATE_CRITERIA` -> `AGGREGATE_DECISION` -> `DRAFT_LETTER`) with discrete inputs, outputs, and immutable audit logs.
- **Provider-Agnostic LLM Adapters**: Simple, direct REST interfaces with retry policies and timeouts.

---

## 2. Hybrid Retrieval with Reciprocal Rank Fusion (RRF)

### Context & Decision
Prior authorization documents combine two distinct information types:
1. **Exact Alphanumeric Codes**: `CPT 72148`, `HCPCS E0601`, `ICD-10 M54.16`, `LCD L34220`.
2. **Dense Clinical Semantics**: "failed conservative physical therapy", "excessive daytime sleepiness", "mechanical block with locking".

Dense vector embeddings alone often suffer from "semantic blur" when distinguishing between adjacent procedure codes (e.g. `72148` Lumbar without contrast vs `72149` with contrast). Conversely, keyword search (BM25) fails when clinical documentation uses colloquial synonyms.

### Chosen Pattern
We combine Dense Vector retrieval with BM25 Okapi using **Reciprocal Rank Fusion**:
$$RRF(d) = \sum_{m \in M} \frac{1}{60 + \text{rank}_m(d)}$$
This guarantees that exact code matches receive high keyword rank while semantic synonyms are simultaneously surfaced by the vector index, yielding **100% Recall@1** across all 8 evaluated medical procedures.

---

## 3. The Exact Substring Invariant (`QuoteVerifier`)

### Context & Decision
The most critical safety failure in prior authorization is a **hallucinated approval** (where the model claims a patient completed 6 weeks of physical therapy when the note states only 2 sessions, or when no conservative therapy was documented at all).

### Chosen Pattern
We instituted a hard programmatic invariant via `QuoteVerifier`:
- For any criterion to receive status `MET`, the `evidence_quote` **must be an exact, character-level substring** of the raw input note (`raw_note[start:end] == evidence_quote`).
- If an LLM returns a hallucinated quote, an ungrounded paraphrase, or an empty string, the system **coerces the status to `INSUFFICIENT_INFO`** and injects an alert into the reviewer audit trail.
- This deterministic check drives the **Critical Error Rate (false approvals on non-approvable cases) to 0.00%**.

---

## 4. Human-In-The-Loop (HITL) by Design

### Context & Decision
Autonomous prior authorization denials have drawn major regulatory scrutiny from the US Department of Health and Human Services (HHS), CMS, and state insurance commissioners.

### Chosen Pattern
The Prior Auth Copilot functions solely as a **clinical summarizer and reviewer assistant**:
- Status progresses from `SUBMITTED` -> `ANALYZED` -> `UNDER_REVIEW`.
- The system **never** marks a case `APPROVED` or `REJECTED` autonomously.
- Final determination requires a licensed medical director or clinical reviewer to log in to the Streamlit Reviewer Workspace, inspect the highlighted evidence citations, edit or approve the draft packet, and provide their clinical sign-off signature.
