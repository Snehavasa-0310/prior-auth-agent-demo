# System Limitations & Honest Weaknesses

> **DISCLAIMER:** Demo only. Not medical or coverage advice. Do NOT use with real Protected Health Information (PHI).

---

## 1. Single-Document Scope vs Multi-Encounter Longitudinal Records

### Current Reality
The current implementation evaluates a single consolidated clinical encounter note containing subjective history, physical exam findings, prior treatments, and diagnostic labs.

### In Production
Real prior authorization submissions span multiple distinct artifacts:
- Scanned, low-resolution PDF faxes from outside physical therapy clinics.
- Discharge summaries, operative notes, and physical therapy flowsheets with tabular checkmarks.
- Longitudinal EHR logs spanning 6-12 months across disparate health systems.

**Impact**: In production, an additional ingestion pipeline with clinical Document AI / OCR (e.g. AWS Textract, Google Document AI Healthcare Parser) and longitudinal timeline merging is required to aggregate evidence scattered across multiple documents.

---

## 2. Temporal & Discontinuous Negation Reasoning

### Current Reality
The `QuoteVerifier` guarantees that any quoted evidence is an exact substring of the clinical note. However, clinical language often contains discontinuous or temporal negations across distant paragraphs:
> *"Patient previously took metformin with good tolerance in 2021. However, after developing acute renal insufficiency last month (eGFR 24), metformin was permanently discontinued due to lactic acidosis risk."*

### In Production
A naive quote extractor might quote *"Patient previously took metformin with good tolerance"* without capturing the qualifying paragraph 20 lines later. Although our structured clinical fact extractor captures contraindications and lab values, complex multi-year clinical chronologies require explicit temporal event graphs.

---

## 3. Policy Churn & Quarterly Payer Revisions

### Current Reality
The repository contains 8 curated coverage policies derived from CMS LCDs/NCDs and commercial guidelines. These policies are indexed into the vector/BM25 knowledge base.

### In Production
US healthcare payers update coverage guidelines on monthly and quarterly cycles (e.g. changing HbA1c thresholds, requiring step therapy with biosimilars before originator biologics). 

**Impact**: Production deployment requires automated policy monitoring workers, webhook listeners on CMS MCD updates, and version-controlled criteria registries with automated regression testing before deploying policy updates into clinical production.

