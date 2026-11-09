# Prior Authorization Copilot: Comprehensive Evaluation Report

> **Evaluation Run Date:** Real Execution Benchmark across 100% Verified Synthetic Test Cases.
> **Safety Invariant:** All evidence citations are programmatically verified exact substrings.

## 1. Executive Summary & Core Safety Metrics

| Metric | Result | Benchmark Target | Status |
|---|---|---|---|
| **Critical Error Rate (False Approvals)** | **0.00%** (0/56) | < 1.0% | ✅ PASS |
| **Evidence Substring Faithfulness** | **100.00%** | 100.0% | ✅ PASS |
| **Overall Decision Accuracy** | **85.58%** | > 90.0% | ❌ FAIL |
| **Criterion Classification Macro F1** | **0.8140** | > 0.8500 | ❌ FAIL |
| **Abstention Quality (Recall on Missing Info)** | **94.44%** | > 85.0% | ✅ PASS |
| **Policy Retrieval Recall@1** | **100.00%** | > 95.0% | ✅ PASS |
| **Latency (p50 / p95)** | **0.3ms / 0.5ms** | < 250ms | ✅ PASS |

> [!IMPORTANT]
> **Zero Critical Error Rate**: In healthcare prior authorization, falsely approving a non-covered or clinically unindicated request creates severe liability. The system achieved **0.00%** false approvals on non-approvable cases thanks to the QuoteVerifier exact substring guard.

## 2. Per-Criterion Classification Performance

| Criterion Class | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| `MET` | 1.0000 | 0.9293 | 0.9634 | 198 |
| `NOT_MET` | 0.9474 | 0.7692 | 0.8491 | 117 |
| `INSUFFICIENT_INFO` | 0.4722 | 0.9444 | 0.6296 | 36 |

### Criterion Confusion Matrix
| True \ Pred | MET | NOT_MET | INSUFFICIENT_INFO |
|---|---|---|---|
| **MET** | 184 | 3 | 11 |
| **NOT_MET** | 0 | 90 | 27 |
| **INSUFFICIENT_INFO** | 0 | 2 | 34 |

## 3. Systematic Ablation Studies

### A. Retrieval Strategy Ablation
| Strategy | Recall@1 | Recall@3 | MRR |
|---|---|---|---|
| Hybrid (Dense + BM25 + RRF) | 100.0% | 100.0% | 1.0000 |
| Dense Vector Only | 100.0% | 100.0% | 1.0000 |
| BM25 Keyword Only | 100.0% | 100.0% | 1.0000 |
| Hybrid + Cross-Encoder Reranker | 100.0% | 100.0% | 1.0000 |

### B. Architecture & Safety Guard Ablation
| Architecture | Overall Accuracy | Critical Error Rate (False Approvals) | Substring Faithfulness |
|---|---|---|---|
| **State-Machine Agent (Ours)** | 85.6% | 0.0% | 100.0% |
| **Single-Pass Monolithic Baseline** | 83.7% | 30.4% | 84.8% |

## 4. Dataset Distribution & Edge Cases
- **Total Gold-Standard Cases:** 104
- **Explicit Tricky / Edge Cases:** 21 (Contradictions, Near-Misses, Missing Dates, Clinical Abbreviations)
- **Specialties Evaluated:** Spine Surgery, Knee Orthopedics, Diabetes/Endocrinology, Sleep Medicine, Rheumatology, Bariatrics, CPAP, Physical Therapy.
