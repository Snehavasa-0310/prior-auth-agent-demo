# Data Notes: Policies, Synthetic Datasets, and Licensing

> **DISCLAIMER:** Demo and portfolio research only. Not medical or coverage advice. All clinical notes in this repository are 100% synthetic.

---

## 1. Public Coverage Policies

This project incorporates 8 representative clinical coverage policies covering diverse medical specialties (orthopedics, radiology, endocrinology, sleep medicine, rheumatology, bariatric surgery, physical medicine & rehabilitation):

| Policy ID | Procedure / Drug | CPT / HCPCS | Payer Type | Source Type | URL Reference |
|---|---|---|---|---|---|
| `POL-CMS-L34220-LUMBAR-MRI` | Lumbar Spine MRI without Contrast | 72148 | Medicare | CMS LCD L34220 | [CMS Coverage Database](https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=34220) |
| `POL-COMM-CG-SURG-05-KNEE-ARTHRO` | Knee Arthroscopy with Meniscectomy | 29881 | Commercial | Anthem CG-SURG-05 | [Anthem Medical Policies](https://www.anthem.com/dam/medpolicies/abc/active/guidelines/gl_pw_d074312.html) |
| `POL-UHC-GLP1-DIABETES` | GLP-1 Receptor Agonists (Semaglutide) | J3490 | Commercial | UHC PA-PHARM-GLP1 | [UHC Provider Pharmacy Policy](https://www.uhcprovider.com/) |
| `POL-CMS-L36593-SLEEP-STUDY` | In-lab Polysomnography (Sleep Study) | 95810 | Medicare | CMS LCD L36593 | [CMS Coverage Database](https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=36593) |
| `POL-AETNA-CPB0315-BIOLOGICS-RA` | Adalimumab (Humira) for RA | J0135 | Commercial | Aetna CPB 0315 | [Aetna Clinical Policy Bulletins](https://www.aetna.com/cpb/medical/data/300_399/0315.html) |
| `POL-CMS-NCD100.1-BARIATRIC` | Roux-en-Y Bariatric Surgery | 43644 | Medicare | CMS NCD 100.1 | [CMS Coverage Database](https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=57) |
| `POL-CMS-L33718-CPAP` | CPAP Initial Authorization | E0601 | Medicare | CMS LCD L33718 | [CMS Coverage Database](https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=33718) |
| `POL-CMS-L35036-PT-EXTENSION` | Physical Therapy Extension | 97110 | Medicare | CMS LCD L35036 | [CMS Coverage Database](https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=35036) |

### Licensing of Policy Documents
- **CMS National & Local Coverage Determinations (NCDs/LCDs)**: Created by Medicare Administrative Contractors (MACs) under contract with CMS and are in the US Public Domain.
- **Commercial Payer Policies**: Publicly accessible clinical criteria published on insurer web portals for transparency under CMS interoperability and state mandate guidelines.

---

## 2. Synthetic Clinical Notes (`data/synthetic_notes.jsonl`)

The dataset comprises **104 synthetic cases** generated with known gold-standard ground truth:
- **Case Distribution**: Exactly 13 cases per policy covering:
  - Clear approvals (`LIKELY_APPROVABLE`): Full documentation of symptom duration, conservative treatment failures, diagnostic labs/imaging, and absence of exclusions.
  - Clear denials (`LIKELY_DENIED`): Acute uncomplicated symptoms, normal labs, refusal or lack of conservative treatment, non-covered indications.
  - Partial / missing information (`NEEDS_MORE_INFO`): Gaps in therapy duration, unconfirmed lab dates, telehealth visits without in-person exams.
- **Edge Cases & Stress Tests (21 Tricky Cases)**:
  - *Contradictions*: Patient self-report in HPI contradicted by physical therapy discharge records or lab reports.
  - *Missing Dates*: "Tried metformin in past for unknown duration"; "sleep test performed at outside clinic last year".
  - *Near Misses*: 4 weeks of physical therapy completed when policy demands >= 6 weeks; Epworth score of 9 when policy requires >= 10; BMI 34.2 when requirement is >= 35.
  - *Clinical Shorthand & Abbreviations*: `s/p`, `+ JLT medial`, `csDMARD`, `MTX`, `T2D`, `AHI`, `SLR + left`.
  - *Spelling & Typo Variations*: "conserative therapy", "experiancing numbness", "naproxin".

### Substring Invariant
Every ground-truth `evidence_quote` associated with a `MET` criterion is verified via continuous automated assertions to be a character-exact substring of the clinical note. No loose paraphrasing is admitted into the gold standard dataset.

---

## 3. Protected Health Information (PHI) & Privacy Safeguards

- **Strict Zero-PHI Guarantee**: All patient names (`David Miller`, `Margaret Evans`, etc.) are synthetically generated combinations of common census names. All dates of birth, MRNs (`SYNTH-***`), and dates are synthetic.
- **Automated PHI Ingestion Gate**: Every submission passing through the API or batch ingestion pipeline is evaluated by `src/core/phi.py`. Any attempt to pass unredacted SSNs, direct US phone numbers, emails, or real hospital MRNs immediately rejects the request with an HTTP 422 error.

---

## 4. Limitations

1. **Not a Licensed Medical Device**: This software has not been submitted to the US FDA for clearance as Software as a Medical Device (SaMD) under 21 CFR 860.
2. **Deterministic Fallback**: In clinical practice, edge cases require medical director clinical judgment. The agent explicitly stops at `NEEDS_MORE_INFO` or routes to a human reviewer.
3. **Payer Variation**: Payer policies change quarterly. Production deployment requires automated webhook ingestion of CMS MUE/LCD updates and payer policy revision feeds.

