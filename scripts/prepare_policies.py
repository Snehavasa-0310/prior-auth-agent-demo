"""Policy generation and preparation script.

Builds structured coverage policy documents for at least 8 standard procedures
based on CMS Local/National Coverage Determinations (LCD/NCD) and public payer policies.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

POLICIES: list[dict[str, Any]] = [
    {
        "id": "POL-CMS-L34220-LUMBAR-MRI",
        "title": "Magnetic Resonance Imaging (MRI) of the Lumbar Spine",
        "payer": "Medicare (CMS)",
        "policy_type": "LCD",
        "policy_number": "LCD L34220",
        "procedure_name": "Lumbar Spine MRI without Contrast",
        "cpt_codes": ["72148", "72149"],
        "icd10_codes": ["M54.50", "M54.16", "M51.26", "G83.4"],
        "effective_date": "2023-01-01",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=34220",
        "summary": "Covers non-emergent MRI of the lumbar spine after documented failure of at least 6 weeks of conservative management, or immediately in presence of red flag signs (cauda equina syndrome, progressive neurological deficit, active cancer history, infection).",
        "sections": [
            {
                "title": "Indications and Limitations of Coverage",
                "content": (
                    "Lumbar spine MRI (CPT 72148) is considered medically necessary when ANY of the following criteria are met:\n"
                    "1. Red Flag Signs: Immediate MRI indicated for progressive neurological deficit (e.g. progressive motor weakness), "
                    "suspicion of cauda equina syndrome (bowel/bladder dysfunction, saddle anesthesia), known active malignancy with new back pain, "
                    "or clinical suspicion of spinal infection/osteomyelitis (fever, elevated ESR/CRP, IV drug use history).\n"
                    "2. Radiculopathy with Failure of Conservative Therapy: Severe radiating radicular pain persisting after a minimum of "
                    "6 weeks of active documented conservative management (including physical therapy, structured home exercise, NSAIDs or neuropathic pain medication).\n"
                    "3. Post-surgical evaluation: Persistent or recurrent symptoms following lumbar spine surgery within 12 months."
                ),
            },
            {
                "title": "Exclusions and Non-Covered Scenarios",
                "content": (
                    "MRI is not covered for uncomplicated acute low back pain (< 6 weeks duration) without radicular symptoms or neurological signs. "
                    "Repeat MRI within 6 months without new neurological deficits or acute trauma is considered not medically necessary."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-LUMBAR-01",
                "title": "Red Flag Signs or Neurological Emergency",
                "criterion_type": "INCLUSION",
                "description": "Documented acute red flag symptoms: cauda equina syndrome (bowel/bladder incontinence, saddle anesthesia), progressive motor weakness, or active malignancy.",
                "required_evidence": "Physical exam or clinical documentation showing progressive motor deficit, bowel/bladder dysfunction, or oncologic history with localized bone pain.",
                "is_mandatory": False,
            },
            {
                "id": "CRIT-LUMBAR-02",
                "title": "Documented Radicular Symptoms",
                "criterion_type": "INCLUSION",
                "description": "Presence of true radicular symptoms radiating below the knee in a dermatomal distribution with positive straight leg raise or nerve root irritation signs.",
                "required_evidence": "Documented radiating nerve root pain or positive neural tension sign (positive straight leg raise, dermatomal sensory loss, or reflex asymmetry).",
                "is_mandatory": False,
            },
            {
                "id": "CRIT-LUMBAR-03",
                "title": "Failure of Conservative Therapy (>= 6 weeks)",
                "criterion_type": "CONSERVATIVE_THERAPY",
                "description": "Trial of at least 6 consecutive weeks of conservative management consisting of formal physical therapy, prescribed medication (NSAIDs or oral steroids or neuropathic agents), and activity modification within the past 6 months.",
                "required_evidence": "Clinical notes or therapy discharge summary specifying at least 6 weeks of PT/medication trial with dates and lack of functional improvement.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-LUMBAR-04",
                "title": "No Uncomplicated Non-Specific Back Pain Exclusion",
                "criterion_type": "EXCLUSION",
                "description": "Exclusion applies if pain is non-specific axial lower back pain of less than 6 weeks duration without neurologic involvement.",
                "required_evidence": "Rule out non-specific axial back pain lacking duration or neurological findings.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-COMM-CG-SURG-05-KNEE-ARTHRO",
        "title": "Knee Arthroscopy and Meniscectomy",
        "payer": "Anthem / Commercial Payer",
        "policy_type": "COMMERCIAL_POLICY",
        "policy_number": "CG-SURG-05",
        "procedure_name": "Arthroscopy, knee, surgical; with meniscectomy",
        "cpt_codes": ["29881", "29880"],
        "icd10_codes": ["M23.22", "M23.23", "M23.32", "S83.24"],
        "effective_date": "2023-04-01",
        "source_url": "https://www.anthem.com/dam/medpolicies/abc/active/guidelines/gl_pw_d074312.html",
        "summary": "Outpatient knee arthroscopy with partial meniscectomy requires confirmed mechanical symptoms (locking, catching), documented physical examination signs (McMurray or joint line tenderness), MRI confirmation of tear, and at least 6-12 weeks of failed conservative therapy in degenerative cases without acute mechanical block.",
        "sections": [
            {
                "title": "Clinical Indications",
                "content": (
                    "Knee arthroscopy with meniscectomy (CPT 29881) is medically necessary when ALL of the following are met:\n"
                    "1. Subjective symptoms of knee pain accompanied by mechanical symptoms (true locking, catching, or giving way).\n"
                    "2. Objective physical examination findings including joint line tenderness and positive provocative test (e.g. McMurray test or Thessaly test).\n"
                    "3. Preoperative MRI demonstrating a tear of the meniscus in an area accessible to repair or resection.\n"
                    "4. For degenerative tears: Failure of at least 6 weeks of non-operative treatment including physical therapy, NSAIDs, and/or intra-articular steroid injections (not required for acute displaced bucket-handle tear with locked knee)."
                ),
            },
            {
                "title": "Contraindications and Exclusions",
                "content": (
                    "Arthroscopy is not covered for isolated osteoarthritis of the knee without identifiable mechanical symptoms or when advanced Kellgren-Lawrence grade IV joint space narrowing is present."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-KNEE-01",
                "title": "Mechanical Symptoms (Locking, Catching, Giving Way)",
                "criterion_type": "INCLUSION",
                "description": "Patient reports clear mechanical symptoms such as true joint locking, intermittent catching, or unstable giving way.",
                "required_evidence": "History of present illness documenting specific mechanical knee symptoms.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-KNEE-02",
                "title": "Physical Exam Signs of Meniscal Pathology",
                "criterion_type": "INCLUSION",
                "description": "Documented joint line tenderness and positive provocative test (McMurray, Thessaly, or Apley grind).",
                "required_evidence": "Physical examination section recording localized joint line tenderness and positive McMurray sign.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-KNEE-03",
                "title": "Diagnostic Imaging Confirmation (MRI)",
                "criterion_type": "DIAGNOSTIC",
                "description": "Knee MRI demonstrating meniscal tear without isolated end-stage osteoarthritis.",
                "required_evidence": "MRI report quote confirming tear of medial or lateral meniscus.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-KNEE-04",
                "title": "Conservative Management (>= 6 weeks) unless Acute Block",
                "criterion_type": "CONSERVATIVE_THERAPY",
                "description": "Trial of at least 6 weeks of conservative management including PT, NSAIDs, or corticosteroid injection, unless presenting with an acute locked knee.",
                "required_evidence": "Records showing at least 6 weeks of structured physical therapy or non-operative interventions.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-UHC-GLP1-DIABETES",
        "title": "Glucagon-Like Peptide-1 (GLP-1) Receptor Agonists for Type 2 Diabetes",
        "payer": "UnitedHealthcare / Commercial",
        "policy_type": "COMMERCIAL_POLICY",
        "policy_number": "PA-PHARM-GLP1-2023",
        "procedure_name": "Semaglutide / Dulaglutide / Tirzepatide (GLP-1)",
        "cpt_codes": ["J3490", "J1627"],
        "icd10_codes": ["E11.65", "E11.9", "E11.21"],
        "effective_date": "2023-07-01",
        "source_url": "https://www.uhcprovider.com/content/dam/provider/docs/public/prior-auth/drugs-pharmacy/commercial/GLP-1-Receptor-Agonists.pdf",
        "summary": "Prior authorization for GLP-1 receptor agonist therapy requires confirmed diagnosis of Type 2 Diabetes Mellitus, documented baseline HbA1c >= 7.0% within the past 90 days, and documented failure or contraindication/intolerance to Metformin at maximally tolerated dose for at least 90 days.",
        "sections": [
            {
                "title": "Initial Authorization Criteria",
                "content": (
                    "Initial approval of GLP-1 receptor agonists (e.g., Ozempic, Trulicity, Mounjaro) requires:\n"
                    "1. Confirmed diagnosis of Type 2 Diabetes Mellitus (ICD-10 E11 series).\n"
                    "2. Baseline Glycated Hemoglobin (HbA1c) level >= 7.0% (or target not achieved per clinical guidelines) documented within the prior 90 days.\n"
                    "3. Trial of Metformin for at least 90 days with inadequate glycemic control, OR documented clinical contraindication (e.g. eGFR < 30 mL/min/1.73m2, severe lactic acidosis history) or documented gastrointestinal intolerance.\n"
                    "4. Patient is not taking another GLP-1 receptor agonist or DPP-4 inhibitor concurrently."
                ),
            },
            {
                "title": "Exclusions",
                "content": (
                    "Coverage is excluded when used solely for weight loss in non-diabetic patients without specific plan weight-management riders, or for Type 1 Diabetes Mellitus."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-GLP1-01",
                "title": "Confirmed Type 2 Diabetes Mellitus Diagnosis",
                "criterion_type": "INCLUSION",
                "description": "Patient has an established diagnosis of Type 2 Diabetes Mellitus.",
                "required_evidence": "Clinical note documenting diagnosis of Type 2 Diabetes Mellitus (T2DM) or ICD-10 E11 code.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-GLP1-02",
                "title": "Elevated HbA1c (>= 7.0%) within 90 days",
                "criterion_type": "DIAGNOSTIC",
                "description": "Laboratory value of HbA1c >= 7.0% documented within the preceding 90 days.",
                "required_evidence": "Lab value showing HbA1c percentage and recent date within 90 days.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-GLP1-03",
                "title": "Metformin Trial (>= 90 days) or Documented Contraindication",
                "criterion_type": "CONSERVATIVE_THERAPY",
                "description": "Documented trial of metformin at >= 1000 mg/day for at least 90 days with failure to reach glycemic target, OR documented intolerance or contraindication (e.g. eGFR < 30).",
                "required_evidence": "Note detailing metformin trial duration and intolerance or insufficient response.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-GLP1-04",
                "title": "Absence of DPP-4 Inhibitor Dual Therapy Exclusion",
                "criterion_type": "EXCLUSION",
                "description": "Patient is not concurrently prescribed or taking a DPP-4 inhibitor (e.g. sitagliptin, linagliptin).",
                "required_evidence": "Medication list showing discontinuation or absence of DPP-4 inhibitors.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-CMS-L36593-SLEEP-STUDY",
        "title": "Polysomnography and Sleep Testing",
        "payer": "Medicare (CMS)",
        "policy_type": "LCD",
        "policy_number": "LCD L36593",
        "procedure_name": "Polysomnography (Sleep Study), in-lab",
        "cpt_codes": ["95810", "95811"],
        "icd10_codes": ["G47.33", "G47.30"],
        "effective_date": "2023-01-01",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=36593",
        "summary": "Covers diagnostic in-laboratory polysomnography (CPT 95810) for suspected Obstructive Sleep Apnea (OSA) when comprehensive clinical evaluation demonstrates symptoms of excessive daytime sleepiness (Epworth Sleepiness Scale score >= 10 or loud snoring/witnessed apneas) and home sleep apnea testing is contraindicated or indeterminate.",
        "sections": [
            {
                "title": "Coverage Indications",
                "content": (
                    "In-lab attended polysomnography (CPT 95810) is covered for adult patients when ALL of the following criteria are met:\n"
                    "1. Clinical evaluation by physician documenting symptoms of sleep-disordered breathing: habitual loud snoring, witnessed apneas, choking/gasping, or excessive daytime sleepiness.\n"
                    "2. Validated daytime sleepiness assessment such as Epworth Sleepiness Scale (ESS) score >= 10.\n"
                    "3. Indication for in-laboratory testing over unattended home sleep apnea test (HSAT), such as significant comorbid cardiorespiratory disease, neuromuscular weakness, hypoventilation risk, or prior inconclusive HSAT."
                ),
            },
            {
                "title": "Non-Coverage",
                "content": (
                    "Sleep testing is not covered for chronic uncomplicated insomnia or restless legs syndrome without sleep-related breathing disorder symptoms."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-SLEEP-01",
                "title": "Documented Symptoms of Sleep-Disordered Breathing",
                "criterion_type": "INCLUSION",
                "description": "Patient exhibits documented symptoms of habitual loud snoring, nocturnal gasping/choking, or witnessed apneas.",
                "required_evidence": "Clinical history recording snoring, witnessed apneas, or nocturnal waking with gasping.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-SLEEP-02",
                "title": "Excessive Daytime Sleepiness (Epworth Score >= 10)",
                "criterion_type": "DIAGNOSTIC",
                "description": "Epworth Sleepiness Scale (ESS) documented with score of 10 or greater.",
                "required_evidence": "Clinical documentation of Epworth Sleepiness Scale score >= 10.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-SLEEP-03",
                "title": "Indication for In-Lab Polysomnography vs Home Sleep Test",
                "criterion_type": "INCLUSION",
                "description": "Presence of comorbid cardiopulmonary disease, morbid obesity with hypoventilation, neuromuscular disorder, or failed/inconclusive home sleep test.",
                "required_evidence": "Note detailing reason why home sleep apnea testing is contraindicated or prior inconclusive test.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-AETNA-CPB0315-BIOLOGICS-RA",
        "title": "Biologic DMARDs for Rheumatoid Arthritis",
        "payer": "Aetna",
        "policy_type": "COMMERCIAL_POLICY",
        "policy_number": "CPB 0315",
        "procedure_name": "Adalimumab (Humira) / Anti-TNF Biologic",
        "cpt_codes": ["J0135", "Q5103"],
        "icd10_codes": ["M05.79", "M06.0", "M06.9"],
        "effective_date": "2023-09-01",
        "source_url": "https://www.aetna.com/cpb/medical/data/300_399/0315.html",
        "summary": "Covers subcutaneous adalimumab for moderate to severe active Rheumatoid Arthritis following documented failure, intolerance, or contraindication to a 3-month trial of conventional synthetic DMARD (methotrexate, leflunomide, or sulfasalazine) and negative baseline tuberculosis screening.",
        "sections": [
            {
                "title": "Indications for Biologic Therapy",
                "content": (
                    "Adalimumab (CPT J0135) is considered medically necessary for adult patients with Rheumatoid Arthritis when:\n"
                    "1. Diagnosis of moderate to severe active Rheumatoid Arthritis established by rheumatologist (based on swollen/tender joint count, elevated ESR/CRP, positive RF or anti-CCP antibodies).\n"
                    "2. Inadequate response to or intolerance/contraindication to at least one conventional synthetic disease-modifying antirheumatic drug (csDMARD), typically oral methotrexate at target doses (>= 15 mg/week) for at least 12 weeks.\n"
                    "3. Documentation of screening for latent tuberculosis infection (PPD skin test or IGRA / QuantiFERON Gold) with negative result prior to initiation."
                ),
            },
            {
                "title": "Exclusions",
                "content": (
                    "Concurrent use with other biologic DMARDs or targeted synthetic DMARDs (JAK inhibitors). Active serious systemic infection."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-RA-01",
                "title": "Moderate to Severe Active Rheumatoid Arthritis",
                "criterion_type": "INCLUSION",
                "description": "Confirmed diagnosis of moderate to severe active RA with documented joint swelling, tenderness, and elevated inflammatory markers (ESR or CRP).",
                "required_evidence": "Rheumatology note confirming active RA, swollen joint counts, and elevated CRP/ESR.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-RA-02",
                "title": "Failure or Intolerance to csDMARD (Methotrexate >= 12 weeks)",
                "criterion_type": "CONSERVATIVE_THERAPY",
                "description": "Documented trial of at least 12 weeks of methotrexate (or other csDMARD like leflunomide) at therapeutic dosage with inadequate disease suppression or documented hepatotoxicity/intolerance.",
                "required_evidence": "Medication history recording >= 12 week trial of methotrexate with dates and lack of response or side effects.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-RA-03",
                "title": "Negative Latent Tuberculosis Screening",
                "criterion_type": "DIAGNOSTIC",
                "description": "Documented negative TB screening test (QuantiFERON-TB Gold or PPD) within the prior 12 months.",
                "required_evidence": "Laboratory or clinical note citing negative QuantiFERON Gold or negative PPD test.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-RA-04",
                "title": "Absence of Active Serious Infection or Biologic Duplication",
                "criterion_type": "EXCLUSION",
                "description": "No active untreated serious infection and no concurrent administration of another biologic or JAK inhibitor.",
                "required_evidence": "Review of systems confirming absence of active infection and singular biologic regimen.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-CMS-NCD100.1-BARIATRIC",
        "title": "Bariatric Surgery for Morbid Obesity",
        "payer": "Medicare (CMS)",
        "policy_type": "NCD",
        "policy_number": "NCD 100.1",
        "procedure_name": "Laparoscopic Roux-en-Y Gastric Bypass / Sleeve Gastrectomy",
        "cpt_codes": ["43644", "43775"],
        "icd10_codes": ["E66.01", "Z68.41", "Z68.42"],
        "effective_date": "2023-01-01",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/ncd.aspx?ncdid=57",
        "summary": "Bariatric surgery is covered for individuals with BMI >= 35 with at least one major obesity-related comorbidity (e.g. type 2 diabetes, severe sleep apnea, refractory hypertension) or BMI >= 40, who have completed a structured non-surgical weight loss program and psychological evaluation.",
        "sections": [
            {
                "title": "Indications",
                "content": (
                    "Open and laparoscopic Roux-en-Y gastric bypass and sleeve gastrectomy (CPT 43644, 43775) are covered when:\n"
                    "1. Body Mass Index (BMI) >= 35 kg/m2 with at least one severe obesity-related comorbid condition (Type 2 Diabetes, Obstructive Sleep Apnea, resistant hypertension), OR BMI >= 40 kg/m2 with or without comorbidities.\n"
                    "2. Documentation of prior participation in a structured physician-supervised or multidisciplinary medical weight loss program for at least 6 consecutive months within the prior 2 years.\n"
                    "3. Comprehensive multidisciplinary psychiatric/psychological clearance assessing patient stability and readiness for permanent dietary alterations."
                ),
            },
            {
                "title": "Contraindications",
                "content": (
                    "Untreated active substance abuse within 12 months, uncontrolled active psychiatric psychosis, or inability to adhere to lifelong nutritional supplementation."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-BARIATRIC-01",
                "title": "BMI Criterion (BMI >= 40 or BMI >= 35 with Comorbidity)",
                "criterion_type": "DIAGNOSTIC",
                "description": "Documented BMI >= 40, or BMI >= 35 with at least one serious obesity-related comorbidity (T2DM, OSA, hypertension).",
                "required_evidence": "Physical exam recording patient height, weight, and calculated BMI with comorbid conditions.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-BARIATRIC-02",
                "title": "Supervised Medical Weight Loss Program (>= 6 months)",
                "criterion_type": "CONSERVATIVE_THERAPY",
                "description": "Documented failure of at least 6 consecutive months of structured physician-supervised dietary and lifestyle modification program.",
                "required_evidence": "Clinical notes detailing monthly visits, diet plans, and weight trajectory across 6 months.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-BARIATRIC-03",
                "title": "Psychological Evaluation and Clearance",
                "criterion_type": "DIAGNOSTIC",
                "description": "Formal pre-bariatric psychological evaluation confirming absence of active substance abuse and psychological readiness.",
                "required_evidence": "Mental health evaluation report confirming clearance for bariatric surgery.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-CMS-L33718-CPAP",
        "title": "Continuous Positive Airway Pressure (CPAP) Therapy",
        "payer": "Medicare (CMS)",
        "policy_type": "LCD",
        "policy_number": "LCD L33718",
        "procedure_name": "Continuous Positive Airway Pressure Device",
        "cpt_codes": ["E0601"],
        "icd10_codes": ["G47.33"],
        "effective_date": "2023-01-01",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=33718",
        "summary": "Initial 12-week coverage of CPAP (HCPCS E0601) requires a diagnostic sleep test showing Apnea-Hypopnea Index (AHI) or Respiratory Disturbance Index (RDI) >= 15 events/hour, or AHI 5-14.9 events/hour with documented excessive daytime sleepiness, hypertension, or ischemic heart disease.",
        "sections": [
            {
                "title": "Coverage Criteria for Initial 12-Week Period",
                "content": (
                    "A single-level CPAP device (HCPCS E0601) is covered for adult patients with OSA when:\n"
                    "1. The patient had a face-to-face clinical evaluation prior to the sleep study.\n"
                    "2. The patient had a valid diagnostic sleep test (polysomnography or HSAT) showing:\n"
                    "   a. AHI or RDI >= 15 events per hour; OR\n"
                    "   b. AHI or RDI between 5 and 14.9 events per hour accompanied by documented excessive daytime sleepiness (ESS >= 10), impaired cognition, mood disorder, hypertension, or ischemic heart disease.\n"
                    "3. The patient and caregiver have received education on the use and maintenance of CPAP."
                ),
            },
            {
                "title": "Continued Coverage After 12 Weeks",
                "content": (
                    "Continued coverage past 90 days requires documented compliance: usage >= 4 hours per night on 70% of nights during a consecutive 30-day period."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-CPAP-01",
                "title": "Face-to-Face Clinical Evaluation",
                "criterion_type": "INCLUSION",
                "description": "Documented in-person face-to-face clinical evaluation with physician documenting sleep-related symptoms.",
                "required_evidence": "Clinical encounter note with history of sleep disturbance and physical exam.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-CPAP-02",
                "title": "Diagnostic Sleep Study with AHI Criteria",
                "criterion_type": "DIAGNOSTIC",
                "description": "Sleep test documenting AHI/RDI >= 15 events/hr, OR AHI 5-14.9 events/hr with documented daytime sleepiness, hypertension, or cardiovascular comorbidity.",
                "required_evidence": "Sleep study report stating exact AHI/RDI number and accompanying symptoms if AHI < 15.",
                "is_mandatory": True,
            },
        ],
    },
    {
        "id": "POL-CMS-L35036-PT-EXTENSION",
        "title": "Outpatient Physical Therapy Extension",
        "payer": "Medicare (CMS)",
        "policy_type": "LCD",
        "policy_number": "LCD L35036",
        "procedure_name": "Physical Therapy Extension (Therapeutic Exercise)",
        "cpt_codes": ["97110", "97140", "97530"],
        "icd10_codes": ["M25.561", "M54.5", "S83.511A"],
        "effective_date": "2023-01-01",
        "source_url": "https://www.cms.gov/medicare-coverage-database/view/lcd.aspx?lcdid=35036",
        "summary": "Authorizes extension of outpatient physical therapy services beyond initial 12 visits when documented re-evaluation demonstrates measurable objective functional progress towards specific functional goals and patient requires skilled care rather than maintenance home exercise.",
        "sections": [
            {
                "title": "Medical Necessity Requirements",
                "content": (
                    "Extension of physical therapy (CPT 97110, 97140) beyond initial authorized visits is covered when:\n"
                    "1. A formal physical therapy re-evaluation is performed within the last 30 days.\n"
                    "2. Objective measurable progress is documented (e.g. range of motion in degrees, strength grades, validated functional scoring such as Oswestry Disability Index, Lower Extremity Functional Scale).\n"
                    "3. Realistic, time-specific functional goals remain to be achieved.\n"
                    "4. The services require the unique skills of a licensed physical therapist and cannot be safely delivered via an independent home exercise program (maintenance therapy is non-covered)."
                ),
            },
            {
                "title": "Exclusions",
                "content": (
                    "Repetitive, non-skilled maintenance therapy where patient has plateaued with no documented functional gains over the preceding 30 days."
                ),
            },
        ],
        "criteria": [
            {
                "id": "CRIT-PT-01",
                "title": "Recent Physical Therapy Re-Evaluation (<= 30 days)",
                "criterion_type": "DIAGNOSTIC",
                "description": "Documented PT re-evaluation or progress report completed within the last 30 days.",
                "required_evidence": "Date and findings of physical therapy re-evaluation report.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-PT-02",
                "title": "Documented Measurable Objective Progress",
                "criterion_type": "INCLUSION",
                "description": "Objective data showing measurable functional gains (e.g., ROM degrees, strength 3/5 to 4/5, LEFS/Oswestry percentage improvement) compared to baseline.",
                "required_evidence": "Baseline vs current objective metrics showing functional improvement.",
                "is_mandatory": True,
            },
            {
                "id": "CRIT-PT-03",
                "title": "Ongoing Need for Skilled Care vs Maintenance",
                "criterion_type": "INCLUSION",
                "description": "Documentation justifying why ongoing skilled therapist intervention is required rather than independent transition to a home exercise program.",
                "required_evidence": "Therapist clinical rationale specifying complexity of skilled intervention required.",
                "is_mandatory": True,
            },
        ],
    },
]


def prepare_policies(target_dir: Path) -> list[Path]:
    """Write policy files to target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    written_files = []
    for policy in POLICIES:
        file_path = target_dir / f"{policy['id']}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(policy, f, indent=2)
        written_files.append(file_path)
    return written_files


if __name__ == "__main__":
    out_dir = Path("data/policies")
    files = prepare_policies(out_dir)
    print(f"Successfully prepared {len(files)} policy documents in {out_dir}")
