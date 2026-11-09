# Production-Grade Prior Authorization Agent: Architecture & Plan

> **DISCLAIMER:** Demo only. Not medical or coverage advice. Do NOT use with real Protected Health Information (PHI).

---

## 1. Executive Summary & Problem Framing

Prior authorization (PA) represents an estimated \$30B+ in annual administrative waste across the US healthcare system. Providers spend hours manually scouring clinical records to justify procedures and medications against fragmented, complex payer coverage policies (such as CMS National/Local Coverage Determinations and commercial Clinical Coverage Guidelines). 

This project implements an enterprise-ready, deterministic, safety-guarded **Prior Authorization Copilot Agent**. The agent assists human clinical reviewers by:
1. Identifying relevant payer coverage policies through hybrid retrieval (dense vector embeddings + BM25/FTS merged with Reciprocal Rank Fusion).
2. Decomposing policies into discrete, structured clinical criteria with Pydantic schemas.
3. Extracting clinical facts and mapping ICD-10/RxNorm codes while preserving exact character offsets from the raw note.
4. Evaluating each criterion using a deterministic state machine and verifying that every supporting citation is an exact, character-level substring of the input clinical note. If no verifiable quote exists, the agent strictly falls back to `INSUFFICIENT_INFO`.
5. Generating a structured prior authorization request packet and letter.
6. Enforcing a strict Human-In-The-Loop (HITL) gate: the system **never** makes autonomous final decisions.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer ["Client & Interface Layer"]
        UI["Streamlit Reviewer Dashboard<br/>(Visual Citation Inspector, Letter Editor)"]
        API["FastAPI REST Service<br/>(API Key Auth, OpenAPI, Audit Trails)"]
    end

    subgraph GuardLayer ["Ingestion & Safety Layer"]
        PHIGuard["PHI Detector Guard<br/>(Regex + Entity Scanners for SSN, MRN, Phone, Email)"]
        RawNote["Synthetic Clinical Note<br/>(Messy notes: typos, abbreviations, contradictions)"]
    end

    subgraph RetrievalLayer ["Policy Understanding & Hybrid RAG"]
        PolicyDB[("Policy Store<br/>8+ CMS/Commercial Policies")]
        DenseVec["Vector Index<br/>(pgvector / Dense Cosine Sim)"]
        KeywordFTS["Keyword Search<br/>(BM25 / PostgreSQL FTS)"]
        RRF["Reciprocal Rank Fusion (RRF)<br/>+ Optional Cross-Encoder"]
        CriteriaExtractor["Criteria Extractor<br/>(Structured Pydantic Checklist)"]
    end

    subgraph AgentLayer ["Deterministic State Machine Orchestrator"]
        FactExtractor["Clinical Fact Extractor<br/>(Diagnoses, Treatments, Durations, Labs)"]
        CodeNormalizer["Code Normalizer<br/>(ICD-10-CM / RxNorm Public Dictionaries)"]
        CriterionEvaluator["Criterion Evaluator Tool<br/>(MET / NOT_MET / INSUFFICIENT_INFO)"]
        QuoteVerifier{"Deterministic<br/>Quote Verifier<br/>(Exact Substring Check)"}
        DecisionAggregator["Decision Engine<br/>(LIKELY_APPROVABLE / NEEDS_MORE_INFO / LIKELY_DENIED)"]
        LetterDrafter["Letter Synthesis Tool<br/>(Claims Linked to Verified Quotes)"]
    end

    subgraph StorageLayer ["Persistence & Governance"]
        CaseRepo[("PostgreSQL / SQLite Dual Store<br/>Cases, Audit Events, Criteria Results")]
        AuditLog["Immutable Event Log<br/>(Prompts, Latencies, Tool Invocations, Model IDs)"]
    end

    subgraph HITLLayer ["Human-In-The-Loop Approval"]
        ReviewerAction{"Human Reviewer Decision"}
        Approve["APPROVED_BY_REVIEWER"]
        Reject["REJECTED_BY_REVIEWER"]
        RequestInfo["ADDITIONAL_CLINICALS_REQUESTED"]
    end

    %% Data Flow
    RawNote --> PHIGuard
    PHIGuard -->|Pass| API
    PHIGuard -->|Fail: Detected Real PHI| RejectBlock["HTTP 422: Potential Real Identifier Blocked"]
    
    API --> FactExtractor
    FactExtractor --> CodeNormalizer
    
    API --> DenseVec & KeywordFTS
    DenseVec & KeywordFTS --> RRF
    RRF --> PolicyDB
    PolicyDB --> CriteriaExtractor
    
    CriteriaExtractor --> CriterionEvaluator
    FactExtractor --> CriterionEvaluator
    CriterionEvaluator --> QuoteVerifier
    
    QuoteVerifier -->|Verified Substring| DecisionAggregator
    QuoteVerifier -->|Substring Missing / Mismatched| ForceInsufficient["Enforce INSUFFICIENT_INFO"]
    ForceInsufficient --> DecisionAggregator
    
    DecisionAggregator --> LetterDrafter
    LetterDrafter --> StorageLayer
    
    API <--> UI
    UI --> ReviewerAction
    ReviewerAction --> Approve & Reject & RequestInfo
    ReviewerAction --> AuditLog
```

---

## 3. Data Model Specification

```mermaid
erDiagram
    CASE {
        string id PK
        string procedure_name
        string procedure_code
        string payer_name
        text raw_clinical_note
        string status
        string overall_recommendation
        float confidence_score
        text draft_letter
        text reviewer_notes
        timestamp created_at
        timestamp updated_at
    }

    POLICY {
        string id PK
        string title
        string payer
        string procedure_code
        string category
        text full_text
        string source_url
        string effective_date
    }

    POLICY_CHUNK {
        string id PK
        string policy_id FK
        string section_title
        text chunk_text
        int chunk_index
        float_array embedding
    }

    CRITERION {
        string id PK
        string policy_id FK
        string title
        text description
        string criterion_type
        text required_evidence_description
        boolean is_mandatory
    }

    CASE_CRITERION_RESULT {
        string id PK
        string case_id FK
        string criterion_id FK
        string status
        text evidence_quote
        int quote_char_start
        int quote_char_end
        boolean quote_verified
        text reasoning
        float confidence
    }

    CLINICAL_FACT {
        string id PK
        string case_id FK
        string category
        string term
        string normalized_code
        string code_system
        text raw_mention
        int char_start
        int char_end
    }

    AUDIT_EVENT {
        string id PK
        string case_id FK
        string step_name
        string tool_name
        json input_payload
        json output_payload
        string model_name
        float latency_ms
        timestamp timestamp
    }

    CASE ||--o{ CASE_CRITERION_RESULT : evaluates
    CASE ||--o{ CLINICAL_FACT : extracts
    CASE ||--o{ AUDIT_EVENT : logs
    POLICY ||--o{ POLICY_CHUNK : contains
    POLICY ||--o{ CRITERION : defines
    CRITERION ||--o{ CASE_CRITERION_RESULT : instantiated_in
```

### Core Entities & States
1. **Case Status**: `SUBMITTED`, `ANALYZING`, `ANALYZED`, `UNDER_REVIEW`, `APPROVED_BY_REVIEWER`, `REJECTED`
2. **Criterion Status**: `MET`, `NOT_MET`, `INSUFFICIENT_INFO`
3. **Overall Recommendation**: `LIKELY_APPROVABLE`, `NEEDS_MORE_INFO`, `LIKELY_DENIED`
4. **Invariant 1 (PHI Invariant)**: Ingestion halts immediately if SSN, direct phone, or non-synthetic identity markers are flagged.
5. **Invariant 2 (Evidence Invariant)**: A criterion status can be `MET` **if and only if** `evidence_quote` is an exact substring of `raw_clinical_note` (`raw_note[start:end] == evidence_quote`). If substring check fails or quote is absent, status is coerced to `INSUFFICIENT_INFO`.

---

## 4. Phase Breakdown & Implementation Task List

| Phase | Milestone & Scope | Key Artifacts |
|---|---|---|
| **Phase 1** | Repo setup, public policy curation (8 policies), synthetic dataset generation (100+ cases with ground truth) | `data/policies/*.json`, `data/synthetic_notes.jsonl`, `docs/DATA_NOTES.md`, `src/core/phi.py` |
| **Phase 2** | Chunking, hybrid search (dense + BM25 with RRF), and criteria extractor with Pydantic validation and caching | `src/retrieval/`, `src/policy/`, `tests/test_retrieval.py` |
| **Phase 3** | Clinical note fact extraction, ICD-10/RxNorm normalization, character offset alignment | `src/clinical/`, `data/terminology/`, `tests/test_clinical.py` |
| **Phase 4** | Prior Auth State Machine Agent with tools, exact quote verification, decision logic, letter drafting, and audit logging | `src/agent/`, `src/tools/`, `tests/test_agent.py`, `tests/test_quote_verification.py` |
| **Phase 5** | FastAPI endpoints (`/cases`, `/review`, `/policies`, `/health`), API key auth, and Streamlit Reviewer Workspace | `src/api/`, `src/ui/`, `tests/test_api.py` |
| **Phase 6** | Comprehensive Evaluation Suite: 100+ test cases, 20+ edge cases, Recall@k, per-criterion F1, critical error rate, faithfulness judge, ablations, `make eval` | `eval/`, `eval/results/`, `Makefile`, `tests/test_eval_smoke.py` |
| **Phase 7** | Quality, Docker/compose, GitHub Actions, Makefile, complete documentation, weaknesses, and interview presentation | `Dockerfile`, `docker-compose.yml`, `docs/DESIGN_DECISIONS.md`, `docs/LIMITATIONS.md`, `README.md` |

---

## 5. Technology Choices & Justification

- **No Heavy Framework Abstractions**: No LangChain / LlamaIndex wrappers. Pure Python 3.11 with explicit typing, Pydantic v2 schemas, and standard async design.
- **Hybrid Search with RRF**: Healthcare documents feature both semantic concepts (e.g. "conservative management failed") and exact alphanumeric codes (e.g. `CPT 72148`, `ICD-10 M54.5`). Dense vectors alone miss exact code tokens; BM25 alone misses semantic synonyms. Reciprocal Rank Fusion ($RRF = \sum \frac{1}{60 + \text{rank}_i}$) balances both optimally.
- **Programmatic Exact-Quote Verifier**: Eliminates hallucinated approvals. The LLM output must pass a character-level slice check before any approval recommendation is computed.
- **Provider-Agnostic LLM Client**: Unified interface supporting OpenAI, Gemini, Anthropic, as well as an offline Deterministic Mock Engine so test suites and evaluations run identically in CI without network or API key dependencies.

